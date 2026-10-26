"""Playable library/canteen interiors in the two existing Povo 1 glazed wings."""
import hashlib
import json
import math

try:
    from .povo_room_fitout import subtract_box
    from .povo2_exterior_entrance import door_bank
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo2_exterior_entrance import door_bank
    from povo_stairs import railing

COLORS={'canteen_orange':(220,109,47),'canteen_blue':(43,81,142)}


def extend(boxes,levels,root):
    cfg=json.loads((root/'config/povo_wings.json').read_text())
    z0,z1=cfg['ground_z'],cfg['first_z'];height=cfg['wall_height']
    # Replace the solid placeholders AND their old full-height framing. New
    # per-floor panes leave no horizontal rail crossing an entrance or a stair.
    result=[b for b in boxes if not b[0].startswith(('exterior_povo1_library_0_', 'exterior_povo1_library_1_'))]
    spec=dict(config=cfg,levels=[],stairs=[],lights=[],signs=[])

    def add(name,lo,hi,mat):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError(name)
        result.append((name,tuple(lo),tuple(hi),mat))

    def cut(hole,prefix):
        nonlocal result
        result=[part for b in result for part in
                (subtract_box(b,hole) if b[0].startswith(prefix) else [b])]

    def bank(prefix,x,y,z):
        cut(((x-.3,y-1.85,z-.01),(x+.3,y+1.85,z+2.85)),prefix.split('_entry_')[0])
        def box(name,lo,hi,material):
            add(prefix+'_'+name,lo,hi,'exterior_'+material)
        door_bank(box,'bank_0',x,y,z,bank_width=3.6,clear_width=1.8,door_height=2.65)

    def slab(name,rect,z,mat='floor_p2_tile'):
        a,b,c,d=rect;add(name,(a,b,z-.22),(c,d,z),mat)

    def station(level,name,x,y):level['audit_stations'].append(dict(id=name,point=[x,y]))

    def table(name,x,y,z,orange=False,high=False):
        h=1.02 if high else .74
        add(name+'_top',(x,y,z+h),(x+1.6,y+.8,z+h+.06),'canteen_orange' if orange else 'seat_wood')
        for dx in (.1,1.44):
            for dy in (.08,.66):
                add(name+f'_leg_{dx}_{dy}',(x+dx,y+dy,z),(x+dx+.06,y+dy+.06,z+h),'metal_dark')
        for i,(dx,dy) in enumerate(((.2,-.6),(.95,-.6),(.2,1.0),(.95,1.0))):
            sh=.72 if high else .44
            add(name+f'_seat_{i}',(x+dx,y+dy,z+sh),(x+dx+.43,y+dy+.43,z+sh+.05),
                'canteen_orange' if high else 'canteen_blue' if orange else 'seat_wood')
            # Legs and backs keep furniture readable; leave circulation beside rows.
            add(name+f'_chair_stem_{i}',(x+dx+.18,y+dy+.18,z),(x+dx+.25,y+dy+.25,z+sh),'metal_dark')
            if not high:
                yy=y+dy if dy<0 else y+dy+.38
                add(name+f'_back_{i}',(x+dx,yy,z+sh+.05),(x+dx+.43,yy+.05,z+.9),
                    'canteen_blue' if orange else 'seat_wood')

    def stair(kind,rect):
        a,b,c,d=rect;w=(c-a-.2)/2;rise=(z1-z0)/20
        if rise>.19 or d-b<6:raise ValueError('Wing stair does not fit')
        prefix=kind+'_stairs';path=[];rails=[]
        for z in (z0,z1):slab(prefix+f'_floor_landing_{z:g}',(a,b,c,b+1.5),z)
        mid=(z0+z1)/2;add(prefix+'_mid_landing',(a,b+4.5,z0),(c,d,mid),'floor_p2_tile')
        for flight in range(2):
            for i in range(10):
                x=a if flight==0 else c-w
                y=b+1.5+i*.3 if flight==0 else b+4.5-(i+1)*.3
                top=z0+(i+1)*rise if flight==0 else mid+(i+1)*rise
                add(prefix+f'_step_{flight}_{i}',(x,y,z0),(x+w,y+.3,top),'floor_p2_tile')
                path.append([x+w/2,y+.15,top])
        railing(add,rails,prefix+'_inner_lower',(a+w-.04,b+1.5,z0+.18),(a+w-.04,b+4.5,mid))
        railing(add,rails,prefix+'_inner_upper',(c-w+.04,b+4.5,mid+.18),(c-w+.04,b+1.5,z1))
        # Perimeter guards at both landings leave the south approach clear.
        add(prefix+'_mid_north_guard',(a,d-.07,mid),(c,d,mid+1.05),'metal_dark')
        spec['stairs'].append(dict(building=kind,bounds=rect,path=path,rails=rails,
                                   bottom=[a+w/2,b+.7,z0],top=[c-w/2,b+.7,z1]))
        return ((a,b+1.5,z1-.3),(c,d,z1+.01))

    def glazed_shell(kind,rect,z,level):
        a,b,c,d=rect;prefix=level['id']
        slab(prefix+'_slab',rect,z)
        add(prefix+'_ceiling',(a,b,z+height-.08),(c,d,z+height),'ceiling_panel')
        # Split facade into short independent panes, with clear floor heights.
        for side,value,start,end in [('west',a,b,d),('east',c,b,d),('south',b,a,c),('north',d,a,c)]:
            bays=math.ceil((end-start)/1.35)
            for i in range(bays):
                lo=start+(end-start)*i/bays;hi=start+(end-start)*(i+1)/bays
                if side in ('west','east'):
                    add(prefix+f'_{side}_glass_{i}',(value-.02,lo+.04,z+.1),(value+.02,hi-.04,z+height-.1),'window_glass')
                    add(prefix+f'_{side}_mullion_{i}',(value-.055,lo-.025,z),(value+.055,lo+.025,z+height),'window_frame')
                else:
                    add(prefix+f'_{side}_glass_{i}',(lo+.04,value-.02,z+.1),(hi-.04,value+.02,z+height-.1),'window_glass')
                    add(prefix+f'_{side}_mullion_{i}',(lo-.025,value-.055,z),(lo+.025,value+.055,z+height),'window_frame')
            # Match Povo 1's metal grid from both sides: close the final bay,
            # and add the base, waist transom and head on every facade.
            if side in ('west','east'):
                add(prefix+f'_{side}_mullion_{bays}',(value-.055,end-.025,z),(value+.055,end+.025,z+height),'window_frame')
            else:
                add(prefix+f'_{side}_mullion_{bays}',(end-.025,value-.055,z),(end+.025,value+.055,z+height),'window_frame')
            for j,h in enumerate((.1,1.9,height-.1)):
                if side in ('west','east'):
                    add(prefix+f'_{side}_transom_{j}',(value-.055,start,z+h-.025),(value+.055,end,z+h+.025),'window_frame')
                else:
                    add(prefix+f'_{side}_transom_{j}',(start,value-.055,z+h-.025),(end,value+.055,z+h+.025),'window_frame')
        for x in (a+4,c-3):
            for y in range(math.ceil(b+3),int(d-1),5):spec['lights'].append([x,y,z+2.8])

    for kind in ('canteen','library'):
        building=cfg[kind];a,b,c,d=building['bounds']
        for floor,z in enumerate((z0,z1)):
            level=dict(id=f'{kind}_{floor}',building=kind,floor=floor,z=z,
                       bounds=building['bounds'],audit_stations=[],rooms=[])
            spec['levels'].append(level)
            glazed_shell(kind,building['bounds'],z,level)
        hole=stair(kind,building['stair'])
        # Cut ONLY upper-floor slab and lower ceiling; protect the upper roof.
        for suffix in ('1_slab','0_ceiling'):
            cut(((hole[0][0],hole[0][1],z0+height-.1),
                 (hole[1][0],hole[1][1],z1+.01)),kind+'_'+suffix)
        lower,upper=[l for l in spec['levels'] if l['building']==kind]
        bottom,top=spec['stairs'][-1]['bottom'],spec['stairs'][-1]['top']
        station(lower,'stairs_bottom',*bottom[:2]);station(upper,'stairs_top',*top[:2])
        # Nav/sign metadata is separate from the original Povo 1 room records.
        spec['signs'].append(dict(text=kind.upper(),point=[36.2,building['entrance_y'],z0+2.5],angles='0 180 90'))

    # Library: a continuous west-side circulation strip and three reading rooms
    # per floor. Ground reception sits to the right when entering from Povo 1.
    for level in [l for l in spec['levels'] if l['building']=='library']:
        z=level['z'];prefix=level['id']
        for i,rect in enumerate(cfg['library']['rooms']):
            a,b,c,d=rect;door=b+2.5
            add(prefix+f'_partition_west_{i}',(a-.08,b,z),(a+.08,d,z+height),'wall')
            if i:add(prefix+f'_partition_south_{i}',(a,b-.08,z),(c,b+.08,z+height),'wall')
            cut(((a-.2,door-.8,z-.01),(a+.2,door+.8,z+2.25)),prefix+'_partition_west')
            level['rooms'].append(dict(id=f'reading_{i}',bounds=rect,door=[a,door]))
            station(level,f'reading_{i}_door',a,door)
            station(level,f'reading_{i}_back',50.5,d-1.2)
            # Leave a 2 m cross aisle at each room entrance and north end.
            for row,y in enumerate(range(math.ceil(b+5),int(d-2),3)):
                for col,x in enumerate((41,45,48)):
                    table(prefix+f'_reading_{i}_table_{row}_{col}',x,y,z)
        station(level,'west_corridor_south',37.5,-65)
        station(level,'west_corridor_middle',37.5,-40)
        station(level,'west_corridor_north',37.5,-22.5)
        if level['floor']==0:
            add(prefix+'_reception_counter',(40,-65,z),(43,-64.2,z+1.05),'seat_wood')
            add(prefix+'_reception_monitor',(41,-64.35,z+1.08),(41.5,-64.3,z+1.4),'desk_dark')
            station(level,'entrance',37.5,cfg['library']['entrance_y'])
            station(level,'povo1_side_approach',32,cfg['library']['entrance_y'])
    bank('exterior_library_entry',36,cfg['library']['entrance_y'],z0)
    # Wing facade names use library_0; explicitly open it before adding the bank.
    cut(((35.7,-62.85,z0-.01),(36.3,-59.15,z0+2.85)),'library_0_west')

    # Enter from Povo 1 facing east: bar on the right/south, the smaller
    # ground dining area on the left/north, and the stair directly ahead.
    entrance_y=cfg['canteen']['entrance_y']
    for level in [l for l in spec['levels'] if l['building']=='canteen']:
        z=level['z'];prefix=level['id'];upper=level['floor']==1
        serving=(37,-105,38.3,-94) if upper else (37,-92,38.3,-80)
        x0,y0,x1,y1=serving
        add(prefix+'_serving_counter',(x0,y0,z),(x1,y1,z+1.05),'canteen_orange')
        add(prefix+'_serving_counter_top',(x0-.05,y0-.05,z+1.05),(x1+.05,y1+.05,z+1.12),'sign_white')
        rows=range(-106,-79,3) if upper else (-90,-86,-82)
        sx0,sy0,sx1,sy1=cfg['canteen']['stair']
        for row,y in enumerate(rows):
            for col,x in enumerate((41,45,48)):
                if y-.6<entrance_y+.7 and y+1.43>entrance_y-.7:continue
                if x<sx1+.4 and x+1.6>sx0-.4 and y-.6<sy1+.4 and y+1.43>sy0-.4:continue
                table(prefix+f'_dining_table_{row}_{col}',x,y,z,orange=True)
        for i,y in enumerate((-90,-85,-80) if not upper else (-107.5,-90,-80)):
            station(level,f'dining_aisle_{i}',39.5,y)
            station(level,f'dining_outer_{i}',50.5,y)
        station(level,'cross_aisle',42,entrance_y)
        station(level,'stair_approach',43,entrance_y)
        if not upper:
            add(prefix+'_bar_counter',(37,-108,z),(42,-106.8,z+1.1),'canteen_orange')
            for i,x in enumerate((38,41)):
                table(prefix+f'_bar_high_table_{i}',x,-104,z,orange=True,high=True)
            station(level,'bar_approach',45,-105)
            station(level,'entrance',37.2,entrance_y)
            # Open black double leaves mark the fire-door entrance straight ahead.
            for i,y in enumerate((entrance_y-.65,entrance_y+.65)):
                add(prefix+f'_stair_fire_door_{i}',(43.4,y-.025,z+.02),(44,y+.025,z+2.18),'door_black')
                add(prefix+f'_stair_pushbar_{i}',(43.5,y-.05,z+1),(43.9,y+.05,z+1.05),'door_pushbar')
        else:
            station(level,'street_exit',50.5,cfg['canteen']['exit_y'])
            station(level,'street_pavement',53.5,cfg['canteen']['exit_y'])
    # Projecting porch: outside bank -> turn south -> inner bank.
    p=cfg['canteen']['porch'];a,b,c,d=p
    slab('canteen_0_porch_slab',p,z0)
    add('canteen_0_porch_roof',(a,b,z0+2.95),(c,d,z0+3.05),'ceiling_panel')
    for side,lo,hi in [('south',(a,b-.03,z0),(c,b+.03,z0+2.95)),
                       ('north',(a,d-.03,z0),(c,d+.03,z0+2.95)),
                       ('west',(a-.03,b,z0),(a+.03,d,z0+2.95)),
                       ('east',(c-.03,b,z0),(c+.03,d,z0+2.95))]:
        add('canteen_0_porch_'+side+'_glass',lo,hi,'window_glass')
    bank('exterior_canteen_outer_entry',a,cfg['canteen']['outer_y'],z0)
    bank('exterior_canteen_inner_entry',c,cfg['canteen']['entrance_y'],z0)
    for x,y in ((a,cfg['canteen']['outer_y']),(c,cfg['canteen']['entrance_y'])):
        cut(((x-.3,y-1.85,z0-.01),(x+.3,y+1.85,z0+2.85)),'canteen_0')
    bank('exterior_canteen_upper_entry',52,cfg['canteen']['exit_y'],z1)
    cut(((51.7,cfg['canteen']['exit_y']-1.85,z1-.01),(52.3,cfg['canteen']['exit_y']+1.85,z1+2.85)),'canteen_1_east')
    lower=next(l for l in spec['levels'] if l['id']=='canteen_0')
    for name,x,y in [('porch_outer',32,cfg['canteen']['outer_y']),('porch_turn',33.5,entrance_y),('porch_inner',35,entrance_y)]:station(lower,name,x,y)
    station(lower,'povo1_side_approach',30,cfg['canteen']['outer_y'])
    # Ground-level Povo 1-side access, not an entrance from the raised street.
    slab('canteen_0_access',(29,cfg['canteen']['porch'][1],31.5,-77),z0)
    slab('library_0_access',(29,-69,36,-13),z0)
    # Join the lower plaza around the original external stair footprint.
    slab('library_0_access_join',(25,-74,29,-65),z0)
    slab('canteen_0_access_join',(25,-83,31.5,-77),z0)
    levels[0]['wings']=spec
    ext=levels[0].get('exterior',{})
    ext.setdefault('input_hashes',{})['config/povo_wings.json']=hashlib.sha256((root/'config/povo_wings.json').read_bytes()).hexdigest()
    return result
