"""Draw room and door trace overlays directly over the October 27 photographs."""
import base64
import io
import json
from pathlib import Path
from html import escape
from PIL import Image, ImageOps, ImageDraw

try:
    from .povo1_survey import source_config, PHOTO_DIR, ROOT
except ImportError:
    from povo1_survey import source_config, PHOTO_DIR, ROOT


def render(root=ROOT):
    config, alignment = source_config(root)
    out=root/'exports/povo1_survey_20261027'
    out.mkdir(parents=True,exist_ok=True)
    for floor, filename, rotation, outer in ((0,'image00019.jpeg',0,(165,388,1545,1184)),
                                             (1,'image00022.jpeg',-90,None)):
        photo=ImageOps.exif_transpose(Image.open(root/PHOTO_DIR/filename))
        if rotation: photo=photo.rotate(rotation,expand=True)
        target_width=1824 if floor else 1800
        photo=photo.resize((target_width,round(photo.height*target_width/photo.width)))
        buffer=io.BytesIO();photo.save(buffer,format='JPEG',quality=88)
        width,height=photo.size
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height+80}" viewBox="0 0 {width} {height+80}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<image width="{width}" height="{height}" href="data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"/>']
        draw=ImageDraw.Draw(photo)
        level=config['levels'][floor+1]
        profile=alignment['profiles'][floor+1]
        a,b,c,d=profile['outer']
        def point(x,y):
            if floor: return x,y
            e,f,g,h=outer
            return e+(x-a)/(c-a)*(g-e),f+(y-b)/(d-b)*(h-f)
        def box(bounds,label,color):
            x,y=point(*bounds[:2]);xx,yy=point(*bounds[2:])
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{xx-x:.1f}" height="{yy-y:.1f}" fill="none" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<text x="{(x+xx)/2:.1f}" y="{(y+yy)/2:.1f}" text-anchor="middle" fill="{color}" stroke="white" stroke-width="3" paint-order="stroke" font-family="Arial" font-weight="bold" font-size="15">{escape(label)}</text>')
            draw.rectangle((x,y,xx,yy),outline=color,width=2)
            draw.text(((x+xx)/2,(y+yy)/2),label,fill=color,stroke_width=1,stroke_fill='white')
        for room in level['rooms']:
            box(room['pixel_bounds'],room['label'],'#005fb5')
            x,y,xx,yy=room['pixel_bounds'];f=room['door_fraction']
            p={'u_min':(x,y+(yy-y)*f),'u_max':(xx,y+(yy-y)*f),
               'v_min':(x+(xx-x)*f,y),'v_max':(x+(xx-x)*f,yy)}[room['door_side']]
            px,py=point(*p)
            svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="#ff8a00" stroke="white"/>')
            draw.ellipse((px-5,py-5,px+5,py+5),fill='#ff8a00',outline='white')
        if floor:
            stairs=[(450,260,610,420),(1175,280,1320,420),(450,953,610,1100),(1175,953,1320,1100)]
            for i,bounds in enumerate(stairs):box(bounds,'stair '+str(i+1),'#a900a9')
        else:
            for feature in profile['features']:
                if 'stair' in feature['id']:box(feature['pixel_bounds'],feature['id'].replace('stair_',''),'#a900a9')
        captions=[f'Povo 1 floor {floor}; source {filename}; blue: individual room trace; orange: estimated door centre; purple: stair core.',
                  'Photograph perspective is unrectified. Floor 0 overlay compares existing trace with new photo; no exact dimensions or clearance claim.']
        for i,line in enumerate(captions):svg.append(f'<text x="20" y="{height+25+i*24}" font-family="Arial" font-size="16">{escape(line)}</text>')
        svg.append('</svg>')
        (out/f'floor_{floor}_source_overlay.svg').write_text('\n'.join(svg),encoding='utf-8')
        photo.save(out/f'floor_{floor}_source_overlay.jpg',quality=90)
    return out


if __name__=='__main__':
    print(render())
