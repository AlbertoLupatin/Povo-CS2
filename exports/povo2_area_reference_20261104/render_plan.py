"""Draw the reference-review plan from the final assembled approved area bounds."""
import html,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
g=json.loads((OUT/'approved-area-bounds.json').read_text())['gardens']
cfg=json.loads((ROOT/'config/povo_exterior.json').read_text())
image=Image.new('RGB',(1460,1040),'#f8fafc');draw=ImageDraw.Draw(image)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1460" height="1040" viewBox="0 0 1460 1040">',
     '<rect width="1460" height="1040" fill="#f8fafc"/>']
font_path='C:/Windows/Fonts/segoeui.ttf'
def label(x,y,text,size=20,color='#172a3a'):
    draw.text((x,y),text,font=ImageFont.truetype(font_path,size),fill=color)
    svg.append(f'<text x="{x}" y="{y+size}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" fill="{color}">{html.escape(text)}</text>')
def line(points,color,width=2):
    draw.line(points,fill=color,width=int(width))
    svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}"/>')
def polygon(points,fill,stroke='#596977',width=2):
    draw.polygon(points,fill=fill);draw.line(points+[points[0]],fill=stroke,width=width)
    svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
def pt(x,y):return (80+(x-8)*15,160+(32-y)*15)
def rect(bounds,fill,stroke='#596977',width=2):
    a,b,c,d=bounds;polygon([pt(a,b),pt(c,b),pt(c,d),pt(a,d)],fill,stroke,width)
def tag(x,y,text,color='#172a3a'):label(*pt(x,y),text,20,color)

label(70,32,'Povo 2 roadside area: what to fill, and what to keep open',30)
label(70,80,'Reference interpretation from photos + municipal orthophoto + RoanS77 shaders-mod',20)
label(70,111,'Plan uses the current approved source coordinates. Coloured treatments are proposals.',18,'#526575')
rect([8,-10,68,32],'#eef1f4','#c9d2da')
for x in range(10,69,5):
    line([pt(x,-10),pt(x,32)],'#dce3e9',1);label(pt(x,-10)[0]-10,810,str(x),14,'#596977')
for y in range(-10,33,5):
    line([pt(8,y),pt(68,y)],'#dce3e9',1);label(39,pt(8,y)[1]-9,str(y),14,'#596977')
# Existing roads and the recently repaired campus-side sidewalk.
line([pt(62,-10),pt(62,0),pt(64.38,15),pt(64.64,21.97),pt(65.01,32)],'#9ba4ae',105)
line([pt(12,-5),pt(22,-5),pt(32,-5),pt(50,-5),pt(62,-5)],'#9ba4ae',90)
line([pt(62,-10),pt(62,0),pt(64.38,15),pt(65.01,32)],'#f8fafc',2)
polygon([pt(56.7,0),pt(58.5,0),pt(60.92,15.55),pt(61.5,32),pt(56.7,32)],'#d3d6db')
# Final assembled layout, not the superseded 28 October stair locations.
rect(g['entrance_courtyard'],'#dbe4ed')
rect(g['garden'],'#b8dcae','#38683a',3)
rect(g['passage'],'#dbe4ed','#415268',3)
for key in ('up_stair','down_stair','down_landing'):
    rect(g[key],'#ffdda0','#8b642c',3)
    a,b,c,d=g[key]
    if key!='down_landing':
        for i in range(1,10):
            if key=='up_stair':line([pt(a,b+(d-b)*i/10),pt(c,b+(d-b)*i/10)],'#a57a39',1)
            else:line([pt(a+(c-a)*i/10,b),pt(a+(c-a)*i/10,d)],'#a57a39',1)
# Proposed bank/retaining treatment: detailed route clearances are cut out later.
rect([35.75,2.75,56.7,8.75],'#f7d4a2','#b77b28',3)
line([pt(56.7,0),pt(56.7,20)],'#b77b28',9)
line([pt(34.5,20),pt(58,20)],'#6689aa',6)
# Source confirms an old paving remnant floating above this bank.
for m in json.loads((OUT/'approved-area-bounds.json').read_text())['legacy_meshes']:
    a,b=m['bounds'];r=[a[0],a[1],b[0],b[1]]
    rect(r,'#f6b8b8','#b63838',3)
    line([pt(r[0],r[1]),pt(r[2],r[3])],'#b63838',3)
    line([pt(r[0],r[3]),pt(r[2],r[1])],'#b63838',3)
# Lower route is an explicit protected void through/along proposed backing.
for key in ('down','garden','office_exit'):
    route=g['routes'].get(key,[])
    if route:
        line([pt(p[0],p[1]) for p in route],'#ffffff',10)
        line([pt(p[0],p[1]) for p in route],'#266699',5)
tag(39,16,'KEEP OPEN')
tag(39,14,'Garden / lightwell')
tag(39,12,'existing -2 level')
tag(39,6.7,'B')
tag(35.4,25,'C: terrace edge')
tag(25,-4,'BUS')
tag(18.5,-9,'UP')
tag(31.8,-.4,'DOWN')
tag(9.2,3.8,'Approved -1 terrace')
line([pt(56.7,12),pt(65,12)],'#b77b28',2);tag(65,13.7,'A')
line([pt(55.7,4),pt(66,1)],'#b63838',2);tag(65.7,.7,'D','#b63838')
line([pt(11,27),pt(11,31)],'#172a3a',3);tag(10.5,31.8,'N')

x=1030
for y,title,body,color in [
    (170,'A  Road-edge backing',['Close exposed vertical faces.','Top follows the repaired slope.','Retain lower-route clearance.'],'#b77b28'),
    (310,'B  Ground / planting',['Re-form the upper bank with','paving, grass and low shrubs.','Keep the blue lower route open.'],'#b77b28'),
    (450,'C  Terrace / podium edge',['Flat terrace stays flat.','Close its outer facade below;','use glazing only where evidenced.'],'#6689aa'),
    (590,'D  Remove old remnant',['Legacy sloped paving remains','at z 6.2-7.42 m above this area.','Remove/trim it before adding fill.'],'#b63838'),
    (730,'Green  Open lower garden',['Retain the approved footprint,','stairs, terrace and exits.','No raised slab across this void.'],'#38683a')]:
    label(x,y,title,21,color)
    for i,text in enumerate(body):label(x,y+37+i*28,text,17)
label(80,860,'Blue: protected lower walking route. Orange: proposed edge/bank treatment, not a solid-fill mask.',19)
label(80,899,'Evidence: P010-P012, user photos 44-45, municipal 2024 orthophoto; branch 97769b5 (shaders-mod).',18)
label(80,936,'Photo/branch levels differ from this approved layout: transfer the construction method, not their 1.25 scale.',18)
label(80,975,'This review changes no map geometry or installed package. See README.md for the source comparison and next steps.',17,'#526575')
image.save(OUT/'fill_review_plan.png')
(OUT/'fill_review_plan.svg').write_text('\n'.join(svg+['</svg>']),encoding='utf-8')
print('Wrote fill_review_plan.png and editable SVG')
