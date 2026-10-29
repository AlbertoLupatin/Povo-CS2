"""Render the generated Povo 2 garden surfaces and audited route centrelines."""
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import ROOT, build_geometry
except ImportError:
    from build_povo_campus import ROOT, build_geometry


def render():
    _, _, boxes, levels, _ = build_geometry()
    spec = levels[-1]['connection']['povo2']['gardens']
    image = Image.new('RGB', (1500, 1100), '#edf1f2')
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype('arial.ttf', 30)
    font = ImageFont.truetype('arial.ttf', 20)
    small = ImageFont.truetype('arial.ttf', 16)
    draw.text((40, 25), 'POVO 2 / BELOW-BRIDGE EXIT AND GARDENS', font=title, fill='#193441')
    draw.text((40, 72), 'Generated surfaces and audited routes. Dimensions and registration remain provisional.', font=font, fill='#43545b')
    scale = 30
    def pt(x, y):
        return 125 + (x-26)*scale, 135 + (29-y)*scale
    palette = {'floor_p2_tile':'#bac2c2', 'exterior_paving':'#d8d5cc',
               'floor_yard_grass':'#8eab83', 'floor_grating':'#8d969a'}
    surfaces = sorted((b for b in boxes if b[0].startswith(('p2_gardens_', 'p2_basement_gardens_'))
                       and b[3] in palette), key=lambda b:b[2][2])
    for name, lo, hi, mat in surfaces:
        if 'ceiling' in name or 'office_garden_approach' in name:
            continue
        if lo[1]>=29:continue
        draw.rectangle((*pt(lo[0],min(hi[1],29)), *pt(hi[0],lo[1])), fill=palette[mat], outline='#6c7a7e')
    for key in ('entrance_courtyard',):
        a,b,c,d=spec[key]
        draw.rectangle((*pt(a,d),*pt(c,b)), outline='#6c7a7e', width=3)
    colors={'passage':'#275b84','up':'#9b4b30','down':'#785293','garden':'#386a45'}
    for key,path in spec['routes'].items():
        if key in ('indoor','office_exit'):continue  # Far turn / separate -2 doorway.
        draw.line([pt(*p[:2]) for p in path], fill=colors[key], width=4)
        for p in (path[0],path[-1]):
            x,y=pt(*p[:2]);draw.ellipse((x-4,y-4,x+4,y+4),fill=colors[key])
    labels=[(30,21,'Inside -1: straight corridor'),(30,27.5,'Left turn beyond this view'),
            (36.5,9.2,'Level -1'),(34.5,5.75,'UP'),(42.375,10,'DOWN'),(47,16,'Garden -2'),
            (47,5.5,'Street garden'),(45,24,'Existing entrance courtyard'),
            (58.8,18,'Road'),(58.8,7,'Sloped sidewalk')]
    for x,y,label in labels:
        draw.text(pt(x,y),label,font=small,fill='#193441',anchor='mm')
    door_x, door_y = pt(*spec['exit_door'])
    a,b,c,d=spec['indoor_corridor']
    draw.line((pt(a,b),pt(c,b)),fill='#c52e2e',width=8)
    draw.ellipse((door_x-17,door_y-17,door_x+17,door_y+17),outline='#c52e2e',width=4)
    draw.rounded_rectangle((45,745,320,835),radius=10,fill='white',outline='#c52e2e',width=3)
    draw.text((62,760),'EXIT DOOR -1',font=font,fill='#a51d1d')
    draw.text((62,794),'Inside above; UP below',font=small,fill='#193441')
    draw.line((300,745,door_x-3,door_y+22),fill='#c52e2e',width=4)
    draw.polygon(((door_x,door_y+17),(door_x-15,door_y+35),(door_x+4,door_y+40)),fill='#c52e2e')
    draw.text((40, 990), 'Blue: -1 passage   /   Brown: up to exterior paving   /   Purple: down to -2   /   Green: lower garden', font=font, fill='#193441')
    draw.text((40, 1035), 'Diagram colours explain routes; user sketch annotation colours are not game materials. North is up.', font=small, fill='#43545b')
    target=ROOT/'exports/povo_campus/povo2_gardens_implemented.png'
    image.save(target)
    print(target)
    return target


if __name__ == '__main__':
    render()
