"""Print the restored full -1 plan to matching PNG and SVG drawings."""
from collections import Counter
from html import escape
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.build_povo_campus import ROOT


def render(layout, out):
    floor=next(f for f in layout['floors'] if f['f']==-1)
    office=layout['west_offices_context']
    rs=floor['slabs']+[office['bounds']]
    xmin=min(r[0] for r in rs);xmax=max(r[2] for r in rs)
    ymin=min(r[1] for r in rs);ymax=max(r[3] for r in rs)
    scale=22;left=95;top=205
    width=math.ceil((xmax-xmin)*scale+2*left)
    height=math.ceil((ymax-ymin)*scale+top+235)
    im=Image.new('RGB',(width,height),'white');d=ImageDraw.Draw(im)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="white"/>']
    def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',size)
    def xy(x,y):return left+(x-xmin)*scale,top+(ymax-y)*scale
    def rect(r,fill,outline=None,stroke=1,dashed=False):
        x,y=xy(r[0],r[3]);w=(r[2]-r[0])*scale;h=(r[3]-r[1])*scale
        d.rectangle((x,y,x+w,y+h),fill=fill)
        if outline:
            if dashed:
                for start,end in [((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))]:
                    length=math.dist(start,end)
                    for n in range(0,math.ceil(length),14):
                        a=n/length;b=min(n+7,length)/length
                        p=tuple(start[i]+(end[i]-start[i])*a for i in (0,1));q=tuple(start[i]+(end[i]-start[i])*b for i in (0,1))
                        d.line((p,q),fill=outline,width=stroke)
            else:d.rectangle((x,y,x+w,y+h),outline=outline,width=stroke)
        svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{outline or "none"}" stroke-width="{stroke}"'+(' stroke-dasharray="7 7"' if dashed else '')+'/>')
    def text(x,y,t,size=20,bold=False,fill='#233b46',anchor='la'):
        lines=t.split('\n');lineheight=size*1.2
        if anchor=='mm':
            base=y-(len(lines)-1)*lineheight/2
            for i,s in enumerate(lines):
                d.text((x,base+i*lineheight),s,font=font(size,bold),fill=fill,anchor='mm')
                svg.append(f'<text x="{x:.2f}" y="{base+i*lineheight:.2f}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}" text-anchor="middle" dominant-baseline="central">{escape(s)}</text>')
        else:
            for i,s in enumerate(lines):
                d.text((x,y+i*lineheight),s,font=font(size,bold),fill=fill,anchor='la')
                svg.append(f'<text x="{x:.2f}" y="{y+i*lineheight+size*.85:.2f}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}">{escape(s)}</text>')
    def line(p,q,fill='#344957',width=2):
        d.line((p,q),fill=fill,width=width)
        svg.append(f'<path d="M{p[0]:.2f},{p[1]:.2f} L{q[0]:.2f},{q[1]:.2f}" stroke="{fill}" stroke-width="{width}"/>')
    text(65,30,'POVO 2  /  FLOOR −1',38,True)
    built=layout.get('west_offices')
    text(65,83,'Full-plan arrangement preserved — West Offices added from planimetry' if built else 'Full-plan corridor arrangement restored — before the west-office rearrangement',25)
    text(65,122,f'{len(layout["rooms"])} room outlines · 4 stair cores · north up · all dimensions estimated',20,fill='#5d6d74')
    key=[('#dcebef','Labs / other rooms'),('#e7dbef','Office row'),('#dcebdc','Main corridors'),('#efcea0','Stair cores')]
    xx=65
    for col,label in key:
        d.rectangle((xx,163,xx+18,181),fill=col,outline='#8a999e')
        svg.append(f'<rect x="{xx}" y="163" width="18" height="18" fill="{col}" stroke="#8a999e"/>')
        text(xx+28,158,label,19);xx+=340
    # This block is a plan-edge context outline, not a new public corridor.
    rect(office['bounds'],'#f6f0f8','#9778a7',2,True)
    for r in floor['slabs']:rect(r,'#eff2f2')
    for r in layout['corridors']:rect(r['bounds'],'#dcebdc')
    if built:
        for c in built['corridors']:rect(c['bounds'],'#f2e8d6')
    counts=Counter();codes={}
    for room in layout['rooms']:
        kind=room['kind'];prefix={'laboratory':'L','office':'O','sanitary':'WC','lift_lobby':'LL'}.get(kind,'S')
        counts[prefix]+=1;codes[room['id']]=room['label'] if room['id'].startswith('west_W') else prefix+str(counts[prefix]).zfill(2)
        color={'office':'#e7dbef','sanitary':'#e3e8db','lift_lobby':'#e1e3e7'}.get(kind,'#dcebef')
        rect(room['bounds'],color)
        if room.get('excluded_for_c7_bypass'):rect(room['excluded_for_c7_bypass'],'#dcebdc')
    for c in layout['cores']:rect(c['bounds'],'#efcea0')
    for r in floor['walls']:rect(r[:4],'#344957')
    for r in floor['glazing']:rect(r[:4],'#709ba4')
    for room in layout['rooms']:
        r=room['bounds'];x,y=xy((r[0]+r[2])/2,(r[1]+r[3])/2)
        code=codes[room['id']]
        if room['id']=='annotated_lab_e':code='ROOM 1\nDoor position ?'
        elif room['id']=='annotated_lab_w':code='ROOM 2'
        text(x,y,code,18 if room['id'].startswith('annotated') else 16,True,anchor='mm')
        for opening in [room['door'],*room.get('secondary_doors',[])]:
            if not opening:continue
            p,q=opening['points']
            if opening['status'].startswith('estimated'):
                start,end=xy(*p),xy(*q);length=math.dist(start,end)
                for step in range(0,math.ceil(length),9):
                    u=step/length;v=min(step+5,length)/length
                    line(tuple(start[i]+(end[i]-start[i])*u for i in (0,1)),tuple(start[i]+(end[i]-start[i])*v for i in (0,1)),'#b5762b',4)
            else:line(xy(*p),xy(*q),'#328b83',4)
    for i,c in enumerate(layout['cores']):
        r=c['bounds'];text(*xy((r[0]+r[2])/2,(r[1]+r[3])/2),'MAIN\nSTAIR CORE' if i==1 else 'STAIR\nCORE '+str(i+1),19,True,anchor='mm')
    for i,c in enumerate(layout['corridors'][:8],1):
        r=c['bounds'];name='C'+str(i)
        if i==7:name+='  /  WEST MAIN CORRIDOR'
        text(*xy((r[0]+r[2])/2,(r[1]+r[3])/2),name,19,True,fill='#4c6954',anchor='mm')
    for r in layout['voids']:
        text(*xy((r[0]+r[2])/2,(r[1]+r[3])/2),'CENTRAL VOID',26,True,fill='#7d878c',anchor='mm')
    if built:
        for c in built['corridors']:
            r=c['bounds'];text(*xy((r[0]+r[2])/2,(r[1]+r[3])/2),c['id'],19,True,fill='#775387',anchor='mm')
        p,q=built['entrance']['points'];line(xy(*p),xy(*q),'#328b83',5)
    else:
        r=office['bounds'];text(*xy((r[0]+r[2])/2,(r[1]+r[3])/2),
            'WEST OFFICES\nPhotographed corridor is INTERNAL\nExact internal route / partitions unresolved',23,True,fill='#775387',anchor='mm')
    # Preserve emergency-exit marks as source references, not access claims.
    for e in layout['exits']:
        x,y=xy(*e['campus_point']);points=[]
        for j in range(10):
            ang=-math.pi/2+j*math.pi/5;r=8 if j%2==0 else 3.5
            points.append((x+math.cos(ang)*r,y+math.sin(ang)*r))
        d.polygon(points,fill='#b85c4f');svg.append('<polygon points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in points)+'" fill="#b85c4f"/>')
    y=height-173
    text(65,y,'West Offices built south of C7; C8 now ends at C7, and C7 passes south of the main core to C5.' if built else 'Photos describe internal West Offices circulation; they do not relocate the main corridors.',21,True)
    text(65,y+35,'Research wings remain restricted. Plan door / exit symbols do not indicate public access.',20)
    text(65,y+68,'L = laboratory   O = office row   W = new West rooms   WC = toilets   LL = lift lobby   C / WI = corridors' if built else 'L = laboratory   O = office row   S = service / other   WC = toilets   LL = lift lobby   C = corridor',19)
    text(65,y+100,'Drawing references, not official room numbers. Blue fronts = glazing; amber door marks = estimated positions.' if built else 'Codes are drawing references, not official room numbers. Dashed West Offices boundary is partial / provisional.',18,fill='#66777f')
    # A short scale bar and north arrow use the drawing's actual geometry.
    x=width-300;y=height-36;line((x,y),(x+scale*10,y),'#233b46',3);text(x+scale*5,y-18,'10 m',16,anchor='mm')
    arrowx=width-58;arrowy=250;line((arrowx,arrowy+65),(arrowx,arrowy+15),'#233b46',3)
    line((arrowx,arrowy+15),(arrowx-8,arrowy+30),'#233b46',3);line((arrowx,arrowy+15),(arrowx+8,arrowy+30),'#233b46',3)
    text(arrowx,arrowy,'N',19,True,anchor='mm')
    svg.append('</svg>')
    out.mkdir(parents=True,exist_ok=True)
    im.save(out/'minus1_full_plan_restored.png')
    (out/'minus1_full_plan_restored.svg').write_text('\n'.join(svg),encoding='utf-8')
    (out/'minus1_full_plan_room_key.json').write_text(json.dumps(codes,indent=2)+'\n',encoding='utf-8')
    if built:
        # An enlarged detail is cut from the exact full-plan drawing, so it
        # cannot drift from the main SVG's geometry.
        r=built['footprint'];p=xy(r[0]-1,27);q=xy(27,r[1]-1)
        crop=(max(0,int(p[0])),max(0,int(p[1])),min(width,int(q[0])),min(height-200,int(q[1])))
        piece=im.crop(crop);piece=piece.resize((piece.width*2,piece.height*2),Image.Resampling.LANCZOS)
        detail=Image.new('RGB',(piece.width+60,piece.height+210),'white');detail.paste(piece,(30,110));dd=ImageDraw.Draw(detail)
        dd.text((30,22),'POVO 2 −1 / WEST OFFICES',font=font(30,True),fill='#233b46')
        dd.text((30,64),'Internal passages WI1–WI4 (WI4 joins the spine to C7); C8 now ends at C7.',font=font(23),fill='#536773')
        dd.text((30,detail.height-65),'W01–W23 are drawing references (W03 retired: now WI4). Glazed fronts in blue; approximate door positions in amber.',font=font(22),fill='#536773')
        detail.save(out/'west_offices_detail.png')
        cw,ch=crop[2]-crop[0],crop[3]-crop[1]
        content='\n'.join(svg[1:-1])
        detail_svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{ch+100}" viewBox="0 0 {cw} {ch+100}"><rect width="100%" height="100%" fill="white"/><text x="15" y="30" font-family="Arial" font-size="22" fill="#233b46">Povo 2 −1 / West Offices</text><svg x="0" y="65" width="{cw}" height="{ch}" viewBox="{crop[0]} {crop[1]} {cw} {ch}">{content}</svg></svg>'
        (out/'west_offices_detail.svg').write_text(detail_svg,encoding='utf-8')
    return out/'minus1_full_plan_restored.png'


if __name__=='__main__':
    out=ROOT/'exports/povo2_minus1_layout_20261029'
    layout=json.loads((out/'layout.json').read_text(encoding='utf-8'))
    print(render(layout,out))
