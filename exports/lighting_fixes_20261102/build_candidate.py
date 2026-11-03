"""Build an isolated standard-season lighting-geometry repair candidate."""
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools import cs2_campus as campus
from tools.cs2_project import discover_cs2_root
from tools.package_cs2 import package_map
work=ROOT/'build/lighting-fixes-20261102';work.mkdir(exist_ok=True)
options=campus.map_lighting_options
campus.map_lighting_options=lambda **kw:[*options(quality=kw.get('quality',1)),'-lightmapMaxResolution','1024']
installed=discover_cs2_root();campus.build(installed,pack=False)
short=ROOT/'build/lfr';short.mkdir(exist_ok=True)
report=package_map(installed,ROOT/'build/tools/vpkedit-4.4.2/vpkeditcli.exe',short/'candidate.vpk',
    force=True,map_name='trento_povo_campus',model_name='povo1_campus',
    overview_source=ROOT/'exports/povo_campus/radar/trento_povo_campus.txt',
    extra_assets=['soundevents/soundevents_addon.vsndevts_c','maps/scripts/povo_ffa.vjs_c','models/povo/povo1_campus_paving.vmdl_c'])
target=work/'candidate.vpk';shutil.copyfile(short/'candidate.vpk',target)
report['package']=str(target);target.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
print('Lighting fixture and frontage lamp candidate build passed',flush=True)
