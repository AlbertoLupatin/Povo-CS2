#!/usr/bin/env python3
"""One test cycle: build the site, load it in CS2, take the screenshots, report.

  test_build.py [--bake] [views.json ...]

- Unlit by default (compiles in seconds); --bake bakes lightmaps, which needs the GPU,
  so CS2 is closed first.
- Stops at the first failure and says why; never launches a map that failed to build.
- Reuses a running CS2 (console port 27400) for unlit builds: it only disconnects so
  the map package can be overwritten, then loads the new one.
- Writes build/maps/last_run.json with every step's outcome; exits 1 on any failure.
"""

import argparse
import json
import subprocess
import sys
import time

from cs2_launch import launch, quit_game, running
from cs2_shots import console, shoot
from vmap_build import ROOT

MAP, LIT = 'povo_site', 'povo_site_lit'     # unlit layout map, baked map
STATUS = ROOT / 'build/maps/last_run.json'


def report(steps, ok):
    STATUS.write_text(json.dumps(dict(ok=ok, time=time.strftime('%Y-%m-%d %H:%M:%S'), steps=steps), indent=1))
    for name, outcome in steps:
        print(f'{name:10s} {outcome}')
    print('RESULT', 'ok' if ok else 'FAILED')
    return 0 if ok else 1


def load_running(name, tries=45):
    """Load the map in an already running CS2; True once the server reports it."""
    console([f'map maps/{name}.vpk'], 2)
    for _ in range(tries):
        time.sleep(4)
        try:
            out = console(['status'], 1.5)
        except OSError:
            continue
        if 'spawngroup' in out and '<empty>' not in out and name in out:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bake', action='store_true')
    parser.add_argument('--quality', type=int, default=0, help='bake quality: 0 fast (16 samples), 1 normal')
    parser.add_argument('views', nargs='*')
    args = parser.parse_args()
    steps = []
    reuse = running() and not args.bake
    if args.bake:
        quit_game()
    elif reuse:
        try:
            console(['disconnect'], 1)
        except OSError:
            reuse = False
    name = LIT if args.bake else MAP
    build = subprocess.run([sys.executable, str(ROOT / 'tools/build_site.py'), '--quality', str(args.quality)]
                           + (['--bake'] if args.bake else []), capture_output=True, text=True)
    last = [l for l in build.stdout.splitlines() if l.startswith('compile')]
    steps.append(('build', last[-1] if last else build.stderr.strip().splitlines()[-1:]))
    if build.returncode:
        return report(steps, False)
    try:
        if reuse and load_running(name):
            steps.append(('load', 'loaded in the running CS2'))
        else:
            launch(name)
            steps.append(('load', 'launched CS2 and loaded'))
    except Exception as err:                       # noqa: BLE001 - report any launch failure
        steps.append(('load', f'FAILED: {err}'))
        return report(steps, False)
    for views in args.views:
        try:
            shoot(json.loads(open(views).read()))
            steps.append(('shots', f'{views}: ok'))
        except Exception as err:                   # noqa: BLE001
            steps.append(('shots', f'{views}: FAILED: {err}'))
            return report(steps, False)
    return report(steps, True)


if __name__ == '__main__':
    raise SystemExit(main())
