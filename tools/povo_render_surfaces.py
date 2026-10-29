"""Remove coplanar render duplicates in any orientation; preserve collision."""
import math
try:
    from .povo_floor_surfaces import area,bounds,overlaps,subtract
except ImportError:
    from povo_floor_surfaces import area,bounds,overlaps,subtract

CELL = 4


def project(points, uvs=None):
    """Return a signed plane and CCW projected polygon carrying XYZ and UV."""
    a,b,c=points[:3]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    length=math.sqrt(sum(n*n for n in normal))
    if length<1e-12:return None
    normal=tuple(n/length for n in normal)
    axis=max(range(3),key=lambda i:abs(normal[i]))
    # Small road-corner triangles can amplify sub-ulp height differences into
    # spurious tilted normals. Use the common coordinate for flat source faces.
    if max(p[axis] for p in points)-min(p[axis] for p in points)<1e-9:
        sign=1 if normal[axis]>0 else -1
        normal=tuple(sign if i==axis else 0 for i in range(3))
    distance=sum(normal[i]*a[i] for i in range(3))
    if any(abs(sum(normal[i]*p[i] for i in range(3))-distance)>1e-7 for p in points):return None
    axes=((axis+1)%3,(axis+2)%3)
    polygon=[(p[axes[0]],p[axes[1]],*p,*(uvs[i] if uvs is not None else ())) for i,p in enumerate(points)]
    reverse=normal[axis]<0
    if reverse:polygon.reverse()
    key=(*[round(n,8) for n in normal],round(distance,7))
    return key,polygon,reverse,axis


def cells(box):
    return ((x,y) for x in range(math.floor(box[0]/CELL),math.floor(box[2]/CELL)+1)
            for y in range(math.floor(box[1]/CELL),math.floor(box[3]/CELL)+1))


class SurfaceIndex:
    def __init__(self):
        self.planes={}

    def candidates(self,key,box):
        index=self.planes.get(key,{})
        unique={id(entry):entry for cell in cells(box) for entry in index.get(cell,())}
        return [entry for entry in unique.values() if overlaps(box,entry[1])]

    def add(self,key,polygon,metadata=None):
        box=bounds(polygon);entry=(polygon,box,metadata)
        index=self.planes.setdefault(key,{})
        for cell in cells(box):index.setdefault(cell,[]).append(entry)


def priority(face):
    material=face[1]
    rank=2 if material.startswith('campus_exterior_') else 1 if material in (
        'campus_wall','campus_ceiling_panel','campus_floor_circulation') else 0
    # Inset windows, paint, trim and other small coplanar details own their
    # patch of a larger backing face, instead of disappearing into that face.
    points=face[2];size=0
    for i in range(1,len(points)-1):
        u=[points[i][k]-points[0][k] for k in range(3)]
        v=[points[i+1][k]-points[0][k] for k in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        size+=math.sqrt(sum(n*n for n in cross))/2
    return rank,size


def exclusive_faces(faces):
    """Clip same-facing duplicates while preserving both sides of real sheets.

    A plane's spatial index keeps the full campus and repeated furniture from
    requiring an all-pairs comparison. XYZ and UV are interpolated together.
    Opposite-facing surfaces retain their separate visibility and lighting.
    """
    index=SurfaceIndex()
    for group,material,points,uvs in sorted(faces,key=priority):
        projected=project(points,uvs)
        if projected is None:
            yield group,material,points,uvs
            continue
        key,polygon,reverse,_=projected
        fragments=[polygon]
        for occupied,box,_ in index.candidates(key,bounds(polygon)):
            fragments=[part for fragment in fragments for part in
                       (subtract(fragment,occupied) if overlaps(bounds(fragment),box) else [fragment])]
            if not fragments:break
        for fragment in fragments:
            index.add(key,fragment)
            if reverse:fragment=list(reversed(fragment))
            for i in range(1,len(fragment)-1):
                triangle=[fragment[j] for j in (0,i,i+1)]
                if area(triangle)>1e-8:
                    yield group,material,[p[2:5] for p in triangle],[p[5:] for p in triangle]
