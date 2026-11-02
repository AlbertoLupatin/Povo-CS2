from collections import Counter
import unittest
from tools.build_povo_exterior import strip
from tools.solid_mesh import subtract
from tools.povo2_interiors import mesh_intersects_box


class SolidMeshTests(unittest.TestCase):
    def test_shaft_removes_only_its_volume_and_every_piece_remains_closed(self):
        source=strip('road',(2,0,4),(2,4,4),4,'asphalt',4)
        pieces=subtract(source,((1,1,-1),(3,3,5)))
        volume=0
        for m in pieces:
            edges=Counter(tuple(sorted((a,b))) for f in m['faces'] for a,b in zip(f,(*f[1:],f[0])))
            self.assertTrue(all(n==2 for n in edges.values()),edges)
            self.assertFalse(mesh_intersects_box(m,((1.2,1.2,1),(2.8,2.8,3))))
            for f in m['faces']:
                a,b,c=[m['vertices'][i] for i in f]
                volume+=sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))/6
        self.assertAlmostEqual(volume,48.)

    def test_no_intersection_preserves_original_mesh(self):
        source=strip('road',(2,0,4),(2,4,4),4,'asphalt',.16)
        self.assertEqual(subtract(source,((5,5,0),(6,6,8))),[source])
