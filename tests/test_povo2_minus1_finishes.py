"""Finishing changes must preserve the definitive plan and standing access."""
import unittest
from unittest.mock import patch

from tools.build_povo_campus import build_geometry, collision_boxes, is_breakable_glass
from tools.audit_povo2_integrated import audit_stair_routes


class Minus1FinishesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.spec=next(l['connection']['povo2'] for l in cls.levels if l.get('connection'))
        cls.physics=collision_boxes(cls.boxes)

    def test_definitive_room_corridor_stair_and_terrace_coordinates_unchanged(self):
        with patch('tools.povo2_minus1_finishes.extend',side_effect=lambda boxes,levels:boxes):
            _,_,_,levels,stair=build_geometry()
        before=next(l['connection']['povo2'] for l in levels if l.get('connection'))
        for key in ('footprint','c7','c7_end','corridors','openings','public_portals'):
            self.assertEqual(before['west_offices'][key],self.spec['west_offices'][key],key)
        def without_fitout(rooms):return [{k:v for k,v in r.items() if k!='fitout'} for r in rooms]
        self.assertEqual(without_fitout(before['west_offices']['rooms']),without_fitout(self.spec['west_offices']['rooms']))
        self.assertEqual(before['stairs'],self.spec['stairs'])
        self.assertEqual(before['drawio_entrance'],self.spec['drawio_entrance'])
        for old,new in zip(before['levels'],self.spec['levels']):
            self.assertEqual(without_fitout(old.get('rooms',[])),without_fitout(new.get('rooms',[])))

    def test_shared_offices_have_two_populated_rows_and_other_W_rooms_one_computer(self):
        labs=next(l['rooms'] for l in self.spec['levels'] if l['floor']==-1)
        for room in self.spec['west_offices']['rooms']+labs:
            fit=room['fitout'];shared=room in labs or room['label'] in ('W01','W02','W04')
            if shared:self.assertEqual(len(fit['rows']),2);self.assertGreaterEqual(min(fit['rows']),2)
            else:self.assertEqual(fit['desks'],1)
            actual=[b for b in self.boxes if b[0].startswith('p2_basement_fitout_'+room['id']+'_row_')]
            self.assertEqual(sum(n.endswith('_monitor') for n,*_ in actual),fit['desks'])
            a,b,c,d=room['bounds']
            for n,lo,hi,_ in actual:
                self.assertTrue(a+.149<=lo[0]<hi[0]<=c-.149 and b+.149<=lo[1]<hi[1]<=d-.149,n)
            self.assertTrue(any(n.endswith('_desk') and n.startswith('p2_basement_fitout_'+room['id']+'_') for n,*_ in self.physics))

    def test_only_outside_w_faces_and_opposite_cibio_walls_are_glass(self):
        for f in self.spec['minus1_finishes']['external_w_faces']:
            along=1-f['axis'];p=[0.,0.,1.9];p[f['axis']]=f['fixed'];p[along]=sum(f['span'])/2
            panes=[b for b in self.boxes if is_breakable_glass(b) and all(b[1][i]<p[i]<b[2][i] for i in range(3))]
            self.assertTrue(panes,f)
            self.assertFalse(any(m=='wall' and all(lo[i]<p[i]<hi[i] for i in range(3)) for _,lo,hi,m in self.boxes),f)
        for room in next(l['rooms'] for l in self.spec['levels'] if l['floor']==-1):
            a,b,c,d=room['bounds'];p=(a,(b+d)/2,1.9)
            self.assertTrue(any(is_breakable_glass(box) and all(box[1][i]<p[i]<box[2][i] for i in range(3)) for box in self.boxes))
            self.assertTrue(any(m=='wall' and lo[0]<c<hi[0] and lo[1]<b+1<hi[1] for _,lo,hi,m in self.boxes))

    def test_photo1_wall_blocks_front_and_left_doorway_is_empty_and_walkable(self):
        x,y=self.spec['west_offices']['c7'][:2]
        self.assertTrue(any(m=='wall' and lo[0]<=x<=hi[0] and lo[1]<y+1<hi[1] for _,lo,hi,m in self.physics))
        cx,cy=self.spec['minus1_finishes']['empty_wi2_door']['centre']
        route=dict(points=[[cx,cy+.7,.4],[cx,cy-.7,.4]])
        _,failures=audit_stair_routes(self.physics,[route])
        self.assertFalse(failures,failures[:5])
        self.assertFalse(any(abs(d['pivot'][0]-cx)<.6 and abs(d['pivot'][1]-cy)<.1 for d in self.spec['repair_doors']))

    def test_photo2_facade_is_opaque_and_all_six_black_door_pairs_are_fixed(self):
        self.assertFalse(any(d['id'].startswith('p2_cibio_terrace_') for d in self.spec['repair_doors']))
        leaves=[b for b in self.physics if b[0].startswith('p2_basement_fitout_terrace_closed_')]
        self.assertEqual(len(leaves),12)
        self.assertTrue(all(m=='door_black' for _,_,_,m in leaves))
        for i in range(750):
            y=18.081+i*(55.899-18.081)/749
            for z in (.6,1.9,2.9):
                self.assertTrue(any(m in ('wall','door_black') and lo[0]<-2.3<hi[0] and lo[1]-1e-6<=y<=hi[1]+1e-6 and lo[2]<=z<=hi[2]
                                    for _,lo,hi,m in self.physics),(y,z))

    def test_office_doors_passages_and_all_retained_basement_routes_stay_clear(self):
        routes=self.spec['basement_rebuild']['routes']
        _,failures=audit_stair_routes(self.physics,routes)
        self.assertFalse(failures,failures[:8])
