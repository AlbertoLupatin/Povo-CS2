"""Draw a review proposal from the current assembled layout; edit no geometry."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
areas=meta['povo2']['drawio_entrance']['areas']
garden=json.loads((ROOT/'config/povo2_gardens.json').read_text())
im=Image.new('RGB',(1900,1360),'#f3f5f5');d=ImageDraw.Draw(im)
def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),n)
def text(p,s,n=22,fill='#20313b',bold=False):d.multiline_text(p,s,font=font(n,bold),fill=fill,spacing=7)
text((55,30),'EXTERIOR CONCRETE · FILL PROPOSAL',37,bold=True)
text((55,85),'Review drawing — no exterior geometry changed. Locations follow the current assembled map.',23)
text((55,122),'Amber = proposed concrete / edge closure     Blue = existing routes to keep open     Green = existing garden',21)

X0,X1,Y0,Y1=6,73,-10,32;K=21;OX,OY=60,200
def xy(x,y):return OX+(x-X0)*K,OY+(Y1-y)*K
def rect(r,fill,outline='#52616a',width=2):d.rectangle((*xy(r[0],r[3]),*xy(r[2],r[1])),fill=fill,outline=outline,width=width)
def label(s,x,y,n=18,fill='#20313b'):
    d.multiline_text(xy(x,y),s,font=font(n,True),fill=fill,anchor='mm',align='center',spacing=4)
def fill(r,letter):
    rect(r,'#f5be63','#bb6f13',3)
    label(letter,(r[0]+r[2])/2,(r[1]+r[3])/2,22)
def leader(letter,p,end):
    x,y=xy(*p);d.line([(x,y),end],fill='#a8620b',width=3)
    d.ellipse((end[0]-17,end[1]-17,end[0]+17,end[1]+17),fill='#f5be63',outline='#a8620b',width=2)
    d.text(end,letter,font=font(21,True),fill='#56350a',anchor='mm')

rect([X0,Y0,X1,Y1],'#ffffff','#aebac0')
for x in range(10,74,5):
    d.line([xy(x,Y0),xy(x,Y1)],fill='#e4e9eb',width=1)
    label(str(x),x,Y0-.7,15,'#65767f')
for y in range(-10,33,5):
    d.line([xy(X0,y),xy(X1,y)],fill='#e4e9eb',width=1)
    label(str(y),X0-1,y,15,'#65767f')

# Existing footprints are read from the final Draw.io assembly, not the legacy sketch.
rect([8.5,2,20.36,26],'#e2e4e5');label('POVO 2\nexisting offices',14.4,23,19)
for key in ('e1','e2','restricted'):
    rect(areas[key],'#e2e4e5');r=areas[key];label('closed' if key=='restricted' else key.upper(),(r[0]+r[2])/2,(r[1]+r[3])/2,12 if key=='restricted' else 18)
rect(areas['c5'],'#bcdde7');label('C5',21.8,12,17)
rect([11,18,20.5,26],'#c4cbd0');label('Main stair',15.7,22,17)
rect(areas['terrace'],'#bcdde7');label('−1 terrace  z 0.4 m',18.2,1.15,16)
for key in ('up','down'):
    r=areas[key];rect(r,'#bcdde7','#366a83',3)
    if key=='up':
        for i in range(1,20):
            yy=r[1]+(r[3]-r[1])*i/20;d.line([xy(r[0],yy),xy(r[2],yy)],fill='#71929f')
        label('UP',21.75,-2.7,16)
    else:
        for i in range(1,20):
            xx=r[0]+(r[2]-r[0])*i/20;d.line([xy(xx,r[1]),xy(xx,r[3])],fill='#71929f')
        label('DOWN',37.5,1.15,15)
rect([42.3,2,45.3,10.2],'#bcdde7','#366a83',3)
rect(garden['garden'],'#d1dfcb','#6a8460',3)
rect([42.3,8.75,45.3,10.2],'#bcdde7')
label('LOWER GARDEN\nkeep open\nz −3.2 m',48,15.5,19)
rect(garden['street_garden'],'#d1dfcb','#6a8460',2)
rect([42.3,2,45.3,10.2],'#bcdde7','#366a83',3)
label('Street garden\nz 4.0 m',48.3,6.4,17)
rect([55.5,8.75,58,28.3],'#d8dbdc');label('walk',56.75,24,15)
rect([34.5,20,55.5,28.3],'#e9ebeb');label('Existing upper courtyard',44.8,24,17)
road=meta['exterior'].get('street_end_gate',{})
# Show the configured frontage carriageway and both current footway edges.
cfg=json.loads((ROOT/'config/povo_exterior.json').read_text())['front_road']
for a,b in zip(cfg['points'],cfg['points'][1:]):
    if max(a[1],b[1])<Y0 or min(a[1],b[1])>Y1:continue
    dy=b[1]-a[1];lo=max(Y0,min(a[1],b[1]));hi=min(Y1,max(a[1],b[1]))
    points=[]
    for y,side in ((lo,-1),(hi,-1),(hi,1),(lo,1)):
        x=a[0]+(b[0]-a[0])*(y-a[1])/dy+side*cfg['width']/2;points.append(xy(x,y))
    d.polygon(points,fill='#b7bec3',outline='#71818a')
label('STREET',64.6,23,18)

# Proposal boundaries are intentionally reviewable; no change to stairs or garden levels.
soil=[31.96,2.75,35.75,8.75];rect(soil,'#b4c59d','#6a8460',2)
for a,b in [((soil[0],soil[1]),(soil[2],soil[1])),((soil[2],soil[1]),(soil[2],soil[3]))]:
    d.line([xy(*a),xy(*b)],fill='#d28b22',width=8)
leader('A',(35.75,5.7),(470,860))
fill([35.75,2,42.02,2.75],'B');leader('B',(38.7,2.4),(760,935))
fill([45.58,2,55.5,2.75],'C');leader('C',(50.5,2.4),(1110,935))
rect([56.7,-1,58,15],'#f5be63','#bb6f13',3)
leader('D',(57.35,9),(1260,700))
label('N',8,29,21);d.line([xy(8,27),xy(8,28.5)],fill='#20313b',width=3)
text((65,1125),'Local metres: east → / north ↑',19)

# A section makes the proposed vertical fill explicit instead of suggesting a new slab over the garden.
text((1510,200),'WHAT WOULD BE FILLED',24,bold=True)
items=[('A','Concrete facing on the exposed\nsoil-block sides; retain the top.'),
       ('B / C','Close the small discontinuities\nbetween existing upper surfaces.\nKeep the lower stair passage open.'),
       ('D','Close exposed side / underside\nvoids beneath the sloping street\nwalk. Top follows the current grade.')]
yy=255
for tag,description in items:
    text((1510,yy),tag,26,'#a8620b',True);text((1510,yy+37),description,19);yy+=160
text((1500,805),'D · SCHEMATIC SECTION',22,bold=True)
d.polygon([(1510,920),(1810,1010),(1810,1115),(1510,1115)],fill='#f5be63',outline='#a8620b')
d.line([(1510,920),(1810,1010)],fill='#536c7c',width=9)
d.line([(1495,1115),(1830,1115)],fill='#61765a',width=4)
text((1510,850),'Existing walking surface',18)
text((1510,1040),'Closed concrete support',17,'#694714')
text((1510,1140),'Section is schematic.\nExact fill edges require review.',18)

d.rounded_rectangle((55,1190,1840,1320),radius=12,fill='#e5edf0')
text((80,1208),'KEEP OPEN',22,'#28546d',True)
text((285,1206),'The −1 terrace, both stair flights, the lower approach and the −2 garden.',22)
text((285,1245),'This proposal closes exposed sides and unintended gaps; it does not raise the garden or redesign the approved layout.',20)
OUT.mkdir(exist_ok=True);im.save(OUT/'exterior_fill_proposal.png')
proposal=dict(status='proposal_only',source='Current assembled provenance and Draw.io bounds; screenshot 2 visual correspondence is provisional',
    A=dict(bounds=soil,action='Concrete facing on exposed vertical sides; retain top'),
    B=dict(bounds=[35.75,2,42.02,2.75],action='Proposed upper edge continuity; verify against screenshot'),
    C=dict(bounds=[45.58,2,55.5,2.75],action='Proposed upper edge continuity; keep approach open'),
    D=dict(bounds=[56.7,-1,58,15],action='Close underside/side voids following existing street-walk grade'),
    preserve=['Approved terrace and stair coordinates','Lower garden at -3.2','Existing street elevations'],geometry_changed=False)
(OUT/'exterior_fill_proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
print(OUT/'exterior_fill_proposal.png')
