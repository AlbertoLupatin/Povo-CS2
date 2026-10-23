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


def classroom_kit(level, room, z, wall_height, settings):
    """Return furniture/finish boxes and an opening for a west-facing pilot room."""
    x0, y0, x1, y1 = room['footprint_local_metres']
    width, depth = x1-x0, y1-y0
    if settings.get('teaching_side') not in ('south', 'north'):
        raise ValueError('Pilot teaching side must be north or south')
    for key in ('aisle_width_metres', 'row_pitch_metres'):
        value = settings.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError('Fit-out dimensions must be finite and positive')
    if width < 6 or depth < 6 or wall_height < 2.8:
        raise ValueError('Pilot kit needs at least a 6 x 6 m room and 2.8 m height')
    aisle, pitch = settings['aisle_width_metres'], settings['row_pitch_metres']
    if not 1.1 <= aisle <= 2 or not 1.05 <= pitch <= 1.8:
        raise ValueError('Fit-out aisle/row spacing is outside the supported pilot range')
    if settings.get('window_side') != 'west':
        raise ValueError('Current photo-guided pilot supports west-facing glazing')
    prefix = f"{level['id']}_room_{room['id']}_"
    boxes = []
    def box(label, lo, hi, material):
        a, b = list(lo), list(hi)
        if settings['teaching_side'] == 'north':
            a[1], b[1] = depth-b[1], depth-a[1]
        minimum = (x0+a[0], y0+a[1], z+a[2])
        maximum = (x0+b[0], y0+b[1], z+b[2])
        if any(not math.isfinite(v) for v in (*minimum, *maximum)) or any(a>=b for a,b in zip(minimum, maximum)):
            raise ValueError('Invalid fit-out box')
        boxes.append((prefix+label, minimum, maximum, material))

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

    # Leave a central aisle and a transverse aisle aligned with the side door.
    # This is a reviewable playable arrangement, not an observed seat count.
    seats = 0
    cross_door = room['door_fraction']*depth
    if settings['teaching_side']=='north':cross_door=depth-cross_door
    row=0;cy=1.75
    while cy+.9 < depth-.65:
        if not (cy+.9 > cross_door-.6 and cy < cross_door+.6):
            for block in range(2):
                start = width/2-aisle/2-3*.58 if block==0 else width/2+aisle/2
                for seat in range(3):
                    cx=start+(seat+.5)*.58;name=f'desk_{row}_{block}_{seat}'
                    box(name+'_top',(cx-.28,cy,.73),(cx+.28,cy+.45,.77),'desk_dark')
                    for ix,dx in enumerate((-.23,.23)):
                        for iy,dy in enumerate((.06,.39)):
                            box(name+f'_leg_{ix}_{iy}',(cx+dx-.017,cy+dy-.017,.014),(cx+dx+.017,cy+dy+.017,.73),'metal_dark')
                    chair=f'chair_{row}_{block}_{seat}'
                    box(chair+'_seat',(cx-.215,cy+.49,.44),(cx+.215,cy+.86,.475),'seat_wood')
                    box(chair+'_back',(cx-.215,cy+.84,.475),(cx+.215,cy+.88,.89),'seat_wood')
                    for ix,dx in enumerate((-.18,.18)):
                        for iy,dy in enumerate((.53,.82)):
                            box(chair+f'_leg_{ix}_{iy}',(cx+dx-.014,cy+dy-.014,.014),(cx+dx+.014,cy+dy+.014,.44),'metal_dark')
                    seats+=1
        row+=1;cy+=pitch

    # Photo P020 establishes the frame/transom style, not these dimensions.
    sill, head = .12, wall_height-.16
    opening=((x0-.20,y0+.45,z+sill),(x0+.20,y1-.45,z+head))
    window_width=depth-.9;bays=max(1,round(window_width/.95))
    box('window_glass',(-.012,.45,sill),(.012,depth-.45,head),'window_glass')
    for i in range(bays+1):
        cy=.45+i*window_width/bays
        box(f'window_mullion_{i}',(-.045,cy-.025,sill),(.045,cy+.025,head),'window_frame')
    for i,cz in enumerate((sill,1.9,head)):
        box(f'window_transom_{i}',(-.045,.425,cz-.025),(.045,depth-.425,cz+.025),'window_frame')
    return boxes, opening, dict(seats=seats,window_bays=bays,
        status='Photo-guided pilot; dimensions, seat count, teaching side and placement provisional',
        teaching_side=settings['teaching_side'],reference_ids=['P020','P021','P022'])


def apply_fitouts(config, levels, boxes, origin):
    settings=config.get('classroom_fitout')
    if settings is None:return boxes
    matching=[(level,room) for level in levels for room in level['rooms']
              if level['id']==settings['level'] and room['id']==settings['room']]
    if len(matching)!=1:raise ValueError('Fit-out must name an existing unique room')
    level,room=matching[0]
    if room['kind']!='classroom':raise ValueError('Pilot kit requires an ordinary classroom')
    if not math.isclose(room['bounds'][1],0,abs_tol=1e-9):
        raise ValueError('West-facing pilot must adjoin the exterior west wall')
    z=level['floor_elevation_metres']-origin[2]
    additions,opening,record=classroom_kit(level,room,z,config['wall_height_metres'],settings)
    result=[]
    for b in boxes:
        result.extend(subtract_box(b,opening) if b[0].startswith(level['id']+'_') and b[3]=='wall' else [b])
    room['fitout']=record
    room['window_opening_local_metres']=opening
    return result+additions
