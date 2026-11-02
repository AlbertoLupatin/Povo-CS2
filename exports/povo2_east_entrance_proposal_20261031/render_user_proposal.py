from pathlib import Path
import xml.etree.ElementTree as ET
import base64,zlib,urllib.parse,json,hashlib,re
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[2]
source=root/'data/reference/user_feedback/2026-10-31/east_entrance_edited.drawio'
doc=ET.fromstring(source.read_text(encoding='utf-8'));page=doc.find('diagram')
model=page[0] if len(page) else ET.fromstring(urllib.parse.unquote(zlib.decompress(base64.b64decode(page.text),-15).decode()))
cells={c.get('id'):c for c in model.iter('mxCell')}
def geometry(id):
    g=cells[id].find('mxGeometry');x,y,w,h=[float(g.get(k,'0')) for k in ('x','y','width','height')]
    return [8+x/30,32-(y+h)/30,8+(x+w)/30,32-y/30]
areas={key:geometry(id) for key,id in dict(core='c3',core_west_room='c4',c7_west='c5',c7='c6',wi1='c7',w01='c8',w07='c9',w08='c10',w09='c11',w10='c12',w02_north='c13',w02_south='c14',up_stair='c17',garden_stair='c18',terrace='c19',e1='c25',e2='c26',restricted='c27',c5='c23').items()}
doors={key:geometry(id) for key,id in dict(terrace_door='c29',wi1_door='c30',sealed='c31',e2_shut='c33',stair_door='c36').items()}
out=root/'exports/povo2_east_entrance_proposal_20261031';out.mkdir(exist_ok=True)
W,H=1470,1390;left,top,k=90,150,32
bounds=(8,-7,43,28)
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if b else 'segoeui.ttf'),n)
def xy(x,y):return left+(x-8)*k,top+(28-y)*k
def rect(r,fill,outline='#334d5b',width=3):d.rectangle((*xy(r[0],r[3]),*xy(r[2],r[1])),fill=fill,outline=outline,width=width)
def label(s,x,y,n=18,color='#173440',bold=True):
    d.multiline_text(xy(x,y),s,font=font(n,bold),fill=color,anchor='mm',align='center',spacing=5)
d.text((38,25),'POVO 2 -1 / YOUR CORRECTED ENTRANCE LAYOUT',font=font(29,True),fill='#173440')
d.text((38,73),'Source: east_entrance_edited.drawio (30 October). Shape positions follow your drawing.',font=font(19),fill='#496474')
d.text((38,105),'North up. Coordinates are the drawing\'s fitted metres, not independently measured dimensions.',font=font(17),fill='#496474')
rect([8,-7,43,28],'#fbfcfd','#bac9d0',1)
for x in range(10,44,5):
    d.line([xy(x,-7),xy(x,28)],fill='#e2e8eb');d.text((xy(x,-7)[0],xy(x,-7)[1]+12),str(x),font=font(16),fill='#647c88',anchor='mt')
for y in range(-5,29,5):
    d.line([xy(8,y),xy(43,y)],fill='#e2e8eb');d.text((xy(8,y)[0]-12,xy(8,y)[1]),str(y),font=font(16),fill='#647c88',anchor='rm')
colors=dict(core='#f0ce9e',core_west_room='#eee9e1',c7_west='#dcebe5',c7='#dcebe5',c5='#dcebe5',wi1='#e6c79f',restricted='#e8d5d5',terrace='#beddd6',up_stair='#bbc6cc',garden_stair='#bbc6cc',e1='#e8e2da',e2='#e8e2da')
for key in ('core_west_room','c7_west','c7','wi1','w01','w07','w08','w09','w10','w02_north','w02_south','terrace','up_stair','garden_stair','e1','e2','restricted','core','c5'):
    rect(areas[key],colors.get(key,'#ead3b6'))
# The user's touching corridor rectangles describe continuous circulation.
for key in ('c7','wi1'):
    r=areas[key];a=areas['c5'];d.line([xy(r[2],r[1]+.07),xy(r[2],r[3]-.07)],fill=colors[key],width=7)
    if key=='c7':d.line([xy(a[0],r[1]+.07),xy(a[0],r[3]-.07)],fill=colors['c5'],width=7)
for key,r in doors.items():rect(r,'#b43f3a' if key in ('sealed','e2_shut') else '#d79225',None)
for key in ('up_stair','garden_stair'):
    a,b,c,e=areas[key]
    if key=='up_stair':
        for i in range(1,13):d.line([xy(a,b+(e-b)*i/13),xy(c,b+(e-b)*i/13)],fill='#6d808b',width=1)
    else:
        for i in range(1,21):d.line([xy(a+(c-a)*i/21,b),xy(a+(c-a)*i/21,e)],fill='#6d808b',width=1)
for key,title in dict(core='MAIN STAIR',wi1='WI1 / wooden corridor',c7='C7',c5='C5',w01='W01',w07='W07',w08='W08',w09='W09',w10='W10',e1='E1\nclosed room',e2='E2\nclosed room',restricted='Restricted\nbeyond\ndoor',terrace='TERRACE').items():
    a,b,c,e=areas[key];label(title,(a+c)/2,(b+e)/2,14 if key=='restricted' else 17 if key=='c5' else 19)
label('UP',21.75,-2.9,19)
label('to street',24.9,-3.1,18,'#496474')
label('Metal stair to Garden -2',37.1,3.3,17,'#496474')
label('SEALED DOOR',27.7,21.1,19,'#a03030')
a,b,c,e=doors['sealed'];d.line([xy((a+c)/2,e+.15),xy(24.4,21.1)],fill='#a03030',width=2)
label('Terrace entrance',27.6,-1.7,18,'#95601b')
a,b,c,e=doors['terrace_door'];d.line([xy((a+c)/2,b),xy(25.7,-1.4)],fill='#b37b23',width=2)
# The deleted arm/link are intentionally absent; notes identify the change.
notes=[('C5 extends north', 'Sealed door at N ~21.1;\ncurrent build stops at N 18.'),
       ('E1 / E2 extend east', 'East facade at E 31.8;\ncurrent build stops at E 29.7.'),
       ('UP stair relocated', 'Directly south of C5,\nacross the terrace.'),
       ('Extra connectors removed', 'Your drawing has no added\neastward C7 arm\nor terrace detour.')]
nx=1235
for i,(title,body) in enumerate(notes):
    y=185+i*205
    d.rounded_rectangle((nx-20,y-15,1450,y+155),radius=10,fill='#eff5f7')
    d.multiline_text((nx,y),title,font=font(17,True),fill='#173440',spacing=4)
    d.multiline_text((nx,y+49),body,font=font(15),fill='#496474',spacing=7)
d.text((38,1325),'Proposal copied from your Draw.io geometry. The installed map has not been changed by this review.',font=font(18),fill='#496474')
im.save(out/'user_layout_proposal.png')
(out/'proposal.json').write_text(json.dumps(dict(source=str(source.relative_to(root)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),authority='User says this Draw.io layout is correct',areas=areas,openings=doors,notes='Geometry derived directly from Draw.io; no configuration or installed package changed'),indent=2)+'\n')
(out/'README.md').write_text('# East entrance proposal from the user drawing\n\nSource: `data/reference/user_feedback/2026-10-31/east_entrance_edited.drawio`, copied byte-for-byte from Downloads. The user identifies this drawing as correct.\n\nThe PNG follows its shape coordinates; `proposal.json` records the fitted campus coordinates. This supersedes model-derived assumptions for the local arrangement. No game source/configuration or compiled map is changed by this proposal.\n\nDifferences from the current compiled map: C5 extends to approximately N21.1; E1/E2 extend to E31.8; the UP stair lies directly south of C5 across the terrace; the extra eastern C7 arm and provisional terrace connector are absent. Room labels and metric axes are drawing references, not a new physical survey.\n',encoding='utf-8')
print(out/'user_layout_proposal.png')
