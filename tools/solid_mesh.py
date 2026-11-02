"""Subtract an axis-aligned opening from a closed convex triangle mesh."""
import math


def clip(mesh,axis,value,below):
    polygons=[];cuts={};sign=1 if below else -1
    distances=[(value-p[axis])*sign for p in mesh['vertices']]
    if min(distances)>=-1e-9:return mesh
    if max(distances)<=1e-9:return None
    for face in mesh['faces']:
        p=[mesh['vertices'][i] for i in face];out=[]
        for a,b in zip(p,p[1:]+p[:1]):
            da=(value-a[axis])*sign;db=(value-b[axis])*sign
            if da>=-1e-9:out.append(tuple(a))
            if (da>1e-9 and db< -1e-9) or (da< -1e-9 and db>1e-9):
                t=da/(da-db);q=tuple(round(a[k]+t*(b[k]-a[k]),10) for k in range(3))
                out.append(q);cuts[q]=q
            elif abs(da)<1e-9:cuts[tuple(a)]=tuple(a)
        out=list(dict.fromkeys(out))
        if len(out)>=3:polygons.append(out)
    if not polygons:return None
    if len(cuts)>=3:
        points=list(cuts);centre=tuple(sum(p[k] for p in points)/len(points) for k in range(3))
        u,v=(axis+1)%3,(axis+2)%3
        points.sort(key=lambda p:math.atan2(p[v]-centre[v],p[u]-centre[u]))
        if not below:points.reverse()
        # A centre fan retains every collinear edge vertex, so side triangles
        # and caps share identical edges instead of producing T junctions.
        polygons.extend([[centre,a,b] for a,b in zip(points,points[1:]+points[:1])])
    vertices=[];faces=[];indices={}
    def vertex(p):
        p=tuple(round(x,9) for x in p)
        if p not in indices:indices[p]=len(vertices);vertices.append(p)
        return indices[p]
    for p in polygons:
        for i in range(1,len(p)-1):
            a,b,c=p[0],p[i],p[i+1];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if sum(x*x for x in cross)>1e-18:faces.append(tuple(vertex(q) for q in (a,b,c)))
    if not vertices or any(max(p[k] for p in vertices)-min(p[k] for p in vertices)<1e-8 for k in range(3)):return None
    return dict(mesh,vertices=vertices,faces=faces)


def subtract(mesh,hole):
    """Return <=6 disjoint, capped convex pieces outside the hole."""
    lo,hi=hole
    if any(max(p[k] for p in mesh['vertices'])<=lo[k] or min(p[k] for p in mesh['vertices'])>=hi[k] for k in range(3)):
        return [mesh]
    pieces=[];core=mesh
    for axis in range(3):
        for value,below in ((lo[axis],True),(hi[axis],False)):
            outside=clip(core,axis,value,below)
            if outside:pieces.append(outside)
            core=clip(core,axis,value,not below)
            if core is None:return pieces
    return pieces
