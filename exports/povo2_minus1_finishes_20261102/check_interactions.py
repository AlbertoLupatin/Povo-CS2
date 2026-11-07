"""Native collision and bullet checks for the new wall and glazing finishes."""
from pathlib import Path
import hashlib,json,math,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.playtest_povo_survey import Console,Driver


def main():
    base=Path(__file__).parent
    meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())
    console=Console(27400);driver=Driver(console,'trento_povo_campus')
    report=dict(status='failed',checks=[])
    def check(name,passed,**details):
        report['checks'].append(dict(name=name,passed=bool(passed),**details))
        print(name,passed,flush=True)
        if not passed:raise RuntimeError(name)
    try:
        driver.guard()
        # Push against the middle of every fixed pair from both sides. The
        # starting placement is followed only by ordinary standing movement.
        for i in range(6):
            for sign in (-1,1):
                driver.guard();driver.place([-2.3+sign,22.025+i*3,.4])
                console.pulse([f'setang 0 {-90*sign} 0','+forward 42'],.6)
                p=driver.position()
                check(f'fixed_terrace_pair_{i}_side_{sign}',
                    sign*(p[0]+2.3)>.4 and abs(p[2]-.4)<.25,position=p)
        for prefix in ('p2_basement_fitout_west_W10_exterior_',
                       'p2_basement_fitout_cibio_office_0_exterior_'):
            driver.guard()
            pane=next(p for p in meta['breakable_glass'] if p['name'].startswith(prefix))
            lo,hi=pane['lo'],pane['hi'];axis=0 if hi[0]-lo[0]<hi[1]-lo[1] else 1
            target=[(a+b)/2 for a,b in zip(lo,hi)];target[2]=2.15
            room_id='west_W10' if 'west_W10' in prefix else 'cibio_office_0'
            rooms=meta['povo2']['west_offices']['rooms']+next(l['rooms'] for l in meta['povo2']['levels'] if l['floor']==-1)
            a,b,c,d=next(r['bounds'] for r in rooms if r['id']==room_id)
            start=[(a+c)/2,(b+d)/2,.4]
            driver.place(start)
            entity='povo_glass_'+pane['name']
            check(prefix+'exists',"'func_breakable'" in console.command('ent_find '+entity,.2))
            dx,dy=target[0]-start[0],target[1]-start[1]
            yaw=math.degrees(math.atan2(dx,-dy))
            pitch=-math.degrees(math.atan2(target[2]-(start[2]+1.6256),math.hypot(dx,dy)))
            console.command(['cmd give weapon_ak47','slot1',f'setang {pitch} {yaw} 0'],1.5)
            console.command('+attack',.8);console.command('-attack',.4)
            check(prefix+'breaks_from_bullets','Found 0 matches.' in console.command('ent_find '+entity,.25),pane=pane['name'])
        report['status']='passed'
    except Exception as error:
        report['error']=str(error);raise
    finally:
        try:driver.cleanup()
        finally:
            console.close()
            report['package_sha256']=hashlib.sha256((ROOT/'build/minus1-finishes-20261102/candidate.vpk').read_bytes()).hexdigest()
            (base/'native-interactions.json').write_text(json.dumps(report,indent=2)+'\n')
            (ROOT/'build/minus1-finishes-20261102/interactions-console.log').write_text('\n'.join(console.transcript),encoding='utf-8')


if __name__=='__main__':main()
