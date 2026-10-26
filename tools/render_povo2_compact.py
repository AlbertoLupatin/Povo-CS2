"""Focused upper/lower source review for the compact Povo 2 arrival."""
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import ROOT, build_geometry
except ImportError:
    from build_povo_campus import ROOT, build_geometry


def render():
    _,_,boxes,levels,_=build_geometry()
    link=levels[1]['connection'];stair=link['stair']
    img=Image.new('RGB',(1260,1040),'#edf1f2');d=ImageDraw.Draw(img)
    title=ImageFont.truetype('arial.ttf',28);head=ImageFont.truetype('arial.ttf',20)
    font=ImageFont.truetype('arial.ttf',16);small=ImageFont.truetype('arial.ttf',13)
    d.text((35,25),'POVO 2 / COMPACT BRIDGE ARRIVAL',font=title,fill='#193441')
    d.text((35,70),'Two arrival alcoves retained. W1 becomes enclosed gray stairs down.',font=head,fill='#193441')
    for lower,left in ((False,55),(True,675)):
        top=150;scale=27
        def p(x,y):return left+(x-6)*scale,top+(27-y)*scale
        def rect(r,fill,outline='#4e6066',width=1):
            a,b,c,e=r;d.rectangle((*p(a,e),*p(c,b)),fill=fill,outline=outline,width=width)
        def text(x,y,s,anchor='mm',f=font,color='#193441'):
            d.text(p(x,y),s,font=f,fill=color,anchor=anchor)
        d.text((left,115),'GROUND / CLOSED LOWER LANDING' if lower else 'FLOOR 1 / FROM BRIDGE',font=head,fill='#193441')
        if lower:
            rect((7,14,20,26),'#d7e9ed')
        else:
            for r in link['povo2_floor_parts']:rect(r,'#d7e9ed')
            rect((16.5,6,20,10),'#b9d5e3')
            rect((20.15,14.15,25,26),'#edf1f2',None)
            text(22.5,21,'E1 removed',f=small,color='#667980')
            text(12,27,'W2 / E2 and rear corridor removed',anchor='lm',f=small,color='#667980')
        rect(stair['bounds'],'#d0d3ce')
        if not lower:rect((9.7,18.5,14.2,22.72),'#889da3')
        for name,lo,hi,mat in boxes:
            if 'p2_stair_' not in name:continue
            if '_step_' in name and (lower or '_upper_' in name):
                rect((lo[0],lo[1],hi[0],hi[1]),'#a7aaa4','#6e7774')
            if '_middle_landing' in name:rect((lo[0],lo[1],hi[0],hi[1]),'#b4b8b0')
        # The enclosing walls are drawn after the treads, with the live doorway.
        for r in ((6.9,14,7.1,26),(7,13.9,16.5,14.1),(7,25.9,16.5,26.1)):
            rect(r,'#4e6066')
        n=22 if lower else 20
        for r in ((16.4,14,16.6,n-.825),(16.4,n+.825,16.6,26)):
            rect(r,'#4e6066')
        for y in (n-.825,n+.825):rect((16.55,y-.025,17.35,y+.025),'#242b2f',width=2)
        rect((19.9,14,20.1,26),'#4e6066')
        rect((16.5,25.9,20,26.1),'#4e6066')
        text(18.25,24.8,'End wall',f=small)
        text(11.7,24.3,'Gray enclosed stairs',f=small)
        text(18.25,n-1.5,'Open black doors',f=small)
        if lower:
            text(18.25,17,'Closed lower\nlanding',f=small)
            route=[(15.2,22),(14.5,21.72),(11.5,21.72),(10.45,21.72),(10.45,19.5)]
        else:
            rect((8,11,12,11.65),'#b49a77');text(10.5,12.8,'Bench',f=small)
            rect((22,11,23.05,11.85),'#9babb0');text(22.5,12.8,'Printer',f=small)
            text(18.25,7.5,'Bridge',f=small)
            route=[(18.25,7.8),(18.25,20),(15.2,20),(14.6,19.5),(11.5,19.5)]
        pts=[p(*v) for v in route];d.line(pts,fill='#1c7890',width=4)
        x,y=pts[-1];d.polygon(((x-9,y),(x+5,y-6),(x+5,y+6)),fill='#1c7890')
    d.text((35,850),'20 risers / 18 cm rise / 30 cm treads / two 2 m-wide flights',font=head,fill='#193441')
    for i,line in enumerate(('North is up. New end wall is exactly at the former W2/E2 boundary.',
                             'The bridge remains level with Povo 1 and Povo 2 floor 1.',
                             'Ground and basement planimetry is separate source work pending stair alignment.',
                             'Prototype dimensions are estimates; this image is a source plan, not a game capture.')):
        d.text((35,895+i*28),line,font=font,fill='#43545b')
    output=ROOT/'exports/povo_campus/povo2_compact_review.png';img.save(output);print(output)


if __name__=='__main__':render()
