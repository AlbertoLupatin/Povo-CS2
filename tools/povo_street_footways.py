"""Closed street footways with outside corner joins and open carriageways."""
import math

try:
    from .povo_floor_surfaces import area, bounds, clean, overlaps, subtract
except ImportError:
    from povo_floor_surfaces import area, bounds, clean, overlaps, subtract


def prism(name, top, material='exterior_paving', thickness=.22):
    """Extrude a convex walking polygon, preserving its grade and closed sides."""
    top=clean(top)
    # Repeated road cuts can leave sub-micron edges or collinear cap vertices.
    # Remove them before triangulation rather than exporting sliver triangles.
    while len(top)>3:
        for i,b in enumerate(top):
            a,c=top[i-1],top[(i+1)%len(top)]
            length=math.dist(a[:2],c[:2])
            cross=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if length<1e-7 or cross/length<1e-7:
                top.pop(i);break
        else:break
    if area(top)<1e-7 or min(math.dist(a[:2],b[:2]) for a,b in zip(top,top[1:]+top[:1]))<1e-7:
        return None
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(top,top[1:]+top[:1]))<0:
        top.reverse()
    n=len(top)
    # Choose the cap fan with the widest smallest triangle. Repeated cuts can
    # leave almost-collinear vertices near one possible fan origin.
    def smallest_triangle(start):
        p=top[start:]+top[:start];a=p[0]
        return min(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
                   for b,c in zip(p[1:],p[2:]))
    start=max(range(n),key=smallest_triangle)
    top=top[start:]+top[:start]
    vertices=[(x,y,z-thickness) for x,y,z in top]+top
    faces=[]
    for i in range(1,n-1):
        faces.extend(((0,i+1,i),(n,n+i,n+i+1)))
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j),(i,n+j,n+i)))
    return dict(name=name,vertices=vertices,faces=faces,material=material)


def corners(name, road):
    """Fill only the outside-turn sector between adjoining footway end faces.

    Both strip end faces have the joint's elevation even on a steep approach,
    so the corner connects to them at that exact height. A complete annulus
    would instead run along and across the carriageway, above its grade.
    """
    inner=road['width']/2;outer=inner+road['footway_width']
    for k,(a,p,b) in enumerate(zip(road['points'],road['points'][1:],road['points'][2:])):
        u=[p[i]-a[i] for i in (0,1)];v=[b[i]-p[i] for i in (0,1)]
        turn=u[0]*v[1]-u[1]*v[0]
        if abs(turn)<1e-7:continue
        side=-1 if turn>0 else 1
        start=math.atan2(side*u[0],-side*u[1])
        end=math.atan2(side*v[0],-side*v[1])
        sweep=(end-start+math.pi)%math.tau-math.pi
        count=max(1,math.ceil(abs(sweep)/(math.pi/24)))
        for i in range(count):
            t=start+sweep*i/count;s=start+sweep*(i+1)/count
            top=[(p[0]+r*math.cos(q),p[1]+r*math.sin(q),p[2]+.12)
                 for r,q in ((inner,t),(outer,t),(outer,s),(inner,s))]
            mesh=prism(f'exterior_paving_{name}_corner_{k}_{i}',top)
            if mesh:yield mesh


def campus_frontage(road, inner_x=56.7):
    """One campus-side footway, sharing the road's true perpendicular end planes.

    The previous Y-aligned widening overlapped the normal-offset footway at a
    different elevation. Loft to the same curb endpoints instead, keep the
    descending strip whole, and cut its footprint from the following landing.
    """
    half=road['width']/2
    sections=[]
    for i,(a,b) in enumerate(zip(road['points'][1:],road['points'][2:])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if dy<=0:raise ValueError('Frontage requires northward street segments')
        def cross(p):
            return [(inner_x,p[1]-(inner_x-p[0])*dx/dy,p[2]+.12),
                    (p[0]-half*dy/length,p[1]+half*dx/length,p[2]+.12)]
        start,end=cross(a),cross(b)
        sections.append([start[0],start[1],end[1],end[0]])
    footprints=[]
    for i,top in enumerate(sections):
        parts=[top]
        for previous in footprints:
            parts=[piece for part in parts for piece in
                   (subtract(part,previous) if overlaps(bounds(part),bounds(previous)) else [part])]
        for j,part in enumerate(parts):
            mesh=prism(f'road_front_campus_paving_{i}_{j}',part,material='paving',thickness=.18)
            if mesh:yield mesh
        footprints.append(top)
    for i,(a,b) in enumerate(zip(sections,sections[1:])):
        # Convex hull of the adjoining end faces; only retain the uncovered gap.
        points=sorted(set(a[2:]+b[:2]))
        def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
        def chain(points):
            out=[]
            for p in points:
                while len(out)>=2 and cross(out[-2],out[-1],p)<=1e-9:out.pop()
                out.append(p)
            return out
        hull=chain(points)[:-1]+chain(list(reversed(points)))[:-1]
        if len(hull)<3:continue
        parts=[hull]
        for section in sections:
            parts=[piece for part in parts for piece in
                   (subtract(part,section) if overlaps(bounds(part),bounds(section)) else [part])]
        for j,part in enumerate(parts):
            mesh=prism(f'road_front_campus_paving_join_{i}_{j}',part,material='paving',thickness=.18)
            if mesh:yield mesh


def tops(mesh):
    if len(mesh['vertices'])==8:
        return [mesh['vertices'][4:]]
    if '_joint_' in mesh['name']:
        return [mesh['vertices'][len(mesh['vertices'])//2:]]
    result=[]
    for face in mesh['faces']:
        p=[mesh['vertices'][i] for i in face];a,b,c=p[:3]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>1e-9:
            result.append(p)
    return result


def plane(p):
    a,b,c=p[:3]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    x,y=-normal[0]/normal[2],-normal[1]/normal[2]
    return x,y,a[2]-x*a[0]-y*a[1]


def at_grade(cutter, pavement, road):
    """Limit an asphalt cutter to the curb-height overlap of the two planes.

    This opens intersecting streets without excavating an elevated footway
    merely because a road elsewhere passes beneath its XY footprint.
    """
    dx,dy,dz=[a-b for a,b in zip(pavement,road)]
    for low in (True,False):
        result=[]
        for a,b in zip(cutter,cutter[1:]+cutter[:1]):
            def distance(p):
                delta=dx*p[0]+dy*p[1]+dz
                return delta+.02 if low else .25-delta
            da,db=distance(a),distance(b)
            if da>=0:result.append(a)
            if (da>=0)!=(db>=0):
                t=da/(da-db)
                result.append(tuple(a[i]+t*(b[i]-a[i]) for i in (0,1)))
        cutter=clean(result)
        if len(cutter)<3:return []
    return cutter


def is_street_footway(mesh):
    name=mesh['name']
    return mesh['material']=='exterior_paving' and (
        name.startswith(('exterior_footway_','exterior_road_north_footway_',
                         'exterior_road_front_footway_','exterior_road_front_campus_paving_'))
        or (name.startswith('exterior_paving_') and '_corner_' in name))


def trim_carriageways(exterior):
    """Apply identical closed footway pieces to rendering and collision."""
    cutters=[(p,bounds(p),plane(p)) for m in exterior['meshes']
             if m['material']=='exterior_asphalt' for p in tops(m)]
    replacements={}
    for mesh in exterior['meshes']:
        if not is_street_footway(mesh):continue
        pieces=[];removed=0
        for top in tops(mesh):
            parts=[top];box=bounds(top);grade=plane(top)
            for cutter,cutbox,roadgrade in cutters:
                if not overlaps(box,cutbox):continue
                footprint=at_grade([p[:2] for p in cutter],grade,roadgrade)
                if len(footprint)<3 or area(footprint)<1e-8:continue
                parts=[piece for part in parts for piece in
                       (subtract(part,footprint) if overlaps(bounds(part),bounds(footprint)) else [part])]
                if not parts:break
            removed+=area(top)-sum(area(p) for p in parts)
            pieces.extend(parts)
        if removed>1e-7:
            thickness=mesh['vertices'][len(mesh['vertices'])//2][2]-mesh['vertices'][0][2]
            replacements[mesh['name']]=[piece for i,p in enumerate(pieces)
                if (piece:=prism(mesh['name']+f'_roadcut_{i}',p,mesh['material'],thickness)) is not None]
    for key in ('meshes','collision_meshes'):
        exterior[key]=[piece for mesh in exterior[key]
                       for piece in replacements.get(mesh['name'],[mesh])]
    return sorted(replacements)
