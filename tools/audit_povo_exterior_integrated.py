"""Check supported outdoor routes, both door banks and the garage connection.

Includes sloped mesh support rather than treating ramps as axis-aligned boxes.
This is source geometry validation, not an engine traversal claim.
"""
import json
import math
from pathlib import Path
try:
    from .build_povo_campus import build_geometry,collision_boxes
except ImportError:
    from build_povo_campus import build_geometry,collision_boxes


def height_at(mesh,x,y):
    vertices=mesh['vertices'];heights=[]
    if not min(v[0] for v in vertices)-1e-7<=x<=max(v[0] for v in vertices)+1e-7:return heights
    if not min(v[1] for v in vertices)-1e-7<=y<=max(v[1] for v in vertices)+1e-7:return heights
    for face in mesh['faces']:
        a,b,c=[vertices[i] for i in face]
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if den<1e-9:continue # upward-facing walking surfaces only
        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w=1-u-v
        if min(u,v,w)>=-1e-7:heights.append(u*a[2]+v*b[2]+w*c[2])
    return heights


def exterior_routes():
    """Supported outdoor walking routes, as (x, y, z) waypoint polylines."""
    cy=33.5
    cfg=json.loads((Path(__file__).resolve().parents[1]/'config/povo_exterior.json').read_text())
    upper=cfg['east_approach']['upper_z'];a,b,c,d=cfg['east_approach']['stairs']
    count=math.ceil((upper-4)/.18-1e-9)
    routes={
        'povo1_entrance_to_front':[(22,-73.73,4),(26.5,-73.73,4),(27,-73.73,4),
                                  *[(a+(i+.5)*(c-a)/count,-73.73,4+(i+1)*(upper-4)/count) for i in range(count)],
                                  (36.5,-73.73,upper),(54,-73.73,upper),(57.5,-73.73,upper+.12)],
        'front_walk_to_povo2':[(54.5,-71,upper),(54.5,-13,upper),(54.5,-5,upper),
                              (54.5,0,upper+.12),(57.5,0,upper+.12),
                              (57.5,7.5,(upper+4)/2+.12),(57.5,15,4.12),(57.5,31.35,4.12),(54,31.35,4)],
        'bridge_road_to_straight_ramp':[(50,-5,upper),(32,-5,4),(22,-5,4),(-23,-5,3),(-29,-8,3),(-29,-2.5,3),(-29,30,-3.2)],
        'ramp_into_existing_parking':[(-29,30,-3.2),(-29,36,-3.2),(-5,36,-3.2),(19.8,36,-3.2)],
        'road_to_north_end':[(-29,-8,3),(-38,-8,3),(-38,6,3),(-38,112,3),(-25,118,3)],
        'surface_parking':[(-48,-44,3),(-48,-90,3)],
        # The photo-guided sunken yard replaces the old direct terrace route.
        # Preserve the outer pavement; audit_povo_yard checks its stair connection.
        'p2_yard_outer_pavement':[(57.5,31.35,4.12),(57.5,25.5,4.12),(57.5,15,4.12)]
    }
    for index,y in enumerate((cy-2.15,cy+2.15)):
        routes[f'p2_door_bank_{index}']=[(54,y,4),(49.4,y,4),(40,y,4),(34.5,y,4),(31.5,y,4),(22,y,4)]
    return routes


def route_points(path,step=.5):
    points=[]
    for a,b in zip(path,path[1:]):
        count=max(1,math.ceil(math.dist(a,b)/step))
        points.extend(tuple(a[k]+(b[k]-a[k])*i/count for k in range(3)) for i in range(count))
    points.append(tuple(path[-1]));return points


def standing(x,y,z,boxes,meshes):
    """Supporting surface near z and the boxes/meshes blocking a standing player."""
    support=[hi[2] for _,lo,hi,_ in boxes if lo[0]-1e-6<=x<=hi[0]+1e-6 and lo[1]-1e-6<=y<=hi[1]+1e-6 and abs(hi[2]-z)<=.22]
    for mesh in meshes:support.extend(v for v in height_at(mesh,x,y) if abs(v-z)<=.22)
    foot=max(support) if support else z
    obstacles=[n for n,lo,hi,m in boxes if lo[0]<x+.4 and hi[0]>x-.4 and lo[1]<y+.4 and hi[1]>y-.4
               and hi[2]>foot+.20 and lo[2]<foot+1.85]
    for mesh in meshes:
        heights=[h for xx,yy in ((x,y),(x-.4,y-.4),(x+.4,y+.4)) for h in height_at(mesh,xx,yy)]
        if heights and min(v[2] for v in mesh['vertices'])<foot+1.85 and max(heights)>foot+.22:
            # Only an actual strip volume at player height is an obstacle.
            if max(heights)-.16<foot+1.85:obstacles.append(mesh['name'])
    return (foot if support else None),obstacles


def audit():
    _,_,boxes,levels,_=build_geometry();boxes=collision_boxes(boxes)
    meta=levels[0]['exterior'];meshes=meta['collision_meshes']
    reports=[]
    for name,path in exterior_routes().items():
        points=route_points(path);failures=[];expected_blockage=[]
        for x,y,z in points:
            foot,obstacles=standing(x,y,z,boxes,meshes)
            if foot is None or obstacles:
                issue=dict(point=[x,y,z],supported=foot is not None,obstacles=obstacles[:8])
                if (name=='bridge_road_to_straight_ramp' and foot is not None and obstacles
                        and all(n.startswith('exterior_abandoned_bus_') for n in obstacles)):
                    expected_blockage.append(issue)
                else:failures.append(issue)
        status='failed' if failures else 'blocked_as_designed' if expected_blockage else 'passed'
        reports.append(dict(route=name,samples=len(points),status=status,failures=failures,
                            expected_blockage=expected_blockage))
    return dict(status='passed' if all(r['status']!='failed' for r in reports) else 'failed',routes=reports,
                samples=sum(r['samples'] for r in reports),door_opacity=meta['door_opacity'],
                limitations='Source support/standing checks; native engine movement and visuals still required')


if __name__=='__main__':
    result=audit();out=Path('exports/povo_campus/exterior_clearance.json');out.write_text(json.dumps(result,indent=2)+'\n')
    for r in result['routes']:
        print(r['route'],r['status'],r['samples'],'samples')
        for f in r['failures'][:6]:print(f)
    raise SystemExit(0 if result['status']=='passed' else 1)
