import tempfile
import unittest
from pathlib import Path

from tools.povo_elevators import apply, static_boxes, overlap
from tools.povo_elevator_entities import entity_graph, insert_entities
from tools.build_povo_campus import build_registered_geometry, COLORS
from tools.povo_campus_finishes import write_materials
from tools import cs2_project
from tests.test_map_entities import minimal_map

ROOT=Path(__file__).resolve().parents[1]


class LiftGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings,cls.config,cls.boxes,cls.levels,cls.stair=build_registered_geometry(ROOT)
        cls.banks=cls.levels[0]['elevator_banks']

    def test_retired_ladder_and_terrace_closers_are_absent(self):
        names=[b[0] for b in self.boxes]
        self.assertFalse(self.levels[0].get('elevator'))
        self.assertFalse(any(n.startswith('elevator_') or 'east_lift_closer' in n for n in names))
        self.assertTrue(any(n.startswith('p1_courtyard_terrace_east_corridor') for n in names))

    def test_bank_registration_and_stop_levels(self):
        p1,p2=self.banks
        self.assertEqual(p1['bounds'],[8,-85.2,12.6,-79.2])
        self.assertEqual([s['floor'] for s in p1['stops']],[-1,0,1])
        self.assertEqual([s['floor'] for s in p2['stops']],[-1,0])
        self.assertAlmostEqual(p2['bounds'][2]-p2['bounds'][0],9.5)
        self.assertAlmostEqual(p2['bounds'][3]-p2['bounds'][1],8.)
        for bank in self.banks:self.assertEqual(len(bank['cars']),2)

    def test_entire_cabin_sweep_is_free_of_static_geometry(self):
        fixed=static_boxes(self.boxes)
        for bank in self.banks:
            for car in bank['cars']:
                dz=car['stops'][-1]['z']-car['stops'][0]['z']
                for name,lo,hi,mat in car['parts']:
                    swept=(hi[0],hi[1],hi[2]+dz)
                    hits=[n for n,a,b,m in fixed if overlap(lo,swept,a,b)]
                    self.assertEqual(hits,[],(name,hits[:10]))

    def test_sliding_door_sweeps_clear_frames_and_cabin(self):
        fixed=static_boxes(self.boxes)
        for bank in self.banks:
            for car in bank['cars']:
                for gate in car['gates']:
                    name,lo,hi,_=gate['box'];lo=list(lo);hi=list(hi)
                    travel=hi[1]-lo[1]+2/39.37007874
                    if gate['leaf']==0:lo[1]-=travel
                    else:hi[1]+=travel
                    obstacles=fixed+car['parts']+[b['box'] for b in car['buttons']]
                    hits=[n for n,a,b,m in obstacles if overlap(lo,hi,a,b)]
                    self.assertEqual(hits,[],(name,hits))

    def test_team_spawns_do_not_enter_the_new_shaft(self):
        from tools.cs2_campus import T_STARTS
        from tools.audit_povo_exterior_integrated import standing
        from tools.build_povo_campus import collision_boxes
        physics=collision_boxes(self.boxes)
        for x,y,z in T_STARTS:
            foot,obstacles=standing(x,y,4,physics,self.levels[0]['exterior']['collision_meshes'])
            self.assertAlmostEqual(foot,4)
            self.assertFalse(obstacles,(x,y,obstacles))
            for bank in self.banks:
                a,b,c,d=bank['bounds']
                self.assertFalse(a-.4<x<c+.4 and b-.4<y<d+.4)

    def test_landings_have_no_open_unserved_shaft(self):
        for bank in self.banks:
            for car in bank['cars']:
                for i in range(len(car['stops'])):
                    self.assertEqual(len([g for g in car['gates'] if g['stop']==i]),2)
                self.assertEqual(len([g for g in car['gates'] if g['parent']]),2)

    def test_basement_corridor_connects_to_both_lift_entrances(self):
        from tools.audit_povo_interior import audit_level
        from tools.build_povo_campus import collision_boxes
        p2=next(l['connection']['povo2'] for l in self.levels if 'connection' in l)
        level=next(l for l in p2['levels'] if l['floor']==-1)
        physics=collision_boxes(self.boxes)
        support=[(level['id']+'_alias_'+n,a,b,m) for n,a,b,m in physics
                 if n.startswith(('p2_','academic_first_link_p2'))
                 and m.startswith('floor_') and abs(b[2]-.4)<.02]
        stations=[*level['audit_stations'],dict(id='lift1_approach',point=[24.6,28.8]),
                  dict(id='lift2_approach',point=[24.6,32.8]),dict(id='d1_approach',point=[22,35.2])]
        report,_,_=audit_level(physics+support,dict(id=level['id'],floor_elevation_local=.4),stations)
        self.assertEqual(report['status'],'passed',report)

    def test_new_lobby_floor_and_sealed_restricted_boundaries(self):
        for point in [(22,35,.4),(24,30,.4)]:
            self.assertTrue(any(a[0]<=point[0]<=b[0] and a[1]<=point[1]<=b[1] and abs(b[2]-point[2])<.001
                for n,a,b,m in self.boxes if 'floor' in m))
        p=next(l['connection']['povo2'] for l in self.levels if 'connection'in l)
        self.assertEqual(p['minus1_corrections']['c5_north_junction_door']['centre'],[21.8,36,.4])
        self.assertNotIn('lower_junction_door',p['minus1_corrections'])
        self.assertTrue(any(n=='p2_lifts_restricted_corridor_cap' for n,*_ in self.boxes))

    def test_vmap_unique_ids_and_no_duplicate_static_cars(self):
        import re
        graph=entity_graph(self.banks)
        self.assertEqual(len(graph),len({e['name'] for e in graph}))
        template=minimal_map().replace('"origin" "vector3" "0 0 0"', '"origin" "vector3" "0 0 0"\n"angles" "qangle" "0 0 0"\n"scales" "vector3" "1 1 1"')
        text=insert_entities(template,self.banks)
        nodes=re.findall(r'"nodeID"\s+"int"\s+"(\d+)"',text)
        ids=re.findall(r'"elementid"\s+"([^"]+)"',text)
        self.assertEqual(len(nodes),len(set(nodes)))
        self.assertEqual(len(ids),len(set(ids)))
        classes=[c for a,b,c,s in cs2_project._entity_ranges(text)]
        self.assertEqual(classes.count('func_tracktrain'),4)
        self.assertEqual(classes.count('path_track'),10)
        self.assertFalse(any(n.startswith('lift_dynamic_') for n,*_ in static_boxes(self.boxes)))

    def test_interlocks_and_arrival_routing(self):
        graph=entity_graph(self.banks);byname={e['name']:e for e in graph}
        for bank in self.banks:
            for car in bank['cars']:
                cid=car['id'];depart=byname[cid+'_depart']
                self.assertEqual(depart['properties']['StartDisabled'],'1')
                callers=[e for e in graph for out in e['outputs'] if out['target']==cid+'_depart' and out['input']=='Trigger']
                self.assertEqual([e['classname'] for e in callers],['logic_branch_listener'])
                self.assertEqual(byname[cid]['outputs'][0]['output'],'OnArrivedAtDestinationNode')
                for gate in car['gates']:
                    outs=byname[gate['name']]['outputs']
                    self.assertTrue(any(o['output']=='OnFullyClosed' and o['param']=='1' for o in outs))
                    self.assertTrue(any(o['output']=='OnOpen' and o['param']=='0' for o in outs))
                for i in range(len(car['stops'])):
                    opened={o['target'] for o in byname[cid+f'_open{i}']['outputs'] if o['input']=='Open'}
                    self.assertEqual(opened,{g['name'] for g in car['gates'] if g['parent'] or g['stop']==i})
                    self.assertEqual(byname[cid+f'_at{i}']['outputs'][0]['target'],cid+f'_open{i}')
                    self.assertFalse(any(o['input']=='Enable' for o in byname[cid+f'_open{i}']['outputs']))
                    drive=byname[cid+'_drive_case']['outputs'][i]
                    self.assertEqual(drive['param'],cid+f'_path{i}')


class LiftMaterialTests(unittest.TestCase):
    def test_cs2_metalness_maps_exist_and_are_reproducible(self):
        import re
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);selected={k:v for k,v in COLORS.items() if k.startswith('lift_')}
            write_materials(p,'materials/trento/povo/campus/',selected)
            for name in ('lift_steel','lift_dark_steel'):
                text=(p/(name+'.vmat')).read_text()
                self.assertIn('shader "csgo_complex.vfx"',text)
                self.assertIn('g_flMetalness "1"',text)
                self.assertIn('PhysicsSurfaceProperties "metal"',text)
                for path in re.findall(r'Texture\w+ "([^"]+)"',text):self.assertTrue((p/Path(path).name).exists())
            original=(p/'lift_steel.png').read_bytes()
            write_materials(p,'materials/trento/povo/campus/',selected)
            self.assertEqual(original,(p/'lift_steel.png').read_bytes())
