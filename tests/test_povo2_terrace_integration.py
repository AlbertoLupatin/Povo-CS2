"""Checks against the final campus assembly used by the Windows build."""
import unittest

from tools.audit_povo_exterior_integrated import height_at, standing
from tools.build_povo_campus import build_registered_geometry, collision_boxes
from tools.povo2_levels import NEW as LEVELS, remap_z

M1 = LEVELS[-1]  # Povo 2 -1 office threshold (was 0.4)


class RegisteredTerraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, boxes, levels, _ = build_registered_geometry()
        cls.boxes = collision_boxes(boxes)
        cls.ext = levels[0]['exterior']
        cls.meshes = cls.ext['collision_meshes']
        cls.terrace = cls.ext['terrace_integration']
        cls.p2 = next(l['connection']['povo2'] for l in levels if 'connection' in l)

    def assert_walkable(self, x, y, z, delta=None):
        foot, obstacles = standing(x, y, z, self.boxes, self.meshes)
        self.assertIsNotNone(foot, (x, y, z))
        if delta is None:
            self.assertAlmostEqual(foot, z, places=5, msg=(x, y, z))
        else:
            self.assertAlmostEqual(foot, z, delta=delta, msg=(x, y, z))
        self.assertFalse(obstacles, (x, y, z, obstacles))

    def test_south_extension_connects_to_the_approved_terrace(self):
        approved = self.p2['drawio_entrance']['areas']['terrace']
        extension = self.terrace['slabs']['south_run']
        self.assertEqual(extension[1:], [approved[1], approved[0], approved[3]])
        for i in range(-98, 54):
            self.assert_walkable(i / 4, (approved[1] + approved[3]) / 2, M1)

    def test_both_decks_are_at_the_office_threshold_below_the_sidewalks(self):
        for x in (-24.5, -19., -10., 0., 7.5):
            for y in (5., 6.5, 8.5, 9.5):
                self.assert_walkable(x, y, M1)
        for x in (-32.7, -29., -27.):
            for y in (31., 48., 74., 101., 108.):
                self.assert_walkable(x, y, M1)
        for y in (31., 48., 74., 101.):
            self.assert_walkable(-34.3, y, 3.12)

    def test_west_lightwells_have_no_context_slab_or_roof(self):
        self.assertEqual(len(self.terrace['holes']), 2)
        for west, south, east, north in self.terrace['holes']:
            for x in (west + .25, (west + east) / 2, east - .25):
                for y in (south + .3, (south + north) / 2, north - .3):
                    blockers = [name for name, lo, hi, _ in self.boxes
                                if lo[0] < x < hi[0] and lo[1] < y < hi[1]
                                and lo[2] < remap_z(3.5) and hi[2] > remap_z(.16)]
                    self.assertFalse(blockers, (x, y, blockers))
        for name, (west, south, east, north) in self.terrace['slabs'].items():
            if name.startswith(('west_strip_', 'recess_')):
                self.assert_walkable((west + east) / 2, (south + north) / 2, M1)

    def test_west_terrace_joins_the_garage_deck_and_bays(self):
        for i in range(10, 134):
            self.assert_walkable(-24.6, i / 4 + 7.5, M1)
        slabs = self.terrace['slabs']
        for name in ('west_near_bay_join', 'west_far_bay_join'):
            _, south, _, north = slabs[name]
            for i in range(-111, -86):
                self.assert_walkable(i / 4, (south + north) / 2, M1)
        # Stay a full player hull north of the lightwell's end guard.
        for i in range(442, 452):
            self.assert_walkable(-24.6, i / 4, M1)
        for y in (32., 40., 86., 95.):
            for i in range(-111, -96):
                self.assert_walkable(i / 4, y, M1)

    def test_cibio_aprons_are_flush_and_the_old_context_is_clear_of_the_glass(self):
        for a, b in ((26.88, 35.3), (65.3, 73.3)):
            for y in (a+.6, (a+b)/2, b-.6):
                self.assert_walkable(-15.2, y, M1)
                self.assertFalse(any(n.startswith(('exterior_ground', 'exterior_garage_roof'))
                                     and lo[0] < -13.9 < hi[0] and lo[1] < y < hi[1]
                                     and hi[2] > M1 and lo[2] < remap_z(3.35)
                                     for n, lo, hi, _ in self.boxes))

    def test_driveway_ramp_and_portal_have_standing_clearance(self):
        for x in (-31.1, -29., -26.9):
            for i in range(-10, 125):
                y = i / 4
                # Same road junction; the ramp now ends at the re-levelled -2.
                z = 3. if y <= 1 else max(LEVELS[-2], 3 - (3 - LEVELS[-2]) * (y - 1) / 29)
                # The road junction meets the LiDAR-regraded south road, whose
                # fade tilts the shared road triangles by about a millimetre here.
                self.assert_walkable(x, y, z, delta=.005 if y <= 1 else None)
        for mesh in self.meshes:
            if mesh['material'] == 'exterior_paving':
                self.assertFalse(height_at(mesh, -29., -.5), mesh['name'])

    def test_north_stair_opens_onto_a_mirrored_sunken_garden(self):
        south_garden = self.p2['gardens']
        south = south_garden['garden']
        north = self.terrace['north_garden']
        self.assertEqual(south[::2], north[::2])
        self.assertAlmostEqual(south[3] - south[1], north[3] - north[1])
        reflection = south[1] + north[3]
        for original, reflected in zip(south_garden['routes']['down'],
                                       self.terrace['north_routes']['down'], strict=True):
            self.assertAlmostEqual(original[1] + reflected[1], reflection)
            self.assertEqual(original[::2], reflected[::2])
            self.assert_walkable(*reflected)
        for point in self.terrace['north_routes']['garden']:
            self.assert_walkable(*point)


if __name__ == '__main__':
    unittest.main()
