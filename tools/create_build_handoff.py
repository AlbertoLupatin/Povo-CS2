#!/usr/bin/env python3
"""Snapshot current Git-listed source, including uncommitted and untracked files.

Excludes ignored files (build outputs, virtual environments) and Git history.
Run while source editing/generation is idle; a concurrent change fails the export.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/handoff/povo-cs2-source.zip')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f'Output already exists: {output}. Choose a new filename.')
    names = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT
    ).decode('utf-8').split('\0')
    paths = sorted({ROOT / name for name in names if name and (ROOT / name).is_file()})
    if output in paths:
        parser.error('Output must not be a source file.')
    before = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in paths}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.partial')
    manifest = {}
    with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            manifest[relative] = hashlib.sha256(data).hexdigest()
            archive.writestr('Povo-CS2/' + relative, data)
        for path, metadata in before.items():
            if (path.stat().st_size, path.stat().st_mtime_ns) != metadata:
                raise RuntimeError(f'Source changed while exporting: {path}. Retry when editing is idle.')
        archive.writestr('Povo-CS2/HANDOFF_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    temporary.rename(output)
    print(f'Created {output} ({output.stat().st_size:,} bytes; {len(paths)} files).')


if __name__ == '__main__':
    main()
