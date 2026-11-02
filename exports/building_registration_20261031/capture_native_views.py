"""Capture the saved visual cameras in an already loaded solo campus session."""
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.cs2_campus import world
from tools.cs2_console import run
from tools.cs2_explore import campus_loaded
from tools.cs2_project import discover_cs2_root
from PIL import Image


def main():
    status=run(['status'],seconds=.5)
    if not campus_loaded(status,'trento_povo_campus') or not re.search(r'players\s*:\s*1 humans, 0 bots',status):
        raise RuntimeError('Requires the freshly loaded solo campus')
    output=Path(__file__).parent/'runtime-verified/visual'
    output.mkdir(parents=True,exist_ok=True)
    screenshots=discover_cs2_root()/'game/csgo_addons/trento_povo_campus_test/screenshots'
    views=json.loads((Path(__file__).parent/'native-visual-views.json').read_text())
    transcript=[status];captures=[]
    try:
        transcript.append(run(['sv_cheats 1','cl_drawhud 0','r_drawviewmodel 0','noclip 1'],seconds=.3))
        for view in views:
            p,t=view['position'],view['target'];dx,dy,dz=[t[i]-p[i] for i in range(3)]
            yaw=math.degrees(math.atan2(dx,-dy));pitch=-math.degrees(math.atan2(dz,math.hypot(dx,dy)))
            transcript.append(run(['setpos_exact '+world(p),f'setang {pitch:.5f} {yaw:.5f} 0'],seconds=.6))
            prefix='registration_final_'+view['id'];before=set(screenshots.glob(prefix+'*.tga'))
            transcript.append(run(['screenshot '+prefix],seconds=.8))
            added=set(screenshots.glob(prefix+'*.tga'))-before
            if len(added)!=1:raise RuntimeError('Screenshot was not uniquely written: '+prefix)
            source=added.pop();target=output/(view['id']+'.png')
            with Image.open(source) as im:im.save(target)
            captures.append(dict(**view,image=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
            print(view['id'],'captured',flush=True)
    finally:
        transcript.append(run(['cl_drawhud 1','r_drawviewmodel 1','noclip 0'],seconds=.2))
        (output/'capture.log').write_text('\n'.join(transcript))
        (output/'captures.json').write_text(json.dumps(dict(package_sha256=hashlib.sha256(
            (ROOT/'build/package/trento_povo_campus.vpk').read_bytes()).hexdigest(),
            scope='Noclip camera review; walking is verified separately',captures=captures),indent=2)+'\n')


if __name__=='__main__':main()
