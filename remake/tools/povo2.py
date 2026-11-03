"""Povo 2 (Via Sommarive 9, "Blocco 2"), its street strip, glass boxes and the bridge.

Sources
- Outlines: OSM 1193371312 (main block), 1193371313 (strip along Via Sommarive, notched by
  Hole 2), 1193371314/15 (the two glass boxes on the plaza), 1192921194 (bridge).
- Rooms: the official evacuation plans of the ground floor and semi-basement rectified onto
  the outline (data/plans/povo2_floor0.png, povo2_floor-1.png), the -2 plan photo and the
  floor-1 department directory (walk_2026-10-27 images 37, 31).
- Levels (user, aerial POVO2_5, LiDAR): -2/-1/0/1 at 368.5/373.25/378.0/382.3 m. Floor 0
  is the street plaza on the strip roof; the courtyard floor and Holes 1/3 are at -1 and -2.
  Stairs climb two flights from 0 to 1 and three per storey below (user).
- Looks: beige stone frame with ribbon glazing on 0/1 over glass -1/-2 (POVO2_1, POVO2_5,
  P011, P071); cream 40 cm floor tiles, white walls, grey stairs with stainless railings
  (P074-P114); frosted green glass boxes (P010, P065-P069); grey-slab plaza (P012, P073);
  louvred bridge with diagonal steel (P013, P031).
"""

from shapely.geometry import box as rect

import building as b
from building import Room, row_x, row_y

E0, N0 = 666226.9, 5103810.85            # main block plan origin
HOLE2 = (45.65, 56.05)                   # y range of the notch between main block and strip
STRIP_Y = (9.25, 92.15)                  # y range of the strip (main-block frame)
BOX1, BOX2 = (20.6, 35.8), (67.0, 82.2)  # glass boxes, y ranges (main-block frame)
BRIDGE_X = (40.1, 43.6)


def split(a, b, n):
    return [a + (b - a) * k / n for k in range(n + 1)]


class Main(b.Spec):
    name = 'Povo 2'
    origin = (E0, N0, 368.5)
    X, Y = 49.7, 101.5
    levels = {-2: 0.0, -1: 4.75, 0: 9.5, 1: 13.8}
    roof = 18.8
    clear = 3.3
    court = (18.3, 23.4, 32.4, 78.5)
    court_floor = -1
    cores = [('SW', (0.3, 15.5, 9.6, 23.4), 'S'), ('SE', (33.0, 15.5, 41.0, 23.4), 'S'),
             ('NW', (0.3, 78.5, 9.6, 86.5), 'N'), ('NE', (33.0, 78.5, 41.0, 86.5), 'N')]
    lifts = [((44.8, 15.5, 49.4, 23.4), 'W'), ((44.8, 78.5, 49.4, 86.5), 'W')]
    floors = dict(classroom='oak', study='oak', office='cream', lab='cream', wc='tile', hall='cream',
                  terrace='pavers', stair='grey_stair', lift='dark', service='concrete', garage='concrete')
    corridor_floor = 'cream'
    stair_floor = 'grey_stair'
    doors = {
        'S': [(-1, 41.5, 48.5), (1, *BRIDGE_X)],                     # exit to the lane (POVO2_5), bridge
        'W': [(-2, 3.0, 9.0)],                                      # parking ramp (POVO2_4)
        'E_h1': [(-2, 3.5, 6.5), (-1, 3.5, 6.5)],                   # Hole 1
        'E_s1': [(-2, 29.0, 31.0), (-1, 29.0, 31.0), (0, 25.4, 31.0)],   # strip corridors, Glass Box 1
        'E_h2': [(-1, 49.5, 52.5)],                                 # Hole 2
        'E_s2': [(-2, 69.0, 71.0), (-1, 69.0, 71.0), (0, 71.9, 77.3)],   # strip corridors, Glass Box 2
        'E_h3': [(-2, 95.0, 98.0), (-1, 95.0, 98.0)],               # Hole 3
        'CS': [(-1, 24.0, 26.6)], 'CN': [(-1, 24.0, 26.6)],
    }

    def frames(self):
        X, T = self.X, self.T
        east = [('E_h1', T, STRIP_Y[0]), ('E_s1', STRIP_Y[0], HOLE2[0]), ('E_h2', *HOLE2),
                ('E_s2', HOLE2[1], STRIP_Y[1]), ('E_h3', STRIP_Y[1], self.Y - T)]
        base = [f for f in super().frames() if f[0] != 'E']
        return base[:3] + [(n, 'x', X, a, c, -1) for n, a, c in east] + base[3:]

    def style(self, frame, level):
        name = frame[0]
        if name.startswith('C'):
            return None if level == -2 else ('ribbon' if level == 1 else 'curtain')
        if level >= 0:
            return 'stone'
        if name == 'W':
            return 'curtain'                                  # ground falls to -2 on the west
        if name in ('S', 'N'):
            return 'curtain' if level == -1 else 'solid'
        if name in ('E_h1', 'E_h3') or (name == 'E_h2' and level == -1):
            return 'curtain'
        return 'solid'                                        # shared with the strip

    def extras(self, g, m):
        # Columns in the -2 garage on a ~6 x 7.5 m grid.
        for x in (6.3, 12.3):
            for k in range(1, 8):
                y = k * 7.5
                g.box('walls-2', x - .25, y - .25, 0, x + .25, y + .25, self.clear, 'concrete')
        # Roof (aerials POVO2_2-4): plant rooms over both ends, air units, skylights by the court.
        b.roof_kit(g, self,
                   units=[(14.0, 8.0, 3.2, 1.8), (24.0, 8.0, 3.2, 1.8), (36.0, 92.0, 3.2, 1.8),
                          (42.0, 50.0, 1.8, 3.2), (6.0, 50.0, 1.8, 3.2), (6.0, 60.0, 1.8, 3.2)],
                   rooms=[((12.0, 88.0, 30.0, 98.0), 3.2), ((28.0, 3.0, 42.0, 11.0), 2.8)],
                   skylights=[(13.5, 27.0 + k * 9.0, 15.5, 30.0 + k * 9.0) for k in range(6)]
                   + [(35.5, 27.0 + k * 9.0, 37.5, 30.0 + k * 9.0) for k in range(6)])

    def lights(self, level):
        east_x = 45.2 if level == 0 else 42.25
        return [((1.5, 14.4), (48, 14.4)), ((1.5, 87.75), (48, 87.75)),
                ((10.7, 16), (10.7, 85)), ((east_x, 24), (east_x, 78))]

    def rooms(self, level):
        return main_rooms(level)


def service():
    return [Room('WC', 'wc', (11.8, 15.5, 16.0, 23.4), [('W', 22.4, 1.0)]),
            Room('WC', 'wc', (16.0, 15.5, 26.0, 23.4), [('S', 21.0, 1.0)]),
            Room('Locale', 'office', (26.0, 15.5, 33.0, 23.4), [('S', 29.5, 1.0)]),
            Room('WC', 'wc', (11.8, 78.5, 16.0, 86.5), [('W', 79.5, 1.0)]),
            Room('WC', 'wc', (16.0, 78.5, 26.0, 86.5), [('N', 21.0, 1.0)]),
            Room('Locale', 'office', (26.0, 78.5, 33.0, 86.5), [('N', 29.5, 1.0)])]


def main_rooms(level):
    ring = 23.4, 78.5
    if level == 0:
        out = row_x(['B101', 'B102', 'B103', 'B104', 'B105'], [0.3, 11.8, 22.5, 33.0, 41.0, 49.4],
                    0.3, 13.3, 'classroom', 'N')
        out += row_x(['B120', 'B121', 'B122', 'B123'], [0.3, 11.8, 25.5, 41.0, 49.4], 89.0, 101.2, 'classroom', 'S')
        out += row_y(['Ufficio'] * 8, split(*ring, 8), 0.3, 9.6, 'office', 'E')
        out += row_y(['Ufficio'] * 9, split(*ring, 9), 11.8, 18.3, 'office', 'W')
        out += row_y(['Portineria', 'B110', 'B111', 'B112', 'B113', 'Aula PC'],
                     [23.4, 28.4, 38.4, 48.4, 58.4, 68.4, 78.5], 32.4, 41.0, 'classroom', 'E', 1.6)
        out[-6].kind = 'office'
        # x 41.0-49.4: the long hall with tables along the east facade, open to both glass boxes.
    elif level == 1:
        out = row_x(['Ufficio'] * 10, split(0.3, 39.6, 10), 0.3, 8.5, 'office', 'N', 1.0)
        out.append(Room('Ufficio', 'office', (44.1, 0.3, 49.4, 8.5), [('N', 46.75, 1.0)]))
        out += row_x(['Ufficio'] * 12, split(0.3, 49.4, 12), 91.5, 101.2, 'office', 'S', 1.0)
        out += row_y(['Ufficio'] * 14, split(*ring, 14), 0.3, 9.6, 'office', 'E', 1.0)
        out += row_y(['Ufficio'] * 14, split(*ring, 14), 11.8, 18.3, 'office', 'W', 1.0)
        out += row_y(['Ufficio'] * 8, split(*ring, 8), 32.4, 41.0, 'office', 'E', 1.0)
        out += row_y(['Ufficio'] * 13, split(*ring, 13), 43.5, 49.4, 'office', 'W', 1.0)
    elif level == -1:
        out = row_x(['Aula', 'Aula', 'Laboratorio', 'Laboratorio'], [0.3, 11.8, 22.5, 33.0, 41.0],
                    0.3, 13.3, 'classroom', 'N')
        out += row_x(['Laboratorio'] * 4, [0.3, 11.8, 25.5, 41.0, 49.4], 89.0, 101.2, 'lab', 'S')
        out += row_y(['Ufficio'] * 8, split(*ring, 8), 0.3, 9.6, 'office', 'E', 1.0)
        out += row_y(['Ufficio'] * 9, split(*ring, 9), 11.8, 18.3, 'office', 'W', 1.0)
        out += row_y(['Ufficio'] * 8, split(*ring, 8), 32.4, 41.0, 'office', 'E', 1.0)
        out += row_y(['Ufficio'] * 3, [ring[0], 35.0, 45.65, 56.05], 43.5, 49.4, 'office', 'W', 1.0)
        out += row_y(['Ufficio'] * 3, [56.05, 66.0, 72.0, ring[1]], 43.5, 49.4, 'office', 'W', 1.0)
    else:   # -2: parking under the south-west, halls under the courtyard, labs round them
        out = [Room('Autorimessa', 'garage', (0.3, 0.3, 18.3, 60.0), [('E', 30.0, 3.0)], open='')]
        out += [Room('Sala', 'hall', (18.3, 23.4, 32.4, 78.5), [('E', 50.0, 2.0), ('W', 70.0, 2.0)])]
        out += row_x(['Laboratorio'] * 3, [18.3, 25.0, 33.0, 41.0], 0.3, 13.3, 'lab', 'N')
        out.append(Room('FabLab', 'lab', (41.0, 0.3, 49.4, 13.3), [('N', 45.0, 1.6)]))
        out += row_x(['Laboratorio'] * 4, [0.3, 11.8, 25.5, 41.0, 49.4], 89.0, 101.2, 'lab', 'S')
        out += row_y(['Laboratorio'] * 2, [60.0, 70.0, 78.5], 0.3, 9.6, 'lab', 'E', 1.0)
        out += row_y(['Laboratorio'] * 4, split(*ring, 4), 32.4, 41.0, 'lab', 'E', 1.2)
    return out + service()


class Strip(b.Spec):
    """The volume along Via Sommarive: -2 and -1 under the floor-0 plaza, Hole 2 cut into it."""
    name = 'Povo 2 strip'
    origin = (666276.3, 5103820.1, 368.5)         # inner face meets the main block's east wall
    X, Y = 28.3, 82.9
    levels = {-2: 0.0, -1: 4.75}
    roof = 9.5                                    # the plaza
    clear = 3.3
    court = (0.0, 36.4, 25.0, 46.8)               # Hole 2, open on the main-block side
    court_floor = -1
    floors = Main.floors
    corridor_floor = 'cream'
    stair_floor = 'grey_stair'
    spandrel = 'louvre'
    doors = {'S': [(-2, 10.0, 13.0), (-1, 10.0, 13.0)], 'N': [(-2, 10.0, 13.0), (-1, 10.0, 13.0)],
             'CS': [(-1, 18.0, 20.0)], 'CN': [(-1, 18.0, 20.0)]}

    def style(self, frame, level):
        name = frame[0]
        if name in ('S', 'N'):
            return 'curtain'                      # facing Holes 1 and 3 (POVO2_5: grey cladding)
        if name == 'E':
            return 'solid'                        # against the street embankment
        if name in ('CS', 'CN', 'CE'):
            return 'curtain' if level == -1 else None
        return None                               # W and CW: the main block's facade

    def lights(self, level):
        return [((1.4, 1), (1.4, 81)), ((26.2, 1), (26.2, 81))]

    def rooms(self, level):
        kinds = 'office' if level == -1 else 'lab'
        out = []
        for ys in ([0.3, 9.0, 18.0, 27.0, 36.4], [46.8, 55.0, 64.0, 73.0, 82.6]):
            for a, c in zip(ys, ys[1:]):
                out.append(Room('Locale', kinds, (2.5, a, 24.5, c), [('E', (a + c) / 2, 1.2), ('W', (a + c) / 2, 1.2)]))
        return out

    parapet_gaps = [(24.9, 36.7, 25.4, 38.3)]     # top of the Hole 2 stair

    def roof_hole(self):
        return rect(*self.court).buffer(self.T, join_style=2).intersection(rect(0, 0, self.X, self.Y))

    def extras(self, g, m):
        z = self.roof
        # Plaza railing round the edges of Holes 1 and 3 (the strip's short ends).
        for y in (0.0, self.Y):
            g.railing('plaza', (0.0, y), (self.X, y), z, height=1.1)
        for y0, y1 in (BOX1, BOX2):
            glass_box(g, self, y0 - STRIP_Y[0], y1 - STRIP_Y[0])
        hole2_stair(g, self)


def hole2_stair(g, s):
    """Steel stair from the Hole 2 floor (-1) up to the plaza (P108, P109), two flights of
    13 risers along the hole's south glass wall. The last riser steps onto the plaza at the
    hole's east edge (x 25.0): nothing of the stair lies on or in the plaza slab."""
    y0, y1 = 36.7, 38.3
    z0, z1 = s.levels[-1], s.roof
    rise = (z1 - z0) / 26
    run = 12 * .3
    x = s.court[2] - (2 * run + 1.6)                         # foot, so the top lands at the edge
    for flight in range(2):
        base = z0 + flight * 13 * rise
        for k in range(12):
            g.box('plaza', x + k * .3, y0, base + (k + 1) * rise - .06, x + (k + 1) * .3, y1, base + (k + 1) * rise,
                  'grating')
        g.beam('plaza', (x, y1 - .04, base - .1), (x + run, y1 - .04, base + 12 * rise - .1), .08, .3, 'alu')
        g.railing('plaza', (x + .3, y1), (x + run, y1), base + 2 * rise, base + 12 * rise)
        x += run
        if flight == 0:
            g.box('plaza', x, y0, base + 13 * rise - .08, x + 1.6, y1, base + 13 * rise, 'grating')   # landing
            g.railing('plaza', (x, y1), (x + 1.6, y1), base + 13 * rise)
            for cx in (x + .1, x + 1.5):
                g.box('plaza', cx - .06, y1 - .12, z0, cx + .06, y1, base + 13 * rise - .08, 'alu')
            x += 1.6


def glass_box(g, s, y0, y1):
    """Frosted green pavilion on the plaza, against the main block (P010, P065-P069). The
    street face has a centred porch, 2 m deep, with two double sliding doors symmetric
    about the middle (P011, 23-10 photos 14, 15, 23)."""
    x0, x1, z0, z1 = 0.0, 25.5, s.roof, s.roof + 7.0
    bucket = 'boxes'
    mid, half, depth, head = (y0 + y1) / 2, 4.2, 2.0, z0 + 2.8
    g.box(bucket, x0, y0, z1 - .4, x1, y1, z1, 'roof')                              # roof slab
    g.box(bucket, x0, y0, z0, x1, y1, z0 + .02, 'cream')                            # interior floor
    for side in ('S', 'N', 'E'):
        if side == 'E':
            a, c, fixed = y0, y1, x1
        else:
            a, c, fixed = x0, x1, y0 if side == 'S' else y1
        n = max(1, round((c - a) / 1.3))
        if side == 'E':                                       # an odd count puts a pane, not a mullion, mid-face
            n += 1 - n % 2
        for k in range(n + 1):
            p = a + (c - a) * k / n
            if side == 'E':
                lo = head if mid - half < p < mid + half else z0
                g.box(bucket, fixed - .1, p - .05, lo, fixed, p + .05, z1 - .4, 'alu')
            else:
                g.box(bucket, p - .05, fixed - .05, z0, p + .05, fixed + .05, z1 - .4, 'alu')
        for k in range(n):
            p0, p1 = a + (c - a) * k / n, a + (c - a) * (k + 1) / n
            if side == 'E':
                lo = head if p1 > mid - half and p0 < mid + half else z0
                g.box(bucket, fixed - .08, p0 + .05, lo, fixed - .02, p1 - .05, z1 - .4, 'frosted')
            else:
                g.box(bucket, p0 + .05, fixed - .03, z0, p1 - .05, fixed + .03, z1 - .4, 'frosted')
    # The porch: opening in the street face, side walls, ceiling, inner glass wall with doors.
    xi = x1 - depth
    g.box(bucket, xi, mid - half, head, x1, mid + half, head + .25, 'panel')
    for y in (mid - half, mid + half):
        g.box(bucket, xi, y - .1, z0, x1 - .1, y + .1, head, 'panel')
    doors = [(mid - 3.3, mid - .9), (mid + .9, mid + 3.3)]
    edges = [mid - half, *[v for d in doors for v in d], mid + half]
    for a, c in zip(edges[::2], edges[1::2]):
        g.box('glass', xi - .02, a + .05, z0, xi + .02, c - .05, head, 'glass')
    for a, c in doors:
        for y in (a, c):
            g.box(bucket, xi - .05, y - .05, z0, xi + .05, y + .05, head, 'alu')
        g.box(bucket, xi - .05, a, z0 + 2.3, xi + .05, c, head, 'alu')
    for k in range(3):
        g.light(x1 / 2, y0 + (k + .5) * (y1 - y0) / 3, z1 - .6, 900, 10)


def bridge(g):
    """Louvred bridge on Povo 2 floor 1 / Povo 1 floor +1 (382.3 m): P013, P031."""
    x0, x1 = BRIDGE_X
    y0, y1 = -30.8, 0.0
    z = Main.levels[1]
    top = z + 3.2
    g.box('bridge', x0, y0, z - .5, x1, y1, z, 'concrete')
    g.box('bridge', x0, y0, top, x1, y1, top + .45, 'panel')
    g.box('bridge', x0 + .15, y0, top - .02, x1 - .15, y1, top, 'ceiling')
    for x, inner in ((x0, x0 + .15), (x1, x1 - .15)):
        g.box('bridge', min(x, inner), y0, z, max(x, inner), y1, z + .1, 'alu')          # curb
        g.box('glass', inner - .015, y0, z, inner + .015, y1, top, 'glass')
        for k in range(int((top - z) / .3)):                                         # external louvres
            h = z + .15 + k * .3
            g.box('bridge', x - .06, y0, h, x + .06, y1, h + .12, 'louvre')
        for j in range(10):                                                           # diagonal braces
            ya, yb = y0 + j * 3.08, y0 + (j + 1) * 3.08
            za, zb = (z, top) if j % 2 == 0 else (top, z)
            g.beam('bridge', (inner, ya, za), (inner, yb, zb - .25), .12, .25, 'alu')
    for k in range(4):
        g.light((x0 + x1) / 2, y0 + (k + .5) * (y1 - y0) / 4, top - .3, 500, 7)


MAIN = Main()
STRIP = Strip()


def build(m, world, u):
    b.build(m, world, u, MAIN)
    b.build(m, world, u, STRIP)
    g = b.Builder(MAIN, world)
    bridge(g)
    b.flush(g, m, u, 'bridge')


def bridge_outline_en():
    return rect(E0 + BRIDGE_X[0], N0 - 30.8, E0 + BRIDGE_X[1], N0)
