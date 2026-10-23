"""Editable box-based classroom kit, inferred from user architectural photos.

Source photos establish appearance, not metric dimensions or exact furniture
placement. No source pixels or people are included in generated assets.
"""
import math

COLORS = {
    'floor_wood': (172, 135, 89), 'desk_dark': (49, 55, 55),
    'seat_wood': (143, 98, 54), 'metal_dark': (61, 66, 68),
    'window_frame': (154, 162, 161), 'window_glass': (151, 196, 210),
    'ceiling_panel': (217, 217, 204), 'light_diffuser': (245, 243, 216),
    'teaching_board': (74, 83, 79), 'projection_screen': (234, 234, 224),
}


def subtract_box(box, hole):
    """Subtract a rectangular opening, preserving all solid around its six sides."""
    name, lo, hi, material = box
    a = tuple(max(lo[i], hole[0][i]) for i in range(3))
    b = tuple(min(hi[i], hole[1][i]) for i in range(3))
    if any(a[i] >= b[i] for i in range(3)):
        return [box]
    pieces = []
    lower, upper = list(lo), list(hi)
    for axis in range(3):
        for left, right in ((lower[axis], a[axis]), (b[axis], upper[axis])):
            if left < right:
                minimum, maximum = list(lower), list(upper)
                minimum[axis], maximum[axis] = left, right
                pieces.append((f'{name}_windowcut_{len(pieces)}', tuple(minimum), tuple(maximum), material))
        lower[axis], upper[axis] = a[axis], b[axis]
    return pieces


def classroom_kit(level, room, z, wall_height, wall_thickness, settings):
    """Build continuous desk rows with side aisles and windows opposite the board."""
    x0, y0, x1, y1 = room['footprint_local_metres']
    side=settings.get('teaching_side')
    frames={'south':((x0,y0),(1,0),(0,1),x1-x0,y1-y0),
            'north':((x0,y1),(1,0),(0,-1),x1-x0,y1-y0),
            'east':((x1,y0),(0,1),(-1,0),y1-y0,x1-x0),
            'west':((x0,y0),(0,1),(1,0),y1-y0,x1-x0)}
    if side not in frames:raise ValueError('Unknown teaching side')
    base,cross,back,width,depth=frames[side]
    opposite={'south':'north','north':'south','east':'west','west':'east'}
    if settings.get('window_side')!=opposite[side]:
        raise ValueError('Windows must be behind the seats, opposite the teaching wall')
    for key in ('side_aisle_metres','row_pitch_metres'):
        value=settings.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
            raise ValueError('Fit-out dimensions must be finite and positive')
    if width < 6 or depth < 6 or wall_height < 2.8:
        raise ValueError('Classroom kit needs at least a 6 x 6 m room and 2.8 m height')
    aisle,pitch=settings['side_aisle_metres'],settings['row_pitch_metres']
    if not .85<=aisle<=2 or not 1.05<=pitch<=1.8:
        raise ValueError('Fit-out aisle/row spacing is outside the supported range')
    prefix=f"{level['id']}_room_{room['id']}_"
    boxes=[]
    def point(x,y):return (base[0]+cross[0]*x+back[0]*y,base[1]+cross[1]*x+back[1]*y)
    def bounds(lo,hi):
        corners=[point(x,y) for x in (lo[0],hi[0]) for y in (lo[1],hi[1])]
        return ((min(p[0] for p in corners),min(p[1] for p in corners),z+lo[2]),
                (max(p[0] for p in corners),max(p[1] for p in corners),z+hi[2]))
    def box(label,lo,hi,material):
        minimum,maximum=bounds(lo,hi)
        if any(not math.isfinite(v) for v in (*minimum,*maximum)) or any(a>=b for a,b in zip(minimum,maximum)):
            raise ValueError('Invalid fit-out box')
        boxes.append((prefix+label,minimum,maximum,material))

    box('wood_floor', (.095,.095,.001), (width-.095,depth-.095,.014), 'floor_wood')
    box('ceiling_panel', (.095,.095,wall_height-.065), (width-.095,depth-.095,wall_height), 'ceiling_panel')
    # Recessed lighting: pale diffuser, dark rim and a visible louvre grid.
    for ix in range(3):
        for iy in range(3):
            cx,cy=width*(ix+1)/4,depth*(iy+1)/4
            name=f'ceiling_light_{ix}_{iy}'
            box(name+'_rim',(cx-.31,cy-.31,wall_height-.105),(cx+.31,cy+.31,wall_height-.065),'metal_dark')
            box(name+'_diffuser',(cx-.28,cy-.28,wall_height-.108),(cx+.28,cy+.28,wall_height-.105),'light_diffuser')
            for line in range(1,5):
                t=-.28+line*.112
                box(name+f'_grid_x{line}',(cx+t-.006,cy-.28,wall_height-.114),(cx+t+.006,cy+.28,wall_height-.108),'window_frame')
                box(name+f'_grid_y{line}',(cx-.28,cy+t-.006,wall_height-.114),(cx+.28,cy+t+.006,wall_height-.108),'window_frame')
    for index,cx in enumerate((width*.375,width*.625)):
        cy=depth*.5
        box(f'ceiling_vent_{index}',(cx-.28,cy-.28,wall_height-.11),(cx+.28,cy+.28,wall_height-.065),'window_frame')
        for line in range(6):
            t=-.23+line*.09
            box(f'ceiling_vent_{index}_slat{line}',(cx+t-.014,cy-.22,wall_height-.118),(cx+t+.014,cy+.22,wall_height-.11),'metal_dark')
    box('ceiling_projector', (width/2-.16,1.25,wall_height-.38), (width/2+.16,1.49,wall_height-.22), 'projection_screen')
    box('ceiling_projector_mount', (width/2-.025,1.34,wall_height-.22), (width/2+.025,1.39,wall_height-.065), 'metal_dark')
    box('board',(width/2-2,.10,.95),(width/2+2,.15,2.35),'teaching_board')
    box('screen',(width/2-1,.16,1.25),(width/2+1,.19,2.55),'projection_screen')
    box('screen_case',(width/2-1.08,.13,2.55),(width/2+1.08,.23,2.63),'window_frame')
    box('teaching_desk_top',(width/2-.7,.45,.74),(width/2+.7,1.0,.79),'desk_dark')
    for index,dx in enumerate((-.61,.61)):
        box(f'teaching_desk_leg{index}',(width/2+dx-.025,.5,.014),(width/2+dx+.025,.95,.74),'metal_dark')

    # User-confirmed layout: a continuous desktop across each row, with a
    # clear metre measured from each finished wall face. No centre aisle.
    inner=wall_thickness/2
    start,end=inner+aisle,width-inner-aisle
    seat_count=max(1,int((end-start)/.58))
    seat_pitch=(end-start)/seat_count
    door_side=room['door_side'];f=room['door_fraction']
    door_world={'u_min':(x0+(x1-x0)*f,y0),'u_max':(x0+(x1-x0)*f,y1),
                'v_min':(x0,y0+(y1-y0)*f),'v_max':(x1,y0+(y1-y0)*f)}[door_side]
    door_depth=(door_world[0]-base[0])*back[0]+(door_world[1]-base[1])*back[1]
    door_cross=(door_world[0]-base[0])*cross[0]+(door_world[1]-base[1])*cross[1]
    if door_depth<.05 and abs(door_cross-width/2)<2+room['door_width_metres']/2:
        raise ValueError('Teaching board overlaps the front-wall doorway; refine its plan position')
    side_door=.05<door_depth<depth-.05
    rows=[];seats=0;row=0;cy=1.75
    while cy+.9 < depth-.65:
        if not side_door or not (cy+.9>door_depth-.6 and cy<door_depth+.6):
            name=f'desk_row_{row}'
            box(name+'_top',(start,cy,.73),(end,cy+.45,.77),'desk_dark')
            rows.append(dict(id=row,bounds_local_metres=bounds((start,cy,.73),(end,cy+.45,.77))))
            for seat in range(seat_count):
                cx=start+(seat+.5)*seat_pitch
                for ix,dx in enumerate((-.23,.23)):
                    for iy,dy in enumerate((.06,.39)):
                        box(name+f'_leg_{seat}_{ix}_{iy}',(cx+dx-.017,cy+dy-.017,.014),(cx+dx+.017,cy+dy+.017,.73),'metal_dark')
                chair=f'chair_{row}_{seat}'
                box(chair+'_seat',(cx-.215,cy+.49,.44),(cx+.215,cy+.86,.475),'seat_wood')
                box(chair+'_back',(cx-.215,cy+.84,.475),(cx+.215,cy+.88,.89),'seat_wood')
                for ix,dx in enumerate((-.18,.18)):
                    for iy,dy in enumerate((.53,.82)):
                        box(chair+f'_leg_{ix}_{iy}',(cx+dx-.014,cy+dy-.014,.014),(cx+dx+.014,cy+dy+.014,.44),'metal_dark')
                seats+=1
        row+=1;cy+=pitch
    sill,head=.12,wall_height-.16
    opening=bounds((.45,depth-.20,sill),(width-.45,depth+.20,head))
    window_width=width-.9;bays=max(1,round(window_width/.95))
    box('window_glass',(.45,depth-.012,sill),(width-.45,depth+.012,head),'window_glass')
    for i in range(bays+1):
        cx=.45+i*window_width/bays
        box(f'window_mullion_{i}',(cx-.025,depth-.045,sill),(cx+.025,depth+.045,head),'window_frame')
    for i,cz in enumerate((sill,1.9,head)):
        box(f'window_transom_{i}',(.425,depth-.045,cz-.025),(width-.425,depth+.045,cz+.025),'window_frame')
    return boxes,opening,dict(seats=seats,window_bays=bays,rows=rows,
        status='Continuous rows, 1 m side clearances and rear windows confirmed by user; other dimensions and seat count estimated',
        teaching_side=side,window_side=settings['window_side'],side_aisle_metres=aisle,
        reference_ids=settings['reference_ids'],location_status=settings['location_status'],
        audit_points_local_metres=[point(inner+aisle/2,depth-.75),point(width-inner-aisle/2,depth-.75)])


def apply_fitouts(config, levels, boxes, origin):
    settings_list=config.get('classroom_fitouts',[])
    if not isinstance(settings_list,list):raise ValueError('classroom_fitouts must be a list')
    result=list(boxes);used=set()
    exterior={'west':(1,0),'east':(3,1),'south':(0,0),'north':(2,1)}
    for settings in settings_list:
        references=settings.get('reference_ids')
        if not isinstance(references,list) or not references or any(not isinstance(r,str) for r in references) or not set(references)<=set(config.get('photo_reference',{}).get('ids',[])):
            raise ValueError('Fit-out references must be registered photo IDs')
        key=(settings['level'],settings['room'])
        if key in used:raise ValueError('Duplicate classroom fit-out target')
        used.add(key)
        matching=[(level,room) for level in levels for room in level['rooms'] if (level['id'],room['id'])==key]
        if len(matching)!=1:raise ValueError('Fit-out must name an existing unique room')
        level,room=matching[0]
        if room['kind']!='classroom':raise ValueError('Kit requires an ordinary classroom')
        if settings.get('window_side') not in exterior:raise ValueError('Unknown window side')
        index,edge=exterior[settings['window_side']]
        if not math.isclose(room['bounds'][index],edge,abs_tol=1e-9):
            raise ValueError('Window wall must adjoin the exterior building perimeter')
        z=level['floor_elevation_metres']-origin[2]
        additions,opening,record=classroom_kit(level,room,z,config['wall_height_metres'],config['wall_thickness_metres'],settings)
        rebuilt=[]
        for b in result:
            rebuilt.extend(subtract_box(b,opening) if b[0].startswith(level['id']+'_') and b[3]=='wall' else [b])
        room['fitout']=record;room['window_opening_local_metres']=opening
        result=rebuilt+additions
    return result
