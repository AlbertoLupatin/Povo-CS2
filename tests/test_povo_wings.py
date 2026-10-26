from unittest import TestCase

from tools.audit_povo_wings import audit
from tools.build_povo_campus import build_geometry,split_auto_doors,is_breakable_glass


class WingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,_=build_geometry()
        cls.spec=levels[0]['wings']

    def test_identity_floor_relationship_and_povo1_side_entrances(self):
        cfg=self.spec['config']
        self.assertLess(cfg['canteen']['bounds'][3],cfg['library']['bounds'][1])
        self.assertEqual([cfg['ground_z'],cfg['first_z']],[4,7.6])
        self.assertFalse(any('_core' in n and n.startswith('exterior_povo1_library_') for n,_,_,_ in self.boxes))
        doors,_=split_auto_doors(self.boxes)
        names={d['name']:d for d in doors}
        for name in ['canteen_outer_entry_bank_0','canteen_inner_entry_bank_0','library_entry_bank_0']:
            self.assertLessEqual(names[name]['parts'][0]['lo'][0],36.2)
            self.assertAlmostEqual(min(p['lo'][2] for p in names[name]['parts']),4.035)
        exit=names['canteen_upper_entry_bank_0']
        self.assertAlmostEqual(min(p['lo'][2] for p in exit['parts']),7.635)
        self.assertTrue(any(n=='exterior_povo1_front_walk' and abs(hi[2]-7.6)<.02 for n,lo,hi,m in self.boxes))

    def test_glass_is_breakable_and_each_library_floor_has_reading_rooms(self):
        for kind in ('library','canteen'):
            for floor in (0,1):
                self.assertTrue(any(n.startswith(f'{kind}_{floor}_') and is_breakable_glass(b)
                                    for b in self.boxes for n,_,_,_ in [b]))
        for level in self.spec['levels']:
            if level['building']=='library':self.assertEqual(len(level['rooms']),3)
        for feature in ['canteen_0_bar_counter','canteen_0_serving_counter','canteen_1_serving_counter','library_0_reception_counter']:
            self.assertTrue(any(n==feature for n,_,_,_ in self.boxes))
        self.assertFalse(any(n=='canteen_1_bar_counter' for n,_,_,_ in self.boxes))

    def test_room_routes_and_both_stairs_have_support_and_standing_headroom(self):
        result=audit()
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(len(result['levels']),4)
        self.assertEqual(result['stair_samples'],44)
        self.assertFalse(result['stair_failures'])

    def test_south_entrance_has_bar_right_dining_left_stairs_ahead(self):
        entry=self.spec['config']['canteen']['entrance_y']
        self.assertLess(entry,-94)
        bar=next(b for b in self.boxes if b[0]=='canteen_0_bar_counter')
        self.assertLess(bar[2][1],entry)
        tables=[b for b in self.boxes if b[0].startswith('canteen_0_dining_table_') and b[0].endswith('_top')]
        self.assertTrue(tables)
        self.assertTrue(all(b[1][1]>entry for b in tables))
        stair=next(s for s in self.spec['stairs'] if s['building']=='canteen')
        self.assertAlmostEqual(stair['bottom'][1],entry)
        self.assertGreater(stair['bottom'][0],36)
