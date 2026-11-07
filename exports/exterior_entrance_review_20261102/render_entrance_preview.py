"""Source geometry comparison of the entrance; native review remains separate."""
from pathlib import Path
import json,pickle,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_povo_campus import build_geometry,COLORS
from tools import render_povo_exterior as render
render.COLORS.update(COLORS);render.OPACITY.update(window_glass=.25,reception_glass=.25)
old,oldlevels=pickle.load(open(ROOT/'build/exterior-entrance-20261102/baseline.pkl','rb'))
_,_,new,levels,_=build_geometry()
pickle.dump((new,levels),open(ROOT/'build/exterior-entrance-20261102/current.pkl','wb'))
def local(boxes):return [b for b in boxes if b[1][0]<40 and b[2][0]>10 and b[1][1]<40 and b[2][1]>8 and b[1][2]<8 and b[2][2]>3.7 and '_clip_' not in b[0]]
sheet=Image.new('RGB',(1800,1130),'#f3f5f5');draw=ImageDraw.Draw(sheet)
f=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',25)
for row,camera in enumerate([dict(position=[28,24,5.6256],target=[20.5,22,6.1],fov=85),dict(position=[25,17,5.6256],target=[20.5,20,6.1],fov=90)]):
    for col,(label,boxes) in enumerate([('BEFORE',old),('AFTER · source preview',new)]):
        image=render.perspective(local(boxes),[],camera,900,510)
        sheet.paste(image,(900*col,50+row*560));draw.text((25+900*col,12+row*560),label,font=f,fill='#20313b')
target=Path(__file__).with_name('entrance_before_after.png');sheet.save(target)
print(target)
