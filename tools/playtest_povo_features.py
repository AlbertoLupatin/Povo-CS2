#!/usr/bin/env python3
"""Check native door collision, bullet breakage and round restoration in solo CS2.

The loaded map must match --season with exactly one human and zero bots. Tests
temporarily move the player and operate the selected doors via native inputs.
Use the separate exterior walking audit to validate complete campus routes.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import re

try:
    from .cs2_console import run
    from .cs2_campus import UNITS,world
    from .cs2_explore import campus_loaded,explore
except ImportError:
    from cs2_console import run
    from cs2_campus import UNITS,world
    from cs2_explore import campus_loaded,explore

ROOT=Path(__file__).resolve().parents[1]


def playtest(*,season='standard',port=27400,output=None):
    map_name='trento_povo_campus'+('_winter' if season=='winter' else '')
    output=Path(output or ROOT/f'exports/povo_campus/runtime/atmosphere/{season}')
    output.mkdir(parents=True,exist_ok=True)
    transcript=[];checks=[];changed=False
    package=ROOT/'build/package'/(map_name+'.vpk')
    report=dict(status='failed',map=map_name,checks=checks,
                package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
                started_at_utc=datetime.now(timezone.utc).isoformat())
    def cmd(commands,seconds=.4):
        if isinstance(commands,str):commands=[commands]
        text=run(commands,port=port,seconds=seconds)
        transcript.append('> '+'\n> '.join(commands)+'\n'+text)
        return text
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        print(checks[-1],flush=True)
        if not passed:raise RuntimeError('Native feature check failed: '+name)
    def position():
        text=cmd('getpos_exact')
        matches=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',text)
        if not matches:raise RuntimeError('No player position')
        x,y,z=map(float,matches[-1]);return [y/UNITS,-x/UNITS,z/UNITS]
    def pose(point,yaw):
        cmd(['-forward 42','-attack','sv_cheats 1','god 1','noclip 0','slot3',
             'gameui_hide','setpos '+world(point),f'setang 0 {yaw} 0'],.6)
    def input_names(names,action):cmd([f'ent_fire {n} {action}' for n in names],1.2)
    def cross(name,names,start,yaw,axis,plane,direction):
        pose(start,yaw);input_names(names,'Close');input_names(names,'Lock')
        cmd('+forward 42',.8);cmd('-forward 42');closed=position()
        check(name+'_closed_blocks',direction*(closed[axis]-plane)<-.30,position=closed)
        pose(start,yaw);input_names(names,'Unlock');input_names(names,'Open')
        cmd('+forward 42',.65);cmd('-forward 42');opened=position()
        check(name+'_open_passes',direction*(opened[axis]-plane)>.45 and abs(opened[2]-start[2])<.3,
              position=opened)
    try:
        status=cmd('status')
        if not campus_loaded(status,map_name) or not re.search(r'players\s*:\s*1 humans, 0 bots\b',status):
            raise RuntimeError('Matching solo exploration required; no player changes were made')
        changed=True
        spec=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())['interactions']
        found=cmd('ent_find func_door')
        count=len(re.findall(r"'func_door(?:_rotating)?' :",found))
        check('all_native_doors_spawned',count==len(spec['doors']),expected=len(spec['doors']),actual=count)
        cross('p1_fire_pair',['p1_se_floor0_south','p1_se_floor0_north'],(14.3,-85.1,4.1),90,0,15.81,1)
        cross('p2_sliding_pair',['p2_entry_outer_0_-1','p2_entry_outer_0_1'],(51,31.35,4.1),-90,0,49.4,-1)
        cross('p1_entrance_pair',['p1_main_south','p1_main_north'],(22.5,-73.7294686,4.1),90,0,24,1)
        classroom=next(d for d in spec['doors'] if d['id']=='classroom_a224')
        lo,hi=classroom['bounds'];e=(lo[0]+hi[0])/2;n=(lo[1]+hi[1])/2
        cross('classroom_a224',['classroom_a224'],(e+1.5,n,7.7),-90,0,e,-1)
        for pane in spec['glass']:
            lo,hi=pane['bounds'];e=(lo[0]+hi[0])/2;n=(lo[1]+hi[1])/2
            pose((e-1.25,n,4.1),90)
            cmd(['cmd give weapon_ak47','slot1'],.7)
            cmd('+attack',.22);cmd('-attack')
            result=cmd('ent_find '+pane['id'])
            check(pane['id']+'_breaks_from_bullets','Found 0 matches.' in result)
        cmd(['mp_warmup_end','mp_restartgame 1'],4)
        for pane in spec['glass']:
            result=cmd('ent_find '+pane['id'])
            check(pane['id']+'_restored_next_round',"'func_breakable'" in result)
        check('doors_restored_next_round',len(re.findall(r"'func_door(?:_rotating)?' :",cmd('ent_find func_door')))==len(spec['doors']))
        for name,point,event in [('garage',(-20,60,-3.1),'Povo.Garage'),
                                  ('classroom',(-18,-47,7.7),'Povo.Room'),
                                  ('street',(62,-70,5.9),'Povo.Winter' if season=='winter' else 'Povo.Outside')]:
            pose(point,90);cmd('cl_soundscape_printdebuginfo',3.5)
            transcript.append('Expected natural zone at '+name+': '+event)
            cmd('soundscape_dumpclient')
        if season=='winter':
            found=cmd('ent_find winter_snow')
            count=len(re.findall(r"'info_particle_system' :",found))
            check('winter_snow_emitters_spawned',count>0,count=count)
        report['status']='passed'
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        if changed:
            try:
                cmd(['-forward 42','-attack','ent_fire func_door Unlock',
                     'ent_fire func_door_rotating Unlock','ent_fire func_door Open','ent_fire func_door_rotating Open'])
                explore(port=port,map_name=map_name,timeout=15)
                pose((24.7,-73.73,4.1),90)
            except (OSError,RuntimeError) as error:
                report['cleanup_error']=str(error);report['status']='failed'
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (output/'native-features.json').write_text(json.dumps(report,indent=2)+'\n')
        (output/'native-features.log').write_text('\n'.join(transcript),encoding='utf-8')
    if report['status']!='passed':raise RuntimeError('Feature test cleanup failed')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season',choices=('standard','winter'),default='standard')
    parser.add_argument('--port',type=int,default=27400)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();playtest(season=args.season,port=args.port,output=args.output)
