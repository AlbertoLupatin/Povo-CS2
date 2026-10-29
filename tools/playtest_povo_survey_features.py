"""Guarded native feature checks for the current survey map.

No console calls happen on import or with --plan. The operator must serialize
this harness with other playtests. Bullets test glass; walking tests automatic
door sensors. A round restart checks that the broken panes return.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

try:
    from .cs2_console import run
    from .cs2_campus import UNITS, world
    from .cs2_explore import campus_loaded
except ImportError:
    from cs2_console import run
    from cs2_campus import UNITS, world
    from cs2_explore import campus_loaded

ROOT=Path(__file__).resolve().parents[1]
EYE=64/UNITS


def feature_plan(metadata):
    """Derive entities, floor heights and representative shots from provenance."""
    ground=min(l['floor_elevation_metres']-metadata['origin'][2] for l in metadata['levels'])
    panes=metadata['breakable_glass']
    shots=[]
    for label,name,inside in (
        ('a103_teaching_front','academic_ground_room_a103_window_glass','north'),
        ('acquario_corridor','academic_ground_acquario_corridor_glass_1','west'),
        ('library_glazing','library_0_west_glass_0','west')):
        family=[p for p in panes if p.get('source_facet',p['name'])==name]
        if not family:raise ValueError('Missing glazing facet '+name)
        eligible=[p for p in family if p['lo'][2]+.08<ground+1.45<p['hi'][2]-.08]
        if inside=='north':pane=max(eligible,key=lambda p:p['hi'][0])
        else:
            middle=(min(p['lo'][1] for p in family)+max(p['hi'][1] for p in family))/2
            pane=min(eligible,key=lambda p:abs((p['lo'][1]+p['hi'][1])/2-middle))
        lo,hi=pane['lo'],pane['hi']
        centre=[(a+b)/2 for a,b in zip(lo,hi)]
        target=[*centre[:2],ground+1.45]
        if inside=='north':
            target[0]=(lo[0]+hi[0])/2
            start=[target[0],centre[1]+1.25,ground+.25]
        else:start=[centre[0]-1.25,centre[1],ground+.1]
        siblings=[p for p in family if p['name']!=pane['name']]
        neighbor=min(siblings,key=lambda p:math.dist([(a+b)/2 for a,b in zip(p['lo'],p['hi'])],centre)) if siblings else None
        shots.append(dict(id=label,targetname='povo_glass_'+pane['name'],start=start,target=target,
                          neighbor='povo_glass_'+neighbor['name'] if neighbor else None))
    doors=[]
    for name in ('p1_entry_bank_0','p2_entry_outer_bank_0','library_entry_bank_0'):
        door=next(d for d in metadata['auto_doors'] if d['name']==name)
        lo,hi=door['trigger'];plane=sum(p['lo'][0]+p['hi'][0] for p in door['parts'])/(2*len(door['parts']))
        y=(lo[1]+hi[1])/2
        floors=[l['floor_elevation_metres']-metadata['origin'][2] for l in metadata['levels']]
        sill=min(p['lo'][2] for p in door['parts'])
        floor=min(floors,key=lambda z:abs(z-sill))
        z=floor+.35  # settle onto the landing/first tread outside the sensor
        # Start outside the sensor and cross naturally, without native Open inputs.
        doors.append(dict(id=name,targetname='trento_door_'+name,
                          start=[hi[0]+.5,y,z],target=[plane-1.0,y,z],plane=plane,floor=floor))
    return dict(shots=shots,doors=doors,
                expected_glass=len(metadata['breakable_glass'])+len(metadata['interactions']['glass']),
                expected_doors=len(metadata['interactions']['doors'])+sum(len(d['parts']) for d in metadata['auto_doors']))


def playtest(*,port=27400,output=None,map_name='trento_povo_campus',package=None,capture_screenshots=False):
    metadata=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    plan=feature_plan(metadata)
    output=Path(output or ROOT/'build/gameplay/survey-features');output.mkdir(parents=True,exist_ok=True)
    package=Path(package or ROOT/'build/package'/f'{map_name}.vpk')
    report=dict(status='failed',map=map_name,started_at_utc=datetime.now(timezone.utc).isoformat(),
                package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
                package_identity_scope='On-disk package hash; live status checks map name, not loaded bytes',
                plan=plan,checks=[])
    transcript=[];changed=False
    def cmd(commands,seconds=.3):
        if isinstance(commands,str):commands=[commands]
        text=run(commands,port=port,seconds=seconds)
        transcript.append('> '+'\n> '.join(commands)+'\n'+text)
        return text
    def guard():
        status=cmd('status')
        if not campus_loaded(status,map_name) or not re.search(r'players\s*:\s*1 humans, 0 bots\b',status):
            raise RuntimeError('Matching map with exactly one human and zero bots required')
    def check(name,passed,**details):
        record=dict(name=name,passed=bool(passed),**details);report['checks'].append(record)
        print(record,flush=True)
        if not passed:raise RuntimeError('Feature check failed: '+name)
    def position():
        matches=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',cmd('getpos_exact'))
        if not matches:raise RuntimeError('Player position unavailable')
        x,y,z=map(float,matches[-1]);return [y/UNITS,-x/UNITS,z/UNITS]
    def place(point):
        cmd(['-forward 42','-attack','sv_cheats 1','god 1','noclip 0','gameui_hide','setpos '+world(point)],.6)
    try:
        guard()
        check('native_glass_count',len(re.findall(r"'func_breakable' :",cmd('ent_find func_breakable')))==plan['expected_glass'],expected=plan['expected_glass'])
        check('native_door_count',len(re.findall(r"'func_door(?:_rotating)?' :",cmd('ent_find func_door')))==plan['expected_doors'],expected=plan['expected_doors'])
        changed=True
        for door in plan['doors']:
            guard();place(door['start'])
            # Exploration may leave every bank open. Reset only this bank while
            # outside its sensor; subsequent opening must come from the trigger.
            cmd('ent_fire '+door['targetname']+' Close',1.2)
            cmd('setang 0 -90 0')
            # Short pulses stop on the near side of the far sensor edge.
            for _ in range(12):
                cmd('+forward 42',.12);cmd('-forward 42',.12)
                p=position()
                if p[0]<door['plane']-.55:break
            check(door['id']+'_sensor_opens_for_walking',p[0]<door['plane']-.55 and abs(p[2]-door['floor'])<.3,position=p)
        for shot in plan['shots']:
            guard()
            check(shot['id']+'_present',"'func_breakable'" in cmd('ent_find '+shot['targetname']))
            place(shot['start']);p=position();target=shot['target']
            dx,dy=target[0]-p[0],target[1]-p[1]
            yaw=math.degrees(math.atan2(dx,-dy))
            pitch=-math.degrees(math.atan2(target[2]-p[2]-EYE,math.hypot(dx,dy)))
            cmd(['cmd give weapon_ak47','slot1',f'setang {pitch:.4f} {yaw:.4f} 0'],.7)
            if capture_screenshots:cmd('png_screenshot tile_before_'+shot['id'],.6)
            for _ in range(3):
                cmd('+attack',.22);cmd('-attack',.3)
                found=cmd('ent_find '+shot['targetname'])
                if 'Found 0 matches.' in found:break
            check(shot['id']+'_breaks_from_bullets','Found 0 matches.' in found,position=p,yaw=yaw,pitch=pitch)
            if shot['neighbor']:
                check(shot['id']+'_neighbor_tile_stays_intact',"'func_breakable'" in cmd('ent_find '+shot['neighbor']))
            if capture_screenshots:cmd('png_screenshot tile_after_'+shot['id'],.6)
        guard();cmd(['mp_warmup_end','mp_restartgame 1'],4)
        guard()
        for shot in plan['shots']:
            check(shot['id']+'_restored_next_round',"'func_breakable'" in cmd('ent_find '+shot['targetname']))
        report['status']='passed'
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        if changed:
            try:cmd(['-forward 42','-attack'])
            except OSError as error:report['cleanup_error']=str(error);report['status']='failed'
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (output/'features.json').write_text(json.dumps(report,indent=2)+'\n')
        (output/'features.log').write_text('\n'.join(transcript),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',action='store_true',help='Print metadata-derived test plan without connecting to CS2')
    parser.add_argument('--screenshots',action='store_true',help='Capture the selected tile before and after each bullet check')
    parser.add_argument('--port',type=int,default=27400)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--package',type=Path)
    args=parser.parse_args()
    if args.plan:print(json.dumps(feature_plan(json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())),indent=2))
    else:playtest(port=args.port,output=args.output,package=args.package,capture_screenshots=args.screenshots)
