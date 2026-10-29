"""The bus must block the road broadside and stay before the live bridge."""
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes, is_breakable_glass
from tools.povo_physics_surfaces import surface
from tools.audit_povo_exterior_integrated import audit, height_at
from tools.povo_abandoned_bus import DESTINATION, destination_mask


class AbandonedBusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.boxes, cls.levels, _ = build_geometry()
        cls.bus = [b for b in cls.boxes if b[0].startswith('exterior_abandoned_bus_')]

    def test_spans_road_and_footways_before_bridge(self):
        self.assertTrue(self.bus)
        body = next(b for b in self.bus if b[0].endswith('_chassis'))
        bridge = next(l['connection']['bridge'] for l in self.levels if l.get('connection'))
        self.assertGreater(body[1][0], bridge[2] + 2)
        self.assertLessEqual(body[1][1], -5 - 3 - 1.4)
        self.assertGreaterEqual(body[2][1], -5 + 3 + 1.4)
        self.assertAlmostEqual(body[2][0] - body[1][0], 2.5)

    def test_opposite_wall_still_blocks_each_lane(self):
        solids = collision_boxes(self.bus)
        for yy in (-7.8, -6.5, -5, -3.5, -2.2):
            for zz in (4.5, 5.4):
                self.assertTrue(any(lo[0] < 23.85 < hi[0] and lo[1] < yy < hi[1]
                                    and lo[2] < zz < hi[2] for _, lo, hi, _ in solids))
        self.assertFalse(any(is_breakable_glass(b) for b in self.bus))
        self.assertEqual(surface('exterior_bus_paint'), 'metal')

    def test_standing_player_can_enter_and_walk_the_aisle(self):
        # Sweep a CS2-sized standing hull from the street up every tread,
        # through the entrance and down the centre aisle in both directions.
        solids = collision_boxes(self.bus)
        path = [(27.5, -3.475, 4), (27.0, -3.475, 4.1625),
                (26.7, -3.475, 4.325), (26.4, -3.475, 4.4875),
                (26.1, -3.475, 4.67), (25.5, -3.475, 4.67), (25, -3.475, 4.67)]
        path += [(25, -1.825-i*.1, 4.67) for i in range(68)]
        for x, y, foot in [*path, *reversed(path)]:
            blockers = [name for name, lo, hi, _ in solids
                        if lo[0] < x+.4-1e-6 and hi[0] > x-.4+1e-6
                        and lo[1] < y+.4-1e-6 and hi[1] > y-.4+1e-6
                        and lo[2] < foot+1.85 and hi[2] > foot+.20]
            self.assertEqual(blockers, [], (x, y, foot, blockers))
            supports = [hi[2] for _, lo, hi, _ in solids
                        if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]]
            for mesh in self.levels[0]['exterior']['collision_meshes']:
                supports.extend(height_at(mesh, x, y))
            self.assertTrue(any(abs(top-foot) < .025 for top in supports), (x, y, foot, supports))

    def test_cabin_is_hollow_and_contains_abandoned_fittings(self):
        names = [b[0] for b in self.bus]
        self.assertNotIn('exterior_abandoned_bus_cabin', names)
        self.assertEqual(sum('seat_cushion_' in n for n in names), 9)
        self.assertEqual(sum('seat_exposed_foam_' in n for n in names), 2)
        self.assertEqual(sum('discarded_paper_' in n for n in names), 5)
        self.assertEqual(sum('open_door_' in n and '_glass' in n for n in names), 2)
        # Broken side panes have an open view into the hollow passenger cabin.
        for side in (-1, 1):
            for row in (1, 4):
                yy = -5-4.5+.38+row*1.18+.5
                xx = 25+side*1.25
                self.assertFalse(any(lo[0] <= xx <= hi[0] and lo[1] <= yy <= hi[1]
                                     and lo[2] < 6.1 < hi[2] for _, lo, hi, _ in self.bus))

    def test_route_audit_reports_the_intended_closure(self):
        route = next(r for r in audit()['routes'] if r['route'] == 'bridge_road_to_straight_ramp')
        self.assertEqual(route['status'], 'blocked_as_designed')
        self.assertTrue(route['expected_blockage'])
        self.assertEqual(route['failures'], [])

    def test_reference_livery_and_front_destination_are_exported(self):
        self.assertEqual(DESTINATION, '5/ Università di Povo')
        self.assertIsNotNone(destination_mask().getbbox())
        meshes = self.levels[0]['exterior']['meshes']
        lettering = [m for m in meshes if 'abandoned_bus_destination_glyph_' in m['name']]
        self.assertGreater(len(lettering), 100)
        self.assertTrue(all(m['material']=='exterior_bus_led' for m in lettering))
        self.assertTrue(all(abs(v[1] - (-.425)) < 1e-6 for m in lettering for v in m['vertices']))
        mountains = [m for m in meshes if 'abandoned_bus_mountain_' in m['name']]
        self.assertEqual(len(mountains), 15)  # One graphic falls entirely within the open doorway.


if __name__ == '__main__':
    unittest.main()
