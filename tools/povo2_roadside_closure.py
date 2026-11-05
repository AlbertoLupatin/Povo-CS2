"""Close the Povo 2 roadside around the bridge-road corner (user review, 5 Nov 2026).

The user's in-game screenshot from the sloped front-road sidewalk showed three
faults, checked against the street photos (walk 2026-10-23 photos 24-26,
walk 2026-10-26 photos 19-20, WhatsApp photo 2026-10-29 2.16.20 PM (2)) and the
aerial images embedded in ``Povo2 Gardens.drawio``:

* The street-level garden between the -1 terrace/DOWN stair and Garden -2 had
  disappeared. ``povo2_drawio_entrance`` deleted the earlier grass embankments
  without replacing them, leaving open voids down to the context underlay.
* Through those voids and the uncapped area west of Garden -2, bare -1 ceilings,
  the -2 garden-approach doors and wall ends were visible from the road.
* There was no barrier between the bridge-road footway and the sunken -1
  terrace (a 3.6-7 m unguarded drop), and no fence between the front-road
  sidewalk and the street garden/garden/entrance courtyard. Remnants of an
  obsolete street ramp and its guard bars floated above Garden -2.

This pass restores the street garden as solid ground with a lawn at street
level, raises Garden -2's south retaining wall to street level, caps the open
-1 roofs at ground level, adds a retaining wall flush with the footway and the
grey grating fence on a concrete kerb along both roads. Garden -2 stays open
and visible through the fence. The approved Povo 2 -1 layout (rooms, terrace,
both stairs, lower approach and garden) is not changed. Dimensions follow the
existing geometry; the fence and kerb heights are photo estimates.
"""
import math

from .povo_room_fitout import subtract_box
from .povo_stairs import railing
from .build_povo2_west_offices import subtract_rect

BASE = -3.42
STREET_Z = 4.
LAWN_SKIN = .12
CAP_BOTTOM = 3.5
KERB_HEIGHT = .35
FENCE_HEIGHT = 1.7
BAR_SPACING = .1
POST_SPACING = 2.

# Plan rectangles [east min, north min, east max, north max], campus metres.
LAWNS = dict(
    stair_edge=[31.88, 2., 35.75, 2.67],
    west=[35.83, 2.75, 42.02, 8.57],
    west_corner=[35.83, 8.57, 38., 8.75],
    east=[45.58, 2.75, 55.5, 8.57],
    landing_east=[45.42, .13, 56.7, 2.],
    landing_edge=[45.3, .29, 45.42, 2.],
    east_corner=[55.5, 2., 56.7, 2.75])
# Solid support under the retained paved strip inside the front-road fence.
SIDEWALK_BODY = [55.5, 2.75, 56.7, 8.75]
# Garden -2 south retaining wall, raised from the old -1 passage level.
GARDEN_WALL = [[38., 8.57, 42.02, 8.75], [45.58, 8.57, 55.5, 8.75]]
GARDEN_WALL_WEST = [37.82, 8.75, 38., 11.25]
# Ground-level cap over the open -1 roofs; existing ground-floor slabs win.
CAP_REGIONS = [[31., 2., 31.88, 8.83], [31., 8.83, 37.82, 11.], [35.83, 8.75, 37.82, 8.83],
               [20.36, 11., 37.82, 19.4], [20.36, 19.4, 25.4, 19.5], [34.5, 19.4, 37.82, 19.91]]
# -2 office garden approach: closed sides and ceiling under the new cap.
APPROACH = [34.5, 12.5, 37.82, 14.5]
APPROACH_TOP = -.1
# Missing 2 m of bridge-road footway between its end and the corner paving.
FOOTWAY_GAP = [50., -2., 52., -.6]
# Road-edge wall between the footway and the terrace/stair: plan intervals in
# east, with the footway edge north and the shared terrace-wall face north.
ROAD_EDGE_RUNS = [(8.34, 20.34), (23.16, 56.7)]
ROAD_EDGE_NORTH = .13
# Slot between the wall and the terrace/DOWN-stair guard posts (N0.27).
EDGE_SLOT = (23.16, 42.3, .27)
KERB_SOUTH = -.2
FRONT_KERB = (56.7, 57.03)
FRONT_FENCE_END = 28.3
REMNANTS = ('exterior_povo1_street_yard_guard', 'exterior_povo1_street_grade')

FACES = ((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7))


def footway_z(x):
    """Footway grade at the bridge-road edge, from the exported road meshes."""
    if x <= 20.34:
        return 3.08 + (x + 23.) * (4.08 - 3.08) / (20.34 + 23.)
    if x <= 32.:
        return 4.12
    if x <= 50.:
        return 4.12 + (x - 32.) * 3.6 / 18.
    if x <= 52.:
        return 7.72 + (x - 50.) * (7.6 - 7.72) / 2.
    return 7.6


def _hexa(name, footprint, bottom, top, material):
    """Closed prism over a counterclockwise plan quad with per-corner heights."""
    vertices = [(x, y, z) for (x, y), z in zip(footprint, bottom)] + \
               [(x, y, z) for (x, y), z in zip(footprint, top)]
    return dict(name=name, vertices=vertices, faces=FACES, material=material)


def _along_x(name, x0, x1, y0, y1, z0, z1, material):
    """Prism over x0..x1 x y0..y1; z0/z1 give (bottom, top) at x0 and x1."""
    plan = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return _hexa(name, plan, [z0[0], z1[0], z1[0], z0[0]], [z0[1], z1[1], z1[1], z0[1]], material)


def _along_y(name, y0, y1, x0, x1, z0, z1, material):
    plan = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return _hexa(name, plan, [z0[0], z0[0], z1[0], z1[0]], [z0[1], z0[1], z1[1], z1[1]], material)


def _post(name, x, y, half, z0, z1, material='exterior_fence'):
    return _along_x(name, x - half, x + half, y - half, y + half, (z0, z1), (z0, z1), material)


def _surface_top(meshes, boxes, x, y, zmax=9.):
    """Highest walking surface of the paved exterior at (x, y)."""
    best = None
    for mesh in meshes:
        if mesh['material'] not in ('exterior_paving', 'exterior_asphalt') or 'bus' in mesh['name']:
            continue
        vv = mesh['vertices']
        if not (min(v[0] for v in vv) <= x <= max(v[0] for v in vv) and
                min(v[1] for v in vv) <= y <= max(v[1] for v in vv)):
            continue
        for f in mesh['faces']:
            a, b, c = (vv[i] for i in f[:3])
            d = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if d <= 1e-9:
                continue  # downward or vertical faces
            u = ((x - a[0]) * (c[1] - a[1]) - (y - a[1]) * (c[0] - a[0])) / d
            v = ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) / d
            if u < -1e-9 or v < -1e-9 or u + v > 1 + 1e-9:
                continue
            z = a[2] + u * (b[2] - a[2]) + v * (c[2] - a[2])
            if z <= zmax and (best is None or z > best):
                best = z
    for name, lo, hi, material in boxes:
        if material == 'exterior_paving' and lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1] and hi[2] <= zmax:
            best = hi[2] if best is None else max(best, hi[2])
    return best


def _fence(meshes, prefix, start, end, cross, grade, axis):
    """Grey grating fence on a kerb top: posts, four rails and dense flat bars.

    ``grade(t)`` is the kerb-top elevation at station ``t`` along the run;
    ``axis`` is the plan axis the run follows and ``cross`` its fixed other
    coordinate. Everything here is visual; ``_barrier`` carries collision.
    """
    def place(t):
        return (t, cross) if axis == 0 else (cross, t)
    def piece(name, t0, t1, c0, c1, b0, b1):
        build = _along_x if axis == 0 else _along_y
        meshes.append(build(name, t0, t1, c0, c1, b0, b1, 'exterior_fence'))
    length = end - start
    posts = max(1, math.ceil(length / POST_SPACING))
    stations = [start + length * i / posts for i in range(posts + 1)]
    for i, t in enumerate(stations):
        x, y = place(t)
        meshes.append(_post(f'{prefix}_post_{i}', x, y, .03, grade(t) - .02, grade(t) + FENCE_HEIGHT))
    rails = ((.06, .05, .025), (.62, .02, .01), (1.16, .02, .01), (FENCE_HEIGHT - .05, .05, .025))
    for i, (t0, t1) in enumerate(zip(stations, stations[1:])):
        g0, g1 = grade(t0), grade(t1)
        for k, (lift, thick, half) in enumerate(rails):
            piece(f'{prefix}_rail_{i}_{k}', t0 + .03, t1 - .03, cross - half, cross + half,
                  (g0 + lift - thick / 2, g0 + lift + thick / 2), (g1 + lift - thick / 2, g1 + lift + thick / 2))
        count = max(1, round((t1 - t0) / BAR_SPACING))
        for j in range(1, count):
            t = t0 + (t1 - t0) * j / count
            g = g0 + (g1 - g0) * j / count
            x, y = place(t)
            along, across = (.012, .015) if axis == 0 else (.015, .012)
            z = (g + .085, g + FENCE_HEIGHT - .075)
            meshes.append(_along_x(f'{prefix}_bar_{i}_{j}', x - along, x + along, y - across, y + across,
                                   z, z, 'exterior_fence'))


def _barrier(name, start, end, cross, grade, axis, samples):
    """Thin invisible collision wall covering the whole fence height."""
    pieces = []
    for i, (t0, t1) in enumerate(zip(samples, samples[1:])):
        g0, g1 = grade(t0), grade(t1)
        b0, b1 = (g0 - .02, g0 + FENCE_HEIGHT + .1), (g1 - .02, g1 + FENCE_HEIGHT + .1)
        if axis == 0:
            pieces.append(_along_x(f'{name}_{i}', t0, t1, cross - .04, cross + .04, b0, b1, 'exterior_fence'))
        else:
            pieces.append(_along_y(f'{name}_{i}', t0, t1, cross - .04, cross + .04, b0, b1, 'exterior_fence'))
    return pieces


def _stations(start, end, breaks, step=.5):
    points = {start, end, *[b for b in breaks if start < b < end]}
    count = max(1, math.ceil((end - start) / step))
    points.update(start + (end - start) * i / count for i in range(count + 1))
    return sorted(points)


def _merge_linear(samples, grade, tolerance=1e-4):
    """Drop samples where the grade is linear between neighbours."""
    kept = [samples[0]]
    for i in range(1, len(samples) - 1):
        a, b, c = kept[-1], samples[i], samples[i + 1]
        expected = grade(a) + (grade(c) - grade(a)) * (b - a) / (c - a)
        if abs(expected - grade(b)) > tolerance:
            kept.append(b)
    kept.append(samples[-1])
    return kept


def extend(boxes, levels):
    ext = levels[0]['exterior']
    spec = levels[1]['connection']['povo2']
    rails = spec['stairs']['rails']
    added = []
    def box(name, lo, hi, material):
        if any(a >= b for a, b in zip(lo, hi)):
            raise ValueError(name)
        added.append(('p2_roadside_' + name, tuple(lo), tuple(hi), material))
    # 1. Remove the floating remnants of the obsolete Povo 1 street ramp.
    result = [b for b in boxes if not b[0].startswith(REMNANTS)]
    for key in ('meshes', 'collision_meshes'):
        ext[key] = [m for m in ext[key] if not m['name'].startswith(REMNANTS)]
    # 2. Street-level garden: closed earth with a lawn at street level.
    for name, r in LAWNS.items():
        box('lawn_body_' + name, (r[0], r[1], BASE), (r[2], r[3], STREET_Z - LAWN_SKIN), 'exterior_concrete')
        box('lawn_' + name, (r[0], r[1], STREET_Z - LAWN_SKIN), (r[2], r[3], STREET_Z), 'exterior_grass')
    r = SIDEWALK_BODY
    box('sidewalk_body', (r[0], r[1], BASE), (r[2], r[3], 3.78), 'exterior_concrete')
    for i, r in enumerate(GARDEN_WALL):
        box(f'garden_wall_south_{i}', (r[0], r[1], .4), (r[2], r[3], STREET_Z), 'wall')
    r = GARDEN_WALL_WEST
    box('garden_wall_west', (r[0], r[1], BASE), (r[2], r[3], STREET_Z), 'wall')
    # 3. The -2 approach becomes a closed passage under the new cap.
    a, b, c, d = APPROACH
    box('approach_wall_south', (a + .1, b - .16, BASE), (c, b, APPROACH_TOP), 'wall')
    box('approach_wall_north', (a + .1, d, BASE), (c, d + .16, APPROACH_TOP), 'wall')
    box('approach_ceiling', (a + .1, b - .16, APPROACH_TOP - .07), (c, d + .16, APPROACH_TOP), 'ceiling_panel')
    # 4. Ground-level cap wherever no existing slab, wall or roof occupies it.
    occupied = [[lo[0], lo[1], hi[0], hi[1]] for _, lo, hi, _ in result
                if lo[2] < STREET_Z - 1e-6 and hi[2] > CAP_BOTTOM + 1e-6
                and hi[0] - lo[0] > 1e-6 and hi[1] - lo[1] > 1e-6]
    caps = [list(r) for r in CAP_REGIONS]
    for hole in occupied:
        caps = [p for r in caps for p in subtract_rect(r, hole)]
    caps = [r for r in caps if r[2] - r[0] > .02 and r[3] - r[1] > .02]
    for i, r in enumerate(caps):
        box(f'cap_{i}', (r[0], r[1], CAP_BOTTOM), (r[2], r[3], STREET_Z), 'exterior_concrete')
    # 5. Missing footway piece, at the adjoining footway/corner grades.
    a, b, c, d = FOOTWAY_GAP
    gap = _along_x('exterior_p2_roadside_footway_gap', a, c, b, d,
                   (footway_z(a) - .22, footway_z(a)), (footway_z(c) - .22, footway_z(c)), 'exterior_paving')
    ext['meshes'].append(gap); ext['collision_meshes'].append(gap)
    # 6. Road-edge retaining wall flush with the footway, with a kerb on top.
    walls = []
    for k, (x0, x1) in enumerate(ROAD_EDGE_RUNS):
        samples = _merge_linear(_stations(x0, x1, (20.34, 32., 50., 52.)), footway_z)
        for i, (u, v) in enumerate(zip(samples, samples[1:])):
            south = 0. if u >= 52. else -.6
            if south < KERB_SOUTH:
                walls.append(_along_x(f'exterior_p2_roadside_edge_{k}_{i}', u, v, south, KERB_SOUTH,
                                      (BASE, footway_z(u)), (BASE, footway_z(v)), 'exterior_concrete'))
            walls.append(_along_x(f'exterior_p2_roadside_kerb_{k}_{i}', u, v, KERB_SOUTH, ROAD_EDGE_NORTH,
                                  (BASE, footway_z(u) + KERB_HEIGHT), (BASE, footway_z(v) + KERB_HEIGHT),
                                  'exterior_concrete'))
    x0, x1, north = EDGE_SLOT
    samples = _merge_linear(_stations(x0, x1, (32.,)), footway_z)
    for i, (u, v) in enumerate(zip(samples, samples[1:])):
        walls.append(_along_x(f'exterior_p2_roadside_edge_slot_{i}', u, v, ROAD_EDGE_NORTH, north,
                              (BASE, footway_z(u)), (BASE, footway_z(v)), 'exterior_concrete'))
    ext['meshes'].extend(walls); ext['collision_meshes'].extend(walls)
    # Carve the low concrete apron that the wall now replaces.
    for k, (x0, x1) in enumerate(ROAD_EDGE_RUNS):
        hole = ((x0, -.6, BASE - .1), (x1, ROAD_EDGE_NORTH, 8.))
        result = [p for item in result for p in
                  (subtract_box(item, hole) if item[0].startswith('exterior_ground') else [item])]
    # Same for the lawn footprints.
    for r in [*LAWNS.values(), SIDEWALK_BODY]:
        hole = ((r[0], r[1], BASE - .1), (r[2], r[3], STREET_Z + .01))
        result = [p for item in result for p in
                  (subtract_box(item, hole) if item[0].startswith('exterior_ground') else [item])]
    # 7. Front-road kerb following the sloped sidewalk.
    x0, x1 = FRONT_KERB
    front_samples = _stations(KERB_SOUTH, FRONT_FENCE_END, (0., .58, 15., 20.), .5)
    tops = {y: _surface_top(ext['collision_meshes'], result, x1 + .05, y) for y in front_samples}
    last = 7.6
    for y in front_samples:
        if tops[y] is None:
            tops[y] = last
        last = tops[y]
    all_samples = list(front_samples)
    front_grade = lambda y: _interp(all_samples, tops, y)
    front_samples = _merge_linear(all_samples, front_grade, .005)
    kerbs = []
    for i, (u, v) in enumerate(zip(front_samples, front_samples[1:])):
        kerbs.append(_along_y(f'exterior_p2_roadside_front_kerb_{i}', u, v, x0, x1,
                              (front_grade(u) - .1, front_grade(u) + KERB_HEIGHT),
                              (front_grade(v) - .1, front_grade(v) + KERB_HEIGHT), 'exterior_concrete'))
    ext['meshes'].extend(kerbs); ext['collision_meshes'].extend(kerbs)
    # 8. Grating fence on both kerbs; one barrier per run carries collision.
    fences = []
    barriers = []
    road_cross = (KERB_SOUTH + ROAD_EDGE_NORTH) / 2
    for k, (s0, s1) in enumerate(ROAD_EDGE_RUNS):
        end = (x0 + x1) / 2 if s1 >= FRONT_KERB[0] else s1
        grade = lambda t: footway_z(min(t, 56.7)) + KERB_HEIGHT
        _fence(fences, f'exterior_p2_roadside_fence_road_{k}', s0, end, road_cross, grade, 0)
        barriers.extend(_barrier(f'exterior_p2_roadside_fence_road_barrier_{k}', s0, end, road_cross, grade, 0,
                                 _merge_linear(_stations(s0, end, (20.34, 32., 50., 52.)), grade)))
    front_cross = (x0 + x1) / 2
    grade = lambda t: front_grade(t) + KERB_HEIGHT
    _fence(fences, 'exterior_p2_roadside_fence_front', road_cross, FRONT_FENCE_END, front_cross, grade, 1)
    barriers.extend(_barrier('exterior_p2_roadside_fence_front_barrier', road_cross, FRONT_FENCE_END,
                             front_cross, grade, 1, [s for s in front_samples if s >= road_cross] or
                             [road_cross, FRONT_FENCE_END]))
    ext['meshes'].extend(fences)
    ext['collision_meshes'].extend(barriers)
    # 9. Guards where the restored lawn meets a drop.
    newrails = []
    def rail(name, p, q):
        railing(lambda n, lo, hi, m: added.append((n, lo, hi, m)), newrails, 'p2_roadside_' + name, p, q)
    rail('stair_north', (31.88, 2.05, STREET_Z), (42.02, 2.05, STREET_Z))
    rail('landing_east', (45.36, .29, STREET_Z), (45.36, 2., STREET_Z))
    rail('garden_south_west', (37.9, 8.66, STREET_Z), (42.02, 8.66, STREET_Z))
    rail('garden_south_east', (45.58, 8.66, STREET_Z), (55.5, 8.66, STREET_Z))
    rail('garden_west_south', (37.8, 8.75, STREET_Z), (37.8, 11.25, STREET_Z))
    rails.extend(newrails)
    ext['roadside_closure'] = dict(
        source='User in-game review 5 Nov 2026; street photos walk_2026-10-23 24-26, walk_2026-10-26 19-20, walk_2026_10_29 WhatsApp (2)',
        lawns=LAWNS, caps=caps, road_edge_runs=ROAD_EDGE_RUNS, front_fence=[*FRONT_KERB, KERB_SOUTH, FRONT_FENCE_END],
        fence=dict(kerb_height=KERB_HEIGHT, height=FENCE_HEIGHT, bar_spacing=BAR_SPACING, post_spacing=POST_SPACING),
        removed=list(REMNANTS),
        preserve='Approved Povo 2 -1 rooms, terrace, both stairs, lower approach and Garden -2 unchanged')
    return result + added


def _interp(samples, values, t):
    if t <= samples[0]:
        return values[samples[0]]
    for a, b in zip(samples, samples[1:]):
        if a <= t <= b:
            return values[a] + (values[b] - values[a]) * (t - a) / (b - a) if b > a else values[a]
    return values[samples[-1]]
