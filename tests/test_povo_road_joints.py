"""Road junction disks must not stand above the sloping road next to them."""
import json
import math
import unittest
from pathlib import Path

from tools.build_povo_campus import build_geometry
from tools.build_povo_exterior import LEDGE_METRES, joint

ROOT = Path(__file__).resolve().parents[1]


def surface(q, a, b):
    """(distance, road height) of the segment a-b nearest to q."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(q[0] - a[0] - t * dx, q[1] - a[1] - t * dy), a[2] + t * (b[2] - a[2])


class RoadJointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ext = build_geometry(ROOT)[3][0]['exterior']
        cls.physics = {m['name']: m for m in ext['collision_meshes']}
        cls.config = json.loads((ROOT / 'config/povo_exterior.json').read_text())

    def test_no_joint_collider_is_a_ledge_over_the_road(self):
        checked = 0
        for prefix, key in (('exterior_road', 'road'), ('exterior_road_north', 'north_road'),
                            ('exterior_road_front', 'front_road')):
            points = self.config[key]['points']
            for i, (a, p, b) in enumerate(zip(points, points[1:], points[2:])):
                mesh = self.physics.get(f'{prefix}_joint_{i}')
                if mesh is None:
                    continue            # split by a later excavation (road_joint_1)
                top = mesh['vertices'][len(mesh['vertices']) // 2:]
                worst = max(q[2] - min(surface(q, a, p), surface(q, p, b))[1] for q in top)
                self.assertLessEqual(worst, LEDGE_METRES, mesh['name'])
                checked += 1
        self.assertGreaterEqual(checked, 15)

    def test_via_sommarive_crest_is_cut_at_the_downhill_segment(self):
        # Formerly a flat 3.5 m disk 0.82 m above the descending street (TODO, 2 November).
        mesh = self.physics['exterior_road_front_joint_0']
        top = mesh['vertices'][len(mesh['vertices']) // 2:]
        a, p, b = self.config['front_road']['points'][:3]
        self.assertTrue(all((q[0] - p[0]) * (b[0] - p[0]) + (q[1] - p[1]) * (b[1] - p[1]) <= 1e-6 for q in top))
        self.assertTrue(all(abs(q[2] - (p[2] + .002)) < 1e-9 for q in top))
        # The outside of the bend (west, between both strip ends) stays filled.
        self.assertTrue(any(q[0] < p[0] - 3.4 and q[1] > 0 for q in top))

    def test_level_and_gentle_joints_keep_the_full_disk(self):
        flat = joint('j', (0, -10, 1), (0, 0, 1), (5, 10, 1), 3)
        gentle = joint('j', (32, -5, 4), (22, -5, 4), (-23, -5, 3), 3)   # 6.7 cm lip, by Povo 2's entrance
        for mesh in (flat, gentle):
            self.assertEqual(len(mesh['vertices']), 17)
            self.assertEqual(mesh['faces'], [(0, k + 1, (k + 1) % 16 + 1) for k in range(16)])

    def test_cut_joint_fan_is_upward_and_nondegenerate(self):
        mesh = joint('j', (62, -116, 7.6), (62, 0, 7.6), (64.4, 15, 4), 3.5)
        for f in mesh['faces']:
            p, q, r = (mesh['vertices'][i] for i in f)
            self.assertGreater((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]), 1e-6)


if __name__ == '__main__':
    unittest.main()
