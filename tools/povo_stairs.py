"""Stair railings as in the walk photos: a top handrail over horizontal bars.

The rails and bars follow the stair pitch, so they are sheared prisms (faces),
not axis-aligned boxes. Posts are ordinary boxes. A stepped `_clip_` panel gives
the railing its collision; render_obj() leaves `_clip_` boxes out of the model.
"""
import math

RAIL_HEIGHT = 1.0
BARS = 6


def railing(add, rails, prefix, a, b, *, height=RAIL_HEIGHT, bars=BARS, posts=True, clip=True):
    """Railing from a to b (floor-line points, axis-aligned in plan).

    add(name, lo, hi, material) receives posts and clip boxes; rails receives
    the sloped bar specs that rail_faces() turns into model faces.
    """
    rails.append(dict(name=prefix+'_handrail', a=list(a), b=list(b), lift=height, size=.025))
    for i in range(bars):
        lift = .12 + (height - .2) * i / max(1, bars - 1)
        rails.append(dict(name=f'{prefix}_railbar_{i}', a=list(a), b=list(b), lift=lift, size=.009))
    length = math.dist(a[:2], b[:2])
    def at(t): return [a[k] + (b[k] - a[k]) * t for k in range(3)]
    if posts:
        count = max(1, math.ceil(length / 1.2))
        for i in range(count + 1):
            x, y, z = at(i / count)
            add(f'{prefix}_post_{i}', (x - .02, y - .02, z), (x + .02, y + .02, z + height), 'metal_dark')
    if clip and length > 0:
        count = max(1, math.ceil(length / .3))
        along = 0 if abs(b[0] - a[0]) > abs(b[1] - a[1]) else 1
        for i in range(count):
            p, q = at(i / count), at((i + 1) / count)
            lo = [min(p[k], q[k]) for k in range(2)] + [min(p[2], q[2])]
            hi = [max(p[k], q[k]) for k in range(2)] + [max(p[2], q[2]) + height]
            lo[1 - along] -= .02
            hi[1 - along] += .02
            add(f'{prefix}_clip_{i}', tuple(lo), tuple(hi), 'metal_dark')


def wall_handrail(rails, prefix, a, b, height=.9):
    rails.append(dict(name=prefix+'_handrail', a=list(a), b=list(b), lift=height, size=.022))


def shifted(rails, dz, rename):
    return [dict(r, name=rename(r['name']), a=[*r['a'][:2], r['a'][2] + dz], b=[*r['b'][:2], r['b'][2] + dz])
            for r in rails]


def mirrored(rails, mirror, rename):
    return [dict(r, name=rename(r['name']), a=list(mirror(r['a'])), b=list(mirror(r['b']))) for r in rails]


def rail_faces(rails, material='campus_metal_dark'):
    """Triangles of each sheared square bar, outward-facing."""
    faces = []
    for rail in rails:
        a, b, s = rail['a'], rail['b'], rail['size']
        a = (a[0], a[1], a[2] + rail['lift'])
        b = (b[0], b[1], b[2] + rail['lift'])
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        side = (-dy / length * s, dx / length * s)
        def corners(p):
            return [(p[0] + side[0] * u, p[1] + side[1] * u, p[2] + s * v) for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        p, q = corners(a), corners(b)
        centre = [(a[k] + b[k]) / 2 for k in range(3)]
        quads = [[p[i], p[(i + 1) % 4], q[(i + 1) % 4], q[i]] for i in range(4)] + [p[::-1], q]
        for quad in quads:
            for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                u = [tri[1][k] - tri[0][k] for k in range(3)]
                v = [tri[2][k] - tri[0][k] for k in range(3)]
                n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                out = [sum(t[k] for t in tri) / 3 - centre[k] for k in range(3)]
                if sum(n[k] * out[k] for k in range(3)) < 0:
                    tri = (tri[0], tri[2], tri[1])
                faces.append((rail['name'], material, list(tri), None))
    return faces


if __name__ == '__main__':
    # Smallest check: a sloped rail gives 12 outward triangles and stepped clips.
    boxes, rails = [], []
    railing(lambda *b: boxes.append(b), rails, 'demo', (0, 0, 0), (0, 3, 1.8))
    faces = rail_faces(rails)
    assert len(faces) == 12 * (1 + BARS), len(faces)
    clips = [b for b in boxes if '_clip_' in b[0]]
    assert len(clips) == 10 and abs(clips[-1][2][2] - 2.8) < 1e-9
    print('ok')
