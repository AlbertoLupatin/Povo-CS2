#!/usr/bin/env python3
"""Generate povo_site.vmap: the real Povo site as a playable blockout.

- Terrain: PAT LiDAR DTM sampled every 2 m, split into 24 m Hammer mesh tiles.
  Each triangle gets a surface from OSM (roads, paths, parking) or, elsewhere,
  from the 2024 orthophoto (green -> grass, otherwise paving).
- Buildings: OSM footprints (with courtyards) extruded from the ground to the
  LiDAR roof height. Campus buildings are placeholders for the detailed ones.
- Trees: OSM trees plus LiDAR canopy peaks, as stock CS2 tree models.
Everything is at the project's uniform gameplay scale.
"""

import argparse
import csv
import json
import math

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter
import contourpy
import shapely
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from vmap_build import MapBuilder, ROOT, CONFIG
import vmap_mesh as vm
from site_master import load_lidar, CELL
import building
import povo1
import povo2
import east_block

MAP = 'povo_site'                   # unlit layout builds; baked builds go to povo_site_lit
LIT = 'povo_site_lit'
E0, N0, Z0 = CONFIG['local_origin_metres']
U = CONFIG['hammer_units_per_metre_real'] * CONFIG['gameplay_scale']
STEP = 2.0          # terrain sample spacing, metres
TILE = 12           # samples per tile edge -> 24 m tiles
MAT = dict(
    asphalt='materials/asphalt/hr_c/hr_asphalt_001.vmat',
    paving='materials/cs_italy/ground/sidewalk_concrete_slabs_1.vmat',
    concrete='materials/concrete/hr_c/hr_concrete_floor_001.vmat',
    sidewalk='materials/povo/dark_paving.vmat',                     # dark grey street sidewalk
    path='materials/de_overpass/ground/sidewalk_cement_tile_02.vmat',
    grass='materials/de_overpass/nature/wild_grass_1.vmat',
    wall='materials/de_overpass/concrete/concrete_1_painted_white_hs.vmat',
    roof='materials/concrete/hr_c/hr_concrete_roof_001.vmat',
    house_roof='materials/cs_italy/tileroof01.vmat',
    house_wall='materials/de_overpass/concrete/concrete_5.vmat',
    red='materials/povo/red_paving.vmat',
)
ROAD_WIDTH = dict(secondary=7.5, tertiary=7.0, residential=6.0, unclassified=6.0,
                  service=4.5, living_street=5.0)
PATH_WIDTH = dict(footway=2.5, pedestrian=4.0, cycleway=2.5, path=1.8, track=3.0, steps=2.0)
TREES = [(6, ['models/foliage/trees/urban/urban_tree_small_1.vmdl']),
         (12, ['models/foliage/trees/maple/maple_01/maple_tree_01.vmdl',
               'models/foliage/trees/maple/maple_01/maple_tree_02.vmdl']),
         (99, ['models/foliage/trees/poplar/tree_poplar_mature_01.vmdl',
               'models/foliage/trees/poplar/tree_poplar_mature_02.vmdl',
               'models/cs_italy/foliage/tree/generic_tree_large_1.vmdl'])]


SPECS = [povo1.SPEC, povo2.MAIN, povo2.STRIP, east_block.MENSA, east_block.LIBRARY]
# (footprint, lowest floor) of the buildings built room by room; OSM blocks inside are skipped.
DETAILED = [(building.outline_en(s), s.origin[2] + s.levels[s.ordered()[0]]) for s in SPECS]
DETAILED.append((east_block.PASSAGE_EN, east_block.ORIGIN_Z))   # entrance stair pit
NOT_EXTRUDED = [povo2.bridge_outline_en()]          # spans between buildings, built separately
# The terrain is cut exactly at the detailed buildings' walls (no ditch round them) ...
CUT = unary_union([building.outline_en(s) for s in SPECS])
# Flat terraces at the buildings' ground level, ending in straight retaining walls (user):
# round Povo 1 at its -1 (LiDAR 373.3 m within 8 m on every side), along the -1 lane and the
# passage to the mensa and library, and the floors of Holes 1 and 3 at Povo 2's -2.
P2 = (povo2.MAIN.origin[0], povo2.MAIN.origin[1])
ZONES = [
    (unary_union([shapely.box(666221.3, 5103692.65, 666280.8, 5103786.05),       # Povo 1 + 6 m
                  shapely.box(666274.8, 5103689.0, 666287.5, 5103787.0),         # the -1 lane
                  shapely.box(666274.8, 5103722.7, 666297.0, 5103732.6)]),       # passage, to the stair
     east_block.ORIGIN_Z),
    (shapely.box(P2[0] + povo2.MAIN.X, P2[1], P2[0] + 77.7, P2[1] + povo2.STRIP_Y[0]), povo2.MAIN.origin[2]),
    (shapely.box(P2[0] + povo2.MAIN.X, P2[1] + povo2.STRIP_Y[1], P2[0] + 77.7, P2[1] + povo2.MAIN.Y),
     povo2.MAIN.origin[2]),
]
WALL = .3                                            # retaining wall thickness, outside the terraces
NATURAL_CUT = unary_union([CUT] + [z.buffer(WALL, join_style='mitre') for z, _l in ZONES])
# Campus hardscape: grey concrete round the buildings except clear lawns (user, 23-10 photo 34);
# young trees only near the buildings (user: no big trees by the university roads).
CAMPUS = unary_union([CUT.buffer(14), shapely.box(666274.8, 5103689.0, 666287.5, 5103787.0)])
CAMPUS_TREES = CUT.buffer(30)
RED = east_block.PASSAGE_EN                          # red paving only under the glass roof (P018, 34)


def world(e, n, z):
    return ((e - E0) * U, (n - N0) * U, (z - Z0) * U)


def areas(layers):
    """[(polygon, surface)], disjoint, top first: red paving, asphalt (roads, parking),
    footpaths (outside the campus hardscape). Terrain triangles are split along their edges."""
    red = RED
    asphalt = unary_union([Polygon(p['ring']) for p in layers['parking']] +
                          [LineString(r['line']).buffer(ROAD_WIDTH[r['tags']['highway']] / 2, cap_style='flat')
                           for r in layers['roads'] if r['tags'].get('highway') in ROAD_WIDTH and len(r['line']) > 1])
    paths = unary_union([LineString(p['line']).buffer(PATH_WIDTH.get(p['tags'].get('highway'), 2) / 2)
                         for p in layers['paths'] + layers['steps'] if len(p['line']) > 1])
    # In front of both Povos, from Via Sommarive towards the buildings (user, OSM sidewalks
    # 742336419 and 780554821): road, dark grey sidewalk 2.5 m, grass strip with the young
    # trees 3 m, then the light grey campus paving up to the walls or the plaza fence. In
    # front of the red entrance stair the grass opens and the red runs out to the sidewalk.
    parts = [LineString(r['line']) for r in layers['roads'] if r['tags'].get('name') == 'Via Sommarive'
             and r['tags'].get('oneway') != 'yes' and len(r['line']) > 1]
    street = shapely.line_merge(unary_union(parts).intersection(shapely.box(666290, 5103660, 666340, 5103900)))
    street = max(shapely.get_parts(street), key=lambda g: g.length)
    if street.coords[0][1] > street.coords[-1][1]:
        street = street.reverse()                     # south to north: its left is the campus side
    half = ROAD_WIDTH['tertiary'] / 2
    front = shapely.box(666280, 5103686, 666340, 5103912)
    kerb = street.buffer(half + 2.5, single_sided=True).intersection(front)
    verge = street.buffer(half + 5.5, single_sided=True).intersection(front).difference(kerb)
    opening = shapely.box(666297.0, 5103722.7, 666330, 5103732.6)
    red = unary_union([red, opening.difference(kerb).difference(street.buffer(half))])
    # On a 5 cm grid, so neighbouring areas share their edges exactly (no hair-thin slivers).
    snap = lambda g: shapely.set_precision(g, .05)
    red, asphalt, paths = snap(red), snap(asphalt), snap(paths)
    sidewalk = snap(kerb.difference(asphalt).difference(red))
    grass = snap(verge.difference(opening).difference(asphalt).difference(red))
    path = snap(paths.difference(asphalt).difference(red).difference(CAMPUS).difference(front))
    lawn = snap(lawns().difference(unary_union([red, asphalt, kerb, verge, path])))
    out = [(red, 'red'), (snap(asphalt.difference(red)), 'asphalt'), (sidewalk, 'sidewalk'), (grass, 'grass'),
           (path, 'path'), (lawn, 'grass')]
    for poly, _name in out:
        shapely.prepare(poly)
    return out


def lawns():
    """Grass areas from the 2024 orthophoto as smooth polygons: the share of green pixels over
    ~6 m, contoured at one half (stricter, two thirds, on the campus hardscape)."""
    e0, n0, e1, n1 = CONFIG['site_extent_metres']
    ortho = np.asarray(Image.open(ROOT / 'data/ortho/site_50cm.jpg').convert('RGB'), np.float32)
    gw = [float(v) for v in (ROOT / 'data/ortho/site_50cm.jgw').read_text().split()]
    c0, c1 = int((e0 - 10 - gw[4]) / gw[0]), int((e1 + 10 - gw[4]) / gw[0])
    r0, r1 = int((n1 + 10 - gw[5]) / gw[3]), int((n0 - 10 - gw[5]) / gw[3])
    crop = ortho[r0:r1, c0:c1]
    exg = 2 * crop[..., 1] - crop[..., 0] - crop[..., 2]
    green = uniform_filter((exg > 18).astype(np.float32), size=13)
    x = gw[4] + np.arange(c0, c1) * gw[0]
    y = gw[5] + np.arange(r0, r1) * gw[3]

    def above(level):
        gen = contourpy.contour_generator(x, y, green, fill_type='OuterOffset')
        polys = []
        for pts, offsets in zip(*gen.filled(level, 2.0)):
            rings = [pts[a:b] for a, b in zip(offsets, offsets[1:])]
            poly = Polygon(rings[0], rings[1:]).buffer(0)
            if poly.area > 4:
                polys.append(poly)
        return unary_union(polys).simplify(.3)
    return unary_union([above(.5).difference(CAMPUS), above(.65).intersection(CAMPUS)])


def surfaces(X, Y, regions):
    """(base, final) surface names at points (triangle centroids): base is the campus
    concrete or the town paving, final puts the areas (roads, grass...) on top."""
    base = np.where(shapely.contains_xy(CAMPUS, X, Y), 'concrete', 'paving').astype(object)
    final = base.copy()
    for poly, name in reversed(regions):
        final[shapely.contains_xy(poly, X, Y)] = name
    return base, final


class Welder:
    """Vertex lookup by position within 2 mm: neighbouring triangles compute the same crossing
    a hair apart, and rounding to a fixed grid can still split such a pair."""
    TOL = .002

    def __init__(self):
        self.cells = {}

    def add(self, e, n, k):
        self.cells.setdefault((math.floor(e / self.TOL), math.floor(n / self.TOL)), []).append((e, n, k))

    def find(self, e, n):
        ci, cj = math.floor(e / self.TOL), math.floor(n / self.TOL)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for x, y, k in self.cells.get((ci + di, cj + dj), ()):
                    if abs(x - e) <= self.TOL and abs(y - n) <= self.TOL:
                        return k
        return None


def arrangement(area, extra, regions):
    """Faces of `area` split by the extra lines and every area edge, noded together once so
    that all faces share their edges exactly: [(polygon, inner point, area name or None)]."""
    reach = area.buffer(1e-3)                  # edges reach just past, so every crossing is noded
    lines = [area.boundary] + extra + [reach.intersection(poly.boundary) for poly, _n in regions
                                       if poly.intersects(reach)]
    # Snap-rounded on a 1 mm grid: a corner a hair off a line still splits it (floating point).
    noded = shapely.union_all([g for g in lines if not g.is_empty], grid_size=1e-3)
    out = []
    for face in shapely.get_parts(shapely.polygonize(shapely.get_parts(noded))):
        inner = face.point_on_surface()
        if area.contains(inner):
            out.append((face, inner, next((n for poly, n in regions if poly.contains(inner)), None)))
    return out


def triangles(face):
    """Counter-clockwise triangles [(x, y)] * 3 of a polygon."""
    out = []
    for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(face)):
        pts = list(tri.exterior.coords)[:3]
        area = ((pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1]))
        if abs(area) > 1e-9:
            out.append(pts if area > 0 else pts[::-1])
    return out


def terrain(m, layers, dtm, extent):
    e0, n0, e1, n1 = extent
    nx, ny = round((e1 - e0) / STEP), round((n1 - n0) / STEP)
    xs = e0 + np.arange(nx + 1) * STEP
    ys = n0 + np.arange(ny + 1) * STEP
    # Node heights: mean of the 4 x 4 DTM cells around each node.
    grid = dtm['grid']
    heights = np.zeros((ny + 1, nx + 1))
    for j, y in enumerate(ys):
        r = int((dtm['n1'] - y) / CELL)
        for i, x in enumerate(xs):
            c = int((x - dtm['e0']) / CELL)
            heights[j, i] = np.nanmean(grid[r - 2:r + 2, c - 2:c + 2])
    X, Y = np.meshgrid(xs, ys)
    # Two triangles per cell, (i,j)(i+1,j)(i+1,j+1) and (i,j)(i+1,j+1)(i,j+1), each surfaced at its centroid.
    cx, cy = np.meshgrid(xs[:-1], ys[:-1])
    regions = areas(layers)
    (base0, surf0), (base1, surf1) = (surfaces(cx + STEP * 2 / 3, cy + STEP / 3, regions),
                                      surfaces(cx + STEP / 3, cy + STEP * 2 / 3, regions))
    surf, base = np.stack([surf0, surf1], axis=-1), np.stack([base0, base1], axis=-1)
    shapely.prepare(NATURAL_CUT)
    edges = unary_union([NATURAL_CUT.boundary] + [poly.boundary for poly, _n in regions])
    shapely.prepare(edges)

    def plane(i, j, t, x, y):
        """Height at (x, y) on triangle t of cell (i, j)."""
        dx, dy = (x - xs[i]) / STEP, (y - ys[j]) / STEP
        h00, h10, h11, h01 = heights[j, i], heights[j, i + 1], heights[j + 1, i + 1], heights[j + 1, i]
        if t == 0:                                     # (i,j) (i+1,j) (i+1,j+1): below the diagonal
            return h00 + dx * (h10 - h00) + dy * (h11 - h10)
        return h00 + dy * (h01 - h00) + dx * (h11 - h01)
    for tj in range(0, ny, TILE):
        for ti in range(0, nx, TILE):
            jj = range(tj, min(tj + TILE, ny) + 1)
            ii = range(ti, min(ti + TILE, nx) + 1)
            box = shapely.box(xs[ii[0]], ys[jj[0]], xs[ii[-1]], ys[jj[-1]])
            faces, verts, weld = [], [], Welder()

            def vertex(e, n, z):
                k = weld.find(e, n)
                if k is None:
                    k = len(verts)
                    verts.append(world(e, n, z))
                    weld.add(e, n, k)
                return k
            if not edges.intersects(box.buffer(.01)):
                # Plain grid: two triangles per cell, surfaced at their centroids.
                for j in list(jj)[:-1]:
                    for i in list(ii)[:-1]:
                        c = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                        for t, tri in enumerate(((0, 1, 2), (0, 2, 3))):
                            faces.append((tuple(vertex(xs[c[k][0]], ys[c[k][1]], heights[c[k][1], c[k][0]])
                                                for k in tri), MAT[surf[j, i, t]]))
            else:
                # Grid lines, cell diagonals, building and terrace cuts and area edges, noded together.
                grid = ([LineString([(xs[ii[0]], ys[j]), (xs[ii[-1]], ys[j])]) for j in jj] +
                        [LineString([(xs[i], ys[jj[0]]), (xs[i], ys[jj[-1]])]) for i in ii] +
                        [LineString([(xs[i], ys[j]), (xs[i + 1], ys[j + 1])]) for j in list(jj)[:-1]
                         for i in list(ii)[:-1]])
                area = box.difference(NATURAL_CUT)
                if area.is_empty:
                    continue
                for face, inner, name in arrangement(area, grid, regions):
                    i = min(int((inner.x - xs[0]) // STEP), nx - 1)
                    j = min(int((inner.y - ys[0]) // STEP), ny - 1)
                    t = 0 if inner.x - xs[i] > inner.y - ys[j] else 1
                    mat = MAT[name or base[j, i, t]]
                    for tri in triangles(face):
                        faces.append((tuple(vertex(x, y, plane(i, j, t, x, y)) for x, y in tri), mat))
            faces = [(f, mat) for f, mat in faces if len(set(f)) == len(f)]   # slivers merged to a line
            if faces:                                 # open sheets: the cuts leave holes at the walls
                m.mesh([(verts, faces)], (255, 255, 255), closed=False)
    terraces(m, regions, heights, xs, ys)
    return heights, xs, ys


def terraces(m, regions, heights, xs, ys):
    """Each flat terrace as one sheet at its level (surfaced like the terrain), and straight
    concrete retaining walls round it wherever it meets the natural ground."""
    def ground(e, n):
        i = int(np.clip(round((e - xs[0]) / STEP), 0, len(xs) - 1))
        j = int(np.clip(round((n - ys[0]) / STEP), 0, len(ys) - 1))
        return heights[j, i]
    done = []
    for zone, level in ZONES:
        area = zone.difference(CUT).difference(unary_union(done)) if done else zone.difference(CUT)
        done.append(zone)
        verts, faces, weld = [], [], Welder()

        def vertex(e, n):
            k = weld.find(e, n)
            if k is None:
                k = len(verts)
                verts.append(world(e, n, level))
                weld.add(e, n, k)
            return k
        for face, _inner, name in arrangement(area, [], regions):
            for tri in triangles(face):
                faces.append((tuple(vertex(x, y) for x, y in tri), MAT[name or 'concrete']))
        faces = [(f, mat) for f, mat in faces if len(set(f)) == len(f)]
        m.mesh([(verts, faces)], (255, 255, 255), closed=False)
        # Walls: along every edge of the terrace not against a building, in pieces of <= 2 m.
        walls = []
        for ring in [zone.exterior]:
            pts = list(ring.coords)
            ccw = ring.is_ccw
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                length = math.hypot(x1 - x0, y1 - y0)
                n = max(1, math.ceil(length / STEP))
                ox, oy = ((y1 - y0), -(x1 - x0)) if ccw else (-(y1 - y0), (x1 - x0))
                ox, oy = ox / length, oy / length                 # outward unit normal
                for k in range(n):
                    a = (x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n)
                    b = (x0 + (x1 - x0) * (k + 1) / n, y0 + (y1 - y0) * (k + 1) / n)
                    mid = ((a[0] + b[0]) / 2 + ox * .15, (a[1] + b[1]) / 2 + oy * .15)
                    if CUT.buffer(.05).contains(shapely.Point(mid)):
                        continue                                  # against a building wall
                    if any(z is not zone and z.buffer(.05).contains(shapely.Point(mid)) for z, _l in ZONES):
                        continue
                    nat = [ground(p[0] + ox * 1.0, p[1] + oy * 1.0) for p in (a, b)]
                    top, bottom = max(level, *nat), min(level, *nat) - .6
                    if top - bottom < .7 and abs(max(nat) - level) < .05:
                        continue
                    xs4 = [a[0], b[0], a[0] + ox * WALL, b[0] + ox * WALL]
                    ys4 = [a[1], b[1], a[1] + oy * WALL, b[1] + oy * WALL]
                    lo = world(min(xs4), min(ys4), bottom)
                    hi = world(max(xs4), max(ys4), top)
                    walls.append(vm.box(lo, hi, MAT['concrete']))
        for k in range(0, len(walls), 300):
            m.mesh(walls[k:k + 300])


def extruded(poly, z0, z1, wall, roof):
    """Closed prism over a polygon with holes, top/bottom triangulated."""
    return vm.prism(poly, z0, z1, wall, roof, wall, world)


def buildings(m, layers, extent):
    table = {r['id']: r for r in csv.DictReader(open(ROOT / 'data/derived/buildings.csv', encoding='utf8'))}
    box = shapely.box(*extent)
    footprints = []
    for b in layers['buildings']:
        poly = Polygon(b['ring'], b.get('holes', [])).buffer(0).simplify(.25)
        if poly.is_empty or not box.contains(poly.centroid) or poly.geom_type != 'Polygon':
            continue
        # Built in detail instead; OSM also maps canopies and overhangs just outside the walls.
        if any(o.buffer(2.5).contains(poly.centroid) for o in [outline for outline, _f in DETAILED] + NOT_EXTRUDED):
            continue
        row = table.get(str(b['id']))
        if not row or not row.get('roof_p50_abs'):
            continue
        house = b['tags'].get('building') in ('house', 'detached', 'apartments', 'residential')
        z0 = float(row['ground_min']) - .5
        z1 = max(float(row['roof_p50_abs']), z0 + 3)
        try:
            m.mesh([extruded(poly, z0, z1, MAT['house_wall' if house else 'wall'],
                             MAT['house_roof' if house else 'roof'])])
        except ValueError as err:
            print('skip building', b['id'], err)
            continue
        footprints.append(poly)
    return unary_union(footprints + [outline for outline, _floor in DETAILED])


def trees(m, layers, footprints, heights, xs, ys, extent, limit):
    rows = list(csv.DictReader(open(ROOT / 'data/derived/trees.csv', encoding='utf8')))
    e0, n0, e1, n1 = extent
    # Street rows (Via Sommarive etc.) are young, slender trees (P002, P009, P061).
    streets = unary_union([LineString(r['line']) for r in layers['roads']
                           if r['tags'].get('highway') in ('secondary', 'tertiary', 'residential', 'unclassified')
                           and len(r['line']) > 1]).buffer(9)
    placed = []
    for r in sorted(rows, key=lambda r: r['source'] != 'osm'):
        if len(placed) >= limit:
            break
        e, n, h = float(r['e']), float(r['n']), float(r.get('height_m') or 8)
        if not (e0 + 2 < e < e1 - 2 and n0 + 2 < n < n1 - 2) or h < 2.5:
            continue
        if footprints.buffer(1).contains(shapely.Point(e, n)):
            continue
        campus = CAMPUS_TREES.contains(shapely.Point(e, n))
        if campus and r['source'] != 'osm':
            continue                  # LiDAR canopy peaks near the buildings: often not real trees
        if any((e - a) ** 2 + (n - b) ** 2 < 16 for a, b in placed):
            continue
        placed.append((e, n))
        z = heights[int((n - ys[0]) / STEP), int((e - xs[0]) / STEP)]
        street = campus or streets.contains(shapely.Point(e, n))
        models = TREES[0][1] if street else next(ms for top, ms in TREES if h <= top)
        model = models[(int(e * 7 + n * 13)) % len(models)]
        # The cloned example prop carries a magenta rendercolor.
        tree = m.entity('prop_static', dict(model=model, solid=6, disableshadows=0, rendercolor='255 255 255 255'),
                        world(e, n, z - .1), f'0 {int(e * 37 + n * 11) % 360} 0')
        if street:
            s = 0.7 + (int(e * 13 + n * 3) % 5) * .04
            tree.set('scales', f'{s:.2f} {s:.2f} {s:.2f}', 'vector3')
    return len(placed)


def build(tree_limit, name=MAP):
    layers = json.loads((ROOT / 'data/derived/site_layers.json').read_text(encoding='utf8'))
    dtm = load_lidar('DTM')
    extent = CONFIG['site_extent_metres']
    m = MapBuilder(name)
    heights, xs, ys = terrain(m, layers, dtm, extent)
    footprints = buildings(m, layers, extent)
    n_trees = trees(m, layers, footprints, heights, xs, ys, extent, tree_limit)
    building.build(m, world, U, povo1.SPEC)
    povo2.build(m, world, U)
    building.build(m, world, U, east_block.MENSA)
    building.build(m, world, U, east_block.LIBRARY)

    def ground(e, n):
        # Highest corner of the terrain cell, so the player hull clears the slope.
        j, i = int((n - ys[0]) / STEP), int((e - xs[0]) / STEP)
        return heights[j:j + 2, i:i + 2].max() + .25
    # Provisional starts on the Via Sommarive centreline (E ~666314), clear of buildings:
    # T north by Povo 2, CT south by Povo 1.
    for team, (e, n), yaw in (('info_player_terrorist', (666317, 5103880), 270),
                              ('info_player_counterterrorist', (666314, 5103690), 90)):
        for k in range(3):
            m.entity(team, dict(enabled=1, priority=0), world(e - 2 + 2 * k, n, ground(e - 2 + 2 * k, n)),
                     f'0 {yaw} 0')
    m.set_kept('env_sky', dict(skyname='materials/skybox/sky_de_overpass_01.vmat'))   # sunny, blue (user, P011)
    # The template's fog suits a small Wingman map; the site spans ~30,000 u. Light valley haze.
    m.set_kept('env_cubemap_fog', dict(cubemapfogstartdistance=2000, cubemapfogenddistance=40000,
                                       cubemapheightfog=0, cubemapfogmaxopacity=0.3))
    print(f'{len(m.new)} elements, {n_trees} trees')
    return m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-compile', action='store_true')
    parser.add_argument('--trees', type=int, default=600)
    parser.add_argument('--quality', type=int, default=0)
    parser.add_argument('--vis', action='store_true', help='run the visibility pass (over 2 h on this map)')
    parser.add_argument('--bake', action='store_true', help='bake lightmaps (default: unlit test build)')
    args = parser.parse_args()
    lit = args.bake or args.vis
    raise SystemExit(build(args.trees, LIT if lit else MAP).deploy(not args.no_compile, args.quality,
                                                                   args.vis, lit))
