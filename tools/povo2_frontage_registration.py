"""Register the assembled Povo 2 interiors against one shared facade datum.

The historical construction passes use their original local coordinates. This
final export stage keeps that reconstruction reproducible while registering
geometry, doors, navigation, furniture and collision together. Dimensions are
fitted to the confirmed topology, not an independent measured survey.
"""
import copy
import math
import random
import re
from .povo_room_fitout import subtract_box
from .povo2_interiors import fit_ground_room
from .povo_floor_surfaces import bounds, overlaps, subtract
from .povo_stairs import railing
from .povo_library_stair import WALL_Y, grass_z
from .povo2_roadside_closure import _hexa, _fence, _barrier
from .povo_street_footways import corners, prism, tops, trim_carriageways

FACADE = 10.8
OFFSET = FACADE-2.
GRASS_WIDTH = 5.
TERRACE_WIDTH = 1.71
GRATE = FACADE-TERRACE_WIDTH
PAVEMENT_EDGE = GRATE-GRASS_WIDTH
ROAD_WIDTH = 7.
WALK_WIDTH = 1.4
ROAD_NORTH = PAVEMENT_EDGE-WALK_WIDTH
ROAD_CENTRE = ROAD_NORTH-ROAD_WIDTH/2
ROAD_OFFSET = ROAD_CENTRE-(-5.)
BUS_PREFIX = 'exterior_abandoned_bus_'
BUS_NORTH_SHIFT = 1.8
ROOMS = ('b106','b108','b109')
_SKIP = {'flight_counts','scale_metres_per_crop_pixel','core_registered_span_metres',
         'size_pixels','span','crop_original_pixels','trace_crop_pixels_approx',
         'trace_original_pixels_approx','public_door_pixels','source_pixels',
         'source_plan_bounds','trace_bounds','source_bounds','source_anchors',
         'ground_opening_east','table_rows_y'}


def shift_metadata(obj, offset=OFFSET, key='', seen=None):
    """Translate coordinate records, preserving shared mutable/immutable aliases.

    Pixel measurements, relative offsets and furniture row counts are not
    coordinates. North intervals translate both endpoints; east intervals stay.
    """
    if seen is None:seen={}
    if key in _SKIP or 'pixels' in key:return obj
    if key in {'door_y','vestibule_front_north',
               'lower_junction_door_north_coordinate','upper_route_y'}:
        return obj+offset
    if not isinstance(obj,(dict,list,tuple)):return obj
    if id(obj) in seen:return seen[id(obj)]
    numeric=isinstance(obj,(list,tuple)) and all(isinstance(v,(int,float)) for v in obj)
    if numeric and key=='rows':return obj  # office furniture row counts
    if isinstance(obj,dict):
        seen[id(obj)]=obj
        for k,v in list(obj.items()):obj[k]=shift_metadata(v,offset,k,seen)
        return obj
    if numeric and key=='entrance' and len(obj)==3:
        result=[obj[0],obj[1]+offset,obj[2]+offset]
    elif numeric and key=='side_opening_north':
        result=[v+offset for v in obj]
    elif numeric and len(obj) in (2,3,4):
        result=list(obj);result[1]+=offset
        if len(obj)==4:result[3]+=offset
    else:
        if isinstance(obj,list):seen[id(obj)]=obj
        result=[shift_metadata(v,offset,key,seen) for v in obj]
    if isinstance(obj,list):obj[:]=result;value=obj
    else:value=tuple(result)
    seen[id(obj)]=value
    return value


def apply(boxes, levels):
    """Return the final registered assembly; called once after local assembly."""
    link=next(l['connection'] for l in levels if l.get('connection'))
    p=link['povo2'];ext=levels[0]['exterior']
    if p.get('frontage_registration'):raise ValueError('Frontage already registered')
    source_entrance=copy.deepcopy(p['ground']['entrance'])
    seen={}
    shift_metadata(p,seen=seen)
    for key in ('stair','ground','lift','povo2_arrival','povo2_floor_parts','povo2_corridor'):
        if key in link:shift_metadata(link[key],key=key,seen=seen)
    for station in link['audit_stations']:
        if station['point'][1]>=10:shift_metadata(station,seen=seen)
    for point in link['nav_seeds']:
        if point[1]>=10:shift_metadata(point,key='point',seen=seen)
    for point in link['lights']:
        if point[1]>=10:shift_metadata(point,key='point',seen=seen)
    shift_metadata(ext['entrance'],seen=seen)
    p['ground']['source_entrance']=source_entrance
    banks=[b for b in ext['entrance']['door_banks'] if b['line']=='inner']
    p['ground']['entrance']=[ext['entrance']['inner_x'],
        min(b['centre'][1]-b['clear_width']/2 for b in banks),
        max(b['centre'][1]+b['clear_width']/2 for b in banks)]
    # Ground-floor room fronts remain at the common facade; the corridor and
    # north room walls follow the translated core. Furnishings keep their size.
    ground=next(l for l in p['levels'] if l['floor']==0)
    rooms = [room for room in ground['rooms'] if room['id'] in ROOMS]
    for room in rooms:
        room['bounds'][1]=FACADE
        room['footprint_local_metres'][1]=FACADE
    cfg=p['additions']['config']
    for room in cfg['ground_rooms']:room['bounds'][1]=FACADE
    cfg['ground_registration'].update(facade_north=FACADE,stairwell_south=18+OFFSET,
        corridor_width=2.6,status='Shared floor registration; room depths fitted to translated core')
    # The speculative south parking bays extended outside the building. Keep
    # the aisle, vestibule, columns and the retained northern parking bays.
    p['parking']['bounds'][1]=FACADE
    p['parking']['cars']=[[x,y+OFFSET,m] for x,y,m in p['parking']['cars'] if y+OFFSET>=FACADE]
    p['parking']['columns']=[v for v in p['parking'].get('columns',[]) if v[1]>=FACADE]
    p['lights']=[v for v in p['lights'] if not (v[0]<=11 and v[1]<FACADE and v[2]<0)]
    for floor in p['basement_rebuild']['levels']:
        if floor['floor']==-2:
            for key in ('areas','floor_pieces'):
                if key in floor:floor[key]=[[a,max(b,FACADE),c,d] for a,b,c,d in floor[key] if d>FACADE]
    # Remove routes into the deleted speculative southern parking bays.
    for route in [*p['parking']['routes'],*p['basement_rebuild']['routes']]:
        for pt in route['points']:
            if pt[0]<=11 and pt[2]<0:pt[1]=max(pt[1],FACADE+.6)
    remove=('p2_roadside_', 'p2_basement_drawio_up_', 'p2_basement_drawio_drawio_up_',
            'p2_basement_drawio_old_up_infill','p2_gardens_street_',
            'exterior_user_fill_','exterior_p2_roadside_',
            'p2_aligned_garden_guard_east_', 'exterior_povo1_street_corner',
            'exterior_library_library_street_fence_', 'exterior_library_library_street_extension_',
            'exterior_library_hedge_', 'exterior_p2_entry_floor_joint_',
            'exterior_library_sidewalk_corner',
            'exterior_p2_entry_ceiling_joint_', 'p2_basement_repair_former_shaft_ceiling_0')
    result=[]
    for name,lo,hi,material in boxes:
        if name.startswith(remove):continue
        if name.startswith('exterior_p2_entry_floor'):
            material='floor_p2_tile'
        elif name.startswith('exterior_p2_entry_ceiling'):
            material='ceiling_panel'
        own=name.startswith(('p2_','academic_first_link_p2_', 'exterior_p2_entry_',
                             'exterior_povo2_front_annex_0_'))
        if own:
            lo=(lo[0],lo[1]+OFFSET,lo[2]);hi=(hi[0],hi[1]+OFFSET,hi[2])
            # Stretch only the room envelope, never desks, chairs or door leaves.
            for room in ROOMS:
                prefix='p2_ground_'+room+'_'
                if name.startswith(prefix):
                    suffix=name[len(prefix):]
                    if suffix.startswith(('floor','ceiling','wall_west','wall_east')):
                        lo=(lo[0],lo[1]-OFFSET,lo[2])
            if hi[2]<0 and name.startswith(('p2_parking_','p2_basement_')):
                if hi[1]<=FACADE:continue
                lo=(lo[0],max(lo[1],FACADE),lo[2])
            if name in ('p2_aligned_garden_wall_road',
                        'p2_basement_drawio_terrace_retaining_west_south',
                        'p2_basement_drawio_terrace_retaining_west_end'):
                hi=(hi[0],hi[1],.4)
        if name.startswith(BUS_PREFIX):
            lo=_move_bus(lo);hi=_move_bus(hi)
        result.append((name,lo,hi,material))
    def add(name,lo,hi,material='wall'):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError(name)
        result.append(('p2_registered_'+name,tuple(lo),tuple(hi),material))
    add('parking_front',(-25,FACADE-.16,-3.42),(11,FACADE,-.1))
    # Extend the existing overhead bridge INSIDE the retained facade. Its
    # external span and the Povo 1 arrival never move.
    add('bridge_floor',(16.5,10,10.98),(20,10+OFFSET,11.2),'floor_circulation')
    add('bridge_ceiling',(16.5,10,14.43),(20,10+OFFSET,14.5),'ceiling_panel')
    for x in (16.34,20.):add('bridge_side_'+str(x),(x,10,11.2),(x+.16,10+OFFSET,14.5))
    link['povo2_floor_parts'].append([16.5,10,20,10+OFFSET])
    # Clear context at the translated interiors. Never clip another interior,
    # the Povo 1 building, or the shared bridge outside the Povo 2 facade.
    holes=[]
    for name,lo,hi,m in result:
        if name.startswith(('p2_','academic_first_link_p2_')) and m.startswith('floor_') and any(abs(hi[2]-z)<.02 for z in (-3.2,.4,4.,11.2)):
            holes.append(((lo[0],lo[1],hi[2]-.23),(hi[0],hi[1],hi[2]+3.1)))
    holes.append(((11.1,26.801,-3.21),(20.4,34.69,14.5)))
    # All old upper-road fences, lawns and cap meshes are superseded below.
    for key in ('meshes','collision_meshes'):
        ext[key]=[m for m in ext[key] if not m['name'].startswith(('exterior_p2_roadside_',
            'exterior_user_fill_','exterior_p2_garden_'))]
    result=_carve_context(result,ext,holes)
    result=_finish_ground_rooms(result, ground, rooms, cfg['ground_corridor'], levels[0]['facades'])
    _clear_garden_overhang(result,p['gardens']['garden'])
    _extend_garden_exit(result,ext,p,add)
    link['nav_seeds'].append([30.8,15.,-3.2])
    link['nav_seeds'].extend(([53.5,13.,4.89],[43.,-5.,6.32]))
    _road_and_landscape(result,ext,p,add,levels[0]['library_stair']['rails'])
    _finish_povo1_lobby(result)
    library=levels[0]['library_stair']
    west,east=library['x']
    edge=library['grass_y'][0]
    ext['meshes'].extend(_shrub_leaves(
        'exterior_library_hedge', (west,edge+.05,east,edge+.6),
        lambda x,y:grass_z(x), (23,2), seed=20261108, radius=.32, inset=.04))
    p['frontage_registration']=dict(facade_north=FACADE,interior_offset_north=OFFSET,
        grass_width=GRASS_WIDTH,grate_north=GRATE,pavement_edge_north=PAVEMENT_EDGE,
        road_offset_north=ROAD_OFFSET,road_width=ROAD_WIDTH,pavement_width=WALK_WIDTH,
        room_depth=cfg['ground_rooms'][0]['bounds'][3]-FACADE,
        source='User confirms all floors align; no protruding frontage',
        metric_status='Fitted to confirmed topology and approximate grass/bush dimensions; not surveyed',
        preserve='Internal room/corridor relationships and stair directions; Povo 1 and external bridge span')
    return result


def _finish_ground_rooms(boxes, ground, rooms, corridor, facades):
    """Rebuild the kits and glazing in the registered classroom footprint."""
    west, east = corridor[0], corridor[2]
    z = ground['z']
    ceiling = next(hi[2] for n, _, hi, _ in boxes if n == 'p2_ground_left_extension_ceiling')
    air = ((west, FACADE, z+3.1), (east, corridor[3], ceiling))
    old_front = ((west, 9.7, z), (east, FACADE-.1, ceiling))
    room_prefixes = tuple(f"p2_ground_{r['id']}_" for r in rooms)
    kits = tuple(f"{ground['id']}_room_{r['id']}_" for r in rooms)
    obsolete = kits + tuple(p+s for p in room_prefixes for s in ('monitor_', 'tier_', 'wall_south', 'window_'))
    result = []
    for box in boxes:
        name = box[0]
        if name.startswith(obsolete):
            continue
        if name.startswith('exterior_povo2_context'):
            result.extend(subtract_box(box, air))
        elif name.startswith('facade_p2_south_l0_'):
            result.extend(subtract_box(box, old_front))
        else:
            result.append(box)

    openings = facades['openings']
    openings[:] = [r for r in openings if not (r['face'] == 'p2_south' and r['floor'] == -1
                   and r['span'][0] < east and r['span'][1] > west)]
    for room in rooms:
        ident = room['id']
        result.extend(fit_ground_room(ground, room, ceiling-z))
        station_prefix = ident+'_aisle_'
        stations = ground['audit_stations']
        stations[:] = [s for s in stations if not s['id'].startswith(station_prefix)]
        stations.extend(dict(id=station_prefix+str(i), point=list(q))
                        for i, q in enumerate(room['fitout']['audit_points_local_metres']))
        a, _, b, _ = room['bounds']
        sill, head = z+.15, ceiling-.18
        prefix = f'p2_registered_{ident}_front_'
        for label, x0, x1, z0, z1 in (('sill', a, b, z, sill), ('head', a, b, head, ceiling),
                                       ('west_jamb', a, a+.1, sill, head),
                                       ('east_jamb', b-.1, b, sill, head)):
            result.append((prefix+label, (x0, FACADE-.1, z0), (x1, FACADE+.1, z1), 'wall'))
        width = b-a-.2
        count = math.ceil(width/1.45)
        for i in range(count):
            left = a+.1 + i*width/count
            right = a+.1 + (i+1)*width/count
            if i:
                result.append((prefix+f'mullion_{i}', (left-.025, FACADE-.05, sill),
                               (left+.025, FACADE+.05, head), 'window_frame'))
            lo = (left+(.025 if i else 0.), FACADE-.015, sill)
            hi = (right-(.025 if i+1 < count else 0.), FACADE+.015, head)
            name = prefix+f'pane_{i}'
            result.append((name, lo, hi, 'window_glass'))
            openings.append(dict(face='p2_south', floor=-1, bay=name, span=[lo[0], hi[0]],
                                 glass=(lo, hi), material='window_glass', sealed=False))
    # The old curtain-wall carve shortened the tips of the party walls.
    for x in (west, *sorted(r['bounds'][0] for r in rooms if r['bounds'][0] > west)):
        hi = (x+.1, FACADE+.4, ceiling)
        lo = (x-.1, 10.025 if x == west else FACADE+.1, z)
        tip = [(f'p2_registered_classroom_wall_tip_{x:g}', lo, hi, 'wall')]
        for name, a, b, material in result:
            if material == 'wall' and all(a[i] < hi[i] and b[i] > lo[i] for i in range(3)):
                tip = [p for piece in tip for p in subtract_box(piece, (a, b))]
        result.extend(tip)
    return result


def _carve_context(boxes,ext,holes):
    from .build_povo_campus import subtract_polygon_box
    result=[]
    for box in boxes:
        if not box[0].startswith('exterior_') or box[0].startswith(('exterior_p2_entry_', 'exterior_abandoned_bus_')):
            result.append(box);continue
        relevant=[h for h in holes if all(box[1][i]<h[1][i] and box[2][i]>h[0][i] for i in range(3))]
        parts=[box]
        for hole in relevant:parts=[p for b in parts for p in subtract_box(b,hole)]
        result.extend(parts)
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext[key]:
            if mesh['name'].startswith('exterior_abandoned_bus_'):
                clipped.append(mesh)
                continue
            vv=mesh['vertices'];lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
            relevant=[h for h in holes if all(lo[i]<h[1][i] and hi[i]>h[0][i] for i in range(3))]
            if not relevant:clipped.append(mesh);continue
            vertices=[];faces=[]
            for face in mesh['faces']:
                polys=[[(tuple(vv[i]),(0,0)) for i in face]]
                for hole in relevant:polys=[p for poly in polys for p in subtract_polygon_box(poly,*hole)]
                for poly in polys:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+i,start+i+1) for i in range(1,len(poly)-1))
            if faces:clipped.append(dict(mesh,vertices=vertices,faces=faces,surface_clipped=True))
        ext[key]=clipped
    return result


def _finish_povo1_lobby(boxes):
    # Run the terrazzo finish to the stair-enclosure wall. The original
    # finish stopped short of it, exposing the pale structural slab.
    _,lo,hi,material=next(box for box in boxes if box[0]=='academic_ground_entrance_lobby_000')
    wall_face=max(top[1] for name,_,top,_ in boxes
                  if name.startswith('stair_enclosure_north_'))
    boxes.append(('academic_ground_lobby_finish_south', (lo[0],wall_face,lo[2]),
                  (hi[0],lo[1],hi[2]),material))


def _move_bus(point):
    x,y,z=point
    return x,y+BUS_NORTH_SHIFT,z


def _clear_garden_overhang(boxes, garden):
    # The prototype ground slab predates the shifted garden. Trim its
    # cantilever from the open yard while retaining the ground outside it.
    west,south,east,north=garden
    air=((west,south,-3.19),(east,north,4.))
    boxes[:]=[part for box in boxes for part in
              (subtract_box(box,air) if box[0].startswith('exterior_ground_') else [box])]


def _road_sections(points):
    """Return a cross-section with shared miters at every centreline joint."""
    # Shared cross-sections keep both sidewalks and the road joined on bends.
    normals = []
    for a, b in zip(points, points[1:]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        normals.append((dy/length, -dx/length))
    offsets = [normals[0]]
    for a, b in zip(normals, normals[1:]):
        scale = 1 + a[0]*b[0] + a[1]*b[1]
        offsets.append(((a[0]+b[0])/scale, (a[1]+b[1])/scale))
    offsets.append(normals[-1])

    def section(index, distance, lift):
        x, y, z = points[index]
        nx, ny = offsets[index]
        return x+nx*distance, y+ny*distance, z+lift
    return section


def _edge_at_x(edge,x):
    for a,b in zip(edge,edge[1:]):
        if a[0] <= x <= b[0]:
            f = (x-a[0])/(b[0]-a[0])
            return x,a[1]+f*(b[1]-a[1]),a[2]+f*(b[2]-a[2])
    raise ValueError(f'No road edge at east coordinate {x}')


def _road_bands(name,points,section,width,walk,*,concrete_mouth=False,markings=False):
    def offset(index,side):
        return math.copysign(width[index]+(abs(side)-1)*walk,side)

    for i in range(len(points)-1):
        for band,lo,hi,lift,material in (
            ('road',-1,1,0.,'exterior_asphalt'),
            ('footway_south',-2,-1,.12,
             'exterior_concrete' if concrete_mouth and i==0 else 'exterior_paving'),
            ('footway_north',1,2,.12,'exterior_paving'),
        ):
            top = [section(j,offset(j,k),lift) for j,k in
                   ((i,lo),(i,hi),(i+1,hi),(i+1,lo))]
            yield prism(f'exterior_{name}_{band}_{i}',top,material)
        if markings:
            for side in (-1,1):
                ends = [section(j,side*(width[j]-inset),.012) for j,inset in
                        ((i,.17),(i,.07),(i+1,.07),(i+1,.17))]
                if i==0 and side==-1:
                    # The west edge stripe stops at either side of the T-junction.
                    a,b,c,d = ends
                    for suffix,poly in enumerate(((a,b,(b[0],-9.,b[2]),(a[0],-9.,a[2])),
                                                   ((d[0],-2.,d[2]),(c[0],-2.,c[2]),c,d))):
                        yield prism(f'exterior_{name}_edge_{i}_{side}_{suffix}',poly,'exterior_marking',.008)
                else:
                    yield prism(f'exterior_{name}_edge_{i}_{side}',ends,'exterior_marking',.008)


def _measured_outer(x,y,side):
    # Both spans are measured at E44. Fade to the existing apron at E49.3;
    # the library-side widening ends only after the E52 planting tip.
    end = 49.3 if side>0 else 54.
    plateau = 46. if side>0 else 52.
    weight = max(0.,min(1.,(x-22.)/10.,(end-x)/(end-plateau)))
    return y+weight*((7. if side>0 else -7.9)-y)


def _measured_footways(meshes,section,width):
    """Build the changed walks from shared global curb/outer cross-sections.

    The original miter is diagonal in plan. Stretching individual clipped
    polygons gives its two sides different cross-sections and leaves holes.
    One east-coordinate station grid instead joins both edges exactly.
    """
    result=[]
    def clip(poly,x,keep_right):
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            ina = a[0]>=x if keep_right else a[0]<=x
            inb = b[0]>=x if keep_right else b[0]<=x
            if ina:out.append(a)
            if ina!=inb:
                t=(x-a[0])/(b[0]-a[0])
                out.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(3)))
        return out
    for mesh in meshes:
        if not mesh['name'].startswith('exterior_registered_footway_'):
            result.append(mesh);continue
        original=mesh['vertices'][len(mesh['vertices'])//2:]
        for j,poly in enumerate((clip(original,22.,False),clip(original,54.,True))):
            if len(poly)>=3:
                slab=prism(mesh['name']+f'_terminal_{j}',poly,mesh['material'])
                if slab:result.append(slab)
    for side,label in ((-1,'south'),(1,'north')):
        indices=range(len(width)-1,-1,-1)
        curb=[section(i,side*width[i],.12) for i in indices]
        outside=[section(i,side*(width[i]+WALK_WIDTH),.12) for i in range(len(width)-1,-1,-1)]
        stations=sorted({22.,32.,46.,49.3,52.,54.} |
                        {v[0] for v in curb+outside if 22.<v[0]<54.})
        for j,(left,right) in enumerate(zip(stations,stations[1:])):
            a,b=(_edge_at_x(curb,x) for x in (left,right))
            c,d=(_edge_at_x(outside,x) for x in (right,left))
            c=(c[0],_measured_outer(c[0],c[1],side),c[2])
            d=(d[0],_measured_outer(d[0],d[1],side),d[2])
            if side*(c[1]-b[1])<=0 or side*(d[1]-a[1])<=0:
                raise ValueError('Measured sidewalk crossed its fixed curb')
            slab=prism(f'exterior_registered_footway_{label}_span_{j}',[a,b,c,d])
            if slab:result.append(slab)
    return result


def _road_and_landscape(result,ext,p,add,library_rails):
    # Rebuild the straight descending road and its western transition, removing
    # the obsolete stair excavation from the actual carriageway.
    road=re.compile(r'exterior_(?:road_[0-3](?:_|$)|footway_[0-3]_|road_joint_[0-2](?:_|$)|road_edge_[0-3](?:_|$))')
    for key in ('meshes','collision_meshes'):ext[key]=[m for m in ext[key] if not road.match(m['name']) and not m['name'].startswith('exterior_road_front_link')]
    for key in ('meshes','collision_meshes'):
        ext[key]=[dict(mesh,vertices=[_move_bus(v) for v in mesh['vertices']])
                  if mesh['name'].startswith(BUS_PREFIX) else mesh for mesh in ext[key]]
    front_road = ext['front_road']
    front_points = front_road['points']
    half = ROAD_WIDTH/2
    mouth = front_points[0][0]-half
    points=[(mouth,-5.5,7.6),(56.5,-5.5,7.6),(50,ROAD_CENTRE,7.6),
            (32,ROAD_CENTRE,4.),(22,ROAD_CENTRE,4.),(-23,ROAD_CENTRE,3.),(-36,-12,3.)]
    section = _road_sections(points)
    width = [half]*(len(points)-1)+[3.]
    new = list(_road_bands('registered', points, section, width, WALK_WIDTH,
                           concrete_mouth=True))
    new = _measured_footways(new,section,width)
    old_front = re.compile(r'exterior_road_front_(?:\d+|joint_|footway_|edge_|campus_paving_)')
    for key in ('meshes', 'collision_meshes'):
        ext[key] = [m for m in ext[key] if not old_front.match(m['name'])
                    and not m['name'].startswith('exterior_paving_front_road_corner_')
                    and (not m['name'].startswith('exterior_paving_road_corner_')
                         or m['name'].startswith(('exterior_paving_road_corner_4_', 'exterior_paving_road_corner_5_')))]
    new.extend(corners('registered_west', dict(points=[points[-2], points[-1], (-47,-27,3.)],
                                              width=6., footway_width=WALK_WIDTH)))

    front_section = _road_sections(front_points)
    front_width = front_road['footway_width']
    via = _road_bands('registered_via', front_points, front_section,
                      [half]*len(front_points), front_width, markings=True)
    mouth_bands = [poly for mesh in new[:6] for poly in tops(mesh)]
    for mesh in via:
        if mesh['name'] != 'exterior_registered_via_footway_south_0':
            new.append(mesh)
            continue
        # The mouth has its own two sidewalks. Cut their shared footprint
        # out of the Via sidewalk to keep the three finishes at one grade.
        pieces = tops(mesh)
        for cutter in mouth_bands:
            pieces = [part for poly in pieces for part in
                      (subtract(poly,cutter) if overlaps(bounds(poly),bounds(cutter)) else [poly])]
        for i,top in enumerate(pieces):
            piece = prism(f"{mesh['name']}_junction_{i}",top)
            if piece:
                new.append(piece)
    frontage_x = front_points[0][0]-half-front_width
    front_inner = []
    for i in range(1,len(front_points)):
        x,y,z = front_section(i,0.,.12)
        nx,ny,_ = front_section(i,1.,.12)
        front_inner.append((frontage_x,y+(frontage_x-x)*(ny-y)/(nx-x),z))
    for i,(a,b) in enumerate(zip(front_inner,front_inner[1:]),1):
        # Concrete connects the fixed forecourt edge to the measured sidewalk.
        near = front_section(i,-half-front_width,.12)
        far = front_section(i+1,-half-front_width,.12)
        top = [a,near,far,b]
        for j,indices in enumerate(((0,1,2),(0,2,3))):
            slab = prism(f'exterior_registered_via_verge_{i}_{j}',
                         [top[k] for k in indices], material='exterior_concrete')
            if slab:
                new.append(slab)
    front_start, front_end = (point[1] for point in front_inner[:2])
    court_z = front_points[2][2]

    def front_grade(y):
        fraction = min(1.,max(0.,(y-front_start)/(front_end-front_start)))
        return 7.72+(court_z+.12-7.72)*fraction

    original_north = [section(i,width[i]+WALK_WIDTH,.12) for i in (5,4,3,2,1,0)]
    north_edge = sorted({v[0]:v for v in original_north}.values(),key=lambda v:v[0])
    for x in (32.,46.,49.3):
        v = _edge_at_x(original_north,x)
        north_edge.append((x,_measured_outer(x,v[1],1),v[2]))
    north_edge = sorted(north_edge,key=lambda v:v[0])
    north_edge = [(x,_measured_outer(x,y,1),z) for x,y,z in north_edge]
    original_south = [section(i,-width[i]-WALK_WIDTH,.12) for i in (5,4,3,2,1,0)]
    south_edge = list(original_south)
    for x in (32.,52.,54.):
        south_edge.append(_edge_at_x(original_south,x))
    south_edge = sorted([(x,_measured_outer(x,y,-1),z) for x,y,z in south_edge])

    def verge_grade(x):
        return _edge_at_x(north_edge,x)[2]

    garden_end = p['gardens']['garden'][2]
    edge = [_edge_at_x(north_edge,garden_end),
            *(v for v in north_edge if garden_end<v[0]<frontage_x),
            _edge_at_x(north_edge,frontage_x)]
    back = [(x, GRATE, front_grade(GRATE)) for x, _, _ in edge]
    for i in range(len(edge)-1):
        top = [edge[i], edge[i+1], back[i+1], back[i]]
        for j, indices in enumerate(((0,1,2),(0,2,3))):
            new.append(prism(f'exterior_registered_corner_apron_{i}_{j}',
                             [top[k] for k in indices], thickness=8.))
    # Extend the apron down the street grade to the existing forecourt.
    # The east wall of the open garden is the west edge of this connection.
    court_start, court_end = 17.55, p['gardens']['garden'][3]+.08
    court_edge = 55.5
    new.append(prism('exterior_registered_forecourt_slope',
        [(garden_end,GRATE,back[0][2]),(frontage_x,GRATE,back[-1][2]),
         (frontage_x,front_end,court_z+.12),(garden_end,front_end,court_z+.12)], thickness=8.))
    new.append(prism('exterior_registered_forecourt_landing',
        [(garden_end,front_end,court_z+.12),(court_edge,front_end,court_z+.12),
         (court_edge,court_start,court_z),(garden_end,court_start,court_z)], thickness=7.5))
    new.append(prism('exterior_registered_forecourt_landing_corner',
        [(court_edge,front_end,court_z+.12),(frontage_x,front_end,court_z+.12),
         (frontage_x,court_start,court_z+.12)], thickness=7.5))
    new.append(prism('exterior_registered_forecourt_landing_join',
        [(court_edge,front_end,court_z+.12),(frontage_x,court_start,court_z+.12),
         (court_edge,court_start,court_z)], thickness=7.5))
    new.append(prism('exterior_registered_forecourt_edge',
        [(court_edge,court_start,court_z),(frontage_x,court_start,court_z+.12),
         (frontage_x,29.62,court_z+.12),(court_edge,29.62,court_z)], thickness=7.5))

    _south_footway(new,result,south_edge,frontage_x,library_rails)
    # The old Povo 2 yard cut a rectangle out of the Povo 1 lower plaza.
    result.append(('exterior_registered_povo1_plaza_rejoin',
                   (24.,-22.02,3.78),(30.82,-15.88,4.),'exterior_paving'))
    # The same obsolete excavation also cut the bridge apron beside Povo 1.
    # Close the remaining rectangle between the glazed facade and the paving.
    result.append(('exterior_registered_povo1_bus_side_infill',
                   (11.08,-20.,3.78),(24.,-15.88,4.),'exterior_paving'))
    # Clear old context ground above/beside the rebuilt road surface.
    hole=((-23,ROAD_CENTRE-half-WALK_WIDTH,2.7),(50,PAVEMENT_EDGE,10.))
    kept=[]
    for box in result:
        kept.extend(subtract_box(box,hole) if box[0].startswith('exterior_') and not box[0].startswith(('exterior_p2_entry_', 'exterior_abandoned_bus_')) else [box])
    result[:]=kept
    ext['meshes'].extend(new)
    ext['collision_meshes'].extend(copy.deepcopy(
        [mesh for mesh in new if mesh['material']!='exterior_marking']))
    trim_carriageways(ext)
    # Grass slopes from the footway to the outside of the terrace grate, with
    # a real break for the exit stair. Closed earth prisms carry collision.
    runs=[(8.5,20.5),(23.,49.3)]
    terrace_end=p['gardens']['garden'][0]

    def bank_toe(x):
        # Retain the lowest part of the drop at the grate. Across the -1
        # corridor frontage this leaves a 3 m rise over the 5 m planted bank.
        blend=min(1.,max(0.,(34.-x)/(34.-terrace_end)))
        return .4+blend*max(0.,verge_grade(x)-3.4)

    def bank_grade(x,y):
        road_z=verge_grade(x)
        boundary = _edge_at_x(north_edge,x)[1]
        return road_z+(bank_toe(x)-road_z)*(y-boundary)/(GRATE-boundary)

    for run,(a,b) in enumerate(runs):
        count=math.ceil(b-a)
        stations=sorted({a+(b-a)*i/count for i in range(count+1)} |
                        {x for x in (22.,terrace_end,32.,34.,46.,49.3) if a<x<b})
        for i,(x0,x1) in enumerate(zip(stations,stations[1:])):
            footprint=[(x0,_edge_at_x(north_edge,x0)[1]),(x1,_edge_at_x(north_edge,x1)[1]),(x1,GRATE),(x0,GRATE)]
            top=[verge_grade(x0),verge_grade(x1),bank_toe(x1),bank_toe(x0)]
            earth=_hexa(f'exterior_registered_grass_{run}_{i}',footprint,[-3.42]*4,top,'exterior_grass')
            ext['meshes'].append(earth);ext['collision_meshes'].append(copy.deepcopy(earth))
            if x0<34.:
                curb=prism(f'exterior_registered_bank_toe_{run}_{i}',
                    [(x0,GRATE-.14,top[3]),(x1,GRATE-.14,top[2]),
                     (x1,GRATE,top[2]),(x0,GRATE,top[3])],
                    material='exterior_concrete',thickness=1.)
                ext['meshes'].append(curb);ext['collision_meshes'].append(copy.deepcopy(curb))
    # One bush, approximately five metres from the right edge of the UP stair,
    # five metres long and the full width of the grass strip, follows its grade.
    a,b=28.,33.
    ext['meshes'].extend(_shrub_leaves(
        'exterior_registered_bush', (a,7.,b,GRATE), bank_grade, (7,7)))
    fences=[];barriers=[]
    for i,(a,b) in enumerate(runs):
        _fence(fences,f'exterior_registered_grate_{i}',a,b,GRATE-.06,lambda x:.4,0)
        barriers.extend(_barrier(f'exterior_registered_grate_barrier_{i}',a,b,GRATE-.06,lambda x:.4,0,[a,b]))
    ext['meshes'].extend(fences);ext['collision_meshes'].extend(barriers)
    # UP retains its southward ascent and exit-door alignment, with its upper
    # landing on the pavement instead of the former opening in the road.
    g=p['gardens'];z=.4;high=4.;count=20;run=GRASS_WIDTH/count;cx=21.75
    path=[[21.85,GRATE+TERRACE_WIDTH/2,z],[cx,GRATE+.15,z]]
    for i in range(count):
        y=GRATE-(i+1)*run;h=z+(high-z)*(i+1)/count
        add('up_step_'+str(i),(20.5,y,h-.16),(23.,y+run,h),'floor_grating')
        path.append([cx,y+run/2,h])
    add('up_top',(20.5,PAVEMENT_EDGE-1.1,4.12-.22),(23.,PAVEMENT_EDGE,4.12),'floor_terrace')
    path.append([cx,PAVEMENT_EDGE-.55,4.12])
    rails=p['stairs']['rails'];rails[:]=[r for r in rails if not r['name'].startswith(('drawio_up_', 'p2_roadside_'))]
    for x in (20.5,23.):railing(add,rails,'registered_up_'+str(x),(x,GRATE,z),(x,PAVEMENT_EDGE,high))
    # Guard the drop along the sidewalk and return around the garden corner.
    for i, (left, right) in enumerate(((8.5,20.5),(23.,32.),(32.,46.),(46.,garden_end))):
        railing(add, rails, f'registered_street_guard_{i}',
                (left, _edge_at_x(north_edge,left)[1]+.045, verge_grade(left)),
                (right, _edge_at_x(north_edge,right)[1]+.045, verge_grade(right)))
    garden_rail = garden_end+.035
    corner = (garden_rail, GRATE, back[0][2])
    railing(add, rails, 'registered_corner_guard_west',
            (garden_rail, edge[0][1]+.045, edge[0][2]), corner)
    landing = (garden_rail, front_end, court_z+.12)
    railing(add, rails, 'registered_corner_guard_slope', corner, landing)
    railing(add, rails, 'registered_corner_guard_landing', landing,
            (garden_rail, court_start, court_z))
    railing(add, rails, 'registered_corner_guard_forecourt',
            (garden_rail, court_start, court_z), (garden_rail, court_end, court_z))
    g.update(up_stair=[20.5,PAVEMENT_EDGE,23.,GRATE],up_top=[20.5,PAVEMENT_EDGE-1.1,23.,PAVEMENT_EDGE],
             street_garden=[8.5,PAVEMENT_EDGE,49.3,GRATE])
    g['routes']['up']=path
    yard=p['additions']['yard'];yard.update(outdoor_path=path,top_path=[path[-1]])
    yard['routes']['up']=path
    p['drawio_entrance']['areas']['up']=g['up_stair']
    p['landscape_registration']=dict(grass_runs=runs,grass_north=[PAVEMENT_EDGE,GRATE],
        bush=[28.,7.,33.,GRATE],pavement_boundary=north_edge,
        grate_north=GRATE-.06,up_stair=g['up_stair'])


def _south_footway(meshes,boxes,edge,frontage_x,rails):
    """Join continuous paving to the planting retaining wall and rail."""
    inner_north = WALL_Y[1]
    split = 52.
    verge_edge = [*(v for v in edge if v[0]<split),_edge_at_x(edge,split)]

    def inside_grade(x):
        if x>=24.:
            return grass_z(x)
        # Join the existing lower Povo 1 apron at the same crossfall.
        road = 3.12+min(1.,max(0.,(x+23.)/45.))
        return 4.+(road-4.)*(inner_north+20.)/12.

    for i,(a,b) in enumerate(zip(verge_edge,verge_edge[1:])):
        # Join the lower apron to the planting retaining edge.
        # The measured central run is already filled by the widened walk.
        top = [(a[0],inner_north,inside_grade(a[0])),(b[0],inner_north,inside_grade(b[0])),
               (b[0],b[1],b[2]-.12),(a[0],a[1],a[2]-.12)]
        for j,indices in enumerate(((0,1,2),(0,2,3))):
            slab = prism(f'exterior_registered_library_verge_{i}_{j}',
                         [top[k] for k in indices],'exterior_paving')
            if slab:
                meshes.append(slab)
    # Fill between the library upper landing and the two joined sidewalks.
    corner = [_edge_at_x(edge,split),*(v for v in edge if split<v[0]<frontage_x),
              _edge_at_x(edge,frontage_x)]
    for i,(a,b) in enumerate(zip(corner,corner[1:])):
        meshes.append(prism(f'exterior_registered_south_landing_{i}',
            [(a[0],-13.,7.6),(b[0],-13.,7.6),b,a], 'exterior_concrete'))

    def add(name,lo,hi,material):
        boxes.append(('exterior_library_'+name,tuple(lo),tuple(hi),material))

    rails[:] = [rail for rail in rails if not rail['name'].startswith('library_street_fence_')]
    # Leave the forecourt access and the bus body clear of the street rail.
    for run,(first,last) in enumerate(((8.5,21.),(28.,split))):
        line = [_edge_at_x(edge,first),*(v for v in edge if first<v[0]<last),_edge_at_x(edge,last)]
        # Seat the posts on the verge so the diagonal clip panels do not
        # project into the measured walking width.
        line = [(x,WALL_Y[1]-.1 if x>=24. else y-.15,z-.12) for x,y,z in line]
        for i,(a,b) in enumerate(zip(line,line[1:])):
            railing(add,rails,f'library_street_extension_{run}_{i}',a,b,height=1.1)


def _shrub_leaves(name, bounds, grade, cells, *, seed=20261107, radius=.44, inset=.11):
    """Layer textured leaves in irregular clusters within a planting bed."""
    west,south,east,north=bounds
    columns,rows=cells
    rng = random.Random(seed)
    foliage = [dict(name=f'{name}_{shade}', vertices=[], faces=[],
                    uvs=[], material='exterior_shrub_leaf'+suffix)
               for shade, suffix in enumerate(('_dark', '', '_light'))]
    for ix in range(columns):
        for iy in range(rows):
            cx = west + (ix+.5)*(east-west)/columns + rng.uniform(-.12,.12)
            cy = south + (iy+.5)*(north-south)/rows + rng.uniform(-.12,.12)
            for _ in range(42):
                angle = rng.uniform(0, math.tau)
                radial = math.sqrt(rng.random())*radius
                x = cx + radial*math.cos(angle)
                y = cy + radial*math.sin(angle)
                if not (west+inset < x < east-inset and south+inset+.04 < y < north-inset):
                    continue
                z = grade(x,y) + rng.uniform(.24,.90)*math.sqrt(1-(radial/.55)**2)
                length = rng.uniform(.05,.105)
                dx, dy = length*math.cos(angle), length*math.sin(angle)
                bend = rng.uniform(-.035,.035)
                mesh = rng.choices(foliage, (5, 5, 2))[0]
                first = len(mesh['vertices'])
                side_tilt = rng.uniform(-.028,.028)
                mesh['vertices'].extend(((x-dx,y-dy,z-bend),
                    (x-dy*.48,y+dx*.48,z+side_tilt), (x+dx,y+dy,z+bend),
                    (x+dy*.48,y-dx*.48,z-side_tilt), (x,y,z+.018)))
                mesh['uvs'].extend(((.5,.04),(.04,.48),(.5,.96),(.96,.48),(.5,.48)))
                mesh['faces'].extend((first+i,first+(i+1)%4,first+4) for i in range(4))
    return foliage


def _extend_garden_exit(result,ext,p,add):
    """Connect the lower internal corridor to the garden west edge at N15."""
    g=p['gardens'];z=g['garden_z'];north=g['garden'][3]
    corridor=[20.75,13.5,31.8,21.3]
    corridor_parts=[[20.75,13.5,23.75,21.3],[22.25,13.5,31.8,16.5]]
    obsolete=('p2_parking_garden_door_', 'p2_aligned_garden_office_approach',
        'p2_aligned_garden_approach_wall_', 'p2_aligned_garden_approach_ceiling')
    result[:]=[b for b in result if not b[0].startswith(obsolete)]
    # The approved extension follows the existing W-21 corridor, turns once
    # at N15, and reaches the garden. Carve only below the retained -1 floor.
    pieces=[[20.75,13.5,23.75,21.4],[23.75,13.5,31.8,16.5]]
    holes=[((a,b,z-.23),(c,d,-.1)) for a,b,c,d in pieces]
    result[:]=_carve_context(result,ext,holes)
    for hole in holes:
        result[:]=[part for box in result for part in
            (subtract_box(box,hole) if box[0].startswith('p2_parking_rebuilt_wall_8') else [box])]
    portal=((31.60,14.15,z-.01),(31.90,15.85,z+2.25))
    result[:]=[part for box in result for part in
        (subtract_box(box,portal) if box[0]=='p2_aligned_garden_wall_west' else [box])]
    # The old eastward garden spur has no room entrances. Close its junction
    # so the usable route is the approved single L rather than a second branch.
    add('garden_old_spur_seal',(23.9,21.3,z),(24.1,23.3,-.1))
    add('garden_old_exit_seal',(34.4,21.3,z),(34.6,23.3,-.1))
    add('garden_north_gap_seal',(34.5,north,z-.22),(37.5,north+.16,4.),'exterior_concrete')
    for i,(a,b,c,d) in enumerate(pieces):
        add('garden_exit_floor_'+str(i),(a,b,z-.22),(c,d,z),'floor_p2_tile')
        add('garden_exit_ceiling_'+str(i),(a,b,-.17),(c,d,-.1),'ceiling_panel')
    add('garden_exit_west',(20.59,13.34,z-.22),(20.75,21.3,-.1))
    add('garden_exit_south',(20.75,13.34,z-.22),(31.8,13.5,-.1))
    add('garden_exit_inner_east',(23.75,16.5,z),(23.91,21.3,-.1))
    add('garden_exit_inner_north',(23.75,16.5,z),(31.64,16.66,-.1))
    for i,(sign,y) in enumerate(((-1,14.15),(1,15.85))):
        add('garden_exit_jamb_'+str(i),(31.75,y-.025,z),(31.85,y+.025,z+2.25),'window_frame')
        add('garden_exit_interactive_leaf_'+str(i),(31.84,y-.024,z+.025),
            (32.65,y+.024,z+2.18),'door_black')
        a,b=sorted((15.,y))
        p['repair_doors'].append(dict(id='p2_registered_garden_exit_'+str(i),kind='exit',
            bounds=[[31.776,a+.018,z+.025],[31.824,b-.018,z+2.18]],
            pivot=[31.8,y,z],reverse=sign!=1,
            material='materials/trento/povo/campus/door_black.vmat'))
    add('garden_exit_head',(31.75,14.1,z+2.2),(31.85,15.9,z+2.25),'window_frame')
    route=[[22.25,26.8,z],[22.25,15.,z],[31.8,15.,z],[33.3,15.,z]]
    for path in p['parking']['routes']:
        if any(pt[0]>34.5 for pt in path['points']):
            path['points']=[path['points'][0],[22.25,24.85,z],*route[1:]]
    g['routes']['office_exit']=route
    g['routes']['garden']=[*g['routes']['garden'][:3],[33.3,north-1,z],[33.3,15.,z]]
    for path in p['basement_rebuild']['routes']:
        if path['id']=='minus2_garden_exit':path['points']=list(route)
    for floor in p['basement_rebuild']['levels']:
        if floor['floor']==-2:
            for key in ('areas','floor_pieces'):
                floor[key]=[[a,b,min(c,24.),d] if b>=21.3 and d<=23.31 else [a,b,c,d]
                    for a,b,c,d in floor[key] if not (a>=24. and b>=21.3 and d<=23.31)]
                floor[key].extend(copy.deepcopy(corridor_parts))
    g['office_exit']=dict(corridor=corridor,corridor_parts=corridor_parts,door_centre=[31.8,15.,z],clear_width=1.7,
        outward_direction=[1.,0.,0.],former_side_opening='Sealed')
    g['excavations']=[h for h in g['excavations'] if h[0][0]!=34.5]
    g['excavations'].extend(holes)
    yard=p['additions']['yard'];yard['routes']=g['routes']
    yard['audit_stations']=[dict(id='garden_'+str(i),point=q[:2]) for i,q in enumerate(g['routes']['garden'])]
    level=next(l for l in p['levels'] if l['floor']==-2)
    for station in level['audit_stations']:
        if station['id']=='garden_door':station['point']=[30.8,15.]
    level['audit_stations'].append(dict(id='garden_exit_threshold',point=[30.8,15.]))
