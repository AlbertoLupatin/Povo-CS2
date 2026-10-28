"""Povo 1 courtyard from the 28 October review of photos 5-10, 19, 22-30."""
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes
from tools.povo1_courtyard_stair import DOOR, EAST, LIFT_SPAN, PLANTERS, PLANTER_SIZE, WEST


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
        self.assertEqual({(lo[0], hi[0], hi[1]) for lo, hi in landings}, {(WEST, EAST, -74.3)})
        self.assertEqual(sorted(hi[2] for _, hi in landings), self.zs[1:])

    def test_treads_and_landings_are_steel_grating(self):
        walking = [m for n, lo, hi, m in self.boxes if n.startswith('p1_courtyard_stair_')
                   and any(t in n for t in ('_up_', '_down_', '_turn', '_landing'))
                   and not any(t in n for t in ('_post_', '_clip_', '_outer', '_well', '_finish_'))]
        self.assertEqual(len(walking), 2*(2*9+1)+2)
        self.assertEqual(set(walking), {'floor_grating'})

    def test_coffee_room_sits_between_the_south_restrooms_behind_the_door(self):
        rooms = {r['id']: r for r in self.levels[1]['rooms']}
        coffee = rooms['f_south_coffee']['footprint_local_metres']
        male = rooms['f_south_centre_male']['footprint_local_metres']
        female = rooms['f_south_centre_female']['footprint_local_metres']
        self.assertAlmostEqual(male[2], coffee[0], places=6)
        self.assertAlmostEqual(coffee[2], female[0], places=6)
        self.assertTrue(coffee[0] < DOOR[0] and DOOR[1] < coffee[2])

    def test_coffee_area_is_furnished_from_the_28_october_photos(self):
        prefix = 'academic_first_f_south_coffee_'
        names = [n[len(prefix):] for n, *_ in self.boxes if n.startswith(prefix)]
        self.assertEqual(sum(n.startswith('vending_') and '_finish_' not in n for n in names), 6)
        self.assertEqual(sum(n.startswith('recycling_bin_') for n in names), 4)
        self.assertEqual(sum(n.endswith('_top') for n in names), 2)
        # Nothing stands in the line between the corridor door and the stair door.
        z = self.zs[1]
        blocking = [n for n, lo, hi, m in self.physics if n.startswith(prefix)
                    and overlaps(lo, hi, (DOOR[0]+.2, -85.9, z+.05), (DOOR[1]-.2, self.walls[1], z+1.8))]
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

    def test_terraces_are_glazed_from_the_corridors_without_doors(self):
        z = self.zs[-1]
        terraces = self.stair['courtyard']['terraces']
        y0, y1 = terraces['y']
        for x in (terraces['west'][0], terraces['east'][1]):
            for i in range(1, 30):
                y = y0+(y1-y0)*i/30
                if x > 0 and LIFT_SPAN[0]-.1 <= y <= LIFT_SPAN[1]+.1:
                    continue  # the enclosed lift shaft is the wall here
                solid = [m for n, lo, hi, m in self.physics if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]
                         and lo[2] <= z+1.5 <= hi[2]]
                self.assertTrue(solid, (x, y))
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
