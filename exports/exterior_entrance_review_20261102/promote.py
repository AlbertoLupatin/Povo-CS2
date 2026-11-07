"""Promote the exact package covered by the completed entrance/fill review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,shutil,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.verify_cs2_package import verify_package

def main():
    out=Path(__file__).parent;work=ROOT/'build/exterior-entrance-20261102'
    candidate=work/'candidate.vpk';digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    required=('source-preservation.json','main-overlaps.json','paving-overlaps.json',
              'compiled-checks.json','compiled-floors.json','native/visual-review.json','walking/survey-runtime.json')
    reports={name:json.loads((out/name).read_text()) for name in required}
    for name,r in reports.items():
        assert r['status']=='passed',(name,r.get('status'))
        if r.get('package_sha256'):assert r['package_sha256']==digest,name
    tests=(work/'source-tests.log').read_text()
    assert re.search(r'Ran 378 tests',tests) and tests.rstrip().endswith('OK')
    assert json.loads((out/'native/captures.json').read_text())['package_sha256']==digest
    manifest=json.loads((work/'candidate.json').read_text())
    assert manifest['status']=='passed'
    overview=ROOT/'exports/povo_campus/radar/trento_povo_campus.txt'
    check=verify_package(candidate,overview,full_crc=True,map_name='trento_povo_campus',model_name='povo1_campus')
    assert check['status']=='passed',check
    (out/'candidate-package-check.json').write_text(json.dumps(check,indent=2)+'\n')
    target=ROOT/'build/package/trento_povo_campus.vpk';temporary=target.with_suffix('.entrance-review.tmp')
    shutil.copyfile(candidate,temporary)
    assert hashlib.sha256(temporary.read_bytes()).hexdigest()==digest
    temporary.replace(target)
    manifest['package']=str(target);target.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    promoted=verify_package(target,overview,full_crc=True,map_name='trento_povo_campus',model_name='povo1_campus')
    assert promoted['status']=='passed' and promoted['package_sha256']==digest
    (out/'promoted-package-check.json').write_text(json.dumps(promoted,indent=2)+'\n')
    shutil.copyfile(work/'source-tests.log',out/'source-tests.log')
    shutil.copyfile(work/'native-build.log',out/'native-build.log')
    routes=reports['walking/survey-runtime.json']['routes']
    summary=dict(status='passed',completed_at_utc=datetime.now(timezone.utc).isoformat(),
        package_sha256=digest,package_bytes=target.stat().st_size,package_entries=promoted['package_entries'],
        crc_verified_entries=promoted['crc_verified_entries'],source_tests=378,
        compiled_entrance_fill_checks=len(reports['compiled-checks.json']['checks']),
        ordinary_routes=len(routes),ordinary_waypoints=sum(len(r['checks']) for r in routes),
        reviewed_views=reports['native/visual-review.json']['reviewed_views'],
        preservation=reports['source-preservation.json']['checks'],
        local_package=str(target),scope='Standard local package; Winter and Workshop not updated',
        remaining_issue='Existing flat asphalt disk at (62,0,7.602) is unchanged; full uphill street traversal remains uncertified.')
    (out/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
