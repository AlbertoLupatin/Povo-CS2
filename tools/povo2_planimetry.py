"""Povo 2 entrance, empty B rooms, four-level grey stair and covered parking.

All coordinates are local metres in the existing campus frame. The standalone
review command never deploys assets or touches the running CS2 package.
"""
import copy
import json
from pathlib import Path

try:
    from .povo_room_fitout import subtract_box
    from .povo_interior_fixtures import reception_boxes
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_interior_fixtures import reception_boxes

ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    'floor_p2_tile': (158, 159, 154), 'floor_p2_asphalt': (76, 79, 80),
    'reception_frosted': (149, 167, 171), 'p2_accent_green': (121, 154, 56),
    'parking_line': (213, 213, 198), 'car_blue': (54, 79, 108),
    'car_silver': (151, 154, 155), 'car_red': (120, 49, 42),
    'car_tyre': (29, 30, 31), 'car_glass': (54, 69, 76),
}


def build(root=ROOT, wall_height=3.35):
    spec = copy.deepcopy(json.loads((root/'config/povo2_planimetry.json').read_text()))
    boxes = []

    def add(name, lo, hi, mat='wall'):
        if any(a >= b for a, b in zip(lo, hi)):
            raise ValueError('Invalid Povo 2 box: '+name)
        boxes.append((name, tuple(lo), tuple(hi), mat))

    def cut(hole, materials=('wall',)):
        nonlocal boxes
        boxes = [p for b in boxes for p in (subtract_box(b, hole) if b[3] in materials else [b])]

    def slab(name, r, z, mat='floor_p2_tile'):
        a, b, c, d = r
        add(name, (a, b, z-.22), (c, d, z), mat)

    def shell(level, r):
        a,b,c,d=r;z=level['z'];prefix=level['id']
        slab(prefix+'_slab',r,z,'floor_p2_asphalt' if level['floor']==-2 else 'floor_p2_tile')
        # No slab or suspended ceiling crosses the stair well.
        hole=((25,32,z-.3),(31.4,42,z+.01))
        cut(hole,('floor_p2_tile','floor_p2_asphalt'))
        ceiling=z+wall_height
        add(prefix+'_ceiling',(a,b,ceiling-.07),(c,d,ceiling),'ceiling_panel')
        cut(((25,32,ceiling-.1),(31.4,42,ceiling+.01)),('ceiling_panel',))
        for side,lo,hi in (
            ('west',(a-.1,b,z),(a+.1,d,z+wall_height)),
            ('east',(c-.1,b,z),(c+.1,d,z+wall_height)),
            ('south',(a,b-.1,z),(c,b+.1,z+wall_height)),
            ('north',(a,d-.1,z),(c,d+.1,z+wall_height))):
            add(prefix+'_shell_'+side,lo,hi)

    ground=next(l for l in spec['levels'] if l['floor']==0)
    z=ground['z'];g=spec['ground'];shell(ground,spec['footprint'])
    a,y0,y1=g['entrance']
    cut(((a-.3,y0,z-.01),(a+.3,y1,z+2.7)))
    slab('p2_ground_outside_landing',g['outside_landing'],z)
    # The glazed entrance has a broad permanently open centre for gameplay.
    for y in (y0,y1):
        add('p2_ground_entrance_jamb_'+str(y),(a-.08,y-.06,z),(a+.08,y+.06,z+2.75),'window_frame')
        add('p2_ground_entrance_open_glass_'+str(y),(a+.1,y-.025,z+.05),(a+1.1,y+.025,z+2.65),'window_glass')
    add('p2_ground_entrance_head',(a-.08,y0,z+2.7),(a+.08,y1,z+2.78),'window_frame')
    ground['rooms']=[]
    for room in g['rooms']:
        a,b,c,d=room['bounds'];name='p2_ground_'+room['id']
        for side,x in (('west',a),('east',c)):
            add(name+'_'+side,(x-.1,b,z),(x+.1,d,z+wall_height))
        for side,y in (('south',b),('north',d)):
            add(name+'_'+side,(a,y-.1,z),(c,y+.1,z+wall_height))
        y=room['door_y'];width=1.4
        cut(((a-.25,y-width/2,z-.01),(a+.25,y+width/2,z+2.2)))
        # The requested opposite wall is north in the drawing frame.
        add(name+'_blackboard',(a+1.4,d-.16,z+.95),(c-1.4,d-.115,z+2.2),'teaching_board')
        add(name+'_board_tray',(a+1.4,d-.25,z+.91),(c-1.4,d-.12,z+.95),'window_frame')
        room.update(footprint_local_metres=room['bounds'],door_side='v_min',
                    door_fraction=(y-b)/(d-b),door_width_metres=width,playable=True,
                    board_wall='north',sign_offset_metres=.16,
                    fitout={'seats':0,'rows':[], 'furniture':[]})
        ground['rooms'].append(room)
        # The fixed text plane is 0.13 m outside the room wall. Keep the
        # plaque's outer face behind that plane so it cannot hide the label.
        add(name+'_sign_plaque',(a-.12,y-.63,z+2.28),(a-.105,y+.63,z+2.6),'sign_blue')
        for yy in (y-width/2-.025,y+width/2+.025):
            add(name+'_jamb_'+str(yy),(a-.12,yy-.025,z),(a+.12,yy+.025,z+2.25),'window_frame')
        add(name+'_door_head',(a-.12,y-width/2-.05,z+2.2),(a+.12,y+width/2+.05,z+2.25),'window_frame')
    # Reception is enclosed on every side, with no hidden player entrance.
    boxes.extend(reception_boxes('p2_ground_reception',g['reception'],z,wall_height))
    g['office_fitout']=dict(desks=3,staff=3,front_staff='female',palette='gray')
    # Continue the front wall to the LEFT of reception, screening the stair.
    x,y0,_,y1=g['reception_wall_extension']
    add('p2_ground_reception_wall_extension',(x-.1,y0,z),(x+.1,y1,z+wall_height))
    sy=spec['stairs']['door_y'];sw=spec['stairs']['door_width']/2
    cut(((x-.25,sy-sw,z-.01),(x+.25,sy+sw,z+2.25)))
    for y in (38,41.8):
        add('p2_ground_stair_access_return_'+str(y),(21,y-.08,z),(25,y+.08,z+wall_height))
    # Photo 12: repeated tables along the RIGHT wall of the southbound hall.
    ground['table_bounds']=[]
    table_width=g['tables'][2]-g['tables'][0]
    for row,y in enumerate(g['table_rows_y']):
        for col,x in enumerate((g['tables'][0],)):
            name=f'p2_ground_table_{row}_{col}'
            add(name+'_top',(x,y,z+.72),(x+table_width,y+.85,z+.78),'sign_white')
            ground['table_bounds'].append([x,y,x+table_width,y+.85])
            for dx in (.12,table_width-.22):
                for dy in (.08,.69):
                    add(name+f'_leg_{dx}_{dy}',(x+dx,y+dy,z),(x+dx+.06,y+dy+.06,z+.72),'metal_dark')
            for dx in (.4,table_width/2-.2,table_width-.85):
                for dy in (-.6,1.02):
                    add(name+f'_chair_{dx}_{dy}',(x+dx,y+dy,z+.42),(x+dx+.43,y+dy+.43,z+.47),'seat_wood')
                    by=y+dy if dy<0 else y+dy+.38
                    add(name+f'_back_{dx}_{dy}',(x+dx,by,z+.47),(x+dx+.43,by+.05,z+.86),'seat_wood')
                    for cx in (.04,.35):
                        for cy in (.04,.35):
                            add(name+f'_chair_leg_{dx}_{dy}_{cx}_{cy}',
                                (x+dx+cx,y+dy+cy,z),(x+dx+cx+.035,y+dy+cy+.035,z+.42),'metal_dark')
    for i in range(10):
        x=10+i*1.25
        add('p2_ground_locker_'+str(i),(x,40.9,z),(x+1.18,41.7,z+1.85),'seat_wood')
        add('p2_ground_locker_handle_'+str(i),(x+.96,40.86,z+.8),(x+1,40.9,z+1.05),'window_frame')
    ground['audit_stations']=[dict(id='entrance',point=[8,28]),dict(id='reception_front',point=[19.5,29]),
        dict(id='left_corridor',point=[10,36]),dict(id='stair_approach',point=[23.8,39.5]),
        dict(id='tables_front',point=[17,24.8]),dict(id='tables_back',point=[17,g['right_corridor'][1]+1])]
    for r in ground['rooms']:
        a,b,c,d=r['bounds']
        ground['audit_stations'].extend([dict(id=r['id']+'_door',point=[a,r['door_y']]),
                                       dict(id=r['id']+'_centre',point=[(a+c)/2,(b+d)/2])])
    # Basement corridors: grey doors, display case, lime-green accent, ceiling.
    basement=next(l for l in spec['levels'] if l['floor']==-1);z=basement['z']
    for name,r in spec['basement'].items():
        a,b,c,d=r;slab('p2_basement_'+name+'_slab',r,z)
        add('p2_basement_'+name+'_ceiling',(a,b,z+wall_height-.07),(c,d,z+wall_height),'ceiling_panel')
        for side,x in (('west',a),('east',c)):
            add('p2_basement_'+name+'_'+side,(x-.1,b,z),(x+.1,d,z+wall_height))
        for side,y in (('south',b),('north',d)):
            add('p2_basement_'+name+'_'+side,(a,y-.1,z),(c,y+.1,z+wall_height))
    # Subtract both corridor interiors from their overlapping shell walls.
    # Cutting only to the wall centre leaves a blocking half-thickness strip.
    for r in spec['basement'].values():
        a,b,c,d=r
        cut(((a+.11,b+.11,z-.01),(c-.11,d-.11,z+wall_height)))
    for i,y in enumerate((36,43)):
        add('p2_basement_closed_door_'+str(i),(24.88,y,z),(24.91,y+1.2,z+2.15),'door_black')
    add('p2_basement_accent',(21.605,44,z+.25),(21.625,49,z+2.65),'p2_accent_green')
    add('p2_basement_display_base',(21.62,37,z),(21.88,42.5,z+.85),'seat_wood')
    add('p2_basement_display_glass',(21.64,37,z+.85),(21.68,42.5,z+2.2),'window_glass')
    basement['audit_stations']=[dict(id='stair_approach',point=[23.8,39.5]),
        dict(id='corridor_mid',point=[23.25,45]),dict(id='corridor_south',point=[23.25,34]),
        dict(id='right_turn_from_stairs',point=[23.25,63]),
        dict(id='cross_corridor',point=[29.5,63]),dict(id='cross_corridor_end',point=[35,63])]
    # Generic covered parking. The access aisle is intentionally clear of cars.
    parking=next(l for l in spec['levels'] if l['floor']==-2);z=parking['z'];shell(parking,spec['parking']['bounds'])
    for i,x in enumerate((10,20,40)):
        for j,y in enumerate((19,31)):
            add(f'p2_parking_column_{i}_{j}',(x-.3,y-.3,z),(x+.3,y+.3,z+wall_height),'wall')
            add(f'p2_parking_column_band_{i}_{j}',(x-.31,y-.31,z+.8),(x+.31,y+.31,z+1.1),'parking_line')
    for y in (10.5,32):
        for i in range(12):
            x=8+i*2.8
            add(f'p2_parking_bay_line_{y}_{i}',(x,y,z+.001),(x+.07,y+5.2,z+.008),'parking_line')
    for i,(x,y,mat) in enumerate(spec['parking']['cars']):
        name='p2_parking_car_'+str(i)
        add(name+'_body',(x-.9,y-2.05,z+.36),(x+.9,y+2.05,z+1.05),mat)
        add(name+'_cabin',(x-.75,y-.85,z+1.05),(x+.75,y+.95,z+1.53),'car_glass')
        add(name+'_roof',(x-.77,y-.85,z+1.5),(x+.77,y+.95,z+1.58),mat)
        for dx in (-.98,.8):
            for dy in (-1.5,1.2):
                add(name+f'_tyre_{dx}_{dy}',(x+dx,y+dy,z+.12),(x+dx+.18,y+dy+.6,z+.66),'car_tyre')
        for dx in (-.72,.42):
            add(name+'_lamp_'+str(dx),(x+dx,y-2.075,z+.65),(x+dx+.3,y-2.05,z+.83),'sign_white')
    parking['audit_stations']=[dict(id='stair_approach',point=[23.8,39.5]),
        dict(id='aisle_west',point=[9,25]),dict(id='aisle_east',point=[41,25]),
        dict(id='aisle_centre',point=[26,25]),dict(id='north_east_bays',point=[37,39]),
        dict(id='north_west_bays',point=[12,39])]
    # Enclosed switchback core: one storey up and two down from ground.
    st=spec['stairs'];a,b,c,d=st['bounds'];low=spec['levels'][0]['z'];high=spec['levels'][-1]['z']+wall_height
    for side,x in (('west',a),('east',c)):
        add('p2_stair_shell_'+side,(x-.1,b,low),(x+.1,d,high))
    add('p2_stair_shell_south',(a,b-.1,low),(c,b+.1,high))
    # North shell belongs to the level shells below +1; close upper return too.
    add('p2_stair_shell_north',(a,d-.1,low),(c,d+.1,high))
    slab('p2_stair_roof',(a,b,c,d),high,'ceiling_panel')
    slab('p2_parking_shaft_bottom',(a,b,c,d),low,'floor_p2_asphalt')
    st['portals']=[];st['flights']=[];st['path']=[]
    for level in spec['levels']:
        z=level['z'];y=st['door_y'];w=st['door_width']/2
        # All four portals align with a full-width landing, never a stair tread.
        cut(((a-.3,y-w,z-.01),(a+.3,y+w,z+2.25)))
        slab(level['id']+'_stair_landing',(a,st['flight_north'],c,d),z)
        st['portals'].append(dict(floor=level['floor'],centre=[a,y,z]))
        for side,dy in (('south',-w),('north',w)):
            add(level['id']+'_fire_door_'+side+'_panel',(a-.8,y+dy-.025,z+.03),(a,y+dy+.025,z+2.18),'door_black')
            add(level['id']+'_fire_door_'+side+'_pushbar',(a-.7,y+dy-.04,z+1.0),(a-.1,y+dy+.04,z+1.05),'door_pushbar')
        level.setdefault('audit_stations',[]).append(dict(id='stair_landing',point=[26.2,39.5]))
    for lower,upper in zip(spec['levels'],spec['levels'][1:]):
        z=lower['z'];rise=(upper['z']-z)/st['risers_per_storey'];half=st['risers_per_storey']//2
        if rise>.19 or abs(half*st['tread']-(st['flight_north']-st['flight_south']))>1e-6:
            raise ValueError('Povo 2 stair proportions do not fit')
        mid=z+half*rise;prefix='p2_stair_'+str(lower['floor']);width=st['flight_width']
        slab(prefix+'_mid_landing',(a,b,c,st['flight_south']),mid)
        path=[(a+width/2,39,z),(a+width/2,st['flight_north']+.45,z)]
        for flight in (1,2):
            for i in range(half):
                if flight==1:
                    x=a;y=st['flight_north']-(i+1)*st['tread'];top=z+(i+1)*rise
                else:
                    x=c-width;y=st['flight_south']+i*st['tread'];top=mid+(i+1)*rise
                add(prefix+f'_flight{flight}_{i}',(x,y,top-.16),(x+width,y+st['tread'],top),'floor_p2_tile')
                st['flights'].append(dict(lower_floor=lower['floor'],flight=flight,step=i,top=top,rise=rise))
                path.append((x+width/2,y+st['tread']/2,top))
                # Stair rails have vertical balusters and tread-length rails.
                edge=x+width-.045 if flight==1 else x+.005
                add(prefix+f'_rail_post_{flight}_{i}',(edge,y,top),(edge+.04,y+.04,top+1.02),'metal_dark')
                add(prefix+f'_handrail_{flight}_{i}',(edge,y,top+1),(edge+.04,y+st['tread'],top+1.04),'metal_dark')
            if flight==1:
                path.extend([(a+width/2,33.5,mid),(c-width/2,33.5,mid)])
        path.append((c-width/2,39,upper['z']))
        st['path'].append(dict(lower_floor=lower['floor'],points=path))
        # Horizontal rails protect the exposed sides of the middle landing.
        for x in (a+.05,c-.09):
            add(prefix+'_mid_guard_'+str(x),(x,b+.15,mid),(x+.04,st['flight_south'],mid+1.05),'metal_dark')
        for y,h in ((st['flight_south'],mid),(st['flight_north'],upper['z'])):
            for x in (a+width,a+width+.45,c-width):
                add(prefix+f'_gap_post_{y}_{x}',(x,y-.02,h),(x+.04,y+.02,h+1.05),'metal_dark')
            add(prefix+'_gap_guard_'+str(y),(a+width,y-.02,h+1),(c-width+.04,y+.02,h+1.05),'metal_dark')
    # The upper portal continues the existing rear cross-corridor at y=38..42.
    first=spec['levels'][-1]
    slab('p2_first_link_slab',(24.8,38,25.2,41.8),first['z'])
    first['audit_stations']=[dict(id='bridge_arrival',point=[18.25,12]),
        dict(id='rear_corridor',point=[18.25,39.5]),dict(id='stair_landing',point=[26.2,39.5])]
    spec['lights']=[]
    for level in spec['levels']:
        z=level['z']
        points=([(x,y) for x in (11,19,27,35,40) for y in (13.5,19,26,35)] if level['floor']==-2
                else [(11.5,y) for y in (-9,-3,3,9,15,21,28,35,39.5)]+[(22,y) for y in (-5.5,3.5,12.5,21.5)]+[(23,39.5)] if level['floor']==0
                else [(23.25,y) for y in (34,39,44,49,53.5,58,63)]+[(29.5,63),(35,63)] if level['floor']==-1 else [])
        points=[p for p in points if not (25<p[0]<31.4 and p[1]>32)]
        if level['floor']==0:
            points=[p for p in points if not (p[0]>31.4 and p[1]>32)]
            a,b,c,d=g['reception']
            points.extend((a+(c-a)*fx,b+(d-b)*fy) for fx in (.3,.7) for fy in (.3,.7))
        for x,y in [*points,(28.2,39.5)]:
            spec['lights'].append([x,y,z+2.9])
            add(level['id']+f'_fixture_{x}_{y}_rim',(x-.3,y-.3,z+wall_height-.1),(x+.3,y+.3,z+wall_height-.05),'window_frame')
            add(level['id']+f'_fixture_{x}_{y}_diffuser',(x-.26,y-.26,z+wall_height-.11),(x+.26,y+.26,z+wall_height-.1),'light_diffuser')
    return boxes,spec


def extend(boxes, levels, root, wall_height):
    extra,spec=build(root,wall_height)
    # Cut the previous upper east wall, glazing and trim at the new stair door.
    z=spec['levels'][-1]['z'];y=spec['stairs']['door_y'];w=spec['stairs']['door_width']/2
    hole=((24.7,y-w,z-.01),(25.3,y+w,z+2.25))
    boxes=[part for box in boxes for part in subtract_box(box,hole)]
    # The original closed future-phase panel is superseded by the stairs.
    boxes=[b for b in boxes if 'p2_future_door' not in b[0]]
    # Povo 2's photographed grey square tiles differ from Povo 1's pale finish.
    boxes=[(n,lo,hi,'floor_p2_tile' if ('_link_p2' in n or '_room_p2_' in n) and m.startswith('floor_') else m) for n,lo,hi,m in boxes]
    levels[1]['connection']['povo2']=spec
    return boxes+extra


if __name__=='__main__':
    from render_povo2_planimetry import render
    render()
