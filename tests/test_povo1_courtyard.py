"""Povo 1 courtyard from the 28 October review of photos 5-10, 19, 22-30."""
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.povo1_courtyard_stair import (DOOR, EAST, FLIGHT_TREADS, LANDING_EDGE, LIFT_SPAN, PLANTERS,
                                         PLANTER_SIZE, TERRACE_DOORS, WEST)


def overlaps(lo, hi, a, b):
    return all(lo[i] < b[i] and hi[i] > a[i] for i in range(3))


class CourtyardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.boxes, cls.levels, cls.stair = build_geometry()
        cls.physics = collision_boxes(cls.boxes)
        cls.zs = [l['floor_elevation_metres']-370 for l in cls.levels]
        cls.walls = [l['voids_local_metres'][0][1] for l in cls.levels]

    def test_one_door_per_floor_at_the_same_plan_point(self):
        for z, wall in zip(self.zs, self.walls):
            a, b = (DOOR[0]+.05, wall-.3, z+.1), (DOOR[1]-.05, wall+.3, z+2.1)
            blocking = [n for n, lo, hi, m in self.physics if overlaps(lo, hi, a, b)]
            self.assertFalse(blocking, (z, blocking))

    def test_landings_stack_one_above_the_other(self):
        landings = [(lo, hi) for n, lo, hi, m in self.boxes
                    if n.startswith('p1_courtyard_stair_') and n.endswith('_landing')]
        self.assertEqual(len(landings), 2)
        self.assertEqual({(lo[0], hi[0], hi[1]) for lo, hi in landings}, {(WEST, EAST, LANDING_EDGE)})
        self.assertEqual(sorted(hi[2] for _, hi in landings), self.zs[1:])

    def test_treads_and_landings_are_steel_grating(self):
        walking = [m for n, lo, hi, m in self.boxes if n.startswith('p1_courtyard_stair_')
                   and any(t in n for t in ('_up_', '_down_', '_turn', '_landing'))
                   and not any(t in n for t in ('_post_', '_clip_', '_outer', '_well', '_finish_'))]
        self.assertEqual(len(walking), 2*(2*FLIGHT_TREADS+1)+2)
        self.assertEqual(set(walking), {'floor_grating'})

    def test_south_end_follows_fire_plan_19(self):
        rooms = {r['id']: r for r in self.levels[1]['rooms']}
        order = ['f_south_west', 'f_south_centre', 'f_south_coffee', 'f_south_centre_female']
        spans = [rooms[i]['footprint_local_metres'] for i in order]
        for left, right in zip(spans, spans[1:]):
            self.assertAlmostEqual(left[2], right[0], places=6)
        self.assertEqual([rooms[i]['kind'] for i in order], ['restroom', 'office', 'service', 'restroom'])
        tables = [n for n, *_ in self.boxes if n.startswith('academic_first_f_south_centre_table_') and n.endswith('_top')]
        self.assertEqual(len(tables), 2)
        coffee = spans[2]
        self.assertAlmostEqual(coffee[2]-coffee[0], 5.3, delta=.1)
        self.assertTrue(coffee[0] < DOOR[0] and DOOR[1] < coffee[2])
        # The stair stands on the courtyard's centre line (plan 19: 3.1 m wide).
        court = self.levels[1]['voids_local_metres'][0]
        self.assertAlmostEqual((WEST+EAST)/2, (court[0]+court[2])/2, delta=.2)
        self.assertAlmostEqual(EAST-WEST, 3.1, places=6)

    def test_coffee_area_is_furnished_from_the_28_october_photos(self):
        prefix = 'academic_first_f_south_coffee_'
        names = [n[len(prefix):] for n, *_ in self.boxes if n.startswith(prefix)]
        self.assertEqual(sum(n.startswith('vending_') and '_finish_' not in n for n in names), 6)
        self.assertEqual(sum(n.startswith('recycling_bin_') for n in names), 4)
        self.assertEqual(sum(n.endswith('_top') for n in names), 2)
        # A standing player walks from the corridor door to the stair door.
        room = next(r for r in self.levels[1]['rooms'] if r['id'] == 'f_south_coffee')
        a, b, c, d = room['footprint_local_metres']
        door = a+(c-a)*room['door_fraction']; stair = sum(DOOR)/2; z = self.zs[1]
        for (x0, y0), (x1, y1) in (((door, b+.3), (door, d-1)), ((door, d-1), (stair, d-1)), ((stair, d-1), (stair, d-.3))):
            lo = (min(x0, x1)-.4, min(y0, y1)-.4, z+.05); hi = (max(x0, x1)+.4, max(y0, y1)+.4, z+1.85)
            blocking = [n for n, l, h, m in self.physics if n.startswith(prefix) and overlaps(l, h, lo, hi)]
            self.assertFalse(blocking)

    def test_terraces_are_open_to_the_sky_and_paved(self):
        z = self.zs[-1]
        terraces = self.stair['courtyard']['terraces']
        y0, y1 = terraces['y']
        for side in ('west', 'east'):
            a, b = terraces[side]
            covers = [n for n, lo, hi, m in self.boxes if lo[2] > z+.5 and m == 'ceiling_panel'
                      and overlaps(lo, hi, (a+.1, y0+.1, z), (b-.1, y1-.1, z+5))]
            self.assertFalse(covers, side)
            floors = {m for n, lo, hi, m in self.boxes if n.startswith(f'academic_upper_{side}_terrace_0')}
            self.assertEqual(floors, {'floor_terrace'})

    def test_terraces_are_glazed_from_the_corridors_with_plan_22_doors(self):
        z = self.zs[-1]
        terraces = self.stair['courtyard']['terraces']
        y0, y1 = terraces['y']
        for side, x in (('west', terraces['west'][0]), ('east', terraces['east'][1])):
            doors = TERRACE_DOORS[side]
            for i in range(1, 60):
                y = y0+(y1-y0)*i/60
                if x > 0 and LIFT_SPAN[0]-.1 <= y <= LIFT_SPAN[1]+.1:
                    continue  # the enclosed lift shaft is the wall here
                if any(a-.1 <= y <= b+.1 for a, b in doors):
                    continue
                solid = [m for n, lo, hi, m in self.physics if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]
                         and lo[2] <= z+1.5 <= hi[2]]
                self.assertTrue(solid, (x, y))
            # A standing player walks from the corridor through each doorway onto the terrace.
            for a, b in doors:
                lo, hi = (x-1.0, a+.1, z+.05), (x+1.0, b-.1, z+1.85)
                blocking = [n for n, l, h, m in self.physics if overlaps(l, h, lo, hi)]
                self.assertFalse(blocking, (side, a, b, blocking))
                for dx in (-.8, .8):
                    floor = [n for n, l, h, m in self.physics if l[0] <= x+dx <= h[0] and l[1] <= (a+b)/2 <= h[1]
                             and abs(h[2]-z) < .05]
                    self.assertTrue(floor, (side, a, dx))
        self.assertEqual(terraces['doors'], {s: [list(d) for d in v] for s, v in TERRACE_DOORS.items()})
        panes = [n for n, lo, hi, m in self.boxes if n.startswith('p1_courtyard_terrace_') and m == 'window_glass']
        self.assertGreater(len(panes), 20)

    def test_courtyard_drop_is_guarded_by_railings(self):
        z = self.zs[-1]
        terraces = self.stair['courtyard']['terraces']
        y0, y1 = terraces['y']
        for x in (self.levels[-1]['voids_local_metres'][0][0]-.1, self.levels[-1]['voids_local_metres'][0][2]+.1):
            for i in range(1, 20):
                y = y0+.2+(y1-y0-.4)*i/20
                guard = [n for n, lo, hi, m in self.physics if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]
                         and lo[2] <= z+.9 <= hi[2]]
                self.assertTrue(guard, (x, y))

    def test_planters_stand_on_the_lower_court_clear_of_the_stair(self):
        court = self.levels[0]['voids_local_metres'][0]
        bounds = self.stair['courtyard']['bounds']
        half = PLANTER_SIZE/2
        for x, y in PLANTERS:
            self.assertTrue(court[0] < x-half and x+half < court[2] and court[1] < y-half and y+half < court[3])
            self.assertFalse(x+half > bounds[0] and x-half < bounds[2] and y+half > bounds[1] and y-half < bounds[3])
        names = {n for n, *_ in self.physics}
        self.assertIn('p1_courtyard_planter_0_trunk', names)
        self.assertNotIn('p1_courtyard_planter_0_canopy_low', names)


if __name__ == '__main__':
    unittest.main()
