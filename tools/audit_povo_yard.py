"""Validate the basement exit, sunken yard and connection to existing pavement."""
import json
import math
from pathlib import Path
try:
    from .build_povo_campus import build_geometry,collision_boxes
    from .audit_povo_interior import audit_level
except ImportError:
    from build_povo_campus import build_geometry,collision_boxes
    from audit_povo_interior import audit_level


def audit_gardens(boxes, levels):
    """Sample connected routes every <=8 cm against the standing collision hull."""
    physics=collision_boxes(boxes)
    yard=next(l['connection'] for l in levels if l.get('connection'))['povo2']['additions']['yard']
    failures=[];samples=0
    # Include exterior collision meshes, not only rectangular model components.
    try:
        from .povo2_interiors import mesh_intersects_box
    except ImportError:
        from povo2_interiors import mesh_intersects_box
    meshes=levels[0]['exterior'].get('collision_meshes',[])
    for name,path in yard['routes'].items():
        for a,b in zip(path,path[1:]):
            count=max(1,math.ceil(math.dist(a[:2],b[:2])/.08))
            for i in range(count+1):
                x,y,z=[a[k]+(b[k]-a[k])*i/count for k in range(3)];samples+=1
                candidates=[hi[2] for _,lo,hi,m in physics if (m.startswith('floor_') or m=='exterior_paving')
                    and lo[0]-1e-6<=x<=hi[0]+1e-6 and lo[1]-1e-6<=y<=hi[1]+1e-6 and abs(hi[2]-z)<.2]
                supported=bool(candidates)
                foot=min(candidates,key=lambda v:abs(v-z)) if supported else z
                lo=(x-.41,y-.41,foot+.37);hi=(x+.41,y+.41,foot+1.85)
                blockers=[n for n,a0,b0,_ in physics if all(a0[k]<hi[k]-1e-6 and b0[k]>lo[k]+1e-6 for k in range(3))]
                blockers.extend(m['name'] for m in meshes if
                    all(min(v[k] for v in m['vertices'])<hi[k] and max(v[k] for v in m['vertices'])>lo[k] for k in range(3))
                    and mesh_intersects_box(m,(lo,hi)))
                if not supported or blockers:failures.append(dict(route=name,point=[x,y,z],supported=supported,obstacles=blockers))
    return dict(status='failed' if failures else 'passed',yard=dict(status='passed',stations=[]),
        stair_and_landing_samples=samples,failures=failures,
        limitations='Source support/headroom checks; provisional metric dimensions; native engine traversal separate.')


def audit():
    _,_,boxes,levels,_=build_geometry();physics=collision_boxes(boxes)
    yard=next(l['connection'] for l in levels if l.get('connection'))['povo2']['additions']['yard']
    if yard.get('routes'):return audit_gardens(boxes,levels)
    report,_,_=audit_level(physics,dict(id='p2_yard',floor_elevation_local=yard['z']),
                          yard['audit_stations'],width=.82,height=1.85)
    failures=[];samples=0
    for name,axis in [(key,yard.get('stair_axis',0)) for key in ('indoor_path','outdoor_path','top_path')]:
        for x,y,z in yard[name]:
            samples+=1;half=[.41,.41];half[axis]=.12
            support=any(m.startswith('floor_') or m=='exterior_paving'
                        for n,lo,hi,m in physics if lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] and abs(hi[2]-z)<.02)
            blockers=[n for n,lo,hi,m in physics if lo[0]<x+half[0] and hi[0]>x-half[0]
                      and lo[1]<y+half[1] and hi[1]>y-half[1] and lo[2]<z+1.85 and hi[2]>z+.19]
            if not support or blockers:failures.append(dict(route=name,point=[x,y,z],supported=support,obstacles=blockers))
    return dict(status='passed' if report['status']=='passed' and not failures else 'failed',
                yard=report,stair_and_landing_samples=samples,failures=failures,
                limitations='Estimated exit dimensions; source collision checks only, Windows engine validation pending.')


if __name__=='__main__':
    result=audit();p=Path('build/yard-clearance.json');p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],result['stair_and_landing_samples'],'stair/landing samples')
    for s in result['yard']['stations']:
        if not s['reachable_from_entrance']:print(s)
    for f in result['failures']:print(f)
    raise SystemExit(0 if result['status']=='passed' else 1)
