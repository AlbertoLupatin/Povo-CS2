"""Package the clean native bake, keeping the published local VPK untouched."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.package_cs2 import package_map
from tools.cs2_project import discover_cs2_root
from tools.vpk import Package

work=ROOT/'build/render-corruption-20261102'
if (work/'native-1024-exit-code.txt').read_text().strip()!='0':raise RuntimeError('Native bake did not pass')
result=package_map(discover_cs2_root(),ROOT/'build/tools/vpkedit-4.4.2/vpkeditcli.exe',
    ROOT/'build/rv/trento_povo_campus.vpk',force=True,map_name='trento_povo_campus',model_name='povo1_campus',
    overview_source=ROOT/'exports/povo_campus/radar/trento_povo_campus.txt',
    extra_assets=['soundevents/soundevents_addon.vsndevts_c','maps/scripts/povo_ffa.vjs_c',
                  'models/povo/povo1_campus_paving.vmdl_c'])
before=Package(work/'corrupt-input.vpk');after=Package(ROOT/'build/rv/trento_povo_campus.vpk')
checks=[]
for name in ['models/povo/povo1_campus.vmdl_c','models/povo/povo1_campus_paving.vmdl_c']:
    a=hashlib.sha256(b''.join(before.chunks(before.entries[name]))).hexdigest()
    b=hashlib.sha256(b''.join(after.chunks(after.entries[name]))).hexdigest()
    checks.append(dict(name=name,before_sha256=a,after_sha256=b,unchanged=a==b))
if not all(c['unchanged'] for c in checks):raise RuntimeError('Structural/finishing model unexpectedly changed')
report=dict(status='passed',package_sha256=result['package_sha256'],package_bytes=result['package_bytes'],
    package_entries=result['package_entries'],crc_verified_entries=result['crc_verified_entries'],models=checks,
    native_lighting=dict(atlas=1024,quality=1,script_modified=False),native_visual_status='pending')
(ROOT/'exports/render_corruption_20261102/candidate.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
