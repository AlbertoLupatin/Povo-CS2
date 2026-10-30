"""Walkthrough regressions against the whole assembled campus."""
import unittest
from tools.build_povo_campus import build_geometry, collision_boxes, is_breakable_glass
from tools.audit_povo2_integrated import audit_stair_routes
from tools.povo_interactions import extract_static_leaves


class WalkthroughRepairsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,cls.stair=build_geometry()
        cls.p2=next(l['connection']['povo2'] for l in cls.levels if l.get('connection'))

    def test_street_arrival_reaches_both_left_turns_with_no_ladder(self):
        self.assertFalse(self.p2['lift']['enabled'])
        self.assertFalse(any(n.startswith('p2_lift_') for n,*_ in self.boxes))
        ids=('street_to_c5','c5_to_wi1','c5_to_c7','c5_to_sealed_end','terrace_to_garden')
        paths=[r for r in self.p2['basement_rebuild']['routes'] if r['id'] in ids]
        self.assertEqual(len(paths),5)
        _,failures=audit_stair_routes(collision_boxes(self.boxes),
            paths+[dict(points=list(reversed(r['points']))) for r in paths])
        self.assertFalse(failures,failures[:5])

    def test_east_entrance_follows_the_user_correction(self):
        """User draw.io, 30 Oct, on the registered building (real metres)."""
        repair=self.p2['walkthrough_repairs'];c5=repair['c5'];front=self.p2['south_front']
        reg=self.p2['registration']
        # C5: narrow, on the office facade line, under the bridge (E 16.5-20).
        self.assertLess(c5[2]-c5[0],2.5)
        self.assertTrue(16<c5[0]<c5[2]<20)
        self.assertAlmostEqual(c5[1],front['terrace'][3],delta=.1)
        doors={d['id']:d for d in self.p2['repair_doors']}
        self.assertAlmostEqual(doors['p2_c5_terrace_0']['pivot'][1],c5[1])
        self.assertTrue(c5[0]<doors['p2_c5_terrace_0']['pivot'][0]<c5[2])
        # WI1 then C7 on the left (west); C7 opens full width.
        self.assertAlmostEqual(doors['p2_wi1_public_0']['pivot'][0],c5[0])
        self.assertNotIn('p2_c7_public_0',doors);self.assertNotIn('p2_c7_exit_0',doors)
        physics=collision_boxes(self.boxes)
        blocked=lambda x,y,z:any(lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<z<hi[2] for _,lo,hi,_ in physics)
        from tools.povo2_registration import Registration
        from tools.build_povo_campus import ROOT
        c7=[Registration(ROOT).fy(y) for y in (15.6,16.6,17.6)]  # C7 at the junction
        for y in c7:
            for z in (.6,1.5,2.4):self.assertFalse(blocked(c5[0]-.07,y,z),(y,z))
        # The sealed door ends C5 north of C7, beside the core.
        sealed=self.p2['minus1_corrections']['c5_north_junction_door']
        self.assertAlmostEqual(sealed['centre'][1],c5[3])
        self.assertGreater(c5[3],self.p2['stairs']['bounds'][1])
        for x in (sealed['centre'][0]-.5,sealed['centre'][0]+.5):
            for z in (.6,1.5,2.4):self.assertTrue(blocked(x,c5[3],z),(x,z))
        # No exit corridor, garden exit or locked lower door any more.
        self.assertNotIn('lower_junction_door',self.p2['minus1_corrections'])
        self.assertNotIn('p2_garden_exit_0',doors)
        self.assertFalse(any(n.startswith('p2_basement_locked_lower_') for n,*_ in self.boxes))
        # E1/E2 reach the real building edge (LiDAR E 25.75).
        self.assertAlmostEqual(repair['closed_rooms']['E2'][2],25.8,delta=.3)
        self.assertIn('x_knots',reg)

    def test_glass_fronts_are_entities_and_no_privacy_strip_blocks_the_broken_opening(self):
        fronts=[b for b in self.boxes if b[0].startswith('p2_basement_west_glazing_')]
        self.assertGreater(len(fronts),20)
        self.assertTrue(all(is_breakable_glass(b) for b in fronts))
        physics=collision_boxes(self.boxes)
        self.assertFalse(any(m=='office_frost' for _,_,_,m in physics))
        door_ids={d['id'] for d in self.p2['repair_doors']}
        for room in self.p2['west_offices']['rooms']:
            self.assertIn('p2_'+room['id']+'_0',door_ids)
        extracted=extract_static_leaves(self.boxes,self.levels,self.stair,automatic_entrances=True)
        self.assertFalse(any('_interactive_leaf_' in n for n,*_ in extracted))

    def test_cibio_terrace_doors_and_closed_earth_beside_the_front(self):
        ids={d['id'] for d in self.p2['repair_doors']}
        self.assertTrue({'p2_cibio_terrace_0_0','p2_cibio_terrace_1_0'}<=ids)
        bank=[m for m in self.levels[0]['exterior']['meshes'] if m['name'].startswith('exterior_p2_front_bank_')]
        self.assertEqual(len(bank),18)
        for mesh in bank:
            self.assertAlmostEqual(min(v[2] for v in mesh['vertices']),2.5)
            self.assertEqual(len(mesh['faces']),12)
