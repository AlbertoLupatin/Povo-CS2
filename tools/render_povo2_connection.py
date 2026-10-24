"""Source-layout review of the connected floor-1 route (Pillow)."""
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import ROOT, build_geometry
except ImportError:
    from build_povo_campus import ROOT, build_geometry


def render():
    _s,_c,boxes,levels,stair=build_geometry()
    img=Image.new('RGB',(1240,1510),'#edf1f2');d=ImageDraw.Draw(img)
    title=ImageFont.truetype('arial.ttf',27);head=ImageFont.truetype('arial.ttf',19)
    font=ImageFont.truetype('arial.ttf',12);small=ImageFont.truetype('arial.ttf',11)
    d.text((35,25),'POVO 1 + POVO 2 / FIRST CONNECTED ROUTE',font=title,fill='#193441')
    d.text((35,68),'Two Povo 1 floors; bridge and Povo 2 arrival aligned with floor 1.',font=head,fill='#193441')
    d.text((55,115),'FLOOR 1 / Povo 1 to Povo 2',font=head,fill='#193441')
    d.text((705,115),'GROUND / A202 and A203 relocated',font=head,fill='#193441')
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
            d.text((x-50,y-3),'POVO 2 / floor-1 arrival',font=font,fill='#193441')
            x,y=pt(18.25,-18)
            d.line((x,y,x,y-210),fill='#246b81',width=3)
            d.polygon(((x,y-225),(x-7,y-209),(x+7,y-209)),fill='#246b81')
        for room in rooms:
            r=room['footprint_local_metres'];rect(r,'#e5ddc8')
            for row in room['fitout']['rows']:
                a,b=row['bounds_local_metres'];rect((a[0],a[1],b[0],b[1]),'#888a7c',None)
            a,b,c,e=r;x,y=pt((a+c)/2,(b+e)/2)
            label=room['label'].replace('Aula studio ponte','Studio ponte').replace('Studio P2 ','P2 ')
            d.text((x,y),label,font=small,fill='#193441',anchor='mm',stroke_width=1,stroke_fill='#e5ddc8')
            f=room['door_fraction'];side=room['door_side']
            x,y={'u_min':(a+(c-a)*f,b),'u_max':(a+(c-a)*f,e),'v_min':(a,b+(e-b)*f),'v_max':(c,b+(e-b)*f)}[side]
            x,y=pt(x,y)
            d.line((x-5,y,x+5,y) if side.startswith('u_') else (x,y-5,x,y+5),fill='white',width=3)
        rect(level['voids_local_metres'][0],'#b8cebc')
        for core in stair['cores']:
            rect(core['enclosure']['bounds'],'#e2d3cc')
        for name,lo,hi,_ in boxes:
            if name.startswith(tuple('stair_'+c+'_flight' for c in ('se','sw','ne','nw'))):
                rect((lo[0],lo[1],hi[0],hi[1]),'#ac5147','#763d38')
    panel(levels[1],55,165,8,42,True)
    panel(levels[0],705,165,9,-20)
    y=970
    for line in ('57 open furnished Povo 1 rooms:',
                 '27 Povo 1 ground / 30 Povo 1 floor 1',
                 'Povo 2: two arrival alcoves,',
                 'short corridor and enclosed stairs.',
                 '',
                 'A202/A203 keep their room labels',
                 'after moving to the ground corner.',
                 '',
                 'Four mirrored red stairs retained.',
                 'New signs stay fixed above doors.',
                 '',
                 'W1 is now the gray stair down.',
                 'E1 removed; end wall before W2/E2.',
                 'Lower landing closes this phase.'):
        d.text((705,y),line,font=font,fill='#193441');y+=24
    d.text((35,1455),'Photo-guided prototype: added Povo 2 dimensions, subdivisions and study labels are estimates.',font=font,fill='#43545b')
    path=ROOT/'exports/povo_campus/povo2_connection_review.png';img.save(path);print(path)

if __name__=='__main__':render()
