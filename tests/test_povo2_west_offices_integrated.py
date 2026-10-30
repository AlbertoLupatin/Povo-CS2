"""Check the rooms against the final campus solids, not the review shell."""
from unittest import TestCase

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.audit_povo2_integrated import audit_stair_routes
from tools.audit_povo_interior import audit_level
from tools.cs2_campus import room_sign


class IntegratedWestOfficesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,_=build_geometry()
        cls.physics=collision_boxes(cls.boxes)
        cls.spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
        cls.office=cls.spec['west_offices']

    def test_all_22_rooms_reachable_from_the_existing_stair_landing(self):
        stations=[dict(id='main_stair',point=[19.2,22])]
        for r in self.office['rooms']:
            a,b,c,d=r['bounds']
            stations.append(dict(id=r['id'],point=[(a+c)/2,(b+d)/2]))
        report,_,_=audit_level(self.physics,dict(id='p2_basement',floor_elevation_local=.4),
                             stations,width=.82,height=1.85)
        self.assertEqual(len(report['stations']),23)
        self.assertEqual(report['status'],'passed',report['stations'])

    def test_every_door_passage_and_stair_connection_has_standing_clearance(self):
        routes=self.office['routes']
        routes=routes+[dict(points=list(reversed(r['points']))) for r in routes]
        count,failures=audit_stair_routes(self.physics,routes)
        self.assertGreater(count,1000)
        self.assertFalse(failures,failures[:8])

    def test_room_records_signs_and_photo_finishes_are_in_the_actual_map(self):
        self.assertEqual(len(self.office['rooms']),22)
        self.assertNotIn('W03',[r['label'] for r in self.office['rooms']])
        self.assertEqual(len(self.office['corridors']),4)
        self.assertTrue(any(n.startswith('p2_basement_west_glazing_') and m=='reception_glass' for n,_,_,m in self.boxes))
        self.assertTrue(any(n.startswith('p2_basement_west_front_band_') and m=='office_frost' for n,_,_,m in self.boxes))
        for r in self.office['rooms']:
            room_sign(r,.4)
            a,b,c,d=r['bounds'];x,y=(a+c)/2,(b+d)/2
            self.assertTrue(any(m=='floor_wood' and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] and abs(hi[2]-.4)<.01 for _,lo,hi,m in self.physics),r['id'])
            self.assertTrue(any(m=='ceiling_panel' and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] and abs(hi[2]-3.5)<.01 for _,lo,hi,m in self.boxes),r['id'])

    def test_research_door_pairs_remain_fixed_and_solid(self):
        for name in ('upper','lower'):
            leaves=[b for b in self.physics if b[0].startswith('p2_basement_locked_'+name+'_leaf_')]
            self.assertEqual(len(leaves),2)
            self.assertTrue(all(m=='door_black' for _,_,_,m in leaves))

    def test_relocated_lab_desk_keeps_both_legs_under_its_top(self):
        prefix='p2_basement_cibio_office_0_'
        top=next(b for b in self.boxes if b[0]==prefix+'desk_1')
        legs=[b for b in self.boxes if b[0].startswith(prefix+'desk_leg_1_')]
        self.assertEqual(len(legs),2)
        for _,lo,hi,_ in legs:
            for axis in (0,1):
                self.assertGreaterEqual(lo[axis],top[1][axis])
                self.assertLessEqual(hi[axis],top[2][axis])
            self.assertAlmostEqual(hi[2],top[1][2])
