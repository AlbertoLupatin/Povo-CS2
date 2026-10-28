"""Shared reception offices, posed staff and sanitary fixtures in local metres."""

import math


COLORS = {
    "reception_glass": (180, 191, 194),
    "office_gray": (126, 132, 135), "office_light": (176, 181, 182),
    "office_dark": (65, 73, 78), "office_screen": (34, 47, 53),
    "office_display": (110, 138, 146), "mirror_silver": (149, 164, 169),
    "staff_shirt": (139, 150, 155), "staff_trousers": (65, 73, 81),
    "staff_skin": (184, 148, 127), "staff_hair": (45, 43, 42),
}


def office_frame(bounds, z, front):
    a,b,c,d=bounds
    return {"east": ((c,b,z),(0,1),(-1,0),d-b,c-a),
            "west": ((a,d,z),(0,-1),(1,0),d-b,c-a),
            "north": ((c,d,z),(-1,0),(0,-1),c-a,d-b),
            "south": ((a,b,z),(1,0),(0,1),c-a,d-b)}[front]


def office_point(frame, u, v, h):
    base,across,inside,_,_=frame
    return (base[0]+u*across[0]+v*inside[0],
            base[1]+u*across[1]+v*inside[1],base[2]+h)


def staff_positions(width, depth):
    return [(width*.5,1.85,True),
            (width*.27,depth-.85,False),
            (width*.73,depth-.85,False)]



def reception_boxes(prefix, bounds, z, height, front='west'):
    a,b,c,d=bounds
    panels={'west':((a-.06,b,z),(a+.06,d,z+height)),
            'east':((c-.06,b,z),(c+.06,d,z+height)),
            'south':((a,b-.06,z),(c,b+.06,z+height)),
            'north':((a,d-.06,z),(c,d+.06,z+height))}
    opposite={'west':'east','east':'west','south':'north','north':'south'}
    boxes=[]
    for side,(lo,hi) in panels.items():
        label='front' if side==front else 'back' if side==opposite[front] else side
        boxes.append((prefix+'_'+label,lo,hi,'reception_glass'))
    axis=1 if front in ('west','east') else 0
    fixed={'west':a,'east':c,'south':b,'north':d}[front]
    start,end=(b,d) if axis else (a,c)
    count=max(1,round((end-start)/1.5))
    for i in range(count+1):
        t=start+(end-start)*i/count
        lo=[fixed-.09,t-.025,z];hi=[fixed+.09,t+.025,z+height]
        if not axis:lo[:2]=reversed(lo[:2]);hi[:2]=reversed(hi[:2])
        boxes.append((prefix+'_frame_'+str(i),tuple(lo),tuple(hi),'window_frame'))
    for h in (.08,.95,2.6):
        lo=[fixed-.09,start,z+h];hi=[fixed+.09,end,z+h+.04]
        if not axis:lo[:2]=reversed(lo[:2]);hi[:2]=reversed(hi[:2])
        boxes.append((prefix+'_rail_'+str(h),tuple(lo),tuple(hi),'window_frame'))
    boxes.extend(reception_office_boxes(prefix,bounds,z,front))
    return boxes


def reception_office_boxes(prefix, bounds, z, front):
    frame=office_frame(bounds,z,front);width,depth=frame[3:];boxes=[]
    def add(name,u,v,w,l,bottom,top,mat='office_gray'):
        p=office_point(frame,u,v,bottom);q=office_point(frame,u+w,v+l,top)
        boxes.append((prefix+'_'+name,tuple(min(a,b) for a,b in zip(p,q)),
                      tuple(max(a,b) for a,b in zip(p,q)),mat))
    def chair(name,u,v,guest=False):
        add(name+'_seat',u-.25,v-.24,.5,.48,.43,.49,'office_dark')
        add(name+'_back',u-.25,v+(.18 if not guest else -.24),.5,.06,.49,1.03,'office_dark')
        add(name+'_pedestal',u-.045,v-.045,.09,.09,.08,.43,'window_frame')
        add(name+'_base',u-.3,v-.035,.6,.07,.045,.085,'office_dark')
        add(name+'_base_cross',u-.035,v-.3,.07,.6,.045,.085,'office_dark')
        for side in (-1,1):
            add(name+'_arm_'+str(side),u+side*.28-.025,v-.14,.05,.35,.66,.71,'office_dark')
    def workstation(name,u,v,w,front_desk=False):
        add(name+'_top',u-w/2,v-.36,w,.72,.74,.80,'office_light')
        for side in (-1,1):
            add(name+'_leg_'+str(side),u+side*(w/2-.13)-.035,v-.30,.07,.60,0,.74,'office_dark')
        add(name+'_modesty',u-w/2+.08,v-.31,w-.16,.045,.22,.70)
        add(name+'_drawers',u+w/2-.46,v-.24,.38,.55,.06,.7)
        for i in range(3):
            add(name+'_drawer_pull_'+str(i),u+w/2-.38,v+.32,.2,.025,.2+i*.17,.22+i*.17,'window_frame')
        add(name+'_monitor_stand',u-.035,v-.16,.07,.10,.80,.96,'office_dark')
        add(name+'_monitor_base',u-.17,v-.22,.34,.22,.80,.825,'office_dark')
        add(name+'_monitor',u-.31,v-.19,.62,.055,.94,1.32,'office_dark')
        add(name+'_display',u-.28,v-.132,.56,.008,.97,1.29,'office_display')
        add(name+'_keyboard',u-.22,v+.17,.44,.15,.80,.825,'office_dark')
        add(name+'_mouse',u+.30,v+.18,.065,.10,.80,.835,'office_dark')
        add(name+'_paper',u-w/2+.15,v+.03,.30,.22,.80,.82,'sanitary_white')
        chair(name+'_chair',u,v+.80)
        if front_desk:
            add(name+'_raised_counter',u-w/2,v-.40,w,.16,.97,1.02,'office_light')
    add('office_floor',.12,.12,width-.24,depth-.24,.001,.009,'floor_circulation')
    workstation('front_desk',width*.5,1.05,min(3.25,width-1.5),True)
    for i,u in enumerate((width*.27,width*.73)):
        workstation('back_desk_'+str(i),u,depth-1.65,min(1.7,width*.34))
    for i,(u,v) in enumerate(((width*.5,1.25),(width*.27,depth-1.65),(width*.73,depth-1.65))):
        add('office_light_'+str(i)+'_rim',u-.32,v-.30,.64,.60,3.215,3.24,'window_frame')
        add('office_light_'+str(i)+'_diffuser',u-.28,v-.26,.56,.52,3.20,3.215,'light_diffuser')
    for i,u in enumerate((.65,width-.65)):
        chair('visitor_chair_'+str(i),u,.42,True)
    # Storage down one side and a printer station complete the office.
    add('filing_cabinet',.15,2.35,.48,min(1.1,depth-2.8),0,1.22)
    for i in range(4):
        add('filing_pull_'+str(i),.64,2.55,.025,.5,.18+i*.25,.21+i*.25,'window_frame')
    add('printer',.19,2.55,.40,.55,1.22,1.45,'office_light')
    add('printer_output',.25,2.69,.28,.28,1.45,1.465,'sanitary_white')
    add('back_bookcase',width*.5-.30,depth-.45,.6,.30,0,1.85,'office_dark')
    for level in range(3):
        add('shelf_'+str(level),width*.5-.29,depth-.44,.58,.29,.45+level*.47,.48+level*.47,'office_light')
        for i in range(4):
            add(f'binder_{level}_{i}',width*.5-.25+i*.125,depth-.42,.08,.24,.49+level*.47,.82+level*.47)
    if depth>6.5:
        u=width*.5;v=depth*.52
        add('meeting_table',u-.8,v-.4,1.6,.8,.73,.79,'office_light')
        for side in (-1,1):
            add('meeting_leg_'+str(side),u+side*.65-.03,v-.30,.06,.60,0,.73,'office_dark')
        for i,du in enumerate((-.48,.48)):
            chair('meeting_chair_'+str(i),u+du,v+.77)
    return boxes


def restroom_boxes(level, room, z, height):
    """Four stalls, three basins and accessories, with an open central aisle."""
    a,b,c,d=room['footprint_local_metres'];prefix=level+'_'+room['id']
    boxes=[]
    def add(name,lo,hi,mat='sanitary_white'):
        boxes.append((prefix+'_'+name,tuple(lo),tuple(hi),mat))
    add('floor',(a+.1,b+.1,z),(c-.1,d-.1,z+.012),'floor_circulation')
    north=room['door_side']=='u_max';rear=b+.15 if north else d-.15
    direction=1 if north else -1
    def fixture(name,x,y,w,depth,bottom,top,mat='sanitary_white'):
        yy=rear+direction*y;end=yy+direction*depth
        add(name,(x,min(yy,end),z+bottom),(x+w,max(yy,end),z+top),mat)
    # An interior privacy panel screens the toilets from courtyard glazing.
    fixture('privacy_screen',a+.15,0,c-a-.3,.045,.04,2.18,'office_light')
    stations=[[(a+c)/2,(b+d)/2]]
    # Only as many stalls as keep the last cubicle door clear of the basins.
    stalls=max(1,min(4,int((c-a-2.45)/1.45)+1))
    for i in range(stalls):
        x=a+.25+i*1.45
        fixture(f'toilet_{i}_pedestal',x+.42,.28,.3,.48,0,.34)
        fixture(f'toilet_{i}_tank',x+.28,.065,.58,.2,.38,.83)
        fixture(f'toilet_{i}_bowl',x+.32,.26,.5,.58,.28,.39)
        fixture(f'toilet_{i}_water',x+.41,.40,.32,.29,.39,.402,'sanitary_water')
        for side,xx,yy,w,depth in (('left',x+.3,.25,.09,.62),('right',x+.81,.25,.09,.62),
                                   ('back',x+.39,.25,.42,.1),('front',x+.39,.77,.42,.1)):
            fixture(f'toilet_{i}_seat_'+side,xx,yy,w,depth,.4,.445)
        fixture(f'toilet_{i}_flush',x+.52,.045,.12,.035,.72,.76,'window_frame')
        fixture(f'cubicle_{i}_partition',x+1.35,.05,.06,1.95,.04,2.08,'office_gray')
        fixture(f'cubicle_{i}_front_left',x,1.95,.25,.06,.04,2.08,'office_gray')
        fixture(f'cubicle_{i}_front_right',x+1.30,1.95,.11,.06,.04,2.08,'office_gray')
        fixture(f'cubicle_{i}_door',x+.22,1.08,.045,.87,.05,1.96,'office_light')
        fixture(f'cubicle_{i}_door_handle',x+.265,1.18,.025,.13,.94,.98,'window_frame')
        fixture(f'cubicle_{i}_paper_holder',x+1.20,.62,.13,.16,.66,.83,'office_gray')
        fixture(f'cubicle_{i}_paper_roll',x+1.21,.64,.10,.12,.69,.80)
        fixture(f'cubicle_{i}_bin',x+1.03,.13,.25,.25,0,.40,'office_gray')
        stations.append([x+.78,rear+direction*1.46])
    fixture('basin_counter',c-.90,2.80,.75,3.2,.74,.81,'office_gray')
    fixture('mirror',c-.15,2.80,.025,3.2,1.18,2.05,'mirror_silver')
    for i in range(3):
        y=3+i*1.05;name='sink' if i==0 else 'sink_'+str(i)
        fixture(name+'_pedestal',c-.65,y+.16,.18,.32,0,.74)
        fixture(name+'_basin',c-.82,y,.58,.72,.81,.89)
        fixture(name+'_water',c-.72,y+.12,.34,.46,.89,.90,'sanitary_water')
        fixture(name+'_tap',c-.34,y+.30,.055,.07,.89,1.08,'window_frame')
        fixture(name+'_soap',c-.18,y+.76,.10,.17,1.00,1.25,'office_gray')
        stations.append([c-1.45,rear+direction*(y+.36)])
    fixture('hand_dryer',c-.28,6.40,.13,.42,1.02,1.40,'office_light')
    fixture('waste_bin',c-.62,7.00,.43,.43,0,.64,'office_dark')
    fixture('waste_bin_lid',c-.65,6.98,.49,.47,.64,.69,'office_gray')
    fixture('cleaning_cabinet',a+.18,3.0,.60,1.20,0,2.05,'office_light')
    fixture('cleaning_cabinet_handle',a+.79,3.50,.025,.20,.91,1.08,'window_frame')
    male=room.get('sex')=='male'
    if male:
        for i,y in enumerate((5.20,6.55)):
            fixture(f'urinal_{i}_body',a+.18,y,.40,.50,.45,1.08)
            fixture(f'urinal_{i}_basin',a+.23,y+.09,.30,.32,.47,.64,'sanitary_water')
            fixture(f'urinal_{i}_flush',a+.16,y+.2,.045,.10,1.15,1.29,'window_frame')
            stations.append([a+1.12,rear+direction*(y+.25)])
        fixture('urinal_privacy_divider',a+.14,6.08,.95,.055,.42,1.78,'office_gray')
    else:
        fixture('bench_seat',a+.18,5.30,.55,1.65,.43,.50,'office_gray')
        for y in (5.40,6.70):fixture('bench_leg_'+str(y),a+.23,y,.40,.10,0,.43,'office_dark')
        for i in range(3):fixture('wall_hook_'+str(i),a+.13,5.40+i*.5,.09,.05,1.65,1.69,'window_frame')
    room['fitout']=dict(seats=0,rows=[],furniture=['toilets','washbasins','dispensers','dryer','bins','storage'],
        audit_points_local_metres=stations,toilets=stalls,washbasins=3,urinals=2 if male else 0)
    return boxes


def reception_staff_mesh(prefix, bounds, z, front):
    """Rounded low-poly seated office staff, posed typing at the three desks."""
    frame=office_frame(bounds,z,front);faces=[]
    def tri(name,mat,p,q,r):
        faces.append((prefix+'_'+name,'campus_'+mat,[office_point(frame,*v) for v in (p,q,r)],None))
    def ellipsoid(name,mat,centre,radius,segments=10,rings=6,keep=None):
        def point(t,p):
            return (centre[0]+radius[0]*math.sin(t)*math.cos(p),
                    centre[1]+radius[1]*math.sin(t)*math.sin(p),centre[2]+radius[2]*math.cos(t))
        def emit(p,q,r):
            if keep is None or keep(tuple(sum(v[j] for v in (p,q,r))/3 for j in range(3))):tri(name,mat,p,q,r)
        top=point(0,0);bottom=point(math.pi,0)
        for j in range(segments):
            p0=2*math.pi*j/segments;p1=2*math.pi*(j+1)/segments
            emit(top,point(math.pi/rings,p0),point(math.pi/rings,p1))
            for i in range(1,rings-1):
                a=point(math.pi*i/rings,p0);b=point(math.pi*(i+1)/rings,p0)
                c=point(math.pi*(i+1)/rings,p1);d=point(math.pi*i/rings,p1)
                emit(a,b,c);emit(a,c,d)
            emit(point(math.pi*(rings-1)/rings,p0),bottom,point(math.pi*(rings-1)/rings,p1))
    def limb(name,mat,start,end,r0,r1=None):
        r1=r0 if r1 is None else r1
        axis=[end[i]-start[i] for i in range(3)];length=math.sqrt(sum(v*v for v in axis));axis=[v/length for v in axis]
        ref=(0,0,1) if abs(axis[2])<.9 else (1,0,0)
        cross=(axis[1]*ref[2]-axis[2]*ref[1],axis[2]*ref[0]-axis[0]*ref[2],axis[0]*ref[1]-axis[1]*ref[0])
        n=math.sqrt(sum(v*v for v in cross));u=[v/n for v in cross]
        v=(axis[1]*u[2]-axis[2]*u[1],axis[2]*u[0]-axis[0]*u[2],axis[0]*u[1]-axis[1]*u[0])
        def ring(c,r,j):
            t=2*math.pi*j/8
            return tuple(c[k]+r*(math.cos(t)*u[k]+math.sin(t)*v[k]) for k in range(3))
        for j in range(8):
            a=ring(start,r0,j);b=ring(end,r1,j);c=ring(end,r1,j+1);d=ring(start,r0,j+1)
            tri(name,mat,a,b,c);tri(name,mat,a,c,d)
            tri(name,mat,start,d,a);tri(name,mat,end,b,c)
    for i,(u,v,female) in enumerate(staff_positions(frame[3],frame[4])):
        tag=f'staff_{i}_'+('female' if female else 'male')
        shoulder=.17 if female else .205
        ellipsoid(tag+'_shirt','staff_shirt',(u,v,.99),(shoulder,.115,.235))
        ellipsoid(tag+'_hips','staff_trousers',(u,v,.65),(.18,.14,.12))
        limb(tag+'_waist','staff_shirt',(u,v,.67),(u,v,.89),.13,.15)
        limb(tag+'_neck','staff_skin',(u,v,1.18),(u,v,1.29),.055)
        ellipsoid(tag+'_head','staff_skin',(u,v-.015,1.385),(.103,.092,.135),12,8)
        if female:
            ellipsoid(tag+'_hair','staff_hair',(u,v+.02,1.375),(.125,.108,.19),12,8,
                      lambda p:p[2]>1.47 or p[1]>v+.015)
        else:
            ellipsoid(tag+'_hair','staff_hair',(u,v+.005,1.41),(.11,.098,.128),12,8,
                      lambda p:p[2]>1.45 or p[1]>v+.035)
        ellipsoid(tag+'_nose','staff_skin',(u,v-.111,1.38),(.021,.026,.027),8,4)
        for side in (-1,1):
            ellipsoid(tag+'_eye_'+str(side),'staff_hair',(u+side*.035,v-.100,1.414),(.012,.008,.009),8,4)
            shoulder_p=(u+side*shoulder,v,1.13);elbow=(u+side*.245,v-.17,.94);hand=(u+side*.17,v-.52,.817)
            limb(tag+'_upper_arm_'+str(side),'staff_shirt',shoulder_p,elbow,.069,.056)
            limb(tag+'_forearm_'+str(side),'staff_shirt',elbow,hand,.052,.035)
            ellipsoid(tag+'_hand_'+str(side),'staff_skin',hand,(.045,.069,.025),8,4)
            hip=(u+side*.10,v,.62);knee=(u+side*.12,v-.36,.49);ankle=(u+side*.12,v-.40,.12)
            limb(tag+'_thigh_'+str(side),'staff_trousers',hip,knee,.105,.085)
            limb(tag+'_shin_'+str(side),'staff_trousers',knee,ankle,.075,.055)
            ellipsoid(tag+'_shoe_'+str(side),'office_dark',(ankle[0],v-.47,.075),(.08,.15,.065),8,4)
    return faces


def campus_staff_meshes(levels):
    faces=[]
    for level in levels:
        z=level['floor_elevation_metres']-370
        for room in level['rooms']:
            if room['kind']=='reception':
                faces.extend(reception_staff_mesh(level['id']+'_'+room['id'],room['footprint_local_metres'],z,'east'))
    p2=next((level['connection'].get('povo2') for level in levels if level.get('connection')),None)
    if p2:
        faces.extend(reception_staff_mesh('p2_ground_reception',p2['ground']['reception'],4,'east'))
    return faces
