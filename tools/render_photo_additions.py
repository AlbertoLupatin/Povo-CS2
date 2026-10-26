#!/usr/bin/env python3
"""Render a labelled source plan of the 26 October Povo 2 additions (Pillow)."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from .build_povo_campus import build_geometry, COLORS
except ImportError:
    from build_povo_campus import build_geometry, COLORS


def render(output):
    _,_,boxes,levels,_=build_geometry()
    spec=levels[1]['connection']['povo2']
    image=Image.new('RGB',(2160,1200),'#f1f3f3')
    draw=ImageDraw.Draw(image)
    font=ImageFont.load_default(size=15)
    title=ImageFont.load_default(size=22)
    draw.text((25,20),'POVO 2 / 26 OCTOBER PHOTO ADDITIONS / SOURCE PLAN',font=title,fill='#173348')
    draw.text((25,57),'Estimated dimensions. Temporary room labels and aula magna. Windows compile and engine checks pending.',font=font,fill='#384c55')
    panels=[('Povo 2 ground additions',4,(6,-1,55,102),(30,105),9),
            ('Basement: CIBIO offices',.4,(-7,-17,58,32),(650,150),10.5),
            ('Wings: ground',4,(28,-112,59,-11),(1440,150),8),
            ('Wings: first',7.6,(28,-112,59,-11),(1780,150),8)]
    for label,z,bounds,origin,scale in panels:
        a,b,c,d=bounds;ox,oy=origin
        def xy(x,y):return ox+(x-a)*scale,oy+(d-y)*scale
        def rectangle(lo,hi,color):
            x0,y0=xy(lo[0],hi[1]);x1,y1=xy(hi[0],lo[1])
            draw.rectangle((x0,y0,x1,y1),fill=color)
        draw.text((ox,oy-30),label,font=title,fill='#173348')
        # Paint floors, then furniture, then standing walls/glazing.
        prefixes=('p2_',) if ox<1400 else ('library_','canteen_')
        selected=[box for box in boxes if box[0].startswith(prefixes) and box[2][2]>z-.01
                  and box[1][2]<z+2.5 and box[1][0]<c and box[2][0]>a
                  and box[1][1]<d and box[2][1]>b]
        for _,lo,hi,m in sorted(selected,key=lambda q:0 if q[3].startswith('floor_') else 2 if q[3]=='wall' else 1):
            lo=(max(a,lo[0]),max(b,lo[1]),lo[2]);hi=(min(c,hi[0]),min(d,hi[1]),hi[2])
            rectangle(lo,hi,COLORS[m])
        if ox<1400:
            level=next(l for l in spec['levels'] if abs(l['z']-z)<.01)
            rooms=level.get('rooms',[]);stations=level['audit_stations']
        else:
            wing_levels=[l for l in levels[0]['wings']['levels'] if abs(l['z']-z)<.01]
            rooms=[];stations=[s for l in wing_levels for s in l['audit_stations']]
            for l in wing_levels:
                x0,y0,x1,y1=l['bounds'];px,py=xy((x0+x1)/2,(y0+y1)/2)
                draw.text((px,py),l['building'].upper(),font=font,fill='#003050',anchor='mm',stroke_width=2,stroke_fill='white')
        for room in rooms:
            x0,y0,x1,y1=room['bounds'];x,y=xy((x0+x1)/2,(y0+y1)/2)
            draw.text((x,y),room['label'],font=font,fill='#003050',anchor='mm',stroke_width=2,stroke_fill='white')
        for s in stations:
            x,y=xy(*s['point'])
            if ox<=x<=ox+(c-a)*scale and oy<=y<=oy+(d-b)*scale:
                draw.ellipse((x-2,y-2,x+2,y+2),fill='#009459')
        def label(text,x,y):
            px,py=xy(x,y)
            draw.text((px,py),text,font=font,fill='#003050',anchor='mm',stroke_width=2,stroke_fill='white')
        def route(points,color):
            import math
            pts=[xy(*p) for p in points]
            draw.line(pts,fill=color,width=3)
            for start,end in zip(pts,pts[1:]):
                angle=math.atan2(end[1]-start[1],end[0]-start[0]);length=7
                wing=[(end[0]-length*math.cos(angle+t),end[1]-length*math.sin(angle+t)) for t in (-.5,.5)]
                draw.polygon([end,*wing],fill=color)
        if z==4 and ox<1400:
            for text,x,y in [('TMP AULA MAGNA',45.5,90),('AULA LOBBY',25,75),('CORRIDOR',24,12),
                             ('RECEPTION',16.5,32.5),('STAIR DOOR',19,28),('YARD BELOW',53,19)]:label(text,x,y)
        elif ox<1400:
            route([(17.8,22),(18.25,22),(18.25,-5),(13,-5)],'#b14431')
            route([(18.6,22),(18.6,27.5),(47,27.5)],'#2374ab')
            label('STAIR EXIT',10,22)
            label('RIGHT + RIGHT',5,-1.8)
            label('LEFT + RIGHT / EXIT',35,30.5)
        elif ox>1400 and z==4:
            label('BAR / RIGHT',44,-107)
            label('DINING / LEFT',44,-87)
            label('STAIRS',46,-99.5)
            route([(32,-97),(33.5,-97),(33.5,-99.5),(43,-99.5)],'#2374ab')
    draw.text((650,900),'Green dots: source clearance stations. North is up.',font=font,fill='#173348')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);image.save(output)
    print(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/photo-additions-review.png'))
    render(parser.parse_args().output)
