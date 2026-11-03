#!/usr/bin/env python3
"""Collect the spots marked in game with F6 (addon cfg povo_marks.cfg).

Each F6 press logs "POVO_MARK", the player position (getpos) and takes a screenshot.
This reads game/csgo/console.log (CS2 started with -condebug, as cs2_launch.py does),
pairs each mark with its screenshot and writes them to
data/labeled_pictures/PROBLEMS_TO_SOLVE/marks/mark_NNN.png plus marks.json.

  marks.py            collect new marks
  marks.py --views    also write build/maps/marks_views.json to re-shoot every mark

CS2 rewrites console.log at each start, so cs2_launch.py collects marks before relaunching.
"""

import argparse
import json
import re
import time
from datetime import datetime

from PIL import Image

from cs2_shots import SHOTS
from vmap_build import CS2, ROOT

LOG = CS2 / 'game/csgo/console.log'
OUT = ROOT / 'data/labeled_pictures/PROBLEMS_TO_SOLVE/marks'
INDEX = OUT / 'marks.json'
STAMP = re.compile(r'^(\d\d/\d\d \d\d:\d\d:\d\d) (.*)$')
SETPOS = re.compile(r'setpos ([-\d.]+) ([-\d.]+) ([-\d.]+);\s*setang ([-\d.]+) ([-\d.]+) ([-\d.]+)')
MAP = re.compile(r'maps/(povo_site(?:_lit)?)\b')
SHOT = re.compile(r'Screenshot written to: screenshots[\\/](\S+\.tga)')


def parse_log():
    """[(time, map, pos, ang, screenshot)] for every getpos immediately followed by a screenshot.
    (The F6 alias runs "getpos; screenshot"; automated shots have no getpos before them, and
    their files are deleted at once, so they are skipped.)"""
    if not LOG.exists():
        return []
    year = time.localtime().tm_year
    marks, last, current_map = [], None, ''
    for line in LOG.read_text(encoding='utf8', errors='replace').splitlines():
        m = STAMP.match(line)
        if not m:
            continue
        when, text = m.groups()
        when = datetime.strptime(f'{year}/{when}', '%Y/%m/%d %H:%M:%S')
        found = MAP.search(text)
        if found:
            current_map = found.group(1)
        pos = SETPOS.search(text)
        shot = SHOT.search(text)
        if shot and last and (when - last[0]).total_seconds() <= 2:
            path = SHOTS / shot.group(1)
            if path.exists():
                marks.append((last[0], current_map, last[1][:3], last[1][3:], path))
        last = (when, [float(x) for x in pos.groups()]) if pos else None
    return marks


def collect():
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text(encoding='utf8')) if INDEX.exists() else []
    added = []
    for when, map_name, pos, ang, shot in parse_log():
        n = len(index) + 1
        name = f'mark_{n:03d}.png'
        Image.open(shot).convert('RGB').save(OUT / name)
        shot.unlink()                                 # collected once: the file is the marker
        entry = dict(id=n, time=when.strftime('%Y-%m-%d %H:%M:%S'), map=map_name, pos=pos, ang=ang,
                     file=name, note='')
        index.append(entry)
        added.append(entry)
    INDEX.write_text(json.dumps(index, indent=1), encoding='utf8')
    return index, added


def views(index):
    """Views to re-shoot every mark with cs2_shots.py (eye height is added by setpos)."""
    out = [dict(name=f'mark_{m["id"]:03d}', pos=[m['pos'][0], m['pos'][1], m['pos'][2] - 64], ang=m['ang'])
           for m in index]
    path = ROOT / 'build/maps/marks_views.json'
    path.write_text(json.dumps(out, indent=1), encoding='utf8')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--views', action='store_true')
    args = parser.parse_args()
    index, added = collect()
    for m in added:
        print(f'mark {m["id"]:3d}  {m["time"]}  {m["map"]}  {m["file"]}')
    print(f'{len(added)} new, {len(index)} in total -> {OUT}')
    if args.views:
        print('views', views(index))
