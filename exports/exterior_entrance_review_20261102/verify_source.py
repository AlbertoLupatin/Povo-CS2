"""Compare the entrance/fill revision with the saved pre-change assembly."""
from pathlib import Path
from collections import Counter
import hashlib,json,pickle,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_povo_campus import build_geometry

def main():
    work=ROOT/'build/exterior-entrance-20261102'
    old,oldlevels=pickle.load(open(work/'baseline.pkl','rb'))
    _,_,new,levels,_=build_geometry()
    canonical=lambda v:json.dumps(v,sort_keys=True)
    a=Counter(map(canonical,old));b=Counter(map(canonical,new))
    removed=[json.loads(v) for v in (a-b).elements()]
    added=[json.loads(v) for v in (b-a).elements()]
    oldlink=next(l['connection'] for l in oldlevels if 'connection' in l)
    newlink=next(l['connection'] for l in levels if 'connection' in l)
    p2=dict(newlink['povo2']);p2.pop('entrance_finishes',None)
    oldext=oldlevels[0]['exterior'];newext=levels[0]['exterior']
    checks=dict(
        approved_povo2_metadata_preserved=canonical(oldlink['povo2'])==canonical(p2),
        only_nine_obsolete_ground_wall_tops_removed=len(removed)==9 and all(
            m=='wall' and 20.4<=lo[0]<=25.7 and 10.7<=lo[1]<=29.6
            and 6.29<=lo[2]<hi[2]<=7.36 for _,lo,hi,m in removed),
        only_entrance_finish_and_reviewed_fill_boxes_added=len(added)==9 and all(
            n.startswith(('p2_ground_entrance_','exterior_user_fill_')) for n,*_ in added),
        exterior_meshes_preserved=all(canonical(oldext[k])==canonical([
            m for m in newext[k] if not m['name'].startswith('exterior_user_fill_')])
            for k in ('meshes','collision_meshes')),
        street_asphalt_collision_preserved=canonical([m for m in oldext['collision_meshes'] if m['material']=='exterior_asphalt'])==
            canonical([m for m in newext['collision_meshes'] if m['material']=='exterior_asphalt']))
    result=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,
        removed_boxes=removed,added_boxes=added,
        input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
            'tools/povo2_interiors.py','tools/povo2_entrance_finishes.py','tools/povo_exterior_fills.py','tools/cs2_campus.py')})
    Path(__file__).with_name('source-preservation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(checks,indent=2));assert result['status']=='passed'

if __name__=='__main__':main()
