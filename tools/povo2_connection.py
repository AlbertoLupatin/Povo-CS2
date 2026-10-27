"""Photo-guided first-floor bridge and Povo 2 arrival, in local metres."""
import copy
import json
import math

try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing, wall_handrail
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing, wall_handrail


def extend_campus(boxes, levels, root, wall_height):
    spec=json.loads((root/'config/povo2_connection.json').read_text())
    boxes=list(boxes); z=spec['floor_local_metres']; top=z+wall_height
    spec=copy.deepcopy(spec)
    def add(name,lo,hi,mat='wall'):
        boxes.append(('academic_first_link_'+name,tuple(lo),tuple(hi),mat))
    def cut(hole, materials=('wall',)):
        nonlocal boxes
        boxes=[p for b in boxes for p in (subtract_box(b,hole) if b[3] in materials else [b])]
    def wall(name,a,b):add(name,(*a,z),(*b,top))
    def floor(name,r):
        a,b,c,d=r
        add(name+'_slab',(a,b,z-.22),(c,d,z),'floor_circulation')
        add(name+'_ceiling',(a,b,top-.06),(c,d,top),'ceiling_panel')
    # A continuous 3.5 m route cuts the original north shell and all edge trim.
    a,b,c,d=spec['povo1_corridor']
    cut(((a,-20.3,z-.01),(c,-19.7,z+2.8)))
    # The original first-floor slab/roof already supports the converted room area.
    add('p1_corridor_finish',(a,b,z+.001),(c,d,z+.012),'floor_circulation')
    # Cabinets and seats occupy the remaining east-side bay of former A203.
    for i in range(5):
        y=-31.8+i*1.9
        add(f'p1_locker_{i}',(23.35,y,z),(23.92,y+1.65,z+1.85),'seat_wood')
        add(f'p1_locker_handle_{i}',(23.3,y+.8,z+.9),(23.35,y+.84,z+1.05),'metal_dark')
    add('p1_bench_seat',(20.65,-24.5,z+.42),(23.3,-23.95,z+.5),'seat_wood')
    for x in (20.8,23.1):add('p1_bench_leg_'+str(x),(x,-24.45,z),(x+.08,-24,z+.42),'metal_dark')
    # Bridge: glazed sides, steel posts, horizontal louvers and alternating braces.
    a,b,c,d=spec['bridge']; floor('bridge',spec['bridge'])
    for side,x in (('west',a),('east',c)):
        add('bridge_'+side+'_glass',(x-.025,b,z+.08),(x+.025,d,top-.12),'window_glass')
        add('bridge_'+side+'_base',(x-.09,b,z),(x+.09,d,z+.12),'window_frame')
        add('bridge_'+side+'_head',(x-.09,b,top-.16),(x+.09,d,top),'window_frame')
        for i in range(11):
            y=b+i*3
            add(f'bridge_{side}_post_{i}',(x-.085,y-.07,z),(x+.085,y+.07,top),'metal_dark')
        for i in range(10):
            y=b+i*3
            add(f'bridge_finish_brace_{side}_{i}_'+('rise' if i%2==0 else 'fall'),
                (x-.09,y,z+.15),(x+.09,y+3,z+.27),'metal_dark')
        for i in range(12):
            h=z+.3+i*.24
            add(f'bridge_finish_louver_{side}_{i}',(x-.14,b,h),(x+.14,d,h+.065),'window_frame')
    # The bridge-exit alcoves remain; E1 and the northern bays are removed.
    for i,r in enumerate(spec['povo2_floor_parts']):floor('p2_'+str(i),r)
    wall('p2_west_lobby',(6.9,10),(7.1,14))
    wall('p2_east_lobby',(24.9,10),(25.1,14))
    wall('p2_south',(7,9.9),(25,10.1))
    wall('p2_east_alcove_end',(20,13.9),(25,14.1))
    wall('p2_east_corridor',(19.9,14),(20.1,26))
    wall('p2_north_end',(16.5,25.9),(20,26.1))
    cut(((16.5,9.7,z-.01),(20,10.3,z+2.8)))
    # Former W1 becomes a full-height enclosed switchback stairwell. As in
    # photos 64-66 and 4-8, two 3 m flights side by side fill its width and the
    # mid landing spans it; partitions close the rest of the old enclosure.
    ground=4.0; mid=(ground+z)/2; rise=(z-ground)/20; tread=.3
    south,north,gap=17.85,24.15,.3;split=(south+north)/2
    shaft=((7.1,south,z-.23),(14.2,north,z+.02))
    cut(shaft,('floor_circulation',))
    for name,a,b in [('west',(6.9,14),(7.1,26)),
                     ('south',(7,13.9),(16.5,14.1)),
                     ('north',(7,25.9),(16.5,26.1)),
                     ('east',(16.4,14),(16.6,26))]:
        add('p2_stair_wall_'+name,(*a,ground),(*b,top))
    add('p2_stair_partition_south',(7.1,south-.1,ground),(16.4,south,top))
    add('p2_stair_partition_north',(7.1,north,ground),(16.4,north+.1,top))
    # Independent lower floor/vestibule; the rest of Povo 2 stays closed.
    boxes.append(('p2_compact_ground_slab',(7,14,ground-.22),(20,26,ground),'floor_circulation'))
    for name,a,b in [('east',(19.9,14),(20.1,26)),
                     ('south',(16.5,13.9),(20,14.1)),
                     ('north',(16.5,25.9),(20,26.1))]:
        add('p2_lower_wall_'+name,(*a,ground),(*b,z-.22))
    add('p2_lower_ceiling',(16.5,14,z-.28),(20,26,z-.22),'ceiling_panel')
    # Upper landing -> westbound flight -> landing -> eastbound flight -> lower landing.
    up0,up1,lo0,lo1=south,split-gap/2,split+gap/2,north
    add('p2_stair_middle_landing',(7.1,south,mid-.22),(11.2,north,mid),'floor_p2_tile')
    path=[]
    for i in range(10):
        x0=14.2-(i+1)*tread; h=z-(i+1)*rise
        add('p2_stair_upper_step_'+str(i),(x0,up0,ground),(x0+tread,up1,h),'floor_p2_tile')
        path.append([x0+tread/2,(up0+up1)/2,h])
    path.extend([[9.15,(up0+up1)/2,mid],[9.15,(lo0+lo1)/2,mid]])
    for i in range(10):
        x0=11.2+i*tread; h=mid-(i+1)*rise
        add('p2_stair_lower_step_'+str(i),(x0,lo0,ground-.02),(x0+tread,lo1,h),'floor_p2_tile')
        path.append([x0+tread/2,(lo0+lo1)/2,h])
    # Railings line the well, wrap its landing end and guard the upper opening;
    # wall handrails run along the partitions.
    rails=[]
    railing(add,rails,'p2_stair_well_upper',(14.2,up1,z),(11.2,up1,mid))
    railing(add,rails,'p2_stair_well_lower',(11.2,lo0,mid),(14.2,lo0,ground))
    railing(add,rails,'p2_stair_well_end',(11.2,up1,mid),(11.2,lo0,mid),posts=False)
    railing(add,rails,'p2_stair_guard_east',(14.2,up1,z),(14.2,lo1,z))
    wall_handrail(rails,'p2_stair_wall_upper',(14.2,up0+.06,z),(11.2,up0+.06,mid))
    wall_handrail(rails,'p2_stair_wall_lower',(11.2,lo1-.06,mid),(14.2,lo1-.06,ground))
    rails=[dict(r,name='academic_first_link_'+r['name']) for r in rails]
    portals=[]
    for name,h,y in [('upper',z,20),('lower',ground,22)]:
        cut(((16.3,y-.825,h-.01),(16.7,y+.825,h+2.2)))
        for side,edge in [('south',y-.825),('north',y+.825)]:
            add(f'p2_stair_{name}_door_{side}',(16.55,edge-.025,h+.02),(17.35,edge+.025,h+2.18),'door_black')
            add(f'p2_stair_{name}_panic_{side}',(16.65,edge-.05,h+1.0),(17.25,edge+.05,h+1.045),'stair_red')
        for edge in (y-.865,y+.825):
            add(f'p2_stair_{name}_frame_{edge}',(16.38,edge,h),(16.66,edge+.04,h+2.24),'metal_dark')
        add(f'p2_stair_{name}_frame_head',(16.38,y-.865,h+2.2),(16.66,y+.865,h+2.24),'metal_dark')
        add(f'p2_stair_{name}_finish_sign',(16.605,y-.55,h+2.36),(16.64,y+.55,h+2.66),'sign_blue')
        portals.append(dict(centre=[16.5,y,h],width=1.65,height=2.2))
    spec['stair']=dict(id='p2_compact',bounds=[7,14,16.5,26],shaft=[list(p) for p in shaft],
        risers=20,rise=rise,tread=tread,width=up1-up0,rails=rails,bottom=[15.2,22,ground],
        top=[15.2,20,z],middle=[9.15,split,mid],portals=portals,path=path)
    spec['ground']=dict(id='p2_compact_ground',floor_elevation_local=ground,
        audit_stations=[dict(id='stair_bottom',point=[15.2,22]),
                        dict(id='lower_door_inside',point=[15.85,22]),
                        dict(id='lower_door_hall',point=[17.2,22]),
                        dict(id='lower_landing',point=[18.25,22])])
    # Furnished arrival lobby and print station match photos 62-63 in broad form.
    for y in (11,):
        add('p2_lobby_bench_'+str(y),(8,y,z+.42),(12,y+.65,z+.5),'seat_wood')
        for x in (8.2,11.7):add(f'p2_bench_leg_{y}_{x}',(x,y+.08,z),(x+.1,y+.55,z+.42),'metal_dark')
    add('p2_printer_body',(23.5,11.4,z),(24.55,12.25,z+1.05),'sign_white')
    add('p2_printer_top',(23.45,11.35,z+1.05),(24.6,12.3,z+1.2),'window_frame')
    add('p2_printer_console',(23.65,11.3,z+.86),(24.15,11.35,z+1.02),'metal_dark')
    # Keep the two glazed arrival alcoves and a west stairwell window.
    for side,x in (('west',7),('east',25)):
        spans=((10.7,13.3),(15,17.5)) if side=='west' else ((10.7,13.3),)
        for j,(y0,y1) in enumerate(spans):
            cut(((x-.3,y0,z+.75),(x+.3,y1,z+2.85)))
            add(f'p2_window_{side}_{j}',(x-.015,y0,z+.75),(x+.015,y1,z+2.85),'window_glass')
            for i in range(math.ceil((y1-y0)/1.5)+1):
                y=min(y1,y0+i*1.5)
                add(f'p2_window_{side}_{j}_mullion_{i}',(x-.06,y-.025,z+.75),(x+.06,y+.025,z+2.85),'window_frame')
    # Open glazed fire-door leaves at both bridge ends, kept outside walking lane.
    for name,y in (('povo1',-19.75),('povo2',10.25)):
        # Park the Povo 2 leaves back along the bridge, leaving the alcoves
        # and the separate ladder doorway reachable from its arrival lobby.
        if name=='povo2':y-=1.25
        for side,x in (('west',16.55),('east',19.95)):
            add(f'{name}_bridge_door_{side}_glass',(x-.025,y,z+.05),(x+.025,y+1.25,z+2.65),'window_glass')
            for h in (z+.05,z+1.05,z+2.6):
                add(f'{name}_bridge_door_{side}_bar_{h}',(x-.05,y,h),(x+.05,y+1.25,h+.05),'window_frame')
            for edge in (y,y+1.25):
                add(f'{name}_bridge_door_{side}_edge_{edge}',(x-.05,edge,z+.05),(x+.05,edge+.05,z+2.65),'window_frame')
    spec['lights']=[(18.25,y,z+2.9) for y in (-31,-25,-18,-13,-8,-3,2,7,12,17,22,24.5)]
    spec['lights'].extend([(10.5,12,z+2.9),(22.5,12,z+2.9),(11,19,z+2.9),
                           (11,24,z+2.9),(12,20.6,8.6),(18.25,22,6.85),(15.4,24,6.85)])
    # Fixtures follow each route and room light position.
    for i,(x,y,h) in enumerate(spec['lights']):
        add(f'route_finish_fixture_{i}_rim',(x-.3,y-.3,h+.25),(x+.3,y+.3,h+.3),'window_frame')
        add(f'route_finish_fixture_{i}_diffuser',(x-.26,y-.26,h+.24),(x+.26,y+.26,h+.25),'light_diffuser')
    spec['audit_stations']=[dict(id='link_'+str(i),point=[18.25,y]) for i,y in enumerate((-35.2,-30,-22,-19,-10,0,9,11,17,23,25))]
    spec['audit_stations'].extend([dict(id='west_alcove',point=[10.5,12.8]),
        dict(id='east_alcove',point=[22,12.8]),dict(id='stair_upper_inside',point=[15.2,20]),
        dict(id='stair_upper_hall',point=[17.2,20])])
    spec['nav_seeds']=[[18.25,y,z+.15] for y in (-30,-10,9,12,17,23,25)]
    spec['nav_seeds'].extend([[15.2,20,z+.15],[18.25,22,ground+.15],[15.2,22,ground+.15],
                              [10.45,20.61,mid+.15]])
    # 27 October sketch: stair east face aligns with reception at E=20.5.
    dx=spec.get('stair_offset_east',0)
    if dx:
        def shift(p):return [p[0]+dx,*p[1:]]
        def rect(r):return [r[0]+dx,r[1],r[2]+dx,r[3]]
        moved=('academic_first_link_p2_stair_', 'academic_first_link_p2_lower_',
               'academic_first_link_p2_1_', 'academic_first_link_p2_2_',
               'academic_first_link_p2_east_corridor', 'academic_first_link_p2_north_end',
               'academic_first_link_p2_window_west_1', 'p2_compact_ground_slab')
        boxes=[(n,tuple(shift(lo)),tuple(shift(hi)),m) if n.startswith(moved) else (n,lo,hi,m)
               for n,lo,hi,m in boxes]
        boxes=[(n,(24,lo[1],lo[2]),(25,hi[1],hi[2]),m)
               if n=='academic_first_link_p2_east_alcove_end' else (n,lo,hi,m)
               for n,lo,hi,m in boxes]
        # Close the unused strip west of the relocated enclosure at bridge level.
        add('p2_west_return',(7,13.9,z),(7+dx,14.1,top))
        stair=spec['stair'];stair['bounds']=rect(stair['bounds'])
        for key in ('top','bottom','middle'):stair[key]=shift(stair[key])
        for key in ('shaft','path'):stair[key]=[shift(p) for p in stair[key]]
        for rail in stair['rails']:
            for key in ('a','b'):rail[key]=shift(rail[key])
        for portal in stair['portals']:portal['centre']=shift(portal['centre'])
        spec['povo2_floor_parts']=[r if i==0 else rect(r) for i,r in enumerate(spec['povo2_floor_parts'])]
        spec['povo2_corridor']=rect(spec['povo2_corridor'])
        for station in spec['audit_stations']:
            if station['point'][1]>=14:station['point']=shift(station['point'])
            if station['id']=='link_8':station['point'][1]=17.2
        for station in spec['ground']['audit_stations']:station['point']=shift(station['point'])
        spec['lights']=[shift(p) if p[1]>=14 and p[0]<20.5 else p for p in spec['lights']]
        spec['nav_seeds']=[shift(p) if p[1]>=14 else p for p in spec['nav_seeds']]
    levels[1]['connection']=spec
    return boxes
