#!/usr/bin/env python3
"""Adopt a native cubemap bake only if every packaged source entry is intact."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

try:
    from .cs2_project import discover_cs2_root
    from .vpk import Package
    from .verify_cs2_package import verify_package
except ImportError:
    from cs2_project import discover_cs2_root
    from vpk import Package
    from verify_cs2_package import verify_package

ROOT=Path(__file__).resolve().parents[1]


def adopt(*,season='standard',cs2_root=None):
    name='trento_povo_campus'+('_winter' if season=='winter' else '')
    source=discover_cs2_root(cs2_root)/'game/csgo_addons/trento_povo_campus_test/maps'/(name+'.vpk')
    target=ROOT/'build/package'/(name+'.vpk');report_path=target.with_suffix('.json')
    previous=json.loads(report_path.read_text())
    baked=Package(source)
    hashes={name:hashlib.sha256(b''.join(baked.chunks(entry))).hexdigest()
            for name,entry in baked.entries.items()}
    expected=previous['packaged_asset_sha256']
    for path,sha in expected.items():
        if hashes.get(path)!=sha:raise RuntimeError('Cubemap bake changed packaged source: '+path)
    added=set(hashes)-set(expected);cube='maps/'+name+'/cubemaps/env_cubemap_array.vtex_c'
    if added not in ({cube},set()) or cube not in hashes:raise RuntimeError('Unexpected or absent cubemap entries: '+repr(added))
    report=verify_package(source,ROOT/'exports/povo_campus/radar'/(name+'.txt'),
                          full_crc=True,map_name=name,model_name='povo1_campus')
    if report['status']!='passed':raise RuntimeError(report['errors'])
    backup=ROOT/'build/atmosphere'/(name+'-before-cubemaps.vpk');backup.parent.mkdir(parents=True,exist_ok=True)
    if added:shutil.copyfile(target,backup)
    temporary=target.with_suffix('.vpk.tmp');shutil.copyfile(source,temporary);temporary.replace(target)
    previous.update(report)
    previous.update(package=str(target),package_bytes=target.stat().st_size,packaged_asset_sha256=hashes,
                    cubemap_bake=dict(source=str(source),added_entries=sorted(added),previous_entries_unchanged=True))
    report_tmp=report_path.with_suffix('.json.tmp');report_tmp.write_text(json.dumps(previous,indent=2)+'\n');report_tmp.replace(report_path)
    print(json.dumps({k:previous[k] for k in ('status','package_bytes','package_entries','package_sha256')}))
    return previous


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season',choices=('standard','winter'),default='standard')
    parser.add_argument('--cs2-root',type=Path)
    args=parser.parse_args();adopt(season=args.season,cs2_root=args.cs2_root)
