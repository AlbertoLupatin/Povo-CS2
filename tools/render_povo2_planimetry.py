"""Render ground, basement and parking plans without deploying the map."""
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

try:
    from .build_povo_campus import ROOT, render_obj
    from .povo2_planimetry import build
except ImportError:
    from build_povo_campus import ROOT, render_obj
    from povo2_planimetry import build


def render():
    boxes,spec=build()
    out=ROOT/'exports/povo2_planimetry';out.mkdir(parents=True,exist_ok=True)
    img=Image.new('RGB',(2480,830),'#eef1ed');d=ImageDraw.Draw(img)
    def font(size,bold=False):return ImageFont.truetype('arialbd.ttf' if bold else 'arial.ttf',size)
    d.text((45,30),'POVO 2  /  GAME PLANIMETRY',font=font(34,True),fill='#183641')
    d.text((45,80),'Entrance-relative layout from your photos. Dimensions and storey heights are provisional.',font=font(20),fill='#46616a')
    panels=[(spec['levels'][2],45,145),(spec['levels'][1],865,145),
            (spec['levels'][0],1685,145)]
    for level,left,top in panels:
        d.rounded_rectangle((left-10,top-8,left+765,top+610),12,fill='#ffffff',outline='#cbd4d2',width=2)
        d.text((left+15,top+10),level['label'].upper(),font=font(23,True),fill='#183641')
        scale=8.3 if level['floor']==0 else 13.7
        ox=left+(160 if level['floor']==0 else 70);oy=top+75
        north=67 if level['floor']==-1 else 43
        def pt(x,y):return ox+(x-3)*scale,oy+(north-y)*scale
        def rect(r,fill,outline='#839494',width=1):
            a,b,c,e=r;d.rectangle((*pt(a,e),*pt(c,b)),fill=fill,outline=outline,width=width)
        def text(x,y,label,size=14,fill='#183641'):
            d.multiline_text(pt(x,y),label,font=font(size),fill=fill,anchor='mm',align='center',spacing=3)
        def arrow(points):
            ps=[pt(*p) for p in points];d.line(ps,fill='#217d91',width=4)
            x,y=ps[-1];a,b=ps[-2];dx=x-a;dy=y-b;l=(dx*dx+dy*dy)**.5
            if l:d.polygon(((x,y),(x-13*dx/l+6*dy/l,y-13*dy/l-6*dx/l),
                            (x-13*dx/l-6*dy/l,y-13*dy/l+6*dx/l)),fill='#217d91')
        if level['floor']==0:
            rect(spec['footprint'],'#e0e3dd')
            rect(spec['ground']['outside_landing'],'#cee5e8')
            rect((21,32,25,38),'#f4f4ef')
            rect((21,38,25,41.8),'#e0e3dd')
            for room in spec['ground']['rooms']:
                a,b,c,e=room['bounds'];rect(room['bounds'],'#eee7d8','#334f5b',2)
                text((a+c)/2,(b+e)/2,room['label']+'\nempty',14)
                rect((a+1.4,e-.35,c-1.4,e-.1),'#2e5b4c',None)
                y=room['door_y'];rect((a-.15,y-.7,a+.15,y+.7),'#ffffff',None)
                arrow([(a-1.1,y),(a+1.1,y)])
            for r in level['table_bounds']:rect(r,'#bda27f','#8e8979')
            text(4,7,'TABLES\nalong wall',13)
            rect(spec['ground']['reception'],'#a3b9be','#45636c',2)
            text(25,29,'RECEPTION\nsealed glass',11)
            d.line((*pt(21,32),*pt(21,42)),fill='#334f5b',width=3)
            rect((20.85,38.7,21.15,40.3),'white',None)
            rect((10,40.9,22.5,41.7),'#cdb795',None)
            text(13,35,'Left corridor',13)
            arrow([(4,28),(17.8,28)]);text(12,30.8,'ENTRANCE',14)
            arrow([(16,29.5),(16,39.5),(25,39.5)])
            arrow([(17,24),(17,spec['ground']['right_corridor'][1]+1)])
            text(8,22,'RIGHT',12);text(8,34,'LEFT',12)
        elif level['floor']==-1:
            for r in spec['basement'].values():rect(r,'#e0e3dd','#334f5b',2)
            rect((21.6,44,21.9,49),'#87a94b',None)
            rect((21.6,37,22,42.5),'#cdb795',None)
            text(12,45,'Long corridor\nStair block aligned\nwith corridor start',14)
            text(29,59.6,'Right turn\nat the far end',13)
            arrow([(25,39.5),(23.25,39.5),(23.25,63),(35,63)])
            d.line((*pt(25.05,38.7),*pt(25.05,40.3)),fill='#232b30',width=5)
        else:
            rect(spec['parking']['bounds'],'#909b9e','#334f5b',2)
            for y in (10.5,32):
                for i in range(12):rect((8+i*2.8,y,8.07+i*2.8,y+5.2),'#e6e4d0',None)
            for x,y,mat in spec['parking']['cars']:
                rect((x-.9,y-2.05,x+.9,y+2.05),{'car_blue':'#365979','car_red':'#974f4b','car_silver':'#d1d5d4'}[mat],'#43545d')
            for x in (10,20,40):
                for y in (19,31):rect((x-.3,y-.3,x+.3,y+.3),'#e0e3dd','#43545d')
            arrow([(25,39.5),(23,39.5),(23,25),(37,25)])
            text(26,22,'CLEAR DRIVE AISLE',15,fill='#f5f5e7')
        # Shared switchback, with portals opening west from full landings.
        a,b,c,e=spec['stairs']['bounds'];rect((a,b,c,e),'#e2d5c2','#334f5b',2)
        for x0 in (a,c-2.5):
            for i in range(11):
                y=34.6+i*.3;d.line((*pt(x0,y),*pt(x0+2.5,y)),fill='#89918d',width=1)
        rect((a-.15,38.7,a+.15,40.3),'white',None)
        if level['floor']==-1:
            for y in (38.7,40.3):
                d.line((*pt(24.2,y),*pt(25,y)),fill='#232b30',width=4)
            text(34,43.4,'Black stair door',13)
        text(28.2,39.7,'STAIRS',9 if level['floor']==0 else 12)
        text(28.2,33.2,'turn',9 if level['floor']==0 else 11)
        desc={0:'Tables fill half the hall; B111-B114 start at the entrance. Boards moved to the opposite wall.',
              -1:'Exit the stair door and turn right to reach the short corridor at the end.',
              -2:'Generic covered parking: rubberized grey asphalt, columns and five cars.'}[level['floor']]
        d.text((left+15,top+565),desc,font=font(13),fill='#46616a')
        # Scale bar and north arrow for an unambiguous reading of left/right.
        x,y=pt(35,9 if level['floor']!=-1 else 33)
        length=5*scale if level['floor'] in (0,-1) else 75
        d.line((x,y,x+length,y),fill='#183641',width=3);d.text((x+length/2-10,y+5),'5 m',font=font(11),fill='#183641')
        x,y=pt(44,39);d.line((x,y+25,x,y-10),fill='#183641',width=2);d.text((x-5,y-28),'N',font=font(13),fill='#183641')
    d.text((45,790),'SOURCE DRAFT  /  Ground, -1 and -2 only. First-floor work is handled separately. Dimensions remain provisional.',font=font(18),fill='#46616a')
    img.save(out/'review.png')
    subset=[b for b in boxes if b[0].startswith(('p2_','academic_first_link_p2','academic_first_link_bridge','academic_first_room_p2_'))]
    (out/'povo2_planimetry.obj').write_text(render_obj(subset,[]),encoding='utf-8')
    record=dict(spec=spec,visual_boxes=len(subset),source_sha256=hashlib.sha256((ROOT/'config/povo2_planimetry.json').read_bytes()).hexdigest(),
                displayed_floors=[0,-1,-2],
                runtime_status='Standalone draft, not compiled or deployed. First-floor work is excluded from this review.')
    (out/'provenance.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(out/'review.png')


if __name__=='__main__':render()
