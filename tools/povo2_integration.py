"""Place the approved Povo 2 lower plan against the completed compact stair."""
import copy

try:
    from .povo2_planimetry import build as build_draft
    from .povo_room_fitout import subtract_box
    from .povo_stairs import shifted
except ImportError:
    from povo2_planimetry import build as build_draft
    from povo_room_fitout import subtract_box
    from povo_stairs import shifted


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
    paths=[];rails=[]
    for lower,zshift in ((-1,-3.6),(-2,-7.2)):
        for name,lo,hi,mat in prototype:
            # The upper opening's east guard would block the next flight's arrival.
            if '_guard_east' in name:continue
            add('p2_extended_'+str(lower)+'_'+name.replace('academic_first_link_p2_stair_',''),
                (lo[0],lo[1],lo[2]+zshift),(hi[0],hi[1],hi[2]+zshift),mat)
        paths.append(dict(lower_floor=lower,points=[list((x,y,z+zshift)) for x,y,z in
            [compact['top'],*compact['path'],compact['bottom']]]))
        rails.extend(shifted([r for r in compact['rails'] if '_guard_east' not in r['name']],zshift,
            lambda n:'p2_extended_'+str(lower)+'_'+n.replace('academic_first_link_p2_stair_','')))
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
    (sx0,sy0,_),(sx1,sy1,_)=compact['shaft']
    for z in (4,.4):
        hole=((sx0,sy0,z-.3),(sx1,sy1,z+.01))
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
                fitout=room['fitout']
                fitout['teaching_side']='south';fitout['window_side']='west'
                fitout['audit_points_local_metres']=[list(point(p)) for p in fitout['audit_points_local_metres']]
                for row in fitout['rows']:
                    lo,hi=row['bounds_local_metres'];aa=point(lo);bb=point(hi)
                    row['bounds_local_metres']=[list(min(a,b) for a,b in zip(aa,bb)),list(max(a,b) for a,b in zip(aa,bb))]
    # Ground config room records and level records share objects after deepcopy.
    spec['stairs']=dict(bounds=core,portals=portals,path=paths,risers_per_storey=20,
                        flight_width=compact['width'],tread=.3,door_y=22,door_width=1.65,rails=rails)
    spec['lights']=[list(point(p,-1 if abs(p[2]-3.3)<.1 else 0)) for p in spec['lights'] if p[2]<9]
    spec['lights'].extend([[9.15,21,1.4],[9.15,21,-2.2]])
    spec['ground']['reception_front_sign']=[20.63,32.5,6.5]
    link['povo2']=spec;link['ground']['integrated']=True
    return lift(boxes+added,spec,link)


def lift(boxes, spec, link):
    """Povo 2's lift beside the stair door, a ladder shaft from -1 to +1.

    Like Povo 1's, a CS2 moving platform is untested, so a ladder runs up the
    south wall. It opens north into the ground hall and west into the -1
    corridor and the +1 bridge corridor; ledges at ground and +1 leave the
    ladder side open. spec['lift']['ladder'] becomes CS2's climbable surface.
    """
    lift=link.get('lift')
    if not lift:return boxes
    # Rounded so the shaft and its doorways share exact edges (no slivers).
    x0,y0,x1,y1=lift['shaft'];ga,gb=lift['ground_opening_east'];sa,sb=lift['side_opening_north']
    zb,zg,zu=.4,4.,7.6;top=10.95;t=.1
    x0i,y0i,x1i,y1i=(round(v,3) for v in (x0+t,y0+t,x1-t,y1-t))
    result=[p for b in boxes for p in subtract_box(b,((x0,y0,zb-.22),(x1,y1,top)))]
    # Doorways through the shaft and the corridor/hall walls it backs onto;
    # the ground hall's lockers in front of the doorway go too.
    result=[b for b in result if not ('_locker_' in b[0] and b[1][0]<gb+.1 and b[2][0]>ga-.1
                                      and b[1][1]<y1+1.3 and b[2][1]>y1)]
    holes=[((ga,round(y1-.2,3),zg-.01),(gb,y1+.4,zg+2.2)),*[((x0-.3,sa,z-.01),(x0+.2,sb,z+2.2)) for z in (zb,zu)]]
    for name,lo,hi in (('wall_west',(x0,y0,zb),(x0i,y1,top)),('wall_east',(x1i,y0,zb),(x1,y1,top)),
                       ('wall_south',(x0,y0,zb),(x1,y0i,top)),('wall_north',(x0,y1i,zb),(x1,y1,top)),
                       ('roof',(x0,y0,top),(x1,y1,top+.1))):
        result.append(('p2_lift_'+name,lo,hi,'wall'))
    for hole in holes:
        result=[p for b in result for p in (subtract_box(b,hole) if b[3]=='wall' else [b])]
    inner=(x0i,y0i,x1i,y1i);ledge=round(inner[1]+1.0,3)
    result+=[('p2_basement_lift_floor',(inner[0],inner[1],zb-.22),(inner[2],inner[3],zb),'floor_p2_tile'),
             ('p2_ground_lift_ledge',(inner[0],ledge,zg-.22),(inner[2],inner[3],zg),'floor_p2_tile'),
             ('academic_first_link_p2_lift_ledge',(inner[0],ledge,zu-.22),(inner[2],inner[3],zu),'floor_circulation'),
             # Thresholds across the wall thicknesses.
             ('p2_ground_lift_threshold',(ga,inner[3],zg-.22),(gb,y1+.2,zg),'floor_p2_tile'),
             ('p2_basement_lift_threshold',(x0-.2,sa,zb-.22),(inner[0],sb,zb),'floor_p2_tile'),
             ('academic_first_link_p2_lift_threshold',(x0-.2,sa,zu-.22),(inner[0],sb,zu),'floor_circulation')]
    for z,label in ((zg,'ground'),(zu,'first')):
        result.append(('p2_lift_'+label+'_ledge_finish_edge',(inner[0],ledge,z),(inner[2],ledge+.04,z+.012),'metal_dark'))
    # Steel portals and call buttons on the corridor sides.
    for z,label in ((zb,'basement'),(zu,'first')):
        for i,y in enumerate((sa-.06,sb)):
            result.append((f'p2_lift_{label}_portal_jamb_{i}',(x0-.3,y,z),(x0-.1,y+.06,z+2.26),'metal_dark'))
        result.append((f'p2_lift_{label}_portal_head',(x0-.3,sa-.06,z+2.2),(x0-.1,sb+.06,z+2.26),'metal_dark'))
        result.append((f'p2_lift_{label}_call_button',(x0-.12,sb+.2,z+1.05),(x0-.1,sb+.32,z+1.25),'sign_white'))
    for i,x in enumerate((ga-.06,gb)):
        result.append((f'p2_lift_ground_portal_jamb_{i}',(x,y1+.1,zg),(x+.06,y1+.3,zg+2.26),'metal_dark'))
    result.append(('p2_lift_ground_portal_head',(ga-.06,y1+.1,zg+2.2),(gb+.06,y1+.3,zg+2.26),'metal_dark'))
    result.append(('p2_lift_ground_call_button',(gb+.2,y1+.28,zg+1.05),(gb+.32,y1+.3,zg+1.25),'sign_white'))
    # Visible ladder on the south wall: rails and rungs, no collision (`_finish_`).
    cx=(inner[0]+inner[2])/2;a,b=cx-.3,cx+.3;wall=inner[1]
    for i,x in enumerate((a,b)):
        result.append((f'p2_lift_ladder_finish_rail_{i}',(x-.025,wall,zb),(x+.025,wall+.16,zu+1.0),'metal_dark'))
    for i in range(int((zu+.9-zb-.25)/.28)+1):
        h=zb+.25+i*.28
        result.append((f'p2_lift_ladder_finish_rung_{i}',(a,wall+.1,h),(b,wall+.14,h+.035),'metal_dark'))
    mid=(inner[1]+inner[3])/2
    spec['lift']=dict(shaft=lift['shaft'],ladder=[[a,wall,zb],[b,wall+.2,zu+.4]])
    spec['lights'].extend([[cx,mid,z+2.6] for z in (zb,zg,zu)])
    for level in spec['levels']:
        if level['floor']==0:level['audit_stations'].append(dict(id='lift_ledge',point=[cx,(ledge+inner[3])/2]))
        if level['floor']==-1:level['audit_stations'].append(dict(id='lift_floor',point=[cx,(sa+sb)/2]))
    link['audit_stations'].append(dict(id='p2_lift_ledge',point=[cx,(ledge+inner[3])/2]))
    return result
