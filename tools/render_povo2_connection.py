"""Source-layout review of the three Povo 1 floors and bridge route (Pillow)."""
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import ROOT, build_geometry
except ImportError:
    from build_povo_campus import ROOT, build_geometry


def render():
    _s,_c,boxes,levels,stair=build_geometry()
    img=Image.new('RGB',(1900,1510),'#edf1f2');d=ImageDraw.Draw(img)
    title=ImageFont.truetype('arial.ttf',27);head=ImageFont.truetype('arial.ttf',19)
    font=ImageFont.truetype('arial.ttf',12);small=ImageFont.truetype('arial.ttf',11)
    d.text((35,25),'POVO 1 + POVO 2 / THREE FLOORS + BRIDGE',font=title,fill='#193441')
    d.text((35,68),'Povo 1 -1: A1xx / 0: A2xx / +1: offices and bridge. Elevations 4 / 7.6 / 11.2 m.',font=head,fill='#193441')
    for x,label in [(55,'POVO 1 -1 / A1xx'),(685,'POVO 1 0 / A2xx'),(1315,'POVO 1 +1 / OFFICES + BRIDGE')]:
        d.text((x,115),label,font=head,fill='#193441')
    def panel(level,left,top,scale,north,connection=False):
        def pt(x,y):return left+(x+23)*scale,top+(north-y)*scale
        def rect(r,fill,line='#64767b',width=1):
            a,b,c,e=r;d.rectangle((*pt(a,e),*pt(c,b)),fill=fill,outline=line,width=width)
        rect((-23,-103,24,-20),'#d7e9ed')
        rooms=[*level['rooms'],*level.get('connection',{}).get('rooms',[])]
        if connection:
            link=level['connection']
            for r in link['povo2_floor_parts']:rect(r,'#d7e9ed')
            rect(link['stair']['bounds'],'#c7ccca')
            rect(link['bridge'],'#b9d5e3','#31566d',2)
            rect(link['povo1_corridor'],'#b9d5e3')
            x,y=pt(18.25,-5)
            d.text((x+35,y),'30 m bridge',font=font,fill='#31566d')
            x,y=pt(7,29)
            d.text((x-50,y-3),'POVO 2 / +1 bridge arrival',font=font,fill='#193441')
            x,y=pt(18.25,-18)
            d.line((x,y,x,y-210),fill='#246b81',width=3)
            d.polygon(((x,y-225),(x-7,y-209),(x+7,y-209)),fill='#246b81')
        for room in rooms:
            r=room['footprint_local_metres'];rect(r,'#e5ddc8')
            for row in (room['fitout'].get('rows',[]) if isinstance(room.get('fitout'),dict) else []):
                a,b=row['bounds_local_metres'];rect((a[0],a[1],b[0],b[1]),'#888a7c',None)
            a,b,c,e=r;x,y=pt((a+c)/2,(b+e)/2)
            label=room['label'].replace('Aula studio ponte','Studio ponte').replace('Studio P2 ','P2 ')
            d.text((x,y),label,font=small,fill='#193441',anchor='mm',stroke_width=1,stroke_fill='#e5ddc8')
            f=room['door_fraction'];side=room['door_side']
            x,y={'u_min':(a+(c-a)*f,b),'u_max':(a+(c-a)*f,e),'v_min':(a,b+(e-b)*f),'v_max':(c,b+(e-b)*f)}[side]
            x,y=pt(x,y)
            d.line((x-5,y,x+5,y) if side.startswith('u_') else (x,y-5,x,y+5),fill='white',width=3)
        for void in level.get('voids_local_metres',[]):rect(void,'#b8cebc')
        for core in stair['cores']:
            rect(core['enclosure']['bounds'],'#e2d3cc')
        for name,lo,hi,_ in boxes:
            if name.startswith(tuple('stair_'+c+'_flight' for c in ('se','sw','ne','nw'))):
                rect((lo[0],lo[1],hi[0],hi[1]),'#ac5147','#763d38')
    for floor,left in [(-1,55),(0,685),(1,1315)]:
        level=next(l for l in levels if l.get('user_floor')==floor)
        panel(level,left,165,4.8,42,bool(level.get('connection')))
    d.text((35,1120),'Visible source room labels retained on their surveyed floors. Offices have no classroom seat rows.',font=head,fill='#193441')
    d.text((35,1160),'Bridge connects the upper Povo 1 office floor at 11.2 m. Source XY registration remains provisional.',font=head,fill='#193441')
    d.text((35,1455),'Photo-guided source review; dimensions and fine untraced details remain estimates.',font=font,fill='#43545b')
    path=ROOT/'exports/povo_campus/povo2_connection_review.png';img.save(path);print(path)

if __name__=='__main__':render()
