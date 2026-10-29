#!/usr/bin/env python3
"""Controlled local 2v2 bot regression checks, using native CS2 game rules.

Teleports and a temporary pawn team change isolate objective mechanics from
route timing. This checks buying, legal planting, defusing and elimination;
it does not establish competitive balance or independent-client replication.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,re
from pathlib import Path
try:
    from .cs2_console import run
    from .cs2_campus import world, gameplay_points
    from .cs2_explore import campus_loaded,explore
except ImportError:
    from cs2_console import run
    from cs2_campus import world, gameplay_points
    from cs2_explore import campus_loaded,explore
ROOT=Path(__file__).resolve().parents[1]


def match_plan(metadata):
    t,ct,objective=gameplay_points(metadata)
    ground=t[0][2]-.8;upper=objective[2]-.6
    # Existing audited outdoor spawn supplies an actually supported off-site pose.
    outside=next(s['point'] for s in metadata['deathmatch_spawns'] if s['area']=='exterior_surface_parking')
    return dict(terrorist_buy=[sum(p[0] for p in t)/len(t),sum(p[1] for p in t)/len(t),ground+.12],
                counterterrorist_buy=[sum(p[0] for p in ct)/len(ct),sum(p[1] for p in ct)/len(ct),upper+.12],
                outside=[outside[0],outside[1],outside[2]+.12],
                plant=[objective[0],objective[1],upper+.12],
                defuse=[objective[0],objective[1]-.9,upper+.12])


def playtest(season='standard',port=27400,output=None,package=None):
    name='trento_povo_campus'+('_winter' if season=='winter' else '')
    out=Path(output or ROOT/'build/gameplay/survey-match');out.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    plan=match_plan(metadata)
    package=Path(package or ROOT/'build/package'/(name+'.vpk'))
    transcript=[];checks=[];changed=False
    report=dict(status='failed',map=name,checks=checks,started_at_utc=datetime.now(timezone.utc).isoformat(),
        package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),plan=plan,
        package_identity_scope='On-disk package hash; live status checks map name, not loaded bytes',
        scope='Local 2v2 with three bots; controlled placements and temporary roster team change for the isolated defuse check')
    def cmd(c,seconds=.5):
        if isinstance(c,str):c=[c]
        r=run(c,port=port,seconds=seconds);transcript.append('> '+'\n> '.join(c)+'\n'+r);return r
    def check(n,ok,**details):
        checks.append(dict(name=n,passed=bool(ok),**details));print(checks[-1],flush=True)
        if not ok:raise RuntimeError('Match check failed: '+n)
    def guard(bot_count=None):
        status=cmd('status')
        roster=re.search(r'players\s*:\s*(\d+) humans, (\d+) bots\b',status)
        if not campus_loaded(status,name) or not roster or int(roster[1])!=1 or not 0<=int(roster[2])<=3 or (bot_count is not None and int(roster[2])!=bot_count):
            raise RuntimeError('Matching local map with one human and only the temporary test bots required')
        return status
    def pose(p,pitch=0,yaw=0):
        guard(3)
        cmd(['-attack','-use','-forward 42','setpos '+world(p),f'setang {pitch} {yaw} 0'],.5)
        # A cheat teleport can leave cached buy/bomb trigger contacts unchanged
        # while the pawn is stationary. Simulate movement, then restore the
        # exact pose within the same region before testing ordinary game rules.
        cmd('+forward 42',.22);cmd('-forward 42',.25)
        cmd('setpos '+world(p),.4)
    def teams(human_team):
        guard()
        cmd(['bot_quota 0','bot_kick','bot_stop 1',
             'mp_respawn_on_death_ct 0','mp_respawn_on_death_t 0'],2)
        cmd(['cmd jointeam '+str(human_team),'mp_restartgame 1'],3)
        # Fill mode counts the human in its total. Let the native manager
        # allocate both teams instead of racing asynchronous bot_add requests.
        cmd(['bot_join_team any','bot_quota_mode fill','bot_quota 4','bot_stop 1'],4)
        status=cmd('status')
        check('two_versus_two_'+str(human_team),bool(re.search(r'players\s*:\s*1 humans, 3 bots',status)))
    try:
        guard(0)
        changed=True
        cmd(['log on','mp_logmoney 1','sv_cheats 1','mp_autoteambalance 0','mp_limitteams 0',
             'mp_warmup_offline_enabled 0','mp_warmup_pausetimer 0','mp_warmup_end',
             'mp_respawn_on_death_ct 0','mp_respawn_on_death_t 0','mp_ignore_round_win_conditions 0',
             'mp_freezetime 0','mp_roundtime_defuse 60','mp_startmoney 8000','mp_buytime 3600',
             'mp_buy_anywhere 0','mp_plant_c4_anywhere 0','mp_c4timer 40','god 1','noclip 0'])
        teams(2)
        pose(plan['terrorist_buy']);r=cmd('buy ak47',1)
        check('terrorist_buyzone_purchase','purchased "ak47"' in r or 'purchase: weapon_ak47' in r)
        pose(plan['outside']);r=cmd('buy awp',1)
        check('audited_outdoor_point_is_outside_buyzone','purchase: weapon_awp' not in r and 'purchased "awp"' not in r)
        # Netconsole server commands lack a player context. Forward through the
        # local client so GiveNamedItem targets the actual human pawn.
        cmd('ent_fire weapon_c4 Kill',.6)
        r=cmd('cmd give weapon_c4',.8)
        check('controlled_c4_assigned','Got_The_Bomb' in r)
        cmd('slot5',.8)
        cmd('+attack',4.3);cmd('-attack')
        check('plant_rejected_outside_site','Found 0 matches.' in cmd('ent_find planted_c4'))
        pose(plan['plant']);cmd('slot5',.8)
        r=cmd('+attack',4.5);cmd('-attack')
        check('plant_at_site_a','Planted_The_Bomb' in r)
        # A normal mid-round join is queued until the next round. For this
        # isolated mechanic check change the pawn's team with a native input.
        # ent_fire is a server-only command; unlike give, it cannot be sent
        # through `cmd`. Only this local human and the test bots exist here.
        guard(3)
        cmd(['mp_respawn_on_death_ct 1','mp_respawnwavetime_ct 0',
             'ent_fire cs_player_controller ChangeTeam 3','ent_fire player ChangeTeam 3'],2)
        cmd('cmd give item_defuser',.5)
        pose(plan['defuse'],62,180)
        r=cmd('+use',7);cmd('-use')
        check('native_bomb_defuse','Defused_The_Bomb' in r or 'Bomb_Defused' in r)
        teams(3)
        pose(plan['counterterrorist_buy']);r=cmd('buy m4a1',1)
        check('counterterrorist_buyzone_purchase','purchased ' in r and ('m4a1' in r or 'm4a4' in r))
        guard(3)
        r=cmd('bot_kill all',3)
        check('elimination_round_win','CTs_Win' in r or 'won by ELIMINATION' in r)
        cmd(['bot_stop 0','bot_dont_shoot 0','mp_restartgame 1'],12)
        check('normal_bot_round_running',bool(re.search(r'1 humans, 3 bots',cmd('status'))))
        report['status']='passed'
    except Exception as e:report['error']=str(e);raise
    finally:
        if changed:
            try:
                cmd(['-attack','-use','-forward 42'])
                guard()
                cmd(['-attack','-use','-forward 42','bot_mimic 0','bot_stop 0','bot_dont_shoot 0',
                     'mp_c4timer 40','mp_buytime 20','mp_roundtime_defuse 1.5','mp_logmoney 0'])
                explore(port=port,map_name=name,timeout=20)
            except (OSError,RuntimeError) as e:report['cleanup_error']=str(e);report['status']='failed'
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (out/'survey-match.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'survey-match.log').write_text('\n'.join(transcript),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--season',choices=('standard','winter'),default='standard')
    p.add_argument('--port',type=int,default=27400)
    p.add_argument('--output',type=Path)
    p.add_argument('--package',type=Path)
    p.add_argument('--plan',action='store_true',help='Print source-derived poses without contacting CS2')
    a=p.parse_args()
    if a.plan:print(json.dumps(match_plan(json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())),indent=2))
    else:playtest(a.season,a.port,a.output,a.package)
