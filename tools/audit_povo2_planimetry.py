"""Check Povo 2 horizontal routes and stair support/headroom in source geometry."""
import json

try:
    from .build_povo_campus import ROOT, collision_boxes
    from .povo2_planimetry import build
    from .audit_povo_interior import audit_level
except ImportError:
    from build_povo_campus import ROOT, collision_boxes
    from povo2_planimetry import build
    from audit_povo_interior import audit_level


def audit():
    boxes,spec=build();physics=collision_boxes(boxes)
    reports=[]
    for level in spec['levels']:
        stations=level['audit_stations'] if level['floor']!=1 else [dict(id='draft_stair_landing',point=[26.2,39.5])]
        report,_,_=audit_level(physics,
            dict(id=level['id'],floor_elevation_local=level['z']),
            stations,width=.82,height=1.85)
        report['vertical_traversal']='See separate supported stair-path envelope checks'
        reports.append(report)
    # Sample every tread and both landings with a standing player envelope.
    # Ignore tiny finish detail using the same physics selection as export.
    failures=[];samples=0
    for route in spec['stairs']['path']:
        for x,y,z in route['points']:
            samples+=1
            supported=any(lo[0]-.001<=x<=hi[0]+.001 and lo[1]-.001<=y<=hi[1]+.001
                          and abs(hi[2]-z)<.02 for _,lo,hi,_ in physics)
            # Small overlap onto the next step is allowed within a .19 m rise.
            obstacles=[n for n,lo,hi,_ in physics
                       if lo[0]<x+.41 and hi[0]>x-.41 and lo[1]<y+.12 and hi[1]>y-.12
                       and hi[2]>z+.19 and lo[2]<z+1.85]
            if not supported or obstacles:
                failures.append(dict(point=[x,y,z],supported=supported,obstacles=obstacles))
    result=dict(status='passed' if all(r['status']=='passed' for r in reports) and not failures else 'failed',
                levels=reports,stair_samples=samples,stair_failures=failures,
                limitations='Standalone draft box geometry only. The upper landing is checked locally; connection to the separately edited first floor is not validated. CS2 compilation, collision, navigation and walking remain to be tested.')
    return result


if __name__=='__main__':
    result=audit();out=ROOT/'exports/povo2_planimetry';out.mkdir(parents=True,exist_ok=True)
    (out/'clearance.json').write_text(json.dumps(result,indent=2)+'\n')
    for level in result['levels']:
        print(level['id'],level['status'],len(level['stations']),'stations')
        for s in level['stations']:
            if not s['reachable_from_entrance']:print('UNREACHABLE',s['id'])
    print('Stairs:',result['stair_samples'],'samples;',len(result['stair_failures']),'failures')
    for failure in result['stair_failures']:print(failure)
    raise SystemExit(0 if result['status']=='passed' else 1)
