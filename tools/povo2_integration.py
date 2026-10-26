"""Place the approved Povo 2 lower plan against the completed compact stair."""
import copy

try:
    from .povo2_planimetry import build as build_draft
    from .povo_room_fitout import subtract_box
except ImportError:
    from povo2_planimetry import build as build_draft
    from povo_room_fitout import subtract_box


def point(p, floor=0):
    x,y,*rest=p
    # A half turn preserves all entrance-relative left/right relationships.
    # The basement start follows the actual compact enclosure's north edge.
    return (41.5-x,61.5-y-(3.5 if floor==-1 else 0),*rest)


def rectangle(r, floor=0):
    a=point(r[:2],floor);b=point(r[2:],floor)
    return [min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]


def extend(boxes, levels, root, wall_height):
    boxes=list(boxes);link=levels[1]['connection'];compact=link['stair']
    draft,spec=build_draft(root,wall_height);spec=copy.deepcopy(spec)
    spec['status']='Integrated lower floors using the completed compact staircase'
    spec['placement']={'rotation_degrees':180,'origin':[41.5,61.5],
                       'basement_north_offset':-3.5}
    spec['footprint']=rectangle(spec['footprint'])
    g=spec['ground']
    for key in ('outside_landing','reception','left_corridor','tables','right_corridor','stair_access'):
        g[key]=rectangle(g[key])
    g['entrance_world']=list(point((g['entrance'][0],28)))
    g['reception_wall_extension']=[20.5,19.5,20.5,29.5]
    spec['basement']={k:rectangle(r,-1) for k,r in spec['basement'].items()}
    spec['parking']['bounds']=rectangle(spec['parking']['bounds'])
    spec['parking']['cars']=[[*point((x,y)),m] for x,y,m in spec['parking']['cars']]
    added=[]
    def add(name,lo,hi,mat):added.append((name,tuple(lo),tuple(hi),mat))
    # Exclude the provisional upright core, its landings and its upper level.
    for name,lo,hi,mat in draft:
        if name.startswith(('p2_stair_','p2_first_')) or '_stair_landing' in name or name=='p2_parking_shaft_bottom':continue
        floor=-1 if name.startswith('p2_basement_') else -2 if name.startswith('p2_parking_') else 0
        a=point(lo,floor);b=point(hi,floor)
        add(name,tuple(min(a[i],b[i]) for i in range(3)),tuple(max(a[i],b[i]) for i in range(3)),mat)
    # Restore the draft's old shaft holes before cutting the actual core.
    for floor,prefix,z in ((0,'p2_ground',4),(-2,'p2_parking',-3.2)):
        r=rectangle((25,32,31.4,42),floor);a,b,c,d=r
        add(prefix+'_old_shaft_infill',(a,b,z-.22),(c,d,z),'floor_p2_asphalt' if floor==-2 else 'floor_p2_tile')
        add(prefix+'_old_ceiling_infill',(a,b,z+wall_height-.07),(c,d,z+wall_height),'ceiling_panel')
    # Remove new shell surfaces from the established enclosure, leaving every
    # first-floor wall, opening, guard and walking surface at its original place.
    core=compact['bounds'];a,b,c,d=core
    for z in (-3.2,.4,4):
        hole=((a-.11,b-.11,z-.3),(c+.11,d+.11,z+3.5))
        added=[part for box in added for part in subtract_box(box,hole)]
    # Open the formerly closed vestibule into the new hall.
    boxes=[box for box in boxes if not box[0].startswith(('academic_first_link_p2_lower_wall_',
                                                        'academic_first_link_p2_lower_ceiling'))]
    # Original treads were solid down to ground. Hollow their undersides to
    # allow stacked flights; preserve their tops and all twenty tread positions.
    prototype=[]
    for i,box in enumerate(boxes):
        name,lo,hi,mat=box
        if name.startswith(('academic_first_link_p2_stair_upper_step_',
                            'academic_first_link_p2_stair_lower_step_')):
            boxes[i]=(name,(lo[0],lo[1],hi[2]-.16),hi,mat)
        if name.startswith('academic_first_link_p2_stair_') and not any(s in name for s in ('_wall_','_upper_door_','_lower_door_','_panic_','_frame_','_finish_sign')):
            prototype.append(boxes[i])
    paths=[]
    for lower,zshift in ((-1,-3.6),(-2,-7.2)):
        for name,lo,hi,mat in prototype:
            if name.endswith(('_guard_east','_guard_cap_east')):continue
            add('p2_extended_'+str(lower)+'_'+name.replace('academic_first_link_p2_stair_',''),
                (lo[0],lo[1],lo[2]+zshift),(hi[0],hi[1],hi[2]+zshift),mat)
        paths.append(dict(lower_floor=lower,points=[list((x,y,z+zshift)) for x,y,z in
            [compact['top'],*compact['path'],compact['bottom']]]))
    # Extend the enclosure below ground; the roof and the whole upper arrival
    # are the already verified compact geometry.
    for side,lo,hi in (('west',(a-.1,b,-3.2),(a+.1,d,4)),
                        ('east',(c-.1,b,-3.2),(c+.1,d,4)),
                        ('south',(a,b-.1,-3.2),(c,b+.1,4)),
                        ('north',(a,d-.1,-3.2),(c,d+.1,4))):
        add('p2_extended_enclosure_'+side,lo,hi,'wall')
    portals=[]
    for floor,z in ((0,4),(-1,.4),(-2,-3.2)):
        prefix={0:'p2_ground',-1:'p2_basement',-2:'p2_parking'}[floor]
        # Full landing plate, with the next flight's shaft cut at intermediate floors.
        add(prefix+'_core_slab',(a,b,z-.22),(c,d,z),'floor_p2_asphalt' if floor==-2 else 'floor_p2_tile')
        portals.append(dict(floor=floor,centre=[16.5,22,z],side='v_max'))
        if floor:
            hole=((16.3,21.175,z-.01),(16.7,22.825,z+2.2))
            added=[p for box in added for p in subtract_box(box,hole)]
            for side,y in (('south',21.175),('north',22.825)):
                add(prefix+'_core_door_'+side,(16.55,y-.025,z+.02),(17.35,y+.025,z+2.18),'door_black')
                add(prefix+'_core_panic_'+side,(16.65,y-.05,z+1),(17.25,y+.05,z+1.045),'stair_red')
            add(prefix+'_core_threshold',(16.3,21.175,z-.22),(17.5,22.825,z),'floor_p2_tile')
    # Shaft openings at ground and -1, retaining the unobstructed top/bottom
    # landings on the east side of the stair. Parking closes the bottom well.
    for z in (4,.4):
        hole=((9.7,18.5,z-.3),(14.3,22.82,z+.01))
        def opening(box):
            n,lo,hi,m=box
            plate=m.startswith('floor_') and '_step_' not in n and abs(hi[2]-z)<.02
            return subtract_box(box,hole) if plate else [box]
        boxes=[p for box in boxes for p in opening(box)]
        added=[p for box in added for p in opening(box)]
    spec['levels']=[l for l in spec['levels'] if l['floor']!=1]
    for level in spec['levels']:
        floor=level['floor'];z=level['z']
        level['audit_stations']=[dict(id=s['id'],point=list(point(s['point'],floor)))
                                 for s in level['audit_stations'] if s['id']!='stair_landing']
        level['audit_stations'].extend([dict(id='core_door',point=[17.8,22]),
                                       dict(id='core_landing',point=[15.2,22])])
        if floor==0:
            level['table_bounds']=[rectangle(r) for r in level['table_bounds']]
            for room in level['rooms']:
                room['bounds']=rectangle(room['bounds']);room['footprint_local_metres']=room['bounds']
                room['door_side']='v_max';room['door_fraction']=1-room['door_fraction']
                room['board_wall']='south';room['door_y']=61.5-room['door_y']
    # Ground config room records and level records share objects after deepcopy.
    spec['stairs']=dict(bounds=core,portals=portals,path=paths,risers_per_storey=20,
                        flight_width=2.0,tread=.3,door_y=22,door_width=1.65)
    spec['lights']=[list(point(p,-1 if abs(p[2]-3.3)<.1 else 0)) for p in spec['lights'] if p[2]<9]
    spec['lights'].extend([[11,20.6,1.4],[11,20.6,-2.2]])
    spec['ground']['reception_front_sign']=[20.63,32.5,6.5]
    link['povo2']=spec;link['ground']['integrated']=True
    return boxes+added
