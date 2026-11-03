#!/usr/bin/env python3
"""Start CS2 with the povo_remake addon and load a map; wait until it is up.

Usage: cs2_launch.py <map>      (closes a running CS2 first)
       cs2_launch.py --quit
"""

import argparse
import shutil
import subprocess
import time
from pathlib import Path

from cs2_shots import console
from vmap_build import CS2, ADDON


def running():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq cs2.exe'], capture_output=True, text=True).stdout
    return 'cs2.exe' in out


def quit_game():
    if running():
        try:
            console(['quit'], .5)
        except OSError:
            pass
        for _ in range(60):
            if not running():
                return
            time.sleep(1)
        subprocess.run(['taskkill', '/IM', 'cs2.exe', '/F'], capture_output=True)


def launch(map_name):
    quit_game()
    # The F6 marker config lives in the project (cs2/cfg); install it into the addon.
    cfg = CS2 / 'game/csgo_addons' / ADDON / 'cfg'
    cfg.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve().parents[1] / 'cs2/cfg/povo_marks.cfg', cfg / 'povo_marks.cfg')
    # CS2 rewrites console.log at start: keep the F6 marks of the last session first.
    from marks import collect
    _index, added = collect()
    if added:
        print(f'collected {len(added)} marks')
    exe = CS2 / 'game/bin/win64/cs2.exe'
    subprocess.Popen([str(exe), '-steam', '-retail', '-addon', ADDON, '-tools', '-insecure', '-condebug',
                      '-novid', '-netconport', '27400', '-windowed', '-w', '1600', '-h', '900',
                      '+game_type', '0', '+game_mode', '0', '+sv_cheats', '1', '+bot_quota', '0',
                      '+exec', 'povo_marks'],
                     cwd=str(exe.parent))
    # The console port opens before the game can load an addon map.
    for _ in range(120):
        try:
            if 'Status' in console(['status'], 1):
                break
        except OSError:
            pass
        time.sleep(3)
    # An early map command can be dropped while the menu starts: resend.
    for _attempt in range(4):
        time.sleep(10)
        try:
            console([f'map maps/{map_name}.vpk'], 2)
        except OSError:   # the port can drop briefly while the menu restarts
            continue
        for _ in range(20):
            time.sleep(4)
            try:
                out = console(['status'], 1.5)
            except OSError:
                continue
            if 'spawngroup' in out and '<empty>' not in out:
                print('loaded', map_name)
                return
    raise TimeoutError('map did not load')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('map', nargs='?')
    parser.add_argument('--quit', action='store_true')
    args = parser.parse_args()
    quit_game() if args.quit else launch(args.map)
