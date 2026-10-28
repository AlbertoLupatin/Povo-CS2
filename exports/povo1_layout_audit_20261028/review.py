from pathlib import Path
import json
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
p = json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
archive = ROOT/'data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300'
im = ImageOps.exif_transpose(Image.open(archive/'image00019.jpeg'))
im = im.resize((1800, round(im.height*1800/im.width)))
d = ImageDraw.Draw(im)
align = json.loads((ROOT/'config/povo1_plan_alignment.json').read_text())['profiles'][1]['outer']
a,b,c,e = align
def point(x,y): return 165+(x-a)/(c-a)*1380,388+(y-b)/(e-b)*796
for r in p['levels'][1]['rooms']:
    x,y=point(*r['pixel_bounds'][:2]); xx,yy=point(*r['pixel_bounds'][2:])
    d.rectangle((x,y,xx,yy),outline='#0060d0',width=3)
    d.text((x+3,y+3),r['label'],fill='#0060d0',stroke_width=1,stroke_fill='white')
im.save(OUT/'floor0_current_rooms.jpg',quality=94)
items=[(archive/f'image{n:05}.jpeg',f'27 Oct photo {n}') for n in (9,10,17,23,26,28)]
archive28=ROOT/'data/reference/povo_photos/walk_2026-10-28/wetransfer_image00001-jpeg_2026-10-28_1107'
items += [(archive28/f'image{n:05}.jpeg',f'28 Oct photo {n}') for n in (2,4,5)]
sheet=Image.new('RGB',(1800,1410),'white'); d=ImageDraw.Draw(sheet)
for i,(path,label) in enumerate(items):
    photo=ImageOps.exif_transpose(Image.open(path)); photo.thumbnail((590,430))
    x=(i%3)*600; y=(i//3)*470
    sheet.paste(photo,(x,y+25)); d.text((x+8,y+5),label,fill='black')
sheet.save(OUT/'reference_contact.jpg',quality=93)
print('Saved current floor-0 overlay and source contact sheet.')
