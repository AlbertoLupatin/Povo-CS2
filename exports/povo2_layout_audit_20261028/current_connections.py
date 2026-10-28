from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]
p=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())['povo2']
im=Image.new('RGB',(1700,1330),'#f7f8fa'); d=ImageDraw.Draw(im)
def font(n): return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
def txt(x,y,s,n=23,fill='#172b3a'): d.multiline_text((x,y),s,font=font(n),fill=fill,spacing=6)
txt(35,22,'POVO 2 — CURRENT GENERATED LAYOUT',32)
txt(35,65,'Source geometry, not a proposed correction. North is up. Heights are provisional local map metres.',21)
txt(35,115,'Floor -1 + existing outdoor yard',27)
txt(880,115,'Floor -2: parking + shared internal stairs',27)
scale=8.0
def pt(x,y,panel=0): return (55+(x+16)*scale+panel*845,170+(53-y)*scale)
def rect(r,panel,fill,label=None):
    a,b,c,e=r; x,y=pt(a,e,panel); xx,yy=pt(c,b,panel)
    d.rectangle((x,y,xx,yy),fill=fill,outline='#566975',width=2)
    if label: txt((x+xx)/2-9,(y+yy)/2-13,label,22)
colors={'room':'#eadbc5','corr':'#d6e6ed','core':'#edc9c4','yard':'#d8e7ce'}
for k in ('corridor','cibio_corridor','left_locker','left_return'): rect(p['basement'][k],0,colors['corr'])
for k,num in [('cibio_office_0','1'),('cibio_office_1','2')]: rect(p['basement'][k],0,colors['room'],num)
rect(p['stairs']['bounds'],0,colors['core'],'S')
rect(p['lift']['shaft'],0,'#dccfea','L')
rect(p['additions']['yard']['bounds'],0,colors['yard'],'Y')
for key,col in [('indoor_path','#b25912'),('outdoor_path','#953e30')]:
    path=p['additions']['yard'][key]
    d.line([pt(*q[:2]) for q in path],fill=col,width=9)
    for q in path:
        x,y=pt(*q[:2]); d.line((x-9,y,x+9,y),fill=col,width=2)
door=p['basement_placement']['portal']; x,y=pt(*door[:2]);d.ellipse((x-5,y-5,x+5,y+5),fill='#172b3a')
txt(510,240,'1 / 2: two generic rooms\nCurrently labelled CIBIO offices\n(not photo-traced labs)',20)
txt(510,340,'S: internal stair stack\nConnects 0, -1 and -2\nL: ladder shaft',20)
txt(510,445,'Corridor continues south\nto the below-bridge exit',20)
txt(510,570,'5 steps UP to yard Y\n15 more UP to street\nNo descending garden branch',20)
txt(50,765,'Y is the existing yard at z=+1.3.\nIt is NOT a separately modelled garden at floor -2.',21)
rect(p['parking']['bounds'],1,'#e1e5e9')
rect(p['stairs']['bounds'],1,colors['core'],'S')
for x,y,col in p['parking']['cars']:
    rect([x-1,y-2,x+1,y+2],1,'#899caa')
txt(1110,230,'PARKING\nz = -3.2',23)
txt(935,535,'No modelled office/garden corridor\non this floor in the current layout.',22)
txt(935,625,'The same stair core S links -2 to -1.\nThere is no separate -2 garden here.',22)
d.line((35,845,1660,845),fill='#bac5cb',width=2)
txt(35,870,'CURRENT VERTICAL CONNECTIONS — schematic, not horizontal distances',26)
def box(x,y,w,h,label,fill):
    d.rectangle((x,y,x+w,y+h),fill=fill,outline='#566975',width=2);txt(x+12,y+12,label,22)
box(40,1070,270,80,'Floor -1 corridors\nz = +0.4',colors['corr'])
box(450,1020,270,80,'Existing outdoor yard\nz = +1.3',colors['yard'])
box(870,940,275,80,'Street / entrance level\nz = +4.0','#e1e5e9')
box(40,1220,270,75,'Floor -2 parking\nz = -3.2','#e1e5e9')
d.line((310,1110,450,1060),fill='#b25912',width=4);txt(325,1020,'5 steps up',20)
d.line((720,1060,870,980),fill='#953e30',width=4);txt(735,955,'15 steps up',20)
d.line((175,1150,175,1220),fill='#953e30',width=4);txt(200,1175,'Internal stairs',20)
txt(1190,1060,'MISSING:\nshort exterior landing\n+ left stair DOWN\nto the -2 garden',23)
im.save(Path(__file__).parent/'current_minus1_minus2_connections.png')
