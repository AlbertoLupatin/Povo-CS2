"""Check curb-aligned sidewalk samples against the native model's PHYS dump."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

try:
    from .audit_povo2_compiled_floors import on_triangle
except ImportError:
    from audit_povo2_compiled_floors import on_triangle

ROOT=Path(__file__).resolve().parents[1]


def audit(physics, output):
    physics=Path(physics)
    text=physics.read_text()
    vertex_blocks=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',text,re.S)
    triangle_blocks=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',text,re.S)
    if not vertex_blocks or len(vertex_blocks)!=len(triangle_blocks):
        raise ValueError('Expected paired native PHYS vertices and triangles')
    triangles=[];units=39.37007874
    for vv,tt in zip(vertex_blocks,triangle_blocks):
        vertices=[(y/units,z/units,x/units)
                  for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        for indices in struct.iter_unpack('<III',bytes.fromhex(tt)):
            face=[vertices[i] for i in indices]
            # Only retain triangles in the frontage and bridge-road area.
            if max(p[0] for p in face)<32 or min(p[0] for p in face)>65:continue
            if max(p[1] for p in face)<-10 or min(p[1] for p in face)>22:continue
            triangles.append((face,[(min(p[k] for p in face),max(p[k] for p in face)) for k in range(3)]))
    config=json.loads((ROOT/'config/povo_exterior.json').read_text())
    samples=[]
    a,b=config['front_road']['points'][1:3]
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    for i in range(4,37):
        t=i/40
        for offset in (3.65,4.4,5.15):
            samples.append(('frontage',(
                a[0]+dx*t-dy/length*offset,
                a[1]+dy*t+dx/length*offset,
                a[2]+(b[2]-a[2])*t+.12)))
    # Independent straight walking line, including both transitions.
    for i in range(81):
        x,y=57.5,-.5+i*.25
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/length**2))
        samples.append(('frontage_transitions',(x,y,a[2]+(b[2]-a[2])*t+.12)))
    a,b=config['road']['points'][:2]
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    for i in range(1,36):
        t=i/36
        for side in (-1,1):
            offset=side*(config['road']['width']/2+.7)
            samples.append(('bus_approach',(
                a[0]+dx*t-dy/length*offset,
                a[1]+dy*t+dx/length*offset,
                a[2]+(b[2]-a[2])*t+.12)))
    missing=[]
    for label,point in samples:
        if not any(all(lo-.002<=point[k]<=hi+.002 for k,(lo,hi) in enumerate(box))
                   and on_triangle(point,face) for face,box in triangles):
            missing.append(dict(area=label,point=point))
    report=dict(status='failed' if missing else 'passed',samples=len(samples),
                missing=missing,physics_dump_sha256=hashlib.sha256(physics.read_bytes()).hexdigest(),
                scope='Native collision support at curb grade; normal walking and visual review are separate')
    Path(output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('physics',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    raise SystemExit(0 if audit(args.physics,args.output)['status']=='passed' else 1)
