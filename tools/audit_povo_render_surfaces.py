"""Audit duplicate coplanar render faces, including walls, ceilings and slopes."""
import argparse
from collections import Counter
import json
from pathlib import Path
try:
    from .povo_floor_surfaces import area,bounds,subtract
    from .povo_render_surfaces import project,SurfaceIndex
except ImportError:
    from povo_floor_surfaces import area,bounds,subtract
    from povo_render_surfaces import project,SurfaceIndex


def audit(path):
    vertices=[];material='';group='';index=SurfaceIndex();face_count=0;failures=[];axes=Counter();materials=Counter()
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
        elif line.startswith('usemtl '):material=line[7:]
        elif line.startswith('o '):group=line[2:]
        elif line.startswith('f '):
            points=[vertices[int(r.split('/')[0])-1] for r in line.split()[1:]]
            face_count+=1;projected=project(points)
            if projected is None:continue
            key,polygon,_,axis=projected
            for occupied,_,old in index.candidates(key,bounds(polygon)):
                overlap=area(polygon)-sum(area(p) for p in subtract(polygon,occupied))
                if overlap<=1e-6:continue
                label='horizontal' if axis==2 and abs(key[2])>.99999999 else 'vertical' if abs(key[2])<1e-8 else 'sloped'
                axes[label]+=1;materials[' / '.join(sorted((old['material'],material)))]+=1
                # Projection removes the dominant normal component, so restore
                # true surface area for tilted faces.
                overlap/=abs(key[axis])
                failures.append(dict(face=face_count,group=group,material=material,
                                     other=old,orientation=label,overlap_square_metres=overlap,
                                     vertices=points))
            index.add(key,polygon,dict(face=face_count,group=group,material=material))
    return dict(status='failed' if failures else 'passed',source=str(path),faces=face_count,
                overlapping_pairs=len(failures),by_orientation=dict(axes),by_material=dict(materials),
                overlap_square_metres=sum(f['overlap_square_metres'] for f in failures),failures=failures)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('obj',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=audit(args.obj)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['faces'],'faces;',result['overlapping_pairs'],'overlapping pairs;',result['by_orientation'])
    raise SystemExit(result['status']!='passed')
