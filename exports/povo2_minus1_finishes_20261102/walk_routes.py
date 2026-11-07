"""Ordinary movement through furnished offices and the empty left doorway."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.playtest_povo_survey import Console,Driver

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',help='Run one named route in both directions')
    parser.add_argument('--report',default='native-walking.json')
    args=parser.parse_args()
    base=Path(__file__).parent;meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    p2=meta['povo2'];console=Console(27400);driver=Driver(console,'trento_povo_campus',timings=dict(stop_read=.2))
    report=dict(status='failed',routes=[],entities=[],
        movement='One initial placement per route; ordinary standing movement thereafter',
        xy_tolerance_metres=.025)
    names={'west_W01_entry','west_W02_entry','west_W04_entry','west_W10_entry','west_W19_entry',
           'cibio_office_0_entrance','cibio_office_1_entrance','c7_to_empty_wi2_door'}
    if args.only:
        if args.only not in names:raise ValueError('Unknown route')
        names={args.only}
    selected=[r for r in p2['basement_rebuild']['routes'] if r['id'] in names]
    if {r['id'] for r in selected}!=names:raise RuntimeError('Missing expected walking routes')
    try:
        driver.guard()
        for pane in meta['breakable_glass']:
            if not pane['name'].startswith('p2_basement_fitout_'):continue
            name='povo_glass_'+pane['name'];found=console.command('ent_find '+name,.1)
            passed="'func_breakable'" in found
            report['entities'].append(dict(name=name,passed=passed))
            if not passed:raise RuntimeError('Missing compiled glass entity '+name)
        for i in range(6):
            for j in range(2):
                name=f'p2_cibio_terrace_{i}_{j}';found=console.command('ent_find '+name,.1)
                passed='Found 0 matches.' in found
                report['entities'].append(dict(name=name,passed=passed,expected='No moving door entity'))
                if not passed:raise RuntimeError('A terrace door can still move: '+name)
        for d in p2['repair_doors']:
            if d['id'].startswith('p2_west_'):console.command('ent_fire '+d['id']+' Open',.02)
        console.command(['sv_cheats 1','god 1'],1.)
        for route in selected:
            for back in (False,True):
                name=route['id']+('_return' if back else '')
                path=list(reversed(route['points'])) if back else route['points']
                checks=driver.execute(dict(name=name,kind='walk',category='p2_basement_route',path=path,
                    xy_tolerance=.025,timings=dict(broad_pulse_min=.012,broad_pulse_max=.25)))
                report['routes'].append(dict(id=name,status='passed',checks=checks))
                print(name,'passed',flush=True)
        report['status']='passed'
    except Exception as e:
        report['error']=str(e);raise
    finally:
        try:driver.cleanup()
        finally:
            console.close()
            report['package_sha256']=hashlib.sha256((ROOT/'build/minus1-finishes-20261102/candidate.vpk').read_bytes()).hexdigest()
            (base/args.report).write_text(json.dumps(report,indent=2)+'\n')
            (ROOT/'build/minus1-finishes-20261102'/Path(args.report).with_suffix('.log').name).write_text('\n'.join(console.transcript),encoding='utf-8')

if __name__=='__main__':main()
