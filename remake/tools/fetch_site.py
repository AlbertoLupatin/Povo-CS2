#!/usr/bin/env python3
"""Download the open site data for the Povo remake into data/.

- PAT LiDAR 2014/2018 tiles (CC BY 4.0): DTM (ground), DBM (buildings),
  DSMF (first return: buildings + trees), 0.5 m, EPSG:25832.
- Comune di Trento 2024 orthophoto (CC0), resampled WMS crops.
- OpenStreetMap features via Overpass (ODbL).

Every file gets a provenance entry in data/provenance.json.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

import requests
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
WFS = 'https://siat.provincia.tn.it/geoserver/wfs'
STEM = 'https://siatservices.provincia.tn.it/stemdata'
WMS = 'https://gis.comune.trento.it/ogc'
OVERPASS = 'https://overpass-api.de/api/interpreter'
# WFS layer kind -> (download folder, remote suffix, local suffix)
LIDAR = {'dtm': ('2014_lidar_dtm_asc', 'DTM', 'DTM'),
         'dbm': ('2014_lidar_dbm_asc', 'DBM', 'DBM'),
         'dsmf': ('2014_lidar_dsmfirst_asc', 'DSMFirst', 'DSMF')}
# 1.5 x 1.5 km of 500 m tiles centred on Povo 1 / Povo 2.
LIDAR_BBOX = (665500, 5103000, 667000, 5104500)
# Orthophoto crops: the campus core at full detail, then wider context.
ORTHO = {'campus_15cm': ((666100, 5103600, 666500, 5104000), 0.15),
         'site_50cm': ((665500, 5103000, 667000, 5104500), 0.5)}
OSM_BBOX = (665300, 5102800, 667200, 5104700)
HEADERS = {'User-Agent': 'povo-cs2-remake/0.1 (personal fan map; contact via github.com/AlbertoLupatin)'}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record(prov, path, **info):
    data = path.read_bytes()
    prov[str(path.relative_to(DATA)).replace('\\', '/')] = dict(
        info, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), retrieved_at_utc=now())


def get(url, **kw):
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=180, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def lidar_tiles(kind):
    e0, n0, e1, n1 = LIDAR_BBOX
    r = get(WFS, params=dict(service='WFS', version='1.0.0', request='GetFeature',
                             typeName=f'stem:inqlid2014_{kind}_asc',
                             bbox=f'{e0+1},{n0+1},{e1-1},{n1-1}', outputFormat='application/json'))
    return sorted(f['properties']['n_tavola'] for f in r.json()['features'])


def fetch_lidar(prov):
    out = DATA / 'lidar'
    out.mkdir(parents=True, exist_ok=True)
    for kind, (folder, remote, local) in LIDAR.items():
        for tile in lidar_tiles(kind):
            path = out / f'{tile}_{local}.asc'
            if path.exists():
                continue
            url = f'{STEM}/{folder}/{tile}_{remote}.asc'
            path.write_bytes(get(url).content)
            record(prov, path, source_url=url, provider='Provincia Autonoma di Trento',
                   licence='CC BY 4.0', crs='EPSG:25832 (ETRF2000), heights ITALGEO 2005')
            print('lidar', path.name)


def fetch_ortho(prov):
    out = DATA / 'ortho'
    out.mkdir(parents=True, exist_ok=True)
    for name, ((e0, n0, e1, n1), px) in ORTHO.items():
        path = out / f'{name}.jpg'
        if path.exists():
            continue
        w, h = round((e1 - e0) / px), round((n1 - n0) / px)
        params = dict(SERVICE='WMS', VERSION='1.3.0', REQUEST='GetMap', LAYERS='ortofoto_2024',
                      STYLES='', CRS='EPSG:25832', BBOX=f'{e0},{n0},{e1},{n1}',
                      WIDTH=w, HEIGHT=h, FORMAT='image/jpeg')
        r = get(WMS, params=params)
        if not r.headers.get('content-type', '').startswith('image/'):
            raise RuntimeError(f'WMS error for {name}: {r.text[:300]}')
        path.write_bytes(r.content)
        path.with_suffix('.jgw').write_text(f'{px}\n0\n0\n{-px}\n{e0+px/2}\n{n1-px/2}\n')
        record(prov, path, source_url=r.url, provider='Comune di Trento', layer='ortofoto_2024',
               licence='CC0 1.0', crs='EPSG:25832', bbox=[e0, n0, e1, n1], pixel_metres=px,
               survey_dates=['2024-08-28', '2024-08-29'])
        print('ortho', path.name, w, h)


def fetch_osm(prov):
    out = DATA / 'osm'
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'povo.json'
    if path.exists():
        return
    to_ll = Transformer.from_crs('EPSG:25832', 'EPSG:4326', always_xy=True)
    e0, n0, e1, n1 = OSM_BBOX
    lon0, lat0 = to_ll.transform(e0, n0)
    lon1, lat1 = to_ll.transform(e1, n1)
    bbox = f'{lat0},{lon0},{lat1},{lon1}'
    query = f'[out:json][timeout:120];(nwr({bbox}););out body geom;'
    r = requests.post(OVERPASS, data={'data': query}, headers=HEADERS, timeout=240)
    r.raise_for_status()
    path.write_bytes(r.content)
    record(prov, path, source_url=OVERPASS, query=query, provider='OpenStreetMap contributors',
           licence='ODbL 1.0', attribution='© OpenStreetMap contributors')
    print('osm', len(r.json()['elements']), 'elements')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=('lidar', 'ortho', 'osm'))
    args = parser.parse_args()
    prov_path = DATA / 'provenance.json'
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    try:
        for name, fn in (('osm', fetch_osm), ('ortho', fetch_ortho), ('lidar', fetch_lidar)):
            if args.only in (None, name):
                fn(prov)
    finally:
        DATA.mkdir(exist_ok=True)
        prov_path.write_text(json.dumps(prov, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
