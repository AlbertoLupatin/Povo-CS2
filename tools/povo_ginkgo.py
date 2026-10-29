"""Deterministic young roadside ginkgos, in local metres.

Actual fan silhouettes are geometry, so no downloaded model or alpha texture is
needed. Only the slim lower trunk collides; the crown stays permeable.
"""
import hashlib
import math
import random


def tree(name, x, y, z, height=2.8, prefix=''):
    if not 2.5 <= height <= 3.0:
        raise ValueError('Roadside ginkgo height must be between 2.5 and 3 m')
    rng = random.Random(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], 'big'))
    meshes = []
    bark = dict(name=name+'_branches', vertices=[], faces=[], material=prefix+'trunk')
    leaves = [dict(name=name+f'_fans_{i}', vertices=[], faces=[], material=prefix+mat)
              for i, mat in enumerate(('ginkgo_leaf', 'ginkgo_leaf_light', 'ginkgo_leaf_dark'))]

    def add(a, b):
        return tuple(a[i]+b[i] for i in range(3))

    def mul(a, s):
        return tuple(v*s for v in a)

    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    def unit(a):
        return mul(a, 1/math.sqrt(sum(v*v for v in a)))

    def branch(a, b, r0, r1):
        axis = unit(tuple(b[i]-a[i] for i in range(3)))
        u = unit(cross(axis, (0, 1, 0)))
        v = cross(axis, u)
        offset = len(bark['vertices']); sides = 7
        for centre, radius in ((a, r0), (b, r1)):
            for j in range(sides):
                angle = j*2*math.pi/sides
                bark['vertices'].append(add(centre, add(mul(u, radius*math.cos(angle)), mul(v, radius*math.sin(angle)))))
        for j in range(sides):
            k = (j+1) % sides
            bark['faces'].extend(((offset+j, offset+k, offset+sides+k),
                                  (offset+j, offset+sides+k, offset+sides+j)))
        for j in range(1, sides-1):
            bark['faces'].extend(((offset, offset+j+1, offset+j),
                                  (offset+sides, offset+sides+j, offset+sides+j+1)))

    def fan(base, angle, size):
        # Petiole point and a scalloped, bilobed fan edge. A shallow centre
        # notch makes the ginkgo outline legible even without a leaf texture.
        tilt = rng.uniform(-.35, .7)
        forward = (math.cos(angle)*math.cos(tilt), math.sin(angle)*math.cos(tilt), math.sin(tilt))
        side = (-math.sin(angle), math.cos(angle), 0)
        mesh = rng.choices(leaves, (6, 3, 2))[0]; offset = len(mesh['vertices'])
        mesh['vertices'].append(base)
        for j in range(9):
            theta = math.radians(-72+j*18)
            radius = size*(.77 if j == 4 else 1+rng.uniform(-.035, .035))
            mesh['vertices'].append(add(base, add(mul(forward, radius*math.cos(theta)), mul(side, radius*math.sin(theta)))))
        mesh['faces'].extend((offset, offset+j+1, offset+j+2) for j in range(8))

    # Slender central leader and ascending, irregular branches: narrow at the
    # top, fuller below, rather than the old cuboid crown.
    origin = (x, y, z)
    branch(origin, (x+.025, y-.018, z+height), .055, .006)
    phase = rng.uniform(0, 2*math.pi)
    for i in range(13):
        t = i/12
        angle = phase+i*2.39996+rng.uniform(-.16, .16)
        reach = (.82-.59*t)*height/2.8*rng.uniform(.9, 1.06)
        start = (x+.025*t, y-.018*t, z+height*(.40+.48*t))
        end = (x+reach*math.cos(angle), y+reach*math.sin(angle), z+height*(.63+.31*t))
        branch(start, end, .022*(1-.55*t), .004)
        for j in range(5):
            f = .26+j*.17
            anchor = tuple(start[k]+(end[k]-start[k])*f for k in range(3))
            turn = angle+(-1 if j % 2 else 1)*rng.uniform(.45, 1.05)
            length = rng.uniform(.10, .23)*(1-.45*t)
            tip = add(anchor, (length*math.cos(turn), length*math.sin(turn), rng.uniform(.06, .14)))
            branch(anchor, tip, .006, .002)
            for k in range(6):
                base = tuple(anchor[a]+(tip[a]-anchor[a])*(.35+.13*k) for a in range(3))
                fan(base, turn+k*2.39996, rng.uniform(.095, .135)*height/2.8)
    meshes.extend((bark, *leaves))
    # Keep the exact declared total height even for the tallest leaf tips.
    for mesh in meshes:
        mesh['vertices'] = [(a, b, max(z, min(c, z+height))) for a, b, c in mesh['vertices']]
    # The square collision proxy sits entirely inside the tapered round bark.
    trunk = (name+'_trunk', (x-.018, y-.018, z), (x+.018, y+.018, z+height*.58), prefix+'trunk')
    record = dict(name=name, species='Ginkgo biloba', base=[x, y, z], height_metres=height,
                  crown='Ascending branches with bilobed fan leaves', leaf_count=390)
    return trunk, meshes, record


def height_for(index):
    return (2.65, 2.8, 2.95)[index % 3]
