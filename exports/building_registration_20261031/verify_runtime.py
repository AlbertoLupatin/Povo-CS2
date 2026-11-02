"""Replay the registration walking checks after a fresh solo campus launch.

Run with the repository's Python and --expected-package-sha256 from the latest
verified build. Prior failed runs are retained in runtime and runtime-final.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.audit_povo_exterior_integrated import height_at
from tools.cs2_project import discover_cs2_root
from tools.playtest_povo_survey import Console, Driver, run_routes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-package-sha256',required=True)
    parser.add_argument('--output',type=Path,default=Path(__file__).parent/'runtime-verified')
    args=parser.parse_args()
    package=ROOT/'build/package/trento_povo_campus.vpk'
    metadata_path=ROOT/'exports/povo_campus/provenance.json'
    digest=hashlib.sha256(package.read_bytes()).hexdigest()
    if digest!=args.expected_package_sha256:
        raise RuntimeError('Package differs from the verified build')
    installed=discover_cs2_root()/'game/csgo_addons/trento_povo_campus_test/maps'/package.name
    if hashlib.sha256(installed.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Fresh launch addon differs from the verified package')
    metadata=json.loads(metadata_path.read_text())
    saved=json.loads((Path(__file__).parent/'runtime-routes.json').read_text())
    routes=[];slope_evidence=[]
    for name,start,points in saved:
        path=[[*start[:2],start[2]-.1],*points]
        for i,p in enumerate(path):
            if abs(p[0]-57.5)>.001 or abs(p[1]-7.5)>.001:continue
            # CS2's standing hull has a 16-unit (0.4064 m) half-width.
            # The original centre-point grade missed the adjacent sloping
            # footway touched by that hull. Keep the normal 25 cm tolerance;
            # derive the expected foot height from the actual source surfaces.
            radius=.4064
            support=[h for mesh in metadata['exterior']['collision_meshes']
                     for dx in (-radius,0,radius) for dy in (-radius,0,radius)
                     for h in height_at(mesh,p[0]+dx,p[1]+dy)
                     if abs(h-p[2])<.6]
            if not support:raise RuntimeError('Ramp waypoint has no source support')
            corrected=[p[0],p[1],max(support)]
            slope_evidence.append(dict(route=name,nominal_point=p,expected_point=corrected,
                                       hull_half_width_m=radius))
            path[i]=corrected
        routes.append(dict(name=name,kind='walk',category='registration',path=path,xy_tolerance=.15))
        if name in ('p2_south_door_bank','p2_north_door_bank','surface_parking'):
            routes.append(dict(name=name+'_return',kind='walk',category='registration',
                               path=list(reversed(path)),xy_tolerance=.15))
    report=dict(status='failed',started_at_utc=datetime.now(timezone.utc).isoformat(),
                planned_routes=len(routes),routes=[],route_plan=routes,
                package_on_disk=str(package),package_sha256=digest,package_bytes=package.stat().st_size,
                fresh_launch_copy=str(installed),fresh_launch_copy_sha256=digest,
                metadata_sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
                slope_support=slope_evidence,
                movement='One initial placement per route; ordinary walking; noclip disabled; no waypoint teleports',
                package_identity_scope='Disk and launch-copy hashes match; operator must launch a fresh process before running')
    args.output.mkdir(parents=True,exist_ok=True)
    console=Console(27400);driver=Driver(console,'trento_povo_campus')
    try:
        report['initial_status']=driver.guard()
        run_routes(driver,routes,report,args.output)
    except BaseException as error:
        report['status']='failed';report['error']=str(error)
    finally:
        try:driver.cleanup()
        except Exception as error:
            report['status']='failed';report['cleanup_error']=str(error)
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (args.output/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        (args.output/'survey-runtime.log').write_text('\n'.join(console.transcript))
        console.close()
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
