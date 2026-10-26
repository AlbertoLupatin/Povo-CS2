#!/usr/bin/env python3
"""Normal-walking checks for the compiled exterior, via CS2's local netconsole.

Requires the new package already loaded in solo exploration. Each independent
route has one starting placement; movement between waypoints uses normal walking.
No screenshots or Windows input injection are performed by this script.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
try:
    from .cs2_console import run
    from .cs2_campus import world,UNITS
    from .cs2_explore import campus_loaded
except ImportError:
    from cs2_console import run
    from cs2_campus import world,UNITS
    from cs2_explore import campus_loaded

ROOT=Path(__file__).resolve().parents[1]

def playtest(*, routes=None, output=None, package=None, port=27400,map_name='trento_povo_campus'):
    output=Path(output) if output is not None else ROOT/'build/gameplay'
    package=Path(package) if package is not None else ROOT/'build/package/trento_povo_campus.vpk'
    with package.open('rb') as stream:
        package_hash=hashlib.file_digest(stream,'sha256').hexdigest()
    transcript=[];checks=[]
    def command(commands,seconds=.2):
        if isinstance(commands,str):commands=[commands]
        transcript.append('> '+'\n> '.join(commands))
        out=run(commands,seconds=seconds,port=port);transcript.append(out);return out
    def position():
        text=command('getpos_exact')
        found=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',text)
        if not found:raise RuntimeError('CS2 player position unavailable')
        x,y,z=map(float,found[-1]);return y/UNITS,-x/UNITS,z/UNITS
    def place(point):
        command(['sv_cheats 1','god 1','noclip 0','slot3','gameui_hide','setpos '+world(point)],.6)
    def walk_to(target):
        start=position();distance=math.dist(start[:2],target[:2]);deadline=time.monotonic()+distance/3+8
        stalled=0;old_distance=distance
        while time.monotonic()<deadline:
            p=position();dx=target[0]-p[0];dy=target[1]-p[1];distance=math.hypot(dx,dy)
            if distance<.5:return p
            yaw=math.degrees(math.atan2(dx,-dy));duration=min(.45,max(.07,(distance-.3)/7))
            command([f'setang 0 {yaw:.3f} 0','+forward 42'],duration)
            command('-forward 42',.12)
            stalled=stalled+1 if abs(old_distance-distance)<.035 else 0;old_distance=distance
            if stalled>=6:break
        raise RuntimeError('Normal walking stalled near '+str(position())+' towards '+str(target))
    if routes is None:routes=[
        ('p2_south_door_bank',(54,31.35,4.1),[(49,31.35,4),(34,31.35,4),(31.5,31.35,4)]),
        ('p2_north_door_bank',(54,35.65,4.1),[(49,35.65,4),(34,35.65,4),(31.5,35.65,4)]),
        ('straight_ramp_down',(-29,-3.5,3.1),[(-29,0,2.52),(-29,20,-1.3),(-29,33,-3.2)]),
        ('straight_ramp_up',(-29,33,-3.1),[(-29,20,-1.3),(-29,0,2.52),(-29,-3.5,3)]),
        ('garage_into_original_parking',(-29,36,-3.1),[(-5,36,-3.2),(18,36,-3.2),(18,27,-3.2),(17.8,22,-3.2)]),
        ('povo1_external_stairs',(22,-73.73,4.1),[(26.5,-73.73,4),(36.5,-73.73,5.8),(54,-73.73,5.8)]),
        ('povo1_external_stairs_return',(54,-73.73,5.9),[(36.5,-73.73,5.8),(26.5,-73.73,4),(22,-73.73,4)]),
        ('povo2_left_terrace',(54,31.35,4.1),[(54,24,4),(46,24,4),(37,24,4)]),
        ('basement_right_turn',(18.25,22,.5),[(18.25,-5,.4),(7,-5,.4)]),
        ('front_walk_to_povo2',(57.5,-71,6.02),[(57.5,0,5.92),(57.5,15,4.12),(57.5,31.35,4.12),(54,31.35,4)]),
        ('bridge_road_to_ramp',(50,-5,5.9),[(32,-5,4),(22,-5,4),(-23,-5,3),(-29,-8,3),(-29,-2.5,3)]),
        ('north_road',(-29,-8,3.1),[(-38,-8,3),(-38,6,3),(-38,112,3),(-25,118,3)]),
        ('surface_parking',(-48,-44,3.1),[(-48,-90,3)])
    ]
    report={'status':'failed','checks':checks,'placement':'One initial placement per independent route; normal walking between all waypoints',
            'started_at_utc':datetime.now(timezone.utc).isoformat(),
            'package_on_disk':str(package.resolve()),'package_sha256':package_hash,
            'package_identity_scope':'On-disk package supplied by the operator; status confirms the map name, not the loaded package bytes'}
    movement_started=False
    try:
        status=command('status')
        if not campus_loaded(status,map_name) or not re.search(r'players\s*:\s*1 humans, 0 bots\b',status):
            raise RuntimeError('Load the campus in solo exploration before running walking checks')
        for name,start,points in routes:
            movement_started=True
            place(start)
            for i,point in enumerate(points):
                p=walk_to(point);ok=abs(p[2]-point[2])<.25
                check=dict(route=name,waypoint=i,target=point,position=p,passed=ok);checks.append(check)
                print(check,flush=True)
                if not ok:raise RuntimeError('Unexpected floor height during '+name)
        report['status']='passed'
    except Exception as error:
        report['error']=str(error);raise
    finally:
        if movement_started:
            try:command('-forward 42')
            except OSError as error:
                report['cleanup_error']=str(error)
                report['status']='failed'
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        output.mkdir(parents=True,exist_ok=True)
        (output/'exterior-runtime-walk.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (output/'exterior-runtime-walk.log').write_text('\n'.join(transcript),encoding='utf-8')
    if report['status']!='passed':raise RuntimeError('Walking check cleanup failed: '+report.get('cleanup_error','unknown'))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--package',type=Path)
    parser.add_argument('--port',type=int,default=27400)
    parser.add_argument('--map',dest='map_name',choices=('trento_povo_campus','trento_povo_campus_winter'),default='trento_povo_campus')
    args=parser.parse_args()
    playtest(output=args.output,package=args.package,port=args.port,map_name=args.map_name)
