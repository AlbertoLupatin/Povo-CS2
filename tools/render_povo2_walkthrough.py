"""Render the final assembled eastern approach and its terrace connections."""
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .build_povo_campus import build_geometry
from .povo_campus_finishes import write_png


def font(size,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)


def main():
    _,_,boxes,levels,_=build_geometry()
    spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
    if spec.get('drawio_entrance'):
        render_drawio(boxes,spec)
        return
    out=Path(__file__).resolve().parents[1]/'exports/povo2_walkthrough_20261029'
    out.mkdir(exist_ok=True)
    im=Image.new('RGB',(1500,1170),'#f4f6f7');draw=ImageDraw.Draw(im)
    def xy(x,y):return (60+(x+1)*35,1110-y*32)
    c5=spec['walkthrough_repairs']['c5'];c5x=(c5[0]+c5[2])/2
    for name,lo,hi,mat in boxes:
        floor=abs(hi[2]-.4)<.025 and mat.startswith('floor_')
        wall=lo[2]<1.3 and hi[2]>1.4 and mat in ('wall','window_glass','reception_glass','door_black','window_frame')
        if not (floor or wall) or not (-1<hi[0] and lo[0]<38 and -1<hi[1] and lo[1]<29):continue
        color=('#e2c59f' if mat=='floor_wood' else '#dce6e5') if floor else ('#55bdd1' if 'glass' in mat else '#424e57')
        draw.rectangle((*xy(lo[0],hi[1]),*xy(hi[0],lo[1])),fill=color)
    for d in spec['repair_doors']:
        if not d['id'].startswith(('p2_wi1_public','p2_c7_exit','p2_c5_terrace','p2_garden_exit')):continue
        lo,hi=d['bounds']
        draw.line([xy(lo[0],lo[1]),xy(hi[0],hi[1])],fill='#db871e',width=5)
    for label,point,text in [
        ('Terrace entrance',(c5x,c5[1]),(24,-.3)),
        ('1 · WI1 / wooden W spine',(20.5,9.26),(6,5)),
        ('2 · C7 / main W corridor',(20.5,16.62),(5,22.5)),
        ('3 · Sealed door',(c5x,c5[3]),(22,25.6)),
        ('C7 east door to exit corridor',(24.5,16.8),(25.5,21.3)),
        ('E1 · closed',(26.4,14),(26.4,14)),
        ('E2 · closed',(26.4,7),(26.4,7)),
        ('Stairs',(19.2,22),(12,27.3)),
        ('Outdoor exit',(34.5,11.25),(35.4,13.6)),
        ('UP to street',(34.5,5),(36.4,1.5)),
    ]:
        px,py=xy(*point);tx,ty=xy(*text)
        if point!=text:
            draw.line([(px,py),(tx,ty)],fill='#496474',width=2)
            draw.ellipse((px-5,py-5,px+5,py+5),fill='#db871e')
        bounds=draw.textbbox((tx,ty),label,font=font(21,True))
        draw.rectangle((bounds[0]-5,bounds[1]-5,bounds[2]+5,bounds[3]+5),fill='#f4f6f7')
        draw.text((tx,ty),label,font=font(21,True),fill='#203844')
    draw.line([xy(c5x,c5[1]+.8),xy(c5x,c5[3]-.8)],fill='#d4483a',width=3)
    draw.rectangle((0,0,1500,180),fill='#f4f6f7')
    draw.text((60,30),'POVO 2 −1 / EASTERN APPROACH',font=font(33,True),fill='#203844')
    draw.text((60,82),'Actual assembled geometry · blue glass · amber doors · north up',font=font(22),fill='#496474')
    draw.text((60,122),'Terrace → WI1 → C7 → sealed door. C5, its doors and the closed rooms follow plan 46.',font=font(22),fill='#496474')
    buffer=BytesIO();im.save(buffer,format='PNG');write_png(out/'eastern_approach.png',buffer.getvalue())
    render_full(boxes,spec,out)
    print(out/'eastern_approach.png')


def render_drawio(boxes,spec):
    """Draw actual generated components; never reuse the old entrance sketch."""
    out=Path(__file__).resolve().parents[1]/'exports/povo2_drawio_entrance_20261031'
    out.mkdir(exist_ok=True)
    im=Image.new('RGB',(1500,1330),'white');d=ImageDraw.Draw(im)
    left,top,k=75,140,30
    def xy(x,y):return left+(x-8)*k,top+(29-y)*k
    selected=[]
    for name,lo,hi,mat in boxes:
        if hi[0]<8 or lo[0]>44 or hi[1]<-7 or lo[1]>29:continue
        floor=(abs(hi[2]-.4)<.02 and mat.startswith('floor_'))
        tread=name.startswith(('p2_basement_drawio_up_step_','p2_basement_drawio_down_step_',
                                'p2_basement_drawio_down_midlanding','p2_basement_drawio_up_top'))
        wall=lo[2]<1.5<hi[2] and mat in ('wall','window_glass','reception_glass','door_black','door_closed','exterior_concrete')
        if floor or tread or wall:selected.append((not(floor or tread),name,lo,hi,mat))
    for wall,name,lo,hi,mat in sorted(selected):
        a,b,c,e=max(8,lo[0]),max(-7,lo[1]),min(44,hi[0]),min(29,hi[1])
        color=('#d7e9e2' if mat!='floor_wood' else '#e7c89f') if not wall else ('#5cb7cb' if 'glass' in mat else '#334c59')
        if 'drawio_up_step_' in name or 'drawio_down_step_' in name or 'drawio_down_midlanding' in name:color='#b4c1c8'
        d.rectangle((*xy(a,e),*xy(c,b)),fill=color)
    for x in range(10,45,5):d.text((xy(x,-7)[0],xy(x,-7)[1]+10),str(x),font=font(15),fill='#5b7480',anchor='mt')
    for y in range(-5,30,5):d.text((xy(8,y)[0]-10,xy(8,y)[1]),str(y),font=font(15),fill='#5b7480',anchor='rm')
    def label(text,x,y,size=19):
        d.multiline_text(xy(x,y),text,font=font(size,True),fill='#193943',anchor='mm',align='center')
    for text,x,y in [('MAIN STAIR',15.7,23),('C7',15.,16.62),('WI1',14.,9.26),('W01',15.7,12.8),
                     ('E1',27.5,14),('E2',27.5,7),('C5',21.9,12),('TERRACE',17.,1.1),('UP',21.75,-3.)]:label(text,x,y)
    for door in spec['repair_doors']:
        if door['id'].startswith(('p2_c5_terrace_','p2_wi1_public_')):
            lo,hi=door['bounds'];d.line([xy(lo[0],lo[1]),xy(hi[0],hi[1])],fill='#d28b21',width=5)
    a=spec['drawio_entrance']['areas'];label('Sealed door',27.,a['c5'][3])
    d.line([xy(23.2,a['c5'][3]),xy(24.5,a['c5'][3])],fill='#a43c3c',width=2)
    label('Down to Garden -2',37.,3.2,18)
    d.text((1210,180),'IMPLEMENTED SOURCE',font=font(19,True),fill='#193943')
    for i,text in enumerate(['C5 reaches N21.08','E1/E2 reach E31.8','UP faces C5 entrance','East arm removed','Two-flight DOWN stair']):
        d.text((1210,230+i*48),text,font=font(17),fill='#496474')
    d.text((35,22),'POVO 2 -1 / GENERATED DRAW.IO ENTRANCE',font=font(30,True),fill='#193943')
    d.text((35,76),'Drawn from the assembled source components; north up. Blue: glazing. Amber: usable doors.',font=font(19),fill='#496474')
    d.text((35,1240),'The -1 floor/wall section and relocated tread footprints are shown. Native package checks are recorded separately.',font=font(18),fill='#496474')
    im.save(out/'source_plan.png')
    print(out/'source_plan.png')


def render_full(boxes,spec,out):
    im=Image.new('RGB',(1400,1540),'#f4f6f7');draw=ImageDraw.Draw(im)
    def xy(x,y):return (65+(x+25)*19.5,1450-y*19.5)
    selected=[]
    for name,lo,hi,mat in boxes:
        floor=abs(hi[2]-.4)<.025 and mat.startswith('floor_')
        wall=lo[2]<1.3 and hi[2]>1.4 and mat in ('wall','window_glass','reception_glass','door_black','window_frame')
        if (floor or wall) and hi[0]>-25 and lo[0]<39 and hi[1]>0 and lo[1]<66:
            selected.append((floor,name,lo,hi,mat))
    for floor,name,lo,hi,mat in sorted(selected,key=lambda v:not v[0]):
        color=('#e2c59f' if mat=='floor_wood' else '#b7d5cf' if mat=='floor_terrace' else '#dce6e5') if floor else ('#55bdd1' if 'glass' in mat else '#424e57')
        draw.rectangle((*xy(lo[0],hi[1]),*xy(hi[0],lo[1])),fill=color)
    for a,b,c,d in spec['minus1_corrections']['closed_corridor_areas']:
        draw.rectangle((*xy(a+.12,d-.12),*xy(c-.12,b+.12)),fill='#dbcacb')
    for room in spec['west_offices']['rooms']:
        a,b,c,d=room['bounds'];p=xy((a+c)/2,(b+d)/2)
        draw.text(p,room['label'],anchor='mm',font=font(15,True),fill='#354b55')
    for room in next(l for l in spec['levels'] if l['floor']==-1)['rooms']:
        a,b,c,d=room['bounds'];p=xy((a+c)/2,(b+d)/2)
        draw.text(p,room['label'].replace(' ','\n',1),anchor='mm',align='center',font=font(21,True),fill='#354b55')
    for label,point in [('C7',(-8,19.1)),('WI1',(-2,9.26)),('C5',(21.8,12.4)),
                        ('STAIRS',(15.7,22)),('TERRACE',(-1.45,44)),
                        ('OUTDOOR\nEXIT',(34.5,14)),('RESTRICTED RETURN',(14,57.75))]:
        draw.text(xy(*point),label,anchor='mm',align='center',font=font(18,True),fill='#203844')
    for d in spec['repair_doors']:
        lo,hi=d['bounds'];draw.line([xy(lo[0],lo[1]),xy(hi[0],hi[1])],fill='#db871e',width=3)
    c5=spec['walkthrough_repairs']['c5'];c5x=(c5[0]+c5[2])/2
    draw.line([xy(c5x,c5[1]+.8),xy(c5x,c5[3]-.8)],fill='#d4483a',width=3)
    draw.rectangle((0,0,1400,150),fill='#f4f6f7')
    draw.text((60,25),'POVO 2 −1 / PLAYABLE LAYOUT',font=font(32,True),fill='#203844')
    draw.text((60,76),'Current source · blue glass · amber doors · green terrace · north up',font=font(21),fill='#496474')
    draw.text((60,113),'Room footprints and new exterior connections remain approximate.',font=font(21),fill='#496474')
    buffer=BytesIO();im.save(buffer,format='PNG');write_png(out/'minus1_playable_layout.png',buffer.getvalue())


if __name__=='__main__':main()
