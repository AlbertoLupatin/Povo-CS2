"""Verify the repaired campus in an already loaded, guarded solo session."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import time
from .cs2_project import discover_cs2_root
from .cs2_campus import world
from .cs2_console import run
from .cs2_explore import explore, campus_loaded
from .playtest_povo_survey import Console, Driver

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/povo2_walkthrough_20261029/runtime'


def main(reload=False):
    OUT.mkdir(parents=True,exist_ok=True)
    package=ROOT/'build/package/trento_povo_campus.vpk'
    metadata=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    cs2=discover_cs2_root()
    status=run(['status'],seconds=.4)
    if not campus_loaded(status) or not re.search(r'players\s*:\s*1 humans, 0 bots\b',status):
        raise RuntimeError('Requires the expected campus map with exactly one human and zero bots')
    if reload:
        # Reload only after the solo guard passes. Release the old mounted map
        # before replacing its test package; never terminate the user's game.
        run(['disconnect'],seconds=2)
        destination=cs2/'game/csgo_addons/trento_povo_campus_test/maps/trento_povo_campus.vpk'
        shutil.copy2(package,destination)
        run(['map maps/trento_povo_campus.vpk'],seconds=1)
        explore(timeout=90)
    console=Console(27400);driver=Driver(console,'trento_povo_campus')
    report=dict(status='failed',package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        checks=[],routes=[])
    def check(name,passed,**details):
        item=dict(name=name,passed=bool(passed),**details);report['checks'].append(item)
        print(item,flush=True)
        if not passed:raise RuntimeError(name)
    def cmd(commands,seconds=.3):return console.command(commands,seconds)
    try:
        driver.guard()
        cmd(['sv_cheats 1','god 1','engine_no_focus_sleep 0','fps_max 60'])
        doors=metadata['povo2']['repair_doors']
        for door in doors:
            found=cmd('ent_find '+door['id'],.08)
            check(door['id']+'_exists',"'func_door_rotating'" in found)
            cmd('ent_fire '+door['id']+' Open',.05)
        panes=[p for p in metadata['breakable_glass'] if p['name'].startswith('p2_basement_')]
        for pane in panes:
            found=cmd('ent_find povo_glass_'+pane['name'],.08)
            check(pane['name']+'_breakable_entity',"'func_breakable'" in found)
        # Lock and push against a closed leaf pair, then open and walk through.
        for token in ('c5_terrace','wi1_public','c7_exit','west_W07','cibio_terrace_0','garden_exit'):
            driver.guard()
            pair=[d for d in doors if d['id'] in ('p2_'+token+'_0','p2_'+token+'_1')]
            a=pair[0]['bounds'][0];b=pair[-1]['bounds'][1]
            centre=[(x+y)/2 for x,y in zip(a,b)];centre[2]=.4
            axis=0 if b[0]-a[0]<b[1]-a[1] else 1
            start=list(centre);start[axis]+=1.3
            target=list(centre);target[axis]-=1.3
            yaw=-90 if axis==0 else 0
            driver.place(start)
            for d in pair:cmd(['ent_fire '+d['id']+' Close','ent_fire '+d['id']+' Lock'],.12)
            cmd([],1)
            console.pulse([f'setang 0 {yaw} 0','+forward 42'],.65)
            p=driver.position()
            check(token+'_closed_blocks',p[axis]>centre[axis]+.25,position=p)
            for d in pair:cmd(['ent_fire '+d['id']+' Unlock','ent_fire '+d['id']+' Open'],.12)
            cmd([],1)
            driver.place(start);driver.walk(target,xy_tolerance=.2)
            check(token+'_open_passes',True)
        selected=[*metadata['povo2']['west_offices']['routes'],
                  *[r for r in metadata['povo2']['basement_rebuild']['routes'] if
                    r['id'].startswith(('terrace_to_','garden_to_c5','cibio_terrace_exit_','c5_to_exit_corridor'))]]
        for route in selected:
            driver.guard()
            r=dict(name=route['id'],kind='walk',category='p2_basement_route',path=route['points'],xy_tolerance=.2)
            driver.execute(r);report['routes'].append(dict(id=route['id'],status='passed',checks=driver.checks))
            print('walked '+route['id'],flush=True)
        for prefix in ('p2_basement_west_glazing_','p2_basement_repair_cibio_terrace_glass'):
            driver.guard()
            pane=next(p for p in panes if p['name'].startswith(prefix)
                and max(p['hi'][i]-p['lo'][i] for i in (0,1))>1.4)
            lo,hi=pane['lo'],pane['hi'];axis=0 if hi[0]-lo[0]<hi[1]-lo[1] else 1
            target=[(a+b)/2 for a,b in zip(lo,hi)];start=target[:];start[axis]-=1.2;start[2]=.4
            # Pick the corridor side of a W office front.
            if prefix.startswith('p2_basement_west') and axis==1 and target[1]<9:start[1]=target[1]+1.1
            driver.place(start)
            dx,dy=target[0]-start[0],target[1]-start[1]
            yaw=math.degrees(math.atan2(dx,-dy))
            pitch=-math.degrees(math.atan2(target[2]-(start[2]+1.6256),math.hypot(dx,dy)))
            # Let the rifle finish deploying; a 0.18 s tap registered no hit natively.
            cmd(['cmd give weapon_ak47','slot1',f'setang {pitch} {yaw} 0'],1.5)
            cmd('+attack',.8);cmd('-attack',.4)
            found=cmd('ent_find povo_glass_'+pane['name'])
            check(prefix+'_breaks_from_bullets','Found 0 matches.' in found,pane=pane['name'])
        shots=[('arrival',(22,2.8,.4),(0,180,0)),
               ('c7_stair_connection',(22,16.6,.4),(0,-90,0)),
               ('c5_sealed_door',(22,14.5,.4),(0,180,0)),
               ('c7_exit_door',(22,16.8,.4),(0,90,0)),
               ('gardens',(34.5,6,2.2),(-5,0,0)),
               ('ground_former_shaft',(24,19.4,4),(20,0,0)),
               ('stair_guards',(19.2,19.1,4),(35,-90,0)),
               ('cibio_terrace',(-3.05,24,.4),(0,90,0))]
        for name,point,angles in shots:
            driver.guard();cmd(['noclip 1','setpos '+world(point),
                'setang '+' '.join(map(str,angles)),'cl_drawhud 0','r_drawviewmodel 0'],.5)
            cmd('png_screenshot walkthrough_'+name,1.2)
            files=list((cs2/'game/csgo_addons/trento_povo_campus_test/screenshots').glob('walkthrough_'+name+'*'))
            if not files:files=list((cs2/'game/csgo/screenshots').glob('walkthrough_'+name+'*'))
            if files:shutil.copy2(max(files,key=lambda p:p.stat().st_mtime),OUT/(name+'.png'))
        report['status']='passed'
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        try:
            driver.guard()
            cmd(['-attack','-forward 42','-sprint 42','cl_drawhud 1','r_drawviewmodel 1','noclip 0'])
            for door in metadata['povo2']['repair_doors']:cmd('ent_fire '+door['id']+' Unlock',.01)
            driver.place([22,7.8,.4]);cmd('setang 0 180 0')
        finally:
            (OUT/'native-checks.json').write_text(json.dumps(report,indent=2)+'\n')
            (OUT/'console.log').write_text('\n'.join(console.transcript),encoding='utf-8')
            console.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reload',action='store_true')
    main(parser.parse_args().reload)
