#!/usr/bin/env python3
"""Export outer scenery and aerial/eye-level reviews; never deploy or launch CS2."""
import hashlib
import json
import math
from pathlib import Path

try:
    from .povo_edges import ROOT, build
except ImportError:
    from povo_edges import ROOT, build


def export(root=ROOT):
    meshes,meta=build(root)
    out=root/'exports/povo_edges';out.mkdir(parents=True,exist_ok=True)
    try:
        from .build_povo_campus import render_obj
    except ImportError:
        from build_povo_campus import render_obj
    faces=[(m['name'],m['material'],[m['vertices'][i] for i in f],None) for m in meshes for f in m['faces']]
    # Use the campus's coplanar clipping and metre-based UV/normal writer.
    obj='mtllib povo_edges.mtl\n'+render_obj([],faces)
    (out/'povo_edges.obj').write_text(obj,encoding='utf-8')
    try:
        from .povo_exterior_materials import COLORS
    except ImportError:
        from povo_exterior_materials import COLORS
    (out/'povo_edges.mtl').write_text(''.join('newmtl exterior_'+name+'\nKd '+' '.join(f'{v/255:.5f}' for v in color)+'\nd 1\n\n' for name,color in COLORS.items()))
    meta['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('povo_edges.*')}
    (out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    return meshes,meta,out


def render(root=ROOT):
    # Keep numpy/Pillow optional for source generation and tests.
    from PIL import Image,ImageDraw
    try:
        from .render_povo_exterior import perspective,font
        from .build_povo_exterior import build as exterior_build
    except ImportError:
        from render_povo_exterior import perspective,font
        from build_povo_exterior import build as exterior_build
    meshes,meta,out=export(root);cfg=meta['config']
    im=Image.open(root/cfg['aerial']).convert('RGB').resize((1400,1400));d=ImageDraw.Draw(im,'RGBA')
    def pt(p):return ((p[0]+250)*2.8,(200-p[1])*2.8)
    for item in cfg['buildings']:
        d.polygon([pt(p) for p in item['footprint']],fill=(65,179,231,85),outline=(82,224,255,255),width=3)
        for ring in item.get('courtyards',[]):
            d.line([pt(p) for p in ring+[ring[0]]],fill=(255,240,170,255),width=3)
        d.text(pt(item['footprint'][0]),item['id'].replace('fbk_',''),font=font(16),fill='white',stroke_width=2,stroke_fill='black')
    for road in cfg['roads']:
        d.line([pt(p) for p in road['points']],fill=(255,210,78,255),width=5)
    exterior_cfg=json.loads((root/'config/povo_exterior.json').read_text())
    d.line([pt(p) for p in exterior_cfg['front_road']['points']],fill=(255,210,78,255),width=5)
    residential=exterior_cfg['residential']['footprint']
    d.line([pt(p) for p in residential+[residential[0]]],fill=(82,224,255,255),width=3)
    r=cfg['roundabout'];x,y,_=r['centre']
    for radius in (r['inner_radius'],r['outer_radius']):
        d.line([pt((x+radius*math.cos(i*math.tau/64),y+radius*math.sin(i*math.tau/64))) for i in range(65)],
               fill=(255,210,78,255),width=3)
    for land in cfg['landscape']:
        d.line([pt(p) for p in land['footprint']+[land['footprint'][0]]],fill=(142,232,105,220),width=3)
    d.rectangle((0,0,1400,85),fill=(15,30,40,230))
    d.text((25,12),'POVO / OSM-REGISTERED OUTER SCENERY',font=font(27),fill='white')
    d.text((25,49),'2024 municipal aerial | blue: FBK outlines | pale: courtyards | gold: roads | green: landscape',font=font(19),fill='white')
    im.save(out/'aerial_traces.png')
    boxes,base_meshes,_,_=exterior_build(root)
    # Existing exterior context masses provide campus orientation in this review.
    scene=[*base_meshes,*[dict(m,material=m['material'].removeprefix('exterior_')) for m in meshes]]
    cameras=[
        dict(id='junction_north',position=[65,-11,9.2],target=[105,64,12],fov=82),
        dict(id='junction_south',position=[65,-11,9.2],target=[123,-99,14],fov=82),
        dict(id='fbk_frontage',position=[73,-9,9.2],target=[105,64,12],fov=82),
        dict(id='overview',position=[-190,-260,230],target=[45,-30,0],fov=70)
    ]
    for camera in cameras:
        shot=perspective(boxes,scene,camera,width=1200,height=750)
        d=ImageDraw.Draw(shot);d.rectangle((0,0,1200,64),fill='#182d38')
        d.text((22,9),camera['id'].replace('_',' ').upper()+' / SOURCE PREVIEW',font=font(22),fill='white')
        d.text((22,37),'31 Oct 2026 - OSM footprints / LiDAR heights; retained flat grades; source preview',font=font(17),fill='#c8d8dc')
        shot.save(out/(camera['id']+'.png'))
    (out/'cameras.json').write_text(json.dumps(cameras,indent=2)+'\n')
    print(f'Exported {len(meshes)} scenery meshes, aerial trace and {len(cameras)} source views to {out}')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    if args.render:render()
    else:
        meshes,_,out=export();print(f'Exported {len(meshes)} visual meshes to {out}')
