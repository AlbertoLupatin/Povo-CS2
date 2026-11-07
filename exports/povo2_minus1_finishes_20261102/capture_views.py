"""Native normal-lit review of the office finishing candidate, in a solo addon."""
from pathlib import Path
import hashlib,json,math,re,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.cs2_console import run
from tools.cs2_project import discover_cs2_root
from tools.cs2_campus import world

VIEWS=[
    ('photo1_wall',[-12,16.6,2.02],[-20,12,2.02]),
    ('photo1_empty_door',[-12,16.6,2.02],[-13.91,14.5,2.02]),
    ('photo2_closed_wall',[-3.05,19.5,2.02],[-2.3,40,2.02]),
    ('W01',[19.3,11.2,2.02],[13.,14.2,1.4]),
    ('W02',[10.8,11.2,2.02],[4.,14.2,1.4]),
    ('W04',[.5,11.2,2.02],[-4.4,14.2,1.4]),
    ('professor_W10',[11.2,7.1,2.02],[9.3,3.1,1.4]),
    ('corner_W19',[-18.1,15.5,2.02],[-22.5,17.,1.4]),
    ('CIBIO_OFFICE_1',[-6.2,24.5,2.02],[-12.3,20.,1.4]),
    ('CIBIO_OFFICE_2',[-6.2,62.3,2.02],[-12.3,58.,1.4]),
    ('external_glass',[10.,.4,2.02],[10.,5.,1.4]),
    ('C7_unchanged',[18.,16.6,2.02],[-8.,16.6,2.02]),
]

def main():
    state=run(['status'],seconds=.4)
    if 'trento_povo_campus | main lump' not in state or not re.search(r'players\s*:\s*1 humans, 0 bots',state):
        raise RuntimeError('Requires loaded solo candidate review')
    out=Path(__file__).parent/'native';out.mkdir(exist_ok=True)
    screenshots=discover_cs2_root()/'game/csgo_addons/trento_povo_finish_review/screenshots'
    log=[state,run(['sv_cheats 1','mat_fullbright 0','gameui_hide','-showscores',
                   'cl_drawhud 0','r_drawviewmodel 0','noclip 1'],seconds=.4)]
    captures=[]
    for name,p,t in VIEWS:
        dx,dy,dz=[t[i]-p[i] for i in range(3)]
        yaw=math.degrees(math.atan2(dx,-dy));pitch=-math.degrees(math.atan2(dz,math.hypot(dx,dy)))
        log.append(run(['setpos_exact '+world([p[0],p[1],p[2]-1.62]),f'setang {pitch:.5f} {yaw:.5f} 0'],seconds=.7))
        token='finish_'+name.lower();before=set(screenshots.glob(token+'*.tga'))
        log.append(run(['screenshot '+token],seconds=1))
        added=set(screenshots.glob(token+'*.tga'))-before
        if len(added)!=1:raise RuntimeError('Missing screenshot '+name)
        im=Image.open(added.pop());im.thumbnail((1920,1080));target=out/(name+'.png');im.save(target)
        captures.append(dict(name=name,camera=p,target=t,image=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        print(name,'captured',flush=True)
    log.append(run(['mat_fullbright','cl_drawhud 1','r_drawviewmodel 1'],seconds=.3))
    (out/'capture.log').write_text('\n'.join(log),encoding='utf-8')
    package=ROOT/'build/minus1-finishes-20261102/candidate.vpk'
    (out/'captures.json').write_text(json.dumps(dict(package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        scope='Native normal-lit camera inspection, noclip placement; movement separate',captures=captures),indent=2)+'\n')
    sheet=Image.new('RGB',(1440,4*294),(235,238,240));draw=ImageDraw.Draw(sheet)
    for i,c in enumerate(captures):
        im=Image.open(out/c['image']);im.thumbnail((480,270));x=(i%3)*480;y=(i//3)*294
        sheet.paste(im,(x,y));draw.text((x+8,y+275),c['name'],fill=(20,30,40))
    sheet.save(out/'contact-sheet.jpg',quality=92)

if __name__=='__main__':main()
