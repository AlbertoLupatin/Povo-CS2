"""Check the actual static collision stored in the newly built campus VPK."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.vpk import Package
from tools.audit_povo2_compiled_floors import on_triangle


def main():
    out=Path(__file__).parent
    package=ROOT/'build/package/trento_povo_campus.vpk'
    archive=Package(package);entry=archive.entries['models/povo/povo1_campus.vmdl_c']
    archive.verify(entry);data=b''.join(archive.chunks(entry))
    work=ROOT/'build/drawio-compiled-review';work.mkdir(exist_ok=True)
    model=work/'povo1_campus.vmdl_c';model.write_bytes(data)
    dump=subprocess.check_output([str(ROOT/'build/tools/vrf-20.1/Source2Viewer-CLI.exe'),'-i',str(model),'-b','PHYS'],encoding='utf-8')
    (work/'physics.txt').write_text(dump,encoding='utf-8')
    vb=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',dump,re.S)
    tb=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',dump,re.S)
    if not vb or len(vb)!=len(tb):raise RuntimeError('Invalid compiled collision dump')
    triangles=[];units=39.37007874
    for vv,tt in zip(vb,tb):
        vertices=[(y/units,z/units,x/units) for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        triangles.extend([[vertices[i] for i in f] for f in struct.iter_unpack('<III',bytes.fromhex(tt))])
    bounds=[(f,tuple(min(v[k] for v in f) for k in range(3)),tuple(max(v[k] for v in f) for k in range(3))) for f in triangles]
    def surface(p):
        return any(on_triangle(p,f) for f,lo,hi in bounds if all(lo[k]-.002<=p[k]<=hi[k]+.002 for k in range(3)))
    meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())['povo2']
    if not meta.get('drawio_entrance'):raise RuntimeError('Source provenance is not the Draw.io revision')
    checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    a=meta['drawio_entrance']['areas'];cx=sum(a['c5'][::2])/2
    for key in ('up','down'):
        points=meta['gardens']['routes'][key]
        for i,p in enumerate(points):check(key+'_support_'+str(i),surface(p),point=p)
    for x in (cx-.5,cx+.5):
        for side in (-.04,.04):
            for z in (.7,1.5,2.4):
                p=[x,a['c5'][3]+side,z];check('sealed_north_door',surface(p),point=p)
    for y in (3.,6.,11.,13.4,14.7):
        p=[31.88,y,1.5];check('east_facade_at_31_8',surface(p),point=p)
    for x in (42.3,42.6,43.8,44.9,45.3):
        for y in (3.,5.,8.):
            p=[x,y,-3.2];check('full_lower_approach_floor',surface(p),point=p)
    check('east_arm_floor_removed',not surface([28.,16.6,.4]))
    check('old_up_stair_first_tread_removed',not surface([34.5,8.6,.58]))
    report=dict(status='passed' if all(c['passed'] for c in checks) else 'failed',
        package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),model_sha256=hashlib.sha256(data).hexdigest(),
        metadata_sha256=hashlib.sha256((ROOT/'exports/povo_campus/provenance.json').read_bytes()).hexdigest(),
        scope='Actual packaged static PHYS: tread support, sealed end, widened facade and removed arm/old stair; native player traversal separate',checks=checks)
    (out/'compiled-layout-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],len(checks),'compiled checks')
    for c in checks:
        if not c['passed']:print(c)
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
