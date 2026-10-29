"""Source-only review of the corrected stair stack; does not launch the game."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import build_geometry
except ImportError:
    from build_povo_campus import build_geometry


def render():
    _,_,boxes,levels,_=build_geometry()
    link=next(l['connection'] for l in levels if l.get('connection'));spec=link['povo2']
    im=Image.new('RGB',(1560,860),'#f6f5f0');draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',23)
    draw.text((26,18),'Povo 2: corrected internal stairs and -2 vestibule',font=title,fill='#223640')
    draw.text((26,54),'Confirmed counts and connections; metric dimensions/elevations remain provisional. Game not launched.',font=font,fill='#566874')
    for offset,floor,heading in [(30,0,'0 to +1: 2 x 13'),(540,-1,'-1 to 0: 3 x 10'),(1050,-2,'-2 to -1: 3 x 10')]:
        scale=29 if floor!=-2 else 15
        xmin,xmax,ymin,ymax=(10.5,21.2,13.6,26.8) if floor!=-2 else (7.8,36,13.3,26.8)
        def xy(x,y):return (offset+(x-xmin)*scale,170+(ymax-y)*scale)
        def rect(lo,hi,color,outline=None):
            left,right=max(xmin,lo[0]),min(xmax,hi[0])
            bottom_edge,top_edge=max(ymin,lo[1]),min(ymax,hi[1])
            if left>=right or bottom_edge>=top_edge:return
            x0,y0=xy(left,top_edge);x1,y1=xy(right,bottom_edge)
            draw.rectangle((x0,y0,x1,y1),fill=color,outline=outline)
        draw.text((offset,112),heading,font=title,fill='#223640')
        bottom={0:4,-1:.4,-2:-3.2}[floor]
        for n,lo,hi,mat in boxes:
            if not n.startswith(('p2_internal_','p2_parking_','p2_basement_retained_')):continue
            if lo[0]>=xmax or hi[0]<=xmin or lo[1]>=ymax or hi[1]<=ymin:continue
            if mat.startswith('floor_') and abs(hi[2]-bottom)<.01:rect(lo,hi,'#d5e1df')
        for n,lo,hi,mat in boxes:
            if n.startswith(f'p2_internal_{floor}_flight') and '_step_' in n:rect(lo,hi,'#aabac7','#405564')
            elif n.startswith(f'p2_internal_{floor}_turn'):rect(lo,hi,'#edc879','#8a6824')
        ports=spec['stairs']['portals']+link['stair']['portals'][:1]
        for p in ports:
            if p.get('floor',1)!=floor:continue
            xx,yy=xy(*p['centre'][:2]);draw.ellipse((xx-6,yy-6,xx+6,yy+6),fill='#b84c36')
        if floor==-2:
            for route in spec['parking']['routes']:
                draw.line([xy(*p[:2]) for p in route['points']],fill='#207c71',width=3)
            for x,y,label in [(9,13.8,'Parking'),(22,13.8,'Offices'),(31.8,13.8,'Garden -2')]:
                draw.text(xy(x,y),label,font=font,fill='#223640')
            draw.text((offset,450),'Shifted exit into a vestibule',font=font,fill='#b84c36')
            draw.text((offset,480),'Right: parking',font=font,fill='#207c71')
            draw.text((offset,507),'Left: offices and garden',font=font,fill='#207c71')
        draw.text((offset,610),'Grey: treads / Gold: turn landings',font=font,fill='#405564')
        draw.text((offset,640),'Red: floor exit',font=font,fill='#b84c36')
    draw.text((30,755),'Upper rise: 27.7 cm with retained estimated bridge height. Basement rise: 12 cm.',font=font,fill='#566874')
    draw.text((30,785),'The accepted -1 exit/corridor stays in place. Office interiors behind the new corridor facade remain closed.',font=font,fill='#566874')
    out=Path(__file__).resolve().parents[1]/'exports/povo2_layout_audit_20261028/internal_stairs_implemented.png'
    out.parent.mkdir(parents=True,exist_ok=True);im.save(out);return out


if __name__=='__main__':print(render())
