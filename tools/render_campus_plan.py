#!/usr/bin/env python3
"""Draw the generated campus room/corridor layout for visual review (Pillow)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from .build_povo_campus import ROOT, build_geometry
except ImportError:
    from build_povo_campus import ROOT, build_geometry


def render(output=ROOT/'exports/povo_campus/adjustments_layout_review.png'):
    _settings,_config,boxes,levels,stair=build_geometry()
    image=Image.new('RGB',(1240,1070),'#edf1f2')
    draw=ImageDraw.Draw(image)
    title=ImageFont.truetype('arial.ttf',25)
    label=ImageFont.truetype('arial.ttf',12)
    heading=ImageFont.truetype('arial.ttf',18)
    draw.text((35,24),'POVO 1 / COMPLETE ROOM LAYOUT',font=title,fill='#193441')
    draw.text((35,65),'Updated reception, four separate restrooms, and four mirrored enclosed red stairs.',font=heading,fill='#193441')
    scale=10
    for i,level in enumerate(levels):
        left,top=65+i*610,155
        def point(x,y):return left+(x+23)*scale,top+(-20-y)*scale
        def rectangle(bounds,fill,outline=None,width=1):
            x0,y0,x1,y1=bounds
            draw.rectangle((*point(x0,y1),*point(x1,y0)),fill=fill,outline=outline,width=width)
        z=level['floor_elevation_metres']-370
        draw.text((left,115),f"{'GROUND' if i==0 else 'FLOOR 1'} / {len(level['rooms'])} rooms",font=heading,fill='#193441')
        rectangle((-23,-103,24,-20),'#d7e9ed','#193441',2)
        for room in level['rooms']:
            a,b,c,d=room['footprint_local_metres']
            fill={'restroom':'#b8b8b3','reception':'#95a7ab'}.get(room['kind'],'#e5ddc8')
            rectangle((a,b,c,d),fill,'#57666a')
            for row in room['fitout']['rows']:
                lo,hi=row['bounds_local_metres']
                rectangle((lo[0],lo[1],hi[0],hi[1]),'#77776f')
            if room['kind']=='restroom':
                prefix=level['id']+'_'+room['id']
                for name,lo,hi,mat in boxes:
                    if name.startswith(prefix) and mat in ('sanitary_white','sanitary_water'):
                        rectangle((lo[0],lo[1],hi[0],hi[1]),'#f4f4ee' if mat=='sanitary_white' else '#486066')
            px,py=point((a+c)/2,(b+d)/2)
            draw.text((px,py),room['label'],font=label,fill='#173442',anchor='mm',stroke_width=2,stroke_fill=fill)
            f=room['door_fraction'];side=room['door_side']
            x,y={'u_min':(a+(c-a)*f,b),'u_max':(a+(c-a)*f,d),
                 'v_min':(a,b+(d-b)*f),'v_max':(c,b+(d-b)*f)}[side]
            px,py=point(x,y)
            if side.startswith('u_'):draw.line((px-6,py,px+6,py),fill='white',width=3)
            else:draw.line((px,py-6,px,py+6),fill='white',width=3)
        rectangle(level['voids_local_metres'][0],'#b8cebc','#56755e')
        for core in stair['cores']:
            rectangle(core['enclosure']['bounds'],'#e2d3cc','#43545b',2)
        for name,lo,hi,material in boxes:
            if name.startswith(tuple('stair_'+c+'_flight' for c in ('se','sw','ne','nw'))):
                rectangle((lo[0],lo[1],hi[0],hi[1]),'#ac5147','#763d38')
        for core in stair['cores']:
            portal=core['enclosure']['portals'][i];x,y,_=portal['centre'];half=portal['width']/2
            draw.line((*point(x,y-half),*point(x,y+half)),fill='white',width=4)
            for sign in (-1,1):
                end=x+half if core['mirror_east'] else x-half
                draw.line((*point(x,y+sign*half),*point(end,y+sign*half)),fill='#252d30',width=3)
        draw.text((left,1000),'North corridor: %.2f m; reception and restrooms have dedicated fittings.' % ((next(c for c in level['circulation'] if c['id']=='north_corridor')['bounds'][2]-next(c for c in level['circulation'] if c['id']=='north_corridor')['bounds'][0])*83),font=label,fill='#193441')
    draw.text((35,1035),'Extra Studio bays use approximate subdivisions and repeated furniture; labels are not official room numbers.',font=label,fill='#43545b')
    output.parent.mkdir(parents=True,exist_ok=True)
    image.save(output)
    print(output)


if __name__=='__main__':render()
