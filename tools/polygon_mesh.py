"""Closed scenery prisms with concave outlines and open courtyard rings.

Horizontal bands split at every ring vertex. Even/odd edge pairs form disjoint
trapezoids, so caps never bridge a courtyard. No optional GIS library is needed.
"""


def ring_points(points, clockwise=False):
    points = [tuple(p) for p in points]
    if points[0] == points[-1]:
        points.pop()
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points, points[1:]+points[:1]))
    if (area < 0) != clockwise:
        points.reverse()
    return points


def prism(name, rings, z, height, material):
    rings = [ring_points(r, clockwise=i > 0) for i,r in enumerate(rings)]
    vertices, faces, indices = [], [], {}
    def vertex(p):
        p = tuple(round(v, 10) for v in p)
        if p not in indices:
            indices[p] = len(vertices)
            vertices.append(p)
        return indices[p]
    def triangle(points):
        a,b,c = points
        u = [b[i]-a[i] for i in range(3)]
        v = [c[i]-a[i] for i in range(3)]
        cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        if sum(t*t for t in cross) > 1e-16:
            faces.append(tuple(vertex(p) for p in points))
    edges = [(a,b) for r in rings for a,b in zip(r, r[1:]+r[:1])]
    ys = sorted({p[1] for r in rings for p in r})
    for low,high in zip(ys, ys[1:]):
        mid = (low+high)/2
        active = [(a,b) for a,b in edges if min(a[1],b[1]) < mid < max(a[1],b[1])]
        def x_at(edge, y):
            a,b = edge
            return a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
        active.sort(key=lambda e: x_at(e,mid))
        if len(active) % 2:
            raise ValueError('Invalid building rings: '+name)
        for left,right in zip(active[::2], active[1::2]):
            p = [(x_at(left,low),low), (x_at(right,low),low),
                 (x_at(right,high),high), (x_at(left,high),high)]
            for ids in ((0,1,2), (0,2,3)):
                triangle([(*p[i],z+height) for i in ids])
                triangle([(*p[i],z) for i in reversed(ids)])
    for a,b in edges:
        triangle([(*a,z), (*b,z), (*b,z+height)])
        triangle([(*a,z), (*b,z+height), (*a,z+height)])
    return dict(name=name, vertices=vertices, faces=faces, material=material)
