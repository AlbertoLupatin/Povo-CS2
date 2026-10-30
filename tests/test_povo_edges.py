"""Outer scenery must preserve gameplay and retain traceable reference evidence."""
import hashlib
import math
import unittest
from unittest.mock import patch

from tools.povo_edges import ROOT,build,triangulate
from tools.build_povo_campus import build_geometry,collision_boxes


class PovoEdgeTests(unittest.TestCase):
    def test_concave_landscape_triangulation_preserves_area(self):
        points=[(0,0),(5,0),(5,2),(2,2),(2,5),(0,5)]
        triangles=triangulate(points)
        area=sum(((points[b][0]-points[a][0])*(points[c][1]-points[a][1])-
                  (points[b][1]-points[a][1])*(points[c][0]-points[a][0]))/2 for a,b,c in triangles)
        self.assertAlmostEqual(area,16)
        self.assertEqual(len(triangles),len(points)-2)

    def test_finite_nondegenerate_triangles_and_unique_names(self):
        meshes,_=build()
        self.assertEqual(len(meshes),len({m['name'] for m in meshes}))
        for m in meshes:
            for v in m['vertices']:self.assertTrue(all(math.isfinite(x) for x in v),m['name'])
            for a,b,c in m['faces']:
                p,q,r=[m['vertices'][i] for i in (a,b,c)]
                u=[q[i]-p[i] for i in range(3)];v=[r[i]-p[i] for i in range(3)]
                cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                self.assertGreater(sum(x*x for x in cross),1e-14,m['name'])

    def test_aerial_and_original_photos_are_hashed(self):
        _,meta=build()
        self.assertEqual(len(meta['photos']),3)
        for path,digest in meta['input_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        self.assertEqual(meta['config']['origin'],[666250,5103800,370])
        self.assertEqual(meta['collision_meshes'],0)

    def test_integrated_scenery_preserves_collision_routes_and_bounds(self):
        combined=build_geometry()
        with patch('tools.povo_edges.extend'):
            original=build_geometry()
        self.assertEqual(collision_boxes(combined[2]),collision_boxes(original[2]))
        after,before=combined[3][0]['exterior'],original[3][0]['exterior']
        self.assertEqual(after['collision_meshes'],before['collision_meshes'])
        self.assertEqual(after['bounds'],before['bounds'])
        self.assertEqual([m for m in after['meshes'] if not m['name'].startswith('exterior_edges_')],before['meshes'])
        self.assertGreater(after['edges']['visual_meshes'],100)

    def test_road_continuations_meet_existing_campus_endpoints(self):
        _,meta=build();roads={r['id']:r for r in meta['config']['roads']}
        self.assertEqual(roads['north_roundabout_approach']['points'][0],[62,120,4])
        self.assertEqual(roads['south_sommarive']['points'][0],[62,-116,7.6])
        self.assertEqual(roads['west_lane']['points'][0],[-48,-101,3])


if __name__=='__main__':unittest.main()
