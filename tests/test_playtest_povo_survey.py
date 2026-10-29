"""Source-only survey route/guard tests. Never connects to a game."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from tools import playtest_povo_survey as survey

ROOT=Path(__file__).resolve().parents[1]
READY='@ Current : game\n[1: trento_povo_campus | main lump | mapload]\nplayers : 1 humans, 0 bots'

class SurveyRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
        cls.routes=survey.build_routes(cls.metadata)

    def test_every_stair_segment_has_both_directions_and_current_elevations(self):
        by_name={r['name']:r for r in self.routes}
        for n in range(2):
            for core in ('se','sw','ne','nw'):
                name=f'p1_{core}_segment{n}_up';up=by_name[name]['path']
                self.assertEqual(up,list(reversed(by_name[name+'_return']['path'])))
                self.assertAlmostEqual(up[0][2],4+n*3.6)
                self.assertAlmostEqual(up[-1][2],7.6+n*3.6)
        stair=self.metadata['connection']['stair']
        for module in range(stair['modules']):
            route=by_name[f'p2_upper_module{module}_down']['path']
            self.assertAlmostEqual(route[0][2],4+(module+1)*stair['module_height'])
            self.assertAlmostEqual(route[-1][2],4+module*stair['module_height'])
            self.assertLessEqual(len(route),10)
        self.assertTrue(all(abs(r['target_floor']-11.2)<1e-6 for r in self.routes if r['kind']=='ladder'))
        self.assertEqual(len(by_name),len(self.routes))

    def test_simplification_preserves_corners_and_flat_landing_transition(self):
        path=[[0,0,0],[0,1,1],[0,2,2],[0,3,2],[1,3,2],[2,3,3]]
        self.assertEqual(survey.simplify_path(path),[[0.,0.,0.],[0.,2.,2.],[0.,3.,2.],[1.,3.,2.],[2.,3.,3.]])
        source=self.metadata['stair']['segments'][0]['cores'][0]['path']
        result=survey.simplify_path(source)
        self.assertLess(len(result),len(source))
        self.assertIn(source[8],result)
        self.assertIn(source[15],result)

    def test_p2_floor_checks_use_full_landings_even_with_an_extra_module_turn(self):
        for r in self.routes:
            if r['category'] not in ('p2_upper_stair','p2_lower_stair'):continue
            path=r['path'];landing_x=path[0][0]
            for p in path:
                if any(abs(p[2]-end[2])<1e-6 for end in (path[0],path[-1])):
                    self.assertAlmostEqual(p[0],landing_x,msg=r['name'])

    def test_bridge_and_rotated_basement_use_exported_registration(self):
        bridge=next(r for r in self.routes if r['name']=='p1_p2_bridge')
        self.assertTrue(all(abs(p[2]-11.2)<1e-6 for p in bridge['path']))
        corridor=next(r for r in self.routes if r['name']=='p2_basement_rotated_corridor')['path']
        self.assertEqual(corridor[0][1],corridor[1][1])
        self.assertEqual(corridor[1][0],corridor[2][0])
        self.assertGreater(corridor[2][1],corridor[1][1])
        names={r['name'] for r in self.routes}
        self.assertIn('acquario_door_and_long_aisle',names)
        self.assertIn('a103_side_aisle0',names)
        self.assertIn('a103_side_aisle1',names)
        self.assertEqual(sum(r['category']=='amenity_stair' for r in self.routes),6)


    def test_stair_hull_envelope_is_scoped_to_interior_treads(self):
        for route in self.routes:
            if route['kind']!='walk':continue
            self.assertEqual(survey.waypoint_height_tolerance(route,0),.25)
            self.assertEqual(survey.waypoint_height_tolerance(route,len(route['path'])-1),.25)
            for index,point in enumerate(route['path']):
                tolerance=survey.waypoint_height_tolerance(route,index)
                if any(abs(point[2]-z)<1e-6 for z in (route['path'][0][2],route['path'][-1][2])):
                    self.assertEqual(tolerance,.25)
                if route['category'] not in ('p1_corner_stair','p1_courtyard_stair','p2_upper_stair','p2_lower_stair','amenity_stair'):
                    self.assertEqual(tolerance,.25)
        route=next(r for r in self.routes if r['name']=='p1_se_segment0_up')
        self.assertIn(.42,[survey.waypoint_height_tolerance(route,i) for i in range(len(route['path']))])


class FakeConsole:
    def __init__(self,status):self.status=status;self.calls=[]
    def command(self,commands,seconds=.25):
        self.calls.append(commands)
        return self.status

class SurveyGuardTests(unittest.TestCase):
    def test_rejects_multiplayer_or_wrong_map_without_movement_or_cleanup_mutations(self):
        for status in (READY.replace('trento_povo_campus','de_dust2'),READY.replace('1 humans','2 humans'),READY.replace('0 bots','1 bots')):
            console=FakeConsole(status);driver=survey.Driver(console,'trento_povo_campus')
            with self.assertRaises(survey.GuardError):driver.execute(dict(kind='walk',path=[[0,0,4],[1,0,4]]))
            driver.cleanup()
            self.assertEqual(console.calls,['status'])

    def test_physical_failure_does_not_skip_later_route_and_cannot_false_pass(self):
        class Driver:
            checks=[]
            def execute(self,route):
                if route['name']=='bad':raise RuntimeError('Blocked actual doorway')
                return [dict(passed=True)]
            def cleanup(self):pass
        with tempfile.TemporaryDirectory() as directory:
            report=survey.run_routes(Driver(),[dict(name='bad',kind='walk'),dict(name='good',kind='walk')],dict(routes=[]),Path(directory))
            self.assertEqual(report['status'],'failed')
            self.assertEqual([r['status'] for r in report['routes']],['failed','passed'])
            self.assertTrue((Path(directory)/'bad.json').is_file())
            self.assertTrue((Path(directory)/'good.json').is_file())

    def test_guard_failure_blocks_remaining_routes_and_reports_not_run(self):
        class Driver:
            checks=[]
            def execute(self,route):raise survey.GuardError('Other player joined')
            def cleanup(self):pass
        with tempfile.TemporaryDirectory() as directory:
            report=survey.run_routes(Driver(),[dict(name='one',kind='walk'),dict(name='two',kind='walk')],dict(routes=[]),Path(directory))
            self.assertEqual(report['status'],'failed')
            self.assertEqual([r['status'] for r in report['routes']],['blocked','not_run'])

    def test_wrong_floor_at_matching_xy_fails(self):
        driver=survey.Driver(FakeConsole(READY),'trento_povo_campus')
        with patch.object(driver,'position',return_value=[1,2,4]):
            with self.assertRaisesRegex(RuntimeError,'Unexpected floor height'):driver.walk([1,2,11.2])
        self.assertFalse(driver.checks[-1]['passed'])

    def test_uses_native_sprint_button_and_releases_it(self):
        console=FakeConsole(READY);driver=survey.Driver(console,'trento_povo_campus')
        driver.guard()
        with patch.object(driver,'position',return_value=[0,0,4]):driver.place([0,0,4])
        driver.cleanup()
        sent='\n'.join(c if isinstance(c,str) else '\n'.join(c) for c in console.calls)
        self.assertIn('-sprint 42',sent)
        self.assertNotIn('-speed',sent)
        self.assertNotIn('+speed',sent)
        class PulseConsole(FakeConsole):
            def pulse(self,commands,seconds):self.calls.append(commands)
        console=PulseConsole(READY);driver=survey.Driver(console,'trento_povo_campus')
        with patch.object(driver,'position',side_effect=[[0,0,4],[0,0,4],[1,0,4]]):driver.walk([1,0,4])
        self.assertIn('+sprint 42',console.calls[0])

    def test_position_read_does_not_reuse_last_success_after_missing_reply(self):
        console=FakeConsole('setpos_exact 0 0 157.480315')
        driver=survey.Driver(console,'trento_povo_campus',timings={'position_read':.08})
        self.assertAlmostEqual(driver.position()[2],4,places=3)
        console.status=''
        with self.assertRaisesRegex(RuntimeError,'position unavailable'):driver.position()

    def test_transport_disables_nagle_and_pulse_timings_keep_narrow_cap(self):
        connection=Mock()
        with patch.object(survey.socket,'create_connection',return_value=connection):
            console=survey.Console(27400)
            connection.setsockopt.assert_called_once_with(survey.socket.IPPROTO_TCP,survey.socket.TCP_NODELAY,1)
            console.close()
        class PulseConsole(FakeConsole):
            def pulse(self,commands,seconds):self.calls.append(seconds)
        for tolerance,maximum in ((.15,.45),(.06,.25)):
            console=PulseConsole(READY);driver=survey.Driver(console,'trento_povo_campus')
            with patch.object(driver,'position',side_effect=[[0,0,4],[10,0,4]]):
                driver.walk([10,0,4],xy_tolerance=tolerance)
            self.assertEqual(console.calls,[maximum])

    def test_list_routes_does_not_open_console(self):
        with patch.object(survey,'Console',side_effect=AssertionError('Must not connect')),patch('builtins.print'):
            self.assertEqual(survey.main(['--list-routes','--routes','^p1_p2_bridge$']),0)

if __name__=='__main__':unittest.main()
