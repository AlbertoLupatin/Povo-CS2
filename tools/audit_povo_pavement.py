"""Sample the full repaired paving areas, including their visible collision."""
import json
from pathlib import Path
try:
    from .build_povo_campus import build_geometry,collision_boxes
    from .audit_povo_exterior_integrated import height_at
except ImportError:
    from build_povo_campus import build_geometry,collision_boxes
    from audit_povo_exterior_integrated import height_at


def audit(boxes=None, levels=None, step=.5):
    if boxes is None:_,_,boxes,levels,_=build_geometry()
    ext=levels[0]['exterior'];repairs=ext['pavement_repairs']
    visual=[b for b in boxes if b[3]=='exterior_paving']
    physical=[b for b in collision_boxes(boxes) if b[3]=='exterior_paving']
    yard=repairs['yard_exclusion'];failures=[];samples=0
    def check(x,y,z):
        nonlocal samples
        if yard[0]-.12<=x<=yard[2]+.12 and yard[1]-.12<=y<=yard[3]+.12:return
        if any(a<=x<=c and b<=y<=d for a,b,c,d in repairs.get('garden_exclusions',[])):return
        samples+=1
        def supported(bs,ms):
            return any(lo[0]-1e-6<=x<=hi[0]+1e-6 and lo[1]-1e-6<=y<=hi[1]+1e-6
                       and abs(hi[2]-z)<.03 for _,lo,hi,_ in bs) or any(
                       abs(h-z)<.03 for m in ms for h in height_at(m,x,y))
        v=supported(visual,ext['meshes']);p=supported(physical,ext['collision_meshes'])
        if not v or not p:failures.append(dict(point=[x,y,z],visual=v,collision=p))
    for zone in repairs['zones']:
        a,b,c,d=zone['bounds'];x=a+step/2
        while x<c:
            y=b+step/2
            while y<d:check(x,y,zone['z']);y+=step
            x+=step
    a,b,c,d=repairs['bridge_apron'];x=a+step/2
    while x<c:
        y=b+step/2
        while y<d:
            road=3+min(1,max(0,(x+23)/45))+.12
            check(x,y,4+(road-4)*(y+20)/12);y+=step
        x+=step
    return dict(status='failed' if failures else 'passed',samples=samples,
                failures=failures,grid_metres=step,
                scope='Full repaired plaza areas and grade; source visual/collision support. Engine checks separate.')


if __name__=='__main__':
    result=audit();p=Path('build/pavement-clearance.json');p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['samples'],'samples')
    for f in result['failures'][:10]:print(f)
    raise SystemExit(result['status']!='passed')
