"""Complete floor coverage and usable routes, including the former shaft holes."""
import math
import re
from unittest import TestCase
from tools.build_povo_campus import build_geometry,collision_boxes
from tools.audit_povo2_integrated import audit_stair_routes
from tools.povo2_basements import union_rectangles


class BasementRebuildTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,cls.stair=build_geometry()
        cls.levels=levels
        cls.physics=collision_boxes(cls.boxes)
        cls.spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))

    def test_entire_approved_footprints_have_floor_and_ceiling(self):
        shaft=self.spec['lift']['shaft'];samples=0
        for level in self.spec['basement_rebuild']['levels']:
            z=.4 if level['floor']==-1 else -3.2
            for a,b,c,d in level['areas']:
                for i in range(math.ceil((c-a)/.35)):
                    for j in range(math.ceil((d-b)/.35)):
                        x=min(c-.02,a+.02+i*.35);y=min(d-.02,b+.02+j*.35)
                        if level['floor']==-1 and shaft[0]<=x<=shaft[2] and shaft[1]<=y<=shaft[3]:continue
                        samples+=1
                        self.assertTrue(any(m.startswith('floor_') and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                                            and abs(hi[2]-z)<.02 for _,lo,hi,m in self.physics),(level['floor'],x,y))
                        self.assertTrue(any(m=='ceiling_panel' and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                                            and z+2.9<lo[2]<z+3.2 for _,lo,hi,m in self.boxes),(level['floor'],x,y,'ceiling'))
        self.assertGreater(samples,12000)

    def test_former_parking_shaft_is_closed_at_both_ends(self):
        # These points lay in holes left by the old, moved staircase's floor
        # and ceiling cuts. They are ordinary parking bays in the accepted plan.
        for x,y in ((-8,17),(-4,17),(3,15),(8,18.8)):
            for material,h in (('floor_p2_asphalt',-3.2),('ceiling_panel',-.1)):
                self.assertTrue(any(m==material and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                                    and abs(hi[2]-h)<.01 for _,lo,hi,m in self.boxes),(x,y,material))

    def test_all_six_parking_columns_reach_the_ceiling_without_orphaned_trim(self):
        columns=[b for b in self.boxes if re.fullmatch(r'p2_parking_rebuilt_column_\d+',b[0])]
        self.assertEqual(len(columns),6)
        for name,lo,hi,material in columns:
            self.assertEqual(material,'wall')
            self.assertAlmostEqual(lo[2],-3.2)
            self.assertAlmostEqual(hi[2],-.17)
        self.assertFalse(any(n.startswith('p2_parking_column_') for n,_,_,_ in self.boxes))

    def test_all_accepted_routes_and_thresholds_have_clearance_in_both_directions(self):
        routes=self.spec['basement_rebuild']['routes']+self.spec['parking']['routes']
        both=routes+[dict(points=list(reversed(r['points']))) for r in routes]
        count,failures=audit_stair_routes(self.physics,both)
        self.assertGreater(count,1200)
        self.assertFalse(failures,failures[:5])

    def test_union_has_no_internal_walls_or_overlapping_floor_pieces(self):
        strips,edges=union_rectangles([(0,0,4,2),(2,0,6,2),(4,2,6,4)])
        self.assertAlmostEqual(sum((c-a)*(d-b) for a,b,c,d in strips),16)
        for i,a in enumerate(strips):
            for b in strips[i+1:]:
                self.assertFalse(a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1])
        self.assertNotIn((0,4,0,2),edges)

    def test_markup_lab_gap_is_longer_and_only_its_right_half_is_walkable(self):
        level=next(l for l in self.spec['levels'] if l['floor']==-1)
        first,second=sorted(level['rooms'],key=lambda r:r['bounds'][1])
        self.assertAlmostEqual(second['bounds'][1]-first['bounds'][3],30)
        sections=self.spec['minus1_corrections']['spine_sections'];a,b,c,d=sections[1]
        self.assertAlmostEqual(c-a,1.5)
        self.assertAlmostEqual(a,-3.8)
        x=(a+c)/2;y=(b+d)/2
        self.assertTrue(any(n.startswith('p2_basement_rebuilt_floor') and lo[0]<=x<=hi[0]
            and lo[1]<=y<=hi[1] for n,lo,hi,m in self.physics))
        self.assertFalse(any(n.startswith('p2_basement_rebuilt_floor') and lo[0]<=a-.75<=hi[0]
            and lo[1]<=y<=hi[1] for n,lo,hi,m in self.physics))

    def test_markup_new_doors_are_solid_and_have_no_opening_entities(self):
        from tools.povo_interactions import extract_static_leaves
        extract_static_leaves(self.boxes,self.levels,self.stair,automatic_entrances=True)
        interactions=self.levels[0]['interactions']
        self.assertFalse(any('lab_junction' in d['id'] or 'locked_' in d['id'] for d in interactions['doors']))
        for name in ('upper','lower'):
            leaves=[b for b in self.physics if b[0].startswith(f'p2_basement_locked_{name}_leaf_')]
            self.assertEqual(len(leaves),2)
            self.assertTrue(all(m=='door_black' and hi[2]-lo[2]>=2.2 for _,lo,hi,m in leaves))

    def test_markup_l_corridor_is_isolated_while_labs_and_exit_remain_connected(self):
        from tools.audit_povo_interior import audit_level
        level=next(l for l in self.spec['levels'] if l['floor']==-1)
        report,_,_=audit_level(self.physics,dict(id=level['id'],floor_elevation_local=level['z']),
            level['audit_stations']+level['closed_stations'],width=.82,height=1.85)
        checks={s['id']:s for s in report['stations']}
        for s in level['audit_stations']:self.assertTrue(checks[s['id']]['reachable_from_entrance'],s['id'])
        for s in level['closed_stations']:self.assertFalse(checks[s['id']]['reachable_from_entrance'],s['id'])
