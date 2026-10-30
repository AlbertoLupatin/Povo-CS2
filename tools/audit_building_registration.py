#!/usr/bin/env python3
"""Check campus building footprints and roads against OpenStreetMap and PAT LiDAR.

The generated campus OBJ is rasterised onto the 0.5 m PAT DTM/DBM grid as a
top-surface height map. Each OSM building is compared with the game's
building cells and with the LiDAR building mask (DBM - DTM > 2.5 m); each OSM
road centreline is compared with the game's asphalt. Deviations are reported
per facade side and as a best-fit translation, alongside roof heights.

Game building height is measured from the game's own exterior ground, because
the edge scenery stands on deliberately flattened grades. OSM and LiDAR each
carry roughly 0.5-1 m of error; treat sub-metre differences as agreement.

Inputs: exports/povo_campus OBJ, data/reference/osm (fetch_osm_extract.py),
data/raw/terrain DTM/DBM, data/reference/povo_ortho_2024.png.
"""
import argparse
import json
import re
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CAMPUS = ROOT / 'exports/povo_campus'
OBJS = (CAMPUS / 'povo1_campus.obj', CAMPUS / 'povo1_campus_paving.obj')
OSM = ROOT / 'data/reference/osm/povo_osm_overture.geojson'
DTM = ROOT / 'data/raw/terrain/5h666051035_DTM.asc'
DBM = ROOT / 'data/raw/terrain/5h666051035_DBM.asc'
ORTHO = ROOT / 'data/reference/povo_ortho_2024.png'
OUT = ROOT / 'exports/building_registration_20261030'
ORIGIN = tuple(json.loads((ROOT / 'config/povo_blockout.json').read_text())['origin'])
WEST, NORTH, CELL, SIZE = 666000.0, 5104000.0, 0.5, 1000     # PAT tile grid edges
BUILDING_HEIGHT = 2.5
TERRITORY = 12.0   # metres around a footprint searched for its game/LiDAR mass
BURIED_TOLERANCE, BURIED_STOREY = 1.0, 5.0
# Vegetation, vehicles and people are neither ground nor building.
SKIP = re.compile(r'ginkgo|tree|trunk|bus|car_|_car|staff|tyre|mirror|light$')
# Ground slabs, retaining walls, railings and glass canopies (LiDAR misses glass): never building mass.
NOT_BUILDING = ('campus_exterior_context_concrete', 'campus_exterior_concrete', 'campus_exterior_fence',
                'campus_exterior_canopy_glass')
# Open surfaces: where one is the visible top, the cell is game ground.
GROUND = re.compile(r'^campus_(exterior_(asphalt|paving|marking|grass|grout|context_concrete)|floor_(p2_tile|p2_asphalt|yard_grass)|courtyard_ground|parking_line)$')
ASPHALT = re.compile(r'^campus_exterior_(asphalt|marking)$')
NOT_DRIVEN = {'footway', 'path', 'steps', 'cycleway', 'pedestrian', 'track', 'bridleway'}
SIDES = ('E', 'N', 'W', 'S')
# Scenery volumes traced by hand from the aerial, paired with the OSM building they represent.
PROPOSAL_TARGETS = (
    ('config/povo_edges.json buildings[fbk_north]', 'w28933741'),
    ('config/povo_edges.json buildings[fbk_south_west]', 'r1185625'),
    ('config/povo_edges.json buildings[fbk_south_east]', 'r1185627'),
    ('config/povo_edges.json buildings[fbk_south_link]', 'w1194202499'),
    ('config/povo_edges.json buildings[fbk_far_south_north]', 'w42648436'),
    ('config/povo_edges.json buildings[fbk_far_south_east]', 'w42648467'),
    ('config/povo_edges.json buildings[fbk_far_south_west, fbk_far_south_south]', 'r1185626'),
    ('config/povo_exterior.json residential', 'w275318458'),
)


# ---------------------------------------------------------------- rasters

def read_asc(path):
    lines = Path(path).read_text().split('\n', 6)
    header = {l.split()[0].lower(): float(l.split()[1]) for l in lines[:6]}
    grid = np.array(lines[6].split(), dtype=float).reshape(int(header['nrows']), int(header['ncols']))
    if (header['xllcenter'] - CELL / 2, header['yllcenter'] - CELL / 2 + header['nrows'] * CELL) != (WEST, NORTH):
        raise ValueError(f'{path} is not the expected PAT tile')
    return grid


def rasterise_obj(paths, keep):
    """Highest surface per cell for faces whose material passes keep(material)."""
    vertices, faces, materials = [], [], []
    for path in paths:
        base, material = len(vertices), ''
        with open(path) as stream:
            for line in stream:
                if line.startswith('v '):
                    _, x, y, z = line.split()[:4]; vertices.append((float(x), float(y), float(z)))
                elif line.startswith('usemtl'):
                    material = line.split()[1]
                elif line.startswith('f ') and keep(material):
                    ids = [int(t.split('/')[0]) + base - 1 for t in line.split()[1:]]
                    for k in range(1, len(ids) - 1):
                        faces.append((ids[0], ids[k], ids[k + 1])); materials.append(material)
    names = sorted(set(materials))
    material_id = np.array([names.index(m) for m in materials], np.int16)
    tri = np.array(vertices)[np.array(faces)] + np.array(ORIGIN)
    edge = np.max(np.linalg.norm(tri[:, [1, 2, 0], :2] - tri[:, :, :2], axis=2), axis=1)
    steps = np.clip(np.ceil(edge / 0.2).astype(int), 1, 600)
    top = np.full((SIZE, SIZE), -np.inf); top_material = np.full((SIZE, SIZE), -1, np.int16)
    for n in np.unique(steps):
        chosen = np.nonzero(steps == n)[0]
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij'); inside = i + j <= n
        a, b = (i[inside] / n)[None, :, None], (j[inside] / n)[None, :, None]
        for chunk in np.array_split(chosen, len(chosen) * a.shape[1] // 4_000_000 + 1):
            t = tri[chunk]
            p = t[:, None, 0] + a * (t[:, None, 1] - t[:, None, 0]) + b * (t[:, None, 2] - t[:, None, 0])
            col = np.floor((p[..., 0] - WEST) / CELL).astype(int); row = np.floor((NORTH - p[..., 1]) / CELL).astype(int)
            z, m = p[..., 2], np.broadcast_to(material_id[chunk][:, None], p.shape[:2])
            ok = (col >= 0) & (col < SIZE) & (row >= 0) & (row < SIZE)
            order = np.argsort(z[ok])                       # duplicate cells keep the highest write
            row, col, z, m = row[ok][order], col[ok][order], z[ok][order], m[ok][order]
            higher = z > top[row, col]
            top[row[higher], col[higher]] = z[higher]; top_material[row[higher], col[higher]] = m[higher]
    return top, top_material, names


def fill_nearest(grid):
    """Fill non-finite cells from their nearest finite neighbours by repeated dilation."""
    grid = grid.copy(); known = np.isfinite(grid)
    while not known.all():
        total = np.zeros_like(grid); count = np.zeros(grid.shape)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            shifted_known = np.roll(np.roll(known, dr, 0), dc, 1)
            total += np.where(shifted_known, np.roll(np.roll(np.where(known, grid, 0), dr, 0), dc, 1), 0)
            count += shifted_known
        new = ~known & (count > 0)
        if not new.any(): break
        grid[new] = total[new] / count[new]; known |= new
    return grid


def erode(mask, n=1):
    for _ in range(n):
        m = mask.copy()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            m &= np.roll(np.roll(mask, dr, 0), dc, 1)
        mask = m
    return mask


def dilate(mask, n=1):
    return ~erode(~mask, n)


def opening(mask):
    return dilate(erode(mask))


def label(mask):
    """4-connected component labels (pure Python BFS; masks here are sparse)."""
    labels = np.zeros(mask.shape, int); current = 0
    for r, c in zip(*np.nonzero(mask)):
        if labels[r, c]: continue
        current += 1; labels[r, c] = current; queue = deque([(r, c)])
        while queue:
            y, x = queue.popleft()
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not labels[yy, xx]:
                    labels[yy, xx] = current; queue.append((yy, xx))
    return labels, current


# ---------------------------------------------------------------- geometry

def to_pixel(x, y):
    return (x - WEST) / CELL, (NORTH - y) / CELL


def cell_centres(rows, cols):
    return WEST + (cols + .5) * CELL, NORTH - (rows + .5) * CELL


def polygons(geometry):
    return geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]


def lines(geometry):
    return geometry['coordinates'] if geometry['type'] == 'MultiLineString' else [geometry['coordinates']]


def rasterise_polygon(geometry, grow=0.0):
    """Cells whose centre lies in the polygon, or within grow metres of it."""
    mask = np.zeros((SIZE, SIZE), bool)
    segments = boundary_segments(geometry)
    x0, y0 = segments[..., 0].min() - grow, segments[..., 1].min() - grow
    x1, y1 = segments[..., 0].max() + grow, segments[..., 1].max() + grow
    c0, c1 = max(0, int((x0 - WEST) / CELL)), min(SIZE, int((x1 - WEST) / CELL) + 1)
    r0, r1 = max(0, int((NORTH - y1) / CELL)), min(SIZE, int((NORTH - y0) / CELL) + 1)
    if c0 >= c1 or r0 >= r1: return mask
    rows, cols = np.mgrid[r0:r1, c0:c1]
    x, y = cell_centres(rows.ravel(), cols.ravel())
    inside = np.zeros(x.shape, bool)
    for (ax, ay), (bx, by) in segments:                 # even-odd rule over all rings
        crosses = (ay > y) != (by > y)
        inside ^= crosses & (x < ax + (y - ay) * (bx - ax) / np.where(by == ay, 1, by - ay))
    if grow > 0:
        outside = ~inside
        distance, _ = nearest_on_boundary(np.stack([x[outside], y[outside]], 1), segments)
        inside[np.nonzero(outside)[0][distance <= grow]] = True
    mask[r0:r1, c0:c1] = inside.reshape(rows.shape)
    return mask


def boundary_segments(geometry):
    segments = []
    for rings in polygons(geometry):
        for ring in rings:
            ring = np.array(ring)
            segments.append(np.stack([ring[:-1], ring[1:]], 1))
    return np.concatenate(segments)


def nearest_on_boundary(points, segments):
    """Distance from each point to the polygon boundary and the nearest boundary point."""
    a, b = segments[:, 0], segments[:, 1]; ab = b - a
    length = np.maximum((ab ** 2).sum(1), 1e-12)
    best_d = np.full(len(points), np.inf); best_p = np.zeros_like(points)
    for start in range(0, len(points), 4000):
        p = points[start:start + 4000, None, :]
        t = np.clip(((p - a) * ab).sum(2) / length, 0, 1)
        q = a + t[..., None] * ab; d = np.linalg.norm(p - q, axis=2)
        k = d.argmin(1); best_d[start:start + 4000] = d[np.arange(len(k)), k]
        best_p[start:start + 4000] = q[np.arange(len(k)), k]
    return best_d, best_p


def side_of(dx, dy):
    return ((np.degrees(np.arctan2(dy, dx)) + 45) % 360 // 90).astype(int)


def facade_lengths(geometry):
    """Boundary length per side, by each segment's outward normal."""
    lengths = np.zeros(len(SIDES))
    for rings in polygons(geometry):
        for k, ring in enumerate(rings):
            r = np.array(ring); d = np.diff(r, axis=0)
            ccw = np.dot(r[:-1, 0], r[1:, 1]) - np.dot(r[1:, 0], r[:-1, 1]) > 0
            sign = (1 if ccw else -1) * (-1 if k else 1)      # holes face into the hole
            np.add.at(lengths, side_of(sign * d[:, 1], -sign * d[:, 0]), np.linalg.norm(d, axis=1))
    return lengths


def side_deviation(cells, geometry, outward):
    """Mismatched cells grouped by the facade side they sit on.

    mean_offset_m is the mismatch area over that side's facade length: the
    average distance by which the game facade misses the OSM one. Small
    attached structures raise depth_p95_m but barely move the mean offset.
    """
    rows, cols = np.nonzero(cells)
    if not len(rows): return {}
    points = np.stack(cell_centres(rows, cols), 1)
    distance, nearest = nearest_on_boundary(points, boundary_segments(geometry))
    vector = (points - nearest) * (1 if outward else -1)
    side = side_of(vector[:, 0], vector[:, 1]); lengths = facade_lengths(geometry)
    out = {}
    for k, name in enumerate(SIDES):
        chosen = side == k; area = chosen.sum() * CELL * CELL
        if area >= 5:
            out[name] = dict(mean_offset_m=round(float(area / max(lengths[k], 5.0)), 1),
                             depth_p95_m=round(float(np.percentile(distance[chosen], 95)), 1), area_m2=round(float(area)))
    return out


def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))


def best_shift(moving, fixed, window, limit=10.0):
    """Translation (east, north) in metres that best maps moving onto fixed."""
    r0, r1, c0, c1 = window; pad = int(limit / CELL)
    m = np.pad(moving[r0:r1, c0:c1], pad); f = np.pad(fixed[r0:r1, c0:c1], pad)
    best = (iou(m, f), 0, 0)
    for dr in range(-pad, pad + 1):
        rolled = np.roll(m, dr, 0)
        for dc in range(-pad, pad + 1):
            score = iou(np.roll(rolled, dc, 1), f)
            if score > best[0] + 1e-9: best = (score, dr, dc)
    return [round(best[2] * CELL, 1), round(-best[1] * CELL, 1)], round(best[0], 2)


# ---------------------------------------------------------------- audit

def load_osm(path):
    data = json.loads(Path(path).read_text())
    inside = lambda xs, ys: max(xs) > WEST and min(xs) < WEST + SIZE * CELL and max(ys) > NORTH - SIZE * CELL and min(ys) < NORTH
    buildings, roads = [], []
    for f in data['features']:
        p = f['properties']; g = f['geometry']
        if p['kind'] == 'building' and g['type'] in ('Polygon', 'MultiPolygon'):
            xy = np.concatenate([np.array(r[0]) for r in polygons(g)])
            if inside(xy[:, 0], xy[:, 1]): buildings.append(f)
        elif p['kind'] == 'road' and p.get('class') not in NOT_DRIVEN:
            xy = np.concatenate([np.array(l) for l in lines(g)])
            if inside(xy[:, 0], xy[:, 1]): roads.append(f)
    return data, buildings, roads


def polygon_area(geometry):
    total = 0.0
    for rings in polygons(geometry):
        for k, ring in enumerate(rings):
            r = np.array(ring); a = .5 * abs(np.dot(r[:-1, 0], r[1:, 1]) - np.dot(r[1:, 0], r[:-1, 1]))
            total += -a if k else a
    return total


def verdict(row):
    sides = list(row['game_overhang'].values()) + list(row['game_shortfall'].values())
    worst = max([v['mean_offset_m'] for v in sides] or [0])
    row['worst_side_offset_m'] = worst
    if row['iou_game_osm'] < .25: return 'generic'      # nearby mass does not represent this building
    if row['iou_game_osm'] >= .85 and worst <= 1.5: return 'ok'
    if row['iou_game_osm'] >= .7 and worst <= 3: return 'minor'
    return 'off'


def audit(objs=OBJS, osm=OSM):
    dtm, dbm = read_asc(DTM), read_asc(DBM)
    top, top_material, names = rasterise_obj(objs, lambda m: not SKIP.search(m))
    open_ground = np.isin(top_material, [i for i, n in enumerate(names) if GROUND.match(n)])
    road_top, road_material, road_names = rasterise_obj(objs, lambda m: bool(ASPHALT.match(m)))
    game_ground = fill_nearest(np.where(open_ground, top, np.nan))
    excluded = [names.index(n) for n in NOT_BUILDING if n in names]
    raised = np.isfinite(top) & ~open_ground & (top - game_ground > BUILDING_HEIGHT) & ~np.isin(top_material, excluded)
    # A single storey whose roof is flush with the real terrain is buried beside a sunken game
    # lane or garden: LiDAR cannot see it, so it is reported apart from the visible mass.
    buried = raised & (top <= dtm + BURIED_TOLERANCE) & (top - game_ground < BURIED_STOREY)
    game = opening(raised & ~buried)
    lidar = opening(dbm - dtm > BUILDING_HEIGHT)
    asphalt = np.isfinite(road_top)
    data, buildings, roads = load_osm(osm)

    # Larger footprints first so nested parts (annex bars inside a podium) own their cells.
    buildings.sort(key=lambda f: -polygon_area(f['geometry']))
    owner = np.full((SIZE, SIZE), -1)
    masks = []
    for i, f in enumerate(buildings):
        m = rasterise_polygon(f['geometry']); owner[m] = i; masks.append(m)
    # Outside footprints, each cell within TERRITORY metres belongs to the nearest building.
    nearest = np.where(owner >= 0, 0.0, np.inf); territory = owner.copy()
    for i, f in enumerate(buildings):
        rr, cc = np.nonzero(rasterise_polygon(f['geometry'], grow=TERRITORY) & (owner == -1))
        if not len(rr): continue
        d, _ = nearest_on_boundary(np.stack(cell_centres(rr, cc), 1), boundary_segments(f['geometry']))
        closer = d < nearest[rr, cc]
        nearest[rr[closer], cc[closer]] = d[closer]; territory[rr[closer], cc[closer]] = i

    rows = []
    for i, f in enumerate(buildings):
        g, p = f['geometry'], f['properties']
        near = territory == i
        own = masks[i] & (owner == i)
        game_i, lidar_i = game & near, lidar & near
        if game_i.sum() * CELL * CELL < 20 or own.sum() < 20: continue
        rr, cc = np.nonzero(near)
        window = (rr.min(), rr.max() + 1, cc.min(), cc.max() + 1)
        core = erode(own, 3) if erode(own, 3).sum() > 20 else own
        ring = rasterise_polygon(g, grow=3) & ~rasterise_polygon(g, grow=1) & (owner == -1)
        roof_l, roof_g = dbm[core & lidar_i], top[core & game_i]
        row = dict(osm=p['osm'], name=p.get('name'), osm_class=p.get('class'),
                   centroid_epsg25832=[round(float(v), 1) for v in np.stack(cell_centres(*np.nonzero(own)), 1).mean(0)],
                   osm_area_m2=round(float(own.sum() * CELL * CELL)), game_area_m2=round(float(game_i.sum() * CELL * CELL)),
                   lidar_area_m2=round(float(lidar_i.sum() * CELL * CELL)),
                   iou_game_osm=round(iou(game_i, own), 2), iou_game_lidar=round(iou(game_i, lidar_i), 2),
                   iou_lidar_osm=round(iou(lidar_i, own), 2),
                   game_overhang=side_deviation(game_i & ~own, g, True),
                   game_shortfall=side_deviation(own & ~game_i, g, False))
        row['shift_game_to_osm_m'], row['iou_after_osm_shift'] = best_shift(game_i, own, window)
        row['shift_game_to_lidar_m'], row['iou_after_lidar_shift'] = best_shift(game_i, lidar_i, window)
        if roof_l.size > 20 and ring.sum() > 20:
            row['lidar_roof_p95_m'] = round(float(np.percentile(roof_l, 95)), 1)
            row['lidar_height_m'] = round(float(np.percentile(roof_l, 95) - np.median(dtm[ring])), 1)
        if roof_g.size > 20 and ring.sum() > 20:
            row['game_roof_p95_m'] = round(float(np.percentile(roof_g, 95)), 1)
            row['game_height_m'] = round(float(np.percentile(roof_g, 95) - np.median(game_ground[ring])), 1)
            row['game_ground_minus_dtm_m'] = round(float(np.median(game_ground[ring] - dtm[ring])), 1)
        row['game_buried_storey_m2'] = round(float((opening(buried) & near & ~own).sum() * CELL * CELL))
        row['verdict'] = verdict(row)
        rows.append(row)
    rows.sort(key=lambda r: -r['osm_area_m2'])

    # Game building mass with no OSM building within 3 m.
    covered = np.zeros((SIZE, SIZE), bool)
    for f in buildings: covered |= rasterise_polygon(f['geometry'], grow=3)
    labels, count = label(game & ~covered)
    unmatched = []
    for k in range(1, count + 1):
        rr, cc = np.nonzero(labels == k)
        if len(rr) * CELL * CELL < 40: continue
        x, y = cell_centres(rr, cc)
        unmatched.append(dict(area_m2=round(len(rr) * CELL * CELL), centroid_epsg25832=[round(float(x.mean()), 1), round(float(y.mean()), 1)],
                              bounds_epsg25832=[round(float(x.min()) - .25, 1), round(float(y.min()) - .25, 1), round(float(x.max()) + .25, 1), round(float(y.max()) + .25, 1)],
                              lidar_building_fraction=round(float(lidar[rr, cc].mean()), 2)))
    unmatched.sort(key=lambda u: -u['area_m2'])

    road_rows, samples = audit_roads(roads, asphalt, road_top, dtm)
    layers = dict(game=game, lidar=lidar, asphalt=asphalt)
    report = dict(
        generated_from=dict(objs=[str(Path(o).relative_to(ROOT)) for o in objs], osm=str(Path(osm).relative_to(ROOT)),
                            osm_source=data.get('source'), osm_licence=data.get('licence'), osm_retrieved_utc=data.get('retrieved_utc'),
                            lidar='PAT LiDAR DTM/DBM 2014-2018 tile 5h666051035, CC BY 4.0', grid_m=CELL),
        method=dict(game_building=f'top surface > {BUILDING_HEIGHT} m above the nearest open game ground (exterior ground or open-air floor seen from above); ground slabs, retaining walls, railings and glass canopies excluded; a storey with its roof within 1 m of the DTM and under 5 m above the sunken game ground counts as buried (game_buried_storey_m2)',
                    lidar_building=f'DBM - DTM > {BUILDING_HEIGHT} m', verdicts='ok: IoU>=0.85 and worst side mean offset<=1.5 m; minor: IoU>=0.7 and <=3 m; generic: IoU<0.25 (not traced individually); otherwise off',
                    sides='overhang: game outside OSM; shortfall: OSM not covered by game; depth is the 95th percentile distance from the OSM facade',
                    shift='best translation (east, north) of the game footprint within +/-10 m'),
        buildings=rows, game_only_mass=unmatched, roads=road_rows, proposed_footprints=proposals(buildings, rows))
    return report, layers, buildings, roads, samples


def audit_roads(roads, asphalt, road_top, dtm):
    def cell(x, y): return int((NORTH - y) / CELL), int((x - WEST) / CELL)
    offsets = np.arange(-15, 15.01, .25)
    rows, samples = [], []
    for f in roads:
        p = f['properties']; found = []; total = 0
        for line in lines(f['geometry']):
            line = np.array(line)
            seg = np.linalg.norm(np.diff(line, axis=0), axis=1); along = np.concatenate([[0], np.cumsum(seg)])
            for s in np.arange(0, along[-1] + 1e-9, 2.0):
                k = min(np.searchsorted(along, s, side='right') - 1, len(seg) - 1)
                if seg[k] == 0: continue
                t = (s - along[k]) / seg[k]; x, y = line[k] + t * (line[k + 1] - line[k])
                r0, c0 = cell(x, y)
                if not (0 <= r0 < SIZE and 0 <= c0 < SIZE): continue
                tx, ty = (line[k + 1] - line[k]) / seg[k]; nx, ny = -ty, tx
                total += 1
                hits = np.array([0 <= cell(x + nx * o, y + ny * o)[0] < SIZE and 0 <= cell(x + nx * o, y + ny * o)[1] < SIZE
                                 and asphalt[cell(x + nx * o, y + ny * o)] for o in offsets])
                runs, start = [], None
                for i, h in enumerate(hits):
                    if h and start is None: start = i
                    if start is not None and (not h or i == len(hits) - 1):
                        runs.append((offsets[start], offsets[i if h else i - 1])); start = None
                runs = [(a, b) for a, b in runs if a <= 6 and b >= -6]
                if not runs:
                    samples.append((x, y, None)); continue
                a, b = min(runs, key=lambda ab: 0 if ab[0] <= 0 <= ab[1] else min(abs(ab[0]), abs(ab[1])))
                mid = (a + b) / 2; rm, cm = cell(x + nx * mid, y + ny * mid)
                found.append((mid, nx * mid, ny * mid, b - a + CELL, road_top[rm, cm] - dtm[rm, cm]))
                samples.append((x, y, abs(mid)))
        if total < 5: continue
        row = dict(osm=p['osm'], name=p.get('name'), osm_class=p.get('class'), samples=total, modelled_fraction=round(len(found) / total, 2))
        if found:
            v = np.array(found)
            row.update(offset_median_m=round(float(np.median(np.abs(v[:, 0]))), 1), offset_p90_m=round(float(np.percentile(np.abs(v[:, 0]), 90)), 1),
                       mean_shift_en_m=[round(float(v[:, 1].mean()), 1), round(float(v[:, 2].mean()), 1)],
                       game_width_median_m=round(float(np.median(v[:, 3])), 1),
                       game_minus_dtm_median_m=round(float(np.median(v[:, 4])), 1), game_minus_dtm_p90_abs_m=round(float(np.percentile(np.abs(v[:, 4]), 90)), 1))
        rows.append(row)
    rows.sort(key=lambda r: -r['samples'])
    return rows, samples


def simplify(ring, tolerance):
    """Douglas-Peucker on a closed ring (first point repeated last)."""
    points = np.array(ring, float)
    def keep(a, b):
        if b <= a + 1: return [a]
        p, q = points[a], points[b]; d = q - p; mid = points[a + 1:b]
        dist = np.abs(d[0] * (mid[:, 1] - p[1]) - d[1] * (mid[:, 0] - p[0])) / max(np.hypot(*d), 1e-9)
        k = int(dist.argmax())
        return keep(a, a + 1 + k) + keep(a + 1 + k, b) if dist[k] > tolerance else [a]
    far = int(np.linalg.norm(points - points[0], axis=1).argmax())
    out = points[keep(0, far) + keep(far, len(points) - 1) + [len(points) - 1]]
    return [[round(float(x - ORIGIN[0]), 1), round(float(y - ORIGIN[1]), 1)] for x, y in out]


def proposals(buildings, rows):
    """OSM footprints for the hand-traced scenery volumes, in campus local metres. Not applied."""
    by_osm = {f['properties']['osm']: f for f in buildings}; by_row = {r['osm']: r for r in rows}
    out = []
    for target, osm in PROPOSAL_TARGETS:
        if osm not in by_osm: continue
        geometry, row = by_osm[osm]['geometry'], by_row.get(osm, {})
        out.append(dict(target=target, osm=osm, name=by_osm[osm]['properties'].get('name'),
                        footprints_local_m=[[simplify(ring, .75) for ring in rings] for rings in polygons(geometry)],
                        area_m2=round(polygon_area(geometry)), current_iou_game_osm=row.get('iou_game_osm'),
                        lidar_height_above_ground_m=row.get('lidar_height_m'), game_height_m=row.get('game_height_m')))
    return dict(note='Proposal only, not applied. OSM footprints (ODbL, (c) OpenStreetMap contributors) as campus local metres '
                     f'(EPSG:25832 minus origin {ORIGIN[0]:.0f}, {ORIGIN[1]:.0f}), Douglas-Peucker 0.75 m; first ring outer, others courtyards. '
                     'Height: LiDAR DBM roof p95 minus DTM around the footprint.', proposals=out)


# ---------------------------------------------------------------- images

COLOURS = dict(both=(255, 255, 255), game=(255, 0, 200), lidar=(0, 200, 255), osm=(255, 220, 0), road=(255, 130, 0))
VERDICT_COLOURS = dict(ok=(80, 220, 90), minor=(255, 190, 0), off=(255, 50, 40), generic=(170, 170, 170))


def overlay(layers, buildings, roads, bounds, scale, title, rows=(), samples=None):
    x0, y0, x1, y1 = bounds
    c0, c1 = int((x0 - WEST) / CELL), int((x1 - WEST) / CELL); r0, r1 = int((NORTH - y1) / CELL), int((NORTH - y0) / CELL)
    base = np.array(Image.open(ORTHO).convert('RGB'))[r0:r1, c0:c1].astype(float) * .6
    g, l = layers['game'][r0:r1, c0:c1], layers['lidar'][r0:r1, c0:c1]
    for mask, colour, keep in ((l & ~g, 'lidar', .3), (g & ~l, 'game', .3), (g & l, 'both', .45)):
        base[mask] = base[mask] * keep + np.array(COLOURS[colour]) * (1 - keep)
    image = Image.fromarray(base.clip(0, 255).astype(np.uint8)).resize(((c1 - c0) * scale, (r1 - r0) * scale), Image.NEAREST)
    draw = ImageDraw.Draw(image)
    px = lambda x, y: (((x - WEST) / CELL - c0) * scale, ((NORTH - y) / CELL - r0) * scale)
    for f in buildings:
        for rings in polygons(f['geometry']):
            draw.line([px(*p) for p in rings[0]], fill=COLOURS['osm'], width=max(2, scale // 2))
    for f in roads:
        for line in lines(f['geometry']):
            draw.line([px(*p) for p in line], fill=COLOURS['road'], width=max(1, scale // 3))
    if samples is not None:
        for x, y, off in samples:
            if x0 <= x <= x1 and y0 <= y <= y1:
                colour = (150, 150, 150) if off is None else (80, 220, 90) if off <= 1.5 else (255, 190, 0) if off <= 3 else (255, 50, 40)
                cx, cy = px(x, y); draw.ellipse((cx - scale, cy - scale, cx + scale, cy + scale), fill=colour)
    for row in rows:
        cx, cy = px(*row['centroid_epsg25832'])
        if 0 <= cx < image.width and 0 <= cy < image.height:
            text = f"{row['name'] or row['osm']}: {row['verdict']}"
            draw.rectangle((cx - 3, cy - 3, cx + 7 * len(text) + 4, cy + 13), fill=(0, 0, 0))
            draw.text((cx, cy - 1), text, fill=VERDICT_COLOURS[row['verdict']])
    for x in range(int(np.ceil(x0 / 10) * 10), int(x1) + 1, 10):
        draw.line([px(x, y1), (px(x, y1)[0], 10 if x % 50 else 20)], fill=(220, 220, 220))
        if x % 50 == 0: draw.text((px(x, y1)[0] + 3, 2), str(x), fill=(255, 255, 255))
    for y in range(int(np.ceil(y0 / 10) * 10), int(y1) + 1, 10):
        draw.line([(0, px(x0, y)[1]), (10 if y % 50 else 20, px(x0, y)[1])], fill=(220, 220, 220))
        if y % 50 == 0: draw.text((22, px(x0, y)[1] - 6), str(y), fill=(255, 255, 255))
    legend = f'{title} | white game+LiDAR  magenta game only  cyan LiDAR only  yellow OSM building  orange OSM road | 10 m ticks, EPSG:25832'
    draw.rectangle((0, image.height - 18, image.width, image.height), fill=(0, 0, 0))
    draw.text((6, image.height - 15), legend, fill=(255, 255, 255))
    return image


def write_images(out, layers, buildings, roads, rows, samples):
    images = {}
    overlay(layers, buildings, roads, (666150, 5103540, 666490, 5103940), 4, 'Campus overview', rows).save(out / 'overview.jpg', quality=88)
    images['overview'] = 'overview.jpg'
    overlay(layers, [], roads, (666150, 5103540, 666490, 5103940), 4, 'Roads: dots = game asphalt centre offset (green <=1.5 m, amber <=3 m, red >3 m, grey none)',
            samples=samples).save(out / 'roads.jpg', quality=88)
    images['roads'] = 'roads.jpg'
    areas = dict(povo2=(666205, 5103795, 666320, 5103930), povo1=(666160, 5103680, 666320, 5103800),
                 fbk_nord=(666320, 5103770, 666430, 5103900), fbk_ovest_est=(666330, 5103670, 666490, 5103790),
                 fbk_south=(666320, 5103540, 666490, 5103680))
    for name, bounds in areas.items():
        overlay(layers, buildings, roads, bounds, 6, name, rows).save(out / f'{name}.jpg', quality=88)
        images[name] = f'{name}.jpg'
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--no-images', action='store_true')
    args = parser.parse_args()
    report, layers, buildings, roads, samples = audit()
    args.out.mkdir(parents=True, exist_ok=True)
    if not args.no_images:
        report['images'] = write_images(args.out, layers, buildings, roads, report['buildings'], samples)
    (args.out / 'proposed_footprints.json').write_text(json.dumps(report.pop('proposed_footprints'), indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    (args.out / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    for r in report['buildings']:
        print(f"{r['verdict']:5} {str(r['name'] or r['osm'])[:22]:22} IoU game/OSM {r['iou_game_osm']:.2f} worst side {r['worst_side_offset_m']:4.1f} m "
              f"shift->LiDAR {r['shift_game_to_lidar_m']} height L/G {r.get('lidar_height_m')}/{r.get('game_height_m')}")
    print(json.dumps(dict(buildings=len(report['buildings']), off=sum(r['verdict'] == 'off' for r in report['buildings']),
                          game_only_mass=len(report['game_only_mass']), roads=len(report['roads']))))


if __name__ == '__main__':
    main()
