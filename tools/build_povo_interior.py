#!/usr/bin/env python3
"""Build a separate, provisional Povo 1 interior study; standard library only."""

import argparse
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile
import zlib

try:
    from .build_povo_blockout import write_box
    from .povo_room_fitout import COLORS as FITOUT_COLORS, apply_fitouts
except ImportError:
    from build_povo_blockout import write_box
    from povo_room_fitout import COLORS as FITOUT_COLORS, apply_fitouts

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("povo1_interior_study.obj", "povo1_interior_study.mtl",
           "floor_room.png", "floor_circulation.png", "review.svg",
           "provenance.json", "CREDITS.txt", "floor_wood.png", "ceiling_panel.png")
COLORS = {"floor_room": (183, 180, 167), "floor_circulation": (201, 207, 204),
          "wall": (220, 219, 208), "courtyard_wall": (70, 103, 105), **FITOUT_COLORS}


def rectangle(value):
    if not isinstance(value, (list, tuple)) or len(value) != 4 or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in value
    ) or not (0 <= value[0] < value[2] <= 1 and 0 <= value[1] < value[3] <= 1):
        raise ValueError("Layout bounds must be positive rectangles within normalized [0,1]")
    return tuple(value)


def intersects(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def subtract_rectangles(outer, holes):
    """Partition a rectangle around possibly overlapping voids, without bridging."""
    xs = sorted({outer[0], outer[2], *(max(outer[0], min(outer[2], h[i])) for h in holes for i in (0, 2))})
    ys = sorted({outer[1], outer[3], *(max(outer[1], min(outer[3], h[i])) for h in holes for i in (1, 3))})
    for y0, y1 in zip(ys, ys[1:]):
        run = None
        for x0, x1 in zip(xs, xs[1:]):
            inside = any(h[0] < (x0+x1)/2 < h[2] and h[1] < (y0+y1)/2 < h[3] for h in holes)
            if inside:
                if run is not None:
                    yield (run, y0, x0, y1)
                    run = None
            elif run is None:
                run = x0
        if run is not None:
            yield (run, y0, outer[2], y1)


def local_point(u, v, geographic_bounds, origin):
    west, south, east, north = geographic_bounds
    # Plans have north to the right, east downward.
    return west + v*(east-west) - origin[0], south + u*(north-south) - origin[1]


def local_rectangle(rect, geographic_bounds, origin):
    lo = local_point(rect[0], rect[1], geographic_bounds, origin)
    hi = local_point(rect[2], rect[3], geographic_bounds, origin)
    return (*lo, *hi)


def connected(rectangles):
    seen, pending = {0}, [0]
    while pending:
        current = pending.pop()
        for i, rect in enumerate(rectangles):
            if i not in seen and intersects(rectangles[current], rect):
                seen.add(i); pending.append(i)
    return len(seen) == len(rectangles)


def level_layout(level, alignment):
    """Resolve manually traced source pixels through this floor's registration."""
    profile = next(p for p in alignment['profiles'] if p['id'] == level['id'])
    x0,y0,x1,y1 = profile['outer']
    def normalized(pixels):
        if not isinstance(pixels,list) or len(pixels)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in pixels):
            raise ValueError('Need four finite source pixel bounds')
        a,b,c,d=pixels
        return rectangle(((a-x0)/(x1-x0),(b-y0)/(y1-y0),(c-x0)/(x1-x0),(d-y0)/(y1-y0)))
    return (normalized(level['courtyard_pixels']),
            [dict(c,bounds=normalized(c['pixel_bounds'])) for c in level['circulation']],
            [dict(r,bounds=normalized(r['pixel_bounds'])) for r in level['rooms']])


def validate(config, alignment):
    geographic = alignment.get("geographic_bounds")
    if not isinstance(geographic, list) or len(geographic) != 4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in geographic) or not (geographic[0]<geographic[2] and geographic[1]<geographic[3]):
        raise ValueError("Alignment needs finite geographic bounds with positive area")
    for key in ("reference_elevation_metres", "floor_thickness_metres", "wall_height_metres",
                "wall_thickness_metres", "door_height_metres", "tile_pitch_metres", "stair_opening_inset_metres"):
        value = config.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or (key != "reference_elevation_metres" and value <= 0):
            raise ValueError(f"{key} must be finite and positive where applicable")
    if config["wall_height_metres"] <= config["door_height_metres"]:
        raise ValueError("Door height must be below wall height")
    profiles = {p["id"] for p in alignment["profiles"]}
    previous = None
    seen = set()
    if not config.get("levels"):
        raise ValueError("Need at least one study level")
    for level in config["levels"]:
        height = level.get("height_offset_metres")
        if level["id"] not in profiles or level['id'] in seen or type(height) not in (int, float) or not math.isfinite(height):
            raise ValueError("Level must have a unique alignment profile and finite height offset")
        seen.add(level['id'])
        if type(level.get("stair_openings")) is not bool or type(level.get('external_entrance')) is not bool:
            raise ValueError("stair_openings and external_entrance must be booleans")
        if previous is not None and height-previous <= config["wall_height_metres"]+config["floor_thickness_metres"]:
            raise ValueError("Level spacing must clear the walls and upper slab")
        previous = height
        court, circulation, rooms = level_layout(level,alignment)
        rects = [c['bounds'] for c in circulation]
        if not rects or not connected(rects):
            raise ValueError("Circulation rectangles must form a connected route")
        if any(intersects(r,court) for r in rects):
            raise ValueError("Circulation must not cover the courtyard")
        ids=set()
        for entry in [*circulation,*rooms]:
            identifier=entry.get('id')
            if not isinstance(identifier,str) or not re.fullmatch(r'[a-z][a-z0-9_]*',identifier) or identifier in ids:
                raise ValueError('Each floor needs unique safe room/circulation IDs')
            ids.add(identifier)
        for i,room in enumerate(rooms):
            if intersects(room['bounds'],court) or any(intersects(room['bounds'],r) for r in rects) or any(intersects(room['bounds'],r['bounds']) for r in rooms[i+1:]):
                raise ValueError('Rooms must not overlap other rooms, circulation or courtyard')
            if room.get('door_side') not in ('u_min','u_max','v_min','v_max'):
                raise ValueError('Unknown room door side')
            for key in ('door_fraction','door_width_metres'):
                v=room.get(key)
                if type(v) not in (int,float) or not math.isfinite(v) or v<=0 or (key=='door_fraction' and v>=1):
                    raise ValueError('Door fraction and width must be finite and positive; fraction below one')
    return config


def build_boxes(config, alignment, origin):
    """Resolve slabs, circulation finishes, and walls; upper floor has real voids."""
    validate(config, alignment)
    bounds = alignment["geographic_bounds"]
    whole = local_rectangle((0,0,1,1), bounds, origin)
    boxes, level_records = [], []

    def slab(name, rect, bottom, top, material):
        boxes.append((name, (rect[0],rect[1],bottom), (rect[2],rect[3],top), material))

    def solid_wall(name,start,end,z,material):
        axis=0 if start[0]!=end[0] else 1
        minimum,maximum=list(start),list(end)
        minimum[1-axis]-=config['wall_thickness_metres']/2
        maximum[1-axis]+=config['wall_thickness_metres']/2
        slab(name,(*minimum,*maximum),z,z+config['wall_height_metres'],material)

    for level in config["levels"]:
        name = level["id"]
        z = config["reference_elevation_metres"]+level["height_offset_metres"]-origin[2]
        courtyard,circulation,rooms=level_layout(level,alignment)
        court=local_rectangle(courtyard,bounds,origin)
        holes = [court]
        profile = next(p for p in alignment["profiles"] if p["id"] == name)
        if level["stair_openings"]:
            inset=config["stair_opening_inset_metres"]
            for feature in profile["features"]:
                w,s,e,n=feature["approximate_geographic_bounds"]
                rect=(w-origin[0]+inset,s-origin[1]+inset,e-origin[0]-inset,n-origin[1]-inset)
                if rect[0]>=rect[2] or rect[1]>=rect[3]:
                    raise ValueError("Stair opening inset consumes the reserved opening")
                holes.append(rect)
        paths=[local_rectangle(c["bounds"],bounds,origin) for c in circulation]
        if any(intersects(path,hole) for path in paths for hole in holes):
            raise ValueError("A reserved floor opening intersects the traced circulation")
        if any(intersects(local_rectangle(r["bounds"],bounds,origin),hole) for r in rooms for hole in holes):
            raise ValueError("Room footprint crosses a reserved floor opening")
        for i,rect in enumerate(subtract_rectangles(whole,holes)):
            slab(f"{name}_slab_{i:03d}",rect,z-config["floor_thickness_metres"],z,"floor_room")
        # Overlapping finish rectangles are partitioned so there are no coplanar
        # faces or doubled floor tiles where corridor surfaces meet.
        previous_paths=[]
        for path_spec,path in zip(circulation,paths):
            for i,rect in enumerate(subtract_rectangles(path,previous_paths)):
                slab(f"{name}_{path_spec['id']}_{i:03d}",rect,z,z+.012,"floor_circulation")
            previous_paths.append(path)
        # Collect collinear wall spans, then merge them before cutting door gaps.
        # Adjacent classrooms share one wall, including where a room meets the
        # outer shell or courtyard; no coincident duplicate wall boxes.
        walls={}
        def add_wall(label,start,end,gaps=(),width=1.2,material='wall'):
            a=local_point(*start,bounds,origin); b=local_point(*end,bounds,origin)
            axis=0 if a[0]!=b[0] else 1
            key=(axis,round(a[1-axis],8))
            record=walls.setdefault(key,dict(name=f'{name}_{label}',spans=[],gaps=[],court_spans=[]))
            if material=='courtyard_wall':record['court_spans'].append((a[axis],b[axis]))
            record['spans'].append((a[axis],b[axis]))
            length=b[axis]-a[axis]
            for centre in gaps:
                low,high=a[axis]+centre*length-width/2,a[axis]+centre*length+width/2
                if low<=a[axis] or high>=b[axis]:raise ValueError('Door openings must fit the wall without overlap')
                record['gaps'].append((low,high))
        perimeter=[((0,0),(0,1)),((1,0),(1,1)),((0,0),(1,0)),((0,1),(1,1))]
        entry=(profile["entry"][0]-profile["outer"][0])/(profile["outer"][2]-profile["outer"][0])
        for i,(start,end) in enumerate(perimeter):
            add_wall(f'outer_{i}',start,end,[entry] if i==3 and level['external_entrance'] else [],2.2)
        u0,v0,u1,v1=courtyard
        for i,(start,end) in enumerate([((u0,v0),(u0,v1)),((u1,v0),(u1,v1)),((u0,v0),(u1,v0)),((u0,v1),(u1,v1))]):
            add_wall(f'court_{i}',start,end,material='courtyard_wall')
        room_records=[]
        for room in rooms:
            a,b,c,d=room['bounds']
            sides={'u_min':((a,b),(a,d)),'u_max':((c,b),(c,d)),
                   'v_min':((a,b),(c,b)),'v_max':((a,d),(c,d))}
            for side,(start,end) in sides.items():
                add_wall(f"room_{room['id']}_{side}",start,end,[room['door_fraction']] if side==room['door_side'] else [],room['door_width_metres'])
            rect=local_rectangle(room['bounds'],bounds,origin)
            room_records.append(dict(room,footprint_local_metres=rect,
                approximate_dimensions_metres=[rect[2]-rect[0],rect[3]-rect[1]],
                approximate_area_square_metres=(rect[2]-rect[0])*(rect[3]-rect[1]),
                fitout='Unfurnished; shared photo-guided kit planned'))
        def union(intervals):
            result=[]
            for lo,hi in sorted(intervals):
                if result and lo<=result[-1][1]+1e-7:result[-1]=(result[-1][0],max(hi,result[-1][1]))
                else:result.append((lo,hi))
            return result
        for (axis,constant),record in walls.items():
            def material_at(position):
                return 'courtyard_wall' if any(a<=position<=b for a,b in record['court_spans']) else 'wall'
            def emit_span(label,start,end):
                # Material changes along a collinear wall must not tint unrelated
                # classroom walls just because they align with a courtyard edge.
                low,high=start[axis],end[axis]
                stops=sorted({low,high,*(v for a,b in record['court_spans'] for v in (a,b) if low<v<high)})
                for k,(a,b) in enumerate(zip(stops,stops[1:])):
                    minimum,maximum=list(start),list(end)
                    minimum[axis],maximum[axis]=a,b
                    solid_wall(label+f'_material{k}',minimum,maximum,z,material_at((a+b)/2))
            for i,(low,high) in enumerate(union(record['spans'])):
                cuts=[(a,b) for a,b in union(record['gaps']) if a>=low and b<=high]
                start=[constant,constant];end=[constant,constant]
                start[axis]=low;end[axis]=high
                # Solid spans flank each variable-width door; a lintel bridges it.
                cursor=low
                for j,(a,b) in enumerate(cuts):
                    if a>cursor:
                        end[axis]=a;start[axis]=cursor
                        emit_span(record['name']+f'_{i}_{j}',start,end)
                    minimum=list(start);maximum=list(end)
                    minimum[axis]=a;maximum[axis]=b
                    minimum[1-axis]-=config['wall_thickness_metres']/2
                    maximum[1-axis]+=config['wall_thickness_metres']/2
                    slab(record['name']+f'_header_{i}_{j}',(*minimum,*maximum),z+config['door_height_metres'],z+config['wall_height_metres'],material_at((a+b)/2))
                    cursor=b
                if cursor<high:
                    start[axis]=cursor;end[axis]=high
                    emit_span(record['name']+f'_{i}_tail',start,end)
        level_records.append({"id":name,"floor_elevation_metres":z+origin[2],"labels":profile["labels"],"voids_local_metres":holes,
                              "rooms":room_records,"circulation":circulation,"courtyard":courtyard,
                              "external_entrance":level["external_entrance"],"vertical_connection":"Stair opening reserved; no stair flights or traversable connection yet"})
    return apply_fitouts(config,level_records,boxes,origin), level_records


def tile_png(color, pattern='tile'):
    size=256
    def pixel(x,y):
        if pattern=='wood':
            board=x//64
            seam=x%64==0 or (y+(board%2)*128)%256==0
            grain=round(3*math.sin(x*.9+math.sin(y*.09))+2*math.sin(x*.24+y*.015))
            offset=-25 if seam else grain+(board%3-1)*5
        elif pattern=='perforated':
            offset=-75 if x%8==2 and y%8==2 else (-22 if x==0 or y==0 else 0)
        else:offset=-32 if x==0 or y==0 else 0
        return bytes(max(0,min(255,c+offset)) for c in color)
    raw=b"".join(b"\0"+b"".join(pixel(x,y) for x in range(size)) for y in range(size))
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")


class TexturedWriter:
    def __init__(self,stream,pitch):self.stream,self.pitch=stream,pitch
    def write(self,text):
        for line in text.splitlines(keepends=True):
            self.stream.write("f "+" ".join(f"{i}/{i}" for i in line.split()[1:])+"\n" if line.startswith("f ") else line)
            if line.startswith("v "):
                x,y,_=map(float,line.split()[1:])
                u,v=x/self.pitch,y/self.pitch
                if not math.isfinite(u) or not math.isfinite(v):raise ValueError("Floor UV coordinates overflow; check tile pitch")
                self.stream.write(f"vt {u:.12g} {v:.12g}\n")


def review_svg(config, alignment):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1150" viewBox="0 0 1400 1150">',
           '<rect width="1400" height="1150" fill="#edf1f2"/>',
           '<g font-family="DejaVu Sans, sans-serif" fill="#193441">',
           '<text x="45" y="55" font-size="30" font-weight="bold">POVO 1 / ROOMS INSIDE THE BUILDING</text>',
           '<text x="45" y="94" font-size="19">Two floors of the same building. Interior study only; separate from the outdoor CS2 map.</text>',
           '<text x="45" y="130" font-size="17">Blue = corridors · beige = classrooms · purple = computer rooms / lab · green = open courtyard</text>']
    west,south,east,north=alignment["geographic_bounds"]
    for index,level in enumerate(config["levels"]):
        courtyard,circulation,rooms=level_layout(level,alignment)
        x,y,w=100+index*700,215,400
        h=w*(north-south)/(east-west)
        def point(u,v):return (x+v*w,y+(1-u)*h)
        def draw_rect(rect,fill,stroke="none",extra=""):
            a,b,d,e=rect;px,py=point(d,b)
            return f'<rect x="{px}" y="{py}" width="{(e-b)*w}" height="{(d-a)*h}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" {extra}/>'
        title='GROUND / A101–A110' if index==0 else 'UPPER / A201–A224 + LAB'
        parts.append(f'<text x="{x}" y="{y-35}" font-size="23" font-weight="bold">{title}</text>')
        parts.append(draw_rect((0,0,1,1),'#d9dedf','#193441'))
        for c in circulation:parts.append(draw_rect(c['bounds'],'#8dbbc8'))
        for room in rooms:
            a,b,c,d=room['bounds']
            color={'computer':'#c2b3d5','laboratory':'#c2b3d5','auditorium':'#dcc298'}.get(room['kind'],'#e4d9ba')
            parts.append(draw_rect(room['bounds'],color,'#5a6268'))
            px,py=point((a+c)/2,(b+d)/2)
            parts.append(f'<text x="{px}" y="{py+4}" text-anchor="middle" font-size="13" font-weight="bold">{escape(room["label"])}</text>')
            f=room['door_fraction'];side=room['door_side']
            u,v=(a if side=='u_min' else c,b+(d-b)*f) if side.startswith('u_') else (a+(c-a)*f,b if side=='v_min' else d)
            px,py=point(u,v);half=room['door_width_metres']*w/(east-west)/2
            dx,dy=(half,0) if side.startswith('u_') else (0,half)
            parts.append(f'<path d="M {px-dx} {py-dy} L {px+dx} {py+dy}" stroke="#ffffff" stroke-width="4"/>')
        a,b,c,d=courtyard
        parts.append(draw_rect(courtyard,'#b8d1bc','#466769'))
        px,py=point((a+c)/2,(b+d)/2)
        for dy,label in [(0,'COURTYARD'),(23,'OPEN TO SKY')]:
            parts.append(f'<text x="{px}" y="{py+dy}" text-anchor="middle" font-size="16">{label}</text>')
        profile=next(p for p in alignment['profiles'] if p['id']==level['id'])
        for feature in profile['features']:
            fw,fs,fe,fn=feature['approximate_geographic_bounds'];inset=config['stair_opening_inset_metres']
            rect=((fs+inset-south)/(north-south),(fw+inset-west)/(east-west),(fn-inset-south)/(north-south),(fe-inset-west)/(east-west))
            parts.append(draw_rect(rect,'#f2d3aa','#c07b23','stroke-dasharray="5 3"'))
        if level['external_entrance']:
            u=(profile['entry'][0]-profile['outer'][0])/(profile['outer'][2]-profile['outer'][0]);px,py=point(u,1)
            parts.append(f'<path d="M {px+80} {py} L {px+4} {py} l 12 -7 m -12 7 l 12 7" fill="none" stroke="#193441" stroke-width="2"/>')
            parts.append(f'<text x="{px+8}" y="{py-12}" font-size="14">Entrance</text>')
        parts.append(f'<text x="{x+w+20}" y="{y+22}" font-size="19">N ↑</text>')
        parts.append(f'<text x="{x}" y="{y+h+32}" font-size="17">Building outline: approximately 47 × 83 m</text>')
        detail='A224 pilot furnished' if index==1 and config.get('classroom_fitout') else 'unfurnished'
        parts.append(f'<text x="{x}" y="{y+h+58}" font-size="15">{len(rooms)} named rooms · {detail} · estimated heights</text>')
    parts.extend(['<text x="45" y="1040" font-size="18">White wall gaps = door openings. Orange = stair reservations; stair flights are not built.</text>',
                  '<text x="45" y="1075" font-size="17">Grey = other floor area awaiting subdivision (study areas, toilets, service spaces). Ceiling in A224 only.</text>',
                  '<text x="45" y="1110" font-size="17">A224 has a photo-guided pilot fit-out; furniture positions, dimensions and teaching side remain provisional.</text>',
                  '</g></svg>'])
    return "\n".join(parts)+"\n"


def build_study(config_path,output,*,root=ROOT,force=False):
    config_path,output,root=Path(config_path),Path(output),Path(root)
    if output.is_symlink() or (output.exists() and not output.is_dir()):raise ValueError("Output must be a directory")
    if output.exists() and not force:raise ValueError("Output exists; use --force")
    if any((output/name).is_symlink() or (output/name).is_dir() for name in OUTPUTS):raise ValueError("Output filename occupied")
    config=json.loads(config_path.read_text(encoding="utf-8"))
    alignment_path=root/config["alignment"];campus_path=root/config["campus_config"]
    alignment=json.loads(alignment_path.read_text(encoding="utf-8"))
    campus=json.loads(campus_path.read_text(encoding="utf-8"))
    targets={(output/name).resolve() for name in OUTPUTS}
    inputs=[config_path,alignment_path,campus_path,*(root/p["source_file"] for p in alignment["profiles"])]
    photo_sources=[]
    photo_manifest=None
    if config.get('photo_reference'):
        photo_manifest=root/config['photo_reference']['manifest']
        photos=json.loads(photo_manifest.read_text(encoding='utf-8'))['images']
        inputs.append(photo_manifest)
        for identifier in config['photo_reference']['ids']:
            matching=[p for p in photos if p['id']==identifier]
            if len(matching)!=1:raise ValueError('Missing or duplicate photo reference ID')
            photo=matching[0];file=photo_manifest.parent/photo['file']
            if not file.resolve().is_relative_to(root.resolve()):raise ValueError('Photo reference outside project')
            if hashlib.sha256(file.read_bytes()).hexdigest()!=photo['sha256']:raise ValueError('Photo reference hash mismatch')
            inputs.append(file)
            photo_sources.append(dict(id=identifier,file=str(file.relative_to(root)),sha256=photo['sha256'],
                description=photo['description'],license=photo.get('license','Not supplied')))
    if any(file.resolve() in targets for file in inputs):raise ValueError("Generated files must not replace inputs")
    for profile in alignment["profiles"]:
        image=root/profile["source_file"]
        if hashlib.sha256(image.read_bytes()).hexdigest()!=profile["sha256"]:raise ValueError("Plan image hash mismatch")
    boxes,levels=build_boxes(config,alignment,campus["origin"])
    metadata={"format_version":1,"status":config["status"],"assumptions":config["assumptions"],"origin":campus["origin"],
              "coordinate_system":"Local metres; east +X, north +Y, up +Z; same origin as campus",
              "levels":levels,"statistics":{"boxes":len(boxes),"vertices":8*len(boxes),"triangles":12*len(boxes)},
              "inputs":{name:{"file":str(file.relative_to(root)) if file.is_relative_to(root) else file.name,
                              "sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
                        for name,file in (("configuration",config_path),("alignment",alignment_path),("campus",campus_path))},
              "source_profiles":alignment["profiles"],"deployment":"Excluded from cs2_project deploy; no arena collision changes"}
    if photo_manifest:
        metadata['inputs']['photo_manifest']={'file':str(photo_manifest.relative_to(root)),
            'sha256':hashlib.sha256(photo_manifest.read_bytes()).hexdigest()}
    metadata['photo_sources']=photo_sources
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".povo-interior-",dir=output.parent) as temporary:
        stage=Path(temporary)
        with (stage/OUTPUTS[0]).open("w",encoding="utf-8") as stream:
            stream.write("# Provisional Povo 1 interior study; not a compiled or playable map.\nmtllib povo1_interior_study.mtl\n")
            writer=TexturedWriter(stream,config["tile_pitch_metres"])
            for i,(name,lo,hi,material) in enumerate(boxes):write_box(writer,name,lo,hi,i*8,material)
        mtl=[]
        for name,color in COLORS.items():
            mtl.append(f"newmtl {name}\nKd {' '.join(str(v/255) for v in color)}\nillum 1\n")
            if name.startswith("floor_") or name=='ceiling_panel':
                # White multiplier keeps generated tile colors unchanged.
                mtl[-1]=f"newmtl {name}\nKd 1 1 1\nillum 1\nmap_Kd {name}.png\n"
                pattern={'floor_wood':'wood','ceiling_panel':'perforated'}.get(name,'tile')
                (stage/(name+".png")).write_bytes(tile_png(color,pattern))
            if name=='window_glass':mtl[-1]+='d 0.18\n'
        (stage/OUTPUTS[1]).write_text("\n".join(mtl),encoding="utf-8")
        (stage/"review.svg").write_text(review_svg(config,alignment),encoding="utf-8")
        (stage/"CREDITS.txt").write_text("Povo 1 room and circulation study. Plan reference: https://github.com/agusmeroli/mappe-povo\n"
            "Plans are marked unofficial; no redistribution licence established in the inspected source tree.\n"
            "Geometry is a coarse, assumption-labelled study; no source-image pixels are used as game textures.\n"
            "A224 fit-out appearance references user-supplied P020/P021/P022. Room identity for P022 is unknown.\n"
            "No people, screen text or source-image pixels are reproduced in generated assets.\n"
            "Wood-look floor, ceiling and furniture colors are approximate; generated texture patterns are original.\n"
            "Furniture arrangement, count, glazing and fixture dimensions are provisional. No functional breakable glass is built.\n"
            "Source locations and hashes are recorded in provenance.json; do not treat floor heights or doors as measured.\n",encoding="utf-8")
        metadata["artifacts"]={name:{"sha256":hashlib.sha256((stage/name).read_bytes()).hexdigest(),"bytes":(stage/name).stat().st_size}
                               for name in OUTPUTS if name!="provenance.json"}
        (stage/"provenance.json").write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        output.mkdir(exist_ok=force)
        for name in OUTPUTS:os.replace(stage/name,output/name)
    return metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=ROOT/"config/povo1_interior_study.json")
    parser.add_argument("--output",type=Path,default=ROOT/"exports/povo1_interior_study")
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--force",action="store_true")
    args=parser.parse_args()
    try:metadata=build_study(args.config,args.output,root=args.root,force=args.force)
    except (OSError,ValueError,KeyError) as error:parser.exit(2,f"error: {error}\n")
    print(f"Saved {args.output}: {metadata['statistics']['triangles']} triangles; offline interior study only")


if __name__=="__main__":main()
