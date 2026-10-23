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
except ImportError:
    from build_povo_blockout import write_box

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("povo1_interior_study.obj", "povo1_interior_study.mtl",
           "floor_room.png", "floor_circulation.png", "review.svg",
           "provenance.json", "CREDITS.txt")
COLORS = {"floor_room": (183, 180, 167), "floor_circulation": (201, 207, 204),
          "wall": (220, 219, 208), "courtyard_wall": (70, 103, 105)}


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
    rectangle(config["courtyard"])
    circulation = config.get("circulation")
    if not isinstance(circulation, list) or not circulation:
        raise ValueError("Need circulation rectangles")
    seen = set()
    for entry in [*circulation, *config.get("partitions", []), *config.get("levels", [])]:
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", identifier) or identifier in seen:
            raise ValueError("Study IDs must be unique safe names")
        seen.add(identifier)
    rects = [rectangle(c["bounds"]) for c in circulation]
    if not connected(rects):
        raise ValueError("Circulation rectangles must form a connected route")
    if any(intersects(r, config["courtyard"]) for r in rects):
        raise ValueError("Circulation must not cover the courtyard")
    profiles = {p["id"] for p in alignment["profiles"]}
    previous = None
    if not config.get("levels"):
        raise ValueError("Need at least one study level")
    for level in config["levels"]:
        height = level.get("height_offset_metres")
        if level["id"] not in profiles or type(height) not in (int, float) or not math.isfinite(height):
            raise ValueError("Level must have an alignment profile and finite height offset")
        if type(level.get("stair_openings")) is not bool:
            raise ValueError("stair_openings must be a boolean")
        if previous is not None and height-previous <= config["wall_height_metres"]+config["floor_thickness_metres"]:
            raise ValueError("Level spacing must clear the walls and upper slab")
        previous = height
    for wall in config.get("partitions", []):
        for key in ("start", "end"):
            point = wall.get(key)
            if not isinstance(point, list) or len(point) != 2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 0 <= v <= 1 for v in point):
                raise ValueError("Wall endpoints must be normalized points")
        start, end = wall["start"], wall["end"]
        if (start[0] == end[0]) == (start[1] == end[1]) or any(a > b for a,b in zip(start,end)):
            raise ValueError("Walls must be positive, axis-aligned segments")
        if type(wall.get("door_width_metres")) not in (int,float) or not math.isfinite(wall["door_width_metres"]) or wall["door_width_metres"] <= 0:
            raise ValueError("Door width must be finite and positive")
        if not isinstance(wall.get("door_centres"), list) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0 < v < 1 for v in wall["door_centres"]):
            raise ValueError("Door centres must be fractions between zero and one")
    return config


def build_boxes(config, alignment, origin):
    """Resolve slabs, circulation finishes, and walls; upper floor has real voids."""
    validate(config, alignment)
    bounds = alignment["geographic_bounds"]
    whole = local_rectangle((0,0,1,1), bounds, origin)
    court = local_rectangle(config["courtyard"], bounds, origin)
    boxes, level_records = [], []

    def slab(name, rect, bottom, top, material):
        boxes.append((name, (rect[0],rect[1],bottom), (rect[2],rect[3],top), material))

    def wall(name, start, end, z, openings, width, material="wall"):
        axis = 0 if start[0] != end[0] else 1
        length = end[axis]-start[axis]
        gaps = sorted((centre*length-width/2, centre*length+width/2) for centre in openings)
        if any(a <= 0 or b >= length for a,b in gaps) or any(a[1] >= b[0] for a,b in zip(gaps,gaps[1:])):
            raise ValueError("Door openings must fit the wall without overlap")
        thickness = config["wall_thickness_metres"]
        def piece(index, low, high, bottom, top):
            minimum, maximum = list(start), list(end)
            minimum[axis] = start[axis]+low; maximum[axis] = start[axis]+high
            minimum[1-axis] -= thickness/2; maximum[1-axis] += thickness/2
            slab(name+f"_{index:02d}", (*minimum,*maximum), bottom, top, material)
        cursor = 0
        for i,(low,high) in enumerate(gaps):
            piece(i*2,cursor,low,z,z+config["wall_height_metres"])
            piece(i*2+1,low,high,z+config["door_height_metres"],z+config["wall_height_metres"])
            cursor=high
        piece(len(gaps)*2,cursor,length,z,z+config["wall_height_metres"])

    for level in config["levels"]:
        name = level["id"]
        z = config["reference_elevation_metres"]+level["height_offset_metres"]-origin[2]
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
        paths=[local_rectangle(c["bounds"],bounds,origin) for c in config["circulation"]]
        if any(intersects(path,hole) for path in paths for hole in holes):
            raise ValueError("A reserved floor opening intersects the traced circulation")
        for i,rect in enumerate(subtract_rectangles(whole,holes)):
            slab(f"{name}_slab_{i:03d}",rect,z-config["floor_thickness_metres"],z,"floor_room")
        # Overlapping finish rectangles are partitioned so there are no coplanar
        # faces or doubled floor tiles where corridor surfaces meet.
        previous_paths=[]
        for path_spec,path in zip(config["circulation"],paths):
            for i,rect in enumerate(subtract_rectangles(path,previous_paths)):
                slab(f"{name}_{path_spec['id']}_{i:03d}",rect,z,z+.012,"floor_circulation")
            previous_paths.append(path)
        perimeter=[((0,0),(0,1)),((1,0),(1,1)),((0,0),(1,0)),((0,1),(1,1))]
        entry=(profile["entry"][0]-profile["outer"][0])/(profile["outer"][2]-profile["outer"][0])
        for i,(start,end) in enumerate(perimeter):
            wall(f"{name}_outer_{i}",local_point(*start,bounds,origin),local_point(*end,bounds,origin),z,[entry] if i==3 else [],2.2)
        u0,v0,u1,v1=config["courtyard"]
        for i,(start,end) in enumerate([((u0,v0),(u0,v1)),((u1,v0),(u1,v1)),((u0,v0),(u1,v0)),((u0,v1),(u1,v1))]):
            wall(f"{name}_court_{i}",local_point(*start,bounds,origin),local_point(*end,bounds,origin),z,[],1,"courtyard_wall")
        for partition in config.get("partitions",[]):
            wall(f"{name}_{partition['id']}",local_point(*partition["start"],bounds,origin),local_point(*partition["end"],bounds,origin),z,
                 partition["door_centres"],partition["door_width_metres"])
        level_records.append({"id":name,"floor_elevation_metres":z+origin[2],"labels":profile["labels"],"voids_local_metres":holes,
                              "vertical_connection":"Stair opening reserved; no stair flights or traversable connection yet"})
    return boxes, level_records


def tile_png(color):
    size=256
    raw=b"".join(b"\0"+b"".join(bytes(tuple(max(0,c-32) for c in color) if x==0 or y==0 else color)
                                for x in range(size)) for y in range(size))
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
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850">',
           '<rect width="1200" height="850" fill="#edf1f2"/>',
           '<g font-family="DejaVu Sans, sans-serif" fill="#193441">',
           '<text x="45" y="58" font-size="30" font-weight="bold">POVO 1 / INTERIOR CIRCULATION STUDY</text>',
           '<text x="45" y="94" font-size="17">Simplified plan topology. Two provisional levels; stair flights and measured heights pending.</text>']
    west,south,east,north=alignment["geographic_bounds"]
    for index,level in enumerate(config["levels"]):
        x,y,w=100+index*580,155,310
        h=w*(north-south)/(east-west)
        def draw_rect(rect,fill,stroke="none",extra=""):
            a,b,d,e=rect
            return f'<rect x="{x+b*w}" y="{y+(1-d)*h}" width="{(e-b)*w}" height="{(d-a)*h}" fill="{fill}" stroke="{stroke}" stroke-width="2" {extra}/>'
        parts.append(f'<text x="{x}" y="{y-20}" font-size="21">{escape(level["id"])} (+{level["height_offset_metres"]:g} m estimate)</text>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#b7b4a7" stroke="#193441" stroke-width="3"/>')
        for c in config["circulation"]:
            parts.append(draw_rect(c["bounds"],"#87b5bc"))
        a,b,d,e=config["courtyard"]
        parts.extend([draw_rect(config["courtyard"],"#edf1f2","#466769"),
                      f'<text x="{x+(b+e)*w/2}" y="{y+(1-(a+d)/2)*h}" text-anchor="middle" font-size="13">COURTYARD</text>',
                      f'<text x="{x+(b+e)*w/2}" y="{y+(1-(a+d)/2)*h+20}" text-anchor="middle" font-size="12">OPEN VOID</text>'])
        profile=next(p for p in alignment["profiles"] if p["id"]==level["id"])
        for feature in profile["features"]:
            fw,fs,fe,fn=feature["approximate_geographic_bounds"]
            inset=config["stair_opening_inset_metres"]
            rect=((fs+inset-south)/(north-south),(fw+inset-west)/(east-west),
                  (fn-inset-south)/(north-south),(fe-inset-west)/(east-west))
            parts.append(draw_rect(rect,"#edf1f2" if level["stair_openings"] else "none","#d99042",'stroke-dasharray="5 3"'))
        parts.append(f'<text x="{x+w+14}" y="{y+22}" font-size="18">N ↑</text>')
    parts.extend(['<text x="45" y="755" font-size="17">Blue: connected circulation footprint. Beige: schematic floor area, not fully reconstructed rooms.</text>',
                  '<text x="45" y="789" font-size="16">North up, east right; aspect ratio preserved. Orange: reserved stair regions. Not deployed to CS2.</text>',
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
            if name.startswith("floor_"):
                # White multiplier keeps generated tile colors unchanged.
                mtl[-1]=f"newmtl {name}\nKd 1 1 1\nillum 1\nmap_Kd {name}.png\n"
                (stage/(name+".png")).write_bytes(tile_png(color))
        (stage/OUTPUTS[1]).write_text("\n".join(mtl),encoding="utf-8")
        (stage/"review.svg").write_text(review_svg(config,alignment),encoding="utf-8")
        (stage/"CREDITS.txt").write_text("Povo 1 interior circulation study. Plan reference: https://github.com/agusmeroli/mappe-povo\n"
            "Plans are marked unofficial; no redistribution licence established in the inspected source tree.\n"
            "Geometry is a coarse, assumption-labelled study; no source-image pixels are used as game textures.\n"
            "Tile patterns and material colors are original generated placeholders, not observed campus finishes.\n"
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
