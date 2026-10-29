"""Planar clipping helpers and the horizontal-floor audit's material filter."""
import math

EPSILON = 1e-8


def area(polygon):
    return abs(sum(a[0]*b[1]-b[0]*a[1]
                   for a,b in zip(polygon, polygon[1:]+polygon[:1])))/2


def bounds(polygon):
    return (min(p[0] for p in polygon), min(p[1] for p in polygon),
            max(p[0] for p in polygon), max(p[1] for p in polygon))


def overlaps(a, b):
    return min(a[2],b[2])-max(a[0],b[0]) > EPSILON and min(a[3],b[3])-max(a[1],b[1]) > EPSILON


def clean(polygon):
    result=[]
    for p in polygon:
        if not result or math.dist(p[:2],result[-1][:2])>1e-9:result.append(p)
    if len(result)>1 and math.dist(result[0][:2],result[-1][:2])<=1e-9:result.pop()
    return result


def subtract(polygon, cutter):
    """Subtract a CCW convex polygon, interpolating every vertex attribute.

    XYZ and UV travel together through clipping so newly cut triangles retain
    the original world-aligned texture rather than stretching at the joins.
    """
    remaining = clean(polygon)
    cutter = clean(cutter)
    pieces = []
    for a,b in zip(cutter, cutter[1:]+cutter[:1]):
        length=math.dist(a[:2],b[:2])
        if length<=1e-9:continue
        inside, outside = [], []
        for p,q in zip(remaining, remaining[1:]+remaining[:1]):
            dp = ((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))/length
            dq = ((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))/length
            if abs(dp)<1e-9:dp=0
            if abs(dq)<1e-9:dq=0
            (inside if dp >= 0 else outside).append(p)
            if (dp >= 0) != (dq >= 0):
                t = dp/(dp-dq)
                intersection = tuple(p[i]+t*(q[i]-p[i]) for i in range(len(p)))
                inside.append(intersection)
                outside.append(intersection)
        inside=clean(inside);outside=clean(outside)
        if len(outside) >= 3 and area(outside) > EPSILON:
            pieces.append(outside)
        remaining = inside
        if len(remaining) < 3 or area(remaining) <= EPSILON:
            break
    return pieces


def is_floor(material):
    return material.startswith('campus_floor_') or material in (
        'campus_exterior_paving', 'campus_exterior_asphalt',
        'campus_exterior_concrete', 'campus_courtyard_ground')


def exclusive_tops(faces):
    """Resolve floor tops through the same general surface resolver."""
    try:
        from .povo_render_surfaces import exclusive_faces
    except ImportError:
        from povo_render_surfaces import exclusive_faces
    return exclusive_faces(faces)
