"""Build the accepted basement layout once, in final campus coordinates.

The earlier photo/sketch passes still supply the approved footprints and room
records. Their lower-floor shells are replaced here rather than accumulating
rotated shaft cuts, old ceilings and disconnected wall fragments.
"""
from collections import defaultdict
import re

try:
    from .povo_room_fitout import subtract_box
except ImportError:
    from povo_room_fitout import subtract_box


def union_rectangles(rectangles):
    """Disjoint rectangles and merged perimeter segments of a rectangle union."""
    xs=sorted({r[i] for r in rectangles for i in (0,2)})
    ys=sorted({r[i] for r in rectangles for i in (1,3)})
    cells={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1)
           if any(a<=(xs[i]+xs[i+1])/2<=c and b<=(ys[j]+ys[j+1])/2<=d
                  for a,b,c,d in rectangles)}
    spans=[];edges=defaultdict(list)
    # Merge horizontal cells into strips; floors have no coincident faces.
    for j in range(len(ys)-1):
        start=None
        for i in range(len(xs)):
            if (i,j) in cells:
                if start is None:start=i
            elif start is not None:
                spans.append((xs[start],ys[j],xs[i],ys[j+1]));start=None
    for i,j in cells:
        for axis,fixed,lo,hi,neighbor in (
            (0,xs[i],ys[j],ys[j+1],(i-1,j)),
            (0,xs[i+1],ys[j],ys[j+1],(i+1,j)),
            (1,ys[j],xs[i],xs[i+1],(i,j-1)),
            (1,ys[j+1],xs[i],xs[i+1],(i,j+1))):
            if neighbor not in cells:edges[axis,fixed].append((lo,hi))
    merged=[]
    for (axis,fixed),intervals in sorted(edges.items()):
        lo,hi=sorted(intervals)[0]
        for a,b in sorted(intervals)[1:]:
            if a<=hi+1e-8:hi=max(hi,b)
            else:merged.append((axis,fixed,lo,hi));lo,hi=a,b
        merged.append((axis,fixed,lo,hi))
    return spans,merged


def extend(boxes,levels,root=None):
    link=levels[1]['connection'];spec=link['povo2'];basement=spec['basement']
    try:
        from .povo2_minus1_corrections import apply as correct_minus1
    except ImportError:
        from povo2_minus1_corrections import apply as correct_minus1
    boxes=correct_minus1(boxes,spec,root)
    correction=spec['minus1_corrections'];door=correction['upper_junction_door']
    parking=spec['parking'];garden=spec['gardens']
    # The old corridor cuts removed four column bodies but left their painted
    # bands and trim floating in the garage. Use the intact registered band
    # centres to reconstruct every column from floor to ceiling.
    column_centres=[((lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
                    for n,lo,hi,_ in boxes if re.fullmatch(r'p2_parking_column_band_\d+_\d+',n)]
    # Keep the real stair plates, lift thresholds and photographed furniture.
    # Every legacy floor/wall/ceiling, including invisible old shaft holes,
    # disappears from the two replacement shells.
    def keep(box):
        n=box[0]
        if n.startswith('p2_basement_'):
            return n.startswith(('p2_basement_new_core_floor_', 'p2_basement_lift_',
                'p2_basement_core_door_south_', 'p2_basement_core_south_panic_',
                'p2_basement_cibio_closed_office_', 'p2_basement_gardens_passage',
                'p2_basement_accent', 'p2_basement_display_')) or (
                n.startswith('p2_basement_cibio_office_') and
                any(k in n for k in ('_desk_','_monitor_','_chair_','_sign_plaque')))
        if n.startswith('p2_parking_'):
            return n.startswith(('p2_parking_new_core_floor_', 'p2_parking_car_',
                                 'p2_parking_bay_line_'))
        if n.startswith(('p2_gardens_exit_wall_', 'p2_gardens_exit_ceiling',
                         'p2_gardens_exit_door_', 'p2_gardens_old_exit_spur_infill')):
            return False
        return True
    result=[b for b in boxes if keep(b)]
    # -1: retain the accepted stair, two rooms, long corridor and far exit turn.
    corridors=[basement[k] for k in ('corridor','exit_corridor','exit_turn')]
    corridors.extend(basement['cibio_corridor_sections'])
    # The ladder entrance is a recess of this corridor, not a second corridor
    # wall laid across the lift shaft.
    corridors.append((18.25,14,20.8,17))
    rooms=[r['bounds'] for r in next(l for l in spec['levels'] if l['floor']==-1)['rooms']]
    areas_minus1=corridors+rooms
    vw,vf,ve,vn=parking['vestibule']
    areas_minus2=[parking['bounds'],parking['vestibule'],
        (20.5,12.5,24,23.5),(24,12.5,34.5,14.5)]
    openings={-1:[((18.375,17.65,.39),(20.025,18.35,2.65)),
                   ((20.3,15.4,.39),(21,16.5,2.65)),
                   ((garden['indoor_corridor'][0]-.12,11,.39),
                    (garden['indoor_corridor'][2]+.12,11.5,2.65))],
              -2:[((17.375,17.65,-3.21),(19.025,18.35,-.95)),
                   ((vw-.25,15.2,-3.21),(vw+.25,16.9,-.95)),
                   ((20.25,15.2,-3.21),(20.75,16.9,-.95)),
                   ((34.2,12.65,-3.21),(34.8,14.35,-.95))]}
    for room in next(l for l in spec['levels'] if l['floor']==-1)['rooms']:
        a,b,c,d=room['bounds'];y=b+(d-b)*room['door_fraction']
        openings[-1].append(((c-.3,y-.75,.39),(c+.3,y+.75,2.65)))
    dx,dy,dz=door['centre'];half=door['width']/2
    openings[-1].append(((dx-.3,dy-half,dz-.01),(dx+.3,dy+half,dz+door['height'])))
    locked_lower=correction['lower_junction_door'];lx,ly,lz=locked_lower['centre']
    openings[-1].append(((lx-half,ly-.3,lz-.01),(lx+half,ly+.3,lz+locked_lower['height'])))
    new=[]
    def add(n,lo,hi,m='wall'):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError(n)
        new.append((n,tuple(lo),tuple(hi),m))
    floor_parts={};perimeters={}
    for floor,z,areas,wall_groups in ((-1,.4,areas_minus1,[corridors,*[[r] for r in rooms]]),
                                     (-2,-3.2,areas_minus2,[areas_minus2])):
        prefix='p2_basement_rebuilt' if floor==-1 else 'p2_parking_rebuilt'
        strips,_=union_rectangles(areas);floor_parts[floor]=strips
        material='floor_p2_tile' if floor==-1 else 'floor_p2_asphalt'
        for i,(a,b,c,d) in enumerate(strips):
            add(f'{prefix}_floor_{i}',(a,b,z-.22),(c,d,z),material)
            add(f'{prefix}_ceiling_{i}',(a,b,z+3.03),(c,d,z+3.1),'ceiling_panel')
        edges=[e for group in wall_groups for e in union_rectangles(group)[1]]
        perimeters[floor]=edges
        for i,(axis,fixed,lo,hi) in enumerate(edges):
            a=(fixed-.1,lo,z) if axis==0 else (lo,fixed-.1,z)
            b=(fixed+.1,hi,z+3.1) if axis==0 else (hi,fixed+.1,z+3.1)
            name='p2_parking_junction_facing_wall' if floor==-2 and axis==0 and fixed==24 and lo>=14.5 else f'{prefix}_wall_{i}'
            add(name,a,b)
    # Separate -2 vestibule thresholds. The right turn feeds the parking aisle;
    # the left threshold faces a wall, with offices left and garden right.
    z=-3.2
    turn=basement['exit_turn']
    add('p2_basement_rebuilt_lab_junction_partition',
        (dx-.08,turn[1],dz),(dx+.08,turn[3],dz+3.1))
    add('p2_basement_rebuilt_lower_junction_partition',
        (basement['exit_corridor'][0],ly-.08,lz),(basement['exit_corridor'][2],ly+.08,lz+3.1))
    for n,a,b in (
        ('parking_partition',(vw-.08,vf,z),(vw+.08,18,z+3.1)),
        ('offices_partition',(20.42,vf,z),(20.58,18,z+3.1)),
        ('approach_west',(8.4,11.3,z),(8.5,18,z+3.1)),
        ('approach_north',(8.4,18,z),(vw,18.1,z+3.1)),
        ('approach_east',(10.8,11.3,z),(10.9,vf,z+3.1)),
        ('garden_partition',(34.42,12.5,z),(34.58,14.5,z+3.1))):
        add('p2_parking_rebuilt_'+n,a,b)
    # Remove duplicate walls and plate overlaps before opening the doors. This
    # includes shared room/corridor boundaries and the fixed stair shell.
    fixed=[b for b in result if b[0].startswith(('p2_internal_shell_','p2_basement_new_core_floor_',
                                               'p2_parking_new_core_floor_'))]
    clean=[]
    for box in new:
        parts=[box]
        if box[3]=='wall':
            for other in fixed+[b for b in clean if b[3]=='wall']:
                parts=[p for b in parts for p in subtract_box(b,(other[1],other[2]))]
        elif box[3].startswith('floor_'):
            for other in fixed:
                if other[3].startswith('floor_'):
                    parts=[p for b in parts for p in subtract_box(b,(other[1],other[2]))]
        clean.extend(parts)
    for hole in openings[-1]+openings[-2]:
        clean=[p for b in clean for p in (subtract_box(b,hole) if b[3]=='wall' else [b])]
    # Reserve the ladder shaft in all newly made surfaces; its own walls and
    # bottom plate are retained intact, including the existing door opening.
    a,b,c,d=spec['lift']['shaft'];hole=((a,b,.17),(c,d,3.8))
    clean=[p for box in clean for p in subtract_box(box,hole)]
    result.extend(clean)
    def detail(n,lo,hi,m):result.append((n,tuple(lo),tuple(hi),m))
    parking['columns']=[list(p) for p in column_centres]
    for i,(x,y) in enumerate(column_centres):
        detail(f'p2_parking_rebuilt_column_{i}',(x-.3,y-.3,-3.2),(x+.3,y+.3,-.17),'wall')
        detail(f'p2_parking_rebuilt_column_band_{i}',(x-.31,y-.31,-2.4),(x+.31,y+.31,-2.1),'parking_line')
    # The old well excavation also clipped away -1's open stair-door leaves.
    # Restore them after the well is final, along the inside landing edges.
    for i,x in enumerate((18.375,20.025)):
        detail(f'p2_basement_core_door_south_{i}',(x-.025,18.05,.42),(x+.025,18.85,2.58),'door_black')
        detail(f'p2_basement_core_south_panic_{i}',(x-.05,18.15,1.4),(x+.05,18.75,1.445),'door_pushbar')
    # These two new doors are permanent parts of the solid model. There is no
    # func_door, sensor, use handler or breakable entity capable of opening them.
    for token,portal in (('upper',door),('lower',locked_lower)):
        x,y,z0=portal['centre'];axis=portal['axis'];across=1-axis;h=portal['width']/2
        centre=[x,y,z0]
        for i,(start,end) in enumerate(((-h,-.006),(.006,h))):
            lo=[x-.04,y-.04,z0];hi=[x+.04,y+.04,z0+portal['height']]
            lo[across]=centre[across]+start;hi[across]=centre[across]+end
            detail(f'p2_basement_locked_{token}_leaf_{i}',lo,hi,'door_black')
        for i,offset in enumerate((-h,h)):
            lo=[x-.05,y-.05,z0];hi=[x+.05,y+.05,z0+portal['height']+.04]
            lo[across]=centre[across]+offset-.025;hi[across]=centre[across]+offset+.025
            detail(f'p2_basement_locked_{token}_jamb_{i}',lo,hi,'metal_dark')
    # Retain the vestibule's open black door pairs and closed office frontage.
    for name,x in (('parking',vw),('offices',20.5),('garden',34.5)):
        lo,hi=(12.65,14.35) if name=='garden' else (15.2,16.9)
        for i,y in enumerate((lo,hi)):
            detail(f'p2_parking_{name}_door_{i}',(x+.12,y-.025,z+.02),(x+.92,y+.025,z+2.18),'door_black')
    for i,y in enumerate((20,22)):
        detail(f'p2_parking_office_closed_door_{i}',(23.96,y-.5,z+.02),(24,y+.5,z+2.15),'door_closed')
    # Replace inherited, rotated light positions with fixtures physically inside
    # the rebuilt rooms/corridors. No orphan lamps in the vacated parking wing.
    spec['lights']=[p for p in spec['lights'] if p[2]>=3.8]
    spine_x=correction['spine_route_x'];upper_y=correction['upper_route_y']
    rooms_north=basement['cibio_corridor'][3]
    lamps={-1:[(x,16.25) for x in (-3,3,9,15,24,31)]+
        [(spine_x,y) for y in range(22,int(rooms_north),6)]+
        [(x,upper_y) for x in (3,10,17,24,31)]+[(34.5,y) for y in range(14,int(upper_y),7)]+
        [(-9.5,22.5),(-9.5,35.5+correction['room2_north_shift_metres']),(19.2,22)],
        -2:[(x,y) for x in (-21,-12,-3,5) for y in (-7,3,12)]+
        [(15.5,16.05),(22.3,16),(22.3,21),(28,13.5),(33,13.5),(19.2,22)]}
    for floor,points in lamps.items():
        z=.4 if floor==-1 else -3.2;prefix='p2_basement' if floor==-1 else 'p2_parking'
        for i,(x,y) in enumerate(points):
            if (x,y)==(19.2,22):
                spec['lights'].append([x,y,z+2.7]);continue
            spec['lights'].append([x,y,z+2.85])
            detail(f'{prefix}_rebuilt_fixture_{i}',(x-.36,y-.2,z+2.98),(x+.36,y+.2,z+3.03),'light_diffuser')
    # Clear exterior/context solid geometry from the complete replacement
    # footprints, rather than relying on the pre-rotation excavation locations.
    holes=[((a-.12,b-.12,z-.24),(c+.12,d+.12,z+3.12))
           for floor,z in ((-1,.4),(-2,-3.2)) for a,b,c,d in floor_parts[floor]]
    for hole in holes:
        result=[p for box in result for p in (subtract_box(box,hole)
                if box[0].startswith(('exterior_', 'library_0_access')) else [box])]
    try:
        from .build_povo_campus import subtract_polygon_box
    except ImportError:
        from build_povo_campus import subtract_polygon_box
    ext=levels[0]['exterior']
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext.get(key,[]):
            vv=mesh['vertices'];bounds=([min(v[i] for v in vv) for i in range(3)],
                                     [max(v[i] for v in vv) for i in range(3)])
            relevant=[h for h in holes if all(bounds[0][i]<h[1][i] and bounds[1][i]>h[0][i] for i in range(3))]
            if not relevant:clipped.append(mesh);continue
            vertices=[];faces=[]
            for face in mesh['faces']:
                polygons=[[(tuple(vv[i]),(0,0)) for i in face]]
                for lo,hi in relevant:
                    polygons=[p for poly in polygons for p in subtract_polygon_box(poly,lo,hi)]
                for poly in polygons:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+j,start+j+1) for j in range(1,len(poly)-1))
            if faces:clipped.append(dict(mesh,vertices=vertices,faces=faces,surface_clipped=True))
        ext[key]=clipped
    # Radar, audits and the build all consume this same final-coordinate layout.
    parking['areas']=[list(r) for r in areas_minus2]
    north_y=rooms_north-1.5
    routes=[dict(id='minus1_stair_to_labs',points=[[19.2,22,.4],[19.2,17.15,.4],[spine_x,17.15,.4],[spine_x,north_y,.4]]),
        dict(id='minus1_labs_to_exit',points=[[spine_x,north_y,.4],[spine_x,17.15,.4],[34.5,17.15,.4],[34.5,10,.4]]),
        dict(id='minus1_stair_to_exit_direct',points=[[19.2,22,.4],[19.2,17.15,.4],[34.5,17.15,.4],[34.5,10,.4]]),
        dict(id='minus2_parking_aisle',points=[[9.65,11.3,-3.2],[9.65,5,-3.2],[-23.5,5,-3.2],[-23.5,-8,-3.2]]),
        dict(id='minus2_garden_exit',points=[[22.5,16.05,-3.2],[22.5,13.5,-3.2],[39.5,13.5,-3.2]])]
    for room in next(l for l in spec['levels'] if l['floor']==-1)['rooms']:
        a,b,c,d=room['bounds'];y=b+(d-b)*room['door_fraction']
        routes.append(dict(id=room['id']+'_entrance',points=[[-3.8,y,.4],[-8,y,.4]]))
    spec['basement_rebuild']=dict(status='Rebuilt from accepted footprints in campus coordinates',
        levels=[dict(floor=f,areas=[list(r) for r in areas],floor_pieces=[list(r) for r in floor_parts[f]])
                for f,areas in ((-1,areas_minus1),(-2,areas_minus2))],
        clear_height=3.03,routes=routes,metric_status='Existing estimated dimensions retained')
    return result
