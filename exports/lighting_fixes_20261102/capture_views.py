"""Normal-lit views matching the audited fixture and lamp defects."""
from pathlib import Path
import hashlib,json,math,re,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.cs2_console import run
from tools.cs2_campus import world
from tools.cs2_project import discover_cs2_root

VIEWS=[
 ('west_terrace',[-8.7,-70,12.82],[-8.7,-54.65,14.436]),
 ('east_terrace',[10.43,-59.5,12.82],[10.43,-49,14.436]),
 ('east_terrace_across',[0,-60,12.82],[10.43,-60,14.436]),
 ('stair_wall_19',[8,19,12.82],[10.925,19,14.35]),
 ('stair_wall_24',[8,24,12.82],[10.925,24,14.35]),
 ('lamp_0',[52,15.575,5.62],[55.575,15.575,6.2]),
 ('lamp_1',[52,28.575,5.62],[55.575,28.575,4.67]),
 ('aula_roof',[59,80.575,8.5],[55.575,80.575,7.4]),
 ('aula_corner',[59,93.575,5.62],[55.575,93.575,5.2]),
 ('entrance_preserved',[28,24,5.6256],[20.5,22,6.1]),
 ('basement_preserved',[-12,16.6,2.02],[-20,12,2.02]),
]

def main():
    out=Path(__file__).parent/'native';out.mkdir(exist_ok=True)
    state=run(['status'],seconds=.5)
    if 'trento_povo_campus | main lump' not in state or not re.search(r'players\s*:\s*1 humans, 0 bots',state):raise RuntimeError('Solo review guard rejected')
    shots=discover_cs2_root()/'game/csgo_addons/trento_povo_lighting_review/screenshots'
    package=ROOT/'build/lighting-fixes-20261102/candidate.vpk';digest=hashlib.sha256(package.read_bytes()).hexdigest()
    assert hashlib.sha256((shots.parent/'maps/trento_povo_campus.vpk').read_bytes()).hexdigest()==digest
    log=[state];captures=[]
    try:
        log.append(run(['sv_cheats 1','mat_fullbright 0','gameui_hide','cl_drawhud 0','r_drawviewmodel 0','noclip 1'],seconds=.3))
        for name,eye,target in VIEWS:
            dx,dy,dz=[target[k]-eye[k] for k in range(3)]
            yaw=math.degrees(math.atan2(dx,-dy));pitch=-math.degrees(math.atan2(dz,math.hypot(dx,dy)))
            log.append(run(['setpos_exact '+world((eye[0],eye[1],eye[2]-1.62)),f'setang {pitch:.5f} {yaw:.5f} 0'],seconds=.7))
            token='light_fix_'+name;before=set(shots.glob(token+'*.tga'))
            log.append(run(['screenshot '+token],seconds=1.2));added=set(shots.glob(token+'*.tga'))-before
            if len(added)!=1:raise RuntimeError('Missing screenshot '+name)
            dest=out/(name+'.png');Image.open(added.pop()).save(dest)
            captures.append(dict(name=name,eye=eye,target=target,image=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            print(name,'captured',flush=True)
    finally:
        log.append(run(['mat_fullbright','cl_drawhud 1','r_drawviewmodel 1'],seconds=.3))
        (out/'console.log').write_text('\n'.join(log),encoding='utf-8')
        (out/'captures.json').write_text(json.dumps(dict(package_sha256=digest,captures=captures),indent=2)+'\n')
    sheet=Image.new('RGB',(1440,math.ceil(len(captures)/3)*324),'#edf0f1');draw=ImageDraw.Draw(sheet)
    for i,c in enumerate(captures):
        im=Image.open(out/c['image']);im.thumbnail((480,300));x=i%3*480;y=i//3*324
        sheet.paste(im,(x,y));draw.text((x+5,y+304),c['name'],fill='#182b32')
    sheet.save(out/'contact-sheet.jpg',quality=94)

if __name__=='__main__':main()
