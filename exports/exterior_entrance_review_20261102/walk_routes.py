"""Ordinary standing routes around the entrance correction and concrete fills."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.cs2_project import discover_cs2_root
from tools.playtest_povo_survey import Console,Driver,run_routes

def main():
    package=ROOT/'build/exterior-entrance-20261102/candidate.vpk'
    installed=discover_cs2_root()/'game/csgo_addons/trento_povo_entrance_review/maps/trento_povo_campus.vpk'
    digest=hashlib.sha256(package.read_bytes()).hexdigest()
    assert hashlib.sha256(installed.read_bytes()).hexdigest()==digest
    paths=[
        ('entrance_hall',[[28,28,4],[24,28,4],[24,22,4],[24,16,4],[24,9.5,4]]),
        ('stair_door',[[24,22,4],[21.5,22,4],[19.2,22,4]]),
        ('lower_stair_approach',[[43.8,7,-3.2],[43.8,4,-3.2],[43.8,1.2,-3.2]]),
        ('lower_garden',[[48,17,-3.2],[51,17,-3.2],[54.5,17,-3.2],[54.5,12,-3.2]]),
    ]
    meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    for stair in ('up','down'):
        paths.append(('exterior_stair_'+stair,meta['povo2']['gardens']['routes'][stair]))
    routes=[]
    for name,path in paths:
        for back in (False,True):routes.append(dict(name=name+('_return' if back else ''),kind='walk',category='p2_lower_stair' if name.startswith('exterior_stair') else 'entrance_fill',
            path=list(reversed(path)) if back else path,xy_tolerance=.025,timings=dict(broad_pulse_min=.012,broad_pulse_max=.25)))
    console=Console(27400);driver=Driver(console,'trento_povo_campus',timings=dict(stop_read=.2))
    out=Path(__file__).parent/'walking';out.mkdir(exist_ok=True)
    report=dict(status='failed',package_sha256=digest,routes=[],scope='One initial placement per route; ordinary standing walking, noclip off, 25 cm height tolerance')
    try:
        driver.guard()
        console.command(['sv_cheats 1','god 1','ent_fire stair_p2_internal_door_0_1 Open'],1.)
        run_routes(driver,routes,report,out)
    finally:
        driver.cleanup();console.close()
        (out/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'console.log').write_text('\n'.join(console.transcript),encoding='utf-8')
    assert report['status']=='passed'

if __name__=='__main__':main()
