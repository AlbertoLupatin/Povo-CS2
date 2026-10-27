"""Standing-clearance and stair support checks for the library/canteen source."""
import json
from pathlib import Path
try:
    from .build_povo_campus import build_geometry,collision_boxes
    from .audit_povo_interior import audit_level
except ImportError:
    from build_povo_campus import build_geometry,collision_boxes
    from audit_povo_interior import audit_level


def audit(boxes=None,spec=None):
    if boxes is None:
        _,_,boxes,levels,_=build_geometry()
        spec=levels[0]['wings']
    physics=collision_boxes(boxes)
    reports=[];failures=[];samples=0
    for level in spec['levels']:
        z=level['z'];prefix=level['id']
        support=[(prefix+'_alias_'+n,lo,hi,'floor_route') for n,lo,hi,m in physics
                 if ((n.startswith(level['building']+'_') and (m.startswith('floor_') or n=='canteen_1_street_terrace'))
                     or n=='exterior_povo1_front_walk') and abs(hi[2]-z)<.02]
        report,_,_=audit_level(physics+support,dict(id=prefix,floor_elevation_local=z),
                               level['audit_stations'],width=.82,height=1.85)
        reports.append(report)
    for stair in spec['stairs']:
        for x,y,z in [stair['bottom'],*stair['path'],stair['top']]:
            samples+=1
            supported=any(m.startswith('floor_') and lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                          and abs(hi[2]-z)<.02 for _,lo,hi,m in physics)
            # The short longitudinal probe permits a single riser ahead; the
            # transverse probe keeps the full standing-width envelope.
            rx,ry=(.12,.41) if stair.get('axis')=='x' else (.41,.12)
            blockers=[n for n,lo,hi,m in physics if lo[0]<x+rx and hi[0]>x-rx
                      and lo[1]<y+ry and hi[1]>y-ry and lo[2]<z+1.85 and hi[2]>z+.19]
            if not supported or blockers:failures.append(dict(point=[x,y,z],supported=supported,obstacles=blockers))
    return dict(status='passed' if not failures and all(r['status']=='passed' for r in reports) else 'failed',
                levels=reports,stair_samples=samples,stair_failures=failures,
                limitations='Source standing envelope only; Windows compilation and engine movement remain required.')


if __name__=='__main__':
    result=audit()
    out=Path('build/wings-clearance.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    for r in result['levels']:
        print(r['id'],r['status'],len(r['stations']),'stations')
        for s in r['stations']:
            if not s['reachable_from_entrance']:print('UNREACHABLE',s)
    for f in result['stair_failures']:print(f)
    raise SystemExit(0 if result['status']=='passed' else 1)
