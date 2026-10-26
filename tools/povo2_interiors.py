"""Photo-guided Povo 2 furniture; dimensions and seat counts are estimates."""
try:
    from .povo_room_fitout import classroom_kit, subtract_box
except ImportError:
    from povo_room_fitout import classroom_kit, subtract_box


def mesh_intersects_box(mesh, hole):
    """Exact face clipping avoids treating sloped road bounds as solid boxes."""
    for face in mesh['faces']:
        polygon=[list(mesh['vertices'][i]) for i in face]
        for axis in range(3):
            for bound,sign in ((hole[0][axis],1),(hole[1][axis],-1)):
                clipped=[]
                if not polygon:break
                for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                    da=(a[axis]-bound)*sign;db=(b[axis]-bound)*sign
                    if da>=0:clipped.append(a)
                    if (da>=0)!=(db>=0):
                        t=da/(da-db)
                        clipped.append([a[k]+t*(b[k]-a[k]) for k in range(3)])
                polygon=clipped
        if polygon:return True
    # A box entirely inside a convex prism need not intersect any face.
    centre=[sum(v[i] for v in mesh['vertices'])/len(mesh['vertices']) for i in range(3)]
    point=[(hole[0][i]+hole[1][i])/2 for i in range(3)]
    for face in mesh['faces']:
        a,b,c=[mesh['vertices'][i] for i in face[:3]]
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        inside=sum(normal[i]*(centre[i]-a[i]) for i in range(3))
        test=sum(normal[i]*(point[i]-a[i]) for i in range(3))
        if inside*test<0:return False
    return True


def furnish_b_rooms(boxes, ground, wall_height):
    """Photos 16–18: tiled B11x rooms, dark desks, beech seats and end glazing."""
    result = list(boxes)
    z = ground['z']
    for room in ground['rooms']:
        settings = dict(teaching_side='north', window_side=None,
                        side_aisle_metres=1.1, row_pitch_metres=1.35, first_row_metres=2.1,
                        reference_ids=['P105', 'P106', 'P107'],
                        location_status='26 October photos 16–18; repeated B11x family')
        furniture, _, record = classroom_kit(ground, room, z, wall_height, .2, settings)
        # These rooms have tile, not the kit's default bamboo floor. Retain the
        # existing blackboard/tray so the documented teaching orientation stays.
        result.extend(b for b in furniture if not b[0].endswith(('_wood_floor', '_board')))
        a,b,c,d = room['bounds']
        opening = ((c-.25,b+.6,z+.15),(c+.25,d-.6,z+wall_height-.18))
        result = [part for box in result for part in
                  (subtract_box(box, opening) if box[3] == 'wall' else [box])]
        prefix = 'p2_ground_'+room['id']
        result.append((prefix+'_window_glass',(c-.015,b+.6,z+.15),
                       (c+.015,d-.6,z+wall_height-.18),'window_glass'))
        bays = max(1, round((d-b-1.2)/1.1))
        for i in range(bays+1):
            y=b+.6+(d-b-1.2)*i/bays
            result.append((prefix+f'_window_mullion_{i}',(c-.055,y-.025,z+.15),
                           (c+.055,y+.025,z+wall_height-.18),'window_frame'))
        for i,h in enumerate((.15,1.9,wall_height-.18)):
            result.append((prefix+f'_window_transom_{i}',(c-.055,b+.575,z+h-.025),
                           (c+.055,d-.575,z+h+.025),'window_frame'))
        record.update(window_side='east', window_bays=bays, floor_material='floor_p2_tile',
                      status='Photo-guided B11x fit-out; furniture counts and dimensions estimated')
        room['fitout'] = record
        # The old empty-room centre is now occupied by rows. Test usable front
        # space and both full-depth side aisles instead, as in the Povo 1 kit.
        ground['audit_stations'] = [s for s in ground['audit_stations']
                                    if s['id'] != room['id']+'_centre']
        ground['audit_stations'].append(dict(id=room['id']+'_teaching',point=[(a+c)/2,d-1.55]))
        for i,point in enumerate(record['audit_points_local_metres']):
            ground['audit_stations'].append(dict(id=room['id']+f'_aisle_{i}',point=point))
    return result


def extend_layout(boxes, levels, root, wall_height):
    """Expand the integrated campus without relocating its proven stairs/lifts."""
    import json
    cfg = json.loads((root/'config/povo2_additions.json').read_text())
    spec = levels[1]['connection']['povo2']
    ground = next(l for l in spec['levels'] if l['floor']==0)
    basement = next(l for l in spec['levels'] if l['floor']==-1)
    result = [box for box in boxes if not box[0].startswith('exterior_povo2_terrace_guard_')]
    ext=levels[0].get('exterior',{})
    for key in ('meshes','collision_meshes'):
        ext[key]=[m for m in ext.get(key,[]) if not m['name'].startswith('exterior_povo2_terrace_guard_')]
    # B111--B114 end at their own glazed facade. Remove the shell's obsolete
    # 2.4 m tail behind them, including the opaque wall visible through B112.
    tail=((10,35.5,ground['z']-.3),(12.5,71.6,ground['z']+wall_height+.02))
    result=[p for box in result for p in
            (subtract_box(box,tail) if box[0].startswith('p2_ground_')
             and box[3] in ('wall','ceiling_panel','floor_p2_tile') else [box])]

    def add(name, lo, hi, material='wall'):
        if any(a>=b for a,b in zip(lo,hi)):
            raise ValueError('Invalid addition: '+name)
        result.append((name,tuple(lo),tuple(hi),material))

    def clear(rect, z, ceiling_height=None):
        nonlocal result
        a,b,c,d = rect
        ceiling_height=wall_height if ceiling_height is None else ceiling_height
        hole=((a-.12,b-.12,z-.25),(c+.12,d+.12,z+ceiling_height+.02))
        # Hollow overlapping scenery; never remove the existing interior/core.
        result=[p for box in result for p in
                (subtract_box(box,hole) if box[0].startswith('exterior_') else [box])]
        ext=levels[0].get('exterior',{})
        # Source collision meshes (roads/terrain) must also leave these volumes.
        # Retain a mesh if it has no 3-D overlap. Boxes are carved separately.
        converted=set()
        for key in ('meshes','collision_meshes'):
            kept=[]
            for mesh in ext.get(key,[]):
                lo=[min(v[i] for v in mesh['vertices']) for i in range(3)]
                hi=[max(v[i] for v in mesh['vertices']) for i in range(3)]
                if all(lo[i]<hole[1][i] and hi[i]>hole[0][i] for i in range(3)):
                    if len(mesh['vertices'])!=8 or not all(all(abs(v[i]-lo[i])<1e-7 or abs(v[i]-hi[i])<1e-7 for i in range(3)) for v in mesh['vertices']):
                        if mesh_intersects_box(mesh,hole):
                            raise ValueError('Addition overlaps non-box exterior mesh '+mesh['name'])
                        kept.append(mesh)
                        continue
                    if mesh['name'] not in converted:
                        result.extend(subtract_box((mesh['name'],tuple(lo),tuple(hi),mesh['material']),hole))
                        converted.add(mesh['name'])
                    continue
                kept.append(mesh)
            ext[key]=kept

    def cut(lo,hi,materials=('wall','window_frame')):
        nonlocal result
        result=[p for box in result for p in
                (subtract_box(box,(lo,hi)) if box[3] in materials else [box])]

    def shell(name,rect,z,floor='floor_p2_tile',height=None):
        height=wall_height if height is None else height
        clear(rect,z,height)
        a,b,c,d=rect
        add(name+'_floor',(a,b,z-.22),(c,d,z),floor)
        add(name+'_ceiling',(a,b,z+height-.07),(c,d,z+height),'ceiling_panel')
        for side,lo,hi in [('west',(a-.1,b,z),(a+.1,d,z+height)),
                           ('east',(c-.1,b,z),(c+.1,d,z+height)),
                           ('south',(a,b-.1,z),(c,b+.1,z+height)),
                           ('north',(a,d-.1,z),(c,d+.1,z+height))]:
            add(name+'_wall_'+side,lo,hi)
        spec['lights'].extend([[x,y,z+height-.3] for x in (a+(c-a)*.3,a+(c-a)*.7)
                              for y in (b+(d-b)*.3,b+(d-b)*.7)])

    def north_door(name,x,y,z,width=1.5):
        cut((x-width/2,y-.25,z-.01),(x+width/2,y+.25,z+2.25))
        for i,xx in enumerate((x-width/2-.04,x+width/2)):
            add(name+f'_jamb_{i}',(xx,y-.12,z),(xx+.04,y+.12,z+2.3),'window_frame')
        add(name+'_head',(x-width/2-.04,y-.12,z+2.25),(x+width/2+.04,y+.12,z+2.3),'window_frame')

    def station(level,name,x,y):
        level['audit_stations'].append(dict(id=name,point=[x,y]))

    z=ground['z']; corridor=cfg['ground_corridor']
    # The approach passes the stairs and separate ladder entrance BEFORE the
    # east/west classroom corridor. Remove the old enclosed empty vestibule.
    result=[box for box in result if not box[0].startswith((
        'p2_ground_reception_wall_extension','p2_ground_stair_access_return_',
        'p2_ground_locker_','p2_ground_locker_handle_'))]
    shell('p2_ground_left_approach',cfg['ground_approach'],z)
    shell('p2_ground_left_extension',corridor,z)
    clear((16.6,11,25.5,29.5),z)
    landing=('p2_ground_stair_hall_floor',(16.5,11,z-.22),(25.5,29.5,z),'floor_p2_tile')
    shaft=levels[1]['connection']['lift']['shaft']
    result.extend(subtract_box(landing,((shaft[0],shaft[1],z-.3),(shaft[2],shaft[3],z+.01))))
    # Hollow the existing hall's internal boundaries without clipping the core
    # or the relocated lift. Retain a sealed outside perimeter.
    for lo,hi in [((16.65,14.05,z-.01),(25.4,29.6,z+2.3)),
                  ((22.35,10.75,z-.01),(25.65,11.25,z+2.3))]:
        result=[p for box in result for p in
                (subtract_box(box,(lo,hi)) if box[3] in ('wall','window_frame')
                 and not box[0].startswith('p2_lift_') else [box])]
    # Direct stair entrance: retain the actual core door, remove the first
    # black door and its empty vestibule completely.
    cut((16.25,21.175,z-.01),(16.75,22.825,z+2.2))
    for old_station in ground['audit_stations']:
        if old_station['id']=='left_corridor':old_station['point']=[24,25.5]
    station(ground,'left_extension_entry',24,28.8)
    station(ground,'left_extension_junction',24,9.5)
    station(ground,'left_extension_pc_branch',29.5,9.5)
    station(ground,'left_extension_end',3,9.5)
    station(ground,'reception_stair_door',17.8,22)
    spec['additions_stair_entry']=cfg['stair_entry']
    for record in cfg['ground_rooms']:
        room=dict(record); a,b,c,d=room['bounds']; name='p2_ground_'+room['id']
        shell(name,room['bounds'],z,'floor_wood')
        door=room['door_x']
        north_door(name+'_entry',door,d,z)
        room.update(footprint_local_metres=room['bounds'],door_side='u_max',
                    door_fraction=(door-a)/(c-a),door_width_metres=1.5,
                    playable=True,board_wall='north',sign_offset_metres=.16)
        # Room kit faces away from full-height south-facing facade glazing.
        settings=dict(teaching_side='north',window_side=None,side_aisle_metres=1.1,
                      row_pitch_metres=1.4,first_row_metres=2.1,
                      reference_ids=['P093','P094','P095','P096'],
                      location_status='26 October left-corridor rooms; provisional labels')
        # Door is offset to the side so it does not intersect the board.
        if room['kind']=='computer':
            settings.update(window_side=None,reference_ids=['P097'])
        furniture,opening,fitout=classroom_kit(ground,room,z,wall_height,.2,settings)
        if opening:cut(*opening,materials=('wall',))
        if room['kind']=='classroom':
            import re
            raised=[]
            tiers={}
            for boxname,lo,hi,mat in furniture:
                match=re.search(r'_(?:desk_row|chair)_(\d+)_',boxname)
                rise=int(match[1])*.12 if match else 0
                if match:
                    tiers.setdefault(int(match[1]),[]).append((lo,hi))
                raised.append((boxname,(lo[0],lo[1],lo[2]+rise),(hi[0],hi[1],hi[2]+rise),mat))
            furniture=raised
            for row,parts in tiers.items():
                rise=row*.12
                if not rise:continue
                lo=[min(p[0][i] for p in parts) for i in range(2)]
                hi=[max(p[1][i] for p in parts) for i in range(2)]
                add(name+f'_tier_{row}',(lo[0]-.08,lo[1]-.05,z),(hi[0]+.08,hi[1]+.05,z+rise),'floor_wood')
            fitout['riser_metres']=.12
            fitout['status']='Photo-guided bamboo floor and raked seating; metric dimensions estimated'
        result.extend(furniture)
        add(name+'_sign_plaque',(door-.63,d+.105,z+2.28),
            (door+.63,d+.12,z+2.6),'sign_blue')
        cut((a+.5,b-.25,z+.15),(c-.5,b+.25,z+wall_height-.18),materials=('wall',))
        add(name+'_window_glass',(a+.5,b-.015,z+.15),(c-.5,b+.015,z+wall_height-.18),'window_glass')
        for i in range(int(c-a)):
            x=a+.5+i
            if x<c-.45:
                add(name+f'_window_mullion_{i}',(x-.025,b-.05,z+.15),(x+.025,b+.05,z+wall_height-.18),'window_frame')
        fitout['window_side']='south'
        room['fitout']=fitout
        ground.setdefault('rooms',[]).append(room)
        if spec['ground']['rooms'] is not ground['rooms']:spec['ground']['rooms'].append(room)
        station(ground,room['id']+'_door',door,d)
        for i,p in enumerate(fitout['audit_points_local_metres']):
            station(ground,room['id']+f'_aisle_{i}',*p)
        if room['kind']=='computer':
            # Reuse desk rows, add blank monitors/keyboards: no photographed text.
            for i,row in enumerate(fitout['rows']):
                lo,hi=row['bounds_local_metres']
                for j in range(max(1,int((hi[0]-lo[0])/1.2))):
                    x=lo[0]+.6+j*1.2;y=(lo[1]+hi[1])/2
                    add(name+f'_monitor_{i}_{j}',(x-.22,y-.035,z+.82),(x+.22,y+.035,z+1.15),'desk_dark')
                    add(name+f'_monitor_stand_{i}_{j}',(x-.025,y-.025,z+.77),(x+.025,y+.025,z+.85),'metal_dark')
            fitout['furniture']=['computer desks','blank monitors','chairs']

    # Photo 14–15 lobby, followed by the authorized temporary aula magna.
    lobby=cfg['aula_lobby']; hall=cfg['aula_magna']
    shell('p2_ground_aula_lobby',lobby,z)
    shell('p2_ground_aula_magna',hall,z)
    north_door('p2_ground_aula_lobby_entry',25,71.5,z,2.2)
    # Approved playtest correction: aula on the opposite (west) side of the
    # intermediate area. Glass belongs after the tables, solid wall by aula.
    entry_y=(lobby[1]+lobby[3])/2
    cut((lobby[0]-.25,entry_y-1.1,z-.01),(lobby[0]+.25,entry_y+1.1,z+2.25))
    # Remove the opaque end wall across the table hall, including the old
    # exterior shell; preserve its central passage and the room-end boundary.
    cut((lobby[0]+.1,lobby[1]-.25,z+.1),(lobby[2]-.1,lobby[1]+.25,z+wall_height-.15),materials=('wall',))
    for i,(x0,x1) in enumerate(((lobby[0]+.1,23.9),(26.1,lobby[2]-.1))):
        add(f'p2_ground_aula_lobby_glass_{i}',(x0,lobby[1]-.02,z+.1),(x1,lobby[1]+.02,z+wall_height-.15),'window_glass')
        for j,h in enumerate((.1,1.9,wall_height-.15)):
            add(f'p2_ground_aula_lobby_transom_{i}_{j}',(x0,lobby[1]-.055,z+h-.025),(x1,lobby[1]+.055,z+h+.025),'window_frame')
        import math
        for j in range(math.ceil((x1-x0)/1.3)+1):
            x=min(x1,x0+j*1.3)
            add(f'p2_ground_aula_lobby_mullion_{i}_{j}',(x-.025,lobby[1]-.055,z+.1),(x+.025,lobby[1]+.055,z+wall_height-.15),'window_frame')
    for i,x in enumerate((14,15.3,16.6,17.9)):
        add(f'p2_ground_aula_lobby_locker_{i}',(x,72,z),(x+1.15,72.65,z+1.85),'seat_wood')
    a,b,c,d=hall;centre=(b+d)/2
    add('p2_ground_aula_stage',(c-2.5,b+7,z),(c-.6,d-2,z+.18),'floor_wood')
    add('p2_ground_aula_screen',(c-.25,b+8,z+1),(c-.2,d-3,z+3),'projection_screen')
    # Two seating blocks with a central walking aisle; terraces stay modest
    # enough to preserve standing headroom below the existing upper envelope.
    aula_path=[]
    for row in range(7):
        x=c-4-row*2.1;rise=row*.12
        for block,(y0,y1) in enumerate(((b+1.3,centre-1.3),(centre+1.3,d-1.3))):
            if rise:add(f'p2_ground_aula_tier_{row}_{block}',(x,y0,z),(x+1.7,y1,z+rise),'floor_p2_tile')
            for seat in range(int((y1-y0)/.65)):
                y=y0+.4+seat*.65
                add(f'p2_ground_aula_chair_{row}_{block}_{seat}',(x+.7,y-.23,z+rise+.43),(x+1.12,y+.23,z+rise+.49),'seat_wood')
                add(f'p2_ground_aula_back_{row}_{block}_{seat}',(x+.69,y-.23,z+rise+.49),(x+.75,y+.23,z+rise+.98),'desk_dark')
        aula_path.append([x+.8,centre,z])
    station(ground,'aula_lobby',25,75)
    station(ground,'aula_entry',lobby[0]-1,entry_y)
    station(ground,'aula_rear',a+1.5,centre)
    for i,p in enumerate(aula_path):station(ground,f'aula_centre_aisle_{i}',*p[:2])
    spec['additions']=dict(config=cfg,ground_areas=[cfg['ground_approach'],corridor,lobby,hall],
                           temporary_aula=True,aula_path=aula_path,aula_faces='east / entrance')

    # CIBIO branch: two playable offices on the left; small offices stay shut.
    z=basement['z']; corridor=cfg['cibio_corridor']
    # The stair exit faces east: right is south; a SECOND right heads west.
    result=[box for box in result if not box[0].startswith('p2_basement_cross_corridor_')]
    spec['basement']['cross_corridor']=corridor
    for station_record in basement['audit_stations']:
        if station_record['id']=='cross_corridor':station_record['point']=[8,-5]
        if station_record['id']=='cross_corridor_end':station_record['point']=[-3,-5]
    shell('p2_basement_cibio_corridor',corridor,z,height=2.65)
    cut((16.2,-5.9,z-.01),(16.8,-4.1,z+2.25))
    cut((17.2,-3.8,z-.01),(19.2,-3.2,z+2.25))
    for i,(y0,y1) in enumerate(((-6.4,-5.9),(-4.1,-3.6))):
        add(f'p2_basement_cibio_entry_glass_{i}',(16.48,y0,z),(16.52,y1,z+2.3),'window_glass')
    spec['basement']['cibio_corridor']=corridor
    for i,rect in enumerate(cfg['cibio_offices']):
        a,b,c,d=rect;name=f'p2_basement_cibio_office_{i}'
        shell(name,rect,z,height=2.65)
        north_door(name+'_door',a+1.5,d,z)
        # Ordinary neutral office desks, monitor and storage; estimated fit-out.
        for j,x in enumerate((a+2,c-2)):
            add(name+f'_desk_{j}',(x-.7,b+2,z+.72),(x+.7,b+2.75,z+.78),'desk_dark')
            for dx in (-.6,.55):
                add(name+f'_desk_leg_{j}_{dx}',(x+dx,b+2.1,z),(x+dx+.05,b+2.65,z+.72),'metal_dark')
            add(name+f'_monitor_{j}',(x-.22,b+2.1,z+.8),(x+.22,b+2.16,z+1.15),'desk_dark')
            add(name+f'_chair_{j}',(x-.23,b+3,z+.43),(x+.23,b+3.45,z+.49),'seat_wood')
            add(name+f'_chair_back_{j}',(x-.23,b+3.4,z+.49),(x+.23,b+3.46,z+.98),'desk_dark')
        basement.setdefault('rooms',[]).append(dict(id=f'cibio_office_{i}',label=f'CIBIO / OFFICE {i+1}',
            bounds=rect,footprint_local_metres=rect,door_side='u_max',door_fraction=1.5/(c-a),
            door_width_metres=1.5,playable=True,sign_offset_metres=.16))
        add(name+'_sign_plaque',(a+.87,d+.105,z+2.28),(a+2.13,d+.12,z+2.6),'sign_blue')
        station(basement,f'cibio_office_{i}_door',a+1.5,d)
        station(basement,f'cibio_office_{i}_inside',(a+c)/2,d-1.2)
        spec['basement'][f'cibio_office_{i}']=rect
    # Decorative closed black doors retain solid walls behind them.
    for i,x in enumerate((-3,0,3,6,9,12)):
        add(f'p2_basement_cibio_closed_office_{i}',(x,-3.55,z),(x+.95,-3.51,z+2.15),'door_black')
    station(basement,'cibio_entry',15,-5)
    station(basement,'cibio_end',-3,-5)
    spec['additions']['basement_areas']=[corridor,*cfg['cibio_offices']]
    exit_cfg=cfg['basement_exit'];z=basement['z'];yard_z=exit_cfg['yard_z']
    shell('p2_basement_left_locker',exit_cfg['locker_corridor'],z)
    shell('p2_basement_left_return',exit_cfg['return_corridor'],z)
    # Open the existing north end beyond the core and the right-angle junction.
    north_door('p2_basement_left_entry',18.6,26,z,1.6)
    cut((17.75,25.7,z-.01),(19.45,26.85,z+2.25))
    cut((17.9,26.1,z-.01),(20.3,28.9,z+2.25))
    for i,y in enumerate((27,28)):
        add(f'p2_basement_left_locker_{i}',(16.65,y,z),(17.25,y+.8,z+1.85),'seat_wood')
    for i,x in enumerate(range(21,44,2)):
        add(f'p2_basement_return_locker_{i}',(x,28.25,z),(x+1.7,28.85,z+1.85),'seat_wood')
        add(f'p2_basement_return_locker_handle_{i}',(x+1.45,28.21,z+.8),(x+1.5,28.25,z+1.1),'window_frame')
    add('p2_basement_return_orange_band',(20,28.9,z+2),(48.5,28.92,z+2.18),'canteen_orange')
    # Two open push-door portals: corridor/stair and stair/yard.
    for i,x in enumerate((49,50.5)):
        cut((x-.25,26.65,z-.01),(x+.25,28.35,z+2.8))
        for j,y in enumerate((26.65,28.35)):
            add(f'p2_basement_exit_door_{i}_leaf_{j}',(x-.6,y-.03,z+.02),(x,y+.03,z+2.2),'door_black')
            add(f'p2_basement_exit_door_{i}_pushbar_{j}',(x-.5,y-.06,z+1),(x-.1,y+.06,z+1.05),'door_pushbar')
    clear(exit_cfg['inside_stair'],z)
    indoor=[]
    for i in range(5):
        top=z+(yard_z-z)*(i+1)/5;x=49+i*.3
        add(f'p2_basement_exit_step_{i}',(x,26,z-.2),(x+.3,29,top),'floor_p2_tile')
        indoor.append([x+.15,27.5,top])
    add('p2_basement_exit_stair_ceiling',(49,26,z+wall_height-.07),(50.5,29,z+wall_height),'ceiling_panel')
    # Excavate only the front-side depression, retaining the outer pavement
    # strip used by the already validated Povo 1 -> Povo 2 walking route.
    a,b,c,d=exit_cfg['yard']
    clear((a,b,c,d),yard_z)
    add('p2_yard_floor',(a,b,yard_z-.2),(c,d,yard_z),'floor_p2_tile')
    add('p2_yard_lawn',(51.5,11,yard_z),(53,19,yard_z+.025),'floor_yard_grass')
    for side,lo,hi in [('south',(a,b-.1,yard_z),(c,b+.1,4)),
                       ('east',(c-.1,b,yard_z),(c+.1,d,4)),
                       ('north',(a,d-.1,yard_z),(c,d+.1,4))]:
        add('p2_yard_retaining_'+side,lo,hi,'wall')
    # West wall borders the basement, with its one exit doorway left open.
    add('p2_yard_retaining_west',(a-.1,b,yard_z),(a+.1,26.65,4),'wall')
    add('p2_yard_retaining_west_north',(a-.1,28.35,yard_z),(a+.1,d,4),'wall')
    x0,y0,x1,y1=exit_cfg['steel_stair'];outdoor=[];street=exit_cfg['street_z']
    for i in range(15):
        top=yard_z+(street-yard_z)*(i+1)/15;x=x0+i*.3
        add(f'p2_yard_stair_step_{i}',(x,y0,top-.18),(x+.3,y1,top),'floor_p2_tile')
        outdoor.append([x+.15,(y0+y1)/2,top])
    # Slender metal rails and posts; collision clips use the shared rail kit.
    try:
        from .povo_stairs import railing
    except ImportError:
        from povo_stairs import railing
    rails=[]
    for y in (y0+.03,y1-.03):
        railing(add,rails,'p2_yard_stair_'+str(y),(x0,y,yard_z+.18),(x1,y,street))
    spec['stairs']['rails'].extend(rails)
    add('p2_yard_stair_top_landing',(x1,y0-.2,street-.2),(58,y1+.2,street),'floor_p2_tile')
    for y in (y0-.15,y1+.15):
        add('p2_yard_landing_guard_'+str(y),(x1,y,street),(56.65,y+.04,street+1),'metal_dark')
    # Fall protection along the retained outer street strip.
    add('p2_yard_pavement_guard',(56.35,10,street),(56.41,24.5,street+1.05),'metal_dark')
    station(basement,'left_exit_start',18.6,27.5)
    station(basement,'locker_return',22,27.1)
    station(basement,'exit_stair_approach',48,27.1)
    spec['basement']['left_locker']=exit_cfg['locker_corridor']
    spec['basement']['left_return']=exit_cfg['return_corridor']
    spec['basement']['yard']=exit_cfg['yard']
    spec['lights'].extend([[52,18,yard_z+2.6],[52,27,yard_z+2.6]])
    spec['additions']['yard']=dict(bounds=exit_cfg['yard'],z=yard_z,
        audit_stations=[dict(id='yard_beside_exit',point=[51.3,25.5]),
                        dict(id='yard_side',point=[51.3,19.5]),
                        dict(id='yard_south',point=[54.3,19.2])],
        indoor_path=indoor,outdoor_path=outdoor,
        stair_axis=0,top_path=[[55.5,27.5,street],[57.5,27.5,street]])
    import hashlib
    ext=levels[0].get('exterior',{})
    ext.setdefault('input_hashes',{})['config/povo2_additions.json']=hashlib.sha256((root/'config/povo2_additions.json').read_bytes()).hexdigest()
    return result
