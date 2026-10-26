#!/usr/bin/env python3
"""Bundle a compiled Povo map and its addon assets into a verified map VPK.

Requires the standalone VPKEdit CLI. Never modifies the compiler's original VPK.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

try:
    from .cs2_project import ADDON_NAME, REPO_ROOT, SYNC_CONTENT, discover_cs2_root
    from .verify_cs2_package import RADAR_ALIASES, RADAR_FILES, compare_overviews, verify_package, radar_layout, overview_values
    from .vpk import MAGIC, Package, VPKError
except ImportError:
    from cs2_project import ADDON_NAME, REPO_ROOT, SYNC_CONTENT, discover_cs2_root
    from verify_cs2_package import RADAR_ALIASES, RADAR_FILES, compare_overviews, verify_package, radar_layout, overview_values
    from vpk import MAGIC, Package, VPKError


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require_unsigned(package):
    if not package.signature_size:
        return
    # CS2 writes a 20-byte signature descriptor even without signing keys.
    # ValvePak Package.Read.cs ReadSignatureSection documents this variant.
    with package.path.open('rb') as stream:
        header = struct.unpack('<7I', stream.read(28))
        stream.seek(28 + sum(header[2:6]))
        trailer = stream.read(package.signature_size)
    if trailer != struct.pack('<5I', MAGIC, 1, 0, 0, 0):
        raise VPKError('Refusing to repack a signed or unknown signature trailer')


def blake3_digest(data):
    try:
        from blake3 import blake3
    except ImportError:
        # Keep the optional packager dependency local to this project.
        local_dependencies = REPO_ROOT / 'build/tools/python'
        if str(local_dependencies) not in sys.path:
            sys.path.insert(0, str(local_dependencies))
        try:
            from blake3 import blake3
        except ImportError as error:
            raise VPKError('Install blake3: python -m pip install --target '
                           'build/tools/python blake3==1.0.11') from error
    return blake3(data).digest(length=16)


def source2_hashes(path):
    """Write the BLAKE3 chunk table expected by current CS2, not Source 1 MD5.

    Wire format: ValvePak ChunkHashFraction.cs, EHashType.cs and Package.Verify.cs.
    The installed compiler uses 1 MiB fractions and the empty signature descriptor.
    """
    package = Package(path)
    require_unsigned(package)
    if package.version != 2 or any(e.archive_index != 0x7fff
                                  for e in package.entries.values()):
        raise VPKError('Source 2 hash generation requires a single-file VPK v2')
    raw = Path(path).read_bytes()
    tree = raw[28:package.data_offset]
    payload = raw[package.data_offset:package.data_offset + package.embedded_size]
    table = bytearray()
    for offset in range(0, len(payload), 1024 * 1024):
        block = payload[offset:offset + 1024 * 1024]
        table.extend(struct.pack('<HHII16s', 0x7fff, 1, offset, len(block),
                                 blake3_digest(block)))
    header = struct.pack('<7I', MAGIC, 2, len(tree), len(payload), len(table), 48, 20)
    prefix = (header + tree + payload + table + hashlib.md5(tree).digest()
              + hashlib.md5(table).digest())
    Path(path).write_bytes(prefix + hashlib.md5(prefix).digest()
                           + struct.pack('<5I', MAGIC, 1, 0, 0, 0))


def package_map(cs2_root, vpkedit, output, *, repo_root=REPO_ROOT, force=False,
                map_name='trento_povo', model_name='povo_blockout', overview_source=None, extra_assets=()):
    addon = Path(cs2_root) / 'game' / 'csgo_addons' / ADDON_NAME
    overview = Path(overview_source) if overview_source else Path(repo_root) / 'exports/povo_radar/trento_povo.txt'
    values=overview_values(overview.read_bytes(),map_name)
    sections={k.split('.')[1] for k in values if k.startswith('verticalsections.')}
    files,aliases=radar_layout(map_name,sections=sections)
    source = addon / 'maps' / (map_name+'.vpk')
    output = Path(output).resolve()
    if output.suffix.lower() != '.vpk':
        raise VPKError('Output must have a .vpk extension')
    report_path = output.with_suffix('.json')
    if output == source.resolve() or addon.resolve() in output.parents:
        raise VPKError('Build outside the installed addon; preserve compiler output')
    if not force and (output.exists() or report_path.exists()):
        raise VPKError('Output already exists; use --force to replace a verified build')
    if not Path(vpkedit).is_file():
        raise VPKError(f'VPKEdit CLI is missing: {vpkedit}')

    package = Package(source)
    require_unsigned(package)
    if 'maps/'+map_name+'.vmap_c' not in package.entries:
        raise VPKError('Compiled Povo map resource is missing')

    # Only addon-owned runtime assets: no photos, editable sources, caches or
    # workstation configuration. Include compiler-generated texture dependencies.
    assets = set(files) - set(aliases)
    assets.add('models/povo/'+model_name+'.vmdl_c')
    assets.add('cfg/maps/'+map_name+'.cfg')
    for name in extra_assets:
        if name.startswith('/') or '\\' in name or ':' in name or any(p in ('','..','.') for p in name.split('/')):
            raise VPKError('Invalid extra asset path: '+name)
        assets.add(name)
    assets.update(rel.as_posix() + '_c' for rel in SYNC_CONTENT
                  if rel.suffix == '.vmat')
    for directory in ('materials/trento/povo', 'materials/default'):
        assets.update(p.relative_to(addon).as_posix()
                      for p in (addon / directory).rglob('*.vtex_c'))
    if map_name != 'trento_povo':
        assets.update(p.relative_to(addon).as_posix()
                      for p in (addon/'materials/trento/povo/campus').rglob('*.vmat_c'))
    if not any(name.startswith('materials/trento/povo/') and name.endswith('.vtex_c')
               for name in assets):
        raise VPKError('Compile the terrain texture before packaging')
    for name in assets:
        path = addon / name
        if not path.is_file() or not path.stat().st_size:
            raise VPKError(f'Compile/deploy before packaging; missing or empty {name}')
    if compare_overviews((addon / files[-1]).read_bytes(), overview.read_bytes(),map_name):
        raise VPKError('Installed overview differs from the generated radar; rebuild radar')

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='povo-package-', dir=output.parent) as tmp:
        staging = Path(tmp) / 'assets'
        staging.mkdir()
        expected = {}
        for entry in package.entries.values():
            target = staging / entry.path
            target.parent.mkdir(parents=True, exist_ok=True)
            crc = 0
            with target.open('wb') as stream:
                for chunk in package.chunks(entry):
                    crc = zlib.crc32(chunk, crc)
                    stream.write(chunk)
            if crc != entry.crc32:
                raise VPKError(f'CRC mismatch for {entry.path}')
            expected[entry.path.casefold()] = digest(target)
        for name in sorted(assets):
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(addon / name, target)
            expected[name.casefold()] = digest(target)
        # Current CS2 requests the PSD lookup names even for generated textures.
        # VTEX payloads are identical; aliases preserve the existing TGA sources.
        for name, original in aliases.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staging / original, target)
            expected[name.casefold()] = digest(target)

        candidate = Path(tmp) / (map_name+'.vpk')
        command = [str(Path(vpkedit).resolve()), str(staging), '--output',
                   str(candidate), '--single-file', '--version', '2',
                   '--gen-md5-entries', '--no-progress']
        subprocess.run(command, check=True)
        packed = Package(candidate)
        if set(packed.entries) != set(expected):
            raise VPKError('Packed entries differ from staged assets')
        for name, entry in packed.entries.items():
            hashed = hashlib.sha256()
            for chunk in packed.chunks(entry):
                hashed.update(chunk)
            if hashed.hexdigest() != expected[name]:
                raise VPKError(f'Packed bytes differ from source: {name}')
        source2_hashes(candidate)
        report = verify_package(candidate, overview, full_crc=True,map_name=map_name,model_name=model_name)
        if report['status'] != 'passed':
            raise VPKError('; '.join(report['errors']))
        report.update(package=str(output), source_package=str(source),
                      source_package_sha256=digest(source),
                      packer=str(Path(vpkedit).resolve()),
                      packer_sha256=digest(vpkedit),
                      chunk_hash_type='BLAKE3-128, 1 MiB fractions (CS2)',
                      radar_runtime_aliases=aliases,
                      packaged_asset_sha256=expected,
                      original_map_entries=len(package.entries),
                      loose_assets_added=len(assets),
                      package_bytes=candidate.stat().st_size)
        saved_report = Path(tmp) / 'report.json'
        saved_report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        candidate.replace(output)
        saved_report.replace(report_path)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cs2-root', type=Path)
    parser.add_argument('--vpkedit', required=True, type=Path)
    parser.add_argument('--output', type=Path,
                        default=REPO_ROOT / 'build/package/trento_povo.vpk')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--map',dest='map_name',default='trento_povo')
    parser.add_argument('--model',dest='model_name',default='povo_blockout')
    parser.add_argument('--overview',type=Path)
    args = parser.parse_args(argv)
    try:
        report = package_map(discover_cs2_root(args.cs2_root), args.vpkedit,
                             args.output, force=args.force,map_name=args.map_name,
                             model_name=args.model_name,overview_source=args.overview)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f'error: {error}\n')
    print(f"Built {report['package']}: {report['package_bytes']:,} bytes, "
          f"{report['package_entries']} entries, all CRCs and source hashes verified")
    print('Runtime, clean-install and independent-client checks remain required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
