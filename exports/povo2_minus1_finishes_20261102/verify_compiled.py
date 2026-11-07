"""Verify the requested solids in the actual candidate's compiled physics."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.vpk import Package
from tools.audit_povo2_compiled_floors import on_triangle

def main(model_path=None):
    out=Path(__file__).parent;work=ROOT/'build/minus1-finishes-20261102'
    package=None if model_path else work/'candidate.vpk'
    if model_path:data=Path(model_path).read_bytes()
    else:
        archive=Package(package)
        data=b''.join(archive.chunks(archive.entries['models/povo/povo1_campus.vmdl_c']))
    model=work/'povo1_campus.vmdl_c';model.write_bytes(data)
    dump=subprocess.check_output([str(ROOT/'build/tools/vrf-20.1/Source2Viewer-CLI.exe'),'-i',str(model),'-b','PHYS'],encoding='utf-8')
    (work/'physics.txt').write_text(dump,encoding='utf-8')
    vb=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',dump,re.S)
    tb=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',dump,re.S)
    if not vb or len(vb)!=len(tb):raise RuntimeError('Invalid compiled physics')
    triangles=[];units=39.37007874
    for vv,tt in zip(vb,tb):
        vertices=[(y/units,z/units,x/units) for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        triangles.extend([[vertices[i] for i in f] for f in struct.iter_unpack('<III',bytes.fromhex(tt))])
    bounds=[(f,tuple(min(v[k] for v in f) for k in range(3)),tuple(max(v[k] for v in f) for k in range(3))) for f in triangles]
    def surface(p):
        return any(on_triangle(p,f) for f,lo,hi in bounds if all(lo[k]-.002<=p[k]<=hi[k]+.002 for k in range(3)))
    meta=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text());p2=meta['povo2']
    checks=[]
    def check(name,passed,p):checks.append(dict(name=name,passed=bool(passed),point=p))
    x,y=p2['west_offices']['c7'][:2]
    for side in (-.08,.08):
        for dy in (.5,1.,1.7,2.2):
            for z in (.7,1.5,2.4):
                p=[x+side,y+dy,z];check('photo1_white_end_wall',surface(p),p)
    cx,cy=p2['minus1_finishes']['empty_wi2_door']['centre']
    for side in (-.08,.08):
        for dx in (-.3,0,.3):
            for z in (.7,1.5,2.4):
                p=[cx+dx,cy+side,z];check('photo1_empty_left_doorway',not surface(p),p)
    for i in range(6):
        for side in (-.04,.04):
            for dy in (-.2,.2):
                for z in (.7,1.5,2.4):
                    p=[-2.3+side,22.025+i*3+dy,z];check('photo2_fixed_black_door',surface(p),p)
    for y in (19.,23.,26.,29.,32.,35.,40.,50.,55.):
        for side in (-.1,.1):
            for z in (.7,1.5,2.4):
                p=[-2.3+side,y,z];check('photo2_opaque_wall',surface(p),p)
    import pickle
    boxes,_,_=pickle.load(open(work/'current.pkl','rb'))
    for name,lo,hi,mat in boxes:
        if name.startswith('p2_basement_fitout_') and name.endswith('_desk'):
            p=[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,hi[2]]
            check('furnished_desk_support',surface(p),p)
    panes=[p for p in meta['breakable_glass'] if p['name'].startswith('p2_basement_fitout_')]
    for pane in panes:
        check('four_attached_privacy_bands',len(pane.get('decorations',[]))==4,pane['name'])
    report=dict(status='passed' if all(c['passed'] for c in checks) else 'failed',checks=checks,
        package_sha256=hashlib.sha256(package.read_bytes()).hexdigest() if package else None,
        model_sha256=hashlib.sha256(data).hexdigest())
    (out/'compiled-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],len(checks),'compiled checks')
    for c in checks:
        if not c['passed']:print(c)
    assert report['status']=='passed'

if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else None)
