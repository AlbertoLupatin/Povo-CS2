#!/usr/bin/env python3
"""Rectify a photographed floor plan onto a building's real outline.

Four photo pixels (the drawn outline's corners) are matched to the OSM
building corners, and the photo is warped to a north-up metric image
(EPSG:25832, PX metres per pixel) with an OSM overlay for checking.

Usage: rectify_plan.py <photo> <building osm id> <out name> <corners json>
corners json: {"SW": [x, y], "NW": [...], "NE": [...], "SE": [...]} in photo pixels,
matched to the building's rectangle corners; or, for plans spanning several buildings,
{"pix": {key: [x, y]}, "world": {key: [e, n]}} with any four matching control points.
"""

import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
PX = 0.04
MARGIN = 2.0


def homography(src, dst):
    """3x3 H with dst ~ H @ src, from four point pairs."""
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(rows, float))
    return (vt[-1] / vt[-1][-1]).reshape(3, 3)


def building(osm_id):
    layers = json.loads((ROOT / 'data/derived/site_layers.json').read_text(encoding='utf8'))
    b = next(b for b in layers['buildings'] if str(b['id']) == osm_id)
    return Polygon(b['ring'], b.get('holes', [])), layers


def corners(poly):
    """SW, NW, NE, SE corners of the building's minimum rotated rectangle."""
    pts = list(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    cx, cy = np.mean(pts, axis=0)
    pick = lambda sx, sy: max(pts, key=lambda p: sx * (p[0] - cx) + sy * (p[1] - cy))
    return dict(SW=pick(-1, -1), NW=pick(-1, 1), NE=pick(1, 1), SE=pick(1, -1))


def main(photo, osm_id, name, corner_file):
    poly, layers = building(osm_id)
    spec = json.loads(Path(corner_file).read_text())
    if 'world' in spec:
        pix, real = spec['pix'], spec['world']
        keys = tuple(pix)
        pts = list(real.values())
        minx, miny = min(p[0] for p in pts), min(p[1] for p in pts)
        maxx, maxy = max(p[0] for p in pts), max(p[1] for p in pts)
        minx, miny = min(minx, poly.bounds[0]), min(miny, poly.bounds[1])
        maxx, maxy = max(maxx, poly.bounds[2]), max(maxy, poly.bounds[3])
    else:
        pix, real, keys = spec, corners(poly), ('SW', 'NW', 'NE', 'SE')
        minx, miny, maxx, maxy = poly.bounds
    e0, n1 = minx - MARGIN, maxy + MARGIN
    w, h = round((maxx - minx + 2 * MARGIN) / PX), round((maxy - miny + 2 * MARGIN) / PX)
    to_out = lambda e, n: ((e - e0) / PX, (n1 - n) / PX)
    H = homography([to_out(*real[k]) for k in keys], [pix[k] for k in keys])  # output -> photo
    im = ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
    out = im.transform((w, h), Image.PERSPECTIVE, tuple(H.flatten()[:8]), Image.BICUBIC)
    over = out.copy()
    d = ImageDraw.Draw(over)
    frame = Polygon([(e0, n1), (e0 + w * PX, n1), (e0 + w * PX, n1 - h * PX), (e0, n1 - h * PX)])
    for b in layers['buildings']:
        other = Polygon(b['ring'])
        if other.intersects(frame):
            d.line([to_out(*p) for p in other.exterior.coords], fill=(255, 0, 255), width=3)
    for r in layers['indoor']:
        rp = Polygon(r['ring'])
        if poly.buffer(1).contains(rp.centroid):
            d.line([to_out(*p) for p in rp.exterior.coords], fill=(0, 160, 255), width=2)
    for e in range(int(minx // 5 * 5), int(maxx) + 5, 5):
        d.line([to_out(e, maxy + MARGIN), to_out(e, miny - MARGIN)], fill=(255, 200, 0), width=1)
    for n in range(int(miny // 5 * 5), int(maxy) + 5, 5):
        d.line([to_out(minx - MARGIN, n), to_out(maxx + MARGIN, n)], fill=(255, 200, 0), width=1)
    target = ROOT / 'data/plans'
    target.mkdir(parents=True, exist_ok=True)
    out.save(target / f'{name}.png')
    (target / f'{name}.pgw').write_text(f'{PX}\n0\n0\n{-PX}\n{e0 + PX / 2}\n{n1 - PX / 2}\n')
    over.save(ROOT / 'out' / f'{name}_overlay.jpg', quality=88)
    print(name, w, 'x', h, 'px at', PX, 'm/px')


if __name__ == '__main__':
    main(*sys.argv[1:5])
