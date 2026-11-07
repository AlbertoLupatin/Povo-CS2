"""Inspect the entrance and exterior fills in the candidate's actual PHYS."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.vpk import Package
from tools.audit_povo2_compiled_floors import on_triangle

def main():
    work=ROOT/'build/exterior-entrance-20261102';out=Path(__file__).parent
    package=work/'candidate.vpk';archive=Package(package)
    data=b''.join(archive.chunks(archive.entries['models/povo/povo1_campus.vmdl_c']))
    model=work/'povo1_campus.vmdl_c';model.write_bytes(data)
    dump=subprocess.check_output([str(ROOT/'build/tools/vrf-20.1/Source2Viewer-CLI.exe'),'-i',str(model),'-b','PHYS'],encoding='utf-8')
    (work/'physics.txt').write_text(dump,encoding='utf-8')
    vb=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',dump,re.S)
    tb=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',dump,re.S)
    assert vb and len(vb)==len(tb)
    faces=[];units=39.37007874
    for vv,tt in zip(vb,tb):
        vertices=[(y/units,z/units,x/units) for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        faces.extend([[vertices[i] for i in f] for f in struct.iter_unpack('<III',bytes.fromhex(tt))])
    bounds=[(f,[min(p[k] for p in f) for k in range(3)],[max(p[k] for p in f) for k in range(3)]) for f in faces]
    def surface(p):
        return any(on_triangle(p,f) for f,lo,hi in bounds if all(lo[k]-.002<=p[k]<=hi[k]+.002 for k in range(3)))
    checks=[]
    def check(name,p,expected=True):checks.append(dict(name=name,point=p,expected_surface=expected,passed=surface(p)==expected))
    for p in ([22.4,22,6.5],[22.6,22,6.5],[25.4,25,6.5],[25.6,25,6.5],
              [24,19.4,6.5],[24,19.6,6.5],[24,29.4,6.5],[24,29.6,6.5],
              [24,10.9,6.5],[24,11.1,6.5]):check('obsolete_hanging_wall_removed',p,False)
    for x in (21.,23.,24.5):
        for y in (12.,16.,22.,28.):check('flat_finished_ceiling',[x,y,7.28])
    for x in (20.4,20.6):
        for y in (11.5,14.,16.,17.7):
            for z in (4.2,5.5,6.8):check('closed_side_bay',[x,y,z])
        for z in (4.2,5.1,6.):check('retained_stair_portal',[x,22,z],False)
    for x in (31.88,35.83):
        for z in (-2.,0.,2.,3.8):check('fill_A_concrete_facing',[x,5,z])
    for x in (37.,40.,47.,50.,54.):check('fills_B_C_upper_edge',[x,2.35,4.])
    # D's exposed garden-side face extends to the bottom, with the pavement grade above.
    for y in (3.,5.,9.,13.):
        for z in (-2.,0.,2.):check('fill_D_closed_support',[56.7,y,z])
    result=dict(status='passed' if all(c['passed'] for c in checks) else 'failed',checks=checks,
        package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),model_sha256=hashlib.sha256(data).hexdigest())
    (out/'compiled-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],len(checks),'compiled checks')
    for c in checks:
        if not c['passed']:print(c)
    assert result['status']=='passed'

if __name__=='__main__':main()
