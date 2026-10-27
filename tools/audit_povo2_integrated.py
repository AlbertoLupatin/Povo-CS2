"""Check the actual campus assembly, including stacked Povo 2 stairs."""
import json
import math

try:
    from .build_povo_campus import ROOT, build_geometry, collision_boxes
    from .audit_povo_interior import audit_level, map_png
except ImportError:
    from build_povo_campus import ROOT, build_geometry, collision_boxes
    from audit_povo_interior import audit_level, map_png


def audit_stair_routes(physics, routes):
    """Check every tread and landing with a standing player envelope.

    Routes retain each tread elevation rather than interpolating a ramp through
    solid risers. Equal-height landing segments receive extra 20 cm samples.
    """
    failures=[];samples=0
    expanded=[]
    for route in routes:
        points=route['points'];dense=[]
        for i,p in enumerate(points):
            dense.append(p)
            if i+1<len(points) and abs(p[2]-points[i+1][2])<.001:
                q=points[i+1]
                count=max(1,math.ceil(math.dist(p[:2],q[:2])/.2))
                dense.extend([[p[k]+(q[k]-p[k])*j/count for k in range(3)] for j in range(1,count)])
        expanded.append(dict(points=dense))
    for route in expanded:
        for x,y,z in route['points']:
            samples+=1
            supported=any(lo[0]-.001<=x<=hi[0]+.001 and lo[1]-.001<=y<=hi[1]+.001 and abs(hi[2]-z)<.02
                          for _,lo,hi,m in physics if m.startswith('floor_'))
            obstacles=[n for n,lo,hi,m in physics if lo[0]<x+.41 and hi[0]>x-.41
                       and lo[1]<y+.41 and hi[1]>y-.41 and hi[2]>z+.37 and lo[2]<z+1.85]
            if not supported or obstacles:failures.append(dict(point=[x,y,z],supported=supported,obstacles=obstacles))
    return samples,failures


def audit():
    _,_,boxes,levels,_=build_geometry();physics=collision_boxes(boxes)
    link=next(l['connection'] for l in levels if l.get('connection'));spec=link['povo2'];reports=[]
    for level in spec['levels']:
        z=level['z'];prefix=level['id']
        support=[(prefix+'_alias_'+name,lo,hi,m) for name,lo,hi,m in physics
                 if name.startswith(('p2_','academic_first_link_p2'))
                 and m.startswith('floor_') and abs(hi[2]-z)<.02]
        report,free,visited=audit_level(physics+support,
            dict(id=prefix,floor_elevation_local=z),level['audit_stations'],width=.82,height=1.85)
        reports.append(report)
    routes=[dict(lower_floor=0,points=[link['stair']['top'],*link['stair']['path'],link['stair']['bottom']]),
            *spec['stairs']['path']]
    samples,failures=audit_stair_routes(physics,routes)
    return dict(status='passed' if not failures and all(r['status']=='passed' for r in reports) else 'failed',
                levels=reports,stair_samples=samples,stair_failures=failures,
                limitations='Source geometry only; engine walking is checked separately.')


if __name__=='__main__':
    result=audit();out=ROOT/'exports/povo_campus';out.mkdir(parents=True,exist_ok=True)
    (out/'povo2_integrated_clearance.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in result['levels']:
        print(r['id'],r['status'],len(r['stations']),'stations')
        for s in r['stations']:
            if not s['reachable_from_entrance']:print('UNREACHABLE',s['id'],s['point_local_metres'])
    print('Stairs:',result['stair_samples'],'samples;',len(result['stair_failures']),'failures')
    for f in result['stair_failures']:print(f)
    raise SystemExit(0 if result['status']=='passed' else 1)
