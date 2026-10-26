import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from tools.povo2_planimetry import build
from tools.audit_povo2_planimetry import audit
from tools.build_povo_campus import build_geometry
from tools.cs2_campus import make_radar
from tools.verify_cs2_package import overview_values, radar_layout, VPKError


class Povo2PlanimetryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boxes,cls.spec=build()

    def test_user_layout_is_relative_to_the_entrance(self):
        g=self.spec['ground'];entry=g['entrance'];a,b,c,d=g['reception']
        self.assertGreater(a,entry[0])
        self.assertLess(b, (entry[1]+entry[2])/2)
        self.assertGreater(d, (entry[1]+entry[2])/2)
        self.assertLess(g['tables'][3],entry[1])
        self.assertGreater(g['left_corridor'][1],entry[2])
        self.assertGreater(self.spec['stairs']['bounds'][1],d-.01)

    def test_b_rooms_start_at_b111_with_boards_on_the_opposite_wall(self):
        ground=next(l for l in self.spec['levels'] if l['floor']==0)
        self.assertEqual([r['label'] for r in ground['rooms']],['B111','B112','B113','B114'])
        self.assertEqual([r['door_y'] for r in ground['rooms']],sorted(r['door_y'] for r in ground['rooms'])[::-1])
        for room in ground['rooms']:
            self.assertEqual(room['door_side'],'v_min')  # facing east on entry
            board=next(b for b in self.boxes if b[0]=='p2_ground_'+room['id']+'_blackboard')
            a,b,c,d=room['bounds']
            self.assertGreater(board[1][1],d-.2)  # opposite the previous south wall
            # Assert actual geometry as well as metadata: no seat/desk/window props.
            interior=[n for n,lo,hi,m in self.boxes
                      if a+.3<lo[0] and hi[0]<c-.3 and b+.3<lo[1] and hi[1]<d-.3
                      and 4.01<hi[2] and lo[2]<6.2]
            self.assertFalse(interior,(room['id'],interior))
            self.assertEqual(room['fitout']['seats'],0)

    def test_reception_has_transparent_glazing_furniture_and_no_opening(self):
        self.assertFalse(self.spec['ground']['reception_playable'])
        front=next(b for b in self.boxes if b[0]=='p2_ground_reception_front')
        self.assertEqual(front[3],'reception_glass')
        self.assertEqual(front[1][1],26)
        self.assertEqual(front[2][1],32)
        sides=[b for b in self.boxes if b[3]=='reception_glass']
        self.assertEqual(len(sides),4)
        self.assertEqual(self.spec['ground']['office_fitout']['staff'],3)
        self.assertTrue(any(b[0]=='p2_ground_reception_front_desk_top' for b in self.boxes))

    def test_tables_follow_right_wall_and_rooms_open_from_opposite_side(self):
        ground=next(l for l in self.spec['levels'] if l['floor']==0)
        tables=ground['table_bounds'];hall=self.spec['ground']['right_corridor']
        self.assertEqual(len(tables),11)
        self.assertTrue(all(abs(r[0]-7.8)<1e-8 and r[2]<hall[2] for r in tables))
        self.assertTrue(all(r[2]==(hall[0]+hall[2])/2 for r in tables))
        self.assertEqual(hall[1],min(r['bounds'][1] for r in ground['rooms']))
        self.assertEqual(self.spec['footprint'][1],hall[1])
        self.assertLess(min(r[1] for r in tables),hall[1]+3)
        self.assertGreater(max(r[3] for r in tables),hall[3]-3)
        self.assertTrue(all(r['bounds'][0]==hall[2] for r in ground['rooms']))
        self.assertTrue(all(r['bounds'][0]==self.spec['ground']['reception'][0] for r in ground['rooms']))
        walls=[b for b in self.boxes if b[0].startswith('p2_ground_reception_wall_extension')]
        for y in (32.5,36,41.5):
            self.assertTrue(any(lo[0]<21<hi[0] and lo[1]<y<hi[1] and lo[2]<5<hi[2] for _,lo,hi,_ in walls))
        self.assertFalse(any(lo[0]<21<hi[0] and lo[1]<39.5<hi[1] and lo[2]<5<hi[2] for _,lo,hi,_ in walls))

    def test_basement_stair_block_starts_with_corridor_and_has_right_end_turn(self):
        a,b,c,d=self.spec['basement']['corridor'];door_y=self.spec['stairs']['door_y']
        self.assertEqual(c,self.spec['stairs']['bounds'][0])
        self.assertEqual(b,self.spec['stairs']['bounds'][1])
        self.assertLess((door_y-b)/(d-b),.25)
        short=self.spec['basement']['cross_corridor']
        self.assertEqual(short[3],d)
        self.assertGreater(short[1],door_y)  # north/right when exiting the door westwards
        self.assertEqual(short[0],a)
        self.assertGreater(short[2],c)  # Turn right/east when heading north in the drawing.

    def test_three_stair_connections_reach_four_levels_with_safe_rises(self):
        self.assertEqual([l['floor'] for l in self.spec['levels']],[-2,-1,0,1])
        self.assertEqual([p['floor'] for p in self.spec['stairs']['portals']],[-2,-1,0,1])
        for lower in (-2,-1,0):
            steps=[f for f in self.spec['stairs']['flights'] if f['lower_floor']==lower]
            self.assertEqual(len(steps),20)
            self.assertTrue(all(abs(f['rise']-.18)<1e-8 for f in steps))
        _,_,_,levels,_=build_geometry()
        self.assertEqual(levels[1]['connection']['floor_local_metres'],self.spec['levels'][-1]['z'])
        self.assertEqual(len(levels),2)  # Povo 1 remains two storeys

    def test_all_routes_have_support_clearance_and_stair_headroom(self):
        result=audit()
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual(result['stair_samples'],75)
        self.assertFalse(result['stair_failures'])
        self.assertEqual(len(result['levels']),4)

    def test_four_radar_floors_and_package_aliases(self):
        _,_,_,levels,_=build_geometry()
        metadata={'levels':levels,'connection':levels[1]['connection'],
                  'povo2':self.spec,'stair':{'cores':[]}}
        with tempfile.TemporaryDirectory() as tmp, patch('tools.cs2_campus.ROOT',Path(tmp)):
            out=make_radar(metadata)
            values=overview_values((out/'trento_povo_campus.txt').read_bytes(),'trento_povo_campus')
            sections={k.split('.')[1] for k in values if k.startswith('verticalsections.')}
            self.assertEqual(sections,{'default','lower','basement1','basement2'})
            files,aliases=radar_layout('trento_povo_campus',sections=sections)
            self.assertEqual(len(files),17)
            self.assertEqual(len(aliases),8)
            self.assertEqual(len(list(out.glob('*.vtex'))),8)
            ordered=['basement2','basement1','lower','default']
            for first,second in zip(ordered,ordered[1:]):
                self.assertEqual(values[f'verticalsections.{first}.altitudemax'],
                                 values[f'verticalsections.{second}.altitudemin'])
        with self.assertRaises(VPKError):
            radar_layout('trento_povo_campus',sections=['../bad'])
