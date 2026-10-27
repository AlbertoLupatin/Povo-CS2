#!/usr/bin/env python3
"""Check native free-for-all in a solo CS2 Deathmatch session.

Launch first with `play_campus.cmd -Deathmatch`. The check reads the mode and
the convars the map script sets, counts the Deathmatch spawn entities, then
respawns repeatedly and requires every respawn on an authored campus spawn.
"""
import json
import math
from pathlib import Path
import re
import socket
import time

try:
    from .cs2_console import run
    from .cs2_campus import UNITS
    from .cs2_explore import campus_loaded
except ImportError:
    from cs2_console import run
    from cs2_campus import UNITS
    from cs2_explore import campus_loaded

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/gameplay/ffa'
EXPECTED={'game_type':'1','game_mode':'2','mp_teammates_are_enemies':'true',
          'mp_randomspawn':'1','mp_randomspawn_los':'true','bot_quota':'0'}


def main(*,respawns=12,timeout=240):
    spawns=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())['deathmatch_spawns']
    transcript=[];checks=[]
    def cmd(commands,seconds=.4):
        if isinstance(commands,str):commands=[commands]
        out=run(commands,seconds=seconds);transcript.append('> '+'\n> '.join(commands)+'\n'+out);return out
    def check(name,passed,**details):
        record=dict(name=name,passed=bool(passed),**details);checks.append(record);print(record,flush=True)
        if not passed:raise RuntimeError('Free-for-all check failed: '+name)
    def position():
        found=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',cmd('getpos_exact'))
        if not found:return None
        x,y,z=map(float,found[-1]);return [y/UNITS,-x/UNITS,z/UNITS]
    def nearest(point):
        return min(spawns,key=lambda s:math.dist(s['point'][:2],point[:2]))
    try:
        deadline=time.monotonic()+timeout
        while True:
            try:
                status=cmd('status',.3)
                if campus_loaded(status):break
            except (OSError,socket.timeout):pass
            if time.monotonic()>deadline:raise RuntimeError('Campus did not load in Deathmatch')
            time.sleep(1)
        # The script applies its settings on activation and round start.
        time.sleep(3)
        for name,value in EXPECTED.items():
            found=re.findall(r'^\s*'+re.escape(name)+r'\s*=\s*(\S+)',cmd(name),re.M)
            actual=found[-1].strip('"').lower() if found else None
            if value in ('true','false') and actual in ('1','0'):actual='true' if actual=='1' else 'false'
            check('convar_'+name,actual==value,actual=actual,expected=value)
        listed=cmd('ent_find info_deathmatch_spawn',1)
        found=re.search(r'Found (\d+) match',listed)
        count=int(found[1]) if found else len(re.findall(r"'info_deathmatch_spawn'",listed))
        check('deathmatch_spawn_entities',count>=len(spawns),count=count,authored=len(spawns))
        cmd(['sv_cheats 1','jointeam 2 1'],2)
        seen=[]
        for i in range(respawns):
            cmd('kill',.3);time.sleep(4.5)
            point=position()
            if point is None:raise RuntimeError('No player position after respawn')
            spawn=nearest(point);gap=math.dist(spawn['point'][:2],point[:2])
            check(f'respawn_{i}_on_authored_spawn',gap<.75 and abs(point[2]-spawn['point'][2])<.5,
                  position=[round(v,3) for v in point],spawn=spawn['id'],area=spawn['area'],gap=round(gap,3))
            seen.append(spawn['id'])
        check('respawns_use_several_spawns',len(set(seen))>=min(respawns,6),distinct=sorted(set(seen)))
        status='passed'
    except Exception as error:
        status='failed';checks.append(dict(name='error',passed=False,detail=str(error)));raise
    finally:
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'report.json').write_text(json.dumps(dict(status=status,checks=checks),indent=2)+'\n')
        (OUT/'transcript.txt').write_text('\n'.join(transcript),encoding='utf-8')


if __name__=='__main__':main()
