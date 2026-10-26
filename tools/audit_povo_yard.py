"""Validate the basement exit, sunken yard and connection to existing pavement."""
import json
from pathlib import Path
try:
    from .build_povo_campus import build_geometry,collision_boxes
    from .audit_povo_interior import audit_level
except ImportError:
    from build_povo_campus import build_geometry,collision_boxes
    from audit_povo_interior import audit_level


def audit():
    _,_,boxes,levels,_=build_geometry();physics=collision_boxes(boxes)
    yard=levels[1]['connection']['povo2']['additions']['yard']
    report,_,_=audit_level(physics,dict(id='p2_yard',floor_elevation_local=yard['z']),
                          yard['audit_stations'],width=.82,height=1.85)
    failures=[];samples=0
    for name,axis in [('indoor_path',0),('outdoor_path',1),('top_path',0)]:
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
