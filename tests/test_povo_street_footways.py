"""Regressions for raised concrete across roads and the frontage slope notch."""
from collections import Counter
import json
import math
from pathlib import Path
import unittest

from tools.audit_povo_exterior_integrated import height_at, route_points
from tools.build_povo_campus import build_geometry
from tools.povo_street_footways import corners, is_street_footway

ROOT=Path(__file__).resolve().parents[1]


class StreetFootwayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,_,levels,_=build_geometry()
        cls.exterior=levels[0]['exterior']
        cls.footways=[m for m in cls.exterior['meshes'] if is_street_footway(m)]
        cls.config=json.loads((ROOT/'config/povo_exterior.json').read_text())

    def test_no_street_paving_crosses_the_carriageway(self):
        samples=0
        for key in ('road','north_road','front_road'):
            road=self.config[key]
            for a,b in zip(road['points'],road['points'][1:]):
                length=math.dist(a[:2],b[:2]);nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
                for x,y,z in route_points([a,b],step=.25):
                    for fraction in (-.9,-.5,0,.5,.9):
                        xx=x+nx*road['width']/2*fraction;yy=y+ny*road['width']/2*fraction;samples+=1
                        hits=[(m['name'],h) for m in self.footways for h in height_at(m,xx,yy)
                              if .025<h-z<.24]
                        self.assertFalse(hits,(key,(xx,yy,z),hits))
        self.assertGreater(samples,10000)

    def test_bottom_of_frontage_slope_has_visible_and_physical_paving(self):
        physical={m['name']:m for m in self.exterior['collision_meshes']}
        # These points were all in the confirmed notch in the previous package.
        for x,y in ((67.9420400304,14.4785876664),(68.7591797582,14.5724667902),
                    (69.6236232250,14.7413197446)):
            covering=[m for m in self.footways if any(abs(h-4.12)<1e-6 for h in height_at(m,x,y))]
            self.assertTrue(covering,(x,y))
            for mesh in covering:self.assertEqual(mesh,physical[mesh['name']])

    def test_new_corner_and_trimmed_collision_pieces_are_closed(self):
        physical={m['name']:m for m in self.exterior['collision_meshes']}
        checked=0
        for mesh in self.footways:
            if '_corner_' not in mesh['name'] and '_roadcut_' not in mesh['name']:continue
            self.assertEqual(mesh,physical[mesh['name']])
            # The later approved garden excavation deliberately clips surfaces
            # and duplicates vertex indices; it has its own clearance checks.
            if mesh.get('surface_clipped'):continue
            edges=Counter(tuple(sorted((a,b))) for face in mesh['faces']
                          for a,b in zip(face,(*face[1:],face[0])))
            self.assertTrue(all(n==2 for n in edges.values()),mesh['name'])
            for face in mesh['faces']:
                a,b,c=[mesh['vertices'][i] for i in face]
                u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
                cross=[u[(i+1)%3]*v[(i+2)%3]-u[(i+2)%3]*v[(i+1)%3] for i in range(3)]
                self.assertGreater(sum(n*n for n in cross),1e-18,(mesh['name'],face))
            checked+=1
        self.assertGreater(checked,20)

    def test_left_and_right_sloped_turns_join_the_strip_end_elevations(self):
        for direction in (-1,1):
            road=dict(width=6,footway_width=1.4,points=[(-12,0,6),(0,0,3),(0,direction*12,3)])
            meshes=list(corners('test',road));self.assertTrue(meshes)
            self.assertTrue(all(abs(p[2]-3.12)<1e-8 for m in meshes for p in m['vertices'][len(m['vertices'])//2:]))
            for x,y in ((0,-direction*3.7),(3.7,0)):
                self.assertTrue(any(height_at(m,x,y) for m in meshes),(direction,x,y))
            for point in ((-3.7,0),(0,direction*3.7)):
                self.assertFalse(any(height_at(m,*point) for m in meshes),(direction,point))


if __name__=='__main__':unittest.main()
