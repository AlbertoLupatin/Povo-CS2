"""Traversal regressions from the 26 October playtest screenshots."""
import math
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes, render_obj
from tools.audit_povo_exterior_integrated import height_at


class PlaytestCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,cls.stair=build_geometry()
        cls.physics=collision_boxes(cls.boxes)

    def test_street_gap_has_full_width_support_and_connector_matches_road(self):
        exterior=self.levels[0]['exterior']
        meshes=exterior['collision_meshes']
        for x in (52.45,54.5,56.25):
            for step in range(53):
                y=-13+step*.25
                heights=[hi[2] for _,lo,hi,_ in self.physics
                         if lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]]
                heights.extend(h for mesh in meshes for h in height_at(mesh,x,y))
                self.assertTrue(any(abs(h-7.6)<.02 for h in heights),(x,y,heights))
        connector=next(m for m in meshes if m['name']=='exterior_road_front_link')
        self.assertAlmostEqual(max(v[2] for v in connector['vertices']),7.6)

    def test_stair_runs_are_supported_between_waypoints_with_standing_headroom(self):
        link=next(l['connection'] for l in self.levels if 'connection' in l)
        routes=[[link['stair']['top'],*link['stair']['path'],link['stair']['bottom']],
                *[r['points'] for r in link['povo2']['stairs']['path']]]
        core=[b for b in self.physics if b[1][0]<21 and b[2][0]>10
              and b[1][1]<27 and b[2][1]>13]
        for route in routes:
            for start,end in zip(route,route[1:]):
                for i in range(max(1,math.ceil(math.dist(start,end)/.08))):
                    n=max(1,math.ceil(math.dist(start,end)/.08))
                    x,y,z=[a+(b-a)*i/n for a,b in zip(start,end)]
                    # At a riser edge the standing hull is still supported by
                    # the higher tread under its footprint, not the lower tread
                    # beneath its centre. Use the actual upper riser envelope.
                    support=[hi[2] for _,lo,hi,m in core if m.startswith('floor_')
                             and lo[0]<x+.4 and hi[0]>x-.4 and lo[1]<y+.4 and hi[1]>y-.4
                             and abs(hi[2]-z)<max(.23,link['stair']['rise']+.02)]
                    self.assertTrue(support,(x,y,z))
                    foot=max(support)
                    blockers=[name for name,lo,hi,_ in core if lo[0]<x+.40 and hi[0]>x-.40
                              and lo[1]<y+.40 and hi[1]>y-.40 and lo[2]<foot+1.85 and hi[2]>foot+.37]
                    self.assertFalse(blockers,((x,y,z),blockers))

    def test_povo1_all_three_floors_have_supported_corner_and_courtyard_stair_routes(self):
        self.assertEqual([l['user_floor'] for l in self.levels],[-1,0,1])
        routes=[core['path'] for segment in self.stair['segments'] for core in segment['cores']]
        routes += [segment['path'] for segment in self.stair['courtyard']['segments']]
        self.assertEqual(len(routes),10)
        for route in routes:
            for start,end in zip(route,route[1:]):
                n=max(1,math.ceil(math.dist(start,end)/.08))
                for i in range(n+1):
                    x,y,z=[a+(b-a)*i/n for a,b in zip(start,end)]
                    support=[hi[2] for _,lo,hi,m in self.physics
                             if (m.startswith('floor_') or m in ('stair_red','metal_dark','courtyard_ground'))
                             and lo[0]-.001<=x<=hi[0]+.001 and lo[1]-.001<=y<=hi[1]+.001
                             and abs(hi[2]-z)<.23]
                    self.assertTrue(support,(x,y,z))
                    foot=max(support)
                    blockers=[name for name,lo,hi,_ in self.physics
                              if lo[0]<x+.4 and hi[0]>x-.4 and lo[1]<y+.4 and hi[1]>y-.4
                              and lo[2]<foot+1.85 and hi[2]>foot+.37]
                    self.assertFalse(blockers,((x,y,z),blockers))

    def test_both_ladders_extend_far_enough_above_the_upper_dismount(self):
        ladders=[self.levels[0]['elevator']['ladder'],
                 next(l['connection'] for l in self.levels if 'connection' in l)['povo2']['lift']['ladder']]
        for lo,hi in ladders:
            self.assertGreaterEqual(hi[2],11.2+1.6)
            axis=min(range(2),key=lambda j:hi[j]-lo[j])
            centre=[(a+b)/2 for a,b in zip(lo,hi)]
            centre[axis]=hi[axis]+.4072
            foot=11.2+.25
            blockers=[name for name,a,b,_ in self.physics
                      if all(a[j]<centre[j]+.41 and b[j]>centre[j]-.41 for j in range(2))
                      and a[2]<foot+1.85 and b[2]>foot+.02]
            self.assertFalse(blockers,blockers)

    def test_classroom_end_and_lobby_window_cuts_export_valid_faces(self):
        # The last classroom wall and lobby meet at decimal boundaries that
        # previously left an ulp-wide strip, collapsing into a zero-area face.
        boxes=[b for b in self.boxes if b[0].startswith(('p2_ground_b114_',
                                                     'p2_ground_aula_lobby_'))]
        obj=render_obj(boxes,[])
        faces=[line.split()[1:] for line in obj.splitlines() if line.startswith('f ')]
        self.assertTrue(faces)
        self.assertTrue(all(len({ref.split('/')[0] for ref in face})==3 for face in faces))


if __name__=='__main__':unittest.main()
