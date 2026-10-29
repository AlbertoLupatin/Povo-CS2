#!/usr/bin/env python3
"""Build Povo 1's three source-plan floors in the geographic frame."""

import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import re

try:
    from . import build_povo_interior as interior
    from .build_povo_blockout import write_box
    from .povo_room_fitout import subtract_box
    from .povo_campus_finishes import write_materials
    from .povo2_connection import extend_campus
    from .povo2_planimetry import extend as extend_povo2, COLORS as POVO2_COLORS
    from .povo2_integration import extend as integrate_povo2
    from .povo_interior_fixtures import reception_boxes, restroom_boxes, campus_staff_meshes, COLORS as FIXTURE_COLORS
    from .povo_stairs import railing, wall_handrail, mirrored, rail_faces
    from .povo_exterior_materials import COLORS as EXTERIOR_COLORS, PREFIX as EXTERIOR_PREFIX, write_materials as write_exterior_materials
    from .geometry_cache import memoize_geometry
except ImportError:
    import build_povo_interior as interior
    from build_povo_blockout import write_box
    from povo_room_fitout import subtract_box
    from povo_campus_finishes import write_materials
    from povo2_connection import extend_campus
    from povo2_planimetry import extend as extend_povo2, COLORS as POVO2_COLORS
    from povo2_integration import extend as integrate_povo2
    from povo_interior_fixtures import reception_boxes, restroom_boxes, campus_staff_meshes, COLORS as FIXTURE_COLORS
    from povo_stairs import railing, wall_handrail, mirrored, rail_faces
    from povo_exterior_materials import COLORS as EXTERIOR_COLORS, PREFIX as EXTERIOR_PREFIX, write_materials as write_exterior_materials
    from geometry_cache import memoize_geometry

ROOT = Path(__file__).resolve().parents[1]
PHOTO4_CLASSROOMS = frozenset(('a103','a104','a105','a106'))
MATERIAL_PREFIX = 'materials/trento/povo/campus/'
COLORS = {**interior.COLORS, 'stair_red': (155, 43, 38),
          'stair_nosing': (42, 44, 44), 'sign_blue': (33, 69, 86),
          'sign_white': (238, 236, 218), 'door_closed': (106, 68, 49),
          'courtyard_ground': (141, 153, 125),
          'floor_circulation': (184, 184, 179), 'floor_room': (222, 221, 214),
          'wall': (201, 200, 189), 'ceiling_panel': (190, 191, 184),
          'floor_wood': (158, 125, 88), 'door_black': (43, 47, 48),
          'door_pushbar': (179, 53, 37), 'sanitary_white': (225, 226, 222),
          'sanitary_water': (72, 96, 102), **POVO2_COLORS, **FIXTURE_COLORS,
          **{'exterior_'+n:c for n,c in EXTERIOR_COLORS.items()},
          'canteen_orange': (220,109,47), 'canteen_blue': (43,81,142), 'floor_yard_grass': (95,121,65),
          'floor_grating': (122,128,130), 'floor_terrace': (148,144,138)}


def derived_config(root=ROOT):
    settings = json.loads((root / 'config/povo1_campus.json').read_text())
    config = copy.deepcopy(json.loads((root / settings['interior_source']).read_text()))
    config['wall_height_metres'] = settings['wall_height_metres']
    config['classroom_fitouts'] = []
    config['status'] = 'Playable Povo 1 campus source'
    for level in config['levels']:
        ground = level['id'] == 'academic_ground'
        level['user_floor'] = -1 if ground else 0
        for room in settings.get('additional_rooms', {}).get(level['id'], []):
            if room['id'] in ('a202','a203','bridge_study'):
                continue
            added=dict(copy.deepcopy(room),door_width_metres=1.2)
            added.setdefault('kind','office')
            if added['label'].startswith('Studio '):
                added['label']='Locale'
                added['identity_status']='Legacy provisional cell; current use not identified in photos'
            added.setdefault('door_fraction',.85)
            level['rooms'].append(added)
        for room in level['rooms']:
            room['playable'] = room.get('playable',True) and not (ground and room['id'] in settings['ground_locked_rooms'])
            room['room_template'] = next((name for name, ids in settings['ground_room_templates'].items()
                                          if room['id'] in ids), 'existing_upper_room')
            if room['kind'] in ('reception','restroom','office','elevator','study','service') or not room['playable'] or (room['kind'] != 'classroom' and not settings.get('furnish_all_rooms')):
                continue
            u0, v0, u1, v1 = room['pixel_bounds']
            if 'window_side' in room:
                window = room['window_side']
            elif room['id'] in ('a101','a102','a201','a202','lab'):
                window = 'north'
            elif ground:
                window = ('south' if room['id'] in ('a103','a104','a105','a106','a108')
                          else 'north' if room['id'] == 'a107' else 'west')
            else:
                window = ('south' if room['id'] in ('a204','a205','a206','a207','a208')
                          else 'north' if room['id'] == 'a203'
                          else 'east' if room['id'] in ('a209','a210','a211','a212','a217','a218','a219','a220')
                          else 'west')
            opposite = {'south':'north','north':'south','east':'west','west':'east'}
            # The source doorway centres are provisional. Place the openings
            # near row ends so the teaching board cannot block a front doorway.
            if 'window_side' not in room:room['door_fraction'] = .85
            fitout = dict(level=level['id'], room=room['id'], window_side=window,
                          teaching_side=room.get('teaching_side', opposite.get(window)), side_aisle_metres=1.0,
                          row_pitch_metres=1.15, first_row_metres=2.05,
                          rear_clearance_metres=1.1, reference_ids=['P020','P021','P022'],
                          location_status='User-authorized repeated room family; estimated fit-out')
            fitout['repeat_classroom_template'] = settings.get('furnish_all_rooms', False)
            if ground and room['id'] in PHOTO4_CLASSROOMS:
                fitout.update(teaching_side='south',window_side='south',
                              glazing_position='teaching_front',chair_material='seat_green',
                              projection_screen=False,projector_count=2,front_platform_metres=.14,teacher_desk_width_metres=4.2,source_walk_20261027=[4],
                              location_status=('Photo4 identified by user as A103' if room['id']=='a103' else
                                               'User-authorized repetition of photo4/A103 along external A103-A106 row'),
                              window_context='Teaching board stands before external glazing; compass remains legacy registration')
            if room['id'] == 'a215':
                fitout.update(reference_ids=['P047','P048','P049','P050'],
                              first_row_metres=1.05, row_pitch_metres=1.05,
                              rear_clearance_metres=.65,
                              location_status='A215 identified by user; dimensions estimated')
            config['classroom_fitouts'].append(fitout)
    return settings, config


def mirror_point(point, east=False, north=False):
    """Reflect around the accepted 47 x 83 m building's centre (.5, -61.5)."""
    x,y,*rest=point
    return (1-x if east else x,-123-y if north else y,*rest)


def mirror_rectangle(rect, east=False, north=False):
    a=mirror_point(rect[:2],east,north);b=mirror_point(rect[2:],east,north)
    return (min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))


def mirror_box(box, identifier, east=False, north=False):
    name,lo,hi,material=box
    a=mirror_point(lo,east,north);b=mirror_point(hi,east,north)
    return (name.replace('stair_se_','stair_'+identifier+'_',1),
            tuple(min(a[i],b[i]) for i in range(3)),
            tuple(max(a[i],b[i]) for i in range(3)),material)


def stairs_and_roof(boxes, levels, settings, config, origin, *, continues_up=False):
    """Add the three-flight stairs, close unused voids, and seal both ceilings."""
    boxes = list(boxes)
    z0, z1 = [level['floor_elevation_metres'] - origin[2] for level in levels]
    stair = settings['stairs']
    count = stair['risers']
    # Photos 47-49 and P007: three flights around a central well. From the
    # floor landing one goes left, one straight across the far end, one right.
    n2 = 6
    n1 = (count-n2)//2
    if n1 < 3 or 2*n1+n2 != count:
        raise ValueError('Three-flight stairs need an even riser count of at least 12')
    rise = (z1-z0)/count
    tread = stair['tread_metres']
    ex0,ey0,ex1,ey1 = stair['enclosure_bounds_local_metres']
    t = config['wall_thickness_metres']
    xi0, xi1, yi0, yi1 = ex0+t/2, ex1-.09, ey0+t/2, ey1-t/2
    # Side flights and the far flight share one width; the well is the far
    # flight's run long, and the corner landings are square.
    width = (xi1-xi0-n2*tread)/2
    band = yi1-width
    start = band-n1*tread
    x0, y0 = xi0, start
    used = (ex0, start, ex1, ey1)
    if start < stair['door_centre_north_metres']+stair['door_width_metres']/2+.2 or rise > .25:
        raise ValueError('Stair flights do not fit the enclosure')
    def add(name, lo, hi, mat): boxes.append((name, tuple(lo), tuple(hi), mat))
    instances=(('se',False,False),('sw',True,False),('ne',False,True),('nw',True,True))
    voids=[mirror_rectangle(used,e,n) for _id,e,n in instances]
    shaft=settings.get('elevator',{}).get('shaft')
    holes=voids+([tuple(shaft)] if shaft else [])
    # Replace the provisional registered reservations with the four identical
    # mirrored shafts, so their edges never retain a strip of blocking slab.
    # Remove source partition fragments inside each reserved stair enclosure.
    # The photographic upper trace and legacy metric registration differ at
    # the corner offices; retaining those fragments seals the stair flights.
    for _id,e,n in instances:
        a,b,c,d=mirror_rectangle((ex0,ey0,ex1,ey1),e,n)
        hole=((a+.12,b+.12,z0),(c-.12,d-.12,z1+config['wall_height_metres']))
        boxes=[part for box in boxes for part in
               (subtract_box(box,hole) if box[3] in ('wall','courtyard_wall') else [box])]
    upper_id=levels[1]['id']
    boxes=[b for b in boxes if not b[0].startswith(upper_id+'_slab_')]
    courtyard=levels[1]['voids_local_metres'][0]
    levels[1]['voids_local_metres']=[courtyard,*voids]
    for i,rect in enumerate(interior.subtract_rectangles((-23.,-103.,24.,-20.),[courtyard,*holes])):
        add(f'{upper_id}_slab_{i:03d}',(rect[0],rect[1],z1-.22),(rect[2],rect[3],z1),'floor_room')
    landing1, landing2 = z0+n1*rise, z0+(n1+n2)*rise
    a = xi1-width
    # Thin concrete flights keep the stacked storey's underside above the
    # lower walking route; floor-solid upper flights would crush its headroom.
    for i in range(n1):
        top = z0+(i+1)*rise
        add(f'stair_se_flight1_{i}', (x0,y0+i*tread,top-.16),
            (x0+width,y0+(i+1)*tread,top),'stair_red')
        add(f'stair_se_nosing1_{i}', (x0,y0+i*tread,top-.018),
            (x0+width,y0+i*tread+.035,top+.002),'stair_nosing')
        top = z0+(n1+n2+i+1)*rise
        add(f'stair_se_flight3_{i}', (a,band-(i+1)*tread,top-.16),
            (xi1,band-i*tread,top),'stair_red')
        add(f'stair_se_nosing3_{i}', (a,band-i*tread-.035,top-.018),
            (xi1,band-i*tread,top+.002),'stair_nosing')
    for i in range(n2):
        top = landing1+(i+1)*rise
        add(f'stair_se_flight2_{i}', (x0+width+i*tread,band,top-.16),
            (x0+width+(i+1)*tread,yi1,top),'stair_red')
        add(f'stair_se_nosing2_{i}', (x0+width+i*tread,band,top-.018),
            (x0+width+i*tread+.035,yi1,top+.002),'stair_nosing')
    add('stair_se_corner_landing_1',(xi0,band,landing1-.16),(x0+width,yi1,landing1),'stair_red')
    add('stair_se_corner_landing_2',(a,band,landing2-.16),(xi1,yi1,landing2),'stair_red')
    # Photos 38/39/49: the stairwell floors are the same red as the stairs.
    add('stair_se_floor_red_ground',(xi0,yi0,z0+.001),(xi1,start,z0+.012),'stair_red')
    add('stair_se_floor_red_well',(x0+width,start,z0+.001),(a,band,z0+.012),'stair_red')
    add('stair_se_floor_red_upper',(xi0,yi0,z1+.001),(xi1,start,z1+.012),'stair_red')
    # Railings wrap the well and guard the upper landing edge; wall handrails
    # follow the outer sides of all three flights.
    rails=[]
    railing(add,rails,'stair_se_well_1',(x0+width,y0,z0),(x0+width,band,landing1))
    railing(add,rails,'stair_se_well_2',(x0+width,band,landing1),(a,band,landing2))
    railing(add,rails,'stair_se_well_3',(a,band,landing2),(a,y0,z1))
    railing(add,rails,'stair_se_upper_edge',(x0+width if continues_up else xi0,y0,z1),(a,y0,z1))
    wall_handrail(rails,'stair_se_wall_1',(xi0+.06,y0,z0),(xi0+.06,band,landing1))
    wall_handrail(rails,'stair_se_wall_2',(x0+width,yi1-.06,landing1),(a,yi1-.06,landing2))
    wall_handrail(rails,'stair_se_wall_3',(xi1-.06,band,landing2),(xi1-.06,y0,z1))
    prototype=[b for b in boxes if b[0].startswith('stair_se_')]
    for identifier,e,n in instances[1:]:
        boxes.extend(mirror_box(b,identifier,e,n) for b in prototype)
    # Ground ceiling coincides with the underside of the upper slab; no beam
    # crosses the stair void. The roof excludes the open courtyard.
    outer = (-23.,-103.,24.,-20.)
    for level, z in zip(levels, (z0,z1)):
        ceiling_holes = list(level['voids_local_metres'][:1]) + (holes if z == z0 else [])
        ceiling = z1-.23 if z == z0 else z+config['wall_height_metres']
        for i, rect in enumerate(interior.subtract_rectangles(outer,ceiling_holes)):
            add(f"{level['id']}_ceiling_{i}",(rect[0],rect[1],ceiling-.06),
                (rect[2],rect[3],ceiling),'ceiling_panel')
    seed=dict(core='stair_southeast', risers=count, rise_metres=rise,
                      tread_metres=tread, flight_width_metres=width, void=list(used),
                      bottom=[x0+width/2,y0-.65,z0],
                      top=[a+width/2,y0-.65,z1],
                      mid=[x0+width/2,(band+yi1)/2,landing1])
    seed['path']=[seed['bottom'],
        *[[x0+width/2,y0+(i+.5)*tread,z0+(i+1)*rise] for i in range(n1)],
        [x0+width/2,band+width/2,landing1],
        *[[x0+width+(i+.5)*tread,band+width/2,landing1+(i+1)*rise] for i in range(n2)],
        [a+width/2,band+width/2,landing2],
        *[[a+width/2,band-(i+.5)*tread,z0+(n1+n2+i+1)*rise] for i in range(n1)],seed['top']]
    names={'se':'stair_southeast','sw':'stair_southwest','ne':'stair_northeast','nw':'stair_northwest'}
    cores=[]
    for identifier,e,n in instances:
        core=copy.deepcopy(seed)
        core.update(id=identifier,core=names[identifier],mirror_east=e,mirror_north=n,
                    void=list(mirror_rectangle(used,e,n)))
        for key in ('bottom','top','mid'):core[key]=list(mirror_point(seed[key],e,n))
        core['path']=[list(mirror_point(p,e,n)) for p in seed['path']]
        core['rails']=mirrored(rails,lambda p:mirror_point(p,e,n),lambda s:s.replace('stair_se_','stair_'+identifier+'_',1))
        cores.append(core)
    seed['cores']=cores
    return boxes,seed


def glaze_courtyard(boxes):
    result=[]
    for name,lo,hi,material in boxes:
        if material != 'courtyard_wall' or hi[2]-lo[2] < 2.5:
            result.append((name,lo,hi,material));continue
        result.extend([
            (name+'_sill',lo,(hi[0],hi[1],lo[2]+.75),'wall'),
            (name+'_glass',(lo[0],lo[1],lo[2]+.75),(hi[0],hi[1],hi[2]-.3),'window_glass'),
            (name+'_head',(lo[0],lo[1],hi[2]-.3),hi,'wall')])
        axis = 0 if hi[0]-lo[0] > hi[1]-lo[1] else 1
        span=hi[axis]-lo[axis]
        for i in range(math.ceil(span/2.4)+1):
            a,b=list(lo),list(hi);a[axis]=lo[axis]+min(i*2.4,span-.04);b[axis]=a[axis]+.04
            a[2],b[2]=lo[2]+.75,hi[2]-.3
            result.append((name+f'_frame_{i}',tuple(a),tuple(b),'window_frame'))
    return result


def photo4_corner_glazing(boxes, levels, config, origin):
    """A103's photographed second glazed face; no other room gains this face."""
    if 'a103' not in PHOTO4_CLASSROOMS:return boxes
    room=next(r for r in levels[0]['rooms'] if r['id']=='a103')
    a,b,c,d=room['footprint_local_metres'];z=levels[0]['floor_elevation_metres']-origin[2]
    sill=z+.12;head=z+config['wall_height_metres']-.16
    opening=((c-.2,b+.45,sill),(c+.2,d-.45,head))
    result=[part for box in boxes for part in
            (subtract_box(box,opening) if box[3]=='wall' else [box])]
    result.append(('academic_ground_room_a103_side_window_glass',(c-.012,b+.45,sill),(c+.012,d-.45,head),'window_glass'))
    count=max(1,round((d-b-.9)/1.4))
    for i in range(count+1):
        y=b+.45+(d-b-.9)*i/count
        result.append((f'academic_ground_room_a103_side_window_mullion_{i}',(c-.045,y-.025,sill),(c+.045,y+.025,head),'window_frame'))
    for i,h in enumerate((sill,z+1.9,head)):
        result.append((f'academic_ground_room_a103_side_window_transom_{i}',(c-.045,b+.425,h-.025),(c+.045,d-.425,h+.025),'window_frame'))
    room['fitout']['secondary_glazing']=dict(side='east',source_walk_20261027=[4],
        status='Photo4 shows glazed teaching front and adjacent side; geographic orientation uses provisional legacy plan registration')
    return result


def fit_acquario(boxes, levels, config, origin):
    """Photo9's one open study room, not a set of invented teaching cells.

    Bounds follow the SALA STUDIO strip in plans10/17/18, between the two
    photocopy spaces. Furniture sizes/count remain deliberately approximate.
    """
    ground=levels[0]
    room=next(r for r in ground['rooms'] if r['id']=='acquario')
    a,b,c,d=room['footprint_local_metres'];z=ground['floor_elevation_metres']-origin[2]
    height=config['wall_height_metres'];t=config['wall_thickness_metres']
    # Preserve opaque end partitions and the continuous courtyard windows.
    # Replace only this room's corridor frontage with full-height glazing.
    hole=((a-t,b+.1,z),(a+t,d-.1,z+height))
    result=[part for box in boxes for part in
            (subtract_box(box,hole) if box[3] in ('wall','window_glass','window_frame') else [box])]
    def add(name,lo,hi,mat):result.append(('academic_ground_acquario_'+name,tuple(lo),tuple(hi),mat))
    door=b+(d-b)*room['door_fraction'];half=room['door_width_metres']/2
    for i,(lo,hi) in enumerate(((b+.1,door-half),(door+half,d-.1))):
        add('corridor_glass_'+str(i),(a-.025,lo,z+.02),(a+.025,hi,z+height-.15),'window_glass')
    add('corridor_glass_head',(a-.025,door-half,z+config['door_height_metres']),
        (a+.025,door+half,z+height-.15),'window_glass')
    stops=[b+.1,d-.1,door-half-.04,door+half+.04]
    stops.extend(b+(d-b)*i/10 for i in range(1,10) if abs(b+(d-b)*i/10-door)>half+.12)
    for i,y in enumerate(stops):
        add('corridor_mullion_'+str(i),(a-.055,y-.018,z),(a+.055,y+.018,z+height),'window_frame')
    add('floor',(a+.1,b+.1,z),(c-.1,d-.1,z+.014),'floor_wood')
    points=[]
    # Sparse shared tables, chairs on both sides, flat floor and no teaching
    # front. The photograph establishes this topology, not a table census.
    for row,fraction in enumerate((.25,.5,.75)):
        y=b+(d-b)*fraction
        for column,x in enumerate((a+1.15,c-1.15)):
            token=f'table_{row}_{column}'
            add(token+'_top',(x-.8,y-.5,z+.72),(x+.8,y+.5,z+.77),'seat_wood')
            for ix in (-.65,.65):
                for iy in (-.38,.38):
                    add(token+f'_leg_{ix}_{iy}',(x+ix-.025,y+iy-.025,z),(x+ix+.025,y+iy+.025,z+.72),'metal_dark')
            for side in (-1,1):
                for offset in (-.42,.42):
                    yy=y+side*.85;xx=x+offset
                    chair=token+f'_chair_{side}_{offset}'
                    add(chair+'_seat',(xx-.22,yy-.21,z+.43),(xx+.22,yy+.21,z+.48),'seat_wood')
                    back=yy+side*.19
                    add(chair+'_back',(xx-.22,back-.025,z+.48),(xx+.22,back+.025,z+.88),'seat_wood')
                    for dx in (-.17,.17):
                        add(chair+f'_leg_{dx}',(xx+dx-.018,yy-.15,z),(xx+dx+.018,yy+.15,z+.43),'metal_dark')
        points.append([(a+c)/2,y])
    room['fitout']=dict(tables=6,seats=24,furniture=['shared_tables','chairs'],rows=[],
                        teaching_front=False,source_photos=[9],
                        status='Observed open study furniture; table count and dimensions provisional',
                        audit_points_local_metres=points)
    room['glazing']=dict(corridor_side='west',courtyard_side='east',source_photos=[9,17],
                         status='Continuous frontage; mullion spacing and doorway width estimated')
    return result


def isolate_rooms(boxes, levels, settings, config, origin):
    """Keep room-to-room boundaries opaque after window/office conversions."""
    result=list(boxes);thickness=config['wall_thickness_metres']
    for level in levels:
        z=level['floor_elevation_metres']-origin[2];partitions=[]
        exceptions={frozenset(pair) for pair in settings.get('open_room_connections',{}).get(level['id'],[])}
        rooms=level['rooms']
        for i,first in enumerate(rooms):
            a,b,c,d=first['footprint_local_metres']
            for second in rooms[i+1:]:
                if frozenset((first['id'],second['id'])) in exceptions:continue
                e,f,g,h=second['footprint_local_metres'];rect=None
                if abs(c-e)<1e-7 or abs(a-g)<1e-7:
                    low,high=max(b,f),min(d,h);x=(c+e)/2 if abs(c-e)<1e-7 else (a+g)/2
                    if high-low>1e-6:rect=(x-thickness/2,low-thickness/2,x+thickness/2,high+thickness/2)
                elif abs(d-f)<1e-7 or abs(b-h)<1e-7:
                    low,high=max(a,e),min(c,g);y=(d+f)/2 if abs(d-f)<1e-7 else (b+h)/2
                    if high-low>1e-6:rect=(low-thickness/2,y-thickness/2,high+thickness/2,y+thickness/2)
                if rect is None:continue
                lo=(rect[0],rect[1],z);hi=(rect[2],rect[3],z+config['wall_height_metres'])
                hole=(lo,hi)
                result=[piece for box in result for piece in
                        (subtract_box(box,hole) if box[3] in ('wall','courtyard_wall','reception_glass','window_glass','window_frame') else [box])]
                name=level['id']+'_partition_'+first['id']+'_'+second['id']
                result.append((name,lo,hi,'wall'))
                partitions.append(dict(rooms=[first['id'],second['id']],bounds=[*lo,*hi]))
        level['room_partitions']=partitions
    return result

def elevator_shaft(boxes, levels, settings, config):
    """The lift beside the reception: a two-storey shaft with a ladder inside.

    A CS2 moving lift platform is untested, so the vertical route is a ladder
    on the back wall; metadata['elevator']['ladder'] becomes CS2's climbable
    ladder surface. Openings face the corridor on both floors.
    """
    spec=settings.get('elevator')
    if not spec:return boxes,None
    x0,y0,x1,y1=spec['shaft'];zs=[l['floor_elevation_metres']-370 for l in levels];z0,z1=zs[0],zs[-1]
    top=z1+config['wall_height_metres'];y=spec['opening_centre_north_metres'];w=spec['opening_width_metres']/2
    # Clear the corner of the classroom above (and anything else in the way).
    volume=((x0,y0,z0),(x1,y1,top))
    result=[p for b in boxes for p in subtract_box(b,volume)]
    for z in zs:
        hole=((x1-.2,y-w,z-.01),(x1+.5,y+w,z+2.2))
        result=[p for b in result for p in (subtract_box(b,hole) if b[3]=='wall' else [b])]
    def add(name,lo,hi,mat):result.append(('elevator_'+name,tuple(lo),tuple(hi),mat))
    t=.1
    add('wall_west',(x0,y0,z0),(x0+t,y1,top),'wall')
    add('wall_south',(x0,y0,z0),(x1,y0+t,top),'wall')
    add('wall_north',(x0,y1-t,z0),(x1,y1,top),'wall')
    for i,(lo,hi) in enumerate((((x1-t,y0,z0),(x1,y-w,top)),((x1-t,y+w,z0),(x1,y1,top)))):
        add(f'wall_east_{i}',lo,hi,'wall')
    for zi,z in enumerate(zs):
        label=levels[zi]['id']
        next_floor=zs[zi+1] if zi+1<len(zs) else top
        add(f'wall_east_header_{label}',(x1-t,y-w,z+2.2),(x1,y+w,next_floor),'wall')
        # Steel portal frame and call button on the corridor side.
        for i,yy in enumerate((y-w-.06,y+w)):
            add(f'{label}_portal_jamb_{i}',(x1,yy,z),(x1+.2,yy+.06,z+2.26),'metal_dark')
        add(f'{label}_portal_head',(x1,y-w-.06,z+2.2),(x1+.2,y+w+.06,z+2.26),'metal_dark')
        add(f'{label}_call_button',(x1+.18,y+w+.2,z+1.05),(x1+.2,y+w+.32,z+1.25),'sign_white')
    inner=(x0+t,y0+t,x1-t,y1-t)
    # Floors carry their level prefix, as the clearance audit expects.
    result.append(('academic_ground_elevator_floor',(inner[0],inner[1],z0-.2),(inner[2],inner[3],z0+.012),'floor_circulation'))
    # Upper ledge on the opening side; the ladder side stays open to climb.
    ledge=inner[0]+1.0
    for level,z in zip(levels[1:],zs[1:]):
        result.append((level['id']+'_elevator_ledge',(ledge,inner[1],z-.22),(x1,inner[3],z),'floor_circulation'))
    add('first_ledge_edge',(ledge,inner[1],z1),(ledge+.04,inner[3],z1+.012),'metal_dark')
    # Visible ladder on the back wall: rails and rungs, no collision (`_finish_`).
    a,b=y-.3,y+.3;wall=inner[0]
    for i,yy in enumerate((a,b)):
        add(f'ladder_finish_rail_{i}',(wall,yy-.025,z0),(wall+.16,yy+.025,z1+1.0),'metal_dark')
    for i in range(int((z1+.9-z0-.25)/.28)+1):
        h=z0+.25+i*.28
        add(f'ladder_finish_rung_{i}',(wall+.1,a,h),(wall+.14,b,h+.035),'metal_dark')
    centre=[(inner[0]+inner[2])/2,y]
    # A 0.2 m tool volume held the standing hull under the upper ledge.
    # Its front face must stay close to the visible rungs for full headroom.
    return result,dict(room=spec['room'],shaft=spec['shaft'],ladder=[[wall,a,z0],[wall+.12,b,z1+1.65]],
                       lights=[[*centre,z0+2.6],[*centre,z1+2.6]],
                       sign=[x1+.22,y,z1+2.44],
                       stations=dict(ground=[ledge-.2,y],first=[(ledge+inner[2])/2,y]))


def enclose_stair(boxes, levels, stair, settings, config, *, include_top=True):
    """Photo 38's black fire doors open into the hall; photo 39's outer glazing."""
    bounds = settings['stairs']['enclosure_bounds_local_metres']
    x0,y0,x1,y1 = bounds
    z0,z1 = [l['floor_elevation_metres']-370 for l in levels]
    top = z1+config['wall_height_metres'] if include_top else z1
    thickness = config['wall_thickness_metres']
    centre = settings['stairs']['door_centre_north_metres']
    width = settings['stairs']['door_width_metres']
    door_height = 2.2
    result = list(boxes)
    wall = [('stair_enclosure_west',(x0-thickness/2,y0,z0),(x0+thickness/2,y1,top),'wall')]
    portals = []
    for floor,z in enumerate((z0,z1)):
        if floor == 1 and not include_top:
            # The following segment owns this floor's enclosure and doors.
            portals.append(dict(floor=floor,centre=[x0,centre,z],width=width,height=door_height))
            continue
        hole = ((x0-thickness,centre-width/2,z-.01),
                (x0+thickness,centre+width/2,z+door_height))
        wall = [part for b in wall for part in subtract_box(b,hole)]
        portals.append(dict(floor=floor,centre=[x0,centre,z],width=width,height=door_height))
        # Two leaves swung 90 degrees out into the corridor. Keep the opening
        # clear and include the door panels in actual collision.
        for side,sign in enumerate((-1,1)):
            y = centre+sign*width/2
            name=f'stair_door_{floor}_{side}'
            result.append((name+'_leaf',(x0-width/2,y-.022,z+.025),
                           (x0,y+.022,z+door_height-.025),'door_black'))
            result.append((name+'_pushbar',(x0-width/2+.08,y-sign*.055-.012,z+1.02),
                           (x0-.08,y-sign*.055+.012,z+1.065),'door_pushbar'))
            result.append((name+'_hinge',(x0-.025,y-.035,z+.12),
                           (x0+.025,y+.035,z+2.05),'window_frame'))
            result.append((name+'_jamb',(x0-.11,y-.025,z),
                           (x0+.11,y+.025,z+door_height+.05),'window_frame'))
        result.append((f'stair_door_{floor}_head',(x0-.11,centre-width/2-.05,z+door_height),
                       (x0+.11,centre+width/2+.05,z+door_height+.05),'window_frame'))
    result.extend(wall)
    for name,y in (('south',y0),('north',y1)):
        result.append(('stair_enclosure_'+name,(x0-thickness/2,y-thickness/2,z0),
                       (x1,y+thickness/2,top),'wall'))
    # Cut the existing outer wall rather than layering glass over opaque mass.
    for floor,z in enumerate((z0,z1) if include_top else (z0,)):
        bottom,head = z+.65,z+config['wall_height_metres']-.25
        window = ((x1-.22,y0+.45,bottom),(x1+.22,y1-.45,head))
        result = [part for b in result for part in (subtract_box(b,window) if b[3]=='wall' else [b])]
        result.append((f'stair_window_{floor}',(x1-.015,y0+.45,bottom),
                       (x1+.015,y1-.45,head),'window_glass'))
        for i in range(7):
            y=y0+.45+(y1-y0-.9)*i/6
            result.append((f'stair_window_{floor}_mullion_{i}',(x1-.045,y-.025,bottom),
                           (x1+.045,y+.025,head),'window_frame'))
        for i,h in enumerate((bottom,z+1.9,head)):
            result.append((f'stair_window_{floor}_transom_{i}',(x1-.045,y0+.425,h-.025),
                           (x1+.045,y1-.425,h+.025),'window_frame'))
    stair['enclosure'] = dict(bounds=bounds,portals=portals,door_open_degrees=90,
                              reference_photos=[38,39])
    prototype=[b for b in result if b[0].startswith(('stair_enclosure_','stair_door_','stair_window_'))]
    for core in stair['cores']:
        e,n=core['mirror_east'],core['mirror_north']
        enclosure=copy.deepcopy(stair['enclosure'])
        enclosure['bounds']=list(mirror_rectangle(bounds,e,n))
        for portal in enclosure['portals']:portal['centre']=list(mirror_point(portal['centre'],e,n))
        core['enclosure']=enclosure
        if core['id']=='se':continue
        for floor,z in enumerate((z0,z1) if include_top else (z0,)):
            bottom,head=z+.65,z+config['wall_height_metres']-.25
            a=mirror_point((x1-.22,y0+.45,bottom),e,n)
            b=mirror_point((x1+.22,y1-.45,head),e,n)
            window=(tuple(min(a[i],b[i]) for i in range(3)),tuple(max(a[i],b[i]) for i in range(3)))
            result=[part for box in result for part in (subtract_box(box,window) if box[3]=='wall' else [box])]
        for box in prototype:
            original_name,lo,hi,mat=box
            canonical=(original_name.replace('stair_','stair_se_',1),lo,hi,mat)
            result.append(mirror_box(canonical,core['id'],e,n))
    return result


@memoize_geometry
def build_geometry(root=ROOT,*,include_exterior=True):
    settings, config = derived_config(root)
    alignment = json.loads((root / config['alignment']).read_text())
    campus = json.loads((root / config['campus_config']).read_text())
    origin = campus['origin']
    # Validate the original reference bytes before deriving the playable model.
    for profile in alignment['profiles']:
        if hashlib.sha256((root/profile['source_file']).read_bytes()).hexdigest() != profile['sha256']:
            raise ValueError('Plan source hash mismatch')
    manifest_path=root/config['photo_reference']['manifest']
    manifest=json.loads(manifest_path.read_text())['images']
    for identifier in config['photo_reference']['ids']:
        photo=next(p for p in manifest if p['id']==identifier)
        if hashlib.sha256((manifest_path.parent/photo['file']).read_bytes()).hexdigest()!=photo['sha256']:
            raise ValueError('Photo source hash mismatch')
    boxes, levels = interior.build_boxes(config,alignment,origin)
    for level in levels:
        z=level['floor_elevation_metres']-origin[2]
        for room in level['rooms']:
            if room['kind']=='reception':
                a,b,c,d=room['footprint_local_metres']
                hole=((a-.11,b-.11,z-.01),(c+.11,d+.11,z+config['wall_height_metres']+.01))
                boxes=[part for box in boxes for part in
                       (subtract_box(box,hole) if box[3] in ('wall','courtyard_wall') else [box])]
                boxes.extend(reception_boxes(level['id']+'_'+room['id'],(a,b,c,d),z,config['wall_height_metres'],'east'))
                room['fitout']=dict(seats=5,rows=[],furniture=['desks','chairs','computers','storage'],
                                   staff=3,front_staff='female',audit_points_local_metres=[])
            elif room['kind']=='restroom':
                boxes.extend(restroom_boxes(level['id'],room,z,config['wall_height_metres']))
    boxes=isolate_rooms(boxes,levels,settings,config,origin)
    boxes=glaze_courtyard(boxes)
    boxes=fit_acquario(boxes,levels,config,origin)
    boxes=photo4_corner_glazing(boxes,levels,config,origin)
    boxes, stair=stairs_and_roof(boxes,levels,settings,config,origin,continues_up=True)
    boxes = enclose_stair(boxes, levels, stair, settings, config, include_top=False)
    # Today's plans identify A2xx as floor 0, with a separate office/bridge
    # floor 1 above it. Preserve logical elevation order in public metadata.
    try:
        from .povo1_survey import source_config
    except ImportError:
        from povo1_survey import source_config
    survey_config,survey_alignment=source_config(root)
    upper_source=survey_config['levels'][-1]
    survey_config['levels']=[upper_source]
    survey_config['classroom_fitouts']=[]
    survey_config['wall_height_metres']=config['wall_height_metres']
    upper_boxes,upper_levels=interior.build_boxes(survey_config,survey_alignment,origin)
    upper=upper_levels[0]
    upper['user_floor']=1
    upper['source_photos']=[22,31,32]
    upper['survey_status']='Manual source trace; dimensions and door widths provisional'
    for record,source in zip(levels,config['levels']):
        record['user_floor']=source['user_floor']
        record['labels']['source_plan_floor']=source['user_floor']
        record['labels'].pop('user_confirmed_floor',None)
    upper_boxes=isolate_rooms(upper_boxes,[upper],settings,config,origin)
    upper_boxes=glaze_courtyard(upper_boxes)
    upper_boxes,upper_stair=stairs_and_roof(upper_boxes,[levels[1],upper],settings,config,origin)
    # The first segment's middle-level roof is superseded by the new slab.
    boxes=[b for b in boxes if not b[0].startswith('academic_first_ceiling_')]
    upper_boxes=enclose_stair(upper_boxes,[levels[1],upper],upper_stair,settings,config)
    upper_boxes=[(name+'_upper_segment' if name.startswith(('stair_','elevator_')) else name,lo,hi,mat)
                 for name,lo,hi,mat in upper_boxes]
    boxes.extend(upper_boxes)
    stair['segments']=[copy.deepcopy(stair),upper_stair]
    stair['top']=upper_stair['top']
    for core,upper_core in zip(stair['cores'],upper_stair['cores']):
        core['top']=upper_core['top']
        core['rails'].extend([dict(r,name=r['name']+'_upper_segment') for r in upper_core['rails']])
        core['enclosure']['portals'].append(upper_core['enclosure']['portals'][-1])
    levels.append(upper)
    config['levels'].append(upper_source)
    config['survey_20261027']=survey_config['survey_20261027']
    boxes, elevator = elevator_shaft(boxes, levels, settings, config)
    if elevator:levels[0]['elevator']=elevator
    try:
        from .povo1_courtyard_stair import extend as add_courtyard_stair
    except ImportError:
        from povo1_courtyard_stair import extend as add_courtyard_stair
    boxes,courtyard_stair=add_courtyard_stair(boxes,levels,origin)
    stair['courtyard']=courtyard_stair
    bridge_levels=[levels[0],levels[-1]]
    if settings.get('povo2_connection'):
        boxes=extend_campus(boxes,bridge_levels,root,config['wall_height_metres'])
        if settings.get('povo2_planimetry'):
            if levels[-1]['connection'].get('compact_arrival'):
                boxes=integrate_povo2(boxes,bridge_levels,root,config['wall_height_metres'])
            else:
                boxes=extend_povo2(boxes,bridge_levels,root,config['wall_height_metres'])
    # Omit tiny ceiling grids/seat stems from this first in-game asset.
    boxes=[b for b in boxes if not any(t in b[0] for t in ('_grid_','_slat','_stem'))]
    z=levels[0]['floor_elevation_metres']-origin[2]
    court=levels[0]['voids_local_metres'][0]
    boxes.append(('campus_courtyard_floor',(court[0],court[1],z-.2),(court[2],court[3],z-.02),'courtyard_ground'))
    # Small outside landing exposes the registered entrance without opening the
    # undeveloped campus. A railing bounds it; the accepted arena remains separate.
    entry_y=alignment['profiles'][0]['entrance_geographic'][1]-origin[1]
    boxes.append(('campus_entry_landing',(24,entry_y-3,z-.3),(29,entry_y+3,z),'floor_circulation'))
    # Closed north-wing doors are visible panels over solid collision walls.
    for room in levels[0]['rooms']:
        if room.get('playable',True):continue
        if room['kind'] in ('reception','elevator'):continue
        a,b,c,d=room['footprint_local_metres'];x=a+(c-a)*room['door_fraction']
        boxes.append((room['id']+'_closed_door',(x-.58,b-.12,z+.02),
                      (x+.58,b-.095,z+2.1),'door_closed'))
    for i,(lo,hi) in enumerate((((28.8,entry_y-3,z),(29,entry_y+3,z+1.2)),
                               ((24,entry_y-3,z),(29,entry_y-2.85,z+1.2)),
                               ((24,entry_y+2.85,z),(29,entry_y+3,z+1.2)))):
        boxes.append((f'campus_entry_guard_{i}',lo,hi,'window_glass'))
    boxes = finish_details(boxes, levels, config)
    if include_exterior:
        try:
            from .povo_exterior_integration import extend as add_exterior
        except ImportError:
            from povo_exterior_integration import extend as add_exterior
        boxes=add_exterior(root,settings,config,boxes,bridge_levels,stair)
    if include_exterior and settings.get('povo2_planimetry'):
        try:
            from .povo2_interiors import extend_layout
        except ImportError:
            from povo2_interiors import extend_layout
        boxes=extend_layout(boxes,bridge_levels,root,config['wall_height_metres'])
        try:
            from .povo_wings import extend as extend_wings
        except ImportError:
            from povo_wings import extend as extend_wings
        boxes=extend_wings(boxes,bridge_levels,root)
        try:
            from .povo2_sketch import extend as apply_sketch
            from .povo_pavement import extend as repair_pavement
            from .povo_library_stair import extend as add_library_stair
        except ImportError:
            from povo2_sketch import extend as apply_sketch
            from povo_pavement import extend as repair_pavement
            from povo_library_stair import extend as add_library_stair
        boxes=apply_sketch(boxes,bridge_levels)
        boxes=repair_pavement(boxes,bridge_levels,root)
        boxes=add_library_stair(boxes,bridge_levels)
        try:
            from .povo2_gardens import extend as add_gardens
        except ImportError:
            from povo2_gardens import extend as add_gardens
        try:
            from .povo2_internal_stairs import extend as correct_internal_stairs
        except ImportError:
            from povo2_internal_stairs import extend as correct_internal_stairs
        boxes=correct_internal_stairs(boxes,bridge_levels,root)
        # Excavate the exit after the stair/garage infills have been added.
        boxes=add_gardens(boxes,bridge_levels,root)
        try:
            from .povo2_basements import extend as rebuild_basements
        except ImportError:
            from povo2_basements import extend as rebuild_basements
        boxes=rebuild_basements(boxes,bridge_levels,root)
    try:
        from .povo_room_furnishings import furnish
    except ImportError:
        from povo_room_furnishings import furnish
    boxes=furnish(boxes,levels,stair,origin)
    return settings,config,boxes,levels,stair


def finish_details(boxes, levels, config):
    """Frames, skirtings and visible corridor luminaires from the walk photos."""
    result = list(boxes)
    for name, lo, hi, material in boxes:
        if material != 'wall' or hi[2] - lo[2] < 2.5:
            continue
        # Follow actual solid spans so the trim never bridges a doorway.
        axis = 0 if hi[0] - lo[0] > hi[1] - lo[1] else 1
        for side in (0, 1):
            a, b = list(lo), list(hi)
            other = 1 - axis
            a[other] = lo[other] - .012 if side == 0 else hi[other]
            b[other] = a[other] + .012
            a[2], b[2] = lo[2] + .015, lo[2] + .11
            result.append((name + f'_finish_skirting_{side}', tuple(a), tuple(b), 'window_frame'))
    for level in levels:
        z = level['floor_elevation_metres'] - 370
        for room in [*level['rooms'],*level.get('connection',{}).get('rooms',[])]:
            if not room.get('playable', True) and room['kind']!='reception':
                continue
            a, b, c, d = room['footprint_local_metres']
            f = room['door_fraction']
            side = room['door_side']
            x, y = {'u_min':(a+(c-a)*f,b), 'u_max':(a+(c-a)*f,d),
                    'v_min':(a,b+(d-b)*f), 'v_max':(c,b+(d-b)*f)}[side]
            # A fixed physical plaque above the door, with its outer face
            # beyond the wall; the matching text never rotates toward players.
            nx,ny={'u_min':(0,-1),'u_max':(0,1),'v_min':(-1,0),'v_max':(1,0)}[side]
            normal=config['wall_thickness_metres']/2+.015
            px,py=x+nx*normal,y+ny*normal
            along=0 if side.startswith('u_') else 1
            lo,hi=[px-.01,py-.01,z+2.28],[px+.01,py+.01,z+2.6]
            lo[along]-=.615;hi[along]+=.615
            result.append((level['id']+'_'+room['id']+'_finish_sign_plaque',tuple(lo),tuple(hi),'sign_blue'))
            if not room.get('playable',True):continue
            axis = 0 if side.startswith('u_') else 1
            centre = [x, y]
            half = room['door_width_metres'] / 2
            depth = config['wall_thickness_metres'] / 2 + .018
            for i, offset in enumerate((-half-.025, half+.025)):
                lo, hi = [x-depth,y-depth,z+.015], [x+depth,y+depth,z+config['door_height_metres']+.045]
                lo[axis], hi[axis] = centre[axis]+offset-.025, centre[axis]+offset+.025
                result.append((room['id']+f'_finish_door_jamb_{i}', tuple(lo), tuple(hi), 'window_frame'))
            lo, hi = [x-depth,y-depth,z+config['door_height_metres']], [x+depth,y+depth,z+config['door_height_metres']+.05]
            lo[axis], hi[axis] = centre[axis]-half-.05, centre[axis]+half+.05
            result.append((room['id']+'_finish_door_head', tuple(lo), tuple(hi), 'window_frame'))
        ceiling = 7.31 if level['id'] == 'academic_ground' else z+config['wall_height_metres']-.06
        for corridor in level['circulation']:
            a,b,c,d = corridor['bounds']
            x0,x1 = -23+b*47,-23+d*47
            y0,y1 = -103+a*83,-103+c*83
            axis = 1 if y1-y0 > x1-x0 else 0
            length = (y1-y0) if axis else (x1-x0)
            count = max(1, math.ceil(length/4.2))
            for i in range(count):
                x,y = (x0+x1)/2,(y0+y1)/2
                if axis: y = y0+(i+.5)*length/count
                else: x = x0+(i+.5)*length/count
                name = level['id']+'_'+corridor['id']+f'_finish_fixture_{i}'
                result.append((name+'_rim',(x-.33,y-.33,ceiling-.055),(x+.33,y+.33,ceiling-.005),'window_frame'))
                result.append((name+'_diffuser',(x-.29,y-.29,ceiling-.062),(x+.29,y+.29,ceiling-.054),'light_diffuser'))
    return result


def subtract_polygon_box(polygon,lo,hi):
    """Subtract one box from a convex textured polygon, preserving UVs."""
    def clip(poly,axis,bound,keep_low):
        out=[]
        if not poly:return out
        for (a,ta),(b,tb) in zip(poly,poly[1:]+poly[:1]):
            inside=a[axis]<=bound if keep_low else a[axis]>=bound
            other=b[axis]<=bound if keep_low else b[axis]>=bound
            if inside:out.append((a,ta))
            if inside!=other:
                f=(bound-a[axis])/(b[axis]-a[axis])
                out.append((tuple(a[i]+f*(b[i]-a[i]) for i in range(3)),
                            tuple(ta[i]+f*(tb[i]-ta[i]) for i in range(2))))
        clean=[]
        for item in out:
            if not clean or any(abs(a-b)>1e-9 for a,b in zip(item[0],clean[-1][0])):clean.append(item)
        if len(clean)>1 and all(abs(a-b)<1e-9 for a,b in zip(clean[0][0],clean[-1][0])):clean.pop()
        return clean
    remainder=polygon;outside=[]
    for axis in range(3):
        for bound,low in ((lo[axis],True),(hi[axis],False)):
            piece=clip(remainder,axis,bound,low)
            if len(piece)>=3:outside.append(piece)
            remainder=clip(remainder,axis,bound,not low)
            if len(remainder)<3:return outside
    return outside


def backdrop_mesh(root):
    """Retain campus context, removing solid Povo 1 and the temporary arena."""
    vertices=[];uvs=[];faces=[];name='';material=''
    for line in (root/'exports/povo_blockout/povo_blockout.obj').read_text().splitlines():
        p=line.split()
        if not p:continue
        if p[0]=='v':vertices.append(tuple(map(float,p[1:4])))
        elif p[0]=='vt':uvs.append(tuple(map(float,p[1:3])))
        elif p[0]=='o':name=p[1]
        elif p[0]=='usemtl':material=p[1]
        elif p[0]=='f':
            if name.startswith(('povo1_','arch_povo1_','cover_','boundary_','calibration')):continue
            if name.startswith(('bridge_reference_','arch_bridge_')):continue
            refs=[tuple(int(x) if x else 0 for x in ref.split('/')) for ref in p[1:]]
            points=[vertices[r[0]-1] for r in refs]
            if name=='terrain' and any((-24<=v[0]<=30 and -106<=v[1]<=-18) or
                                      (3.4<=v[0]<=43.2 and 9.8<=v[1]<=42.2) or
                                      (9.8<=v[0]<=34.7 and 19.3<=v[1]<=73.7) for v in points):continue
            tex=[uvs[r[1]-1] if len(r)>1 and r[1] else (0,0) for r in refs]
            if name.startswith(('povo2_east','arch_povo2_core_', 'povo2_south',
                                'povo2_southeast_annex','arch_povo2_annex_')):
                # Remove the old solid mass from the newly opened arrival;
                # retain its northern context by clipping both geometry and UVs.
                poly=list(zip(points,tex));clipped=[]
                for first,second in zip(poly,poly[1:]+poly[:1]):
                    a,ta=first;b,tb=second;inside=a[1]>=42;other=b[1]>=42
                    if inside:clipped.append(first)
                    if inside!=other:
                        f=(42-a[1])/(b[1]-a[1])
                        clipped.append((tuple(a[i]+f*(b[i]-a[i]) for i in range(3)),
                                        tuple(ta[i]+f*(tb[i]-ta[i]) for i in range(2))))
                if len(clipped)<3:continue
                points,tex=map(list,zip(*clipped))
            polygons=[list(zip(points,tex))]
            if name.startswith(('povo2_','arch_povo2_')):
                # Clear only the occupied lower floors from the old solid
                # scenery. Keep the completed upper arrival and upper backdrop.
                for lo,hi in (((9.9,19.3,3.7),(34.7,73.7,7.37)),
                              ((16.3,-6.7,.1),(31.7,26.2,3.77)),
                              ((-1.7,13.8,-3.5),(34.7,51.7,.17)),
                              ((6.8,13.8,-3.5),(16.7,26.2,7.37))):
                    polygons=[part for poly in polygons for part in subtract_polygon_box(poly,lo,hi)]
            for poly in polygons:
                p,t=map(list,zip(*poly))
                # Triangulation avoids a clipped polygon starting with three
                # collinear vertices in the native OBJ importer.
                for i in range(1,len(p)-1):
                    a,b,c=p[0],p[i],p[i+1]
                    u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
                    cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                    if sum(x*x for x in cross)>1e-14:faces.append((name,material,[p[0],p[i],p[i+1]],[t[0],t[i],t[i+1]]))
    return faces


def material_path(material):
    """Compiled-material source for one campus OBJ material name."""
    if material in ('window_glass','reception_glass'):return MATERIAL_PREFIX+material+'.vmat'
    if material.startswith('exterior_'):return EXTERIOR_PREFIX+material.removeprefix('exterior_')+'.vmat'
    return MATERIAL_PREFIX+material+'.vmat'


# Backdrop masses, vehicles and screens: their "glass" has nothing playable behind it.
UNBREAKABLE_GLASS=('_cabin','_screen_','residential_','povo2_west_glazing','povo2_front_window',
                   'povo2_end_window','povo2_front_annex_')


def is_breakable_glass(box):
    """Playable building glass; receptions stay sealed (unplayable offices)."""
    name,_,_,material=box
    return (material in ('window_glass','exterior_glass','exterior_entry_glass')
            and not any(t in name for t in UNBREAKABLE_GLASS))


AUTO_DOOR_PART=re.compile(r'exterior_((?:p[12]_entry_(?:outer_|inner_)?|(?:library|canteen(?:_outer|_inner|_upper)?)_entry_)bank_\d)_(parked_leaf|parked_leaf_band|leaf_bottom)_(-?1)$')


def split_auto_doors(boxes):
    """Povo 1 and Povo 2 sliding entrance leaves, moved from parked-open to closed.

    Each bank becomes one door name. Every leaf part slides by its own width
    toward the sidelight it parks over, which is how func_door measures travel.
    """
    banks={};rest=[]
    for box in boxes:
        match=AUTO_DOOR_PART.match(box[0])
        if not match:rest.append(box);continue
        name,lo,hi,material=box;sign=int(match[3]);width=hi[1]-lo[1]
        closed_lo=(lo[0],lo[1]-sign*width,lo[2]);closed_hi=(hi[0],hi[1]-sign*width,hi[2])
        # Source yaw 0 is local south (-north); see cs2_campus.world().
        banks.setdefault(match[1],[]).append(dict(name=name,lo=list(closed_lo),hi=list(closed_hi),
                                                 material=material_path(material),yaw=0 if sign<0 else 180))
    doors=[]
    for bank,parts in sorted(banks.items()):
        x=parts[0]['lo'][0];z=min(p['lo'][2] for p in parts)
        # Opens about two metres before a player reaches the door line.
        trigger=([x-2,min(p['lo'][1] for p in parts)-.9,z],[x+2,max(p['hi'][1] for p in parts)+.9,z+2.6])
        doors.append(dict(name=bank,parts=parts,trigger=trigger))
    return doors,rest


def all_rails(stair,levels):
    rails=[r for core in stair['cores'] for r in core['rails']]
    rails+=stair.get('courtyard',{}).get('rails',[])
    link=next((l['connection'] for l in levels if 'connection' in l),{})
    rails+=link.get('stair',{}).get('rails',[])
    rails+=link.get('povo2',{}).get('stairs',{}).get('rails',[])
    rails+=[r for wing in levels[0].get('wings',{}).get('stairs',[]) for r in wing.get('rails',[])]
    rails+=levels[0].get('library_stair',{}).get('rails',[])
    return rails


def export(root=ROOT):
    settings, config, boxes, levels, stair = build_geometry(root)
    try:
        from .povo_spawns import deathmatch_spawns
    except ImportError:
        from povo_spawns import deathmatch_spawns
    # Spawns use the complete solid campus: closed doors and intact glass block.
    spawns=deathmatch_spawns(collision_boxes(boxes),levels)
    # Doors and breakable panes become separate map entities, so leave them out
    # of the static model and its collision. build_geometry() keeps them solid.
    doors,boxes=split_auto_doors(boxes)
    glass=[b for b in boxes if is_breakable_glass(b)]
    boxes=[b for b in boxes if not is_breakable_glass(b)]
    try:
        from .povo_interactions import extract_static_leaves
        from .povo_atmosphere import write_winter_assets, write_soundevents
    except ImportError:
        from povo_interactions import extract_static_leaves
        from povo_atmosphere import write_winter_assets, write_soundevents
    try:
        from .povo_physics_surfaces import write_groups,modeldoc_groups
    except ImportError:
        from povo_physics_surfaces import write_groups,modeldoc_groups
    boxes=extract_static_leaves(boxes,levels,stair,automatic_entrances=True)
    try:
        from .povo_exterior_integration import mesh_faces,write_collision,backdrop as exterior_backdrop
    except ImportError:
        from povo_exterior_integration import mesh_faces,write_collision,backdrop as exterior_backdrop
    exterior=levels[0].get('exterior',{})
    output=root/'exports/povo_campus';output.mkdir(parents=True,exist_ok=True)
    scenery=backdrop_mesh(root)
    if exterior:scenery=exterior_backdrop(scenery)
    try:
        from .povo_pavement import smooth_apron_lighting
    except ImportError:
        from povo_pavement import smooth_apron_lighting
    visual=render_obj(boxes,[*scenery,*campus_staff_meshes(levels),*mesh_faces(exterior),*rail_faces(all_rails(stair,levels))])
    visual_tmp=output/'povo1_campus.obj.tmp'
    visual_tmp.write_text(smooth_apron_lighting(visual),encoding='utf-8')
    visual_tmp.replace(output/'povo1_campus.obj')
    try:
        from .povo_pavement_lighting import write_assets as write_pavement_lighting
    except ImportError:
        from povo_pavement_lighting import write_assets as write_pavement_lighting
    if exterior:write_pavement_lighting((output/'povo1_campus.obj').read_text(encoding='utf-8'),root)
    collision=io.StringIO();collision.write('o povo1_campus_collision\n');ci=0;collision_count=0
    last_material=None
    physics=collision_boxes(boxes)
    for index,(name,lo,hi,material) in enumerate(sorted(physics,key=lambda b:b[3])):
        if index%64==0:collision.write(f'o campus_physics_{index//64}\n')
        part=io.StringIO();write_box(part,name,lo,hi,ci,'campus_'+material)
        for line in part.getvalue().splitlines():
            if line.startswith('o '):continue
            if line.startswith('usemtl '):
                if line==last_material:continue
                last_material=line
            collision.write(line+'\n')
        ci+=8;collision_count+=1
    collision_mesh_count=write_collision(collision,exterior,ci)
    (output/'povo1_campus_collision.obj').write_text(collision.getvalue(),encoding='utf-8')
    physical_groups=write_groups(output,'povo1_campus',physics,exterior.get('collision_meshes',[]))
    metadata=dict(map_name=settings['map_name'],origin=[666250,5103800,370],settings=settings,
                  levels=levels,stair=stair,visual_boxes=len(boxes),collision_boxes=collision_count,
                  breakable_glass=[dict(name=n,lo=list(lo),hi=list(hi),material=material_path(m)) for n,lo,hi,m in glass],
                  auto_doors=doors,elevator=levels[0].get('elevator'),
                  assumptions=settings['assumptions'],
                  inputs={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
                          ('config/povo1_campus.json',settings['interior_source'],'config/povo1_plan_alignment.json')})
    # Keep original source bytes reproducible alongside derived geometry.
    survey_inputs=['config/povo1_survey.json','config/povo2_survey.json',
                   'config/povo_amenities_survey.json','config/povo_wings.json',
                   'data/reference/povo_photos/walk_2026-10-28/manifest.json',
                   'data/reference/povo_photos/walk_2026-10-27/manifest.json']
    for manifest in survey_inputs[-2:]:
        manifest_file=root/manifest
        walk_manifest=json.loads(manifest_file.read_text())
        for source in walk_manifest.get('files',[]):
            relative=source.get('file') or source.get('path')
            if relative:
                photo=manifest_file.parent/relative
                if photo.is_file():survey_inputs.append(photo.relative_to(root).as_posix())
    metadata['inputs'].update({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in survey_inputs})
    metadata['interactions']=levels[0]['interactions']
    metadata['deathmatch_spawns']=spawns
    metadata['physics_surface_groups']=physical_groups
    metadata['inputs']['config/povo_atmosphere.json']=hashlib.sha256((root/'config/povo_atmosphere.json').read_bytes()).hexdigest()

    if levels[0].get('wings'):metadata['wings']=levels[0]['wings']
    if exterior:
        metadata['exterior']=exterior
        metadata['exterior_collision_meshes']=collision_mesh_count
        metadata['inputs'].update(exterior['input_hashes'])
    if settings.get('povo2_connection'):
        metadata['connection']=next(l['connection'] for l in levels if 'connection' in l)
        metadata['inputs'][settings['povo2_connection']]=hashlib.sha256((root/settings['povo2_connection']).read_bytes()).hexdigest()
        if 'povo2' in metadata['connection']:
            metadata['povo2']=metadata['connection']['povo2']
            path=settings['povo2_planimetry']
            metadata['inputs'][path]=hashlib.sha256((root/path).read_bytes()).hexdigest()
    write_winter_assets(root,boxes,metadata,render_obj)
    write_soundevents(root)
    metadata['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in output.glob('povo1_campus*.obj')}
    for relative in ('tools/povo2_internal_stairs.py','tools/povo2_basements.py','tools/povo_pavement.py',
                     'tools/povo_pavement_lighting.py','tools/povo_floor_surfaces.py','tools/povo_render_surfaces.py','config/povo2_internal_dimensions.json',
                     'tools/povo2_minus1_corrections.py','config/povo2_minus1_corrections.json',
                     'data/reference/user_feedback/2026-10-29/povo2_minus1_corrections.png',
                     'data/reference/user_feedback/2026-10-28/povo2_basement_stair_vestibule.jpg'):
        metadata['inputs'][relative]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
    provenance_tmp=output/'provenance.json.tmp'
    provenance_tmp.write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    provenance_tmp.replace(output/'provenance.json')
    materials=root/'cs2/content/trento_povo/materials/trento/povo/campus';materials.mkdir(parents=True,exist_ok=True)
    write_materials(materials, MATERIAL_PREFIX, {n:c for n,c in COLORS.items() if not n.startswith('exterior_')})
    write_exterior_materials(materials/'exterior')
    original=(root/'cs2/content/trento_povo/models/povo/povo_blockout.vmdl').read_text()
    original=original.replace('povo_blockout_collision','povo1_campus_collision').replace('povo_blockout','povo1_campus')
    marker='\t\t\t\t\t\tremaps =\n\t\t\t\t\t\t['
    remaps=''.join('\n                            { from = "campus_'+m+'" to = "'+material_path(m)+'" },' for m in COLORS)
    if marker not in original:raise ValueError('ModelDoc material remap insertion point missing')
    original=original.replace(marker,marker+remaps,1)
    original=modeldoc_groups(original,physical_groups)
    (root/'cs2/content/trento_povo/models/povo/povo1_campus.vmdl').write_text(original,encoding='utf-8')
    room_count=sum(r.get('playable',True) for l in levels
                   for r in [*l['rooms'],*l.get('connection',{}).get('rooms',[])])
    room_count+=sum(len(l.get('rooms',[])) for l in metadata.get('povo2',{}).get('levels',[]))
    print(f"Exported {len(boxes)} visual boxes, {collision_count} collision boxes; {room_count} playable rooms")
    return metadata


def render_obj(boxes,backdrop,*,resolve_surfaces=True):
    """Write indexed attributes before faces, with explicit flat normals.

    Repeating vertices between individual terrain faces makes the native OBJ
    importer allocate excessively. Keep shared terrain vertices and bounded
    material sections, and give walls non-degenerate metre-based UVs.
    """
    try:
        from .povo_render_surfaces import exclusive_faces
    except ImportError:
        from povo_render_surfaces import exclusive_faces
    vertices={};uvs={};normals={};groups={};surfaces=[]
    def index(table,value):
        if value not in table:table[value]=len(table)+1
        return table[value]
    def face(group,material,points,texcoords=None,resolve=True):
        a,b,c=points[:3]
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(x*x for x in normal))
        if length<1e-12:raise ValueError('Degenerate campus triangle '+repr((group,material,points)))
        ni=index(normals,tuple(round(x/length,12) for x in normal))
        if texcoords is None:
            axis=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=axis]
            texcoords=[tuple(p[i]/.6 for i in axes) for p in points]
        if resolve and resolve_surfaces:
            surfaces.append((group,material,points,texcoords))
            return
        refs=[f'{index(vertices,tuple(p))}/{index(uvs,tuple(uv))}/{ni}' for p,uv in zip(points,texcoords)]
        groups.setdefault((group,material),[]).append('f '+' '.join(refs)+'\n')
    for name,material,points,texcoords in backdrop:
        face('backdrop_'+name,material,points,texcoords)
    # Railing collision panels are physics only; see povo_stairs.railing().
    for number,(name,lo,hi,material) in enumerate(sorted((b for b in boxes if '_clip_' not in b[0]),key=lambda b:b[3])):
        part=io.StringIO();write_box(part,name,lo,hi,0,material);points=[]
        for line in part.getvalue().splitlines():
            if line.startswith('v '):
                point=tuple(map(float,line.split()[1:]))
                if 'bridge_finish_brace_' in name:
                    height=2.95
                    distance=(point[1]-lo[1])/(hi[1]-lo[1])
                    point=(point[0],point[1],point[2]+height*(distance if name.endswith('_rise') else 1-distance))
                points.append(point)
            elif line.startswith('f '):
                face(f'campus_section_{number//64}','campus_'+material,[points[int(i)-1] for i in line.split()[1:]])
    for group,material,points,texcoords in exclusive_faces(surfaces):
        face(group,material,points,texcoords,resolve=False)
    stream=io.StringIO();stream.write('# Povo 1 playable campus, local metres\n')
    for label,table in (('v',vertices),('vt',uvs),('vn',normals)):
        for values in table:stream.write(label+' '+' '.join(f'{x:.12g}' for x in values)+'\n')
    stream.write('s off\n')
    for number,((name,material),faces) in enumerate(groups.items()):
        stream.write(f'o {name}_{number}\nusemtl {material}\n');stream.writelines(faces)
    return stream.getvalue()


def collision_boxes(boxes):
    """Keep structural surfaces and simplify the inaccessible gaps in seat rows.

    Individual seat gaps are narrower than the player. Joining those surfaces
    avoids thousands of tiny physics pieces while retaining the row ends,
    desktop, chair height and the open floor beneath the seats.
    """
    result=[];rows={}
    for name,lo,hi,material in boxes:
        if material=='exterior_tree':continue  # foliage above sloping pavements
        if name.startswith('exterior_context_concrete_'):continue
        if name.startswith('exterior_street_end_gate_bar_'):continue
        if name.startswith('exterior_') and any(t in name for t in ('floor_joint','ceiling_joint','_mat','_band_','_sensor','_light_','_rough')):continue
        if any(t in name for t in ('ceiling_light','ceiling_vent','projector','_mullion','_transom','_nosing','_handrail','_finish_')):continue
        if material in ('teaching_board','projection_screen','sign_blue','sign_white'):continue
        if re.search(r'_desk_row_\d+_(support|foot|seat_beam)',name) or '_teaching_desk_leg' in name:continue
        chair=re.match(r'(.*_chair_\d+)_\d+_(seat|back)$',name)
        if chair:
            key=chair[1]+'_'+chair[2]
            if key in rows:
                oldlo,oldhi=rows[key]
                lo=tuple(min(a,b) for a,b in zip(lo,oldlo));hi=tuple(max(a,b) for a,b in zip(hi,oldhi))
            rows[key]=(lo,hi)
        else:result.append((name,lo,hi,material))
    result.extend((name,lo,hi,'seat_wood') for name,(lo,hi) in rows.items())
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args();export()
