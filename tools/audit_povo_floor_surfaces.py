"""Detect positive-area duplicate horizontal rendered floor surfaces in OBJ."""
import argparse
import json
import math
from pathlib import Path
try:
    from .povo_floor_surfaces import area,bounds,is_floor,overlaps,subtract
except ImportError:
    from povo_floor_surfaces import area,bounds,is_floor,overlaps,subtract


def audit(path):
    vertices=[];material='';faces=[];cells={};pairs=set()
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
        elif line.startswith('usemtl '):material=line[7:]
        elif line.startswith('f ') and is_floor(material):
            points=[vertices[int(r.split('/')[0])-1] for r in line.split()[1:]]
            if max(p[2] for p in points)-min(p[2] for p in points)>1e-8:continue
            a,b,c=points[:3]
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<=1e-8:continue
            box=bounds(points);index=len(faces);faces.append((points,box,material))
            for x in range(math.floor(box[0]/8),math.floor(box[2]/8)+1):
                for y in range(math.floor(box[1]/8),math.floor(box[3]/8)+1):
                    cell=cells.setdefault((round(a[2],7),x,y),[])
                    pairs.update((old,index) for old in cell if overlaps(faces[old][1],box))
                    cell.append(index)
    failures=[]
    for i,j in sorted(pairs):
        a,_,ma=faces[i];b,_,mb=faces[j]
        overlap=area(a)-sum(area(p) for p in subtract(a,b))
        if overlap>1e-6:failures.append(dict(faces=[i,j],materials=[ma,mb],overlap_square_metres=overlap))
    return dict(status='failed' if failures else 'passed',source=str(path),
                horizontal_floor_faces=len(faces),overlapping_pairs=len(failures),
                overlap_square_metres=sum(f['overlap_square_metres'] for f in failures),failures=failures)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('obj',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=audit(args.obj)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['horizontal_floor_faces'],'floor faces;',result['overlapping_pairs'],'overlapping pairs')
    raise SystemExit(result['status']!='passed')
