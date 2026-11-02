"""Replace the local -1 entrance with the user's corrected Draw.io arrangement.

This is a regional replacement after the legacy basement passes. No old east
arm, terrace detour or stair remains inside the replaced area. Other rooms,
the registered main core and the existing -2 garden are retained.
"""
import base64
import hashlib
import math
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from .povo_room_fitout import subtract_box
from .povo_stairs import railing

SOURCE='data/reference/user_feedback/2026-10-31/east_entrance_edited.drawio'


def read_layout(root):
    doc=ET.fromstring((root/SOURCE).read_text(encoding='utf-8'))
    page=doc.find('diagram')
    model=page[0] if len(page) else ET.fromstring(urllib.parse.unquote(
        zlib.decompress(base64.b64decode(page.text),-15).decode()))
    cells={c.get('id'):c for c in model.iter('mxCell')}
    def rect(id):
        g=cells[id].find('mxGeometry')
        x,y,w,h=[float(g.get(k,'0')) for k in ('x','y','width','height')]
        if w<=0 or h<=0:raise ValueError('Invalid Draw.io geometry: '+id)
        return [8+x/30,32-(y+h)/30,8+(x+w)/30,32-y/30]
    ids=dict(c5='c23',e1='c25',e2='c26',terrace='c19',up='c17',down='c18',restricted='c27')
    raw={name:rect(id) for name,id in ids.items()}
    # Tiny drag offsets (4-14 cm) must not create cracks between shared walls.
    # Keep the existing office facade / terrace datum; retain the edited far
    # edge and north end. These snaps are recorded, not treated as a survey.
    c5=[20.5,2.,23.1,raw['c5'][3]]
    areas=dict(c5=c5,e1=[c5[2],raw['e1'][1],raw['e1'][2],raw['e1'][3]],
               e2=[c5[2],2.,raw['e2'][2],raw['e2'][3]],terrace=raw['terrace'],
               up=raw['up'],down=raw['down'],restricted=[20.5,c5[3],23.1,26.])
    return dict(source=SOURCE,source_sha256=hashlib.sha256((root/SOURCE).read_bytes()).hexdigest(),
        raw=raw,areas=areas,snapping='Shared office facade E20.5, corridor width 2.6 m and south facade N2 retained; edited north/east/stair edges follow Draw.io')


def extend(boxes,levels,root):
    from .build_povo_campus import subtract_polygon_box
    from .build_povo2_west_offices import subtract_rect
    from .solid_mesh import subtract as subtract_solid
    layout=read_layout(root);a=layout['areas']
    spec=levels[1]['connection']['povo2'];ext=levels[0]['exterior']
    c5,e1,e2,terrace,up,down=[a[k] for k in ('c5','e1','e2','terrace','up','down')]
    z,low,high=.4,-3.2,4.;cx=(c5[0]+c5[2])/2;ty=(terrace[1]+terrace[3])/2;walk_x=22.
    old_rail=('up_side_','down_side_','passage_south','passage_west','passage_north',
              'p2_repair_entrance_stair_edge','p2_repair_entrance_slope_edge')
    def obsolete(n):
        return n.startswith(('p2_gardens_up_step_','p2_gardens_down_step_','p2_gardens_up_top',
            'p2_gardens_down_landing','p2_basement_gardens_passage',
            'p2_gardens_passage_','p2_repair_entrance_stair_edge','p2_repair_entrance_slope_edge',
            'p2_basement_repair_terrace_end_west')) or any(
            n.startswith('p2_gardens_'+r) for r in ('up_side_','down_side_'))
    result=[b for b in boxes if not obsolete(b[0])]
    rails=spec['stairs']['rails']
    rails[:]=[r for r in rails if not r['name'].startswith(old_rail)]
    ext['meshes']=[m for m in ext['meshes'] if not m['name'].startswith('exterior_p2_garden_slope_')]
    ext['collision_meshes']=[m for m in ext['collision_meshes'] if not m['name'].startswith('exterior_p2_garden_slope_')]
    # Preserve the sealed end of the old restricted corridor at N18, but remove
    # its former accessible southern section and the east arm entirely.
    # The terrace is one strip along the facade from its west end; the old
    # entrance's end wall at E20.2 and the ground over the west half go.
    indoor_holes=[((20.36,terrace[1]-.16,.17),(33.14,c5[3]+.1,3.77)),
            ((33.14,terrace[1]-.16,.17),(35.9,17.9,3.77)),
            ((terrace[0]-.16,terrace[1]-.16,.17),(20.36,terrace[3]-.08,3.77))]
    lower_path=[down[2],down[1],down[2]+3.,10.]
    excavations=[((up[0]-.16,up[1]-1.5,.17),(up[2]+.16,up[3]+.15,6.2)),
        ((down[0]-.12,down[1]-.12,low-.25),(down[2]+.5,down[3]+.12,3.77)),
        ((lower_path[0]-.12,lower_path[1]-.12,low-.25),(lower_path[2]+.12,lower_path[3]+.12,4.3))]
    def carve(hole,select):
        nonlocal result
        result=[p for b in result for p in (subtract_box(b,hole) if select(b) else [b])]
    local=lambda b:b[0].startswith(('p2_basement_','p2_gardens_','exterior_','library_0_access')) and not b[0].startswith(('p2_basement_new_core_','p2_basement_core_door_'))
    for h in indoor_holes:carve(h,local)
    for h in excavations:carve(h,lambda b:b[0].startswith(('exterior_','p2_gardens_','library_0_access')))
    # Clear a walking opening where the lower paved approach meets the retained
    # garden's south retaining wall. This preserves its accepted footprint.
    carve(((down[2]+.6,8.3,low-.01),(down[2]+2.4,9.1,low+2.35)),
          lambda b:b[0].startswith('p2_gardens_retaining_south'))
    holes=indoor_holes+excavations
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext[key]:
            vv=mesh['vertices'];lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
            relevant=[h for h in holes if all(lo[i]<h[1][i] and hi[i]>h[0][i] for i in range(3))]
            if not relevant:clipped.append(mesh);continue
            if mesh['name'].startswith('exterior_road') and not mesh.get('surface_clipped'):
                pieces=[mesh]
                for h in relevant:pieces=[p for part in pieces for p in subtract_solid(part,h)]
                clipped.extend(dict(p,name=mesh['name']+'_drawio_'+str(i)) for i,p in enumerate(pieces))
                continue
            vertices=[];faces=[]
            for face in mesh['faces']:
                polys=[[(tuple(vv[i]),(0,0)) for i in face]]
                for h in relevant:polys=[p for poly in polys for p in subtract_polygon_box(poly,*h)]
                for poly in polys:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+i,start+i+1) for i in range(1,len(poly)-1))
            if faces:clipped.append(dict(mesh,vertices=vertices,faces=faces,surface_clipped=True))
        ext[key]=clipped
    def box(name,lo,hi,mat='wall'):
        if any(v>=w for v,w in zip(lo,hi)):raise ValueError(name)
        result.append(('p2_basement_drawio_'+name,tuple(lo),tuple(hi),mat))
    def plate(name,r,height,mat='floor_p2_tile'):
        box(name,(r[0],r[1],height-(.07 if mat=='ceiling_panel' else .22)),(r[2],r[3],height),mat)
    def wall(name,axis,fixed,start,end,gaps=()):
        edges=[start]
        for centre,width in sorted(gaps):edges.extend((centre-width/2,centre+width/2))
        edges.append(end)
        for i in range(0,len(edges),2):
            if edges[i+1]-edges[i]<1e-6:continue
            lo=[fixed-.08,edges[i],z] if axis==0 else [edges[i],fixed-.08,z]
            hi=[fixed+.08,edges[i+1],3.5] if axis==0 else [edges[i+1],fixed+.08,3.5]
            box(name+'_'+str(i),lo,hi)
        for i,(centre,width) in enumerate(gaps):
            lo=[fixed-.08,centre-width/2,2.65] if axis==0 else [centre-width/2,fixed-.08,2.65]
            hi=[fixed+.08,centre+width/2,3.5] if axis==0 else [centre+width/2,fixed+.08,3.5]
            box(name+'_header_'+str(i),lo,hi)
    def sealed(name,centre,axis,width):
        lo=[centre[0]-.04,centre[1]-.04,z];hi=[centre[0]+.04,centre[1]+.04,2.65]
        lo[1-axis]-=width/2;hi[1-axis]+=width/2
        box(name,lo,hi,'door_black')
    doors=[d for d in spec['repair_doors'] if not d['id'].startswith(('p2_c5_terrace_','p2_wi1_public_','p2_c7_exit_','p2_garden_exit_'))]
    def door(name,centre,axis,width,park_sign=1):
        across=1-axis
        for i,sign in enumerate((-1,1)):
            pivot=[*centre,z];pivot[across]+=sign*width/2
            lo=[centre[0]-.024,centre[1]-.024,z+.025];hi=[centre[0]+.024,centre[1]+.024,z+2.18]
            lo[across]=min(centre[across],pivot[across])+.018;hi[across]=max(centre[across],pivot[across])-.018
            doors.append(dict(id='p2_'+name+'_'+str(i),kind='glass',bounds=[lo,hi],pivot=pivot,
                reverse=sign!=park_sign if axis==0 else -sign!=park_sign,material='materials/trento/povo/campus/window_glass.vmat'))
            # Matching parked source leaf; entity extraction removes this body.
            p=list(pivot);q=list(pivot);p[2]+= .025;q[2]+=2.18
            p[across]-=.024;q[across]+=.024
            p[axis]+=min(park_sign*.04,park_sign*width/2);q[axis]+=max(park_sign*.04,park_sign*width/2)
            box(name+'_interactive_leaf_'+str(i),p,q,'window_glass')
    floor_c5=[20.28,c5[1],c5[2],c5[3]]
    plate('c5_floor',floor_c5,z);plate('c5_ceiling',floor_c5,3.5,'ceiling_panel')
    for key,r in (('e1',e1),('e2',e2)):
        plate(key+'_floor',r,z);plate(key+'_ceiling',r,3.5,'ceiling_panel')
    plate('restricted_floor',a['restricted'],z);plate('restricted_ceiling',a['restricted'],3.5,'ceiling_panel')
    # C5 joins C7 full width at N15.23..18; WI1 keeps its glass door.
    wall('c5_west',0,20.43,2.,15.23,[(9.260619977,2.)])
    wall('c5_east',0,c5[2],2.,26.,[(9.1,1.)])
    wall('rooms_east',0,e2[2],2.,e1[3])
    wall('rooms_partition',1,e1[1],c5[2],e1[2])
    wall('rooms_north',1,e1[3],c5[2],e1[2])
    wall('facade',1,2.,20.36,e2[2],[(21.85,1.9)])
    wall('c5_north',1,c5[3],c5[0],c5[2],[(cx,1.65)])
    wall('restricted_north',1,26.,c5[0],c5[2])
    sealed('c5_north_closed',(cx,c5[3]),1,1.65)
    sealed('e2_closed',(c5[2],9.1),0,1.)
    door('c5_terrace',(21.85,2.),1,1.8);door('wi1_public',(20.5,9.260619977),0,1.9)
    plate('terrace',terrace,z,'floor_terrace')
    plate('up_top',(up[0],up[1]-1.5,up[2],up[1]),high,'floor_p2_tile')
    # Old stair opening is closed with soil beside, not inside, the new rooms.
    box('old_up_infill',(31.96,2.75,-3.42),(35.75,8.75,4.),'floor_yard_grass')
    # Paved lower landing and narrow approach to the already accepted garden.
    plate('down_landing',(down[2],down[1],down[2]+3.,down[3]),low,'floor_terrace')
    plate('garden_approach',(down[2]-.12,down[3],down[2]+3.12,10.12),low,'floor_terrace')
    plate('garden_join',(down[2]-.12,8.75,down[2]+3.12,10.2),low,'floor_terrace')
    for side,x in (('west',up[0]-.16),('east',up[2])):
        box('up_retaining_'+side,(x,up[1],z-.22),(x+.16,up[3],4.12),'exterior_concrete')
    box('terrace_retaining_west_end',(terrace[0]-.16,terrace[1]-.16,z-.22),(terrace[0],terrace[3]-.08,3.77),'exterior_concrete')
    box('terrace_retaining_west_south',(terrace[0],terrace[1]-.16,z-.22),(up[0]-.16,terrace[1],3.77),'exterior_concrete')
    for side,x in (('west',down[2]-.28),('east',down[2]+3.12)):
        box('garden_approach_retaining_'+side,(x,down[3],low-.22),(x+.16,8.75,high),'exterior_concrete')
    box('garden_landing_retaining_south',(down[2],down[1]-.16,low-.22),
        (down[2]+3.12,down[1],high),'exterior_concrete')
    # True tread/landing paths are shared by source and native checks.
    newrails=[]
    def rail(name,p,q):railing(lambda n,lo,hi,m:box(n,lo,hi,m),newrails,'drawio_'+name,p,q)
    count=20;up_path=[[21.85,ty,z],[(up[0]+up[2])/2,up[3]+.15,z]]
    run=(up[3]-up[1])/count;ux=(up[0]+up[2])/2
    for i in range(count):
        y=up[3]-(i+1)*run;h=z+(high-z)*(i+1)/count
        box('up_step_'+str(i),(up[0],y,h-.16),(up[2],y+run,h),'floor_grating')
        up_path.append([ux,y+run/2,h])
    up_path.append([ux,up[1]-.75,high])
    for x in (up[0],up[2]):rail('up_side_'+str(x),(x,up[3],z),(x,up[1],high))
    for x in (down[2]-.28,down[2]+3.28):
        rail('garden_approach_top_'+str(x),(x,down[3],high),(x,8.75,high))
    dx=down[2]-down[0];step=(dx-1.1)/count;down_path=[[down[0]-.6,ty,z]]
    for i in range(count):
        x=down[0]+i*step+(1.1 if i>=10 else 0);h=z-(z-low)*(i+1)/count
        box('down_step_'+str(i),(x,down[1],h-.16),(x+step,down[3],h),'floor_grating')
        down_path.append([x+step/2,ty,h])
        if i==9:
            start=x+step;plate('down_midlanding',(start,down[1],start+1.1,down[3]),h,'floor_grating')
            down_path.append([start+.55,ty,h])
    down_path.append([down[2]+1.5,ty,low])
    for y in (down[1],down[3]):
        middle=down[0]+10*step
        rail('down_first_'+str(y),(down[0],y,z),(middle,y,(z+low)/2))
        rail('down_landing_'+str(y),(middle,y,(z+low)/2),(middle+1.1,y,(z+low)/2))
        rail('down_second_'+str(y),(middle+1.1,y,(z+low)/2),(down[2],y,low))
    # The UP and DOWN starts are gaps in the south/east terrace guard.
    rail('terrace_south_west',(terrace[0],terrace[1],z),(up[0],terrace[1],z))
    rail('terrace_south_east',(up[2],terrace[1],z),(terrace[2],terrace[1],z))
    rails.extend(newrails)
    connection=spec['west_offices']['connection_route']
    indoor=[connection[0],connection[1],[walk_x,16.62,z],[walk_x,ty,z]]
    passage=[[walk_x,ty,z],[down[0]-.6,ty,z]]
    garden_path=[down_path[-1],[down[2]+1.5,10.,low],[54.5,10.,low],
                 [54.5,18.5,low],[39.5,18.5,low],[39.5,12.5,low]]
    routes=dict(indoor=indoor,passage=passage,up=up_path,down=down_path,garden=garden_path,
                office_exit=spec['gardens']['routes']['office_exit'])
    spec['gardens'].update(source=SOURCE,passage=terrace,up_stair=up,up_top=[up[0],up[1]-1.5,up[2],up[1]],
        down_stair=down,down_landing=[down[2],down[1],down[2]+3.,down[3]],exit_door=[21.85,2.],
        indoor_corridor=c5,indoor_turn=[9.5,15.23,20.5,18.],routes=routes)
    spec['additions']['yard'].update(routes=routes,indoor_path=passage,outdoor_path=up_path,
        down_path=down_path,top_path=[up_path[-1]],status='Entrance stairs relocated from user Draw.io; retained lower garden')
    spec['repair_doors']=doors
    spec['minus1_corrections']['c5_north_junction_door']=dict(centre=[cx,c5[3],z],width=1.65,height=2.2,axis=1)
    repair=spec['walkthrough_repairs'];repair.update(c5=c5,c7_exit_link=None,closed_rooms=dict(E1=e1,E2=e2),
        arrival_terrace=[terrace],source=SOURCE,metric_status=layout['snapping'],garden_slopes=[])
    spec['drawio_entrance']=layout
    floor=next(l for l in spec['basement_rebuild']['levels'] if l['floor']==-1)
    for lo,hi in indoor_holes:
        floor['areas']=[p for r in floor['areas'] for p in subtract_rect(r,[lo[0],lo[1],hi[0],hi[1]])]
    floor['areas'].extend([c5,e1,e2])
    old_routes=spec['basement_rebuild']['routes']
    old_routes[:]=[r for r in old_routes if r['id'] not in
        ('terrace_to_wi1','terrace_to_c7','c5_to_exit_corridor','garden_to_c5_terrace')]
    for r in old_routes:
        if r['id']=='minus1_stair_to_exit_direct':r['points']=indoor
        elif r['id']=='minus1_labs_to_exit':
            r['points']=[*r['points'][:4],[19.2,16.62,z],[walk_x,16.62,z],[walk_x,ty,z]]
    old_routes.extend([
        dict(id='terrace_to_wi1',points=[[walk_x,ty,z],[walk_x,9.260619977,z],[19.5,9.260619977,z],[17.,9.260619977,z]]),
        dict(id='terrace_to_c7',points=[[walk_x,ty,z],[walk_x,16.62,z],[19.2,16.62,z],[10.2,16.62,z]]),
        dict(id='terrace_to_c5_north',points=[[walk_x,ty,z],[walk_x,9.260619977,z],[walk_x,16.62,z],[walk_x,c5[3]-.9,z]])])
    level=next(l for l in spec['levels'] if l['floor']==-1)
    obsolete_stations={'lower_exit_junction','exit_stair_approach'}
    level['audit_stations']=[s for s in level['audit_stations'] if s['id'] not in obsolete_stations]
    for station in level['audit_stations']:
        if station['id']=='former_lift_floor':station['point']=[walk_x,15.95]
    level['audit_stations'].extend([dict(id='drawio_c5_terrace',point=[walk_x,ty]),
                                   dict(id='drawio_c5_north',point=[walk_x,c5[3]-.9])])
    hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in (SOURCE,'tools/povo2_drawio_entrance.py')}
    spec.setdefault('input_hashes',{}).update(hashes)
    ext.setdefault('input_hashes',{}).update(hashes)
    ext['pavement_repairs']['garden_exclusions'].extend([[*lo[:2],*hi[:2]] for lo,hi in excavations])
    spec['lights'].extend([[cx,6,3.1],[cx,16,3.1],[cx,c5[3]-1.,3.1]])
    return result
