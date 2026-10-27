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
        for existing_name,lo,hi,material in result:
            if '_survey_' not in existing_name or material!='wall' or abs(lo[2]-z)>.01:continue
            if x<hi[0]+.25 and x+1.6>lo[0]-.25 and y-.6<hi[1]+.25 and y+1.45>lo[1]-.25:return
        for level in spec['levels']:
            if not name.startswith(level['id']+'_'):continue
            for station in level['audit_stations']:
                if not station['id'].startswith('observed_exit_'):continue
                px,py=station['point']
                if x<px+.6 and x+1.6>px-.6 and y-.6<py+.6 and y+1.45>py-.6:return
        # Reserve both stair landing approaches, including the full chair envelope.
        if name.startswith('canteen_') and x < 43.2 and x+1.6 > 41.0 and y-.6 < -97.0 and y+1.45 > -100.2:return
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
        if kind in ('canteen','library'):
            # The plan13/15 end U stairs run across the short building
            # dimension. Keep the stair inside its source
            # core instead of cutting through kitchen/atrium wall paths.
            if kind=='canteen':xa,xb=42.7,45.7;ya,yb=-99.65,-97.45;w=1.0
            else:xa,xb=38.0,41.0;ya,yb=-18.5,-14.4;w=1.9
            landing_x=xa-1.2
            prefix=kind+'_stairs'
            mid=(z0+z1)/2;path=[];rails=[];rise=(z1-z0)/20
            slab(prefix+'_bottom',(landing_x,ya,xa,yb),z0)
            slab(prefix+'_top',(landing_x,ya,xa,yb),z1)
            add(prefix+'_mid_landing',(xb,ya,z0),(xb+1.6,yb,mid),'floor_p2_tile')
            for flight in range(2):
                for i in range(10):
                    x=xa+i*.3 if flight==0 else xb-(i+1)*.3
                    y=ya if flight==0 else yb-w
                    top=z0+(i+1)*rise if flight==0 else mid+(i+1)*rise
                    add(f'{prefix}_step_{flight}_{i}',(x,y,z0),(x+.3,y+w,top),'floor_p2_tile')
                    path.append([x+.15,y+w/2,top])
            spec['stairs'].append(dict(building=kind,bounds=[landing_x,ya,xb+1.6,yb],path=path,rails=rails,axis='x',
                bottom=[xa-.6,ya+w/2,z0],top=[xa-.6,yb-w/2,z1],source='image00013.jpeg' if kind=='canteen' else 'image00015.jpeg'))
            return ((xa,ya,z1-.3),(xb+1.6,yb,z1+.01))
        raise ValueError('Unknown wing stair '+kind)

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

    # Source-space traces retain observed door offsets, rather than making
    # synthetic equal reading rooms with centred doors.
    survey=json.loads((root/'config/povo_amenities_survey.json').read_text(encoding='utf-8'))
    def project(key,point):
        u,v=point
        if key=='library0':return (52-(v-506)*16/475,-13-(u-132)*56/1497)
        if key=='canteen0':return (52-(v-354)*16/496,-77-(u-67)*33/1256)
        return (36+(v-324)*16/599,-77-(u-98)*33/1468)

    def traced(level,key):
        z=level['z'];source=survey[key];prefix=level['id']+'_survey'
        level['layout_source']=source['source']
        level['registration']='provisional existing XY footprint; actual image door offsets retained'
        level['unresolved']=source.get('unresolved',[])
        for wall in source.get('walls',[]):
            name=prefix+'_'+wall['id'];points=[project(key,p) for p in wall['points']]
            for i,(a,b) in enumerate(zip(points,points[1:])):
                # Photo perspective is retained as a conservative short box
                # envelope; no room is added merely from semantic zone bounds.
                add(name+f'_wall_{i}',(min(a[0],b[0])-.065,min(a[1],b[1])-.065,z),
                    (max(a[0],b[0])+.065,max(a[1],b[1])+.065,z+height),'wall')
            gaps=wall.get('door_gaps',[])
            if not isinstance(gaps,list):continue
            for j,gap in enumerate(gaps):
                a,b=[project(key,p) for p in gap]
                hole=((min(a[0],b[0])-.18,min(a[1],b[1])-.18,z-.01),
                      (max(a[0],b[0])+.18,max(a[1],b[1])+.18,z+2.25))
                cut(hole,name)
                level.setdefault('observed_openings',[]).append(dict(id=wall['id']+f'_{j}',ends=[a,b],source_gap=gap))
            level['rooms'].append(dict(id=wall['id'],source_path=wall['points'],
                bounds=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)],
                confidence='visible wall path; not asserted complete room'))
        for j,opening in enumerate(source.get('interior_openings',[])):
            a,b=[project(key,p) for p in opening['gap']]
            cut(((min(a[0],b[0])-.2,min(a[1],b[1])-.2,z-.01),
                 (max(a[0],b[0])+.2,max(a[1],b[1])+.2,z+2.25)),prefix)
        for j,door in enumerate(source.get('exterior_doors',[])):
            gap=door['segment'] if isinstance(door,dict) else door
            a,b=[project(key,p) for p in gap]
            # Photograph perspective/recesses do not coincide with our rectangular
            # placeholder facade. Extend its aperture to that facade, retaining
            # the observed long-axis offset; keep the standing station indoors.
            west=cfg[level['building']]['bounds'][0]
            cut(((west-.3,min(a[1],b[1])-.12,z-.01),
                 (max(a[0],b[0])+.3,max(a[1],b[1])+.12,z+2.3)),level['id']+'_west')
            station(level,f'observed_exit_{j}',max(west+.7,(a[0]+b[0])/2),(a[1]+b[1])/2)

    for level in spec['levels']:
        level['campus_floor']=-1 if level['floor']==0 else 0
        key=level['building']+str(level['floor'])
        if key in survey:traced(level,key)
        elif level['building']=='library':
            level['layout_source']='image00016.jpeg directory only'
            level['semantic_zones']=['two adjacent group-study spaces along long edge','end reading area','remaining reading area']
            level['unresolved']=['Detailed upper-floor partition/door plan not supplied; directory zones are not traced walls']
    for level in [l for l in spec['levels'] if l['building']=='library']:
        z=level['z'];prefix=level['id']
        # Representative furniture stays in the central open reading strip.
        for i,y in enumerate((-58,-51,-44,-31)):
            table(prefix+f'_open_reading_{i}',40,y,z)
        for name,x,y in [('west_corridor_south',37.5,-65),('west_corridor_middle',37.5,-40),('west_corridor_north',37.5,-22.5)]:station(level,name,x,y)
        if level['floor']==0:
            station(level,'entrance',37.5,cfg['library']['entrance_y'])
            station(level,'povo1_side_approach',32,cfg['library']['entrance_y'])
    # The actual central narrow flight in plan15 connects the library reading
    # floors; keep its traced axis and open corresponding upper slab/soffit.
    p0=project('library0',[960,685]);p1=project('library0',[1211,721])
    xa,xb=sorted((p0[0],p1[0]));ya,yb=sorted((p0[1],p1[1]))
    path=[];count=math.ceil((z1-z0)/.18)
    for i in range(count):
        y=yb-(yb-ya)*(i+1)/count;top=z0+(z1-z0)*(i+1)/count
        add(f'library_central_stair_{i}',(xa,y,z0),(xb,y+(yb-ya)/count,top),'floor_p2_tile')
        path.append([(xa+xb)/2,y+(yb-ya)/count/2,top])
    for prefix in ('library_1_slab','library_0_ceiling'):
        cut(((xa-.08,ya-.08,z0+height-.1),(xb+.08,yb+.08,z1+.01)),prefix)
    spec['stairs'].append(dict(building='library',kind='central_plan15',path=path,axis='y',
        bottom=[(xa+xb)/2,yb+.4,z0],top=[(xa+xb)/2,ya-.4,z1],rails=[],
        registration='source axis; storey rise provisional'))
    bank('exterior_library_entry',36,cfg['library']['entrance_y'],z0)
    # Wing facade names use library_0; explicitly open it before adding the bank.
    cut(((35.7,-62.85,z0-.01),(36.3,-59.15,z0+2.85)),'library_0_west')

    # Enter from Povo 1 facing east: bar on the right/south, the smaller
    # ground dining area on the left/north, and the stair directly ahead.
    entrance_y=cfg['canteen']['entrance_y']
    for level in [l for l in spec['levels'] if l['building']=='canteen']:
        z=level['z'];prefix=level['id'];upper=level['floor']==1
        serving=(40,-105,41.3,-101) if upper else (43,-91,44.3,-80)
        x0,y0,x1,y1=serving
        add(prefix+'_serving_counter',(x0,y0,z),(x1,y1,z+1.05),'canteen_orange')
        add(prefix+'_serving_counter_top',(x0-.05,y0-.05,z+1.05),(x1+.05,y1+.05,z+1.12),'sign_white')
        rows=range(-106,-79,3) if upper else (-90,-86,-82)
        sx0,sy0,sx1,sy1=cfg['canteen']['stair']
        for row,y in enumerate(rows):
            for col,x in enumerate((41,45,48) if upper else (38,40.5)):
                if y-.6<entrance_y+.7 and y+1.43>entrance_y-.7:continue
                if x<sx1+.4 and x+1.6>sx0-.4 and y-.6<sy1+.4 and y+1.43>sy0-.4:continue
                table(prefix+f'_dining_table_{row}_{col}',x,y,z,orange=True)
        for i,y in enumerate((-90,-85,-80) if not upper else (-104.8,-90,-80)):
            station(level,f'dining_aisle_{i}',36.9 if not upper else 37.5,y-1.0 if not upper else y)
            station(level,f'dining_outer_{i}',50.5 if upper else 46.8,y)
        station(level,'cross_aisle',40.8,entrance_y)
        station(level,'stair_approach',42.1,-99.15 if not upper else -97.95)
        if not upper:
            a,b,c,d=cfg['canteen']['bar_counter']
            add(prefix+'_bar_counter',(a,b,z),(c,d,z+1.1),'canteen_orange')
            a,b,c,d=cfg['canteen']['bar_white_wall']
            add(prefix+'_bar_white_wall',(a,b,z),(c,d,z+2.6),'wall')
            for i,(a,b,c,d) in enumerate(cfg['canteen']['bar_tables']):
                add(prefix+f'_bar_sketch_table_{i}_top',(a,b,z+1.02),(c,d,z+1.08),'canteen_orange')
                for x in (a+.08,c-.14):
                    for y in (b+.08,d-.14):
                        add(prefix+f'_bar_sketch_table_{i}_leg_{x}_{y}',(x,y,z),(x+.06,y+.06,z+1.02),'metal_dark')
            station(level,'bar_approach',42.5,-105)
            station(level,'entrance',37.2,entrance_y)
            # Open black double leaves mark the fire-door entrance straight ahead.
            for i,y in enumerate((-99.8,-98.5)):
                add(prefix+f'_stair_fire_door_{i}',(41.5,y-.025,z+.02),(42.1,y+.025,z+2.18),'door_black')
                add(prefix+f'_stair_pushbar_{i}',(41.6,y-.05,z+1),(42,y+.05,z+1.05),'door_pushbar')
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
    for x in (a,c):
        for y in (b,d):
            add(f'canteen_0_porch_corner_{x}_{y}',(x-.04,y-.04,z0),(x+.04,y+.04,z0+3),'window_frame')
    bank('exterior_canteen_outer_entry',a,cfg['canteen']['outer_y'],z0)
    bank('exterior_canteen_inner_entry',c,cfg['canteen']['entrance_y'],z0)
    for x,y in ((a,cfg['canteen']['outer_y']),(c,cfg['canteen']['entrance_y'])):
        cut(((x-.3,y-1.85,z0-.01),(x+.3,y+1.85,z0+2.85)),'canteen_0')
    bank('exterior_canteen_upper_entry',52,cfg['canteen']['exit_y'],z1)
    cut(((51.7,cfg['canteen']['exit_y']-1.85,z1-.01),(52.3,cfg['canteen']['exit_y']+1.85,z1+2.85)),'canteen_1_east')
    lower=next(l for l in spec['levels'] if l['id']=='canteen_0')
    for name,x,y in [('porch_outer',32,cfg['canteen']['outer_y']),('porch_turn',33.5,entrance_y),('porch_inner',35,entrance_y)]:station(lower,name,x,y)
    station(lower,'povo1_side_approach',30,cfg['canteen']['outer_y'])
    # The two photographed plans have independent perspective fits. Preserve
    # their paths but clear the registered stair standing envelope wherever a
    # fitted core edge otherwise clips a flight or its upper-floor arrival.
    for stair_spec in spec['stairs']:
        if stair_spec['building']!='canteen':continue
        for x,y,z in stair_spec['path']:
            for floor in (0,1):
                cut(((x-.15,y-.43,z+.19),(x+.15,y+.43,z+1.9)),f'canteen_{floor}_survey_')

    # Ground-level Povo 1-side access, not an entrance from the raised street.
    slab('canteen_0_access',(29,cfg['canteen']['porch'][1],31.5,-77),z0)
    slab('library_0_access',(29,-69,36,-13),z0)
    # Join the lower plaza around the original external stair footprint.
    slab('library_0_access_join',(25,-74,29,-65),z0)
    slab('canteen_0_access_join',(25,-83,31.5,-77),z0)
    # Photo14 confirms this is the thin overhead canopy. Follow the existing
    # entrance-cover profile, preserving its3.4m clearance above the stair;
    # a slab at the floor elevation would wrongly fill the pedestrian route.
    exterior_cfg=json.loads((root/'config/povo_exterior.json').read_text())
    entry=exterior_cfg['east_approach'];cy=entry['entrance_y']
    sx,_,ex,_=entry['stairs'];clearance=entry['canopy_clearance']
    profile=[(24,entry['lower_z']+clearance),(sx,entry['lower_z']+clearance),
             (ex,entry['upper_z']+clearance),(entry['canopy_end_x'],entry['upper_z']+clearance)]
    for j,((x0,h0),(x1,h1)) in enumerate(zip(profile,profile[1:])):
        count=max(1,math.ceil(abs(h1-h0)/.16))
        for i in range(count):
            left=x0+(x1-x0)*i/count;right=x0+(x1-x0)*(i+1)/count
            top=h0+(h1-h0)*(i+1)/count
            add(f'amenities_walkable_canopy_{j}_{i}',(left,cy-3.1,top-.08),(right,cy+3.1,top),'exterior_canopy_glass')
    spec['canopy']=dict(profile=profile,width=6.2,walkable=True,enclosed=False,
                         source='image00014.jpeg',registration='provisional existing entrance roof profile; clearance retained')
    terrace=cfg['canteen']['terrace'];a,b,c,d=terrace
    slab('canteen_1_street_terrace',terrace,z1,'exterior_concrete')
    rails=[]
    railing(add,rails,'canteen_terrace_outer',(c,b,z1),(c,d,z1))
    railing(add,rails,'canteen_terrace_south',(a,b,z1),(c,b,z1))
    spec['terrace']=dict(bounds=terrace,z=z1,rails=rails,source='image00011.jpeg',registration='provisional footprint')
    spec['survey_hash']=hashlib.sha256((root/'config/povo_amenities_survey.json').read_bytes()).hexdigest()
    levels[0]['wings']=spec
    ext=levels[0].get('exterior',{})
    ext.setdefault('input_hashes',{})['config/povo_wings.json']=hashlib.sha256((root/'config/povo_wings.json').read_bytes()).hexdigest()
    return result
