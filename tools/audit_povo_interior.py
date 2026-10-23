#!/usr/bin/env python3
"""Conservative horizontal clearance audit of the exported interior box mesh.

This uses a configurable standing envelope, not CS2 physics or navigation.
It checks each storey separately; stair/vertical traversal remains unvalidated.
"""

import argparse
import base64
from collections import deque
import hashlib
from html import escape
import json
import math
from pathlib import Path
import re
import struct
import zlib

try:
    from .build_povo_interior import local_point, subtract_rectangles, level_layout
except ImportError:
    from build_povo_interior import local_point, subtract_rectangles, level_layout


ROOT=Path(__file__).resolve().parents[1]
MAX_CELLS=2_000_000


def read_box_mesh(path):
    vertices=[];objects=[];current=None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        parts=line.split()
        if not parts:continue
        if parts[0]=='v':vertices.append(tuple(map(float,parts[1:4])))
        elif parts[0]=='o':
            current={'name':parts[1],'indices':set(),'faces':0,'material':None};objects.append(current)
        elif parts[0]=='usemtl' and current is not None:current['material']=parts[1]
        elif parts[0]=='f':
            if current is None or len(parts)!=4:raise ValueError('Expected named triangle objects')
            for ref in parts[1:]:
                index=int(ref.split('/')[0])
                if not 1<=index<=len(vertices):raise ValueError('Invalid OBJ vertex index')
                current['indices'].add(index-1)
            current['faces']+=1
    boxes=[]
    for obj in objects:
        if len(obj['indices'])!=8 or obj['faces']!=12 or obj['material'] is None:
            raise ValueError('Clearance audit currently supports the generated eight-vertex box components only')
        points=[vertices[i] for i in obj['indices']]
        lo=tuple(min(p[axis] for p in points) for axis in range(3))
        hi=tuple(max(p[axis] for p in points) for axis in range(3))
        if any(not math.isfinite(v) for p in points for v in p) or any(a>=b for a,b in zip(lo,hi)) or any(
            any(not math.isclose(p[axis],lo[axis],abs_tol=1e-8) and not math.isclose(p[axis],hi[axis],abs_tol=1e-8) for axis in range(3)) for p in points):
            raise ValueError('Expected finite axis-aligned closed boxes')
        boxes.append((obj['name'],lo,hi,obj['material']))
    if not boxes:raise ValueError('No box mesh found')
    return boxes


def audit_level(boxes, level, stations, *, cell=.1, width=.85, height=1.9):
    if any(not math.isfinite(v) or v<=0 for v in (cell,width,height)):
        raise ValueError('Cell size and standing envelope must be finite and positive')
    if cell>width/2:raise ValueError('Cell size must be at most half the standing width')
    if not stations:raise ValueError('Need at least one audit station')
    floor_z=level['floor_elevation_local']
    floors=[b for b in boxes if b[0].startswith(level['id']+'_') and b[3].startswith('floor_') and abs(b[2][2]-floor_z)<=.02]
    if not floors:raise ValueError('No support floor for level '+level['id'])
    outer=(min(b[1][0] for b in floors),min(b[1][1] for b in floors),max(b[2][0] for b in floors),max(b[2][1] for b in floors))
    nx=math.ceil((outer[2]-outer[0])/cell);ny=math.ceil((outer[3]-outer[1])/cell)
    if nx*ny>MAX_CELLS:raise ValueError('Audit grid exceeds cell budget; use a larger cell size')
    free=bytearray(nx*ny);half=width/2

    def paint(rect,value):
        left=max(0,math.ceil((rect[0]-outer[0])/cell-.5-1e-9))
        right=min(nx,math.floor((rect[2]-outer[0])/cell-.5+1e-9)+1)
        bottom=max(0,math.ceil((rect[1]-outer[1])/cell-.5-1e-9))
        top=min(ny,math.floor((rect[3]-outer[1])/cell-.5+1e-9)+1)
        if left>=right or bottom>=top:return
        row=bytes([value])*(right-left)
        for y in range(bottom,top):free[y*nx+left:y*nx+right]=row

    paint((outer[0]+half,outer[1]+half,outer[2]-half,outer[3]-half),1)
    support=[(b[1][0],b[1][1],b[2][0],b[2][1]) for b in floors]
    missing=list(subtract_rectangles(outer,support))
    for rect in missing:paint((rect[0]-half,rect[1]-half,rect[2]+half,rect[3]+half),0)
    foot=max(b[2][2] for b in floors)
    obstacles=[b for b in boxes if not b[3].startswith('floor_') and b[2][2]>foot+.001 and b[1][2]<foot+height]
    for _name,lo,hi,_material in obstacles:
        paint((lo[0]-half,lo[1]-half,hi[0]+half,hi[1]+half),0)

    def index_for(point):
        x=math.floor((point[0]-outer[0])/cell);y=math.floor((point[1]-outer[1])/cell)
        return y*nx+x if 0<=x<nx and 0<=y<ny else None

    nodes=[(station,index_for(station['point'])) for station in stations]
    start=nodes[0][1]
    visited=bytearray(nx*ny)
    queue=deque()
    if start is not None and free[start]:visited[start]=1;queue.append(start)
    while queue:
        current=queue.popleft();x=current%nx;y=current//nx
        for neighbor in ((current-1 if x else -1),(current+1 if x+1<nx else -1),
                         (current-nx if y else -1),(current+nx if y+1<ny else -1)):
            if neighbor>=0 and free[neighbor] and not visited[neighbor]:
                visited[neighbor]=1;queue.append(neighbor)
    checks=[]
    for station,index in nodes:
        clear=index is not None and bool(free[index])
        checks.append({'id':station['id'],'point_local_metres':station['point'],'has_clearance':clear,
                       'reachable_from_entrance':clear and bool(visited[index])})
    return {'id':level['id'],'status':'passed' if all(c['reachable_from_entrance'] for c in checks) else 'failed',
            'floor_elevation_local':floor_z,'standing_width_metres':width,'standing_height_metres':height,
            'cell_metres':cell,'grid_dimensions':[nx,ny],'grid_bounds_local':outer,
            'walkable_cells':sum(free),'reachable_cells':sum(visited),'stations':checks,
            'vertical_traversal':'not checked; stair flights are absent'},free,visited


def map_png(report, free, visited):
    nx,ny=report['grid_dimensions']
    rows=[]
    for y in range(ny-1,-1,-1):
        row=bytearray()
        for x in range(nx):
            i=y*nx+x
            color=(104,174,174) if visited[i] else (219,164,77) if free[i] else (49,66,75)
            row.extend(color)
        rows.append(b'\0'+row)
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',nx,ny,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b'')


def run_audit(config_path,asset_dir,output,*,root=ROOT,cell=.1,width=.85,height=1.9):
    config_path,asset_dir,output,root=map(Path,(config_path,asset_dir,output,root))
    if output.resolve()==asset_dir.resolve() or output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('Audit output must be a separate directory from source study assets')
    config=json.loads(config_path.read_text(encoding='utf-8'))
    alignment=json.loads((root/config['alignment']).read_text(encoding='utf-8'))
    campus=json.loads((root/config['campus_config']).read_text(encoding='utf-8'))
    origin=campus['origin']
    provenance=json.loads((asset_dir/'provenance.json').read_text(encoding='utf-8'))
    if any(not re.fullmatch(r'[a-z][a-z0-9_]*',level['id']) for level in provenance['levels']):
        raise ValueError('Invalid level ID in study provenance')
    for role,file in (('configuration',config_path),('alignment',root/config['alignment']),('campus',root/config['campus_config'])):
        if hashlib.sha256(file.read_bytes()).hexdigest()!=provenance['inputs'][role]['sha256']:
            raise ValueError('Study source changed; rebuild the interior study before auditing')
    if 'photo_manifest' in provenance['inputs']:
        record=provenance['inputs']['photo_manifest']
        if hashlib.sha256((root/record['file']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Photo manifest changed; rebuild the interior study before auditing')
    for record in provenance.get('photo_sources',[]):
        if hashlib.sha256((root/record['file']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Photo source changed; rebuild the interior study before auditing')
    mesh=asset_dir/'povo1_interior_study.obj'
    if hashlib.sha256(mesh.read_bytes()).hexdigest()!=provenance['artifacts'][mesh.name]['sha256']:
        raise ValueError('Study OBJ differs from its recorded artifact hash')
    boxes=read_box_mesh(mesh)
    results=[];maps={}
    for level in provenance['levels']:
        specification=next(l for l in config['levels'] if l['id']==level['id'])
        _court,circulation,rooms=level_layout(specification,alignment)
        profile=next(p for p in alignment['profiles'] if p['id']==level['id'])
        u=(profile['entry'][0]-profile['outer'][0])/(profile['outer'][2]-profile['outer'][0])
        v=1-.8/(alignment['geographic_bounds'][2]-alignment['geographic_bounds'][0])
        if not specification['external_entrance']:
            x,y=specification['audit_start_pixels'];a,b,c,d=profile['outer']
            u,v=(x-a)/(c-a),(y-b)/(d-b)
        stations=[{'id':'entrance' if specification['external_entrance'] else 'landing_approach','point':local_point(u,v,alignment['geographic_bounds'],origin)}]
        for corridor in circulation:
            a,b,c,d=corridor['bounds']
            stations.append({'id':corridor['id'],'point':local_point((a+c)/2,(b+d)/2,alignment['geographic_bounds'],origin)})
        for room in rooms:
            exported=next(r for r in level['rooms'] if r['id']==room['id'])
            if isinstance(exported.get('fitout'),dict):
                for i,point in enumerate(exported['fitout']['audit_points_local_metres']):
                    stations.append({'id':room['id']+f'_side_aisle_{i+1}','point':point})
                continue
            a,b,c,d=room['bounds']
            stations.append({'id':room['id'],'point':local_point((a+c)/2,(b+d)/2,alignment['geographic_bounds'],origin)})
        report,free,visited=audit_level(boxes,{'id':level['id'],'floor_elevation_local':level['floor_elevation_metres']-origin[2]},stations,
                                       cell=cell,width=width,height=height)
        results.append(report);maps[level['id']+'.png']=map_png(report,free,visited)
    result={'format_version':1,'status':'passed' if all(r['status']=='passed' for r in results) else 'failed',
            'scope':'Horizontal clearance through the exported axis-aligned box mesh, using a configurable standing envelope',
            'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'levels':results,
            'limitations':['Envelope dimensions are audit assumptions, not a claim about CS2 player physics.',
                           'Grid sampling is conservative for rectangular supports and expanded box obstacles.',
                           'No diagonal movement, jumps, stairs, vertical routes or engine collision/nav are validated.',
                           'Empty-room centres and both furnished-room side aisles are checked; real engine collision is not.',
                           'Upper floor starts at an assumed landing approach; no exterior entry or link between floors is proven.']}
    names=[*maps,'report.json','review.svg']
    if any((output/name).is_symlink() or (output/name).is_dir() for name in names):
        raise ValueError('An audit output filename is occupied by a symlink or directory')
    output.mkdir(parents=True,exist_ok=True)
    for name,data in maps.items():(output/name).write_bytes(data)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="1100">',
         '<rect width="1200" height="1100" fill="#edf1f2"/>',
         '<g font-family="DejaVu Sans, sans-serif" fill="#193441">',
         '<text x="40" y="55" font-size="28" font-weight="bold">POVO 1 / EXPORTED MESH CLEARANCE AUDIT</text>',
         f'<text x="40" y="90" font-size="17">Envelope {width:g} m wide / {height:g} m high; {cell:g} m grid. Horizontal connections only.</text>']
    for i,report in enumerate(results):
        x=80+i*580
        encoded=base64.b64encode(maps[report['id']+'.png']).decode('ascii')
        svg.extend([f'<text x="{x}" y="135" font-size="20">{escape(report["id"])}: {report["status"]}</text>',
                    f'<image xlink:href="data:image/png;base64,{encoded}" x="{x}" y="160" width="470" height="830"/>'])
    svg.extend(['<text x="40" y="1030" font-size="17">Teal: reachable with clearance. Amber: clear but disconnected. Dark: unsupported or obstructed.</text>',
                '<text x="40" y="1066" font-size="16">This does not replace CS2 traversal or validate the estimated building dimensions.</text>','</g></svg>'])
    (output/'review.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config/povo1_interior_study.json')
    parser.add_argument('--asset-dir',type=Path,default=ROOT/'exports/povo1_interior_study')
    parser.add_argument('--output',type=Path,default=ROOT/'exports/povo1_interior_audit')
    parser.add_argument('--cell',type=float,default=.1)
    parser.add_argument('--width',type=float,default=.85)
    parser.add_argument('--height',type=float,default=1.9)
    args=parser.parse_args()
    try:result=run_audit(args.config,args.asset_dir,args.output,cell=args.cell,width=args.width,height=args.height)
    except (OSError,ValueError,KeyError) as error:parser.exit(2,f'error: {error}\n')
    for level in result['levels']:
        print(f"{level['id']}: {level['status']}; {sum(s['reachable_from_entrance'] for s in level['stations'])}/{len(level['stations'])} stations reachable")
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
