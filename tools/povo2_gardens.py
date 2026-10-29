"""Separate the street garden, -1 exit passage and -2 garden from the user sketch."""
import hashlib
import json

try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing


def extend(boxes, levels, root):
    cfg=json.loads((root/'config/povo2_gardens.json').read_text())
    spec=levels[1]['connection']['povo2']; ext=levels[0]['exterior']
    old=spec['additions']['yard']; z=cfg['passage_z']; low=cfg['garden_z']; high=cfg['street_z']
    result=[b for b in boxes if not b[0].startswith(('p2_yard_', 'p2_basement_exit_step_',
        'p2_basement_exit_stair_ceiling', 'p2_basement_exit_door_', 'p2_basement_exit_door',
        'p2_basement_left_return_', 'p2_basement_left_locker_', 'p2_basement_left_entry',
        'p2_basement_return_locker_', 'p2_basement_return_orange_band'))]
    spec['stairs']['rails']=[r for r in spec['stairs']['rails'] if not r['name'].startswith('p2_yard_')]
    def add(n,a,b,m='wall'):
        if not all(x<y for x,y in zip(a,b)):raise ValueError(n)
        prefix='p2_basement_gardens_' if n in ('passage','exit_turn','exit_corridor') else 'p2_gardens_'
        result.append((prefix+n,tuple(a),tuple(b),m))
    def slab(n,r,h,m='floor_p2_tile'):
        a,b,c,d=r;add(n,(a,b,h-.22),(c,d,h),m)
    # Close the obsolete raised-yard excavation, then cut the new routes.
    slab('old_yard_infill',old['bounds'],high,'exterior_paving')
    holes=[]
    for key,base in [('passage',z),('up_stair',z),('up_top',high),('down_landing',low),
                     ('garden',low),('street_garden',high),('street_side_walk',high)]:
        a,b,c,d=cfg[key]
        # Keep the road-side sloping sidewalk from x=57 eastward. The new
        # lower path runs beside it, rather than excavating its walking face.
        holes.append(((a-.12,b-.12,base-.25),(min(c+.12,57.0),d+.12,high+2.2)))
    for key in ('indoor_corridor','indoor_turn'):
        a,b,c,d=cfg[key];holes.append(((a-.12,b-.12,z-.25),(c+.12,d+.12,z+3.37)))
    approach=[34.5,12.5,cfg['garden'][0]+1.5,14.5]
    holes.append(((approach[0]-.12,approach[1]-.12,low-.25),
                  (approach[2]+.12,approach[3]+.12,low+2.7)))
    # Only exterior/context geometry is excavated: the -1 labs and parking remain intact.
    for hole in holes:
        result=[p for box in result for p in (subtract_box(box,hole)
            if box[0].startswith(('exterior_', 'p2_gardens_old_yard_infill','library_0_access')) else [box])]
    # Clip both rendered context meshes and their physical counterparts identically.
    try:
        from .build_povo_campus import subtract_polygon_box
    except ImportError:
        from build_povo_campus import subtract_polygon_box
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext.get(key,[]):
            verts=mesh['vertices']; bounds=([min(v[i] for v in verts) for i in range(3)],
                                           [max(v[i] for v in verts) for i in range(3)])
            relevant=[h for h in holes if all(bounds[0][i]<h[1][i] and bounds[1][i]>h[0][i] for i in range(3))]
            if not relevant:clipped.append(mesh);continue
            vv=[];ff=[]
            for face in mesh['faces']:
                polys=[[(tuple(verts[i]),(0,0)) for i in face]]
                for lo,hi in relevant:polys=[p for poly in polys for p in subtract_polygon_box(poly,lo,hi)]
                for poly in polys:
                    start=len(vv);vv.extend(v for v,_ in poly)
                    for j in range(1,len(poly)-1):ff.append((start,start+j,start+j+1))
            if ff:clipped.append(dict(mesh,vertices=vv,faces=ff,surface_clipped=True))
        ext[key]=clipped
    # Match the approved drawing: exit faces south, UP ahead, passage/DOWN east.
    slab('passage',cfg['passage'],z)
    a,b,c,d=cfg['indoor_corridor'];ta,tb,tc,td=cfg['indoor_turn']
    slab('exit_corridor',cfg['indoor_corridor'],z)
    slab('exit_turn',cfg['indoor_turn'],z)
    add('exit_wall_west',(a-.1,b,z),(a,tb,z+3.35))
    add('exit_wall_east',(c,b,z),(c+.1,td,z+3.35))
    add('exit_wall_turn_south',(ta,tb-.1,z),(a,tb,z+3.35))
    add('exit_wall_turn_north',(ta,td,z),(c,td+.1,z+3.35))
    slab('exit_ceiling',cfg['indoor_corridor'],z+3.35,'ceiling_panel')
    slab('exit_ceiling_turn',cfg['indoor_turn'],z+3.35,'ceiling_panel')
    for xx in (a,c-.05):add('exit_door_jamb_'+str(xx),(xx,b-.05,z),(xx+.05,b+.05,z+2.25),'metal_dark')
    add('exit_door_head',(a,b-.05,z+2.2),(c,b+.05,z+2.25),'metal_dark')
    # Join the far left turn to the existing laboratory corridor, preserving rooms.
    join=((-2.6,tb+.25,z-.01),(-2,tb+2.25,z+2.25))
    result=[p for box in result for p in (subtract_box(box,join)
        if box[0].startswith('p2_basement_') and box[3] in ('wall','window_frame') else [box])]
    add('old_exit_spur_infill',(27.1,14.5,z),(27.3,18,z+3.35))
    slab('down_landing',cfg['down_landing'],z)
    slab('up_top',cfg['up_top'],high,'exterior_paving')
    slab('garden_floor',cfg['garden'],low)
    slab('street_garden_base',cfg['street_garden'],high,'exterior_paving')
    slab('street_side_walk',cfg['street_side_walk'],high+.12,'exterior_paving')
    # The existing entrance courtyard already occupies its registered footprint.
    a,b,c,d=cfg['garden']
    # A broad paved perimeter leaves the approach and lower stair landing clear.
    add('garden_lawn',(a+3,b+3,low),(c-3,d-2,low+.025),'floor_yard_grass')
    a,b,c,d=cfg['street_garden']
    add('street_lawn',(a+.15,b+1.5,high),(c-1.5,d-1.5,high+.025),'floor_yard_grass')
    rails=[]
    def rail(n,a,b):railing(add,rails,n,a,b)
    routes={}
    a,b,c,d=cfg['up_stair'];count=cfg['risers'];run=(d-b)/count
    up=[[34.5,10,z],[34.5,d+.5,z]]
    for i in range(count):
        y=d-(i+1)*run;h=z+(high-z)*(i+1)/count
        add(f'up_step_{i}',(a,y,h-.16),(c,y+run,h),'floor_grating')
        up.append([34.5,y+run/2,h])
    up.extend([[34.5,b-.5,high],[56.25,2.25,high],[56.25,8.55,high],
               [56.25,8.95,high+.12],[56.25,19.5,high+.12],
               [57.5,19.5,high+.12]])
    for x in (a,c):rail('up_side_'+str(x),(x,d,z),(x,b,high))
    a,b,c,d=cfg['down_stair'];run=(c-a)/count
    down=[[a-.5,10,z]]
    for i in range(count):
        x=a+i*run;h=z-(z-low)*(i+1)/count
        add(f'down_step_{i}',(x,b,h-.16),(x+run,d,h),'floor_grating')
        down.append([x+run/2,10,h])
    down.append([c+.45,10,low])
    for y in (b,d):rail('down_side_'+str(y),(a,y,z),(c,y,low))
    # The door, up flight and down flight are the only three open ends.
    a,b,c,d=cfg['passage']
    rail('passage_south',(cfg['up_stair'][2],b,z),(c,b,z))
    rail('passage_west',(a,b,z),(a,d,z))
    rail('passage_north',(cfg['indoor_corridor'][2],d,z),(c,d,z))
    # Retaining walls separate the three exterior levels, not the reference colours.
    a,b,c,d=cfg['garden']
    for name,lo,hi in [('east',(c,b,low-.22),(c+.18,d,high)),
                       ('south',(a,b-.18,low-.22),(c,b,z)),
                       ('west',(a-.18,cfg['down_stair'][3],low-.22),(a,d,high)),
                       ('north',(a,d,low-.22),(c,d+.18,high))]:add('retaining_'+name,lo,hi)
    for name,a0,b0 in [('east',(c+.2,b,high),(c+.2,d,high)),
                       ('west',(a-.2,cfg['down_stair'][3],high),(a-.2,d,high)),
                       ('north',(a,d+.2,high),(c,d+.2,high))]:rail('garden_guard_'+name,a0,b0)
    # Preserve the separately reconstructed -2 office exit at the garden edge.
    slab('office_garden_approach',approach,low)
    portal=((a-.3,12.65,low-.01),(a+.3,14.35,low+2.25))
    result=[p for box in result for p in (subtract_box(box,portal)
            if box[0].startswith('p2_gardens_retaining_west') else [box])]
    spec['stairs']['rails'].extend(rails)
    passage=[[34.5,29,z],[34.5,11.25,z],[34.5,10,z],[37.5,10,z]]
    indoor=[[-3.8,32.75,z],[34.5,32.75,z],[34.5,29,z]]
    garden_path=[[cfg['down_stair'][2]+.45,10,low],[54.5,10,low],
                 [54.5,18.5,low],[39.5,18.5,low],[39.5,12.5,low]]
    routes=dict(indoor=indoor,passage=passage,up=up,down=down,garden=garden_path,
                office_exit=[[34.8,13.5,low],[39.5,13.5,low]])
    yard=dict(bounds=cfg['garden'],z=low,user_floor=-2,
        audit_stations=[dict(id='garden_'+str(i),point=p[:2]) for i,p in enumerate(garden_path)],
        indoor_path=passage,outdoor_path=up,top_path=[up[-1]],down_path=down,routes=routes,
        status=cfg['status'],stair_axis=0)
    spec['additions']['yard']=yard
    spec['basement'].pop('yard',None)
    spec['basement']['exterior_passage']=cfg['passage']
    for key in ('left_return','left_locker','exit_cross'):spec['basement'].pop(key,None)
    spec['basement']['exit_corridor']=cfg['indoor_corridor']
    spec['basement']['exit_turn']=cfg['indoor_turn']
    basement=next(l for l in spec['levels'] if l['floor']==-1)
    for station in basement['audit_stations']:
        if station['id']=='exit_stair_approach':station['point']=[34.5,12.25]
        if station['id']=='left_exit_start':station['point']=[34.5,29]
        if station['id']=='locker_return':station['point']=[34.5,22]
    basement['audit_stations'].extend([dict(id='exit_far_turn',point=[34.5,32.75]),
                                      dict(id='exit_turn_join',point=[-1,32.75])])
    spec['gardens']=dict(cfg,routes=routes,excavations=holes)
    # Existing general paving audit must exempt the deliberately lowered/cut areas.
    ext['pavement_repairs']['garden_exclusions']=[[*lo[:2],*hi[:2]] for lo,hi in holes]
    spec['lights'].extend([[32,11.25,2.9],[45,11.25,3],[36,18,-.5],[56,18,-.5]])
    ext.setdefault('input_hashes',{}).update({s:hashlib.sha256((root/s).read_bytes()).hexdigest()
        for s in ('config/povo2_gardens.json',cfg['source'])})
    return result
