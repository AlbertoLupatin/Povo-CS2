"""Regressions for the fresh, final export assembly (not cached review geometry)."""
import inspect
import json
import unittest

from tools import build_povo_campus as campus
from tools.audit_povo2_integrated import audit_stair_routes
from tools.audit_povo_exterior_integrated import standing
from tools.audit_povo_interior import audit_level
from tools.audit_povo_yard import audit_gardens
from tools.povo2_frontage_registration import shift_metadata
from tools.povo2_levels import NEW as LEVELS, remap_z, p1_band


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

    def test_povo1_bus_side_recess_has_paved_collision(self):
        for x in (11.15, 15., 19., 23.95):
            for y in (-19.95, -18., -15.93):
                self.assertTrue(any(lo[0] < x < hi[0] and lo[1] < y < hi[1] and hi[2] == p1_band(4.)
                                    and material == 'exterior_paving'
                                    for _, lo, hi, material in self.physics), (x, y))

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
        for prefix, z in [('p2_parking_', LEVELS[-2]), ('p2_basement_', LEVELS[-1]), ('p2_ground_', LEVELS[0])]:
            slabs = [lo[1] for n,lo,hi,material in self.boxes if n.startswith(prefix)
                     and material.startswith('floor_') and material != 'floor_terrace'
                     and abs(hi[2]-z)<.02]
            self.assertTrue(slabs, prefix)
            self.assertAlmostEqual(min(slabs), 10.8, msg=prefix)
        self.assertAlmostEqual(self.p2['parking']['bounds'][1], 10.8)
        for n, lo, hi, _ in self.boxes:
            if n.startswith(('p2_parking_', 'p2_basement_')) and hi[2] < remap_z(0):
                self.assertGreaterEqual(lo[1], 10.8 - 1e-8, n)

    def test_room_door_metadata_matches_actual_door_headers(self):
        ground = next(l for l in self.p2['levels'] if l['floor'] == 0)
        for room in ground['rooms']:
            if 'door_y' not in room:
                continue
            lo, hi, _ = self.byname['p2_ground_' + room['id'] + '_door_head']
            self.assertAlmostEqual(room['door_y'], (lo[1] + hi[1])/2, msg=room['id'])

    def test_registered_west_rooms_have_full_fitouts_and_one_glazing_plane(self):
        ground = next(l for l in self.p2['levels'] if l['floor'] == 0)
        rooms = [r for r in ground['rooms'] if r['id'] in ('b106', 'b108', 'b109')]
        for room in rooms:
            name = room['id']
            self.assertGreaterEqual(len(room['fitout']['rows']), 6, name)
            self.assertLess(room['fitout']['rows'][-1]['bounds_local_metres'][0][1], 14., name)
            panes = [b for b in self.boxes if b[0].startswith(f'p2_registered_{name}_front_pane_')]
            self.assertGreater(len(panes), 4, name)
            self.assertTrue(all(campus.is_breakable_glass(pane) and pane[3] == 'window_glass' for pane in panes))
            for _, lo, hi, _ in panes:
                self.assertAlmostEqual((lo[1]+hi[1])/2, 10.8)
        self.assertFalse(any(b[0].startswith('facade_p2_south_l0_') and b[3] == 'window_glass'
                             and b[2][0] > 2 and b[1][0] < 31 for b in self.boxes))

    def test_registered_west_corridor_ceiling_has_no_lower_slabs(self):
        for x, y in ((3., 25.5), (8., 26.45), (22., 24.7)):
            visible = min(lo[2] for _, lo, hi, _ in self.boxes
                          if lo[0] < x < hi[0] and lo[1] < y < hi[1] and lo[2] > remap_z(6.6))
            self.assertAlmostEqual(visible, remap_z(7.28), msg=(x, y))

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
        # 11 November layout: two lanes, west end closed at E13.69.
        self.assertEqual(self.p2['stairs']['well_bounds'], [13.69, 26.9, 20.39, 34.7])
        # From 0 the first flight is on the left (west), so -1 is reached at the
        # west end and -2 at the east end: W,E,W then E,W,E.
        headings = {-1: (-1, 1, -1), -2: (1, -1, 1)}
        for route in self.p2['stairs']['path']:
            self.assertEqual(route['flight_counts'], [10, 10, 10])
            self.assertAlmostEqual(route['rise'], .16)
            points = route['points']
            descending = [(a,b) for a,b in zip(points, points[1:]) if b[2] < a[2] - .01]
            self.assertEqual(len(descending), 30)
            for i, sign in enumerate(headings[route['lower_floor']]):
                self.assertTrue(all((b[0]-a[0])*sign > 0 for a,b in descending[10*i:10*i+10]))
        portals = {p['floor']: p['centre'] for p in self.p2['stairs']['portals']}
        self.assertEqual(portals[-1], [14.69, 26.8, LEVELS[-1]])
        self.assertEqual(portals[-2], [19.2, 26.8, LEVELS[-2]])
        self.assertEqual({tuple(p['centre'][:2]) for p in self.link['stair']['portals']}, {(20.5, 30.8)})
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
            [[22.25,26.8,LEVELS[-2]],[22.25,15.,LEVELS[-2]],[31.8,15.,LEVELS[-2]],[33.3,15.,LEVELS[-2]]])
        self.assertFalse(any(n.startswith('p2_registered_garden_exit_floor_')
            and lo[0] < 30.3 < hi[0] and lo[1] < 18. < hi[1]
            for n,lo,hi,_ in self.boxes))  # No former northward branch near W-30.
        self.assertEqual(exit['door_centre'], [31.8, 15., LEVELS[-2]])
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
            self.assertEqual(door['pivot'][2], LEVELS[-2])
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
                and lo[2] < remap_z(-2) < hi[2] for _,lo,hi,_ in self.physics))

    def test_landscape_width_order_and_grade(self):
        reg = self.p2['frontage_registration']
        self.assertEqual((reg['road_width'], reg['pavement_width']), (7., 1.4))
        landscape = self.p2['landscape_registration']
        self.assertEqual(landscape['grass_north'], [4.09, 9.09])
        self.assertEqual(landscape['bush'], [28., 7., 33., 9.09])
        self.assertAlmostEqual(landscape['grate_north'], 9.03)
        leaves = [v for m in self.ext['meshes'] if m['name'].startswith('exterior_registered_bush_')
                  for v in m['vertices']]
        self.assertGreater(len(leaves), 1000)
        for axis, low, high in ((0,28.,33.), (1,7.,9.09)):
            self.assertGreaterEqual(min(v[axis] for v in leaves), low)
            self.assertLessEqual(max(v[axis] for v in leaves), high)
            self.assertGreater(max(v[axis] for v in leaves)-min(v[axis] for v in leaves), 4. if axis==0 else 1.5)
        self.assertFalse(any(m['name'].startswith('exterior_registered_bush_') for m in self.ext['collision_meshes']))
        grass = [m for m in self.ext['collision_meshes'] if m['name'].startswith('exterior_registered_grass_')]
        self.assertGreater(len(grass), 30)
        for mesh in grass:
            road_left, road_right, toe_right, toe_left = mesh['vertices'][4:]
            for road, toe in ((road_left, toe_left), (road_right, toe_right)):
                # Toes moved with the re-levelled -1 terrace; the road edge did not.
                self.assertGreaterEqual(toe[2], LEVELS[-1]-1e-6)
                self.assertGreaterEqual(road[2], toe[2])
                if toe[0] >= 34.:
                    self.assertAlmostEqual(toe[2], LEVELS[-1])
        self.assertAlmostEqual(self.byname['p2_basement_drawio_terrace'][1][2], LEVELS[-1])
        self.assertAlmostEqual(self.byname['p2_basement_drawio_terrace_retaining_west_south'][1][2], LEVELS[-1])
        steps = [b for b in self.boxes if b[0].startswith('p2_registered_up_step_')]
        self.assertEqual(len(steps), 20)
        up = self.p2['gardens']['routes']['up']
        self.assertTrue(all(b[1]<a[1] and b[2]>=a[2] for a,b in zip(up,up[1:])))
        down = self.p2['gardens']['down_stair']
        self.assertEqual(down[0], 31.8)
        # 27 risers since the 11 November re-levelling: the run ends 2.47 m further east.
        self.assertAlmostEqual(down[2], 43.0175)
        self.assertAlmostEqual(down[1], 9.09)

    def test_corner_apron_connects_both_sidewalks_at_street_grade(self):
        from tools.audit_povo_exterior_integrated import height_at

        meshes = self.ext['collision_meshes']
        for y in (2., 3., 4., 5., 6., 7., 8.):
            heights = []
            for i in range(21):
                x = 56.2 + i*.05
                support = [z for mesh in meshes
                           if mesh['material'] in ('exterior_paving','exterior_concrete')
                           for z in height_at(mesh, x, y)]
                self.assertTrue(support, (x, y))
                heights.append(max(support))
            self.assertLess(max(abs(a-b) for a,b in zip(heights, heights[1:])), .12)
        for x in (49.4, 50., 50.8):
            heights = [max(z for mesh in meshes if mesh['material']=='exterior_paving'
                           for z in height_at(mesh,x,y)) for y in (4.07,4.11)]
            self.assertLess(abs(heights[0]-heights[1]), .02)
        for y in (4.5, 6., 8.):
            for x in (49.4, 51.5, 53.5, 55.5, 56.6):
                self.assertTrue(any(height_at(mesh,x,y) for mesh in meshes
                                    if any(part in mesh['name'] for part in ('registered_corner_apron_',
                                                                               'registered_footway_north_'))), (x,y))

    def test_sidewalks_close_the_recesses_and_keep_the_garden_open(self):
        from tools.audit_povo_exterior_integrated import height_at

        for y in (8.5,9.1,10.,12.,14.,16.,17.,18.,19.,21.,25.,29.):
            for x in (55.9,56.3,56.55,56.8):
                heights = [z for mesh in self.ext['collision_meshes']
                           if mesh['material'] in ('exterior_paving','exterior_concrete')
                           for z in height_at(mesh, x, y)]
                self.assertTrue(heights, (x,y))
                self.assertGreaterEqual(max(heights), 3.99, (x,y))
        # South road and junction regraded to the LiDAR on 11 November.
        for x,y,z in ((53.,-7.,7.947),(47.,-4.97,7.582),(26.,-18.,p1_band(4.)),
                      (19.,9.65,LEVELS[-1]),(36.8,15.,remap_z(-3.175))):
            foot, obstacles = standing(x,y,z,self.physics,self.ext['collision_meshes'])
            self.assertIsNotNone(foot, (x,y,z))
            self.assertAlmostEqual(foot,z,delta=.18)
            self.assertEqual(obstacles, [], (x,y,z))
        self.assertFalse(any(mesh['name'].startswith('exterior_registered_old_road_ground')
                             for mesh in self.ext['meshes']))
        self.assertTrue(any(r['name'].startswith('library_street_extension_1_') and r['name'].endswith('_handrail')
                            for r in self.levels[0]['library_stair']['rails']))
        self.assertTrue(any(r['name']=='registered_street_guard_2_handrail'
                            for r in self.p2['stairs']['rails']))
        self.assertFalse(any(name.startswith('exterior_ground_') and lo[0]<36.8<hi[0]
                             and lo[1]<15.<hi[1] and LEVELS[-2]<hi[2]<LEVELS[0]
                             for name,lo,hi,_ in self.boxes))

    def test_carriageways_and_bridge_footways_keep_their_width(self):
        from tools.audit_povo_exterior_integrated import height_at

        meshes = self.ext['collision_meshes']

        def has(prefix,x,y):
            return any(height_at(mesh,x,y) for mesh in meshes if mesh['name'].startswith(prefix))

        for x in (34.,40.,44.):
            for y in (-4.30,-.81,2.68):
                self.assertTrue(has('exterior_registered_road_',x,y), (x,y))
            for y in (-7.89,-4.32):
                self.assertTrue(has('exterior_registered_footway_south_',x,y), (x,y))
            for y in (2.70,6.99):
                self.assertTrue(has('exterior_registered_footway_north_',x,y), (x,y))
            for y in (-8.2,7.2):
                self.assertFalse(has('exterior_registered_footway_',x,y), (x,y))
        for y in (-8.95,-7.5,-5.5,-2.05):
            for x in (57.6,58.2,58.49):
                self.assertTrue(has('exterior_registered_road_',x,y), (x,y))
            self.assertTrue(has('exterior_registered_via_road_',58.51,y), y)
            self.assertFalse(has('exterior_registered_via_footway_',57.8,y), y)
        for x in (57.1,57.8,58.4):
            foot, obstacles = standing(x,-9.7,8.37,self.physics,meshes)   # LiDAR-regraded junction
            self.assertAlmostEqual(foot,8.37,delta=.05)
            self.assertFalse(obstacles)
        self.assertTrue(any(mesh['name'].startswith('exterior_registered_footway_south_0') and
                            mesh['material']=='exterior_concrete' for mesh in meshes))
        import math
        nx,ny = (-15./math.hypot(15.,2.38),2.38/math.hypot(15.,2.38))
        for sign in (-1,1):
            for offset,prefix in ((3.49,'road_'),(3.51,'footway_'),(5.29,'footway_')):
                x,y = 63.19+sign*offset*nx,7.5+sign*offset*ny
                self.assertTrue(has('exterior_registered_via_'+prefix,x,y), (x,y))
            x,y = 63.19+sign*3.49*nx,7.5+sign*3.49*ny
            self.assertFalse(has('exterior_registered_via_verge_',x,y), (x,y))

    def test_south_walk_has_exactly_one_surface_through_every_miter_section(self):
        from tools.audit_povo_exterior_integrated import height_at
        walks=[m for m in self.ext['collision_meshes']
               if m['name'].startswith('exterior_registered_footway_south_')]
        for i in range(350):
            x=22.053+i*.1
            intersections=[]
            active=[]
            for mesh in walks:
                poly=mesh['vertices'][len(mesh['vertices'])//2:]
                if not min(v[0] for v in poly)<x<max(v[0] for v in poly):continue
                active.append(mesh)
                for a,b in zip(poly,poly[1:]+poly[:1]):
                    if min(a[0],b[0])<=x<=max(a[0],b[0]) and abs(a[0]-b[0])>1e-8:
                        intersections.append(a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]))
            self.assertTrue(intersections,x)
            low,high=min(intersections),max(intersections)
            for j in range(31):
                y=low+(high-low)*(j+.5)/31
                count=sum(bool(height_at(mesh,x,y)) for mesh in active)
                self.assertEqual(count,1,(x,y,count))

    def test_widened_walks_do_not_cross_the_fixed_carriageway(self):
        from tools.povo_floor_surfaces import area, subtract
        from tools.povo_street_footways import tops
        roads = [poly for m in self.ext['collision_meshes']
                 if m['name'].startswith('exterior_registered_road_') for poly in tops(m)]
        for mesh in self.ext['collision_meshes']:
            if not mesh['name'].startswith('exterior_registered_footway_'):continue
            for poly in tops(mesh):
                parts=[poly]
                for road in roads:
                    parts=[piece for part in parts for piece in subtract(part,road)]
                self.assertAlmostEqual(sum(area(p) for p in parts),area(poly),places=5,
                                       msg=mesh['name'])

    def test_library_measured_spans_and_planting_touch_the_rail(self):
        from tools.audit_povo_exterior_integrated import height_at
        wall = -13.
        rails = self.levels[0]['library_stair']['rails']
        rail = next(r['a'][1] for r in rails if r['name'].startswith('library_street_extension_1_')
                    and r['a'][0] <=44.<=r['b'][0])
        from tools.povo2_frontage_registration import _edge_at_x
        opposite = _edge_at_x(self.p2['landscape_registration']['pavement_boundary'],44.)[1]
        self.assertEqual(rail-wall,5.)
        self.assertEqual(opposite-rail,15.)
        for x in (36.,40.,44.,46.):
            for y in (-7.8,-6.,3.,6.9):
                self.assertTrue(any(height_at(m,x,y) for m in self.ext['collision_meshes']
                                    if m['name'].startswith('exterior_registered_footway_')),(x,y))
            self.assertTrue(any(height_at(m,x,-8.1) for m in self.ext['collision_meshes']
                                if m['name']=='exterior_library_grass_slope'))
        self.assertEqual(self.levels[0]['library_stair']['wall_y'],[-8.1,-7.9])
        self.assertFalse(any(m['name'].startswith('exterior_registered_library_verge_2_')
                             for m in self.ext['collision_meshes']))

    def test_bus_moves_right_as_one_assembly_with_solid_wheels(self):
        from tools.povo_abandoned_bus import extend

        expected = {}
        def collect(name, lo, hi, material):
            expected['exterior_'+name] = (lo, hi, 'exterior_'+material)

        config = json.loads((campus.ROOT/'config/povo_exterior.json').read_text())
        extend(collect, [], config['abandoned_bus'])
        actual = {name: box for name,box in self.byname.items()
                  if name.startswith('exterior_abandoned_bus_')}
        self.assertEqual(set(actual), set(expected))
        for name,(lo,hi,material) in expected.items():
            moved_lo,moved_hi,actual_material = actual[name]
            self.assertEqual(actual_material, material)
            for original,moved in ((lo,moved_lo),(hi,moved_hi)):
                # Rigid: the whole bus rides the LiDAR-regraded road by one offset.
                self.assertEqual(moved[0], original[0])
                self.assertAlmostEqual(moved[2]-original[2], self.ext['grade']['bus_dz'])
                self.assertAlmostEqual(moved[1]-original[1], 1.8)
        wheels = [m for m in self.ext['collision_meshes'] if 'abandoned_bus_wheel_' in m['name']]
        self.assertEqual(len(wheels), 4)
        bus = self.ext['grade']['bus_dz']
        for x,y,z in ((25.,-6.2,4.67+bus),(25.,-1.675,4.67+bus),(27.7,-1.675,5.728)):
            foot, obstacles = standing(x,y,z,self.physics,self.ext['collision_meshes'])
            self.assertAlmostEqual(foot,z,delta=.01)
            self.assertEqual(obstacles, [], (x,y,z))

    def test_registered_walkways_and_vestibule_keep_continuous_finishes(self):
        for surface,material in (('floor','floor_p2_tile'),('ceiling','ceiling_panel')):
            prefix='exterior_p2_entry_'+surface
            parts=[m for name,_,_,m in self.boxes if name.startswith(prefix)]
            self.assertTrue(parts)
            self.assertEqual(set(parts),{material})
            self.assertFalse(any(name.startswith(prefix+'_joint_') for name in self.byname))
        self.assertEqual(self.byname['p2_registered_bridge_floor'][2],'floor_circulation')
        for name in ('academic_ground_lobby_finish_south','academic_first_link_p1_corridor_finish_west'):
            self.assertEqual(self.byname[name][2],'floor_circulation')
            self.assertFalse(any(b[0]==name for b in self.physics))
        hedge=[m for m in self.ext['meshes'] if m['name'].startswith('exterior_library_hedge_')]
        self.assertEqual(len(hedge),3)
        self.assertTrue(all(m['material'].startswith('exterior_shrub_leaf') for m in hedge))
        self.assertTrue(all(len(m['vertices'])==len(m['uvs'])>500 for m in hedge))
        self.assertFalse(any(name.startswith('exterior_library_hedge_') for name in self.byname))
        self.assertFalse(any(m['name'].startswith('exterior_library_hedge_') for m in self.ext['collision_meshes']))

    def test_bridge_and_entrance_connections_have_clearance(self):
        bridge = [[x, y, LEVELS[1]] for x, y in ((18.25,9.),(18.25,20.),(22.25,20.),(22.25,30.8),(19.39,30.8))]
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
