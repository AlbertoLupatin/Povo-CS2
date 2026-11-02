"""Normal-lighting camera review of the lighting-repair candidate in a solo test addon."""
from pathlib import Path
import hashlib,json,math,re,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.cs2_console import run
from tools.cs2_campus import world
from tools.cs2_explore import campus_loaded
from tools.cs2_project import discover_cs2_root
VIEWS=[
 ('entrance',[26.3,32,5.6],[15,32,5.6]),
 ('c7',[18,16.6,2.0],[-8,16.6,2.0]),
 ('c5',[21.9,3.6,2.0],[21.9,19.5,2.0]),
 ('wi1',[16.5,9.26,2.0],[22,9.26,2.0]),
 ('terrace',[24,-5,8.0],[27,1.2,.4]),
 ('up_stair',[21.75,1.14,2.0],[21.75,-5,4.9]),
 ('down_stair',[30.7,1.14,2.0],[41,1.14,-2.1]),
 ('lower_approach',[43.8,7,-1.6],[43.8,1,-1.6]),
 ('campus',[72,-75,65],[4,-5,6]),
]

def main():
    status=run(['status'],seconds=.4)
    if not campus_loaded(status) or not re.search(r'players\s*:\s*1 humans, 0 bots',status):
        raise RuntimeError('Requires the agent-owned loaded solo review session')
    base=Path(__file__).parent;out=base/'normal-lighting';out.mkdir(exist_ok=True)
    screenshots=discover_cs2_root()/'game/csgo_addons/trento_povo_render_review/screenshots'
    candidate=ROOT/'build/rv/trento_povo_campus.vpk'
    log=[status];captures=[]
    log.append(run(['sv_cheats 1','mat_fullbright 0','cl_drawhud 0','r_drawviewmodel 0','noclip 1'],seconds=.5))
    for name,p,t in VIEWS:
        dx,dy,dz=[t[i]-p[i] for i in range(3)]
        yaw=math.degrees(math.atan2(dx,-dy));pitch=-math.degrees(math.atan2(dz,math.hypot(dx,dy)))
        # setpos is the player's feet; camera positions above include the eye height.
        feet=[p[0],p[1],p[2]-1.62]
        log.append(run(['setpos_exact '+world(feet),f'setang {pitch:.5f} {yaw:.5f} 0'],seconds=.7))
        prefix='lighting_fix_'+name;before=set(screenshots.glob(prefix+'*.tga'))
        log.append(run(['screenshot '+prefix],seconds=1))
        added=set(screenshots.glob(prefix+'*.tga'))-before
        if len(added)!=1:raise RuntimeError('Screenshot missing: '+name)
        target=out/(name+'.png');Image.open(added.pop()).save(target)
        captures.append(dict(name=name,camera=p,target=t,image=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        print(name,'captured',flush=True)
    log.append(run(['mat_fullbright','cl_drawhud 1','r_drawviewmodel 1'],seconds=.3))
    (out/'capture.log').write_text('\n'.join(log))
    (out/'captures.json').write_text(json.dumps(dict(package_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
        scope='Native normal-lighting visual cameras; noclip placement, not movement verification',captures=captures),indent=2)+'\n')

if __name__=='__main__':main()
