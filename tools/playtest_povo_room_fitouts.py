"""Walk into furnished Povo 1 rooms, including each upper-floor WC cubicle."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

try:
    from .playtest_povo_survey import Console,Driver,run_routes,simplify_path,door_point
    from .povo_interior_fixtures import office_frame,office_point
except ImportError:
    from playtest_povo_survey import Console,Driver,run_routes,simplify_path,door_point
    from povo_interior_fixtures import office_frame,office_point

ROOT=Path(__file__).resolve().parents[1]


def build_routes(metadata,all_levels=False):
    routes=[]
    for level in metadata['levels']:
        if not all_levels and level.get('user_floor')!=1:continue
        z=level['floor_elevation_metres']-metadata['origin'][2]
        for room in level['rooms']:
            fit=room.get('fitout')
            if not room.get('playable',True) or not isinstance(fit,dict) or 'kind' not in fit:continue
            a,b,c,d=room['footprint_local_metres'];door,normal=door_point(room)
            front={'u_min':'south','u_max':'north','v_min':'west','v_max':'east'}[room['door_side']]
            frame=office_frame((a,b,c,d),z,front);width,depth=frame[3:]
            def point(u,v):return list(office_point(frame,u,v,0))
            path=[[*[door[i]+normal[i]*.65 for i in range(2)],z]]
            approach=fit['audit_points_local_metres'][:2 if room['kind']=='meeting' else 3]
            path.extend([*p,z] for p in approach)
            if room['kind']=='restroom':
                shared=depth-2.75
                path.append(point(width/2,shared))
                for p in fit['audit_points_local_metres'][3:3+fit['toilets']]:
                    u=sum((p[i]-frame[0][i])*frame[1][i] for i in range(2))
                    path.extend([point(u,shared),[*p,z],point(u,shared),point(width/2,shared)])
                path.append(point(width/2,1.05))
                for p in fit['audit_points_local_metres'][3+fit['toilets']:]:
                    u=sum((p[i]-frame[0][i])*frame[1][i] for i in range(2))
                    path.extend([point(u,1.05),[*p,z],point(u,1.05)])
                path.append(point(width/2,1.05))
            elif room['kind']=='meeting':path.extend([point(.7,1.05),point(.7,depth*.4)])
            path.extend(reversed(path[:-1]))
            routes.append(dict(name=level['id']+'_'+room['id'],kind='walk',category='furnished_room',
                               room_kind=room['kind'],path=simplify_path(path),xy_tolerance=.08))
    return routes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-package-sha256');p.add_argument('--all-levels',action='store_true')
    p.add_argument('--list-routes',action='store_true');p.add_argument('--rooms')
    p.add_argument('--output',type=Path,default=ROOT/'build/gameplay/interiors-glass/rooms')
    args=p.parse_args();routes=build_routes(json.loads((ROOT/'exports/povo_campus/provenance.json').read_text()),args.all_levels)
    if args.rooms:routes=[r for r in routes if re.search(args.rooms,r['name'])]
    if not routes:p.error('No matching rooms')
    if args.list_routes:print(json.dumps(routes,indent=2));return 0
    package=ROOT/'build/package/trento_povo_campus.vpk';sha=hashlib.sha256(package.read_bytes()).hexdigest()
    if sha!=args.expected_package_sha256:p.error('Explicit matching package hash required')
    report=dict(status='failed',routes=[],route_plan=routes,planned_routes=len(routes),package_sha256=sha,
                started_at_utc=datetime.now(timezone.utc).isoformat(),
                scope='One hall placement per room; normal walking through its door, WC cubicles/basins and back; noclip disabled.')
    args.output.mkdir(parents=True,exist_ok=True);console=Console(27400);driver=Driver(console,'trento_povo_campus')
    try:run_routes(driver,routes,report,args.output)
    finally:
        driver.cleanup();report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (args.output/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        (args.output/'survey-runtime.log').write_text('\n'.join(console.transcript));console.close()
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
