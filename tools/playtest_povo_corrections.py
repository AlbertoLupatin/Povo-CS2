"""Walk the 26 October corrected standard map in a guarded solo CS2 session."""
import json
import math
from pathlib import Path
import re

try:
    from .playtest_povo_exterior import playtest
    from .cs2_console import run
    from .cs2_campus import world,UNITS
except ImportError:
    from playtest_povo_exterior import playtest
    from cs2_console import run
    from cs2_campus import world,UNITS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/gameplay/playtest-corrections'


def main():
    # This routine verifies the map name and one human/zero bots before moving.
    routes=[
        ('classroom_corridor_after_core',(33.5,31.35,4.1),[
            (24,31.35,4),(24,28.8,4),(24,12,4),(24,9.5,4),
            (29.5,9.5,4),(29.5,6.8,4),(29.5,9.5,4),(9,9.5,4),(9,6.8,4)]),
        ('aula_on_opposite_side',(24,31.35,4.1),[
            (24,69,4),(25,75,4),(11.4,74.75,4),(11.4,82.5,4.18),(-7.5,82.5,4)]),
        ('p2_stairs_down',(18.25,20,7.7),[
            (15.2,20,7.6),(15.2,19.35,7.6),(9.15,19.35,5.8),
            (9.15,22.65,5.8),(15.2,22.65,4),(17.8,22,4)]),
        ('p2_stairs_basement_down',(17.8,22,4.1),[
            (15.2,22,4),(15.2,19.35,4),(9.15,19.35,2.2),
            (9.15,22.65,2.2),(15.2,22.65,.4),(17.8,22,.4)]),
        ('p2_stairs_basement_up',(17.8,22,.5),[
            (15.2,22.65,.4),(9.15,22.65,2.2),(9.15,19.35,2.2),
            (15.2,19.35,4),(15.2,22,4),(17.8,22,4)]),
        ('p2_exit_stair_directly_after_door',(18.25,22,.5),[
            (18.6,27.5,.4),(48,27.5,.4),(55.5,27.5,4),(57.5,27.5,4)]),
        ('street_hole_towards_bridge',(54.5,-20,7.7),[
            (54.5,-13,7.6),(54.5,-5,7.6),(54.5,0,7.72),
            (54.5,7.5,5.92),(57.5,7.5,5.92),(57.5,15,4.12)])]
    package=ROOT/'build/package/pc/trento_povo_campus.vpk'
    result=playtest(routes=routes,output=OUT/'walk',package=package)
    metadata=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    checks=[];transcript=[]
    def cmd(commands,seconds=.4):
        if isinstance(commands,str):commands=[commands]
        response=run(commands,seconds=seconds)
        transcript.append('> '+'\n> '.join(commands)+'\n'+response)
        return response
    def position():
        matches=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',cmd('getpos_exact'))
        if not matches:raise RuntimeError('No player position')
        x,y,z=map(float,matches[-1]);return [y/UNITS,-x/UNITS,z/UNITS]
    def check(name,passed,**details):
        record=dict(name=name,passed=bool(passed),**details);checks.append(record);print(record,flush=True)
        if not passed:raise RuntimeError('Runtime correction failed: '+name)
    try:
        for name,spec in [('p1',metadata['levels'][0]['elevator']),('p2',metadata['povo2']['lift'])]:
            if not spec.get('enabled',True):continue
            lo,hi=spec['ladder'];axis=min(range(2),key=lambda i:hi[i]-lo[i])
            start=[(a+b)/2 for a,b in zip(lo,hi)];start[axis]=hi[axis]+.4072;start[2]=lo[2]+.1
            yaw=-90 if axis==0 else 0
            cmd(['-forward 42','sv_cheats 1','god 1','noclip 0','setpos '+world(start),f'setang -55 {yaw} 0'],.6)
            top=start
            for _ in range(18):
                cmd('+forward 42',.2);cmd('-forward 42',.2);top=position()
                if top[2]>7.75:break
            check(name+'_ladder_reaches_above_upper_ledge',top[2]>7.75,position=top)
            # Turn away from the ladder and step onto the supported ledge.
            cmd([f'setang 0 {yaw+180} 0','+forward 42'],.45);cmd('-forward 42',1)
            landed=position()
            check(name+'_ladder_dismounts_to_upper_floor',7.55<landed[2]<7.9,position=landed)
        glass_name='povo_glass_p2_ground_b112_window_glass'
        check('b112_glass_present',"'func_breakable'" in cmd('ent_find '+glass_name))
        cmd(['noclip 0','setpos '+world((14,47.5,4.1)),'setang 0 -90 0',
             'cmd give weapon_ak47','slot1'],1)
        cmd('+attack',.25);cmd('-attack')
        check('b112_glass_breaks_from_inside','Found 0 matches.' in cmd('ent_find '+glass_name))
        result['feature_status']='passed'
    finally:
        cmd(['-forward 42','-attack'])
        result['features']=checks
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'features.json').write_text(json.dumps(result,indent=2)+'\n')
        (OUT/'features.log').write_text('\n'.join(transcript))


if __name__=='__main__':main()
