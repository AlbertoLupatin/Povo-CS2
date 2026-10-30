"""Integrate the approved West Offices into the playable campus assembly.

Only the office block and its C7/C5 connections come from the full-plan review.
The existing research routes, locked doors and fixed stair/lift cores remain.
"""
import copy
import json
import re
from pathlib import Path

from .povo_room_fitout import subtract_box
from .povo2_basements import union_rectangles


def extend(boxes, levels, root=None):
    from .build_povo2_west_offices import build, subtract_rect, cut_openings
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    cfg = json.loads((root/'config/povo2_west_offices.json').read_text())
    layout = build(json.loads((root/cfg['baseline_layout']).read_text()), root)
    office = copy.deepcopy(layout['west_offices'])
    spec = next(l['connection']['povo2'] for l in levels if l.get('connection'))
    level = next(l for l in spec['levels'] if l['floor'] == -1)
    old_areas = copy.deepcopy(next(l['areas'] for l in spec['basement_rebuild']['levels'] if l['floor'] == -1))
    corridors = {c['id']: c['bounds'] for c in layout['corridors']}
    fp = office['footprint']; c7 = corridors['corridor_7']; bypass = corridors['c7_core_bypass']
    # C5 is extended only as far as the new office spine. The remainder of the
    # full-plan research wings is outside this integration.
    c5 = [20.5, corridors['corridor_5'][1], 25.5, 18.0]
    link = [fp[2], office['corridors'][0]['bounds'][1], 20.5, office['corridors'][0]['bounds'][3]]
    public = [c7, bypass, c5, link]
    # Keep the stair core intact, including its existing open south doorway.
    regions = [fp, *public]
    regions = [p for r in regions for p in subtract_rect(r, layout['core'])]
    prefix='p2_basement_cibio_office_0_'
    moving_desks={m[1] for n,lo,hi,material in boxes
                  if (m:=re.fullmatch(prefix+r'desk_(\d+)',n)) and lo[1]<c7[3]+.2}
    result = []
    for n,lo,hi,m in boxes:
        kit=re.search(r'_(?:desk(?:_leg)?|monitor|chair(?:_back)?)_(\d+)(?:_|$)',n)
        if n.startswith(prefix) and kit and kit[1] in moving_desks:
            lo=(lo[0],lo[1]+2.2,lo[2]);hi=(hi[0],hi[1]+2.2,hi[2])
        result.append((n,lo,hi,m))
    for a,b,c,d in regions:
        hole = ((a,b,.179),(c,d,3.501))
        result = [p for box in result for p in
                  (subtract_box(box,hole) if box[0] != 'p2_basement_lift_floor' and box[0].startswith(('p2_basement_', 'exterior_', 'library_0_access'))
                   else [box])]
    # The old two-room blockout's first lab overlaps C7 by 1.96 m. Retain its
    # north part and entrance; its south wall now follows C7's north edge.
    first = next(r for r in level['rooms'] if r['id'] == 'cibio_office_0')
    door_y=first['bounds'][1]+(first['bounds'][3]-first['bounds'][1])*first['door_fraction']
    first['bounds'][1] = c7[3]+.08
    first['footprint_local_metres'] = list(first['bounds'])
    first['door_fraction']=(door_y-first['bounds'][1])/(first['bounds'][3]-first['bounds'][1])
    new=[]
    def add(n,r,z0,z1,m):
        a,b,c,d=r[:4]
        if c-a>1e-7 and d-b>1e-7 and z1-z0>1e-7:
            new.append(('p2_basement_west_'+n,(a,b,z0),(c,d,z1),m))
    # New plates fill just the uncovered area; existing slab/ceiling plates
    # were removed from the same regions, so the finish never floats on tile.
    for i,r in enumerate(union_rectangles(regions)[0]):
        add('floor_'+str(i),r,.18,.4,'floor_wood' if r[1]<fp[3] else 'floor_p2_tile')
        add('ceiling_'+str(i),r,3.43,3.5,'ceiling_panel')
    # Public perimeter walls are omitted where they meet retained circulation.
    for i,(axis,fixed,lo,hi) in enumerate(union_rectangles(public)[1]):
        r=[fixed-.08,lo,fixed+.08,hi] if axis==0 else [lo,fixed-.08,hi,fixed+.08]
        parts=subtract_rect(r,layout['core'])
        for old in old_areas:
            # C7 takes precedence over the old lab's southern strip.
            if old[0] == -13.8 and old[1] == 18.5: continue
            parts=[p for part in parts for p in subtract_rect(part,old)]
        for j,p in enumerate(cut_openings(parts,office['public_portals'])):add(f'corridor_wall_{i}_{j}',p,.4,3.5,'wall')
    for i,r in enumerate(office['walls']):add('partition_'+str(i),r,.4,3.5,'wall')
    for i,r in enumerate(office['glazing']):
        add('glazing_'+str(i),r,.42,3.35,'reception_glass')
        axis=0 if r[2]-r[0] > r[3]-r[1] else 1
        # Slim metal perimeter frame and opaque horizontal privacy bands,
        # matching the photographed permanent glazed office partitions.
        for j,z in enumerate((.42,.72,1.02,1.32,1.62,3.32)):
            add(f'front_band_{i}_{j}',[r[0]-.004,r[1]-.004,r[2]+.004,r[3]+.004],z,z+(.025 if j in (0,5) else .12),'window_frame' if j in (0,5) else 'office_frost')
        for j,at in enumerate((r[axis+2],r[axis])):
            p=list(r);p[axis]=at-.018;p[axis+2]=at+.018
            add(f'front_jamb_{i}_{j}',p,.4,3.35,'window_frame')
    for i,o in enumerate(office['openings']):
        p,q=o['points'];r=[min(p[0],q[0])-.08,min(p[1],q[1])-.08,max(p[0],q[0])+.08,max(p[1],q[1])+.08]
        if o['status'].startswith('open '):continue
        add('door_head_'+str(i),r,2.65,3.5,'wall')
    # A small ceiling diffuser in each room and regularly along each passage.
    points=[]
    for room in office['rooms']:
        a,b,c,d=room['bounds'];points.append(((a+c)/2,(b+d)/2))
    for passage in office['corridors']:
        a,b,c,d=passage['bounds'];n=max(1,round(max(c-a,d-b)/4))
        points.extend((a+(c-a)*(i+.5)/n,(b+d)/2) if c-a>d-b else ((a+c)/2,b+(d-b)*(i+.5)/n) for i in range(n))
    for i,(x,y) in enumerate(points):
        add('fixture_'+str(i),[x-.3,y-.2,x+.3,y+.2],3.39,3.43,'light_diffuser')
        spec['lights'].append([x,y,3.25])
    # Deduplicate all party walls and avoid overlaps with retained structure.
    clean=[]
    for box in new:
        parts=[box]
        if box[3]=='wall':
            for other in result+clean:
                if other[3]=='wall':parts=[p for part in parts for p in subtract_box(part,(other[1],other[2]))]
        clean.extend(parts)
    a,b,c,d=spec['lift']['shaft']
    result.extend(p for box in clean for p in subtract_box(box,((a,b,.17),(c,d,3.8))))
    # The retained ladder platform starts 0.1 m inside its shaft. Bridge that
    # deliberate wall recess at the existing west-facing entrance.
    result.append(('p2_basement_west_lift_threshold',(a,15.4,.18),(a+.1,16.5,.4),'floor_p2_tile'))
    # Reuse the existing exterior excavation for polygon meshes as well.
    from .build_povo_campus import subtract_polygon_box
    for key in ('meshes','collision_meshes'):
        meshes=[]
        for mesh in levels[0]['exterior'].get(key,[]):
            vv=mesh['vertices'];vertices=[];faces=[]
            low=[min(v[i] for v in vv) for i in range(3)];high=[max(v[i] for v in vv) for i in range(3)]
            relevant=[r for r in regions if low[0]<r[2]+.1 and high[0]>r[0]-.1 and low[1]<r[3]+.1 and high[1]>r[1]-.1 and low[2]<3.52 and high[2]>.17]
            if not relevant:
                meshes.append(mesh);continue
            for face in mesh['faces']:
                polygons=[[(tuple(vv[i]),(0,0)) for i in face]]
                for a,b,c,d in relevant:
                    polygons=[p for poly in polygons for p in subtract_polygon_box(poly,(a-.1,b-.1,.17),(c+.1,d+.1,3.52))]
                for poly in polygons:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+j,start+j+1) for j in range(1,len(poly)-1))
            if faces:meshes.append(dict(mesh,vertices=vertices,faces=faces,surface_clipped=True))
        levels[0]['exterior'][key]=meshes
    office.update(status='Integrated into the playable campus',z=.4,source_hashes=layout['source_hashes'])
    spec['west_offices']=office
    integrated_rooms=[]
    for room in office['rooms']:
        # Preserve the existing room record format consumed by signs/radar.
        r=copy.deepcopy(room);r.update(playable=True,footprint_local_metres=list(r['bounds']))
        a,b,c,d=r['bounds'];p,q=r['door']['points'];x,y=(p[0]+q[0])/2,(p[1]+q[1])/2
        if abs(p[1]-q[1])<1e-6:
            r.update(door_side='u_min' if abs(y-b)<abs(y-d) else 'u_max',door_fraction=(x-a)/(c-a),door_width_metres=abs(q[0]-p[0]))
        else:r.update(door_side='v_min' if abs(x-a)<abs(x-c) else 'v_max',door_fraction=(y-b)/(d-b),door_width_metres=abs(q[1]-p[1]))
        integrated_rooms.append(r)
    office['rooms']=integrated_rooms
    floor = next(l for l in spec['basement_rebuild']['levels'] if l['floor']==-1)
    floor['areas'].extend([list(r) for r in regions])
    # Routes follow C7 and the fitted bypass rather than passing through W02.
    y7=(c7[1]+c7[3])/2;yb=(bypass[1]+bypass[3])/2
    detour=[[19.2,17.15,.4],[19.2,yb,.4],[10.2,yb,.4],[10.2,y7,.4],[-3.05,y7,.4]]
    for route in spec['basement_rebuild']['routes']:
        if route['id']=='minus1_stair_to_labs':route['points']=[[19.2,22,.4],*detour,[-3.05,63,.4]]
        elif route['id']=='minus1_labs_to_exit':route['points']=[[-3.05,63,.4],*reversed(detour),[34.5,17.15,.4],[34.5,10,.4]]
    for station in level['audit_stations']:
        if station['id']=='right_turn_from_stairs':station['point']=[-3.8,y7]
    spec['gardens']['routes']['indoor']=[*reversed(detour),[34.5,17.15,.4],[34.5,16.25,.4]]
    spec['additions']['yard']['routes']['indoor']=spec['gardens']['routes']['indoor']
    office['connection_route']=detour
    routes=[]
    for room in office['rooms']:
        a,b,c,d=room['bounds'];p,q=room['door']['points'];x,y=(p[0]+q[0])/2,(p[1]+q[1])/2
        nx,ny={'u_min':(0,-1),'u_max':(0,1),'v_min':(-1,0),'v_max':(1,0)}[room['door_side']]
        routes.append(dict(id=room['id']+'_entry',points=[[x+nx*.7,y+ny*.7,.4],[x,y,.4],[x-nx*.7,y-ny*.7,.4],[(a+c)/2,(b+d)/2,.4]]))
    for passage in office['corridors']:
        a,b,c,d=passage['bounds']
        points=[[a+.65,(b+d)/2,.4],[c-.65,(b+d)/2,.4]] if c-a>d-b else [[(a+c)/2,b+.65,.4],[(a+c)/2,d-.65,.4]]
        routes.append(dict(id='west_'+passage['id'],points=points))
    routes.append(dict(id='west_stair_to_spine',points=[[19.2,22,.4],[19.2,17.15,.4],[24.2,17.15,.4],[24.2,9.2,.4],[-13.5,9.2,.4]]))
    office['routes']=routes
    spec['basement_rebuild']['routes'].extend(routes)
    return result
