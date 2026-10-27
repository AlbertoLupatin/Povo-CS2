"""Apply the user's 27 October rigid basement placement to the assembled map.

The drawing's corridors, offices, yard and exit stairs are one rigid body.
Only the stair/lift interfaces are rebuilt; room shapes are never edited here.
"""
try:
    from .povo_room_fitout import subtract_box
except ImportError:
    from povo_room_fitout import subtract_box


def rotate_point(p, placement):
    a,b=placement['source_anchor'];c,d=placement['target_anchor']
    return [round(c+p[1]-b,6),round(d-p[0]+a,6),*p[2:]]


def rotate_rect(r, placement):
    a=rotate_point(r[:2],placement);b=rotate_point(r[2:],placement)
    return [min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]


def extend(boxes, levels):
    link=levels[1]['connection'];spec=link['povo2']
    placement=spec['additions']['config'].get('basement_rotation')
    if not placement:return boxes
    level=next(l for l in spec['levels'] if l['floor']==-1);z=level['z']
    def point(p):return rotate_point(p,placement)
    def rect(r):return rotate_rect(r,placement)
    result=[]
    fixed=('p2_basement_core_', 'p2_basement_lift_')
    for n,lo,hi,m in boxes:
        if n.startswith(('p2_basement_core_door_','p2_basement_core_panic_','p2_basement_core_threshold')):
            continue
        if n.startswith(('p2_basement_','p2_yard_')) and not n.startswith(fixed):
            a=point(lo);b=point(hi)
            lo=tuple(min(x,y) for x,y in zip(a,b));hi=tuple(max(x,y) for x,y in zip(a,b))
        result.append((n,lo,hi,m))
    # Rotation happens after the lift was installed. Re-excavate its basement
    # volume so a moved corridor wall/display case cannot cross the ladder.
    a,b,c,d=spec['lift']['shaft']
    shaft=((a,b,z-.22),(c,d,3.78))
    result=[p for box in result for p in
            (subtract_box(box,shaft) if box[0].startswith('p2_basement_')
             and not box[0].startswith(fixed) else [box])]
    spec['basement']={k:rect(r) for k,r in spec['basement'].items()}
    spec['additions']['basement_areas']=[rect(r) for r in spec['additions']['basement_areas']]
    for room in level['rooms']:
        room['bounds']=rect(room['bounds']);room['footprint_local_metres']=room['bounds']
        room['door_side']='v_max';room['door_fraction']=1-room['door_fraction']
    for s in level['audit_stations']:
        if s['id'] not in ('core_door','core_landing','lift_floor'):s['point']=point(s['point'])
    yard=spec['additions']['yard'];yard['bounds']=rect(yard['bounds']);yard['stair_axis']=1
    for s in yard['audit_stations']:s['point']=point(s['point'])
    for key in ('indoor_path','outdoor_path','top_path'):yard[key]=[point(p) for p in yard[key]]
    for r in spec['stairs']['rails']:
        if r['name'].startswith('p2_yard_'):
            for key in ('a','b'):r[key]=point(r[key])
    # Rotate room/route lamps, retaining lamps inside the actual stair stack.
    core=spec['stairs']['bounds']
    spec['lights']=[point(p) if 0.4<p[2]<3.8 and not
                    (core[0]<=p[0]<=core[2] and core[1]<=p[1]<=core[3]) else p
                    for p in spec['lights']]
    def add(n,lo,hi,m='wall'):result.append((n,tuple(lo),tuple(hi),m))
    # The east landing stays connected to every flight. Its new portal faces
    # south, reaching the rotated corridor without moving individual rooms.
    x=core[2]-1.3;y=placement['target_anchor'][1]
    for hole in [((x-.85,y-.3,z-.01),(x+.85,y+.3,z+2.25)),
                 ((x-.85,17.65,z-.01),(x+.85,y+.3,z+2.25)),
                 ((core[0]-.2,14.61,z-.01),(core[0]+.2,17.6,z+2.65)),
                 ((20.3,16.65,z-.01),(20.9,17.9,z+2.25)),
                 ((20.3,15.4,z-.01),(20.9,16.5,z+2.25))]:
        result=[p for box in result for p in
                (subtract_box(box,hole) if box[3] in ('wall','window_frame') else [box])]
    # Close the former east-facing basement door.
    add('p2_basement_core_old_door_infill',(core[2]-.1,21.175,z),
        (core[2]+.1,22.825,z+2.25))
    add('p2_basement_core_south_threshold',(x-.85,y-.3,z-.22),
        (x+.85,y+.3,z),'floor_p2_tile')
    add('p2_basement_lift_approach',(18.25,14,z-.22),(20.8,17,z),'floor_p2_tile')
    for i,xx in enumerate((x-.85,x+.85)):
        add('p2_basement_core_door_south_'+str(i),(xx-.025,y+.05,z+.02),
            (xx+.025,y+.85,z+2.18),'door_black')
        add('p2_basement_core_south_panic_'+str(i),(xx-.05,y+.15,z+1),
            (xx+.05,y+.75,z+1.045),'door_pushbar')
    for p in spec['stairs']['portals']:
        if p['floor']==-1:p.update(centre=[x,y,z],side='u_min')
    for s in level['audit_stations']:
        if s['id']=='stair_approach':s['point']=[x,y-.8]
        if s['id']=='core_door':s['point']=[x,y-.8]
        if s['id']=='core_landing':s['point']=[x,22]
        if s['id']=='lift_floor':s['point']=[21.85,15.95]
    # The old yard excavation is no longer a hole in the street pavement.
    add('exterior_povo2_old_yard_paving',(50.5,10,3.78),(56.4,29.5,4),'exterior_paving')
    # Hollow the moved below-ground rooms/yard out of exterior paving/scenery.
    areas=[(spec['basement'][k],z,2.65 if 'cibio' in k else 3.35)
           for k in spec['basement'] if k!='yard']+[(yard['bounds'],yard['z'],3.0)]
    areas.append((rect(spec['additions']['config']['basement_exit']['inside_stair']),z,4.0))
    for r,foot,height in areas:
        hole=((r[0]-.12,r[1]-.12,foot-.25),(r[2]+.12,r[3]+.12,foot+height+.02))
        result=[p for box in result for p in
                (subtract_box(box,hole) if box[0].startswith(('exterior_','library_0_access')) else [box])]
    # The sheltered edge under Povo 1 already has its building facade as fall
    # protection. A duplicated outdoor guard must not cut through its rooms.
    p1=((-23,-103,4),(24,-20,7.3))
    result=[p for box in result for p in
            (subtract_box(box,p1) if box[0].startswith('p2_yard_') and box[3]=='metal_dark' else [box])]
    spec['basement_placement']=dict(placement,portal=[x,y,z])
    return result
