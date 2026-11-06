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
        link=next(l['connection'] for l in self.levels if l.get('connection'))
        self.assertFalse(link['lift']['enabled'])
        self.assertFalse(any(n.startswith('p2_lift_') for n,*_ in self.boxes))
        ids=('terrace_to_wi1','terrace_to_c7','terrace_to_c5_north')
        paths=[r for r in self.p2['basement_rebuild']['routes'] if r['id'] in ids]
        self.assertEqual(len(paths),3)
        _,failures=audit_stair_routes(collision_boxes(self.boxes),
            paths+[dict(points=list(reversed(r['points']))) for r in paths])
        self.assertFalse(failures,failures[:5])

    def test_east_entrance_follows_photo46(self):
        repair=self.p2['walkthrough_repairs'];c5=repair['c5']
        # A narrow C5 on the office facade, entered on the facade line.
        self.assertAlmostEqual(c5[0],20.5);self.assertLess(c5[2]-c5[0],3)
        self.assertAlmostEqual(c5[1],2.0)
        doors={d['id']:d for d in self.p2['repair_doors']}
        self.assertAlmostEqual(doors['p2_c5_terrace_0']['pivot'][1],c5[1])
        self.assertTrue(c5[0]<doors['p2_c5_terrace_0']['pivot'][0]<c5[2])
        # WI1 is the first left turn; C7 opens full width with no door.
        self.assertAlmostEqual(doors['p2_wi1_public_0']['pivot'][0],c5[0])
        self.assertAlmostEqual(doors['p2_wi1_public_0']['bounds'][0][1]+.95-.018,9.260619977)
        self.assertNotIn('p2_c7_public_0',doors)
        physics=collision_boxes(self.boxes)
        blocked=lambda x,y,z:any(lo[0]<x<hi[0] and lo[1]<y<hi[1] and lo[2]<z<hi[2] for _,lo,hi,_ in physics)
        for y in (15.6,16.6,17.6):
            for z in (.6,1.5,2.4):self.assertFalse(blocked(20.43,y,z),(y,z))
        # The user's Draw.io moves the sealed end north of the C7 junction.
        sealed=self.p2['minus1_corrections']['c5_north_junction_door']
        self.assertAlmostEqual(sealed['centre'][1],c5[3]);self.assertAlmostEqual(c5[3],21.0766666667)
        for x in (sealed['centre'][0]-.5,sealed['centre'][0]+.5):
            for z in (.6,1.5,2.4):self.assertTrue(blocked(x,c5[3],z),(x,z))
        self.assertFalse(any(d['id'].startswith('p2_c5_north') for d in self.p2['repair_doors']))
        # No arm north of C7, and the original closed lower door is restored.
        self.assertNotIn('exit_arm',repair)
        self.assertEqual(self.p2['minus1_corrections']['lower_junction_door']['centre'][:2],[34.5,18.0])
        self.assertEqual(self.p2['minus1_corrections']['closed_corridor_areas'][1][1],18.0)
        self.assertIsNone(repair['c7_exit_link'])
        self.assertNotIn('p2_c7_exit_0',doors)

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

    def test_cibio_and_relocated_entrance_keep_doors_and_stair_retaining_walls(self):
        ids={d['id'] for d in self.p2['repair_doors']}
        self.assertTrue({'p2_c5_terrace_0','p2_c5_terrace_1'}<=ids)
        self.assertFalse(any(n.startswith('p2_cibio_terrace_') for n in ids))
        meshes=[m for m in self.levels[0]['exterior']['meshes']
                if m['name'].startswith('exterior_p2_garden_slope_')]
        self.assertEqual(meshes,[])
        retaining=[b for b in self.boxes if b[0].startswith('p2_basement_drawio_up_retaining_')]
        self.assertEqual(len(retaining),2)
        self.assertTrue(all(hi[2]-lo[2]>3.8 for _,lo,hi,_ in retaining))
