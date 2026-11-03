"""The low east block between Povo 1 and Via Sommarive: library (BUP), mensa, the glass
roof over the passage between them and the red entrance stair down to the Povo 1 -1 lane.

Sources
- Outlines and heights: OSM 275318462 (library), 275318465 (mensa), 275318456 (glass roof);
  LiDAR roofs 382.5 m over the -1 lane at 373.4 m, the glass roof at ~383.5 m.
- Layouts: canteen and library evacuation plans (walk_2026-10-27 images 12, 13, 15): mensa
  dining hall upstairs, bar and kitchen at -1; library reading rooms with a row of study
  booths along the street side. Aerials POVO1_1, POVO1_4: library north, mensa south, glass
  roof and the street entrance stair between them.
- Looks: white metal panels with glass bands over a glazed ground floor (photo 14), glass
  roof on a steel frame (photo 14), red stair and paving (P055-P060).
Levels: -1 at 373.4 m (Povo 1 -1 datum), 0 at 377.9 m (street level), roof 382.5 m.
"""

from shapely.geometry import box as rect

import building as b
from building import Room, row_y

ORIGIN_Z = 373.4


class Mensa(b.Spec):
    # West wall in line with the library's (user's corrected campus map, 2 Nov): the OSM
    # outline 1.6 m further west is the canopy over the -1 lane, not the wall.
    name = 'Mensa'
    origin = (666287.5, 5103689.5, ORIGIN_Z)
    X, Y = 13.8, 33.2
    levels = {-1: 0.0, 0: 4.5}
    roof = 9.1
    cores = [('N', (0.3, 26.0, 6.9, 32.9), 'S')]
    lifts = [((6.9, 28.0, 9.9, 32.9), 'E')]
    doors = {'W': [(-1, 4.6, 7.9), (-1, 23.2, 25.8)],        # glass porch to the bar, service corridor
             'E': [(0, 23.2, 25.8)]}                         # street level, Via Sommarive

    def style(self, frame, level):
        if frame[0] == 'E' and level == -1:
            return 'solid'                                   # against the street embankment
        if frame[0] == 'N' and level == -1:
            return 'panel'                                   # grey side wall of the entrance stair (32, 33)
        return 'curtain' if level == -1 else 'ribbon'

    def rooms(self, level):
        wc = Room('WC', 'wc', (8.5, 26.0, 13.5, 32.9), [('S', 11.0, 1.0)])
        if level == -1:
            return [Room('Bar', 'hall', (0.3, 0.3, 13.5, 14.0), [('N', 8.0, 1.6)]),
                    Room('Cucina', 'service', (0.3, 14.0, 13.5, 23.0), [('N', 3.0, 1.2)]), wc]
        return [Room('Sala ristorazione', 'hall', (0.3, 0.3, 13.5, 20.0), [('N', 8.0, 3.0)]), wc]

    def lights(self, level):
        return [((1.0, 24.5), (8.0, 24.5))]

    def extras(self, g, m):
        glass_roof(g)
        entrance_stair(g)
        # Canopy along the whole west side at the -1/0 transition, over the -1 lane, and
        # the small glass porch with two doors under it (user's map: black line, yellow box).
        g.box('canopy', -1.6, 0.0, 4.2, 0.0, self.Y, 4.5, 'panel')
        porch(g, -1.6, 4.0, 8.5, 3.0)
        plant_room(g, self, (2.0, 2.0, 11.5, 9.0), 2.6)


class Library(b.Spec):
    name = 'Biblioteca'
    origin = (666287.5, 5103732.6, ORIGIN_Z)
    X, Y = 13.9, 54.5
    levels = {-1: 0.0, 0: 4.5}
    roof = 9.1
    cores = [('N', (0.3, 47.8, 6.9, 54.2), 'S')]
    lifts = [((6.9, 50.5, 9.9, 54.2), 'E')]
    # The entrance stair fills the passage wall to wall (33), so the door is on the lane side.
    doors = {'W': [(-1, 2.0, 4.4)]}

    def style(self, frame, level):
        if frame[0] == 'E' and level == -1:
            return 'solid'
        if frame[0] == 'S' and level == -1:
            return 'panel'                                   # grey side wall of the entrance stair (32, 33)
        if frame[0] == 'W' or level == -1:
            return 'curtain'                                 # glazed towards Povo 1 (P008)
        return 'ribbon'

    def rooms(self, level):
        booths = row_y(['Box studio'] * 10, [6.0 + k * 4.18 for k in range(11)], 10.3, 13.6, 'study', 'W', .9)
        if level == -1:
            return booths + [Room('Sala lettura', 'study', (0.3, 30.0, 8.5, 47.8), [('E', 39.0, 1.6)]),
                             Room('Uffici', 'office', (0.3, 18.0, 8.5, 30.0), [('E', 24.0, 1.0)]),
                             Room('Sala lettura', 'study', (0.3, 6.0, 8.5, 18.0), [('E', 12.0, 1.6)]),
                             Room('WC', 'wc', (0.3, 0.3, 8.5, 6.0), [('E', 3.0, 1.0)])]
        return booths + [Room('Sala lettura', 'study', (0.3, 0.3, 8.5, 47.8), [('E', 24.0, 1.6), ('E', 40.0, 1.6)])]

    def lights(self, level):
        return [((9.4, 1.0), (9.4, 47.0))]

    def extras(self, g, m):
        plant_room(g, self, (2.0, 44.0, 11.5, 52.5), 2.6)


# The passage between the mensa (north wall y 33.2) and the library (south wall y 43.1),
# mensa frame. Both buildings start at x 0 (E 666287.5): the stair's foot is there.
PASSAGE_Y = (33.2, 43.1)
POVO1_EAST = 666274.8 - 666287.5                              # Povo 1 east facade, mensa frame
STAIR_TOP, STAIR_N = 5.0, 14                                  # street ~378.4 m; 2 x 14 risers


def stair_height(x):
    """Walking surface of the entrance stair at x (mensa frame)."""
    rise = STAIR_TOP / (2 * STAIR_N)
    run = (STAIR_N - 1) * .3
    if x <= 0:
        return 0.0
    if x < run:
        return (int(x / .3) + 1) * rise
    if x < run + 2.0:
        return STAIR_N * rise
    if x < 2 * run + 2.0:
        return (STAIR_N + int((x - run - 2.0) / .3) + 1) * rise
    return STAIR_TOP


def glass_roof(g):
    """Steel and glass roof over the passage, from Povo 1's east facade to the street:
    galvanised square columns along both sides with diagonal braces up to the roof girders
    (photos 23-10 32, 33, P018). Glass at 10.1 m over the -1 lane."""
    (y0, y1), x0, x1, z = PASSAGE_Y, POVO1_EAST + .3, 13.8, 10.1
    for k in range(11):                                       # cross beams
        x = x0 + k * (x1 - x0) / 10
        g.box('canopy', x - .08, y0, z - .45, x + .08, y1, z, 'louvre')
    for y in (y0 + .2, y1 - .2):                              # edge girders
        g.box('canopy', x0, y - .15, z - .75, x1, y + .15, z - .45, 'louvre')
    g.box('glass', x0, y0, z, x1, y1, z + .04, 'glass')
    columns = [x0 + .4, -7.0, -1.5, 4.9, 9.6, x1 - .4]
    for y, inward in ((y0 + .45, 1), (y1 - .45, -1)):
        for k, x in enumerate(columns):
            base = stair_height(x) if x > 0 else 0.0
            g.box('canopy', x - .18, y - .18, base - .3, x + .18, y + .18, z - .75, 'louvre')
            if k + 1 < len(columns):                          # diagonal up to the next column's head
                nx = columns[k + 1]
                g.beam('canopy', (x, y, base + 3.2), (nx, y, z - .8), .12, .2, 'louvre')
            g.beam('canopy', (x, y, z - 3.0), (x, y + inward * 2.6, z - .8), .12, .2, 'louvre')
        for k in range(len(columns) - 1):                     # hanging lanterns (P018)
            g.box('canopy', (columns[k] + columns[k + 1]) / 2 - .2, y - .2, z - 2.6,
                  (columns[k] + columns[k + 1]) / 2 + .2, y + .2, z - 2.0, 'dark')


def entrance_stair(g):
    """Red stair from Via Sommarive down to the -1 lane, wall to wall between the mensa and
    the library, two flights and a landing, foot at their west walls (P058-P060, 23-10 33)."""
    y0, y1 = PASSAGE_Y[0] + .02, PASSAGE_Y[1] - .02
    rise = STAIR_TOP / (2 * STAIR_N)
    run = (STAIR_N - 1) * .3
    for k in range(STAIR_N - 1):                                         # lower flight
        g.box('estair', k * .3, y0, -.5, (k + 1) * .3, y1, (k + 1) * rise, 'red_pave')
    g.box('estair', run, y0, -.5, run + 2.0, y1, STAIR_N * rise, 'red_pave')    # landing
    for k in range(STAIR_N - 1):                                         # upper flight
        x = run + 2.0 + k * .3
        g.box('estair', x, y0, -.5, x + .3, y1, (STAIR_N + k + 1) * rise, 'red_pave')
    x = 2 * run + 2.0
    g.box('estair', x, y0, -.5, 16.0, y1, STAIR_TOP, 'red_pave')        # street landing
    for y in (y0 + .1, y1 - .1, (y0 + y1) / 2):                          # wall rails, central rail
        g.railing('estair', (0.0, y), (run, y), rise, run / .3 * rise, height=.9)
        g.railing('estair', (run + 2.0, y), (x, y), STAIR_N * rise + rise, STAIR_TOP, height=.9)


def porch(g, x0, y0, y1, h):
    """Small glass box against a facade with two doors on its outer face (mensa west)."""
    g.box('porch', x0, y0, h - .2, 0.0, y1, h, 'panel')                  # roof
    g.box('porch', x0, y0, -.02, 0.0, y1, .02, 'concrete')               # floor
    for y in (y0, y1 - .06):
        g.box('porch', x0, y, 0, 0.0, y + .06, h - .2, 'alu')
        g.box('glass', x0 + .06, y + .02, 0, -.02, y + .04, h - .2, 'glass')
    mid = (y0 + y1) / 2
    doors = [(mid - 1.9, mid - .3), (mid + .3, mid + 1.9)]
    edges = [y0, *[v for d in doors for v in d], y1]
    for a, c in zip(edges[::2], edges[1::2]):                            # fixed panes between doors
        g.box('glass', x0 + .02, a, 0, x0 + .04, c, h - .2, 'glass')
    for a, c in doors:
        g.box('porch', x0, a - .05, 0, x0 + .06, a, h - .2, 'alu')
        g.box('porch', x0, c, 0, x0 + .06, c + .05, h - .2, 'alu')
        g.box('porch', x0, a, 2.3, x0 + .06, c, h - .2, 'alu')


def plant_room(g, s, box, h):
    """Rooftop plant room with a grille band and two roof units (aerials POVO1_1, POVO1_4)."""
    b.plant_room(g, box, s.roof, h)


b.M['red_pave'] = 'materials/povo/red_paving.vmat'
MENSA = Mensa()
LIBRARY = Library()
PASSAGE_EN = rect(666274.8, 5103722.7, 666303.5, 5103732.6)      # glass roof and stair, E/N
