from unittest import TestCase
from tools.build_povo_campus import build_geometry
from tools.audit_povo_yard import audit_gardens


class GardensTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.spec=cls.levels[-1]['connection']['povo2']

    def test_up_faces_exit_and_down_continues_straight_from_passage(self):
        g=self.spec['gardens']
        self.assertEqual(g['passage'][3]-g['passage'][1],2.5)
        self.assertEqual((g['up_stair'][0]+g['up_stair'][2])/2,g['exit_door'][0])
        self.assertEqual(g['up_stair'][3],g['passage'][1])
        self.assertEqual(g['down_stair'][1::2],g['passage'][1::2])
        self.assertEqual(g['down_stair'][0],g['passage'][2])
        self.assertTrue(all(p[1]==10 for p in g['routes']['down']))
        self.assertEqual(g['down_stair'][0],g['garden'][0])
        self.assertEqual(g['down_stair'][2],(g['garden'][0]+g['garden'][2])/2)
        self.assertLessEqual(g['garden'][1],g['down_stair'][1])
        self.assertGreaterEqual(g['garden'][3],g['down_stair'][3])
        self.assertEqual(g['indoor_corridor'][1],g['exit_door'][1])
        self.assertGreater(g['indoor_turn'][1],g['garden'][3])
        self.assertEqual(g['garden_z'],next(l['z'] for l in self.spec['levels'] if l['floor']==-2))
        self.assertTrue(all(p[2]==g['passage_z'] for p in g['routes']['passage']))
        self.assertLess(g['routes']['down'][-1][2],g['routes']['down'][0][2])
        self.assertGreater(g['routes']['up'][-1][2],g['routes']['up'][0][2])
        self.assertFalse(any(n.startswith('p2_basement_exit_step_') for n,*_ in self.boxes))

    def test_routes_clear_and_removed_threshold_is_detected(self):
        report=audit_gardens(self.boxes,self.levels)
        self.assertEqual(report['status'],'passed',report['failures'][:5])
        broken=[b for b in self.boxes if b[0]!='p2_basement_gardens_passage']
        self.assertEqual(audit_gardens(broken,self.levels)['status'],'failed')
