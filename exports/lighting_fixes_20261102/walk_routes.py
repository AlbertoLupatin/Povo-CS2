"""Ordinary passage along both restored lamp bases, in both directions."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.playtest_povo_survey import Console,Driver,run_routes
from tools.cs2_project import discover_cs2_root

def main():
    work=ROOT/'build/lighting-fixes-20261102';out=Path(__file__).parent/'walking';out.mkdir(exist_ok=True)
    candidate=work/'candidate.vpk';digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    installed=discover_cs2_root()/'game/csgo_addons/trento_povo_lighting_review/maps/trento_povo_campus.vpk'
    assert hashlib.sha256(installed.read_bytes()).hexdigest()==digest
    paths=[('restored_lamp_0',[[56.25,14.5,4.12],[56.25,15.575,4.12],[56.25,17,4.12],[57.5,17,4.12]]),
           ('restored_lamp_1',[[56.25,27.7,4],[56.25,28.575,4],[56.25,29.5,4],[57.5,29.5,4]])]
    routes=[dict(name=name+('_return' if back else ''),kind='walk',category='lamp_repair',
        path=list(reversed(path)) if back else path,xy_tolerance=.025,
        timings=dict(broad_pulse_min=.012,broad_pulse_max=.25)) for name,path in paths for back in (False,True)]
    report=dict(status='failed',routes=[],package_sha256=digest,
        scope='Four ordinary standing walks beside the restored bases; one initial placement per route, noclip off and standard 25cm floor tolerance.')
    console=Console(27400);driver=Driver(console,'trento_povo_campus',timings=dict(stop_read=.2))
    try:run_routes(driver,routes,report,out)
    finally:
        driver.cleanup();console.close()
        (out/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'console.log').write_text('\n'.join(console.transcript),encoding='utf-8')
    assert report['status']=='passed'

if __name__=='__main__':main()
