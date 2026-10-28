"""Library stair, sloping grass and street wall north of the Povo 1 courtyard.

User review of 28 October (photo 2 of the 27 October walk, from the bridge):
a long red stair runs down the library's whole north side, from the street
corner by the library's north-east corner (7.6 m) to the courtyard (4.0 m).
Beside it a grass strip with trees rises with the stair from the flat
courtyard grass; a railing and hedge keep stair and grass apart. Between
the grass and the bridge road's south sidewalk a wall with a metal fence
reaches the crosswalk on the Povo 1 side; west of it only a low edge
separates sidewalk and grass. As a game mechanic the grass can be climbed
from the courtyard to its fenced top.

Step count and widths are fitted to the photo and the existing geometry,
not measured.
"""
try:
    from .povo_stairs import railing
except ImportError:
    from povo_stairs import railing

# Plan bands between the library's north facade (N-13) and the sidewalk (N-9.5).
STAIR_Y = (-12.95, -11.45)
GRASS_Y = (-11.45, -9.55)
WALL_Y = (-9.6, -9.4)
FLAT_X, BOTTOM_X, TOP_X = 24.0, 36.0, 52.0
LOW, HIGH = 4.0, 7.6
STEPS = 30
CROSSWALK_EAST = 45.5
TREES = (30.0, 35.0, 40.5, 46.0, 50.5)


def grass_z(x):
    """Grass is flat in the courtyard and rises with the stair beside the library."""
    t = min(1, max(0, (x-BOTTOM_X)/(TOP_X-BOTTOM_X)))
    return LOW+(HIGH-LOW)*t


def sidewalk_z(x):
    """South sidewalk of the bridge road (footway mesh grade, capped at the street)."""
    return min(HIGH+.12, 4.12+max(0, x-32)*.2)  # reaches the cap at x50


def prism(name, top, material, thickness=.25):
    vertices = [(x, y, z-thickness) for x, y, z in top]+top
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return dict(name=name, vertices=vertices, faces=faces, material=material)


def extend(boxes, levels):
    exterior = levels[0].get('exterior')
    if exterior is None:
        return boxes
    # The generic road trees stood in the old pit; the grass gets its own.
    result = [b for b in boxes if not b[0].startswith(('exterior_road_tree_5_', 'exterior_road_tree_6_'))]
    rails = []
    def add(name, lo, hi, mat):
        result.append(('exterior_library_'+name, tuple(lo), tuple(hi), mat))
    def mesh(m):
        exterior['meshes'].append(m); exterior['collision_meshes'].append(m)
    # Red stair: solid steps from the courtyard up to the street corner.
    tread = (TOP_X-BOTTOM_X)/STEPS; rise = (HIGH-LOW)/STEPS
    for i in range(STEPS):
        x0 = BOTTOM_X+i*tread; top = LOW+(i+1)*rise
        add(f'stair_step_{i}', (x0, STAIR_Y[0], LOW-.2), (x0+tread, STAIR_Y[1], top), 'stair_red')
        add(f'stair_step_{i}_nosing', (x0, STAIR_Y[0], top-.02), (x0+.04, STAIR_Y[1], top+.005), 'stair_nosing')
    # Paved approach and flat grass at courtyard level, filling the old pit.
    add('stair_approach', (FLAT_X, STAIR_Y[0], LOW-.22), (BOTTOM_X, STAIR_Y[1], LOW), 'exterior_paving')
    add('grass_flat', (FLAT_X, GRASS_Y[0], LOW-.22), (BOTTOM_X, GRASS_Y[1], LOW), 'exterior_grass')
    mesh(prism('exterior_library_grass_slope',
               [(BOTTOM_X, GRASS_Y[0], LOW), (TOP_X, GRASS_Y[0], HIGH), (TOP_X, GRASS_Y[1], HIGH),
                (BOTTOM_X, GRASS_Y[1], LOW)], 'exterior_grass'))
    # Railing and hedge between stair and grass; a fence closes the grass top.
    railing(add, rails, 'library_stair_grass', (BOTTOM_X, GRASS_Y[0], LOW), (TOP_X, GRASS_Y[0], HIGH))
    railing(add, rails, 'library_grass_top', (TOP_X-.05, GRASS_Y[0], HIGH), (TOP_X-.05, GRASS_Y[1], HIGH), height=1.1)
    x = BOTTOM_X
    while x < TOP_X-.01:
        x1 = min(TOP_X, x+1.0)
        add(f'hedge_{x:.1f}', (x, GRASS_Y[0]+.05, grass_z(x)), (x1, GRASS_Y[0]+.6, grass_z(x1)+.85), 'exterior_tree')
        x = x1
    # Wall along the sidewalk: retaining wall + fence east of the crosswalk,
    # a low edge to the west. Sloping solids follow both grades exactly.
    breaks = [FLAT_X, 32.0, BOTTOM_X, CROSSWALK_EAST, 50.0, TOP_X]
    for i, (x0, x1) in enumerate(zip(breaks, breaks[1:])):
        lift = .1 if x0 >= CROSSWALK_EAST else .05
        (y0, y1), (b0, b1) = WALL_Y, (grass_z(x0)-.2, grass_z(x1)-.2)
        t0, t1 = sidewalk_z(x0)+lift, sidewalk_z(x1)+lift
        vertices = [(x0, y0, b0), (x1, y0, b1), (x1, y1, b1), (x0, y1, b0),
                    (x0, y0, t0), (x1, y0, t1), (x1, y1, t1), (x0, y1, t0)]
        mesh(dict(name=f'exterior_library_street_wall_{i}', vertices=vertices, material='exterior_concrete',
                  faces=[(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
                         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]))
    railing(add, rails, 'library_street_fence', (CROSSWALK_EAST, WALL_Y[1]-.1, sidewalk_z(CROSSWALK_EAST)+.1),
            (TOP_X, WALL_Y[1]-.1, sidewalk_z(TOP_X)+.1), height=1.1)
    # Join the sidewalk's end to the street corner above the library.
    add('sidewalk_corner', (50.0, WALL_Y[1], HIGH-.18), (TOP_X, -8.0, HIGH), 'exterior_paving')
    # Small trees in the grass (photo 2); canopies are visual only.
    for i, x in enumerate(TREES):
        z = grass_z(x); y = (GRASS_Y[0]+GRASS_Y[1])/2+.2
        add(f'tree_{i}_trunk', (x-.08, y-.08, z-.1), (x+.08, y+.08, z+2.4), 'exterior_trunk')
        add(f'tree_{i}_canopy_low', (x-.9, y-.85, z+2.1), (x+.9, y+.85, z+3.3), 'exterior_tree')
        add(f'tree_{i}_canopy_top', (x-.6, y-.6, z+3.3), (x+.6, y+.6, z+4.1), 'exterior_tree')
    levels[0]['library_stair'] = dict(
        rails=rails, steps=STEPS, rise_metres=rise, tread_metres=tread,
        stair_y=list(STAIR_Y), grass_y=list(GRASS_Y), wall_y=list(WALL_Y),
        x=[BOTTOM_X, TOP_X], z=[LOW, HIGH], crosswalk_east=CROSSWALK_EAST,
        source_photos=['walk_2026-10-27/image00002.jpeg'],
        status='User-described layout; step count and widths fitted, not measured')
    return result
