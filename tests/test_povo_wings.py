from pathlib import Path
from unittest import TestCase

from tools.audit_povo_wings import audit
from tools.povo_wings import extend
from tools.build_povo_campus import split_auto_doors,is_breakable_glass

ROOT=Path(__file__).resolve().parents[1]

class WingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        levels=[{}]
        cls.boxes=extend([],levels,ROOT)
        cls.spec=levels[0]['wings']

    def test_identity_and_confirmed_floor_relationship(self):
        cfg=self.spec['config']
        self.assertLess(cfg['canteen']['bounds'][3],cfg['library']['bounds'][1])
        self.assertEqual([cfg['ground_z'],cfg['first_z']],[4,7.6])
        self.assertEqual([(v['floor'],v['campus_floor']) for v in self.spec['levels']],[(0,-1),(1,0)]*2)
        doors,_=split_auto_doors(self.boxes)
        names={d['name']:d for d in doors}
        for name in ['canteen_outer_entry_bank_0','canteen_inner_entry_bank_0','library_entry_bank_0']:
            self.assertAlmostEqual(min(p['lo'][2] for p in names[name]['parts']),4.035)
        self.assertAlmostEqual(min(p['lo'][2] for p in names['canteen_upper_entry_bank_0']['parts']),7.635)

    def test_observed_partitions_replace_synthetic_repeated_rooms(self):
        ground=next(v for v in self.spec['levels'] if v['id']=='library_0')
        upper=next(v for v in self.spec['levels'] if v['id']=='library_1')
        self.assertGreater(len(ground['rooms']),3)
        self.assertTrue(ground['observed_openings'])
        self.assertEqual(upper['rooms'],[])
        self.assertTrue(upper['semantic_zones'])
        self.assertTrue(upper['unresolved'])
        for kind in ('library','canteen'):
            for floor in (0,1):
                self.assertTrue(any(n.startswith(f'{kind}_{floor}_') and is_breakable_glass(b)
                                    for b in self.boxes for n,_,_,_ in [b]))
        for feature in ['canteen_0_bar_counter','canteen_0_serving_counter','canteen_1_serving_counter','library_0_open_reading_0_top']:
            self.assertTrue(any(n==feature for n,_,_,_ in self.boxes),feature)
        self.assertEqual(len({b[0] for b in self.boxes}),len(self.boxes))

    def test_room_routes_and_three_stairs_have_support_and_headroom(self):
        result=audit(self.boxes,self.spec)
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(len(result['levels']),4)
        self.assertEqual(len(self.spec['stairs']),3)
        self.assertGreater(result['stair_samples'],60)
        self.assertFalse(result['stair_failures'])

    def test_canopy_is_thin_open_and_clears_entire_entrance_stair(self):
        canopy=self.spec['canopy']
        self.assertTrue(canopy['walkable'])
        self.assertFalse(canopy['enclosed'])
        strips=[b for b in self.boxes if b[0].startswith('amenities_walkable_canopy_')]
        self.assertTrue(strips)
        for _,lo,hi,_ in strips:
            self.assertAlmostEqual(hi[2]-lo[2],.08)
            x=(lo[0]+hi[0])/2
            floor=4 if x<27 else 7.6 if x>36 else 4+(x-27)*3.6/9
            self.assertGreater(lo[2]-floor,3.2)
        self.assertEqual(self.spec['terrace']['z'],7.6)

    def test_south_entrance_has_bar_right_dining_left_stairs_ahead(self):
        entry=self.spec['config']['canteen']['entrance_y']
        bar=next(b for b in self.boxes if b[0]=='canteen_0_bar_counter')
        self.assertLess(bar[2][1],entry)
        tables=[b for b in self.boxes if b[0].startswith('canteen_0_dining_table_') and b[0].endswith('_top')]
        self.assertTrue(tables)
        self.assertTrue(all(b[1][1]>entry for b in tables))
        stair=next(s for s in self.spec['stairs'] if s['building']=='canteen')
        self.assertAlmostEqual(stair['bottom'][1],entry,delta=.4)
        self.assertGreater(stair['bottom'][0],36)
