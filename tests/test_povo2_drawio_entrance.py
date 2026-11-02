"""The final campus must implement the user's corrected entrance drawing."""
import unittest
from pathlib import Path

from tools.build_povo_campus import build_geometry,collision_boxes
from tools.povo2_drawio_entrance import read_layout
from tools.audit_povo2_integrated import audit_stair_routes

ROOT=Path(__file__).resolve().parents[1]


class DrawioEntranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.p2=next(l['connection']['povo2'] for l in cls.levels if l.get('connection'))
        cls.physics=collision_boxes(cls.boxes)

    def test_edited_room_edges_and_north_door_come_from_user_file(self):
        layout=read_layout(ROOT);a=layout['areas']
        self.assertAlmostEqual(a['c5'][3],21.0766666667)
        self.assertAlmostEqual(a['e1'][2],31.8)
        self.assertAlmostEqual(a['e2'][2],31.8)
        self.assertEqual(self.p2['walkthrough_repairs']['c5'],a['c5'])
        self.assertEqual(self.p2['walkthrough_repairs']['closed_rooms'],dict(E1=a['e1'],E2=a['e2']))
        self.assertAlmostEqual(self.p2['minus1_corrections']['c5_north_junction_door']['centre'][1],a['c5'][3])

    def test_old_arms_doors_and_stair_bodies_are_absent(self):
        self.assertIsNone(self.p2['walkthrough_repairs']['c7_exit_link'])
        self.assertFalse(any(d['id'].startswith(('p2_c7_exit_','p2_garden_exit_')) for d in self.p2['repair_doors']))
        self.assertFalse(any(n.startswith(('p2_gardens_up_step_','p2_gardens_down_step_',
            'p2_basement_repair_entrance_terrace_1','p2_basement_repair_entrance_terrace_2')) for n,*_ in self.boxes))

    def test_up_stair_is_opposite_terrace_door_and_down_is_on_south_run(self):
        a=self.p2['drawio_entrance']['areas'];up=a['up'];down=a['down'];terrace=a['terrace']
        self.assertAlmostEqual(up[0],20.5);self.assertAlmostEqual(up[2],23.)
        self.assertAlmostEqual(up[3],terrace[1])
        self.assertEqual(down[1::2],terrace[1::2])
        self.assertAlmostEqual(down[0],terrace[2])
        self.assertEqual(sum(n.startswith('p2_basement_drawio_up_step_') for n,*_ in self.boxes),20)
        self.assertEqual(sum(n.startswith('p2_basement_drawio_down_step_') for n,*_ in self.boxes),20)

    def test_local_routes_and_every_tread_clear_in_both_directions(self):
        paths=[dict(points=p) for p in self.p2['gardens']['routes'].values()]
        paths += [r for r in self.p2['basement_rebuild']['routes'] if r['id'].startswith('terrace_to_')]
        both=paths+[dict(points=list(reversed(r['points']))) for r in paths]
        count,failures=audit_stair_routes(self.physics,both)
        self.assertGreater(count,500)
        self.assertFalse(failures,failures[:8])

    def test_sealed_room_and_corridor_doors_have_solid_collision(self):
        def blocked(x,y,z):return any(lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<z<hi[2]
                                    for _,lo,hi,_ in self.physics)
        for x,y in ((21.8,self.p2['drawio_entrance']['areas']['c5'][3]),(23.1,9.1)):
            for z in (.6,1.5,2.4):self.assertTrue(blocked(x,y,z))
        self.assertFalse(any(d['id'].startswith(('p2_drawio_c5_north','p2_drawio_e2')) for d in self.p2['repair_doors']))

    def test_lower_approach_has_no_unfilled_strip_beside_its_walking_route(self):
        for x in (42.3,42.6,43.8,44.9,45.3):
            for y in (3.,5.,8.):
                self.assertTrue(any(lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] and abs(hi[2]+3.2)<.01
                    for _,lo,hi,m in self.physics if m.startswith('floor_')),(x,y))
        walls=[b for b in self.physics if b[0].startswith('p2_basement_drawio_garden_approach_retaining_')]
        self.assertEqual(len(walls),2)
        self.assertTrue(all(lo[2]<-3.2 and hi[2]>=4. for _,lo,hi,_ in walls))

    def test_terrace_is_one_strip_from_its_west_end(self):
        # User correction 31 Oct: no partition across the drawn terrace.
        terrace=self.p2['drawio_entrance']['areas']['terrace'];y=(terrace[1]+terrace[3])/2
        self.assertFalse(any(n.startswith('p2_basement_repair_terrace_end_west') for n,*_ in self.boxes))
        across=[(n,lo,hi) for n,lo,hi,_ in self.physics if lo[0]<terrace[2]-.2 and hi[0]>terrace[0]+.2
                and lo[1]<terrace[3]-.12 and hi[1]>terrace[1]+.12 and lo[2]<2.3 and hi[2]>.45]
        self.assertFalse(across,across[:5])
        route=dict(points=[[terrace[0]+.6,y,.4],[terrace[2]-.6,y,.4]])
        count,failures=audit_stair_routes(self.physics,[route,dict(points=list(reversed(route['points'])))])
        self.assertGreater(count,40)
        self.assertFalse(failures,failures[:8])
        def blocked(x,y,z):return any(lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<z<hi[2] for _,lo,hi,_ in self.physics)
        # Closed at the west end and along the south edge west of the UP stair.
        for z in (.6,1.5,2.4,3.5):
            self.assertTrue(blocked(terrace[0]-.08,y,z))
            for x in (9.,14.,19.5):self.assertTrue(blocked(x,terrace[1]-.08,z),(x,z))


if __name__=='__main__':unittest.main()
