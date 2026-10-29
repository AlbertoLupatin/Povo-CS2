"""Conservative room-type fit-outs for playable rooms left as empty shells.

These are estimated furnishings, not newly surveyed room plans. Existing walls,
doors, stairs and circulation keep their source registration.
"""
import math

try:
    from .povo_interior_fixtures import office_frame, office_point
except ImportError:
    from povo_interior_fixtures import office_frame, office_point


def overlaps(a,b):
    return all(a[0][i]<b[1][i]-1e-7 and a[1][i]>b[0][i]+1e-7 for i in range(3))


def furnish(boxes,levels,stair,origin):
    result=list(boxes);routes=[]
    for segment in stair.get('segments',[stair]):
        for core in segment['cores']:
            routes.extend(core['path'])
            for portal in core['enclosure']['portals']:routes.append(portal['centre'])
    for segment in stair.get('courtyard',{}).get('segments',[]):routes.extend(segment['path'])
    protected=[((x-.46,y-.46,z+.02),(x+.46,y+.46,z+1.9)) for x,y,z in routes]
    for level in levels:
        z=level['floor_elevation_metres']-origin[2]
        for room in level['rooms']:
            if not room.get('playable',True) or isinstance(room.get('fitout'),dict):continue
            kind=room['kind']
            if kind not in ('office','laboratory','meeting','restroom','service'):continue
            bounds=room['footprint_local_metres'];a,b,c,d=bounds
            front={'u_min':'south','u_max':'north','v_min':'west','v_max':'east'}[room['door_side']]
            frame=office_frame(bounds,z,front);w,depth=frame[3:]
            fraction=room['door_fraction']
            door_u=w*(1-fraction if front in ('north','west') else fraction)
            prefix=level['id']+'_'+room['id']+'_furnishing'
            local=[];points=[];desks=0;toilets=0;basins=0
            def world(u,v):return office_point(frame,u,v,0)[:2]
            def box(name,u,v,width,length,low,high,mat='office_light'):
                p=office_point(frame,u,v,low);q=office_point(frame,u+width,v+length,high)
                return (prefix+'_'+name,tuple(min(x,y) for x,y in zip(p,q)),
                        tuple(max(x,y) for x,y in zip(p,q)),mat)
            near=[v for v in result if v[1][0]<c+.1 and v[2][0]>a-.1
                  and v[1][1]<d+.1 and v[2][1]>b-.1
                  and v[2][2]>z+.03 and v[1][2]<z+2.25]
            floors=[(lo,hi) for _,lo,hi,m in result if m.startswith('floor_') and abs(hi[2]-z)<.025
                    and lo[0]<c and hi[0]>a and lo[1]<d and hi[1]>b]
            reserved=[p for p in protected if p[0][0]<c and p[1][0]>a and p[0][1]<d and p[1][1]>b
                      and p[0][2]<z+2.3 and p[1][2]>z]
            # Keep the real offset doorway and its approach clear.
            approach=[(door_u,.65),(w/2,1.05)]
            if kind!='meeting':approach.append((w/2,depth/2))
            room_paths=[]
            for p,q in zip(approach,approach[1:]):
                count=max(1,math.ceil(math.dist(p,q)/.2))
                for j in range(count+1):
                    u,v=[p[k]+(q[k]-p[k])*j/count for k in range(2)];x,y=world(u,v)
                    room_paths.append(((x-.44,y-.44,z+.02),(x+.44,y+.44,z+1.9)))
            def valid(group):
                for _,lo,hi,_ in group:
                    if lo[0]<a+.1 or hi[0]>c-.1 or lo[1]<b+.1 or hi[1]>d-.1:return False
                    if any(overlaps((lo,hi),(p,q)) for _,p,q,_ in [*near,*local]):return False
                    if any(overlaps((lo,hi),p) for p in [*reserved,*room_paths]):return False
                    if lo[2]<=z+.03:
                        for x,y in ((lo[0],lo[1]),(lo[0],hi[1]),(hi[0],lo[1]),(hi[0],hi[1])):
                            if not any(p[0]-.01<=x<=q[0]+.01 and p[1]-.01<=y<=q[1]+.01 for p,q in floors):return False
                return True
            def add(group):
                if valid(group):local.extend(group);return True
                return False
            def workstation(tag,u,v,width=1.5,computer=True):
                group=[box(tag+'_desk',u-width/2,v-.325,width,.65,.73,.79,'desk_dark'),
                       box(tag+'_chair_seat',u-.24,v-1.04,.48,.48,.43,.49,'office_dark'),
                       box(tag+'_chair_back',u-.24,v-1.08,.48,.055,.49,1.02,'office_dark'),
                       box(tag+'_chair_base',u-.18,v-.98,.36,.36,.03,.43,'window_frame')]
                for dx in (-width/2+.08,width/2-.14):
                    for dy in (-.25,.19):group.append(box(tag+f'_leg_{dx}_{dy}',u+dx,v+dy,.06,.06,0,.73,'window_frame'))
                if computer:
                    group.extend([box(tag+'_monitor',u-.25,v+.15,.5,.055,.91,1.25,'office_screen'),
                                  box(tag+'_monitor_stand',u-.035,v+.13,.07,.12,.79,.91,'window_frame'),
                                  box(tag+'_keyboard',u-.22,v-.17,.44,.15,.79,.815,'office_dark')])
                return group
            if kind in ('office','service'):
                width=min(1.5,w-.5)
                for v in (depth-.52,depth/2,1.7):
                    for u in (w-.25-width/2,.25+width/2,w/2):
                        group=workstation('workstation',u,v,width,kind=='office')
                        if kind=='service':group.append(box('photocopier',u-.35,v-.27,.7,.54,.79,1.35,'office_gray'))
                        if add(group):desks=1;break
                    if desks:break
            elif kind=='laboratory':
                for side,u in enumerate((1.0,w-1.0)):
                    for row,v in enumerate((2.3,4.55,6.8,9.05)):
                        if v+.4>depth-.15:continue
                        if add(workstation(f'bench_{side}_{row}',u,v,min(1.5,w/3),row==0)):desks+=1
            elif kind=='meeting':
                width=min(2.6,w-2.4);length=min(3.0,depth-3.0)
                for fraction in (.4,.5,.6):
                    u=w/2;v=depth*fraction
                    group=[box('meeting_table',u-width/2,v-length/2,width,length,.73,.79,'seat_wood')]
                    for x in (-width/2+.1,width/2-.16):
                        for y in (-length/2+.1,length/2-.16):group.append(box(f'meeting_leg_{x}_{y}',u+x,v+y,.06,.06,0,.73,'window_frame'))
                    for side in (-1,1):
                        for row,y in enumerate((-.7,.7)):
                            x=u+side*(width/2+.4)
                            group.extend([box(f'meeting_chair_{side}_{row}',x-.23,v+y-.23,.46,.46,.43,.49,'office_dark'),
                                          box(f'meeting_back_{side}_{row}',x+side*.20-.025,v+y-.23,.05,.46,.49,1.02,'office_dark')])
                    if add(group):desks=1;break
                points.extend([world(.7,depth*.4),world(w-.7,depth*.4)])
            else:
                count=max(1,min(3,int((w-.4)/1.3)));span=(w-.4)/count
                group=[]
                for i in range(count):
                    u=.2+i*span;mid=u+span/2;rear=depth-.2;front_v=rear-2.05
                    group.extend([box(f'toilet_{i}_bowl',mid-.25,rear-.82,.5,.6,.28,.40,'sanitary_white'),
                                  box(f'toilet_{i}_tank',mid-.29,rear-.20,.58,.18,.38,.83,'sanitary_white'),
                                  box(f'toilet_{i}_pedestal',mid-.15,rear-.68,.3,.44,0,.30,'sanitary_white'),
                                  box(f'toilet_{i}_water',mid-.16,rear-.69,.32,.34,.40,.412,'sanitary_water'),
                                  box(f'cubicle_{i}_left',u,front_v,.055,2.05,.03,2.1,'office_gray'),
                                  box(f'cubicle_{i}_front_left',u,front_v,.16,.055,.03,2.1,'office_gray'),
                                  box(f'cubicle_{i}_front_right',u+span-.16,front_v,.16,.055,.03,2.1,'office_gray'),
                                  box(f'cubicle_{i}_door_open',u+.18,front_v+.06,.045,.86,.04,1.99,'office_light')])
                    points.append(world(mid,rear-1.45))
                group.append(box('cubicle_end',w-.25,depth-2.25,.055,2.05,.03,2.1,'office_gray'))
                for i in range(min(2,max(1,int((depth-3.3)/1.05)))):
                    v=.7+i*.9
                    group.extend([box(f'basin_{i}',.15,v,.6,.68,.76,.88,'sanitary_white'),
                                  box(f'basin_{i}_water',.25,v+.11,.34,.43,.88,.895,'sanitary_water'),
                                  box(f'basin_{i}_tap',.16,v+.3,.055,.08,.88,1.08,'window_frame'),
                                  box(f'basin_{i}_mirror',.105,v,.025,.68,1.18,2.0,'mirror_silver')])
                    points.append(world(1.3,v+.34));basins+=1
                group.append(box('hand_dryer',w-.28,.9,.15,.35,1.0,1.35,'office_light'))
                if not add(group):raise ValueError('Sanitary fit-out intersects circulation/structure: '+room['id'])
                toilets=count
            if not local:raise ValueError('No supported furnishing layout fits '+level['id']+'/'+room['id'])
            if kind!='restroom':
                for u in (.2,w-.7):
                    if add([box('storage_'+str(u),u,depth-.75,.5,.55,0,1.8,'office_gray')]):break
            points=[world(*p) for p in approach]+points
            seats=sum('_chair_seat' in n or '_meeting_chair_' in n for n,*_ in local)
            room['fitout']=dict(kind=kind,desks=desks,toilets=toilets,washbasins=basins,rows=[],seats=seats,
                furniture=(['toilets','washbasins','mirrors','hand dryer','cubicles'] if kind=='restroom' else
                           ['meeting table','chairs'] if kind=='meeting' else ['workbenches','chairs','storage'] if kind=='laboratory' else
                           ['photocopier','work surface'] if kind=='service' else ['desk','computer','chair','storage']),
                audit_points_local_metres=[list(p) for p in points],
                status='Estimated room-type furnishing; wall plan retained, exact furniture placement not surveyed')
            result.extend(local)
    return result
