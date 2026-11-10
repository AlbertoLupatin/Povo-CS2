"""The room row occupies the facade-to-core band, with usable circulation."""
import unittest
from tools.build_povo_campus import build_geometry,collision_boxes
from tools.audit_povo2_integrated import audit_stair_routes

class GroundRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,_=build_geometry()
        cls.p=next(l['connection']['povo2'] for l in levels if l.get('connection'))
        cls.physics=collision_boxes(cls.boxes)

    def test_rooms_fit_behind_facade_without_moving_core_or_reception(self):
        p=self.p;g=next(l for l in p['levels'] if l['floor']==0)
        rooms={r['id']:r for r in g['rooms']}
        for name in ('b106','b108','b109'):
            a,b,c,d=rooms[name]['bounds']
            self.assertAlmostEqual(b,10.8)
            self.assertGreaterEqual(d-b,4.5)
            self.assertLess(d,18.)
        self.assertEqual(p['stairs']['well_bounds'],[11,18,20.5,26])
        self.assertEqual(p['ground']['reception'],[12.5,26,20.5,35.5])
        self.assertGreater(rooms['b106']['bounds'][0],rooms['b108']['bounds'][0])
        self.assertGreater(rooms['b108']['bounds'][0],rooms['b109']['bounds'][0])

    def test_reception_stair_and_every_room_door_connected_both_directions(self):
        paths=[]
        for x in (29.5,18.5,9.):
            path=[[24.,28.,4.],[24.,22.,4.],[24.,16.7,4.],[x,16.7,4.],[x,14.8,4.]]
            paths.extend([dict(points=path),dict(points=path[::-1])])
        paths.append(dict(points=[[24.,22.,4.],[19.2,22.,4.]]))
        n,fail=audit_stair_routes(self.physics,paths)
        self.assertGreater(n,400)
        self.assertFalse(fail,fail[:5])

    def test_no_room_or_corridor_extension_remains_under_bridge(self):
        for name,lo,hi,_ in self.boxes:
            if name.startswith(('p2_ground_b106_','p2_ground_b108_','p2_ground_b109_',
                                'p2_ground_left_extension_')):
                self.assertGreaterEqual(lo[1],10.69,name)
