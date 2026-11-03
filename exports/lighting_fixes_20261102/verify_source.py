"""Preserve the approved campus while repairing only the audited light objects."""
from pathlib import Path
from collections import Counter
import hashlib,json,pickle,re,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.build_povo_campus import build_geometry,collision_boxes

def main():
    work=ROOT/'build/lighting-fixes-20261102';out=Path(__file__).parent
    old,oldlevels,oldphysics=pickle.load(open(work/'baseline.pkl','rb'))
    _,_,new,levels,_=build_geometry();physics=collision_boxes(new)
    pickle.dump((new,levels,physics),open(work/'current.pkl','wb'))
    canonical=lambda v:json.dumps(v,sort_keys=True)
    ac=Counter(map(canonical,old));bc=Counter(map(canonical,new))
    removed=[json.loads(v) for v in (ac-bc).elements()];added=[json.loads(v) for v in (bc-ac).elements()]
    oldlink=next(l['connection'] for l in oldlevels if 'connection' in l)
    link=next(l['connection'] for l in levels if 'connection' in l)
    def permitted(n):return n.startswith(('academic_upper_west_terrace_finish_fixture_',
        'academic_upper_east_terrace_finish_fixture_','academic_first_link_route_finish_fixture_14_',
        'academic_first_link_route_finish_fixture_15_')) or bool(re.match(r'exterior_povo2_front_lamp_(?:head_)?[0156](?:_|$)',n))
    checks=dict(approved_basement_metadata_preserved=canonical(oldlink['povo2'])==canonical(link['povo2']),
        all_exterior_meshes_preserved=all(canonical(oldlevels[0]['exterior'][k])==canonical(levels[0]['exterior'][k]) for k in ('meshes','collision_meshes')),
        only_audited_boxes_changed=all(permitted(b[0]) for b in removed+added),
        only_two_complete_lamp_posts_added=len(added)==2 and {b[0] for b in added}=={'exterior_povo2_front_lamp_0','exterior_povo2_front_lamp_1'},
        room_records_preserved=all(canonical(a['rooms'])==canonical(b['rooms']) for a,b in zip(oldlevels,levels)),
        all_non_lamp_collision_preserved=canonical([b for b in oldphysics if not b[0].startswith('exterior_povo2_front_lamp_')])==
            canonical([b for b in physics if not b[0].startswith('exterior_povo2_front_lamp_')]))
    result=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,removed_boxes=removed,added_boxes=added,
        visible_boxes=len(new),collision_boxes=len(physics),
        package_before_sha256=hashlib.sha256((work/'backup/previous.vpk').read_bytes()).hexdigest())
    (out/'source-preservation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('removed_boxes','added_boxes')},indent=2))
    assert result['status']=='passed'

if __name__=='__main__':main()
