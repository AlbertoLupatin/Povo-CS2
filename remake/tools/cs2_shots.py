#!/usr/bin/env python3
"""Take named in-engine screenshots from a running CS2 (-netconport 27400).

Usage: cs2_shots.py views.json   with [{"name", "pos": [x,y,z], "ang": [p,y,r]}]
Positions are player origins in Hammer units (eye is 64 u higher).
Screenshots land in out/shots/<name>.png.
"""

import ctypes
import json
from pathlib import Path
import re
import socket
import sys
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = Path(r'D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\povo_remake\screenshots')


def console(commands, seconds=1.0, port=27400):
    chunks = []
    with socket.create_connection(('127.0.0.1', port), timeout=5) as conn:
        conn.settimeout(.2)
        for c in commands:
            conn.sendall((c + '\n').encode())
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                data = conn.recv(65536)
            except socket.timeout:
                continue
            if not data:
                break
            chunks.append(data)
    return b''.join(chunks).decode('utf-8', 'replace')


def grab():
    """Take a screenshot and return it as an image (the .tga is removed)."""
    before = set(SHOTS.glob('*.tga')) if SHOTS.exists() else set()
    console(['screenshot'], 1.0)
    for _ in range(20):
        new = set(SHOTS.glob('*.tga')) - before
        if new:
            break
        time.sleep(.3)
    else:
        raise RuntimeError('no screenshot written')
    src = max(new, key=lambda p: p.stat().st_mtime)
    time.sleep(.3)
    im = Image.open(src).convert('RGB')
    src.unlink()
    return im


def wait_in_game(timeout=600):
    """Join T, wait for the spawn, then until the world (not the loading screen) renders:
    two probes looking in opposite directions must differ."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        out = console(['sv_cheats 1', 'jointeam 2', 'getpos'], 1.5)
        m = re.findall(r'setpos ([-\d.]+) ([-\d.]+) ([-\d.]+)', out)
        if m and any(abs(float(v)) > 1 for v in m[-1][:2]):
            break
        time.sleep(3)
    else:
        raise TimeoutError('player never spawned')
    while time.monotonic() < end:
        probes = []
        for yaw in (0, 180):
            console([f'setang 0 {yaw} 0'], .3)
            time.sleep(1)
            probes.append(np.asarray(grab().resize((160, 90)), np.float32))
        if np.abs(probes[0] - probes[1]).mean() > 4:
            return
        time.sleep(10)
    raise TimeoutError('loading screen never cleared')


def keep_display_on():
    """CS2 stops drawing the world while the display is off (idle timeout); for as long
    as this process runs, force the display on."""
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED, ES_DISPLAY_REQUIRED = 0x80000000, 0x1, 0x2
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)


def shoot(views):
    keep_display_on()
    out_dir = ROOT / 'out/shots'
    out_dir.mkdir(parents=True, exist_ok=True)
    wait_in_game()
    console(['god', 'noclip 1', 'cl_drawhud 0', 'r_drawviewmodel 0', 'cl_firstperson_legs 0',
             'mp_warmup_pausetimer 1'], .5)
    for v in views:
        console([f'setpos {v["pos"][0]} {v["pos"][1]} {v["pos"][2]}',
                 f'setang {v["ang"][0]} {v["ang"][1]} {v["ang"][2]}'], .3)
        time.sleep(1.5)
        grab().save(out_dir / f'{v["name"]}.png')
        print('shot', v['name'])


if __name__ == '__main__':
    shoot(json.loads(Path(sys.argv[1]).read_text()))
