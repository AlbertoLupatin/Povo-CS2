#!/usr/bin/env python3
"""Build the georeferenced site master from OSM + PAT LiDAR + 2024 orthophoto.

Outputs (all EPSG:25832 metres):
  data/derived/site_layers.json   OSM layers: buildings, roads, paths, steps,
                                  trees, barriers, entrances, lamps, benches
  data/derived/buildings.csv      per-building footprint + LiDAR heights
  data/derived/trees.csv          OSM trees with LiDAR canopy height/radius,
                                  plus canopy peaks OSM does not map
  out/site_master.png             ortho with OSM overlay, labelled
  out/site_heights.png            nDSM heights (buildings + vegetation)
"""

import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer
from scipy import ndimage
from shapely.geometry import Polygon, LineString, Point, mapping
from shapely.ops import unary_union
from shapely import prepared

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DERIVED = DATA / 'derived'
OUT = ROOT / 'out'
TO_UTM = Transformer.from_crs('EPSG:4326', 'EPSG:25832', always_xy=True)
# The render window: campus core with a margin for the context buildings.
VIEW = (666050, 5103450, 666550, 5104000)
CELL = 0.5


def utm(lon, lat):
    return TO_UTM.transform(lon, lat)


def load_osm():
    elements = json.loads((DATA / 'osm/povo.json').read_text(encoding='utf8'))['elements']
    layers = {k: [] for k in ('buildings', 'roads', 'paths', 'steps', 'trees', 'barriers',
                              'entrances', 'lamps', 'benches', 'landuse', 'parking', 'indoor')}
    for e in elements:
        t = e.get('tags', {})
        if not t:
            continue
        if e['type'] == 'node':
            p = utm(e['lon'], e['lat'])
            item = dict(id=e['id'], tags=t, xy=[round(p[0], 2), round(p[1], 2)])
            if t.get('natural') == 'tree':
                layers['trees'].append(item)
            elif 'entrance' in t or t.get('indoor') == 'door':
                layers['entrances'].append(item)
            elif t.get('highway') == 'street_lamp':
                layers['lamps'].append(item)
            elif t.get('amenity') in ('bench', 'waste_basket', 'bicycle_parking', 'drinking_water'):
                layers['benches'].append(item)
            continue
        if e['type'] == 'relation':
            # Multipolygon buildings: one part per outer ring, with the inner
            # rings (courtyards) it contains as holes.
            if t.get('type') == 'multipolygon' and 'building' in t:
                rings = {'outer': [], 'inner': []}
                for m in e.get('members', []):
                    if m.get('role') in rings and 'geometry' in m:
                        ring = [utm(g['lon'], g['lat']) for g in m['geometry']]
                        if len(ring) >= 4:
                            rings[m['role']].append(ring)
                for ring in rings['outer']:
                    outer = Polygon(ring)
                    holes = [h for h in rings['inner'] if outer.contains(Polygon(h).representative_point())]
                    layers['buildings'].append(dict(id=f"r{e['id']}", tags=t, ring=ring, holes=holes))
            continue
        geom = e.get('geometry')
        if not geom:
            continue
        pts = [utm(g['lon'], g['lat']) for g in geom]
        closed = len(pts) >= 4 and pts[0] == pts[-1]
        item = dict(id=e['id'], tags=t)
        if 'building' in t and closed:
            layers['buildings'].append(dict(item, ring=pts))
        elif t.get('indoor') in ('room', 'corridor', 'area') and closed:
            layers['indoor'].append(dict(item, ring=pts))
        elif t.get('highway') == 'steps':
            layers['steps'].append(dict(item, line=pts))
        elif t.get('highway') in ('footway', 'path', 'pedestrian', 'cycleway', 'track'):
            layers['paths'].append(dict(item, line=pts))
        elif 'highway' in t:
            layers['roads'].append(dict(item, line=pts))
        elif 'barrier' in t:
            layers['barriers'].append(dict(item, line=pts))
        elif t.get('amenity') == 'parking' and closed:
            layers['parking'].append(dict(item, ring=pts))
        elif ('landuse' in t or t.get('leisure') in ('park', 'garden', 'pitch')
              or t.get('natural') in ('wood', 'scrub', 'grassland')) and closed:
            layers['landuse'].append(dict(item, ring=pts))
    return layers


def load_lidar(kind):
    """Mosaic all tiles of one kind into a single array on a common grid."""
    files = sorted((DATA / 'lidar').glob(f'*_{kind}.asc'))
    if not files:
        return None
    heads = []
    for f in files:
        with open(f) as fh:
            h = {}
            for _ in range(6):
                k, v = fh.readline().split()
                h[k.lower()] = float(v)
        heads.append(h)
    e0 = min(h['xllcenter'] for h in heads) - CELL / 2
    n0 = min(h['yllcenter'] for h in heads) - CELL / 2
    e1 = max(h['xllcenter'] + h['ncols'] * CELL for h in heads) - CELL / 2
    n1 = max(h['yllcenter'] + h['nrows'] * CELL for h in heads) - CELL / 2
    grid = np.full((round((n1 - n0) / CELL), round((e1 - e0) / CELL)), np.nan, np.float32)
    for f, h in zip(files, heads):
        a = np.loadtxt(f, skiprows=6, dtype=np.float32)
        a[a == h['nodata_value']] = np.nan
        c = round((h['xllcenter'] - CELL / 2 - e0) / CELL)
        r = round((n1 - (h['yllcenter'] - CELL / 2 + h['nrows'] * CELL)) / CELL)
        grid[r:r + a.shape[0], c:c + a.shape[1]] = a
    return dict(grid=grid, e0=e0, n1=n1)


def sample_mask(lidar, ring):
    """Boolean mask of the LiDAR cells whose centres fall inside the polygon."""
    poly = Polygon(ring)
    minx, miny, maxx, maxy = poly.bounds
    c0 = max(int((minx - lidar['e0']) / CELL), 0)
    c1 = min(int((maxx - lidar['e0']) / CELL) + 1, lidar['grid'].shape[1])
    r0 = max(int((lidar['n1'] - maxy) / CELL), 0)
    r1 = min(int((lidar['n1'] - miny) / CELL) + 1, lidar['grid'].shape[0])
    if c1 <= c0 or r1 <= r0:
        return None
    prep = prepared.prep(poly)
    xs = lidar['e0'] + (np.arange(c0, c1) + .5) * CELL
    ys = lidar['n1'] - (np.arange(r0, r1) + .5) * CELL
    mask = np.array([[prep.contains(Point(x, y)) for x in xs] for y in ys])
    return (slice(r0, r1), slice(c0, c1)), mask


def building_table(layers, dtm, dbm):
    rows = []
    for b in layers['buildings']:
        poly = Polygon(b['ring'])
        if not poly.is_valid or poly.area < 20:
            continue
        cx, cy = poly.centroid.coords[0]
        if not (VIEW[0] - 150 < cx < VIEW[2] + 150 and VIEW[1] - 150 < cy < VIEW[3] + 150):
            continue
        rect = poly.minimum_rotated_rectangle
        xy = list(rect.exterior.coords)
        sides = sorted(math.dist(xy[i], xy[i + 1]) for i in range(2))
        angle = math.degrees(math.atan2(xy[1][1] - xy[0][1], xy[1][0] - xy[0][0])) % 180
        t = b['tags']
        row = dict(id=b['id'], name=t.get('name', ''), building=t.get('building', ''),
                   address=(t.get('addr:street', '') + ' ' + t.get('addr:housenumber', '')).strip(),
                   osm_levels=t.get('building:levels', ''), osm_height=t.get('height', ''),
                   centroid_e=round(cx, 1), centroid_n=round(cy, 1), area_m2=round(poly.area, 1),
                   rect_long_m=round(sides[1], 1), rect_short_m=round(sides[0], 1),
                   rect_angle_deg=round(angle, 1))
        if dtm is not None and dbm is not None:
            s = sample_mask(dtm, b['ring'])
            if s:
                sl, mask = s
                ground = dtm['grid'][sl][mask]
                roof = dbm['grid'][sl][mask]
                h = roof - ground
                ok = np.isfinite(h)
                if ok.sum() > 10:
                    # Ground under a building is interpolated; use the
                    # surrounding ring for the real terrain at its walls.
                    ring_poly = poly.buffer(3).difference(poly.buffer(.5))
                    rs = sample_mask(dtm, list(ring_poly.exterior.coords))
                    row.update(ground_min=round(float(np.nanmin(ground)), 2),
                               ground_max=round(float(np.nanmax(ground)), 2),
                               roof_p50_abs=round(float(np.nanpercentile(roof, 50)), 2),
                               roof_p95_abs=round(float(np.nanpercentile(roof, 95)), 2),
                               height_p50=round(float(np.nanpercentile(h[ok], 50)), 2),
                               height_p95=round(float(np.nanpercentile(h[ok], 95)), 2),
                               est_storeys=round(float(np.nanpercentile(h[ok], 50)) / 3.5, 1))
        rows.append(row)
    return rows


def tree_table(layers, dtm, dsmf, dbm):
    """OSM trees with LiDAR heights, plus unmapped canopy peaks."""
    if dtm is None or dsmf is None:
        return [dict(source='osm', id=t['id'], e=t['xy'][0], n=t['xy'][1],
                     species=t['tags'].get('species', t['tags'].get('genus', '')),
                     leaf_type=t['tags'].get('leaf_type', '')) for t in layers['trees']]
    veg = dsmf['grid'] - dtm['grid']
    if dbm is not None:
        veg = np.where(dbm['grid'] - dtm['grid'] > 1.0, 0, veg)  # drop building cells
    veg = np.nan_to_num(veg)
    # Building footprints from OSM: vegetation can't be on top of them.
    def rc(e, n):
        return int((dtm['n1'] - n) / CELL), int((e - dtm['e0']) / CELL)
    rows = []
    taken = np.zeros(veg.shape, bool)
    for t in layers['trees']:
        r, c = rc(*t['xy'])
        if not (0 <= r < veg.shape[0] and 0 <= c < veg.shape[1]):
            continue
        win = veg[max(r - 4, 0):r + 5, max(c - 4, 0):c + 5]
        h = float(win.max()) if win.size else 0
        crown = (win > h * .6).sum() * CELL * CELL if h > 1.5 else 0
        taken[max(r - 6, 0):r + 7, max(c - 6, 0):c + 7] = True
        rows.append(dict(source='osm', id=t['id'], e=t['xy'][0], n=t['xy'][1],
                         height_m=round(h, 1), crown_radius_m=round(math.sqrt(crown / math.pi), 1),
                         species=t['tags'].get('species', t['tags'].get('genus', '')),
                         leaf_type=t['tags'].get('leaf_type', '')))
    # Canopy peaks: local maxima > 3 m in a 5 m window, not near an OSM tree.
    peaks = (veg == ndimage.maximum_filter(veg, size=11)) & (veg > 3) & ~taken
    for r, c in zip(*np.nonzero(peaks)):
        e = dtm['e0'] + (c + .5) * CELL
        n = dtm['n1'] - (r + .5) * CELL
        if not (VIEW[0] - 100 < e < VIEW[2] + 100 and VIEW[1] - 100 < n < VIEW[3] + 100):
            continue
        h = float(veg[r, c])
        crown = (veg[max(r - 8, 0):r + 9, max(c - 8, 0):c + 9] > h * .6).sum() * CELL * CELL
        rows.append(dict(source='lidar_peak', id='', e=round(e, 1), n=round(n, 1),
                         height_m=round(h, 1), crown_radius_m=round(math.sqrt(crown / math.pi), 1),
                         species='', leaf_type=''))
    return rows, veg


def render_master(layers, rows, trees):
    img = Image.open(DATA / 'ortho/campus_15cm.jpg').convert('RGB')
    gw = [float(x) for x in (DATA / 'ortho/campus_15cm.jgw').read_text().split()]
    px, e0, n1 = gw[0], gw[4] - gw[0] / 2, gw[5] + gw[0] / 2
    scale = .5  # draw at ~0.3 m/px to keep the file reasonable
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    mpp = px / scale

    def P(e, n):
        return ((e - e0) / mpp, (n1 - n) / mpp)
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for r in layers['roads']:
        d.line([P(*p) for p in r['line']], fill=(255, 210, 0, 200), width=3)
    for r in layers['paths']:
        d.line([P(*p) for p in r['line']], fill=(255, 255, 255, 170), width=2)
    for r in layers['steps']:
        d.line([P(*p) for p in r['line']], fill=(255, 60, 60, 230), width=4)
    for r in layers['barriers']:
        col = {'wall': (180, 180, 255, 220), 'retaining_wall': (120, 120, 255, 230),
               'fence': (60, 220, 255, 220), 'hedge': (40, 200, 40, 220)}.get(r['tags'].get('barrier'), (200, 200, 200, 200))
        d.line([P(*p) for p in r['line']], fill=col, width=2)
    for b in layers['buildings']:
        d.polygon([P(*p) for p in b['ring']], outline=(255, 0, 255, 255))
    for b in layers['indoor']:
        d.polygon([P(*p) for p in b['ring']], outline=(255, 140, 0, 200))
    for t in trees:
        x, y = P(t['e'], t['n'])
        rad = max(t.get('crown_radius_m') or 2, 1) / mpp
        col = (0, 255, 0, 230) if t['source'] == 'osm' else (0, 255, 200, 160)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), outline=col, width=2)
    for e in layers['entrances']:
        x, y = P(*e['xy'])
        d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(255, 0, 0, 255))
    for l in layers['lamps']:
        x, y = P(*l['xy'])
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 255, 120, 255))
    img = Image.alpha_composite(img.convert('RGBA'), over)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 15)
    except OSError:
        font = ImageFont.load_default()
    for r in rows:
        x, y = P(r['centroid_e'], r['centroid_n'])
        if not (0 < x < img.width and 0 < y < img.height) or r['area_m2'] < 300:
            continue
        label = f"{r['id']}\n{r['name'][:28]}\n{r['rect_long_m']}x{r['rect_short_m']} m"
        if 'height_p50' in r:
            label += f"\nh {r['height_p50']} (p95 {r['height_p95']})"
        d.multiline_text((x - 50, y - 30), label, fill='white', font=font, stroke_width=2, stroke_fill='black')
    # 50 m grid with UTM labels
    for e in range(int(e0 // 50 * 50), int(e0 + img.width * mpp), 50):
        x, _ = P(e, n1)
        d.line([(x, 0), (x, 12)], fill='white', width=2)
        d.text((x + 2, 12), str(e), fill='white', font=font, stroke_width=2, stroke_fill='black')
    for n in range(int((n1 - img.height * mpp) // 50 * 50 + 50), int(n1), 50):
        _, y = P(e0, n)
        d.line([(0, y), (12, y)], fill='white', width=2)
        d.text((14, y - 8), str(n), fill='white', font=font, stroke_width=2, stroke_fill='black')
    img.convert('RGB').save(OUT / 'site_master.png')


def render_heights(dtm, dbm, veg):
    e0, n0, e1, n1 = VIEW
    c0, c1 = int((e0 - dtm['e0']) / CELL), int((e1 - dtm['e0']) / CELL)
    r0, r1 = int((dtm['n1'] - n1) / CELL), int((dtm['n1'] - n0) / CELL)
    bh = np.nan_to_num(dbm['grid'] - dtm['grid'])[r0:r1, c0:c1]
    vh = veg[r0:r1, c0:c1]
    rgb = np.zeros(bh.shape + (3,), np.uint8)
    b = np.clip(bh / 22, 0, 1)
    rgb[..., 0] = rgb[..., 1] = rgb[..., 2] = (b * 255).astype(np.uint8)
    v = (vh > 1.5) & (bh < 1)
    rgb[v, 1] = np.clip(80 + vh[v] * 8, 0, 255).astype(np.uint8)
    rgb[v, 0] = rgb[v, 2] = 0
    img = Image.fromarray(rgb).resize((bh.shape[1] * 2, bh.shape[0] * 2), Image.NEAREST)
    img.save(OUT / 'site_heights.png')


def main():
    DERIVED.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    layers = load_osm()
    dtm, dbm, dsmf = (load_lidar(k) for k in ('DTM', 'DBM', 'DSMF'))
    rows = building_table(layers, dtm, dbm)
    trees_result = tree_table(layers, dtm, dsmf, dbm)
    trees, veg = trees_result if isinstance(trees_result, tuple) else (trees_result, None)
    trees = [t for t in trees if VIEW[0] - 100 < t['e'] < VIEW[2] + 100 and VIEW[1] - 100 < t['n'] < VIEW[3] + 100]
    (DERIVED / 'site_layers.json').write_text(json.dumps(layers))
    for name, table in (('buildings.csv', rows), ('trees.csv', trees)):
        keys = sorted({k for r in table for k in r}, key=lambda k: list(table[0]).index(k) if k in table[0] else 99)
        with open(DERIVED / name, 'w', newline='', encoding='utf8') as f:
            w = csv.DictWriter(f, keys)
            w.writeheader()
            w.writerows(table)
    render_master(layers, rows, trees)
    if dtm is not None and dbm is not None and veg is not None:
        render_heights(dtm, dbm, veg)
    print(len(rows), 'buildings,', len(trees), 'trees,', {k: len(v) for k, v in layers.items()})


if __name__ == '__main__':
    main()
