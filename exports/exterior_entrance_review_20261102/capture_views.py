"""Record normal-lit native views of the corrected entrance and A-D fills."""
from pathlib import Path
import hashlib,json,math,re,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.cs2_console import run
from tools.cs2_project import discover_cs2_root
from tools.cs2_campus import world

VIEWS=[
    ('entrance_ceiling',[28,24,5.6256],[20.5,22,6.1]),
    ('entrance_side_wall',[25,17,5.6256],[20.5,16,5.5]),
    ('entrance_sign',[24,22,5.6256],[20.5,22,6.5]),
    ('entrance_flat_ceiling',[24,26,5.6256],[24,17,7.1]),
    ('fill_A_facing',[36,-.8,2.3],[33,5,1.8]),
    ('fills_B_C',[43.8,-4,4.2],[43.8,4,2]),
    ('fill_D_support',[54,5,-1.3],[57,8,1.]),
    ('exterior_overview',[74,-28,22],[44,8,1.5]),
    ('lower_garden',[49,17,-1.58],[57,8,1]),
    ('lower_approach',[43.8,7,-1.58],[43.8,1,1]),
]

def main():
    state=run(['status'],seconds=.4)
    if 'trento_povo_campus | main lump' not in state or not re.search(r'players\s*:\s*1 humans, 0 bots',state):
        raise RuntimeError('Requires fresh solo candidate review')
    out=Path(__file__).parent/'native';out.mkdir(exist_ok=True)
    screenshots=discover_cs2_root()/'game/csgo_addons/trento_povo_entrance_review/screenshots'
    package=ROOT/'build/exterior-entrance-20261102/candidate.vpk'
    installed=screenshots.parent/'maps/trento_povo_campus.vpk'
    digest=hashlib.sha256(package.read_bytes()).hexdigest()
    assert hashlib.sha256(installed.read_bytes()).hexdigest()==digest
    log=[state,run(['sv_cheats 1','mat_fullbright 0','gameui_hide','-showscores','cl_drawhud 0','r_drawviewmodel 0','noclip 1'],seconds=.4)]
    captures=[]
    try:
        for name,eye,target in VIEWS:
            dx,dy,dz=[target[i]-eye[i] for i in range(3)]
            yaw=math.degrees(math.atan2(dx,-dy));pitch=-math.degrees(math.atan2(dz,math.hypot(dx,dy)))
            log.append(run(['setpos_exact '+world([eye[0],eye[1],eye[2]-1.62]),f'setang {pitch:.5f} {yaw:.5f} 0'],seconds=.7))
            token='entrance_review_'+name.lower();before=set(screenshots.glob(token+'*.tga'))
            log.append(run(['screenshot '+token],seconds=1.2))
            added=set(screenshots.glob(token+'*.tga'))-before
            if len(added)!=1:raise RuntimeError('Missing screenshot '+name)
            im=Image.open(added.pop());im.thumbnail((1920,1200));dest=out/(name+'.png');im.save(dest)
            captures.append(dict(name=name,eye=eye,target=target,image=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            print(name,'captured',flush=True)
    finally:
        log.append(run(['mat_fullbright','cl_drawhud 1','r_drawviewmodel 1'],seconds=.3))
        (out/'capture.log').write_text('\n'.join(log),encoding='utf-8')
        (out/'captures.json').write_text(json.dumps(dict(package_sha256=digest,captures=captures),indent=2)+'\n')
    sheet=Image.new('RGB',(1440,math.ceil(len(captures)/3)*324),(235,238,240));draw=ImageDraw.Draw(sheet)
    for i,c in enumerate(captures):
        im=Image.open(out/c['image']);im.thumbnail((480,300));x=(i%3)*480;y=(i//3)*324
        sheet.paste(im,(x,y));draw.text((x+8,y+304),c['name'],fill=(20,30,40))
    sheet.save(out/'contact-sheet.jpg',quality=94)

if __name__=='__main__':main()
