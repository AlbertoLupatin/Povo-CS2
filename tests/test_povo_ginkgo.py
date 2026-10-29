"""Roadside planting scale, complete replacement and permeable crowns."""
import math
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.povo_ginkgo import tree


class GinkgoTests(unittest.TestCase):
    def test_scale_is_measured_from_each_planting_point(self):
        for height in (2.5, 2.65, 2.8, 2.95, 3.0):
            trunk, meshes, record = tree('scale', 59, -105, 7.6, height)
            points = [v for m in meshes for v in m['vertices']]
            self.assertAlmostEqual(min(v[2] for v in points), 7.6)
            self.assertAlmostEqual(max(v[2] for v in points)-7.6, height)
            self.assertLess(trunk[2][0]-trunk[1][0], .12)
            for m in meshes:
                for a, b, c in m['faces']:
                    u, v, w = [m['vertices'][i] for i in (a, b, c)]
                    ab = [v[i]-u[i] for i in range(3)]; ac = [w[i]-u[i] for i in range(3)]
                    area = sum((ab[(i+1)%3]*ac[(i+2)%3]-ab[(i+2)%3]*ac[(i+1)%3])**2 for i in range(3))
                    self.assertGreater(area, 1e-16)
                    self.assertTrue(all(math.isfinite(n) for p in (u, v, w) for n in p))

    def test_rebuilds_keep_the_same_tree_shapes(self):
        self.assertEqual(tree('front_0', 1, 2, 3), tree('front_0', 1, 2, 3))
        with self.assertRaises(ValueError):
            tree('too_tall', 0, 0, 0, 6)

    def test_every_roadside_tree_is_replaced_without_reinstating_removed_trees(self):
        _, _, boxes, levels, _ = build_geometry()
        exterior = levels[0]['exterior']; records = exterior['roadside_trees']
        # 8 on each frontage, 7 west, 5 bridge road, 5 library road garden.
        self.assertEqual(len(records), 33)
        names = {t['name'] for t in records}
        self.assertEqual(len(names), len(records))
        self.assertNotIn('exterior_road_tree_5', names)
        self.assertNotIn('exterior_road_tree_6', names)
        self.assertTrue(all(t['species'] == 'Ginkgo biloba' and 2.5 <= t['height_metres'] <= 3 for t in records))
        physics = collision_boxes(boxes)
        for record in records:
            name = record['name']
            colliders = [b[0] for b in physics if b[0].startswith(name+'_')]
            self.assertTrue(colliders)
            self.assertTrue(all(n.startswith(name+'_trunk') for n in colliders))
            self.assertFalse(any(m['name'].startswith(name+'_') for m in exterior['collision_meshes']))
            self.assertFalse(any(b[0].startswith(name+'_') and b[3] == 'exterior_tree' for b in boxes))
            crown = [m for m in exterior['meshes'] if m['name'].startswith(name+'_fans_')]
            self.assertEqual(len(crown), 3)
            self.assertEqual(sum(len(m['faces']) for m in crown), 390*8)


if __name__ == '__main__':
    unittest.main()
