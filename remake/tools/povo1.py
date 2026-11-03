"""Povo 1 (Via Sommarive 5): the room table and the parts only Povo 1 has.

Sources
- Outline, light well and column grid: specs/povo1.json (OSM r3663359 + LiDAR).
- Rooms: the three fire plans rectified onto the outline (data/plans/povo1_floor*.png),
  OSM indoor rooms on level -1, and the legacy survey notes for the courtyard stair.
- Heights: floors -1/0/+1 at 373.4/377.85/382.3 m - 4.45 m apart, so the roof slab lands
  on the LiDAR roof (386.8 m) and +1 meets the bridge deck (LiDAR bridge roof 385.7 m).
- Looks: beige stone fins and bands on floors 0/+1 over a glass -1 (user, P013, P057 and
  the aerials POVO1_1-4); glass and white panels round the courtyard (P005, 27-5..8,
  27-24); terrazzo corridors (P036-P039), oak classrooms (P047-P050), red stairwells with
  bar railings (P040-P044), terraces of grey slabs (28-1), galvanised courtyard stair (27-5).
"""

from shapely.geometry import box as rect
from shapely.ops import unary_union

import building as b
from building import Room, row_x, row_y

QUARTERS = [24.9, 32.375, 39.85, 47.325, 54.8]
TERRACES = ((11.6, 24.9, 16.3, 54.8), (30.6, 24.9, 35.3, 54.8))   # open air on +1
BRIDGE_X = (39.7, 43.2)                                            # OSM bridge, E 666267.0-666270.5
# Floors 0/+1: narrow stone fins ("high frequency") over the stair cores and corners, wide
# glazed bays ("low frequency") all the way between the two stair cores of each side, so
# every facade is symmetric (user, aerials POVO1_1-4, photo 2026-11-02 17.55.42). On -1 the
# east side is glass set back behind columns over that same stretch; elsewhere -1 is flush glass.
WIDE = {'E': [(24.9, 54.8)], 'W': [(24.9, 54.8)], 'N': [(8.6, 38.6)], 'S': [(8.6, 38.6)]}
PORTICO = {'E': [(24.9, 54.8)]}


def split(a, b, spans, inside, outside):
    """[(a, b, kind)]: the spans clipped to a..b get `inside`, the rest `outside`."""
    out, p = [], a
    for s0, s1 in spans:
        s0, s1 = max(a, s0), min(b, s1)
        if s1 <= s0:
            continue
        if s0 > p:
            out.append((p, s0, outside))
        out.append((s0, s1, inside))
        p = s1
    if p < b:
        out.append((p, b, outside))
    return out


class Povo1(b.Spec):
    name = 'Povo 1'
    origin = (666227.3, 5103698.65, 373.4)
    X, Y = 47.5, 81.4
    levels = {-1: 0.0, 0: 4.45, 1: 8.9}
    roof = 13.35
    court = (16.3, 24.9, 30.6, 54.8)
    court_floor = -1
    # (name, box, front wall, inner side): square-spiral stairwells (user's photo and the
    # "Mappa scale" sections) whose floor corner opens on both the front and the inner side.
    cores = [('SW', (0.3, 15.6, 8.6, 24.9), 'S', 'E'), ('SE', (38.6, 15.6, 47.2, 24.9), 'S', 'W'),
             ('NW', (0.3, 54.8, 8.6, 64.6), 'N', 'E'), ('NE', (38.6, 54.8, 47.2, 64.6), 'N', 'W')]
    stair = 'spiral'
    lifts = [((30.6, 15.6, 35.0, 24.9), 'E'), ((30.6, 54.8, 35.0, 64.6), 'E')]
    # Outside doors on -1 from the user's annotated map (Povo 1 mappa piano0_LAYOUT.png).
    doors = {
        'E': [(-1, 26.5, 28.3), (-1, 30.0, 31.8),                       # double sliding doors, Ingresso
              (-1, 15.8, 17.4), (-1, 62.8, 64.4)],                      # east stairwells
        'W': [(-1, 37.8, 39.4), (-1, 41.3, 42.9),                       # A109, A110
              (-1, 15.8, 17.4), (-1, 62.8, 64.4)],                      # west stairwells
        'S': [(-1, 1.1, 2.7), (-1, 8.5, 10.1), (-1, 12.6, 14.2), (-1, 20.4, 22.0), (-1, 24.3, 25.9),
              (-1, 32.2, 33.8), (-1, 36.3, 37.9), (-1, 44.8, 46.4)],    # A106-A103
        'N': [(-1, 1.1, 2.7), (-1, 13.3, 14.9), (-1, 20.4, 22.0), (-1, 28.9, 30.5), (-1, 37.1, 38.7),
              (-1, 44.8, 46.4), (1, *BRIDGE_X)],                        # A101, A102, offices; bridge
        'CS': [(-1, 22.65, 24.25), (0, 22.65, 24.25), (1, 22.65, 24.25)],   # courtyard stair landings
        'CN': [(-1, 22.65, 24.25)],
    }

    def rooms(self, level):
        return rooms(level)

    def lights(self, level):
        lines = [((1.5, 14.1), (46, 14.1)), ((1.5, 65.95), (46, 65.95)),
                 ((10.1, 17), (10.1, 63)), ((36.95, 17), (36.95, 63))]
        if level == -1:
            lines += [((41.2, 27), (41.2, 53)), ((44.5, 27), (44.5, 53))]
        if level == 1:
            lines += [((21, 17), (21, 24)), ((5, 11.6), (42, 11.6))]
        return lines

    def frames(self):
        y0, y1 = self.court[1], self.court[3]
        return super().frames() + [('TW', 'x', TERRACES[0][0], y0, y1, -1), ('TE', 'x', TERRACES[1][2], y0, y1, 1)]

    def style(self, frame, level):
        name = frame[0]
        if name in 'SNWE':
            return 'curtain' if level == -1 else 'stone'
        if name in ('CS', 'CN'):
            return 'ribbon' if level == 1 else 'curtain'
        if name in ('CW', 'CE'):
            return None if level == 1 else 'curtain'      # the terraces replace them on +1
        return 'curtain' if level == 1 else None          # terrace back walls

    def segments(self, frame, level):
        name, a, b = frame[0], frame[3], frame[4]
        if name not in WIDE:
            return super().segments(frame, level)
        if level == -1:
            return split(a, b, PORTICO.get(name, []), 'portico', 'curtain')
        return split(a, b, WIDE[name], 'stone_wide', 'stone')

    def extra_skip(self, level):
        if level != 1:
            return {}
        span = [(self.court[1], self.court[3])]
        return {('x', TERRACES[0][0]): span, ('x', TERRACES[1][2]): span}

    def roof_hole(self):
        x0, y0, x1, y1 = self.court
        return unary_union([rect(x0 - self.T, y0 - self.T, x1 + self.T, y1 + self.T),
                            rect(TERRACES[0][0] - self.T, y0, x0, y1), rect(x1, y0, TERRACES[1][2] + self.T, y1)])

    def extras(self, g, m):
        z1 = self.levels[1]
        for x in (self.court[0], self.court[2]):            # terrace edges: white upstand, railing
            inward = -1 if x == self.court[0] else 1
            g.box('facade1', x, self.court[1], z1, x + inward * self.T, self.court[3], z1 + .3, 'panel')
            g.railing('rails1', (x + inward * self.T / 2, self.court[1]), (x + inward * self.T / 2, self.court[3]),
                      z1 + .3, height=.8)
        # The portico ends against the SE and NE stair cores, whose walls close it.
        # Roof (aerials POVO1_1-4): plant rooms, air units, skylights along the courtyard wings.
        b.roof_kit(g, self,
                   units=[(20.0, 6.0, 3.2, 1.8), (26.0, 6.0, 3.2, 1.8), (32.0, 6.0, 3.2, 1.8),
                          (14.0, 74.0, 3.2, 1.8), (20.0, 74.0, 3.2, 1.8), (44.5, 48.0, 1.8, 3.2),
                          (9.5, 40.0, 1.8, 3.2)],
                   rooms=[((2.0, 1.5, 13.5, 10.0), 3.0), ((28.0, 68.5, 43.0, 78.5), 2.6)],
                   skylights=[(5.0, 27.0 + k * 6.5, 7.0, 29.0 + k * 6.5) for k in range(4)]
                   + [(40.5, 27.0 + k * 6.5, 42.5, 29.0 + k * 6.5) for k in range(3)])
        court_stair(g, self)
        for cx, cy in ((19.0, 40.0), (27.9, 40.0), (19.0, 49.0), (27.9, 49.0)):              # planters
            g.box('court', cx - .8, cy - .8, 0, cx + .8, cy + .8, .5, 'concrete')
            e = m.entity('prop_static', dict(model='models/foliage/trees/urban/urban_tree_small_1.vmdl', solid=6,
                                             rendercolor='255 255 255 255'),
                         g.W(cx, cy, .45), f'0 {int(cx * 41 + cy * 7) % 360} 0')
            e.set('scales', '0.55 0.55 0.55', 'vector3')


# Bands (y): south rooms | corridor 12.6-15.6 | service 15.6-24.9 | courtyard band | service
# 54.8-64.6 | corridor 64.6-67.3 | north rooms. Strips (x) in the courtyard band: outer rooms
# 0.3-8.6 | corridor | inner 11.6-16.3 | court | inner 30.6-35.3 | corridor | outer 38.6-47.2.

def service(level):
    """WCs and the room between them, south and north of the courtyard."""
    centre_s = {-1: Room('A107', 'classroom', (16.3, 15.6, 26.0, 24.9), [('S', 24.4, 1.6)]),
                0: Room('Area caffè', 'hall', (16.3, 15.6, 26.0, 24.9), [('S', 21.0, 3.2)]),
                1: None}[level]           # on +1 the corridor runs on to the courtyard stair door
    centre_n = {-1: Room('A108', 'classroom', (16.3, 54.8, 26.0, 64.6), [('N', 24.4, 1.6)]),
                0: Room('Aula Studio PC', 'classroom', (16.3, 54.8, 26.0, 64.6), [('N', 24.4, 1.6)]),
                1: Room('Sala riunioni', 'office', (16.3, 54.8, 26.0, 64.6), [('N', 24.4, 1.2)])}[level]
    rooms = [Room('WC', 'wc', (11.6, 15.6, 16.3, 24.9), [('W', 23.6, 1.0)]),
             Room('WC', 'wc', (26.0, 15.6, 30.6, 24.9), [('S', 28.3, 1.0)]),
             Room('WC', 'wc', (11.6, 54.8, 16.3, 64.6), [('W', 55.9, 1.0)]),
             Room('WC', 'wc', (26.0, 54.8, 30.6, 64.6), [('N', 28.3, 1.0)]),
             centre_n]
    return rooms + ([centre_s] if centre_s else [])


def rooms(level):
    if level == -1:
        out = row_x(['A106', 'A105', 'A104', 'A103'], [0.3, 12.0, 24.0, 35.8, 47.2], 0.3, 12.6, 'classroom', 'N')
        out += [Room('A101', 'classroom', (0.3, 67.3, 21.0, 81.1), [('S', 19.0, 1.6), ('S', 2.5, 1.6)]),
                Room('A102', 'classroom', (21.0, 67.3, 32.5, 81.1), [('S', 30.5, 1.6)]),
                Room('Uffici', 'office', (32.5, 67.3, 39.6, 81.1), [('S', 36.0, 1.0)]),
                Room('Uffici', 'office', (39.6, 67.3, 47.2, 74.2), [('W', 70.5, 1.0)]),
                Room('Uffici', 'office', (39.6, 74.2, 47.2, 81.1), [('W', 77.6, 1.0)])]
        out += row_y(['A109', 'A110'], [24.9, 39.85, 54.8], 0.3, 8.6, 'classroom', 'E', 1.6)
        out.append(Room('Sala Studio (Acquario)', 'study', (11.6, 24.9, 16.3, 54.8), [('W', 39.85, 1.6)], glass='W'))
        out += row_y(['Disbrigo', 'Portineria', 'Segreteria Studenti', 'Ufficio 2', 'Ufficio 1'],
                     [24.9, 28.0, 33.4, 41.8, 46.4, 54.8], 30.6, 35.3, 'office', 'E', 1.0)
        # East of the courtyard is the open entrance hall (x 35.3-47.2).
    elif level == 0:
        out = row_x(['A208', 'A207', 'A206', 'A205', 'A204'], [0.3, 8.8, 18.4, 28.7, 38.3, 47.2],
                    0.3, 12.6, 'classroom', 'N')
        out += row_x(['Laboratorio', 'A201 Aula PC', 'A202 Aula PC', 'A203'], [0.3, 18.4, 28.7, 38.3, 47.2],
                     67.3, 81.1, 'classroom', 'S')
        out[-4].kind = 'lab'
        out += row_y(['A221', 'A222', 'A223', 'A224'], QUARTERS, 0.3, 8.6, 'classroom', 'E', 1.6)
        out += row_y(['A220', 'A219', 'A218', 'A217'], QUARTERS, 11.6, 16.3, 'classroom', 'W')
        out += row_y(['A213', 'A214', 'A215', 'A216'], QUARTERS, 30.6, 35.3, 'classroom', 'E')
        out += row_y(['A212', 'A211', 'A210', 'A209'], QUARTERS, 38.6, 47.2, 'classroom', 'W', 1.6)
    else:
        xs = [0.3 + i * (46.9 / 12) for i in range(13)]
        out = row_x(['Ufficio'] * 12, xs, 0.3, 10.6, 'office', 'N', 1.0)
        out += row_x(['Open space'] * 4, [0.3, 11.9, 23.7, 35.5, 47.2], 67.3, 81.1, 'office', 'S', 1.2)
        out[-1].doors.append(('S', 41.45, 1.6))                     # corridor end towards the bridge
        out += row_y(['Ufficio'] * 4, QUARTERS, 0.3, 8.6, 'office', 'E', 1.0)
        out += row_y(['Ufficio'] * 4, QUARTERS, 38.6, 47.2, 'office', 'W', 1.0)
        out += [Room('Terrazza', 'terrace', t, glass='W' if t[0] < 20 else 'E') for t in TERRACES]
    return out + service(level)


def court_stair(g, s):
    """Galvanised emergency stair tower at the courtyard's south end (27-10 photos 5-8, P006):
    four corner columns with X bracing, per storey an up flight on the west half and a return
    flight on the east half round a mid landing, door landings against the facade on 0 and +1.
    Railings follow every open edge and leave the flight ends free."""
    xa, xb, xc, xd = 21.0, 23.3, 23.6, 25.9                  # west flight xa-xb, gap, east flight xc-xd
    yl0, yf0 = s.court[1], s.court[1] + 2.0                   # door landing yl0-yf0
    n = 12
    run = (n - 1) * .3
    yf1, yl1 = yf0 + run, yf0 + run + 1.8                     # mid landing yf1-yl1
    steel = 'louvre'
    for level in (-1, 0):
        z = s.levels[level]
        h = s.top(level) - z
        rise = h / (2 * n)
        zm = z + n * rise
        for k in range(n - 1):                                # up, northward, west half
            y = yf0 + k * .3
            g.box('cstair', xa, y, z + (k + 1) * rise - .06, xb, y + .3, z + (k + 1) * rise, 'grating')
        g.box('cstair', xa, yf1, zm - .08, xd, yl1, zm, 'grating')                     # mid landing
        for k in range(n - 1):                                # on up, southward, east half
            y = yf1 - (k + 1) * .3
            g.box('cstair', xc, y, zm + (k + 1) * rise - .06, xd, y + .3, zm + (k + 1) * rise, 'grating')
        for sx in (xa + .04, xb - .04):                       # stringers
            g.beam('cstair', (sx, yf0, z - .1), (sx, yf1, zm - .1), .08, .3, steel)
        for sx in (xc + .04, xd - .04):
            g.beam('cstair', (sx, yf1, zm - .1), (sx, yf0, z + h - .1), .08, .3, steel)
        g.railing('rails', (xa, yf0 + .3), (xa, yf1), z + 2 * rise, zm)                 # west flight
        g.railing('rails', (xb, yf0 + .3), (xb, yf1), z + 2 * rise, zm)
        g.railing('rails', (xc, yf1), (xc, yf0 + .3), zm + rise, z + h - rise)           # east flight
        g.railing('rails', (xd, yf1), (xd, yf0 + .3), zm + rise, z + h - rise)
        g.railing('rails', (xa, yl1), (xd, yl1), zm)                                     # mid landing
        g.railing('rails', (xa, yf1), (xa, yl1), zm)
        g.railing('rails', (xd, yf1), (xd, yl1), zm)
    for level in (0, 1):                                      # door landings
        z = s.levels[level]
        g.box('cstair', xa, yl0 + .05, z - .08, xd, yf0, z, 'grating')
        g.railing('rails', (xa, yl0 + .05), (xa, yf0), z)
        g.railing('rails', (xd, yl0 + .05), (xd, yf0), z)
        if level == 1:                                        # nothing goes up from +1: close the west half
            g.railing('rails', (xa, yf0), (xb, yf0), z)
    top = s.levels[1] + 1.1
    ox0, ox1 = xa - .2, xd + .2                               # columns stand just outside the flights
    for cx, cy in [(ox0, yf0), (ox1, yf0), (ox0, yl1), (ox1, yl1)]:
        g.box('cstair', cx - .12, cy - .12, 0, cx + .12, cy + .12, top, steel)
    for x in (ox0, ox1):                                      # X bracing on the long sides, per storey
        for level in (-1, 0):
            z0, z1 = s.levels[level] + .2, s.top(level) - .3
            g.beam('cstair', (x, yf0 + .15, z0), (x, yl1 - .15, z1), .08, .08, steel)
            g.beam('cstair', (x, yl1 - .15, z0), (x, yf0 + .15, z1), .08, .08, steel)


SPEC = Povo1()
