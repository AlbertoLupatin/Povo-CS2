"""Final-coordinate repairs from the 29 October in-game walkthrough.

Keep the traced office strip west of the core. The eastern arrival follows
C5, with WI1 then C7 on the left (photo 46). No unsurveyed upper-floor plan
is invented.
"""
from .povo_room_fitout import subtract_box
from .povo_stairs import railing, wall_handrail
import json


def extend(boxes, levels, root):
    link=levels[1]['connection'];spec=link['povo2'];ext=levels[0]['exterior']
    result=list(boxes);doors=[];rails=spec['stairs']['rails']

    def add(name,lo,hi,mat='wall'):
        result.append(('p2_basement_repair_'+name,tuple(lo),tuple(hi),mat))

    def cut(hole, select=lambda b:True):
        nonlocal result
        result=[p for b in result for p in (subtract_box(b,hole) if select(b) else [b])]

    def plate(name,r,z,material='floor_p2_tile',ceiling=False):
        a,b,c,d=r
        parts=[('p2_basement_repair_'+name,(a,b,z-(.07 if ceiling else .22)),(c,d,z),material)]
        for old in result:
            if (ceiling and old[3]=='ceiling_panel') or (not ceiling and old[3].startswith(('floor_','exterior_paving'))):
                parts=[p for part in parts for p in subtract_box(part,(old[1],old[2]))]
        result.extend(parts)

    def rail(name,a,b):
        railing(lambda n,lo,hi,m:result.append((n,tuple(lo),tuple(hi),m)),rails,
                'p2_repair_'+name,a,b)

    def door(name,centre,width=1.65,axis=0,glass=False,park_sign=-1):
        """Two usable leaves, shown open in the source clearance model."""
        x,y,z=centre;along=1-axis;middle=[x,y,z]
        material='window_glass' if glass else 'door_black'
        for i,sign in enumerate((-1,1)):
            hinge=list(middle);hinge[along]+=sign*width/2
            lo=[x-.024,y-.024,z+.025];hi=[x+.024,y+.024,z+2.18]
            lo[along]=min(middle[along],hinge[along])+.018
            hi[along]=max(middle[along],hinge[along])-.018
            doors.append(dict(id='p2_'+name+'_'+str(i),kind='glass' if glass else 'exit',
                bounds=[lo,hi],pivot=hinge,
                reverse=(sign!=park_sign) if axis==0 else (-sign!=park_sign),
                material='materials/trento/povo/campus/'+material+'.vmat'))
            # Park inside the destination, with the clear aperture untouched.
            p=list(hinge);q=list(hinge);p[2]=z+.025;q[2]=z+2.18
            p[along]-=.024;q[along]+=.024
            p[axis]+=min(park_sign*width/2,park_sign*.04)
            q[axis]+=max(park_sign*width/2,park_sign*.04)
            add(name+'_interactive_leaf_'+str(i),p,q,material)
            p=list(hinge);q=list(hinge);p[2]=z;q[2]=z+2.25
            for k in (0,1):p[k]-=.025;q[k]+=.025
            add(name+'_jamb_'+str(i),p,q,'window_frame')
        lo=[x-.05,y-.05,z+2.2];hi=[x+.05,y+.05,z+2.25]
        lo[along]-=width/2;hi[along]+=width/2
        add(name+'_head',lo,hi,'window_frame')

    # Remove the entire substitute lift, including the wall fragments visible
    # between the stair and ladder entrances on floor 0. Stairs serve all levels.
    shaft=spec['lift']['shaft'];a,b,c,d=shaft
    result=[v for v in result if not v[0].startswith(('p2_lift_',
        'p2_ground_lift_','p2_basement_lift_','academic_first_link_p2_lift_',
        'p2_basement_west_lift_threshold'))]
    for floor,z in ((-1,.4),(0,4.),(1,link['floor_local_metres'])):
        plate('former_shaft_floor_'+str(floor),shaft,z)
        plate('former_shaft_ceiling_'+str(floor),shaft,z+3.1,'ceiling_panel',True)
    spec['lift']['enabled']=False
    spec['lift']['status']='Removed after user walkthrough; all levels use the stairs'
    for level in spec['levels']:
        for station in level['audit_stations']:
            if station['id'] in ('lift_floor','lift_ledge'):
                station['id']='former_'+station['id']
                if level['floor']==-1:station['point']=[23,15.95]
    link['audit_stations']=[s for s in link['audit_stations'] if s['id']!='p2_lift_ledge']

    # Restore the actual exit pair after the basement shell rebuild.
    door('garden_exit',(34.5,11.25,.4),width=2.3,axis=1,park_sign=1)

    # Eastern entrance, retraced from photo 46 (config/povo2_east_entrance.json).
    # C5 runs up the offices' east facade from a terrace door on the facade
    # line. WI1 opens on its left, then C7 meets it full width under the core,
    # where a sealed door ends C5. C7 continues east through a door to the
    # exit corridor. Closed rooms E1 and E2 fill the block east of C5.
    east=json.loads((root/'config/povo2_east_entrance.json').read_text())
    area={a['id']:a['bounds'] for a in east['areas']}
    opening={o['id']:o for o in east['openings']}
    c5=area['c5'];c7_east=area['c7_east'];e1=area['e1'];e2=area['e2']
    run=area['terrace_south_run'];terrace=[[20.36,run[1],run[2],run[3]],*area['terrace_link']]
    def mid(o,k):return (o['line'][0][k]+o['line'][1][k])/2
    def span(o,k):return abs(o['line'][1][k]-o['line'][0][k])
    zone=[((20.36,run[1]-.16,.17),(33.14,c5[3],3.77)),((c5[0],c5[3],.17),(33.14,c5[3]+.1,3.77))]
    for h in zone:
        cut(h,lambda v:v[0].startswith(('p2_basement_','p2_gardens_','exterior_','library_0_access')))
    east_hole=((run[2],run[1]-.16,.17),(33.25,terrace[2][3],3.77))
    cut(east_hole,lambda v:v[0].startswith(('exterior_','library_0_access')))
    plate('c5_floor',(20.36,c5[1],c5[2],c5[3]),.4)
    plate('c7_east_floor',c7_east,.4)
    for r in (c5,c7_east):plate(('c5' if r is c5 else 'c7_east')+'_ceiling',r,3.5,'ceiling_panel',True)
    for i,r in enumerate(terrace):plate('entrance_terrace_'+str(i),r,.4,'floor_terrace')
    # C7's bypass under the core is public corridor, not office floor.
    bypass=(9.5,15.23,20.36,17.69)
    cut(((bypass[0],bypass[1],.17),(bypass[2],bypass[3],.41)),lambda v:v[3]=='floor_wood')
    plate('c7_bypass_floor',bypass,.4)

    def wall_line(name,axis,fixed,lo,hi,gaps=(),top=3.5,half=.08):
        """Wall along x (axis 1) or y (axis 0) with door gaps and headers."""
        edges=[lo]
        for c,w,_ in sorted(gaps):edges+=[c-w/2,c+w/2]
        edges.append(hi)
        for i in range(0,len(edges),2):
            if edges[i+1]-edges[i]>1e-6:
                a=[fixed-half,edges[i],.4] if axis==0 else [edges[i],fixed-half,.4]
                b=[fixed+half,edges[i+1],top] if axis==0 else [edges[i+1],fixed+half,top]
                add(name+'_'+str(i//2),a,b)
        for j,(c,w,bottom) in enumerate(sorted(gaps)):
            a=[fixed-half,c-w/2,bottom] if axis==0 else [c-w/2,fixed-half,bottom]
            b=[fixed+half,c+w/2,top] if axis==0 else [c+w/2,fixed+half,top]
            add(name+'_header_'+str(j),a,b)

    def sealed(name,centre,width,axis,material='door_black'):
        """Permanent closed leaf with jambs; no entity can open it."""
        x,y=centre;across=1-axis;c=centre[across];h=width/2
        def box(n,a,b,z0,z1,thick,m):
            lo=[x-thick,y-thick,z0];hi=[x+thick,y+thick,z1]
            lo[across]=a;hi[across]=b;add(name+'_'+n,lo,hi,m)
        box('leaf',c-h+.05,c+h-.05,.4,2.6,.04,material)
        box('jamb_0',c-h,c-h+.05,.4,2.65,.05,'metal_dark')
        box('jamb_1',c+h-.05,c+h,.4,2.65,.05,'metal_dark')
        box('head',c-h+.05,c+h-.05,2.6,2.65,.05,'window_frame')

    terrace_door=opening['c5_terrace'];wi1=opening['wi1_public'];c7_exit=opening['c7_exit']
    north=opening['c5_north_closed'];e2_door=opening['e2_closed']
    open_gap=lambda o,k:(mid(o,k),span(o,k)+.1,2.65)
    shut_gap=lambda o,k:(mid(o,k),span(o,k),2.65)
    # C5's west side is the office facade; fill its 0.14 m strip and the WI1 door.
    wall_line('c5_west',0,20.43,c5[1]+.08,15.31,[open_gap(wi1,1)],half=.07)
    add('c5_west_wi1_stub_0',(20.3,8.09,.4),(20.36,8.17,3.5))
    add('c5_west_wi1_stub_1',(20.3,10.35,.4),(20.36,10.43,3.5))
    add('c5_facade_corner',(20.28,c5[1]-.08,.4),(20.36,c5[1],3.77))
    wall_line('facade',1,c5[1],20.36,e2[2]+.25,[open_gap(terrace_door,0)],top=3.77)
    wall_line('c5_east',0,c5[2],c5[1]+.08,c7_east[1]-.08,[shut_gap(e2_door,1)])
    sealed('e2_door',(c5[2],mid(e2_door,1)),span(e2_door,1),0,'door_closed')
    wall_line('e1_e2',1,e1[1],c5[2]+.08,e1[2])
    wall_line('closed_rooms_east',0,e2[2]+.125,e2[1]+.08,c7_east[1]-.08,top=3.77,half=.125)
    wall_line('link_north',1,terrace[1][3],e2[2]+.25,33.15,top=3.77)
    wall_line('c7_east_south',1,c7_east[1],c5[2]-.08,33.14)
    add('c7_east_exit_jamb',(33.14,14.6,.4),(33.35,c7_east[1]+.08,3.5))
    wall_line('c5_north',1,c5[3],c5[0],33.14,[shut_gap(north,0)])
    sealed('c5_north_door',(mid(north,0),c5[3]),span(north,0),1)
    wall_line('c7_exit',0,mid(c7_exit,0),c7_east[1]+.08,c7_east[3]-.08,[open_gap(c7_exit,1)])
    # The terrace is a sunken strip under the ground floor's overhang.
    add('terrace_retaining_south',(20.2,run[1]-.16,.4),(run[2]+.16,run[1],3.77))
    add('terrace_end_west',(20.2,run[1],.4),(20.36,c5[1]-.08,3.77))
    slope=lambda y:.4+3.72*(5.213076923-y)/5.813076923
    y=run[1]
    while y<5.213076923-1e-6:
        top=min(3.77,max(1.5,slope(y)+.1));y1=min(5.213076923,y+.5)
        add('terrace_retaining_east_'+str(round(y,2)),(run[2],y,.4),(run[2]+.16,y1,top));y=y1
    rail('entrance_stair_edge',(33.25,5.213076923,.4),(33.25,8.75,.4))
    rail('entrance_slope_edge',(run[2]+.16,5.213076923,.4),(33.25,5.213076923,.4))
    door('c5_terrace',(mid(terrace_door,0),c5[1],.4),width=span(terrace_door,0),axis=1,glass=True,park_sign=1)
    door('wi1_public',(20.5,mid(wi1,1),.4),width=span(wi1,1),glass=True,park_sign=1)
    door('c7_exit',(mid(c7_exit,0),mid(c7_exit,1),.4),width=span(c7_exit,1),park_sign=1)
    spec['minus1_corrections']['c5_north_junction_door']=dict(
        centre=[mid(north,0),c5[3],.4],width=span(north,0),height=2.2,axis=1)
    # Hollow the new pieces in all context meshes as well.
    result=[v for v in result if not v[0].startswith('p2_gardens_passage_west')]
    rails[:]=[v for v in rails if not v['name'].startswith('passage_west')]
    from .build_povo_campus import subtract_polygon_box
    holes=[*zone,east_hole]
    cibio_south=next(r['bounds'][1] for r in next(l for l in spec['levels'] if l['floor']==-1)['rooms'] if r['id']=='cibio_office_0')
    holes.append(((-2.3,cibio_south,.17),(-.59,55.9,3.52)))
    for h in holes:cut(h,lambda v:v[0].startswith(('exterior_','library_0_access')))
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext[key]:
            vv=mesh['vertices'];vertices=[];faces=[]
            low=[min(v[i] for v in vv) for i in range(3)]
            high=[max(v[i] for v in vv) for i in range(3)]
            relevant=[h for h in holes if all(low[i]<h[1][i] and high[i]>h[0][i] for i in range(3))]
            if not relevant:
                clipped.append(mesh);continue
            for face in mesh['faces']:
                polys=[[(tuple(vv[i]),(0,0)) for i in face]]
                for lo,hi in relevant:
                    polys=[p for poly in polys for p in subtract_polygon_box(poly,lo,hi)]
                for poly in polys:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+j,start+j+1) for j in range(1,len(poly)-1))
            if faces:clipped.append(dict(mesh,vertices=vertices,faces=faces))
        ext[key]=clipped
    basement_level=next(l for l in spec['levels'] if l['floor']==-1)
    for station in basement_level['audit_stations']:
        if station['id']=='corridor_south':station['point']=[22.,12.]
    floor=next(l for l in spec['basement_rebuild']['levels'] if l['floor']==-1)
    from .build_povo2_west_offices import subtract_rect
    for lo,hi in zone:
        floor['areas']=[p for r in floor['areas'] for p in subtract_rect(r,[lo[0],lo[1],hi[0],hi[1]])]
    floor['areas']+=[c5,c7_east]
    # Routes that crossed the old 5 m C5 now keep east of WI1's parked leaves.
    route_x=22.
    for route in [*spec['basement_rebuild']['routes'],dict(points=spec['gardens']['routes']['indoor'])]:
        for p in route['points']:
            if 20.6<p[0]<25.6 and p[1]<c5[3]+.1 and abs(p[2]-.4)<.05:p[0]=route_x
    # W office doors use the same estimated opening positions as the trace.
    for room in spec['west_offices']['rooms']:
        p,q=room['door']['points'];axis=0 if abs(p[0]-q[0])<1e-6 else 1
        middle=(p[axis]+q[axis])/2
        sign=1 if (room['bounds'][axis]+room['bounds'][axis+2])/2>middle else -1
        # The traced service-room opening has solid jambs. Widen the aperture
        # with its replacement door, keeping the header above it.
        half=(abs(q[1-axis]-p[1-axis])+.10)/2
        lo=[(p[0]+q[0])/2-.15,(p[1]+q[1])/2-.15,.39]
        hi=[(p[0]+q[0])/2+.15,(p[1]+q[1])/2+.15,2.65]
        lo[1-axis]=(p[1-axis]+q[1-axis])/2-half-.03
        hi[1-axis]=(p[1-axis]+q[1-axis])/2+half+.03
        cut((lo,hi),lambda v:v[3]=='wall' and v[0].startswith('p2_basement_west_'))
        door(room['id'],((p[0]+q[0])/2,(p[1]+q[1])/2,.4),
             width=abs(q[1-axis]-p[1-axis])+.10,axis=axis,glass=True,park_sign=sign)
        route=next(v for v in spec['west_offices']['routes'] if v['id']==room['id']+'_entry')
        inside=[(p[0]+q[0])/2,(p[1]+q[1])/2,.4]
        inside[axis]+=sign*1.3
        route['points'].insert(-1,inside)
        # The rebuild stores these routes as the same records.
    # Privacy strips must not survive as solid bars after breaking a pane.
    result=[(n+'_finish_attached' if n.startswith('p2_basement_west_front_band_') and m=='office_frost' else n,lo,hi,m)
            for n,lo,hi,m in result]

    # Glazed terrace side of the other open corridor beside CIBIO OFFICE 1.
    # Two exits share the existing wide approach; neither enters the locked L.
    south=next(r['bounds'][1] for r in next(l for l in spec['levels'] if l['floor']==-1)['rooms'] if r['id']=='cibio_office_0')
    terrace_end=55.9  # Stop before the restricted upper return at N=56.5.
    r=[-2.3,south,-.59,terrace_end]
    plate('cibio_terrace',r,.4,'floor_terrace')
    face=((-2.41,south,.4),(-2.19,terrace_end,3.5))
    cut(face,lambda v:v[3] in ('wall','window_frame'))
    old_doors=[v for v in result if v[0].startswith('p2_basement_cibio_closed_office_')]
    result=[v for v in result if not v[0].startswith('p2_basement_cibio_closed_office_')]
    door_ys=sorted((lo[1]+hi[1])/2 for _,lo,hi,_ in old_doors)
    spans=[('p2_basement_repair_cibio_terrace_glass',(-2.325,south,.42),(-2.275,terrace_end,3.35),'window_glass')]
    for i,y in enumerate(door_ys):
        spans=[p for part in spans for p in subtract_box(part,((-2.5,y-.53,.39),(-2.1,y+.53,2.65)))]
        door('cibio_terrace_'+str(i),(-2.3,y,.4),width=1.,glass=True,park_sign=1)
        spec['basement_rebuild']['routes'].append(dict(id='cibio_terrace_exit_'+str(i),
            points=[[-3.05,y,.4],[-1.05,y,.4]]))
    result.extend(spans)
    rail('cibio_terrace_outer',(-.59,south,.4),(-.59,terrace_end,.4))
    for i,y in enumerate((south,terrace_end)):rail('cibio_terrace_end_'+str(i),(-2.3,y,.4),(-.59,y,.4))

    # Guard the exposed southern/northern rims of each landing. Sloped flights
    # already have inner rails; add the missing turn links and wall handrails.
    for floor,z in ((-1,.4),(0,4.),(1,link['floor_local_metres'])):
        for label,y in (('south',18.25),('north',25.65)):
            rail('landing_'+str(floor)+'_'+label,(14.3,y,z),(18.28,y,z))
    for lower in (0,-1,-2):
        top={0:link['floor_local_metres'],-1:4.,-2:.4}[lower]
        bottom={0:4.,-1:.4,-2:-3.2}[lower]
        if lower==0:
            middle=(top+bottom)/2
            rail('turn_upper_south',(11.15,18.35,middle),(14.3,18.35,middle))
            rail('turn_upper_north',(11.15,25.35,middle),(14.3,25.35,middle))
        else:
            z1=top-(top-bottom)/3;z2=top-2*(top-bottom)/3
            rail('turn_'+str(lower)+'_south',(14.15,20.35,z1),(15.2,20.35,z1))
            rail('turn_'+str(lower)+'_north',(14.15,23.35,z2),(15.2,23.35,z2))
            prefix=f'p2_internal_{lower}_rail2'
            for rr in rails:
                if rr['name'].startswith(prefix):
                    rr['a'][0]+=2;rr['b'][0]+=2
            result=[(n,(lo[0]+2,lo[1],lo[2]),(hi[0]+2,hi[1],hi[2]),m)
                    if n.startswith(prefix) else (n,lo,hi,m) for n,lo,hi,m in result]
    # Wall handrails carry no collision into the 2 m flight clear width.
    for r0 in list(rails):
        if r0['name'].startswith('p2_internal_') and '_rail' in r0['name'] and r0['name'].endswith('_handrail'):
            p=list(r0['a']);q=list(r0['b']);axis=0 if p[0]!=q[0] else 1;cross=1-axis
            offset=-1.9 if cross==0 or p[1]<22 else 1.9
            p[cross]+=offset;q[cross]+=offset
            wall_handrail(rails,r0['name']+'_wall',p,q)
    spec['repair_doors']=doors
    spec['walkthrough_repairs']=dict(c5=c5,c7_exit_link=c7_east,closed_rooms=dict(E1=e1,E2=e2),
        arrival_terrace=terrace,cibio_terrace=r,source='config/povo2_east_entrance.json',
        approach_order=east['walk_order'],
        metric_status='Photo-46 retrace on the fitted core and offices; E1/E2 and the terrace link are estimates')
    y7=mid(opening['c7_exit'],1)
    spec['basement_rebuild']['routes'].extend([
        dict(id='terrace_to_wi1',points=[[route_x,1.1,.4],[route_x,9.26,.4],[19.5,9.26,.4],[17,9.26,.4]]),
        dict(id='terrace_to_c7',points=[[route_x,1.1,.4],[route_x,16.62,.4],[19.2,16.62,.4],[10.2,16.62,.4]]),
        dict(id='c5_to_exit_corridor',points=[[route_x,9.26,.4],[route_x,y7,.4],[34.5,y7,.4],[34.5,12,.4],[34.5,10,.4]]),
        dict(id='garden_to_c5_terrace',points=[[34.5,10,.4],[30.9,10,.4],[30.9,1.1,.4],[route_x,1.1,.4]])])
    grade_gardens(result,ext,spec)
    plate('street_garden_sidewalk',(55.5,2.75,58,8.75),4.,'exterior_paving')
    return result


def grade_gardens(boxes,ext,spec):
    """Closed earth embankments on both sides of the outdoor UP stair.

    The street edge follows the bridge road's actual eastward grade. Preserve
    the stair and its paved top landing, and fill all exposed earth underneath.
    The upper floor has no surveyed plan and is not extended by this operation.
    """
    from .build_povo_exterior import FACES
    from .build_povo_campus import subtract_polygon_box
    def road_z(x):return 4.12+max(0,min(1,(x-32)/18))*3.6
    patches=[('west',[31.96,-.6,33.25,5.213076923],
              lambda x,y:.4+(road_z(x)-.4)*(5.213076923-y)/5.813076923),
             ('east_street',[35.75,-.6,58,1.25],
              lambda x,y:4+(road_z(x)-4)*(1.25-y)/1.85),
             ('east_rear',[35.75,2.75,55.5,8.75],
              lambda x,y:4+.10*(x-35.75)/(55.5-35.75)*(y-2.75)/6)]
    # Remove overlapping old flat lawn and context sheets before adding soil.
    boxes[:]=[b for b in boxes if not b[0].startswith(('p2_gardens_street_lawn','p2_gardens_street_garden_base'))]
    for _,r,_ in patches:
        h=((r[0],r[1],-3.5),(r[2],r[3],12))
        boxes[:]=[p for b in boxes for p in (subtract_box(b,h)
            if b[0].startswith('exterior_') and not any(t in b[0] for t in
                ('road','paving','walk','canopy','bus','car_','tree','lamp','stair','street_corner')) else [b])]
        for key in ('meshes','collision_meshes'):
            out=[]
            for mesh in ext[key]:
                vv=mesh['vertices']
                if any(t in mesh['name'] for t in ('road','footway','bus','canopy')):
                    out.append(mesh);continue
                if not all(min(v[k] for v in vv)<h[1][k] and max(v[k] for v in vv)>h[0][k] for k in range(3)):
                    out.append(mesh);continue
                vertices=[];faces=[]
                for face in mesh['faces']:
                    polys=subtract_polygon_box([(tuple(vv[i]),(0,0)) for i in face],*h)
                    for poly in polys:
                        start=len(vertices);vertices.extend(v for v,_ in poly)
                        faces.extend((start,start+j,start+j+1) for j in range(1,len(poly)-1))
                if faces:out.append(dict(mesh,vertices=vertices,faces=faces))
            ext[key]=out
    for name,(a,b,c,d),height in patches:
        # Subdivision prevents bilinear quads from becoming twisted faces.
        for i in range(12):
            x=a+(c-a)*i/12;u=a+(c-a)*(i+1)/12
            top=[(x,b,height(x,b)),(u,b,height(u,b)),(u,d,height(u,d)),(x,d,height(x,d))]
            mesh=dict(name='exterior_p2_garden_slope_'+name+'_'+str(i),
                vertices=[(x0,y0,-3.42) for x0,y0,_ in top]+top,
                faces=FACES,material='exterior_grass')
            ext['meshes'].append(mesh);ext['collision_meshes'].append(mesh)
    spec['walkthrough_repairs']['garden_slopes']=[dict(id=n,bounds=r) for n,r,_ in patches]
