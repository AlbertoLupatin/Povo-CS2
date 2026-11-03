"""User's 2 November finishing pass on the definitive Povo 2 -1 layout.

Room bounds, names, passages, stair registration and terrace plates are inputs,
never reconstructed here. Only the requested wall faces and furniture change.
"""
import math
import re

from .povo_interior_fixtures import office_frame, office_point
from .povo_room_fitout import subtract_box


def extend(boxes, levels):
    spec = levels[1]['connection']['povo2']
    office = spec['west_offices']
    labs = next(l['rooms'] for l in spec['levels'] if l['floor'] == -1)
    result = list(boxes)
    prefix = 'p2_basement_fitout_'

    def add(name, lo, hi, material='wall'):
        parts=[(prefix + name, tuple(lo), tuple(hi), material)]
        if material=='wall':
            for old in result:
                if old[3]=='wall':parts=[p for part in parts for p in subtract_box(part,(old[1],old[2]))]
        result.extend(parts)

    def cut(hole, select):
        nonlocal result
        result = [p for b in result for p in (subtract_box(b, hole) if select(b) else [b])]

    def glass_face(name, axis, fixed, start, end, half=.08):
        """Replace an existing opaque face on its exact plane, with no new gap."""
        across = 1-axis
        lo = [0., 0., .4]; hi = [0., 0., 3.5]
        lo[axis], hi[axis] = fixed-half-.001, fixed+half+.001
        lo[across], hi[across] = start, end
        cut((lo, hi), lambda b: b[0].startswith('p2_basement_') and b[3] == 'wall')
        lo[axis], hi[axis] = fixed-.025, fixed+.025
        lo[2], hi[2] = .42, 3.35
        add(name+'_glass', lo, hi, 'reception_glass')
        # Same glass, frame and horizontal privacy bands as the internal fronts.
        for i,z in enumerate((.42,.72,1.02,1.32,1.62,3.32)):
            a,b=list(lo),list(hi);a[2]=z;b[2]=z+(.025 if i in (0,5) else .12)
            a[axis]-=.004;b[axis]+=.004
            add(name+f'_band_{i}'+('_finish_attached' if i not in (0,5) else ''),
                a,b,'window_frame' if i in (0,5) else 'office_frost')
        for i,at in enumerate((start,end)):
            a,b=list(lo),list(hi);a[across]=at-.018;b[across]=at+.018
            a[2],b[2]=.4,3.35
            add(name+f'_jamb_{i}',a,b,'window_frame')
        # Close the small sill/head margins exactly as on the office shell.
        for label,z0,z1 in (('sill',.4,.42),('head',3.35,3.5)):
            a,b=list(lo),list(hi);a[2],b[2]=z0,z1
            add(name+'_'+label,a,b)

    # True external sides only. C7/C5-facing walls and room party walls remain.
    west,south,east,north=office['footprint']
    external=[]
    for room in office['rooms']:
        a,b,c,d=room['bounds']
        faces=[]
        if abs(a-west)<1e-5:faces.append((0,a,b,d))
        if abs(b-south)<1e-5:faces.append((1,b,a,c))
        if abs(d-north)<1e-5:faces.append((1,d,a,c))
        for i,face in enumerate(faces):
            glass_face(room['id']+f'_exterior_{i}',*face)
            external.append(dict(room=room['id'],axis=face[0],fixed=face[1],span=list(face[2:])))
    # User clarified: the CIBIO side opposite the entrance, on the exterior.
    for room in labs:
        a,b,c,d=room['bounds']
        glass_face(room['id']+'_exterior',0,a,b,d,.1)

    # Photo 1: finish the existing C7 end-wall plane. The sole access is the
    # empty doorway on the left, on WI2's south-facing boundary.
    wi2=next(c['bounds'] for c in office['corridors'] if c['id']=='WI2')
    x,y=office['c7'][:2];top=wi2[3]
    add('c7_end_wall',(x-.08,y,.4),(x+.08,top,3.5))
    centre=(x+wi2[2])/2;half=.475
    add('wi2_left_jamb',(x,y-.08,.4),(centre-half,y+.08,2.65))
    add('wi2_right_jamb',(centre+half,y-.08,.4),(wi2[2],y+.08,2.65))
    # The approved shell already has its full-width header above this opening.
    for route in office['routes']:
        if route['id']=='west_WI2':
            for p in route['points']:p[0]=(wi2[0]+x-.08)/2
    spec['basement_rebuild']['routes'].append(dict(id='c7_to_empty_wi2_door',
        points=[[centre,y+1.,.4],[centre,y-.75,.4],[(wi2[0]+x-.08)/2,y-.75,.4]]))

    # Photo 2: the terrace-side corridor facade is opaque, with fixed black
    # pairs at the same six door locations. No openable/breakable leaf survives.
    terrace_prefix='p2_basement_repair_cibio_terrace'
    doors=[d for d in spec['repair_doors'] if d['id'].startswith('p2_cibio_terrace_')]
    portals={}
    for door in doors:
        key=door['id'].rsplit('_',1)[0]
        portals.setdefault(key,[]).append(door)
    result=[b for b in result if not (b[0].startswith(terrace_prefix) and
            (b[3] in ('window_glass','reception_glass') or '_interactive_leaf_' in b[0]))]
    spec['repair_doors']=[d for d in spec['repair_doors'] if not d['id'].startswith('p2_cibio_terrace_')]
    south=labs[0]['bounds'][1];end=55.9
    walls=[(prefix+'terrace_wall',(-2.4,south,.4),(-2.2,end,3.5),'wall')]
    for i,pair in enumerate(portals.values()):
        edges=sorted(d['pivot'][1] for d in pair);a,b=edges
        hole=((-2.5,a,.39),(-2.1,b,2.65))
        walls=[p for box in walls for p in subtract_box(box,hole)]
        mid=(a+b)/2
        for j,(u,v) in enumerate(((a,mid),(mid,b))):
            add(f'terrace_closed_{i}_leaf_{j}',(-2.34,u,.4),(-2.26,v,2.65),'door_black')
    result.extend(walls)
    routes=spec['basement_rebuild']['routes']
    routes[:]=[r for r in routes if not r['id'].startswith('cibio_terrace_exit_')]

    # Replace CIBIO's original sparse kit; all room identity/door records stay.
    result=[b for b in result if not (re.match(r'p2_basement_cibio_office_\d+_',b[0]) and
            re.search(r'_(desk|monitor|chair)(_|$)',b[0]))]
    counts={}
    for room in [*office['rooms'],*labs]:
        shared=room['id'] in ('west_W01','west_W02','west_W04') or room in labs
        counts[room['id']]=furnish(result,room,spec['basement_rebuild']['routes'],shared)
    spec['minus1_finishes']=dict(date='2026-11-02',external_w_faces=external,
        cibio_glass_side='opposite exterior wall',workstations=counts,
        empty_wi2_door=dict(centre=[centre,y],width=.95),
        fixed_terrace_doors=len(portals),layout='Definitive room/door/stair/terrace coordinates retained')
    return result


def furnish(boxes,room,routes,shared):
    """Two rows for shared offices, one workstation in every other W room."""
    a,b,c,d=room['bounds'];z=.4
    front={'u_min':'south','u_max':'north','v_min':'west','v_max':'east'}[room['door_side']]
    frame=office_frame(room['bounds'],z,front);width,depth=frame[3:]
    prefix='p2_basement_fitout_'+room['id']+'_'
    protected=[]
    for route in routes:
        for p,q in zip(route['points'],route['points'][1:]):
            if not (abs(p[2]-z)<.01 and abs(q[2]-z)<.01):continue
            if max(p[0],q[0])<a-.5 or min(p[0],q[0])>c+.5 or max(p[1],q[1])<b-.5 or min(p[1],q[1])>d+.5:continue
            for i in range(max(1,math.ceil(math.dist(p,q)/.2))+1):
                t=i/max(1,math.ceil(math.dist(p,q)/.2));x=p[0]+(q[0]-p[0])*t;y=p[1]+(q[1]-p[1])*t
                protected.append(((x-.43,y-.43,z+.02),(x+.43,y+.43,z+1.85)))
    # CIBIO has no individual entry route; preserve its doorway-to-centre aisle.
    if room['id'].startswith('cibio_'):
        door=(c,b+(d-b)*room['door_fraction'],z)
        middle=((a+c)/2,(b+d)/2,z)
        for i in range(41):
            x=door[0]+(middle[0]-door[0])*i/40;y=door[1]+(middle[1]-door[1])*i/40
            protected.append(((x-.45,y-.45,z+.02),(x+.45,y+.45,z+1.85)))
    local=[];rows=[]
    def box(n,u,v,w,h,low,high,mat):
        p=office_point(frame,u,v,low);q=office_point(frame,u+w,v+h,high)
        return (prefix+n,tuple(min(x,y) for x,y in zip(p,q)),tuple(max(x,y) for x,y in zip(p,q)),mat)
    def overlap(p,q):return all(p[0][i]<q[1][i]-1e-6 and p[1][i]>q[0][i]+1e-6 for i in range(3))
    def workstation(row,col,u,v):
        n=f'row_{row}_station_{col}';w=1.2
        group=[box(n+'_desk',u-w/2,v-.325,w,.65,.73,.79,'desk_dark'),
               box(n+'_monitor',u-.25,v+.12,.5,.06,.91,1.25,'office_screen'),
               box(n+'_stand',u-.035,v+.11,.07,.12,.79,.91,'window_frame'),
               box(n+'_keyboard',u-.22,v-.17,.44,.15,.79,.815,'office_dark'),
               box(n+'_chair_seat',u-.24,v-1.02,.48,.48,.43,.49,'office_dark'),
               box(n+'_chair_back',u-.24,v-1.07,.48,.05,.49,1.02,'office_dark'),
               box(n+'_chair_base',u-.18,v-.96,.36,.36,.03,.43,'window_frame')]
        for i,dx in enumerate((-.52,.46)):
            for j,dy in enumerate((-.25,.19)):
                group.append(box(n+f'_leg_{i}_{j}',u+dx,v+dy,.06,.06,0,.73,'window_frame'))
        for _,lo,hi,_ in group:
            if lo[0]<a+.15 or hi[0]>c-.15 or lo[1]<b+.15 or hi[1]>d-.15:return False
            if any(overlap((lo,hi),p) for p in protected):return False
            if any(overlap((lo,hi),(p,q)) for _,p,q,m in boxes+local
                   if not m.startswith('floor_') and m!='ceiling_panel'):return False
        local.extend(group);return True
    if shared:
        for row,v in enumerate((1.8,depth-.65)):
            count=0
            for col,u in enumerate(sorted(set((.95,2.65,width-2.65,width-.95)))):
                count+=workstation(row,col,u,v)
            rows.append(count)
        if min(rows)<2:raise ValueError('Two furnished rows do not fit '+room['id']+': '+str(rows))
    else:
        found=False
        for v in (depth-.65,depth/2,1.8):
            for u in (.95,width-.95,width/2):
                if workstation(0,0,u,v):found=True;break
            if found:break
        if not found:raise ValueError('No desk fits '+room['id'])
        rows=[1]
    boxes.extend(local)
    room['fitout']=dict(kind=room.get('kind','office'),desks=sum(rows),computers=sum(rows),
        rows=rows,seats=sum(rows),furniture=['desks','computers','chairs'],
        status='User-requested furnishing; definitive room layout and name retained')
    return sum(rows)
