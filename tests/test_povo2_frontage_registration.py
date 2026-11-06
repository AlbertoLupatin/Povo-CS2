"""Regressions for the fresh, final export assembly (not cached review geometry)."""
import inspect
import unittest

from tools import build_povo_campus as campus
from tools.audit_povo2_integrated import audit_stair_routes
from tools.audit_povo_exterior_integrated import standing
from tools.audit_povo_interior import audit_level
from tools.audit_povo_yard import audit_gardens
from tools.povo2_frontage_registration import shift_metadata


class FrontageMetadataTests(unittest.TestCase):
    def test_shared_coordinates_translate_once_for_every_alias(self):
        for coordinate in ([1., 2., 3.], (1., 2., 3.)):
            with self.subTest(type=type(coordinate).__name__):
                data = dict(first=coordinate, second=coordinate)
                shift_metadata(data)
                self.assertEqual(list(data['first']), [1., 10.8, 3.])
                self.assertEqual(data['first'], data['second'])

    def test_source_pixels_and_dimensions_remain_unchanged(self):
        data = dict(source_pixels=[1, 2, 3, 4], flight_counts=[10, 10, 10],
                    fitout=dict(rows=[2, 4]),
                    furniture=dict(rows=[dict(bounds_local_metres=[[1.,2.,3.],[4.,5.,6.]])]),
                    bounds=[1., 2., 3., 4.])
        shift_metadata(data)
        self.assertEqual(data['source_pixels'], [1, 2, 3, 4])
        self.assertEqual(data['flight_counts'], [10, 10, 10])
        self.assertEqual(data['fitout']['rows'], [2, 4])
        self.assertEqual(data['furniture']['rows'][0]['bounds_local_metres'],
                         [[1., 10.8, 3.], [4., 13.8, 6.]])
        self.assertEqual(data['bounds'], [1., 10.8, 3., 12.8])

    def test_coordinate_scalars_and_relative_offsets_use_their_own_frames(self):
        data = dict(door_y=39., vestibule_front_north=14.4,
                    lower_junction_door_north_coordinate=18., upper_route_y=57.75,
                    basement_north_offset=-3.5, room2_north_shift_metres=25.)
        shift_metadata(data)
        for key, expected in [('door_y', 47.8), ('vestibule_front_north', 23.2),
                              ('lower_junction_door_north_coordinate', 26.8),
                              ('upper_route_y', 66.55)]:
            self.assertAlmostEqual(data[key], expected)
        self.assertEqual(data['basement_north_offset'], -3.5)
        self.assertEqual(data['room2_north_shift_metres'], 25.)

    def test_export_calls_final_registration_stage(self):
        # Export is expensive and writes artifacts; guard its assembly entry point.
        self.assertIn('build_registered_geometry(root)', inspect.getsource(campus.export))


class RegisteredFrontageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.boxes, cls.levels, _ = campus.build_registered_geometry()
        cls.link = next(l['connection'] for l in cls.levels if l.get('connection'))
        cls.p2 = cls.link['povo2']
        cls.ext = cls.levels[0]['exterior']
        cls.physics = campus.collision_boxes(cls.boxes)
        cls.byname = {n: (lo, hi, m) for n, lo, hi, m in cls.boxes}

    def test_common_frontage_and_retained_room_order(self):
        ground = next(l for l in self.p2['levels'] if l['floor'] == 0)
        rooms = {r['id']: r for r in ground['rooms']}
        for name, west, east in [('b109', 2, 10), ('b108', 10, 20), ('b106', 20, 31)]:
            room = rooms[name]
            self.assertEqual(room['bounds'][0::2], [west, east])
            self.assertAlmostEqual(room['bounds'][1], 10.8)
            self.assertAlmostEqual(room['bounds'][3], 24.2)
            self.assertEqual(room['bounds'], room['footprint_local_metres'])
            floor = self.byname['p2_ground_' + name + '_floor']
            self.assertAlmostEqual(floor[0][1], 10.8)
            self.assertAlmostEqual(floor[1][1], 24.2)
        # Each enclosed lower-floor slab shares the facade; the exterior
        # basement terrace deliberately extends south of it.
        for prefix, z in [('p2_parking_', -3.2), ('p2_basement_', .4), ('p2_ground_', 4.)]:
            slabs = [lo[1] for n,lo,hi,material in self.boxes if n.startswith(prefix)
                     and material.startswith('floor_') and material != 'floor_terrace'
                     and abs(hi[2]-z)<.02]
            self.assertTrue(slabs, prefix)
            self.assertAlmostEqual(min(slabs), 10.8, msg=prefix)
        self.assertAlmostEqual(self.p2['parking']['bounds'][1], 10.8)
        for n, lo, hi, _ in self.boxes:
            if n.startswith(('p2_parking_', 'p2_basement_')) and hi[2] < 0:
                self.assertGreaterEqual(lo[1], 10.8 - 1e-8, n)

    def test_room_door_metadata_matches_actual_door_headers(self):
        ground = next(l for l in self.p2['levels'] if l['floor'] == 0)
        for room in ground['rooms']:
            if 'door_y' not in room:
                continue
            lo, hi, _ = self.byname['p2_ground_' + room['id'] + '_door_head']
            self.assertAlmostEqual(room['door_y'], (lo[1] + hi[1])/2, msg=room['id'])

    def test_mixed_coordinate_and_interval_metadata(self):
        # The registered interval describes the actual inner doorway banks.
        x, y0, y1 = self.p2['ground']['entrance']
        for bank in self.ext['entrance']['door_banks']:
            if bank['line'] == 'inner':
                self.assertEqual(bank['centre'][0], x)
                self.assertLessEqual(y0, bank['centre'][1]-bank['clear_width']/2)
                self.assertGreaterEqual(y1, bank['centre'][1]+bank['clear_width']/2)
        self.assertEqual(self.p2['ground']['source_entrance'], [7, 26, 30])
        # The disabled lift still describes its former opening coordinates.
        self.assertEqual(self.link['lift']['ground_opening_east'], [21.25, 22.45])
        for actual, expected in zip(self.link['lift']['side_opening_north'], [24.25, 25.25]):
            self.assertAlmostEqual(actual, expected)

    def test_internal_stair_directions_and_sizes_are_retained(self):
        self.assertEqual(self.p2['stairs']['well_bounds'], [11, 26.8, 20.5, 34.8])
        # Tread sequence preserves the west, north, east flight directions.
        for route in self.p2['stairs']['path']:
            self.assertEqual(route['flight_counts'], [10, 10, 10])
            points = route['points']
            descending = [(a,b) for a,b in zip(points, points[1:]) if b[2] < a[2] - .01]
            self.assertEqual(len(descending), 30)
            self.assertTrue(all(b[0] < a[0] for a,b in descending[:10]))
            self.assertTrue(all(b[1] > a[1] for a,b in descending[10:20]))
            self.assertTrue(all(b[0] > a[0] for a,b in descending[20:]))
        self.assertEqual(self.p2['stairs']['portals'][1]['centre'], [19.2, 26.8, .4])
        self.assertAlmostEqual(self.p2['basement']['corridor'][3], 26.8)

    def test_stair_and_garden_routes_have_player_clearance(self):
        routes = self.p2['basement_rebuild']['routes'] + self.p2['stairs']['path']
        routes += self.p2['parking']['routes']
        routes += [dict(points=p) for p in self.p2['gardens']['routes'].values()]
        samples, failures = audit_stair_routes(self.physics, routes)
        self.assertGreater(samples, 3000)
        self.assertEqual(failures, [])
        garden = audit_gardens(self.boxes, self.levels)
        self.assertEqual(garden['status'], 'passed', garden['failures'])
        self.assertGreater(garden['stair_and_landing_samples'], 100)

    def test_all_floor_stations_remain_reachable(self):
        for level in self.p2['levels']:
            z, prefix = level['z'], level['id']
            support = [(prefix+'_alias_'+n,lo,hi,m) for n,lo,hi,m in self.physics
                       if n.startswith(('p2_', 'academic_first_link_p2'))
                       and m.startswith('floor_') and abs(hi[2]-z)<.02]
            report, _, _ = audit_level(self.physics + support,
                dict(id=prefix, floor_elevation_local=z), level['audit_stations'])
            self.assertEqual(report['status'], 'passed', report)

    def test_lower_corridor_exits_directly_into_garden_at_north_15(self):
        g = self.p2['gardens']
        exit = g['office_exit']
        self.assertEqual(exit['corridor_parts'],
            [[20.75,13.5,23.75,21.3],[22.25,13.5,31.8,16.5]])
        self.assertEqual(g['routes']['office_exit'],
            [[22.25,26.8,-3.2],[22.25,15.,-3.2],[31.8,15.,-3.2],[33.3,15.,-3.2]])
        self.assertFalse(any(n.startswith('p2_registered_garden_exit_floor_')
            and lo[0] < 30.3 < hi[0] and lo[1] < 18. < hi[1]
            for n,lo,hi,_ in self.boxes))  # No former northward branch near W-30.
        self.assertEqual(exit['door_centre'], [31.8, 15., -3.2])
        self.assertEqual(exit['outward_direction'], [1., 0., 0.])
        self.assertAlmostEqual(g['garden'][3], 20.34)
        lo, hi, _ = self.byname['p2_registered_garden_exit_ceiling_0']
        self.assertEqual(lo[:2], (20.75, 13.5))
        self.assertAlmostEqual(hi[1], 21.4)
        self.assertFalse(any(n.startswith('p2_parking_garden_door_') for n in self.byname))
        doors = [d for d in self.p2['repair_doors']
                 if d['id'].startswith('p2_registered_garden_exit_')]
        self.assertEqual(len(doors), 2)
        for door in doors:
            self.assertEqual(door['pivot'][0], 31.8)
            self.assertEqual(door['pivot'][2], -3.2)
            self.assertEqual(door['material'], 'materials/trento/povo/campus/door_black.vmat')
        floor = next(f for f in self.p2['basement_rebuild']['levels'] if f['floor'] == -2)
        for key in ('areas', 'floor_pieces'):
            for part in exit['corridor_parts']:
                self.assertIn(part, floor[key])
        # Cross the end aperture, and verify both sides enclose the extension.
        _, failures = audit_stair_routes(self.physics,
            [dict(points=g['routes']['office_exit'])])
        self.assertEqual(failures, [])
        for x in (20.67, 23.83):
            self.assertTrue(any(lo[0] < x < hi[0] and lo[1] <= 17 <= hi[1]
                and lo[2] < -2 < hi[2] for _,lo,hi,_ in self.physics))

    def test_landscape_width_order_and_grade(self):
        reg = self.p2['frontage_registration']
        self.assertEqual((reg['road_width'], reg['pavement_width']), (6., 1.4))
        landscape = self.p2['landscape_registration']
        self.assertEqual(landscape['grass_north'], [4.09, 9.09])
        self.assertEqual(landscape['bush'], [28., 4.09, 33., 9.09])
        self.assertAlmostEqual(landscape['grate_north'], 9.03)
        bush = next(m for m in self.ext['meshes'] if m['name']=='exterior_registered_bush')
        self.assertAlmostEqual(max(v[0] for v in bush['vertices'])-min(v[0] for v in bush['vertices']), 5.)
        self.assertAlmostEqual(max(v[1] for v in bush['vertices'])-min(v[1] for v in bush['vertices']), 5.)
        grass = [m for m in self.ext['collision_meshes'] if m['name'].startswith('exterior_registered_grass_')]
        self.assertGreater(len(grass), 30)
        for mesh in grass:
            at_grate = [v[2] for v in mesh['vertices'] if abs(v[1]-9.09)<1e-8]
            self.assertAlmostEqual(max(at_grate), .4)
        steps = [b for b in self.boxes if b[0].startswith('p2_registered_up_step_')]
        self.assertEqual(len(steps), 20)
        up = self.p2['gardens']['routes']['up']
        self.assertTrue(all(b[1]<a[1] and b[2]>=a[2] for a,b in zip(up,up[1:])))
        down = self.p2['gardens']['down_stair']
        self.assertEqual(down[0], 31.8)
        self.assertEqual(down[2], 40.55)
        self.assertAlmostEqual(down[1], 9.09)

    def test_bridge_and_entrance_connections_have_clearance(self):
        bridge = [[18.25,9.,11.2],[18.25,20.,11.2],[22.25,20.,11.2],
                  [22.25,28.8,11.2],[19.2,28.8,11.2]]
        samples, failures = audit_stair_routes(self.physics,
            [dict(points=bridge), dict(points=bridge[::-1])])
        self.assertGreater(samples, 250)
        self.assertEqual(failures, [])
        for bank in self.ext['entrance']['door_banks']:
            x,y,z = bank['centre']
            for xx in (x-.5,x,x+.5):
                foot, obstacles = standing(xx,y,z,self.physics,self.ext['collision_meshes'])
                self.assertIsNotNone(foot, (xx,y,z))
                self.assertEqual(obstacles, [], (xx,y,z))
        self.assertFalse(self.link['lift']['enabled'])
        self.assertFalse(any('lift_ladder' in n for n,_,_,_ in self.boxes))


if __name__ == '__main__':
    unittest.main()
