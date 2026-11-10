"""Entrance ceiling, sign and wall corrections plus reviewed exterior fills."""
from collections import Counter
import unittest
from tools.build_povo_campus import build_geometry,collision_boxes
from tools.cs2_campus import stair_signs
from tools.povo_exterior_fills import REGIONS


class EntranceFinishesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.physics=collision_boxes(cls.boxes)
        cls.link=next(l['connection'] for l in cls.levels if l.get('connection'))
        cls.ext=cls.levels[0]['exterior']

    def containing(self,p,boxes=None):
        return [b for b in (boxes if boxes is not None else self.physics)
                if all(b[1][i]<p[i]<b[2][i] for i in range(3))]

    def test_shared_floor0_portal_has_one_readable_sign(self):
        signs=stair_signs(dict(connection=self.link,povo2=self.link['povo2']))
        nearby=[s for s in signs if abs(s['point'][0]-20.63)<.2 and abs(s['point'][1]-22)<.2 and abs(s['point'][2]-6.5)<.2]
        self.assertEqual(len(nearby),1)
        self.assertEqual(nearby[0]['text'],'SCALE / PIANO 0')
        self.assertEqual(len(signs),4)

    def test_rectangle_wall_tops_no_longer_hang_below_ceiling(self):
        for point in ((22.5,22.,6.5),(25.5,25.,6.5),(24.,19.5,6.5),(24.,29.45,6.5)):
            self.assertFalse([b for b in self.containing(point) if b[3]=='wall'],point)
        ceilings=[b for b in self.boxes if b[3]=='ceiling_panel']
        for point in ((24.,22.,7.31),(21.,16.,7.31),(24.,29.,7.31)):
            self.assertTrue(self.containing(point,ceilings),point)

    def test_registered_classroom_corridor_and_stair_door_stay_open(self):
        # The former side bay is now occupied by the registered room row.
        # Its obsolete closure must not bisect the perpendicular corridor.
        self.assertIsNone(self.link['povo2']['entrance_finishes']['closed_side_bay'])
        for x in (3.,9.,18.5,20.5,24.,29.5):
            self.assertFalse(self.containing((x,16.7,5.1)),x)
        self.assertFalse(self.containing((20.5,22.,5.1)))

    def test_upper_gap_fills_leave_lower_approach_and_garden_clear(self):
        fill=[b for b in self.physics if b[0].startswith('exterior_user_fill_')]
        self.assertTrue(fill)
        garden=self.link['povo2']['gardens']['garden']
        for name in ('B','C'):
            a,b,c,d=REGIONS[name]
            x,y=(a+c)/2,(b+d)/2
            inside=garden[0]<=x<=garden[2] and garden[1]<=y<=garden[3]
            self.assertEqual(bool(self.containing((x,y,3.9),fill)),not inside)
        for p in ((43.8,5.,-1.6),(48.,9.,-1.6),(21.75,1.,1.6)):
            self.assertFalse(self.containing(p,fill),p)

    def test_new_street_supports_are_closed_and_below_existing_paving(self):
        supports=[m for m in self.ext['meshes'] if m['name'].startswith('exterior_user_fill_d_')]
        self.assertTrue(supports)
        physical={m['name']:m for m in self.ext['collision_meshes']}
        for m in supports:
            self.assertEqual(m,physical[m['name']])
            edges=Counter(tuple(sorted((a,b))) for f in m['faces'] for a,b in zip(f,(*f[1:],f[0])))
            self.assertTrue(all(n==2 for n in edges.values()),m['name'])
            n=len(m['vertices'])//2
            self.assertTrue(all(abs(v[2]+3.42)<1e-7 for v in m['vertices'][:n]))
            self.assertTrue(all(v[2]>3. for v in m['vertices'][n:]))


if __name__=='__main__':unittest.main()
