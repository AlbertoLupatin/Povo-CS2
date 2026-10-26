"""Software render the reception offices and expanded restroom kit."""
from PIL import Image, ImageDraw

try:
    from .build_povo_campus import COLORS, ROOT
    from .povo_interior_fixtures import reception_boxes, reception_staff_mesh, restroom_boxes, office_frame
    from . import render_povo_exterior as renderer
except ImportError:
    from build_povo_campus import COLORS, ROOT
    from povo_interior_fixtures import reception_boxes, reception_staff_mesh, restroom_boxes, office_frame
    import render_povo_exterior as renderer


def render():
    output=ROOT/'exports/povo_campus/amenities';output.mkdir(exist_ok=True)
    renderer.COLORS=COLORS
    renderer.OPACITY={'reception_glass':.06}
    for kind in ('reception_povo1','reception_povo2','reception_staff_detail','restroom_male','restroom_female'):
        if kind.startswith('reception'):
            width,depth=(6,8) if kind.endswith('2') else (7.919,5.389)
            bounds=(0,0,depth,width);frame=office_frame(bounds,0,'east')
            boxes=reception_boxes('office',bounds,0,3.35,'east')
            staff=reception_staff_mesh('office',bounds,0,'east')
            def local(p):
                dx=p[0]-frame[0][0];dy=p[1]-frame[0][1]
                return (dx*frame[1][0]+dy*frame[1][1],dx*frame[2][0]+dy*frame[2][1],p[2])
            new=[]
            for name,lo,hi,mat in boxes:
                p=local(lo);q=local(hi)
                new.append((name,tuple(min(a,b) for a,b in zip(p,q)),tuple(max(a,b) for a,b in zip(p,q)),mat))
            boxes=new
            meshes=[dict(name=name,vertices=[local(p) for p in points],faces=[(0,1,2)],material=mat.removeprefix('campus_'))
                    for name,mat,points,_ in staff]
            title=('POVO 2' if kind.endswith('2') else 'POVO 1')+' / FURNISHED RECEPTION'
            subtitle='Transparent glazing, gray workstations and three staff; front receptionist seated at her computer.'
            camera=dict(position=(width*.5,-width*.75,1.85),target=(width*.5,depth*.45,1.1),fov=67)
            if kind.endswith('detail'):
                camera=dict(position=(width*.5,-.15,1.62),target=(width*.5,1.9,1.12),fov=75)
                title='FRONT RECEPTIONIST / SEATED WORKING POSE'
        else:
            width,depth=7.073,9.212
            room=dict(id='review',footprint_local_metres=(0,0,width,depth),door_side='u_max',
                      sex='female' if kind.endswith('female') else 'male')
            boxes=restroom_boxes('review',room,0,3.35);meshes=[]
            title=('WOMEN' if room['sex']=='female' else 'MEN')+' / RESTROOM'
            subtitle='Four toilet cubicles, three basins, dispensers, hand dryer, bins and storage.'
            if room['sex']=='male':subtitle+=' Two screened urinals.'
            camera=dict(position=(width*.5,depth+.2,2.6),target=(width*.5,2.3,.95),fov=73)
        im=Image.new('RGB',(1400,980),'#e9edef');draw=ImageDraw.Draw(im)
        draw.text((45,30),title,font=renderer.font(29),fill='#203d49')
        draw.text((45,80),subtitle,font=renderer.font(17),fill='#4f646b')
        im.paste(renderer.perspective(boxes,meshes,camera,width=1400,height=800),(0,120))
        draw.text((45,944),'Generated geometry preview / final materials and lighting are checked in CS2.',font=renderer.font(16),fill='#4f646b')
        path=output/(kind+'.png');im.save(path);print(path,flush=True)


if __name__=='__main__':render()
