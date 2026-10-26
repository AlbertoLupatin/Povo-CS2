import unittest

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.build_povo_exterior import build
from tools.povo_exterior_materials import OPACITY


class UserGeometryCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.exterior,cls.meshes,cls.meta,_=build()

    def test_shared_room_boundaries_are_opaque_and_solid(self):
        for level in self.levels:
            self.assertGreater(len(level['room_partitions']),20)
            for partition in level['room_partitions']:
                a,b,z,c,d,top=partition['bounds']
                axis=0 if c-a>d-b else 1
                for fraction in (.1,.5,.9):
                    p=[(a+c)/2,(b+d)/2,z+1.6]
                    p[axis]=(a if axis==0 else b)+fraction*((c-a) if axis==0 else (d-b))
                    covering=[box for box in self.boxes if all(box[1][i]<=p[i]<=box[2][i] for i in range(3))]
                    self.assertTrue(any(box[3]=='wall' for box in covering),partition['rooms'])
                    self.assertFalse(any(box[3] in ('window_glass','reception_glass') for box in covering),partition['rooms'])

    def test_straight_stair_has_a_clear_landing_and_ends_on_upper_pavement(self):
        spec=self.meta['config']['east_approach']
        stairs=[box for box in self.exterior if box[0].startswith('entry_stair_')]
        self.assertEqual(len(stairs),12)
        self.assertGreaterEqual(stairs[0][1][0]-24,2.5)
        for step in stairs:
            self.assertAlmostEqual((step[1][1]+step[2][1])/2,spec['entrance_y'])
        for lower,upper in zip(stairs,stairs[1:]):
            self.assertAlmostEqual(lower[2][0],upper[1][0])
            self.assertAlmostEqual(upper[2][2]-lower[2][2],.15)
        pavement=next(box for box in self.exterior if box[0]=='povo1_passage_upper')
        self.assertEqual(stairs[-1][2][0],pavement[1][0])
        self.assertEqual(stairs[-1][2][2],pavement[2][2])

    def test_translucent_cover_runs_from_threshold_to_before_street_pavement(self):
        roof=[m for m in self.meshes if m['name'].startswith('entry_canopy_roof_')]
        self.assertEqual(len(roof),3)
        self.assertEqual(min(v[0] for m in roof for v in m['vertices']),24)
        self.assertEqual(max(v[0] for m in roof for v in m['vertices']),52)
        self.assertTrue(all(m['material']=='canopy_glass' for m in roof))
        self.assertTrue(0<OPACITY['canopy_glass']<1)

    def test_basement_turns_right_west_and_retains_only_actual_stair_door(self):
        p2=self.levels[1]['connection']['povo2']
        corridor=p2['basement']['corridor'];branch=p2['basement']['cross_corridor']
        self.assertLess(branch[0],corridor[0])
        self.assertEqual(branch[2],corridor[2])
        self.assertFalse(any('_fire_door_' in n for n,_,_,_ in self.boxes if n.startswith('p2_')))
        doors=[n for n,_,_,_ in self.boxes if n.startswith('p2_basement_core_door_')]
        self.assertEqual(set(doors),{'p2_basement_core_door_south','p2_basement_core_door_north'})
        self.assertFalse(any(n.startswith('p2_basement_closed_door_0') for n,_,_,_ in self.boxes))

    def test_gate_delimits_far_side_of_street_opposite_both_entrances(self):
        gate=self.meta['config']['street_end_gate'];bars=[box for box in self.exterior if box[0].startswith('street_end_gate_bar_')]
        self.assertGreaterEqual(gate['height'],4)
        self.assertTrue(all(box[1][0]>67.3 for box in bars))
        self.assertLessEqual(min(box[1][1] for box in bars),-116)
        self.assertGreaterEqual(max(box[2][1] for box in bars),120)
        self.assertTrue(all(right[1][1]-left[2][1]<.3 for left,right in zip(bars,bars[1:])))

    def test_concrete_fills_outskirts_and_under_map_without_expanding_navigation(self):
        context=[box for box in self.boxes if box[0].startswith('exterior_context_concrete_')]
        self.assertEqual(len(context),5)
        self.assertFalse(any(box[0].startswith('exterior_context_concrete_') for box in collision_boxes(self.boxes)))
        for x,y in ((-300,0),(300,0),(0,300),(0,-300),(-300,-300),(300,300)):
            self.assertTrue(any(lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] and hi[2]==2.75 for _,lo,hi,_ in context))
        underlay=next(box for box in context if box[0].endswith('_underlay'))
        self.assertLess(underlay[2][2],-3.2)


if __name__=='__main__':unittest.main()
