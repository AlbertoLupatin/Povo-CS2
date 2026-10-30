#!/usr/bin/env python3
"""Cache OpenStreetMap buildings and roads around the campus from Overture Maps.

Overture's buildings and transportation themes republish OpenStreetMap
geometry with each feature's OSM way/relation id, and the public S3 bucket is
readable with plain HTTPS range requests. Only row groups whose bbox statistics
touch the PAT tile are downloaded. Output is GeoJSON in EPSG:25832 so the
registration audit needs no projection library.

Needs pyarrow (refresh only; the audit reads the cached file).
"""
import argparse
import datetime
import io
import json
import math
import re
import struct
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://overturemaps-us-west-2.s3.amazonaws.com'
RELEASE = '2026-10-21.0'
# PAT LiDAR tile 5h666051035 (EPSG:25832 666000-666500 E, 5103500-5104000 N) plus a margin.
BBOX_WGS84 = (11.1440, 46.0638, 11.1552, 46.0713)
TILE = (666000, 5103500, 666500, 5104000)
OUT = ROOT / 'data/reference/osm/povo_osm_overture.geojson'
ROAD_SUBTYPE = 'road'


def utm(lon, lat, zone=32):
    """WGS84 -> UTM (Krueger series, sub-millimetre at this latitude)."""
    a = 6378137.0; f = 1 / 298.257223563; n = f / (2 - f)
    A = a / (1 + n) * (1 + n * n / 4 + n ** 4 / 64)
    alpha = (n / 2 - 2 * n * n / 3 + 5 * n ** 3 / 16, 13 * n * n / 48 - 3 * n ** 3 / 5, 61 * n ** 3 / 240)
    e = math.sqrt(f * (2 - f)); phi = math.radians(lat); lam = math.radians(lon - (zone * 6 - 183))
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi = math.atan2(t, math.cos(lam)); eta = math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    E = 500000 + 0.9996 * A * (eta + sum(al * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j, al in enumerate(alpha, 1)))
    N = 0.9996 * A * (xi + sum(al * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j, al in enumerate(alpha, 1)))
    return E, N


def parse_wkb(data):
    """Return a GeoJSON geometry for 2D (Multi)Point/LineString/Polygon WKB."""
    def read(offset):
        order = '<' if data[offset] == 1 else '>'
        kind, = struct.unpack_from(order + 'I', data, offset + 1); offset += 5
        kind %= 1000
        def points(off):
            count, = struct.unpack_from(order + 'I', data, off); off += 4
            values = struct.unpack_from(order + 'd' * 2 * count, data, off)
            return [list(values[i:i + 2]) for i in range(0, len(values), 2)], off + 16 * count
        if kind == 1:
            x, y = struct.unpack_from(order + 'dd', data, offset); return {'type': 'Point', 'coordinates': [x, y]}, offset + 16
        if kind == 2:
            coords, offset = points(offset); return {'type': 'LineString', 'coordinates': coords}, offset
        if kind == 3:
            rings, = struct.unpack_from(order + 'I', data, offset); offset += 4; coords = []
            for _ in range(rings):
                ring, offset = points(offset); coords.append(ring)
            return {'type': 'Polygon', 'coordinates': coords}, offset
        if kind in (4, 5, 6):
            parts, = struct.unpack_from(order + 'I', data, offset); offset += 4; coords = []
            for _ in range(parts):
                part, offset = read(offset); coords.append(part['coordinates'])
            return {'type': ('MultiPoint', 'MultiLineString', 'MultiPolygon')[kind - 4], 'coordinates': coords}, offset
        raise ValueError(f'unsupported WKB geometry type {kind}')
    return read(0)[0]


def project(geometry):
    def walk(value):
        if value and isinstance(value[0], (int, float)):
            return [round(v, 2) for v in utm(*value[:2])]
        return [walk(v) for v in value]
    return {'type': geometry['type'], 'coordinates': walk(geometry['coordinates'])}


class HttpRange(io.RawIOBase):
    """Seekable read-only view of a remote object using HTTP range requests."""
    def __init__(self, url, size):
        self.url, self.size, self.pos = url, size, 0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        if n == 0 or self.pos >= self.size: return b''
        end = min(self.size, self.pos + n) - 1
        for attempt in range(5):
            try:
                request = urllib.request.Request(self.url, headers={'Range': f'bytes={self.pos}-{end}'})
                with urllib.request.urlopen(request, timeout=120) as response:
                    body = response.read()
                break
            except OSError:
                if attempt == 4: raise
        self.pos += len(body)
        return body
    def readinto(self, buffer):
        body = self.read(len(buffer)); buffer[:len(body)] = body; return len(body)


def list_objects(theme, kind):
    with urllib.request.urlopen(f'{BASE}/?list-type=2&prefix=release/{RELEASE}/theme={theme}/type={kind}/', timeout=60) as response:
        listing = response.read().decode()
    if '<IsTruncated>true' in listing:
        raise RuntimeError('Overture listing was truncated; add pagination')
    return list(zip(re.findall(r'<Key>([^<]+)</Key>', listing), map(int, re.findall(r'<Size>(\d+)</Size>', listing))))


def scan(item, columns):
    import pyarrow.parquet as pq
    key, size = item
    west, south, east, north = BBOX_WGS84
    parquet = pq.ParquetFile(HttpRange(f'{BASE}/{key}', size))
    meta = parquet.metadata
    index = {meta.schema.column(i).path: i for i in range(meta.num_columns)}
    rows = []
    for group in range(meta.num_row_groups):
        stats = {k: meta.row_group(group).column(index[f'bbox.{k}']).statistics for k in ('xmin', 'xmax', 'ymin', 'ymax')}
        if not (stats['xmin'].min < east and stats['xmax'].max > west and stats['ymin'].min < north and stats['ymax'].max > south):
            continue
        wanted = [c for c in columns if c in parquet.schema_arrow.names] + ['bbox', 'geometry']
        for row in parquet.read_row_group(group, columns=wanted).to_pylist():
            box = row['bbox']
            if box['xmin'] < east and box['xmax'] > west and box['ymin'] < north and box['ymax'] > south:
                rows.append(row)
    return rows


def fetch(theme, kind, columns):
    with ThreadPoolExecutor(16) as pool:
        return [row for part in pool.map(lambda item: scan(item, columns), list_objects(theme, kind)) for row in part]


def osm_source(row):
    for source in row.get('sources') or []:
        if source.get('dataset') == 'OpenStreetMap' and source.get('record_id'):
            return source['record_id']
    return None


def feature(row, kind):
    record = osm_source(row)
    if not record:
        return None
    osm, _, version = record.partition('@')
    names = row.get('names') or {}
    properties = dict(kind=kind, osm=osm, osm_version=int(version) if version.isdigit() else None,
                      overture_id=row['id'], name=names.get('primary'), **{
                          k: row.get(k) for k in ('class', 'subtype', 'subclass', 'height', 'num_floors') if row.get(k) is not None})
    return {'type': 'Feature', 'properties': properties, 'geometry': project(parse_wkb(row['geometry']))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    buildings = fetch('buildings', 'building', ['id', 'names', 'class', 'subtype', 'height', 'num_floors', 'sources'])
    roads = [r for r in fetch('transportation', 'segment', ['id', 'names', 'class', 'subclass', 'subtype', 'sources'])
             if r.get('subtype') == ROAD_SUBTYPE]
    features = [f for f in (feature(r, 'building') for r in buildings) if f]
    features += [f for f in (feature(r, 'road') for r in roads) if f]
    features.sort(key=lambda f: (f['properties']['kind'], f['properties']['osm'], f['properties']['overture_id']))
    collection = {
        'type': 'FeatureCollection',
        'crs_note': 'EPSG:25832 metres; projected from WGS84 with no datum shift (as EPSG:4326->25832)',
        'source': f'Overture Maps Foundation release {RELEASE}, OpenStreetMap-sourced features only',
        'licence': 'Open Database License 1.0; (c) OpenStreetMap contributors, https://www.openstreetmap.org/copyright',
        'query_bbox_wgs84': list(BBOX_WGS84), 'tile_epsg25832': list(TILE),
        'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'features': features,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(collection, separators=(',', ':')) + '\n', encoding='utf-8')
    counts = {k: sum(f['properties']['kind'] == k for f in features) for k in ('building', 'road')}
    print(json.dumps(dict(out=str(args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out), **counts)))


if __name__ == '__main__':
    main()
