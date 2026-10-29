"""Review the actual basement render/collision boxes, not a parallel diagram."""
from PIL import Image,ImageDraw,ImageFont
try:
    from .build_povo_campus import ROOT,build_geometry,collision_boxes
except ImportError:
    from build_povo_campus import ROOT,build_geometry,collision_boxes


def render():
    _,_,boxes,levels,_=build_geometry();physics=collision_boxes(boxes)
    spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
    im=Image.new('RGB',(1800,900),'#f3f4ef');draw=ImageDraw.Draw(im)
    font=lambda size,bold=False:ImageFont.truetype('arialbd.ttf' if bold else 'arial.ttf',size)
    draw.text((36,25),'POVO 2  /  BASEMENT REBUILD',font=font(30,True),fill='#213f49')
    draw.text((36,72),'Plans drawn from the same final geometry used for the model and collision. North is up.',font=font(19),fill='#536b70')
    for floor,left in ((-1,36),(-2,925)):
        draw.rounded_rectangle((left,120,left+840,795),12,fill='white',outline='#cbd5d3',width=2)
        draw.text((left+22,138),f'LEVEL {floor}',font=font(24,True),fill='#213f49')
        north=max(r['bounds'][3] for r in next(l for l in spec['levels'] if l['floor']==-1)['rooms'])
        xmin,xmax,ymin,ymax=(-16,58,0,north+3) if floor==-1 else (-28,58,-16,29)
        scale=min(790/(xmax-xmin),550/(ymax-ymin));top=207;z=.4 if floor==-1 else -3.2
        def xy(x,y):return left+25+(x-xmin)*scale,top+(ymax-y)*scale
        def rect(lo,hi,color,outline=None):
            a,b,c,d=max(xmin,lo[0]),max(ymin,lo[1]),min(xmax,hi[0]),min(ymax,hi[1])
            if a<c and b<d:draw.rectangle((*xy(a,d),*xy(c,b)),fill=color,outline=outline)
        # Exact floor rectangles, including the formerly perforated parking.
        for n,lo,hi,m in boxes:
            if m.startswith('floor_') and abs(hi[2]-z)<.02 and n.startswith('p2_'):
                rect(lo,hi,'#d2e1df' if m!='floor_yard_grass' else '#c3d5b6')
        if floor==-1:
            for a,b,c,d in spec['minus1_corrections']['closed_corridor_areas']:
                rect((a,b,z),(c,d,z),'#eadcdc')
        for n,lo,hi,m in physics:
            if lo[2]<z+1.6 and hi[2]>z+.4 and n.startswith(('p2_','exterior_')):
                if floor==-1:
                    regions=next(l['areas'] for l in spec['basement_rebuild']['levels'] if l['floor']==-1)
                    regions=regions+[spec['stairs']['bounds']]+[spec['gardens'][k] for k in ('passage','up_stair','down_stair','garden')]
                    for a,b,c,d in regions:
                        rect((max(lo[0],a-.12),max(lo[1],b-.12),lo[2]),
                             (min(hi[0],c+.12),min(hi[1],d+.12),hi[2]),'#344c57')
                else:rect(lo,hi,'#344c57')
        for n,lo,hi,m in boxes:
            if (n.startswith(f'p2_internal_{floor}_flight') and '_step_' in n) or (
                    floor==-1 and n.startswith(('p2_gardens_up_step_','p2_gardens_down_step_'))):
                rect(lo,hi,'#d9bf91','#8c7859')
        for route in spec['basement_rebuild']['routes']+spec['parking']['routes']:
            if abs(route['points'][0][2]-z)>.01:continue
            draw.line([xy(*p[:2]) for p in route['points']],fill='#25857d',width=3)
        def label(x,y,text):
            draw.multiline_text(xy(x,y),text,font=font(15,True),anchor='mm',align='center',fill='#213f49',stroke_width=2,stroke_fill='white')
        if floor==-1:
            for i,room in enumerate(next(l for l in spec['levels'] if l['floor']==-1)['rooms']):
                a,b,c,d=room['bounds'];label((a+c)/2,(b+d)/2,'ROOM '+str(i+1))
            label(16,23,'STAIRS')
            label(12,15.7,'CORRIDOR');label(34.5,31,'EXIT\nCORRIDOR');label(47,17,'GARDEN -2\nBELOW')
            correction=spec['minus1_corrections'];spine=correction['spine_sections'][1]
            label(8,(spine[1]+spine[3])/2,f"~{correction['gap_metres']:g} m gap\n~{correction['gap_clear_width_metres']:g} m wide")
            x,y,z=correction['upper_junction_door']['centre']
            px,py=xy(x,y);draw.ellipse((px-5,py-5,px+5,py+5),outline='#b4642f',width=2)
            draw.line([xy(x,y),xy(5,y+4)],fill='#b4642f',width=2);label(10,y+5,'LOCKED DOOR')
            x,y,z=correction['lower_junction_door']['centre'];px,py=xy(x,y)
            draw.ellipse((px-5,py-5,px+5,py+5),outline='#b4642f',width=2)
            draw.line([xy(x,y),xy(43,y+5)],fill='#b4642f',width=2);label(47,y+7,'LOCKED DOOR')
            label(47,43,'CLOSED L\nNO ACCESS')
            label(42,3,'UP TO STREET')
            draw.line([xy(34.5,5),xy(42,4)],fill='#8c7859',width=2)
            label(47,6,'DOWN TO -2')
        else:
            label(-8,1,'PARKING');label(16,23,'STAIRS');label(15,16,'VESTIBULE')
            label(25,21,'OFFICES');label(48,16,'GARDEN -2')
        draw.text((left+23,754),'Teal: checked walking routes   /   Gold: stair treads',font=font(16),fill='#536b70')
    draw.text((36,828),'User corrections: ~30 m estimated gap, half-width corridor, permanently closed L. Geometry review; not an engine screenshot.',font=font(18),fill='#536b70')
    out=ROOT/'exports/povo_campus/povo2_basements_rebuilt.png';im.save(out);return out


if __name__=='__main__':print(render())
