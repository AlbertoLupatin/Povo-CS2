#!/usr/bin/env python3
"""Checked Windows campus build entry point. See docs/BUILD_HANDOFF.md."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import cs2_project

ROOT = Path(__file__).resolve().parents[1]
PACKER = ROOT / 'build/tools/vpkedit-4.4.2/vpkeditcli.exe'


def preflight(cs2_root=None):
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11 or newer is required.')
    if platform.system() != 'Windows':
        raise RuntimeError('Final compilation requires Windows CS2 Workshop Tools.')
    if cs2_root and not cs2_project.is_cs2_root(cs2_root.resolve()):
        raise RuntimeError(f'Invalid --cs2-root: {cs2_root}')
    installed = cs2_project.discover_cs2_root(cs2_root)
    if not PACKER.is_file():
        raise RuntimeError(f'Missing {PACKER}. Follow docs/BUILD_HANDOFF.md to install VPKEdit 4.4.2 CLI.')
    try:
        from package_cs2 import blake3_digest
        blake3_digest(b'preflight')
    except Exception as error:
        raise RuntimeError('Install build dependencies: python -m pip install -r requirements-build.txt') from error
    # Import the entire generation pipeline now, before any deployment.
    import cs2_campus  # noqa: F401
    for relative in ('exports/povo_blockout/povo_blockout.obj',
                     'cs2/content/trento_povo/maps/trento_povo.vmap',
                     'config/povo1_campus.json'):
        if not (ROOT / relative).is_file():
            raise RuntimeError(f'Missing source: {relative}. Use the complete checkout or handoff ZIP.')
    return installed


def run_logged(arguments, path):
    print(f'Running: {subprocess.list2cmdline(arguments)}\nLog: {path}', flush=True)
    with path.open('w', encoding='utf-8') as log:
        with subprocess.Popen(arguments, cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True,
                              encoding='utf-8', errors='replace',
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}) as process:
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            if process.wait():
                raise RuntimeError(f'Command failed ({process.returncode}); see {path}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cs2-root', type=Path, help='Steam game installation, not the addon directory')
    parser.add_argument('--season', choices=('standard', 'winter', 'both'), default='standard')
    parser.add_argument('--fast-lighting', action='store_true', help='Use a 2048-pixel atlas with normal-quality lighting')
    parser.add_argument('--lighting-quality', type=int, choices=(0,1), default=1, help='Explicit bake quality, 0 preview or 1 normal')
    parser.add_argument('--check', action='store_true', help='Check prerequisites without generating or deploying files')
    args = parser.parse_args(argv)
    try:
        installed = preflight(args.cs2_root)
        print(f'Prerequisites ready. CS2: {installed}', flush=True)
        if args.check:
            return 0
        running = subprocess.check_output(
            ['tasklist', '/FI', 'IMAGENAME eq resourcecompiler.exe', '/FO', 'CSV', '/NH'],
            text=True)
        if 'resourcecompiler.exe' in running.lower():
            raise RuntimeError('A Valve resource compiler is already running. Wait for that build to finish.')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        logs = ROOT / 'build/handoff' / stamp
        logs.mkdir(parents=True)
        record = {'started_utc': stamp, 'python': sys.version, 'platform': platform.platform(),
                  'cs2_root': str(installed), 'season': args.season, 'fast_lighting': args.fast_lighting,
                  'lighting_quality': args.lighting_quality, 'status': 'running'}
        try:
            record['git_revision'] = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
            record['git_status'] = subprocess.check_output(
                ['git', 'status', '--short'], cwd=ROOT, text=True)
        except (OSError, subprocess.CalledProcessError):
            record['git_revision'] = 'source snapshot (no Git metadata)'
        report = logs / 'build.json'
        report.write_text(json.dumps(record, indent=2), encoding='utf-8')
        try:
            run_logged([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'], logs / 'tests.log')
            run_logged([sys.executable, '-u', 'tools/cs2_campus.py', '--cs2-root', str(installed),
                        '--season', args.season, *(['--fast-lighting'] if args.fast_lighting else []),
                        '--lighting-quality',str(args.lighting_quality)], logs / 'compile.log')
            for season in (('standard', 'winter') if args.season == 'both' else (args.season,)):
                name = 'trento_povo_campus' + ('_winter' if season == 'winter' else '')
                run_logged([sys.executable, 'tools/verify_cs2_package.py', f'build/package/{name}.vpk',
                            '--map', name, '--model', 'povo1_campus', '--overview',
                            f'exports/povo_campus/radar/{name}.txt', '--full-crc', '--report',
                            str(logs / f'{name}-check.json')], logs / f'{name}-check.log')
            record['status'] = 'passed'
        except BaseException:
            record['status'] = 'failed'
            raise
        finally:
            record['finished_utc'] = datetime.now(timezone.utc).isoformat()
            report.write_text(json.dumps(record, indent=2), encoding='utf-8')
        print(f'Build verified. Packages: {ROOT / "build/package"}\nEvidence: {logs}')
        return 0
    except (RuntimeError, OSError, cs2_project.ProjectError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
