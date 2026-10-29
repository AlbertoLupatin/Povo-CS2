"""Show the implemented -2 exit route, facing out of the stair door."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import build_geometry
except ImportError:
    from build_povo_campus import build_geometry


def render():
    _,_,boxes,levels,_=build_geometry()
    spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
    portal=next(p for p in spec['stairs']['portals'] if p['floor']==-2)['centre']
    image=Image.new('RGB',(1280,800),'#faf9f5');d=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',23)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',29)
    d.text((35,25),'CORRECTED ROUTE: leaving the -2 stair door',font=title,fill='#1e3445')
    d.text((35,68),'View rotated so you exit facing UP. Arrows follow the generated floor and door positions.',font=font,fill='#526574')
    scale=38
    def xy(x,y):return (55+(36-x)*scale,185+(y-10.5)*30)
    def box(lo,hi,fill):
        left,right=max(8,lo[0]),min(36,hi[0]);bottom,top=max(10.5,lo[1]),min(24,hi[1])
        if left>=right or bottom>=top:return
        x0,y0=xy(right,bottom);x1,y1=xy(left,top)
        d.rectangle((x0,y0,x1,y1),fill=fill)
    selected=('p2_parking_vestibule','p2_parking_office_corridor','p2_parking_right_branch',
              'p2_parking_right_turn','p2_parking_garden_corridor','p2_parking_south_landing','p2_parking_new_core_floor')
    for n,lo,hi,m in boxes:
        if n.startswith(selected) and m.startswith('floor_') and abs(hi[2]+3.2)<.02:box(lo,hi,'#e0e9ed')
    for n,lo,hi,m in boxes:
        if n.startswith(('p2_parking_','p2_internal_shell_-2')) and lo[2]<-2.2<hi[2]:
            if m=='wall':box(lo,hi,'#4b5863')
            elif m in ('door_black','door_closed'):box(lo,hi,'#987c55')
    # Physical route nodes are read from the assembled model's metadata.
    def arrow(p,q,color):
        x,y=xy(*p);u,v=xy(*q);d.line((x,y,u,v),fill=color,width=6)
        angle=math.atan2(v-y,u-x)
        d.polygon([(u,v),(u-15*math.cos(angle-.5),v-15*math.sin(angle-.5)),
                   (u-15*math.cos(angle+.5),v-15*math.sin(angle+.5))],fill=color)
    green='#16766a';orange='#c56d16';blue='#285ca8'
    arrow((portal[0],18.7),(portal[0],16.05),blue)
    for route,color in zip(spec['parking']['routes'][1:],(orange,green,'#76529a')):
        points=route['points']
        for p,q in zip(points,points[1:]):arrow(p[:2],q[:2],color)
    x,y=xy(*portal[:2]);d.ellipse((x-9,y-9,x+9,y+9),fill=blue)
    d.text((x-52,y+45),'STAIRS',font=bold,fill='#1e3445')
    d.text((x+20,y+5),'1  Exit door',font=bold,fill=blue)
    d.text((x-75,135),'2  Vestibule',font=bold,fill=blue)
    d.text((xy(spec['parking']['vestibule'][0],16.05)[0]+14,xy(spec['parking']['vestibule'][0],16.05)[1]-42),'Right door',font=bold,fill=orange)
    d.text((xy(20.5,16.05)[0]+25,xy(20.5,16.05)[1]-42),'Left door',font=bold,fill=green)
    d.text((1035,165),'Parking',font=bold,fill=orange)
    d.text((65,245),'Garden -2',font=bold,fill=green)
    d.text((520,590),'Other offices',font=bold,fill='#76529a')
    d.text((300,398),'Wall straight ahead',font=small,fill='#4b5863')
    d.line((470,412,*xy(24,18)),fill='#4b5863',width=2)
    d.text((35,620),'What is currently built:',font=bold,fill='#1e3445')
    d.text((35,658),'1. Exit into the vestibule.  2. Right through doors toward parking.',font=font,fill='#1e3445')
    d.text((35,693),'3. Left through doors: wall ahead. Left to offices; right, then left to the garden.',font=font,fill='#1e3445')
    d.text((35,748),'Plan-inferred vestibule: 9.5 x 3.6 m. Stair door moved toward the left; dimensions provisional.',font=small,fill='#526574')
    out=Path(__file__).resolve().parents[1]/'exports/povo2_layout_audit_20261028/minus2_exit_route_corrected.png'
    image.save(out);return out


if __name__=='__main__':print(render())
