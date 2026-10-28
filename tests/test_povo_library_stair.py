"""Library stair, sloping grass and street wall from the 28 October review."""
import math
import unittest

from tools.audit_povo_exterior_integrated import height_at
from tools.build_povo_campus import build_geometry, collision_boxes
from tools.povo_library_stair import CROSSWALK_EAST, GRASS_Y, TOP_X, grass_z, sidewalk_z


class LibraryStairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, boxes, cls.levels, _ = build_geometry()
        cls.physics = collision_boxes(boxes)
        cls.meshes = cls.levels[0]['exterior']['collision_meshes']

    def support(self, x, y, z):
        heights = [hi[2] for _, lo, hi, m in self.physics
                   if lo[0]-.001 <= x <= hi[0]+.001 and lo[1]-.001 <= y <= hi[1]+.001 and abs(hi[2]-z) < .23]
        heights += [h for m in self.meshes for h in height_at(m, x, y) if abs(h-z) < .23]
        return max(heights) if heights else None

    def walk(self, route):
        for start, end in zip(route, route[1:]):
            n = max(1, math.ceil(math.dist(start, end)/.08))
            for i in range(n+1):
                x, y, z = [a+(b-a)*i/n for a, b in zip(start, end)]
                foot = self.support(x, y, z)
                self.assertIsNotNone(foot, (x, y, z))
                blockers = [name for name, lo, hi, _ in self.physics
                            if lo[0] < x+.4 and hi[0] > x-.4 and lo[1] < y+.4 and hi[1] > y-.4
                            and lo[2] < foot+1.85 and hi[2] > foot+.37]
                self.assertFalse(blockers, ((x, y, z), blockers))

    def solid(self, x, y, z):
        return [n for n, lo, hi, _ in self.physics if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and lo[2] <= z <= hi[2]]

    def test_stair_runs_the_whole_library_side_from_courtyard_to_street(self):
        spec = self.levels[0]['library_stair']
        self.assertEqual(spec['x'], [36.0, 52.0])
        self.assertLessEqual(spec['rise_metres'], .15)
        y = sum(spec['stair_y'])/2
        self.walk([(30, y, 4.0), (35.8, y, 4.0), (36.1, y, 4.12), (51.9, y, 7.6), (54, y, 7.6)])

    def test_grass_rises_from_the_courtyard_to_a_fenced_top(self):
        self.walk([(26, -11.0, 4.0), (35.9, -11.0, 4.0), (51.4, -11.0, grass_z(51.4))])
        self.assertTrue(self.solid(TOP_X-.05, -10.5, grass_z(TOP_X)+.6))

    def test_railing_separates_grass_and_stair(self):
        for i in range(1, 30):
            x = 36+16*i/30
            self.assertTrue(self.solid(x, GRASS_Y[0], grass_z(x)+.6), x)

    def test_fence_east_of_the_crosswalk_low_edge_west_of_it(self):
        for x in (46.0, 48.0, 50.0, 51.5):
            self.assertTrue(self.solid(x, -9.5, sidewalk_z(x)+.6), x)
        for x in (33.0, 38.0, 42.0):
            self.assertTrue(self.solid(x, -9.5, sidewalk_z(x)-.1), x)
            self.assertFalse(self.solid(x, -9.5, sidewalk_z(x)+.6), x)
        self.assertLess(CROSSWALK_EAST, TOP_X)


if __name__ == '__main__':
    unittest.main()
