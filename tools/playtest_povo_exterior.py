#!/usr/bin/env python3
"""Normal-walking checks for the compiled exterior, via CS2's local netconsole.

Requires the new package already loaded in solo exploration. Each independent
route has one starting placement; movement between waypoints uses normal walking.
No screenshots or Windows input injection are performed by this script.
"""
import json
import math
from pathlib import Path
import re
import time
try:
    from .cs2_console import run
    from .cs2_campus import world,UNITS
except ImportError:
    from cs2_console import run
    from cs2_campus import world,UNITS


def playtest():
    transcript=[];checks=[]
    def command(commands,seconds=.2):
        if isinstance(commands,str):commands=[commands]
        out=run(commands,seconds=seconds);transcript.append('> '+'\n> '.join(commands)+'\n'+out);return out
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
    routes=[
        ('p2_south_door_bank',(54,31.35,4.1),[(49,31.35,4),(34,31.35,4),(31.5,31.35,4)]),
        ('p2_north_door_bank',(54,35.65,4.1),[(49,35.65,4),(34,35.65,4),(31.5,35.65,4)]),
        ('straight_ramp_down',(-29,-3.5,3.1),[(-29,0,2.52),(-29,20,-1.3),(-29,33,-3.2)]),
        ('straight_ramp_up',(-29,33,-3.1),[(-29,20,-1.3),(-29,0,2.52),(-29,-3.5,3)]),
        ('garage_into_original_parking',(-29,36,-3.1),[(-5,36,-3.2),(18,36,-3.2),(18,27,-3.2),(17.8,22,-3.2)]),
        ('povo1_external_stairs',(22,-73.73,4.1),[(27,-73.73,4),(27,-79,4),(32,-79,4),(32,-71,5.8),(52,-71,5.8)])
    ]
    report={'status':'failed','checks':checks,'placement':'One initial placement per independent route; normal walking between all waypoints'}
    try:
        for name,start,points in routes:
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
        command('-forward 42')
        out=Path('build/gameplay');out.mkdir(exist_ok=True)
        (out/'exterior-runtime-walk.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'exterior-runtime-walk.log').write_text('\n'.join(transcript),encoding='utf-8')
    return report


if __name__=='__main__':playtest()
