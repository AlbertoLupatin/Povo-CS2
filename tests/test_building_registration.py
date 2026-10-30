"""The OSM/LiDAR registration audit must measure facade offsets and read its cached sources."""
import json
import struct
import unittest

import numpy as np

from tools.audit_building_registration import (CELL, NORTH, ORIGIN, OSM, WEST, best_shift, facade_lengths,
                                              rasterise_polygon, side_deviation, simplify)
from tools.fetch_osm_extract import parse_wkb, utm


def square(x0, y0, size, clockwise=False):
    ring = [[x0, y0], [x0 + size, y0], [x0 + size, y0 + size], [x0, y0 + size], [x0, y0]]
    return {'type': 'Polygon', 'coordinates': [ring[::-1] if clockwise else ring]}


class BuildingRegistrationTests(unittest.TestCase):
    def test_utm_matches_reference_projection(self):
        # Reference values from pyproj EPSG:4326 -> EPSG:25832.
        east, north = utm(11.15, 46.067)
        self.assertAlmostEqual(east, 666277.0198, places=3)
        self.assertAlmostEqual(north, 5103738.8998, places=3)

    def test_wkb_polygon_and_linestring(self):
        ring = [(0, 0), (4, 0), (4, 3), (0, 0)]
        polygon = struct.pack('<BII', 1, 3, 1) + struct.pack('<I', len(ring)) + struct.pack('<' + 'd' * 8, *sum(ring, ()))
        self.assertEqual(parse_wkb(polygon), {'type': 'Polygon', 'coordinates': [[list(p) for p in ring]]})
        line = struct.pack('>BII', 0, 2, 2) + struct.pack('>dddd', 1, 2, 3, 4)
        self.assertEqual(parse_wkb(line), {'type': 'LineString', 'coordinates': [[1, 2], [3, 4]]})

    def test_facade_lengths_ignore_ring_orientation(self):
        for clockwise in (False, True):
            self.assertEqual(list(facade_lengths(square(0, 0, 20, clockwise))), [20, 20, 20, 20])

    def test_shifted_footprint_reports_side_offsets_and_shift(self):
        osm = square(666200, 5103700, 20)
        game = rasterise_polygon(square(666203, 5103700, 20))
        reference = rasterise_polygon(osm)
        self.assertEqual(reference.sum() * CELL * CELL, 400)
        over = side_deviation(game & ~reference, osm, True)
        short = side_deviation(reference & ~game, osm, False)
        # Strip corners sit nearer the adjacent facades (about depth^2/2 each), so the
        # dominant side reads slightly low and the neighbours must stay negligible.
        self.assertAlmostEqual(over['E']['mean_offset_m'], 3, delta=.6)
        self.assertAlmostEqual(short['W']['mean_offset_m'], 3, delta=.6)
        for side, value in {**{k: v for k, v in over.items() if k != 'E'}, **{k: v for k, v in short.items() if k != 'W'}}.items():
            self.assertLess(value['mean_offset_m'], .5, side)
        r0, c0 = int((NORTH - 5103730) / CELL), int((666190 - WEST) / CELL)
        shift, score = best_shift(game, reference, (r0, r0 + 80, c0, c0 + 80))
        self.assertEqual(shift, [-3.0, 0.0]); self.assertEqual(score, 1.0)

    def test_simplify_drops_collinear_points_and_keeps_corners(self):
        x, y = ORIGIN[0], ORIGIN[1]
        ring = [[x, y], [x + 5, y + .2], [x + 10, y], [x + 10, y + 10], [x, y + 10], [x, y]]
        self.assertEqual(simplify(ring, .75), [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])

    def test_cached_osm_extract_covers_the_campus(self):
        data = json.loads(OSM.read_text())
        self.assertIn('Open Database License', data['licence'])
        buildings = {f['properties']['osm']: f['properties'] for f in data['features'] if f['properties']['kind'] == 'building'}
        # Povo 2, Povo 1, FBK Edificio Nord, library and canteen.
        for osm in ('w1193371312', 'r3663359', 'w28933741', 'w275318462', 'w275318465'):
            self.assertIn(osm, buildings)
        self.assertEqual(buildings['w28933741']['name'], 'Edificio Nord')
        coords = np.array([p for f in data['features'] if f['properties']['osm'] == 'r3663359'
                           for p in f['geometry']['coordinates'][0]])
        self.assertTrue(666200 < coords[:, 0].mean() < 666300 and 5103700 < coords[:, 1].mean() < 5103780)


if __name__ == '__main__':
    unittest.main()
