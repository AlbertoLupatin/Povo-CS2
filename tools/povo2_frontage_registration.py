"""Register the assembled Povo 2 interiors against one shared facade datum.

The historical construction passes use their original local coordinates. This
final export stage keeps that reconstruction reproducible while registering
geometry, doors, navigation, furniture and collision together. Dimensions are
fitted to the confirmed topology, not an independent measured survey.
"""
import copy
import math
import re
from .povo_room_fitout import subtract_box
from .povo_stairs import railing
from .povo2_roadside_closure import _hexa, _fence, _barrier, footway_z
from .build_povo_exterior import strip, joint

FACADE = 10.8
OFFSET = FACADE-2.
GRASS_WIDTH = 5.
TERRACE_WIDTH = 1.71
GRATE = FACADE-TERRACE_WIDTH
PAVEMENT_EDGE = GRATE-GRASS_WIDTH
ROAD_OFFSET = PAVEMENT_EDGE-(-.6)
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
    for room in ground['rooms']:
        if room['id'] in ROOMS:
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
            'exterior_user_fill_','exterior_p2_roadside_')
    result=[]
    for name,lo,hi,material in boxes:
        if name.startswith(remove):continue
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
                    elif suffix.startswith(('wall_south','window_')):
                        lo=(lo[0],lo[1]-OFFSET,lo[2]);hi=(hi[0],hi[1]-OFFSET,hi[2])
            if hi[2]<0 and name.startswith(('p2_parking_','p2_basement_')):
                if hi[1]<=FACADE:continue
                lo=(lo[0],max(lo[1],FACADE),lo[2])
            if name=='p2_aligned_garden_wall_road':hi=(hi[0],hi[1],.4)
        result.append((name,lo,hi,material))
    def add(name,lo,hi,material='wall'):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError(name)
        result.append(('p2_registered_'+name,tuple(lo),tuple(hi),material))
    add('parking_front',(-25,FACADE-.16,-3.42),(11,FACADE,-.1))
    # Extend the existing overhead bridge INSIDE the retained facade. Its
    # external span and the Povo 1 arrival never move.
    add('bridge_floor',(16.5,10,10.98),(20,10+OFFSET,11.2),'floor_p2_tile')
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
    _extend_garden_exit(result,ext,p,add)
    link['nav_seeds'].append([30.8,15.,-3.2])
    _road_and_landscape(result,ext,p,add)
    p['frontage_registration']=dict(facade_north=FACADE,interior_offset_north=OFFSET,
        grass_width=GRASS_WIDTH,grate_north=GRATE,pavement_edge_north=PAVEMENT_EDGE,
        road_offset_north=ROAD_OFFSET,road_width=6.,pavement_width=1.4,
        room_depth=cfg['ground_rooms'][0]['bounds'][3]-FACADE,
        source='User confirms all floors align; no protruding frontage',
        metric_status='Fitted to confirmed topology and approximate grass/bush dimensions; not surveyed',
        preserve='Internal room/corridor relationships and stair directions; Povo 1 and external bridge span')
    return result


def _carve_context(boxes,ext,holes):
    from .build_povo_campus import subtract_polygon_box
    result=[]
    for box in boxes:
        if not box[0].startswith('exterior_') or box[0].startswith('exterior_p2_entry_'):
            result.append(box);continue
        relevant=[h for h in holes if all(box[1][i]<h[1][i] and box[2][i]>h[0][i] for i in range(3))]
        parts=[box]
        for hole in relevant:parts=[p for b in parts for p in subtract_box(b,hole)]
        result.extend(parts)
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext[key]:
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


def _road_and_landscape(result,ext,p,add):
    # Rebuild the straight descending road and its western transition, removing
    # the obsolete stair excavation from the actual carriageway.
    road=re.compile(r'exterior_(?:road_[0-3](?:_|$)|footway_[0-3]_|road_joint_[0-2](?:_|$)|road_edge_[0-3](?:_|$))')
    for key in ('meshes','collision_meshes'):ext[key]=[m for m in ext[key] if not road.match(m['name']) and not m['name'].startswith('exterior_road_front_link')]
    points=[(58,-5,7.6),(50,-5+ROAD_OFFSET,7.6),(32,-5+ROAD_OFFSET,4.),(22,-5+ROAD_OFFSET,4.),
            (-23,-5+ROAD_OFFSET,3.),(-36,-12,3.)]
    new=[]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        new.append(strip(f'exterior_registered_road_{i}',a,b,6.,'exterior_asphalt'))
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
        for side in (-1,1):
            shift=side*3.7
            aa=(a[0]+nx*shift,a[1]+ny*shift,a[2]+.12)
            bb=(b[0]+nx*shift,b[1]+ny*shift,b[2]+.12)
            new.append(strip(f'exterior_registered_footway_{i}_{side}',aa,bb,1.4,'exterior_paving',.22))
    for i,(a,pivot,b) in enumerate(zip(points,points[1:],points[2:])):
        mesh=joint(f'exterior_registered_road_join_{i}',a,pivot,b,3.)
        mesh['material']='exterior_asphalt';new.append(mesh)
    # Restore the vacated road strip as planted ground, not extra carriageway.
    for i,(a,b) in enumerate(zip(points[1:-1],points[2:])):
        if a[1]!=b[1]:continue
        x0,x1=sorted((a[0],b[0]));z0,z1=footway_z(x0),footway_z(x1)
        new.append(_hexa(f'exterior_registered_old_road_ground_{i}',
            [(x0,-9.4),(x1,-9.4),(x1,-5+ROAD_OFFSET-4.4),(x0,-5+ROAD_OFFSET-4.4)],
            [-3.42]*4,[z0,z1,z1,z0],'exterior_grass'))
    # Clear old context ground above/beside the rebuilt road surface.
    hole=((-23,-5+ROAD_OFFSET-4.4,2.7),(50,PAVEMENT_EDGE,10.))
    kept=[]
    for box in result:
        kept.extend(subtract_box(box,hole) if box[0].startswith('exterior_') and not box[0].startswith('exterior_p2_entry_') else [box])
    result[:]=kept
    ext['meshes'].extend(new);ext['collision_meshes'].extend(copy.deepcopy(new))
    # Grass slopes from the footway to the outside of the terrace grate, with
    # a real break for the exit stair. Closed earth prisms carry collision.
    runs=[(8.5,20.5),(23.,49.3)]
    for run,(a,b) in enumerate(runs):
        count=math.ceil(b-a)
        for i in range(count):
            x0=a+(b-a)*i/count;x1=a+(b-a)*(i+1)/count
            footprint=[(x0,PAVEMENT_EDGE),(x1,PAVEMENT_EDGE),(x1,GRATE),(x0,GRATE)]
            top=[footway_z(x0),footway_z(x1),.4,.4]
            earth=_hexa(f'exterior_registered_grass_{run}_{i}',footprint,[-3.42]*4,top,'exterior_grass')
            ext['meshes'].append(earth);ext['collision_meshes'].append(copy.deepcopy(earth))
    # One bush, approximately five metres from the right edge of the UP stair,
    # five metres long and the full width of the grass strip, follows its grade.
    a,b=28.,33.
    bush=_hexa('exterior_registered_bush',[(a,PAVEMENT_EDGE),(b,PAVEMENT_EDGE),(b,GRATE),(a,GRATE)],
        [footway_z(a),footway_z(b),.4,.4],[footway_z(a)+1.,footway_z(b)+1.,1.4,1.4],
        'exterior_ginkgo_leaf_dark')
    ext['meshes'].append(bush)
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
    g.update(up_stair=[20.5,PAVEMENT_EDGE,23.,GRATE],up_top=[20.5,PAVEMENT_EDGE-1.1,23.,PAVEMENT_EDGE],
             street_garden=[8.5,PAVEMENT_EDGE,49.3,GRATE])
    g['routes']['up']=path
    yard=p['additions']['yard'];yard.update(outdoor_path=path,top_path=[path[-1]])
    yard['routes']['up']=path
    p['drawio_entrance']['areas']['up']=g['up_stair']
    p['landscape_registration']=dict(grass_runs=runs,grass_north=[PAVEMENT_EDGE,GRATE],
        bush=[28.,PAVEMENT_EDGE,33.,GRATE],grate_north=GRATE-.06,up_stair=g['up_stair'])


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
