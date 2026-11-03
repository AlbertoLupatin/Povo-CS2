"""Check restored/removed lamps in the actual candidate's PHYS and entities."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.vpk import Package
from tools.audit_povo2_compiled_floors import on_triangle

def main():
    work=ROOT/'build/lighting-fixes-20261102';out=Path(__file__).parent
    package=work/'candidate.vpk';archive=Package(package);decoder=ROOT/'build/tools/vrf-20.1/Source2Viewer-CLI.exe'
    data=b''.join(archive.chunks(archive.entries['models/povo/povo1_campus.vmdl_c']))
    model=work/'povo1_campus.vmdl_c';model.write_bytes(data)
    dump=subprocess.check_output([str(decoder),'-i',str(model),'-b','PHYS'],encoding='utf-8')
    (work/'physics.txt').write_text(dump,encoding='utf-8')
    vb=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',dump,re.S);tb=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',dump,re.S)
    assert vb and len(vb)==len(tb)
    triangles=[];units=39.37007874
    for vv,tt in zip(vb,tb):
        vertices=[(y/units,z/units,x/units) for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        triangles.extend([[vertices[i] for i in ids] for ids in struct.iter_unpack('<III',bytes.fromhex(tt))])
    faces=[(f,[min(p[k] for p in f) for k in range(3)],[max(p[k] for p in f) for k in range(3)]) for f in triangles]
    def surface(p):return any(on_triangle(p,f) for f,lo,hi in faces if all(lo[k]-.002<=p[k]<=hi[k]+.002 for k in range(3)))
    checks=[]
    def check(name,p,expected):checks.append(dict(name=name,point=p,expected_surface=expected,passed=surface(p)==expected))
    for index,y in ((0,15.575),(1,28.575)):
        for z in (4.3,4.7,5.5,6.1,8.5):
            for x,yy in ((55.5,y),(55.65,y),(55.575,y-.075),(55.575,y+.075)):
                check('restored_post_'+str(index),[x,yy,z],True)
    for index,y in ((5,80.575),(6,93.575)):
        for z in (8.0,8.5):check('removed_post_'+str(index),[55.65,y,z],False)
        check('removed_head_'+str(index),[56.,y,9.1],False)
    entry='maps/trento_povo_campus/entities/default_ents.vents_c'
    path=work/'default_ents.vents_c';path.write_bytes(b''.join(archive.chunks(archive.entries[entry])))
    entities=subprocess.check_output([str(decoder),'-i',str(path),'-b','DATA'],encoding='utf-8')
    (work/'entities.txt').write_text(entities,encoding='utf-8')
    old=(ROOT/'exports/map_consistency_audit_20261102/entities.txt').read_text()
    counts=Counter(re.findall(r'\bclassname = "([^"]+)"',entities));previous=Counter(re.findall(r'\bclassname = "([^"]+)"',old))
    expected=dict(previous);expected['light_omni2']-=12
    entity_check=dict(passed=dict(counts)==expected,previous=dict(previous),actual=dict(counts),expected_removed_indoor_lights=12,
        scope='Only twelve indoor ceiling lights over the open terraces should leave the packaged entity inventory.')
    result=dict(status='passed' if all(c['passed'] for c in checks) and entity_check['passed'] else 'failed',checks=checks,
        entity_inventory=entity_check,package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),model_sha256=hashlib.sha256(data).hexdigest())
    (out/'compiled-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],len(checks),'compiled lamp checks; entity inventory',entity_check['passed'])
    for c in checks:
        if not c['passed']:print(c)
    if not entity_check['passed']:print('ENTITY DELTA',dict(counts-previous),dict(previous-counts))
    assert result['status']=='passed'

if __name__=='__main__':main()
