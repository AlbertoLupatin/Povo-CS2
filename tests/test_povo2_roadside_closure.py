"""Povo 2 roadside closure: street garden, road-edge wall and grating fence."""
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.povo2_roadside_closure import (FENCE_HEIGHT, KERB_HEIGHT, LAWNS, REMNANTS,
                                          ROAD_EDGE_RUNS, STREET_Z, footway_z)


def inside_mesh(mesh, p):
    """Point inside a convex 8-vertex prism (bottom quad then top quad)."""
    vv = mesh['vertices']
    if len(vv) != 8:
        return False
    xs = [v[0] for v in vv]; ys = [v[1] for v in vv]
    if not (min(xs) < p[0] < max(xs) and min(ys) < p[1] < max(ys)):
        return False
    # Interpolate bottom/top along the run; the prisms here slope along one axis.
    bottom, top = vv[:4], vv[4:]
    def height(quad):
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = quad
        u = (p[0] - x0) / (x1 - x0) if abs(x1 - x0) > 1e-9 else 0.
        v = (p[1] - y0) / (y3 - y0) if abs(y3 - y0) > 1e-9 else 0.
        if abs(x1 - x0) > 1e-9:
            return z0 + (z1 - z0) * u
        return z0 + (z3 - z0) * v
    return height(bottom) < p[2] < height(top)


class RoadsideClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.boxes, cls.levels, _ = build_geometry()
        cls.physics = collision_boxes(cls.boxes)
        cls.ext = cls.levels[0]['exterior']
        cls.p2 = next(l['connection']['povo2'] for l in cls.levels if l.get('connection'))

    def solid(self, p):
        return any(all(lo[i] < p[i] < hi[i] for i in range(3)) for _, lo, hi, _ in self.physics) or \
            any(inside_mesh(m, p) for m in self.ext['collision_meshes'])

    def support(self, x, y):
        tops = [hi[2] for n, lo, hi, _ in self.physics
                if '_clip_' not in n and '_post_' not in n and lo[0] < x < hi[0] and lo[1] < y < hi[1] and hi[2] < 9]
        return max(tops) if tops else None

    def test_street_garden_is_solid_lawn_at_street_level(self):
        for name, (a, b, c, d) in LAWNS.items():
            x, y = (a + c) / 2, (b + d) / 2
            garden=self.p2['gardens']['garden']
            if garden[0]<=x<=garden[2] and garden[1]<=y<=garden[3]:
                # This former roadside lawn is now the aligned sunken garden.
                self.assertLess(self.support(x,y),STREET_Z)
                continue
            self.assertAlmostEqual(self.support(x, y), STREET_Z, places=6, msg=name)
            self.assertTrue(self.solid((x, y, 0.)), name)
            self.assertTrue(any(n.startswith('p2_roadside_lawn_' + name) and m == 'exterior_grass'
                                for n, lo, hi, m in self.boxes), name)

    def test_open_minus1_roofs_are_capped_at_ground_level(self):
        for x, y in ((28., 17.), (36.5, 15.), (31.4, 5.)):
            self.assertGreaterEqual(self.support(x, y), STREET_Z - 1e-6, (x, y))

    def test_garden_and_approved_sunken_routes_stay_open(self):
        for p in ((48., 9., -1.), (40., 9., 0.), (43.8, 5., -1.6), (25., 1.1, 1.5),
                  (36., 13.5, -2.)):
            self.assertFalse(self.solid(p), p)

    def test_road_edge_wall_meets_footway_and_closes_drop(self):
        for x0, x1 in ROAD_EDGE_RUNS:
            for x in (x0 + .5, (x0 + x1) / 2, x1 - .5):
                # East of N0 corner paving (E52+) the wall starts at the paving edge.
                self.assertTrue(self.solid((x, -.4 if x < 52 else .05, footway_z(x) - .5)), x)
                self.assertTrue(self.solid((x, 0., footway_z(x) + KERB_HEIGHT - .05)), x)
        # The UP stair from the terrace to the street remains open.
        self.assertFalse(self.solid((21.75, -.3, 3.)))

    def test_fence_blocks_whole_height_on_both_roads(self):
        for x in (12., 28., 40., 49., 55.):
            z = footway_z(x) + KERB_HEIGHT
            for dz in (.3, 1., FENCE_HEIGHT - .1):
                self.assertTrue(self.solid((x, -.035, z + dz)), (x, dz))
        for y in (2., 8., 14., 22., 27.):
            barrier = [m for m in self.ext['collision_meshes'] if m['name'].startswith('exterior_p2_roadside_fence_front_barrier')
                       and min(v[1] for v in m['vertices']) <= y <= max(v[1] for v in m['vertices'])]
            self.assertTrue(barrier, y)
            top = min(max(v[2] for v in m['vertices']) for m in barrier)
            self.assertGreater(top, 4. + KERB_HEIGHT + FENCE_HEIGHT - .05, y)

    def test_fence_bars_are_visual_only_and_dense(self):
        bars = [m for m in self.ext['meshes'] if '_fence_' in m['name'] and '_bar_' in m['name']]
        self.assertGreater(len(bars), 600)
        collision = {m['name'] for m in self.ext['collision_meshes']}
        self.assertFalse(any(m['name'] in collision for m in bars))
        self.assertTrue(all(m['material'] == 'exterior_fence' for m in bars))

    def test_floating_street_ramp_remnants_are_removed(self):
        self.assertFalse(any(n.startswith(REMNANTS) for n, *_ in self.boxes))
        self.assertFalse(any(m['name'].startswith(REMNANTS) for m in self.ext['meshes']))

    def test_new_solids_do_not_enter_existing_walking_routes(self):
        new = [b for b in self.physics if b[0].startswith('p2_roadside_') and '_clip_' not in b[0]]
        routes = [*self.p2['gardens']['routes'].values(),
                  *[r['points'] for r in self.p2['basement_rebuild']['routes']]]
        for points in routes:
            for x, y, z in points:
                for dz in (.1, 1., 1.7):
                    hits = [n for n, lo, hi, _ in new if all(lo[i] < (x, y, z + dz)[i] < hi[i] for i in range(3))]
                    self.assertFalse(hits, ((x, y, z + dz), hits))


if __name__ == '__main__':
    unittest.main()
