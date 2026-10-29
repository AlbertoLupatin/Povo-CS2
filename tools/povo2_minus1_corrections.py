"""Apply the user's 29 October -1 markup in final campus coordinates."""
import hashlib
import json
from pathlib import Path


def apply(boxes,spec,root):
    root=Path(root) if root else Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'config/povo2_minus1_corrections.json').read_text())
    basement=spec['basement'];level=next(l for l in spec['levels'] if l['floor']==-1)
    first,second=sorted(level['rooms'],key=lambda r:r['bounds'][1])
    old=list(second['bounds']);old_gap=old[1]-first['bounds'][3]
    shift=cfg['gap_metres']-old_gap
    second['bounds']=[old[0],old[1]+shift,old[2],old[3]+shift]
    second['footprint_local_metres']=list(second['bounds'])
    basement[second['id']]=list(second['bounds'])
    original=list(basement['cibio_corridor']);a,b,c,d=original;d+=shift
    basement['cibio_corridor']=[a,b,c,d];basement['cross_corridor']=[a,b,c,d]
    gap_south=first['bounds'][3];gap_north=second['bounds'][1]
    narrow_west=c-cfg['gap_clear_width_metres'];spine_x=(narrow_west+c)/2
    sections=[[a,b,c,gap_south],[narrow_west,gap_south,c,gap_north],[a,gap_north,c,d]]
    basement['cibio_corridor_sections']=sections
    turn=list(basement['exit_turn']);turn[1]+=shift;turn[3]+=shift
    basement['exit_turn']=turn
    basement['exit_corridor']=[*basement['exit_corridor'][:3],turn[3]]
    lower=list(basement['corridor'])
    if cfg['connect_lower_corridor_to_exit']:lower[2]=basement['exit_corridor'][2]
    basement['corridor']=lower
    for station in level['audit_stations']:
        name=station['id'];x,y=station['point']
        if name.startswith(second['id']) or name in ('cibio_end','cross_corridor_end','exit_far_turn','exit_turn_join'):y+=shift
        if a<=x<=c and gap_south-.5<=y<=gap_north+.5:x=spine_x
        station['point']=[x,y]
    level['audit_stations'].extend([
        dict(id='narrow_gap_south',point=[spine_x,gap_south+1]),
        dict(id='narrow_gap_mid',point=[spine_x,(gap_south+gap_north)/2]),
        dict(id='narrow_gap_north',point=[spine_x,gap_north-1]),
        dict(id='lower_exit_junction',point=[34.5,17.15])])
    result=[]
    for name,lo,hi,material in boxes:
        if name.startswith('p2_basement_'+second['id']+'_'):
            lo=(lo[0],lo[1]+shift,lo[2]);hi=(hi[0],hi[1]+shift,hi[2])
        result.append((name,lo,hi,material))
    spec['additions']['basement_areas']=[*sections,*[list(r['bounds']) for r in level['rooms']]]
    garden=spec['gardens'];garden['indoor_turn']=list(turn)
    garden['indoor_corridor']=list(basement['exit_corridor'])
    upper_y=(turn[1]+turn[3])/2
    garden['routes']['indoor']=[[spine_x,17.15,.4],[34.5,17.15,.4],[34.5,16.25,.4]]
    garden['routes']['passage']=[[34.5,16.25,.4],[34.5,11.25,.4],[34.5,10,.4],[37.5,10,.4]]
    spec['additions']['yard']['routes']['indoor']=garden['routes']['indoor']
    spec['additions']['yard']['routes']['passage']=garden['routes']['passage']
    spec['additions']['yard']['indoor_path']=garden['routes']['passage']
    closed_ids={'left_exit_start','locker_return','exit_far_turn','exit_turn_join'}
    level['closed_stations']=[s for s in level['audit_stations'] if s['id'] in closed_ids]
    level['audit_stations']=[s for s in level['audit_stations'] if s['id'] not in closed_ids]
    door=dict(centre=[c,upper_y,.4],width=cfg['upper_junction_door_width_metres'],height=2.25,axis=0)
    lower_door=dict(centre=[34.5,cfg['lower_junction_door_north_coordinate'],.4],
                    width=cfg['upper_junction_door_width_metres'],height=2.25,axis=1)
    spec['minus1_corrections']=dict(cfg,old_gap_metres=old_gap,room2_north_shift_metres=shift,
        original_spine=original,spine_sections=sections,spine_route_x=spine_x,
        upper_route_y=upper_y,upper_junction_door=door,lower_junction_door=lower_door,
        closed_corridor_areas=[[c,turn[1],turn[2],turn[3]],
                              [33.25,cfg['lower_junction_door_north_coordinate'],35.75,turn[3]]])
    spec.setdefault('input_hashes',{}).update({s:hashlib.sha256((root/s).read_bytes()).hexdigest()
        for s in ('config/povo2_minus1_corrections.json',cfg['source'],'tools/povo2_minus1_corrections.py')})
    return result
