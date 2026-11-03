"""Shared engine for the detailed campus buildings.

A building is a Spec: an origin on the site, a footprint X x Y in metres, named levels,
a room table per level, stair cores, lift shafts, an optional courtyard and a facade
style per facade and level. From it the engine derives:
- walls: room edges merged per line, with door gaps, lintels and anthracite frames;
  glazed partitions where a room asks for them;
- slabs: one prism per room and level, so each room gets its own floor finish, with
  ceiling tiles underneath and holes for the courtyard, stairwells and lift shafts;
- facades on a 1.5 m module: glass curtain wall, stone bays or a white ribbon band;
- stair cores of two or three flights per storey round a well, with bar railings;
- ceiling lights in every room and along the corridors.
Plan frame: x east, y north from the footprint's south-west corner, z up from the
lowest level, metres. place() maps it onto the site via the site builder's world().
"""

from dataclasses import dataclass, field
import math

import shapely
from shapely.geometry import box as rect, Polygon
from shapely.ops import unary_union

import vmap_mesh as vm

M = dict(
    stone='materials/povo/beige_stone.vmat',
    plaster='materials/ar_baggage/baggage_plaster_wall_smooth_01.vmat',
    panel='materials/metal/hr_metal/hr_metal_panel_002.vmat',
    terrazzo='materials/povo/terrazzo.vmat',
    cream='materials/povo/cream_tile.vmat',
    oak='materials/de_train/hr_train_s2/wood/hrts2_wood_floor_boards_01.vmat',
    red='materials/povo/red_floor.vmat',
    ceiling='materials/ceiling/hr_c/hr_ceiling_tile_001_color.vmat',
    glass='materials/ar_baggage/baggage_glass_clear_01.vmat',
    frosted='materials/povo/frosted_glass.vmat',
    alu='materials/povo/aluminium.vmat',
    dark='materials/povo/anthracite.vmat',
    grating='materials/metal/hr_metal/hr_metal_grating_001.vmat',
    pavers='materials/cs_italy/ground/sidewalk_concrete_slabs_1.vmat',
    roof='materials/concrete/hr_c/hr_concrete_roof_001.vmat',
    concrete='materials/concrete/hr_c/hr_concrete_floor_001.vmat',
    tile='materials/de_cache/floor/ch2_floor_vinyl_01.vmat',
    grey_stair='materials/concrete/hr_c/hr_concrete_floor_001.vmat',
    louvre='materials/de_train/hr_train_s2/metal/hrts2_metal_panelling_01_paint.vmat',
)


@dataclass
class Room:
    name: str
    kind: str
    box: tuple                       # x0, y0, x1, y1
    doors: list = field(default_factory=list)   # (side, centre along the side, width)
    glass: str = ''                  # sides built as glazed partitions
    open: str = ''                   # sides with no wall at all
    thick: float = .15
    full: bool = False               # wall runs through the slab void (cores, shafts)


def row_x(names, xs, y0, y1, kind, side, width=1.6):
    """Rooms side by side along x, each with one door near its east end."""
    return [Room(n, kind, (a, y0, b, y1), [(side, b - 1.6, width)]) for n, a, b in zip(names, xs, xs[1:])]


def row_y(names, ys, x0, x1, kind, side, width=1.2):
    """Rooms stacked along y, each with one door near its middle."""
    return [Room(n, kind, (x0, a, x1, b), [(side, (a + b) / 2, width)]) for n, a, b in zip(names, ys, ys[1:])]


class Spec:
    """Override the data and, where a building differs, the hooks."""
    name = 'building'
    origin = (0.0, 0.0, 0.0)         # E, N, Z of the plan origin
    X = Y = 10.0
    T = 0.3                          # facade depth
    levels = {0: 0.0}
    roof = 4.0                       # top of the roof slab
    clear = 3.1                      # floor to ceiling
    parapet = .8
    court = None                     # (x0, y0, x1, y1) open to the sky
    court_floor = None               # level whose slab is the courtyard floor
    cores = []                       # (name, rect, front side 'S'/'N')
    lifts = []                       # (rect, door side 'E'/'W')
    floors = dict(classroom='oak', study='oak', office='terrazzo', lab='terrazzo', wc='tile', hall='terrazzo',
                  terrace='pavers', stair='red', lift='dark', service='concrete')
    corridor_floor = 'terrazzo'
    stair_floor = 'red'
    rail = 'alu'
    spandrel = 'stone'               # band above an outer curtain wall
    doors = {}                     # facade name -> [(level, s0, s1)] full openings
    parapet_gaps = []               # (x0, y0, x1, y1) cut from the courtyard parapet
    module = 1.5
    module_wide = 6.5                # bay of the wide stone facade
    tread, rise_max, flight_w = .3, .19, 1.8
    stair = 'u'                      # 'u': 2-3 flights round a well; 'spiral': 4 per storey (Povo 1)
    spiral_risers = 6

    def rooms(self, level):
        return []

    def lights(self, level):
        """Corridor light lines: [((x, y), (x, y))]."""
        return []

    def style(self, frame, level):
        """'curtain', 'stone', 'stone_wide', 'portico', 'ribbon', 'solid', 'panel' or None."""
        return 'stone'

    def segments(self, frame, level):
        """[(a, b, style)] along the frame; one style for the whole run by default."""
        return [(frame[3], frame[4], self.style(frame, level))]

    def extra_skip(self, level):
        return {}

    def roof_hole(self):
        return rect(*self.court).buffer(self.T, join_style=2) if self.court else None

    def extras(self, g, m):
        pass

    # derived -----------------------------------------------------------------
    def ordered(self):
        return sorted(self.levels)

    def top(self, level):
        """Height of the next level up (or the roof) above this level's floor."""
        order = self.ordered()
        i = order.index(level)
        return self.levels[order[i + 1]] if i + 1 < len(order) else self.roof

    def frames(self):
        """(name, axis, c, a, b, inward) - axis 'y' = runs along x at y=c."""
        X, Y, T = self.X, self.Y, self.T
        out = [('S', 'y', 0.0, 0.0, X, 1), ('N', 'y', Y, 0.0, X, -1),
               ('W', 'x', 0.0, T, Y - T, 1), ('E', 'x', X, T, Y - T, -1)]
        if self.court:
            x0, y0, x1, y1 = self.court
            out += [('CS', 'y', y0, x0 - T, x1 + T, -1), ('CN', 'y', y1, x0 - T, x1 + T, 1),
                    ('CW', 'x', x0, y0, y1, -1), ('CE', 'x', x1, y0, y1, 1)]
        return out

    def fixed_rooms(self, level=None):
        out = []
        for core in self.cores:
            _name, b, front = core[:3]
            if self.stair == 'spiral':
                out.append(Room('Scala', 'stair', b, spiral_doors(self, core, level), thick=.25, full=True))
            else:
                out.append(Room('Scala', 'stair', b, [(front, (b[0] + b[2]) / 2, 1.8)], thick=.25, full=True))
        for b, _side in self.lifts:
            x0, y0, x1, y1 = b
            mid = (y0 + y1) / 2
            out.append(Room('Ascensore', 'lift', (x0, y0, x1, mid), thick=.25, full=True))
            out.append(Room('Ascensore', 'lift', (x0, mid, x1, y1), thick=.25, full=True))
        return out


# ---------------------------------------------------------------- geometry

class Builder:
    def __init__(self, spec, world):
        self.s = spec
        self.world = world
        self.buckets = {}
        self.lights = []

    def W(self, x, y, z):
        o = self.s.origin
        return self.world(o[0] + x, o[1] + y, o[2] + z)

    def add(self, bucket, solid):
        self.buckets.setdefault(bucket, []).append(solid)

    def box(self, bucket, x0, y0, z0, x1, y1, z1, mat):
        lo = (min(x0, x1), min(y0, y1), min(z0, z1))
        hi = (max(x0, x1), max(y0, y1), max(z0, z1))
        if min(h - l for l, h in zip(lo, hi)) > 1e-3:
            self.add(bucket, vm.box(self.W(*lo), self.W(*hi), M[mat]))

    def beam(self, bucket, a, b, w, h, mat):
        """Straight member from a to b (centre of its underside), w wide, h tall."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        nx, ny = (-dy / length * w / 2, dx / length * w / 2) if length > 1e-6 else (w / 2, 0)
        bottom = [(a[0] - nx, a[1] - ny, a[2]), (b[0] - nx, b[1] - ny, b[2]),
                  (b[0] + nx, b[1] + ny, b[2]), (a[0] + nx, a[1] + ny, a[2])]
        top = [(p[0], p[1], p[2] + h) for p in bottom]
        self.add(bucket, vm.hexa([self.W(*p) for p in bottom + top], M[mat]))

    def slab(self, bucket, poly, z0, z1, top, bottom, side='plaster'):
        if poly.geom_type == 'Polygon':
            if poly.area <= .01:
                return
            # Boolean ops leave near-duplicate vertices; snapping can split a polygon in parts.
            snapped = shapely.set_precision(poly, 1e-4).simplify(1e-4)
            if snapped.geom_type == 'Polygon':
                self.add(bucket, vm.prism(snapped, z0, z1, M[side], M[top], M[bottom], self.W))
            else:
                for p in getattr(snapped, 'geoms', []):
                    if p.geom_type == 'Polygon' and p.area > .01:
                        self.add(bucket, vm.prism(p, z0, z1, M[side], M[top], M[bottom], self.W))
        elif hasattr(poly, 'geoms'):       # multi-part or mixed results of boolean ops
            for p in poly.geoms:
                self.slab(bucket, p, z0, z1, top, bottom, side)

    def light(self, x, y, z, lumens=600, range_m=7):
        self.lights.append(((x, y, z), lumens, range_m))

    def railing(self, bucket, a, b, z0, z1=None, height=1.0, mat='alu'):
        """Bar railing from a to b (plan points), rising z0 -> z1."""
        z1 = z0 if z1 is None else z1
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        for k in range(int(length // 1.2) + 2):
            t = min(k * 1.2 / length, 1) if length else 0
            px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            pz = z0 + (z1 - z0) * t
            self.box(bucket, px - .025, py - .025, pz, px + .025, py + .025, pz + height, mat)
        for hgt, size in ((height - .05, .05), (.8, .02), (.6, .02), (.4, .02), (.2, .02)):
            self.beam(bucket, (a[0], a[1], z0 + hgt), (b[0], b[1], z1 + hgt), size, size, mat)


# ---------------------------------------------------------------- walls

def wall_lines(s, level, room_list):
    """Merge room edges into wall segments per line: {(axis, c): [(a, b, kind, thick, full, door)]}.
    Facade and courtyard edges are left to the facades."""
    lines, doors = {}, {}
    for r in room_list:
        x0, y0, x1, y1 = r.box
        edges = {'S': ('y', y0, x0, x1), 'N': ('y', y1, x0, x1), 'W': ('x', x0, y0, y1), 'E': ('x', x1, y0, y1)}
        for side, (axis, c, a, b) in edges.items():
            if side in r.open:
                continue
            kind = 'glass' if side in r.glass else 'wall'
            lines.setdefault((axis, round(c, 2)), []).append((a, b, kind, r.thick, r.full))
        for side, at, width in r.doors:
            axis, c, _a, _b = edges[side]
            doors.setdefault((axis, round(c, 2)), []).append((at - width / 2, at + width / 2))
    T, X, Y = s.T, s.X, s.Y
    skip = {('x', T): [(0, Y)], ('x', round(X - T, 2)): [(0, Y)],
            ('y', T): [(0, X)], ('y', round(Y - T, 2)): [(0, X)]}
    if s.court and (s.court_floor is None or level >= s.court_floor):
        x0, y0, x1, y1 = s.court
        skip.update({('x', x0): [(y0, y1)], ('x', x1): [(y0, y1)], ('y', y0): [(x0, x1)], ('y', y1): [(x0, x1)]})
    for key, spans in s.extra_skip(level).items():
        skip.setdefault(key, []).extend(spans)
    out = {}
    for key, spans in lines.items():
        cuts = sorted({v for a, b, *_ in spans for v in (a, b)} |
                      {v for a, b in doors.get(key, []) for v in (a, b)} |
                      {v for a, b in skip.get(key, []) for v in (a, b)})
        segs = []
        for a, b in zip(cuts, cuts[1:]):
            mid = (a + b) / 2
            cover = [sp for sp in spans if sp[0] - 1e-6 <= mid <= sp[1] + 1e-6]
            if not cover or any(s0 <= mid <= s1 for s0, s1 in skip.get(key, [])):
                continue
            kind = 'wall' if any(c[2] == 'wall' for c in cover) else 'glass'
            seg = (kind, max(c[3] for c in cover), any(c[4] for c in cover),
                   any(d0 <= mid <= d1 for d0, d1 in doors.get(key, [])))
            if segs and segs[-1][1] >= a - 1e-6 and segs[-1][2:] == seg:
                segs[-1] = (segs[-1][0], b, *seg)
            else:
                segs.append((a, b, *seg))
        out[key] = segs
    return out


def build_walls(g, s, level, room_list, door_h=2.2):
    z = s.levels[level]
    last = level == s.ordered()[-1]
    for (axis, c), segs in wall_lines(s, level, room_list).items():
        for a, b, kind, thick, full, is_door in segs:
            top = s.top(level) if full and not last else z + s.clear
            h = thick / 2

            def piece(z0, z1, mat, bucket=f'walls{level}', ext=h):
                if axis == 'x':
                    g.box(bucket, c - h, a - ext, z0, c + h, b + ext, z1, mat)
                else:
                    g.box(bucket, a - ext, c - h, z0, b + ext, c + h, z1, mat)

            def across(s0, s1, z0, z1, mat, bucket, half):
                if axis == 'x':
                    g.box(bucket, c - half, s0, z0, c + half, s1, z1, mat)
                else:
                    g.box(bucket, s0, c - half, z0, s1, c + half, z1, mat)

            if is_door:
                piece(z + door_h, top, 'plaster', ext=0)
                for s0 in (a, b - .06):       # anthracite jambs and head, proud of both faces
                    across(s0, s0 + .06, z, z + door_h, 'dark', f'trim{level}', h + .02)
                across(a, b, z + door_h - .06, z + door_h, 'dark', f'trim{level}', h + .02)
            elif kind == 'wall':
                piece(z, top, 'plaster')
            else:   # glazed partition: aluminium posts every ~1.2 m, glass between
                n = max(1, round((b - a) / 1.2))
                for k in range(n + 1):
                    p = a + (b - a) * k / n
                    across(p - .03, p + .03, z, top, 'alu', f'trim{level}', .04)
                across(a, b, z, top, 'glass', f'glass{level}', .012)


# ---------------------------------------------------------------- facades

def fbox(g, bucket, frame, s0, s1, d0, d1, z0, z1, mat):
    """Box in facade coordinates: s along the facade, d depth inward from the outer face.
    Long runs are cut into <= 10 m pieces: one 100 m band makes an unbakeable lightmap chart."""
    _n, axis, c, _a, _b, inward = frame
    n = max(1, math.ceil((s1 - s0) / 10))
    for k in range(n):
        a, b2 = s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n
        if axis == 'y':
            g.box(bucket, a, c + inward * d0, z0, b2, c + inward * d1, z1, mat)
        else:
            g.box(bucket, c + inward * d0, a, z0, c + inward * d1, b2, z1, mat)


def modules(s, a, b):
    n = max(1, round((b - a) / s.module))
    return [a + (b - a) * k / n for k in range(n + 1)]


def openings(s, frame, level):
    return [(s0, s1) for lv, s0, s1 in s.doors.get(frame[0], []) if lv == level]


def curtain(g, s, frame, level, spandrel, top):
    """Glass curtain wall: aluminium mullions on the module, a transom at 2.6 m."""
    _name, _axis, _c, a, b, _i = frame
    z, T = s.levels[level], s.T
    edges = modules(s, a, b)
    doors = openings(s, frame, level)
    for p in edges:
        fbox(g, f'facade{level}', frame, max(a, p - .04), min(b, p + .04), 0, .22, z, z + s.clear, 'alu')
    for s0, s1 in zip(edges, edges[1:]):
        door = any(o0 < (s0 + s1) / 2 < o1 for o0, o1 in doors)
        fbox(g, f'facade{level}', frame, s0, s1, 0, .22, z + 2.6, z + 2.66, 'alu')
        if not door:
            fbox(g, f'facade{level}', frame, s0, s1, 0, .22, z, z + .06, 'alu')
            fbox(g, f'glass{level}', frame, s0 + .04, s1 - .04, .1, .13, z + .06, z + 2.6, 'glass')
        fbox(g, f'glass{level}', frame, s0 + .04, s1 - .04, .1, .13, z + 2.66, z + s.clear, 'glass')
    fbox(g, f'facade{level}', frame, a, b, 0, T, z + s.clear, top, spandrel)


def stone_bay(g, s, frame, level, top):
    """Stone piers standing proud on the module, recessed glazing between (aerials POVO1_1-4)."""
    _name, _axis, _c, a, b, _i = frame
    z, T = s.levels[level], s.T
    edges = modules(s, a, b)
    doors = openings(s, frame, level)
    for p in edges:
        fbox(g, f'facade{level}', frame, max(a, p - .25), min(b, p + .25), -.25, T, z, z + s.clear, 'stone')
    for s0, s1 in zip(edges, edges[1:]):
        w0, w1 = s0 + .25, s1 - .25
        door = any(o0 < (s0 + s1) / 2 < o1 for o0, o1 in doors)
        if door:
            fbox(g, f'facade{level}', frame, w0, w1, .18, .24, z + 2.4, z + 2.46, 'alu')
            fbox(g, f'glass{level}', frame, w0, w1, .2, .22, z + 2.46, z + s.clear - .06, 'glass')
        else:
            fbox(g, f'facade{level}', frame, w0, w1, .05, T, z, z + .4, 'stone')       # sill
            for lo, hi in ((z + .4, z + .46), (z + 1.0, z + 1.05)):
                fbox(g, f'facade{level}', frame, w0, w1, .18, .24, lo, hi, 'alu')
            fbox(g, f'glass{level}', frame, w0, w1, .2, .22, z + .46, z + s.clear - .06, 'glass')
        fbox(g, f'facade{level}', frame, w0, w1, .18, .24, z + s.clear - .06, z + s.clear, 'alu')
    # Stone band at the slab, standing as proud as the piers.
    fbox(g, f'facade{level}', frame, a, b, -.25, T, z + s.clear, top, 'stone')


def ribbon(g, s, frame, level, top):
    """White panel sill, a ribbon window, white spandrel."""
    _name, _axis, _c, a, b, _i = frame
    z, T = s.levels[level], s.T
    doors = openings(s, frame, level)
    edges = modules(s, a, b)
    for p in edges:
        fbox(g, f'facade{level}', frame, max(a, p - .04), min(b, p + .04), 0, .2, z + 1.0, z + s.clear, 'alu')
    for s0, s1 in zip(edges, edges[1:]):
        if any(o0 < (s0 + s1) / 2 < o1 for o0, o1 in doors):
            fbox(g, f'facade{level}', frame, s0, s1, 0, .2, z + 2.4, z + 2.46, 'alu')
            fbox(g, f'glass{level}', frame, s0 + .04, s1 - .04, .1, .13, z + 2.46, z + s.clear, 'glass')
        else:
            fbox(g, f'facade{level}', frame, s0, s1, 0, T, z, z + 1.0, 'panel')
            fbox(g, f'glass{level}', frame, s0 + .04, s1 - .04, .1, .13, z + 1.0, z + s.clear, 'glass')
    fbox(g, f'facade{level}', frame, a, b, 0, T, z + s.clear, top, 'panel')


def stone_wide(g, s, frame, level, top):
    """Wide glazed bays between broad stone piers: the "low frequency" central parts of the
    Povo 1 facades (aerials POVO1_1-3), against the narrow fins of stone_bay."""
    _name, _axis, _c, a, b, _i = frame
    z, T = s.levels[level], s.T
    n = max(1, round((b - a) / s.module_wide))
    edges = [a + (b - a) * k / n for k in range(n + 1)]
    doors = openings(s, frame, level)
    for p in edges:
        fbox(g, f'facade{level}', frame, max(a, p - .45), min(b, p + .45), -.3, T, z, z + s.clear, 'stone')
    for s0, s1 in zip(edges, edges[1:]):
        w0, w1 = s0 + .45, s1 - .45
        door = any(o0 < (s0 + s1) / 2 < o1 for o0, o1 in doors)
        if not door:
            fbox(g, f'facade{level}', frame, w0, w1, .05, T, z, z + .15, 'stone')
        for p in modules(s, w0, w1):                                    # mullions
            fbox(g, f'facade{level}', frame, max(w0, p - .04), min(w1, p + .04), .14, .24,
                 z + (2.3 if door else .15), z + s.clear, 'alu')
        for h in ((2.6,) if door else (1.0, 2.6)):                      # transoms
            fbox(g, f'facade{level}', frame, w0, w1, .14, .24, z + h, z + h + .06, 'alu')
        fbox(g, f'glass{level}', frame, w0, w1, .2, .22, z + (2.66 if door else .15), z + s.clear, 'glass')
    fbox(g, f'facade{level}', frame, a, b, -.3, T, z + s.clear, top, 'stone')


def portico(g, s, frame, level, top, depth=2.5):
    """Ground floor set back behind stone columns (Povo 1 east, by the entrance: photo
    2026-11-02 17.55.42, aerial POVO1_1): glass wall `depth` in, a soffit, columns on the line."""
    name, axis, c, a, b, inward = frame
    z = s.levels[level]
    curtain(g, s, (name, axis, c + inward * depth, a, b, inward), level, 'stone', top)
    n = max(1, round((b - a) / s.module_wide))
    for k in range(n + 1):
        p = a + (b - a) * k / n
        fbox(g, f'facade{level}', frame, max(a, p - .35), min(b, p + .35), -.3, .4, z, z + s.clear, 'stone')
    fbox(g, f'facade{level}', frame, a, b, 0, depth, z + s.clear - .02, z + s.clear, 'panel')   # soffit
    fbox(g, f'facade{level}', frame, a, b, 0, depth, z - .05, z + .01, 'concrete')              # floor


def solid(g, s, frame, level, top, mat='concrete'):
    """Plain wall (below ground or blind), with any door openings cut."""
    _name, _axis, _c, a, b, _i = frame
    z = s.levels[level]
    cuts = sorted([(max(a, o0), min(b, o1)) for o0, o1 in openings(s, frame, level)])
    p = a
    for o0, o1 in cuts:
        fbox(g, f'facade{level}', frame, p, o0, 0, s.T, z, top, mat)
        fbox(g, f'facade{level}', frame, o0, o1, 0, s.T, z + 2.4, top, mat)
        p = o1
    fbox(g, f'facade{level}', frame, p, b, 0, s.T, z, top, mat)


def build_facades(g, s):
    for whole in s.frames():
        for level in s.ordered():
            for a, b, kind in s.segments(whole, level):
                frame = (*whole[:3], a, b, whole[5])
                top = s.top(level)
                if kind == 'curtain':
                    curtain(g, s, frame, level, 'panel' if frame[0][0] in 'CT' else s.spandrel, top)
                elif kind == 'stone':
                    stone_bay(g, s, frame, level, top)
                elif kind == 'stone_wide':
                    stone_wide(g, s, frame, level, top)
                elif kind == 'portico':
                    portico(g, s, frame, level, top)
                elif kind == 'ribbon':
                    ribbon(g, s, frame, level, top)
                elif kind == 'solid':
                    solid(g, s, frame, level, top)
                elif kind == 'panel':
                    solid(g, s, frame, level, top, 'louvre')
    lowest = s.ordered()[0]
    for frame in s.frames()[:4]:
        # Plinth well below the lowest floor: the terrain is cut at the walls and can be lower.
        fbox(g, f'facade{lowest}', frame, frame[3], frame[4], 0, s.T, s.levels[lowest] - .6, s.levels[lowest], 'stone')
        fbox(g, f'facade{lowest}', frame, frame[3], frame[4], 0, s.T, s.levels[lowest] - 4.0,
             s.levels[lowest] - .6, 'concrete')
    inner = rect(s.T, s.T, s.X - s.T, s.Y - s.T)
    g.slab('roof', rect(0, 0, s.X, s.Y).difference(inner), s.roof, s.roof + s.parapet, 'stone', 'stone', 'stone')
    hole = s.roof_hole()
    if hole is not None:
        ring = hole.buffer(s.T, join_style=2).difference(hole)
        for gap in s.parapet_gaps:                    # e.g. where a stair arrives from below
            ring = ring.difference(rect(*gap))
        g.slab('roof', ring, s.roof, s.roof + s.parapet, 'panel', 'panel', 'panel')


# ---------------------------------------------------------------- slabs

def core_interior(s, b):
    x0, y0, x1, y1 = b
    return (x0 + (.15 if x0 > s.T + .01 else 0), y0 + .125,
            x1 - (.15 if x1 < s.X - s.T - .01 else 0), y1 - .125)


def stair_frame(s, b, front, inner=None):
    """Core-local (u, v) -> plan: v runs from the front (door) wall to the back. For spiral
    cores u = width is the inner side (towards the corridor), mirroring where needed."""
    x0, y0, x1, y1 = core_interior(s, b)
    width, depth = x1 - x0, y1 - y0
    flip = (inner == 'W') if inner else front == 'N'
    fx = (lambda u: x1 - u) if flip else (lambda u: x0 + u)
    fy = (lambda v: y0 + v) if front == 'S' else (lambda v: y1 - v)
    return width, depth, lambda u, v: (fx(u), fy(v))


def flights(s, level):
    """(number of flights, risers per flight) for the storey above this level."""
    h = s.top(level) - s.levels[level]
    n = 2 if h <= 4.4 else 3
    return n, math.ceil(h / n / s.rise_max)


def front_depth(s, b, front):
    width, depth, _P = stair_frame(s, b, front)
    runs = []
    for level in s.ordered()[:-1]:
        n, risers = flights(s, level)
        runs.append((risers - 1) * s.tread)
    return depth - max(runs, default=0) - s.flight_w


def stair_back(s, b, front, inner=None):
    if s.stair == 'spiral':
        width, depth, P = stair_frame(s, b, front, inner)
        floor = unary_union([Polygon([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]).envelope
                             for u0, v0, u1, v1 in spiral(s, width, depth)['floor']])
        return Polygon([P(0, 0), P(width, 0), P(width, depth), P(0, depth)]).envelope.difference(floor)
    width, depth, P = stair_frame(s, b, front)
    fd = front_depth(s, b, front)
    return Polygon([P(0, fd), P(width, fd), P(width, depth), P(0, depth)]).envelope


def build_slabs(g, s):
    inner = rect(s.T, s.T, s.X - s.T, s.Y - s.T)
    lifts = [rect(*b).buffer(-.125, join_style=2) for b, _side in s.lifts]
    backs = [stair_back(s, *core[1:]) for core in s.cores]
    court = rect(*s.court).buffer(s.T, join_style=2) if s.court else None
    order = s.ordered()
    for i, level in enumerate(order):
        z = s.levels[level]
        if i == 0:
            poly, thick, under = inner, .4, 'concrete'
        else:
            holes = lifts + backs
            if court is not None and (s.court_floor is None or level > s.court_floor):
                holes.append(court)
            poly = inner.difference(unary_union(holes))
            thick, under = z - s.levels[order[i - 1]] - s.clear, 'ceiling'
        claimed = []
        for r in s.rooms(level) + s.fixed_rooms(level):
            part = poly.intersection(rect(*r.box))
            if claimed:
                part = part.difference(unary_union(claimed))
            claimed.append(rect(*r.box))
            g.slab(f'slab{level}', part, z - thick, z, s.floors.get(r.kind, s.corridor_floor), under)
        rest = poly.difference(unary_union(claimed)) if claimed else poly
        if s.court and level == s.court_floor:
            g.slab(f'slab{level}', rest.intersection(rect(*s.court)), z - thick, z, 'pavers', under)
            rest = rest.difference(rect(*s.court))
        g.slab(f'slab{level}', rest, z - thick, z, s.corridor_floor, under)
    hole = s.roof_hole()
    roof = inner.difference(hole) if hole is not None else inner
    g.slab('roof', roof, s.levels[order[-1]] + s.clear, s.roof, 'roof', 'ceiling')


# ---------------------------------------------------------------- stair cores

def build_core_stairs(g, s):
    if s.stair == 'spiral':
        return build_spiral_stairs(g, s)
    for _name, b, front in s.cores:
        width, depth, P = stair_frame(s, b, front)
        w = s.flight_w
        fd = front_depth(s, b, front)

        def step(u0, v0, u1, v1, top):
            (x0, y0), (x1, y1) = P(u0, v0), P(u1, v1)
            g.box('stairs', x0, y0, top - .35, x1, y1, top, s.stair_floor)

        def rail(a, b2, z0, z1):
            g.railing('rails', P(*a), P(*b2), z0, z1, mat=s.rail)

        for level in s.ordered()[:-1]:
            z = s.levels[level]
            n, risers = flights(s, level)
            rise = (s.top(level) - z) / (n * risers)
            run = (risers - 1) * s.tread
            # Flight A up the left side from the front landing.
            for k in range(risers - 1):
                step(0, fd + k * s.tread, w, fd + (k + 1) * s.tread, z + (k + 1) * rise)
            rail((w, fd), (w, fd + run), z + rise, z + risers * rise)
            if n == 3:
                step(0, fd + run, w, depth, z + risers * rise)                 # left back landing
                for k in range(risers - 1):                                     # flight B across the back
                    step(w + k * s.tread, depth - w, w + (k + 1) * s.tread, depth, z + (risers + k + 1) * rise)
                step(w + run, depth - w, width, depth, z + 2 * risers * rise)  # right back landing,
                step(width - w, fd + run, width, depth - w, z + 2 * risers * rise)   # down to flight C
                rail((w, depth - w), (w + run, depth - w), z + risers * rise, z + 2 * risers * rise)
                last = 2 * risers
            else:
                step(0, fd + run, width, depth, z + risers * rise)             # full-width back landing
                last = risers
            # Flight C (or B) down the right side towards the front, arriving on the next floor.
            for k in range(risers - 1):
                v1 = fd + run - k * s.tread
                step(width - w, v1 - s.tread, width, v1, z + (last + k + 1) * rise)
            rail((width - w, fd + run), (width - w, fd), z + last * rise, s.top(level) - rise)
        for level in s.ordered():
            z = s.levels[level]
            if level == s.ordered()[-1]:
                rail((0, fd), (width - w, fd), z, z)
            elif level != s.ordered()[0]:
                rail((w, fd), (width - w, fd), z, z)
            cx, cy = P(width / 2, fd / 2)
            g.light(cx, cy, z + s.clear - .2, 800, 9)


def spiral(s, width, depth):
    """Square spiral round a well (photo of the Povo 1 stairwell): per storey four flights,
    one centred on each side, corner landings, the leftover side length added to the corners.
    Core-local; the front-right corner is the floor landing. Pieces are (u0, v0, u1, v1)."""
    w = s.flight_w
    run = (s.spiral_risers - 1) * s.tread
    sides = {'R': depth - 2 * w, 'B': width - 2 * w, 'L': depth - 2 * w, 'F': width - 2 * w}
    pre = {k: max(0.0, (L - run) / 2) for k, L in sides.items()}
    floor = [(width - w, 0, width, w),                                    # the floor corner
             (width - w, w, width, w + pre['R']),                         # right side, before flight 1
             (width - w - pre['F'], 0, width - w, w)]                     # front side, after flight 4
    return dict(w=w, pre=pre, run=run, floor=[r for r in floor if r[2] - r[0] > 1e-3 and r[3] - r[1] > 1e-3])


def spiral_doors(s, core, level):
    """Two doors on the floor corner (front wall and inner side wall), one on the top floor."""
    _name, b, front, inner = core
    width, depth, P = stair_frame(s, b, front, inner)
    w = s.flight_w
    fx, _fy = P(width - w / 2, 0)
    _sx, sy = P(width, w / 2)
    doors = [(front, fx, 1.6)]
    if level is None or level != s.ordered()[-1]:
        doors.append((inner, sy, 1.6))
    return doors


def build_spiral_stairs(g, s):
    for core in s.cores:
        _name, b, front, inner = core
        width, depth, P = stair_frame(s, b, front, inner)
        sp = spiral(s, width, depth)
        w, pre, run = sp['w'], sp['pre'], sp['run']

        def step(u0, v0, u1, v1, top, th=.35):
            (x0, y0), (x1, y1) = P(u0, v0), P(u1, v1)
            g.box('stairs', x0, y0, top - th, x1, y1, top, s.stair_floor)

        def rail(a, b2, z0, z1):
            g.railing('rails', P(*a), P(*b2), z0, z1, mat=s.rail)

        r = s.spiral_risers
        for level in s.ordered()[:-1]:
            z = s.levels[level]
            rise = (s.top(level) - z) / (4 * r)
            q = [z + k * r * rise for k in range(5)]          # corner heights: FR, BR, BL, FL, next FR
            # 1: right side, front to back
            v0 = w + pre['R']
            for k in range(r - 1):
                step(width - w, v0 + k * s.tread, width, v0 + (k + 1) * s.tread, q[0] + (k + 1) * rise)
            step(width - w, v0 + run, width, depth, q[1])                         # up to and incl. BR
            rail((width - w, w), (width - w, depth - w), q[0], q[1])
            # 2: back side, right to left
            u0 = width - w - pre['B']
            step(u0, depth - w, width - w, depth, q[1])
            for k in range(r - 1):
                step(u0 - (k + 1) * s.tread, depth - w, u0 - k * s.tread, depth, q[1] + (k + 1) * rise)
            step(0, depth - w, u0 - run, depth, q[2])                             # up to and incl. BL
            rail((width - w, depth - w), (w, depth - w), q[1], q[2])
            # 3: left side, back to front
            v1 = depth - w - pre['L']
            step(0, v1, w, depth - w, q[2])
            for k in range(r - 1):
                step(0, v1 - (k + 1) * s.tread, w, v1 - k * s.tread, q[2] + (k + 1) * rise)
            step(0, 0, w, v1 - run, q[3])                                         # up to and incl. FL
            rail((w, depth - w), (w, w), q[2], q[3])
            # 4: front side, left to right, arriving on the next floor's corner
            u1 = w + pre['F']
            step(w, 0, u1, w, q[3])
            for k in range(r - 1):
                step(u1 + k * s.tread, 0, u1 + (k + 1) * s.tread, w, q[3] + (k + 1) * rise)
            rail((w, w), (width - w, w), q[3], q[4] - rise)
        top = s.ordered()[-1]
        rail((width - w - pre['F'], w), (width, w), s.levels[top], s.levels[top])
        for level in s.ordered():
            cx, cy = P(width - w / 2, w / 2)
            g.light(cx, cy, s.levels[level] + s.clear - .2, 1000, 10)


def build_lift_doors(g, s):
    for level, z in s.levels.items():
        for b, side in s.lifts:
            x0, y0, x1, y1 = b
            face = x1 if side == 'E' else x0
            out = 1 if side == 'E' else -1
            for yc in ((y0 + y1) / 2 - (y1 - y0) / 4, (y0 + y1) / 2 + (y1 - y0) / 4):
                g.box(f'trim{level}', face + out * .125, yc - .55, z, face + out * .145, yc + .55, z + 2.1, 'alu')
                g.box(f'trim{level}', face + out * .125, yc - .65, z + 2.1, face + out * .16, yc + .65, z + 2.2, 'dark')


def room_lights(g, s, level):
    """Rooms under 90 m2 get no light of their own (windows and corridors light them), big
    rooms one per ~10 m, corridors a dimmer one per 10 m (a 1000 lm light every 20 m burnt
    the narrow corridor walls white in the bake)."""
    z = s.levels[level] + s.clear - .2
    for r in s.rooms(level):
        x0, y0, x1, y1 = r.box
        if r.kind in ('terrace', 'void') or (x1 - x0) * (y1 - y0) < 90:
            continue
        nx, ny = max(1, round((x1 - x0) / 10)), max(1, round((y1 - y0) / 10))
        for i in range(nx):
            for j in range(ny):
                g.light(x0 + (i + .5) * (x1 - x0) / nx, y0 + (j + .5) * (y1 - y0) / ny, z,
                        1100, 11)
    for (ax, ay), (bx, by) in s.lights(level):
        n = max(1, round(math.hypot(bx - ax, by - ay) / 10))
        for k in range(n + 1):
            g.light(ax + (bx - ax) * k / n, ay + (by - ay) * k / n, z, 500, 10)


# ---------------------------------------------------------------- roof equipment

def plant_room(g, box, z, h):
    """Rooftop plant room: white panels, a grey grille band, a capping slab, two units on top."""
    x0, y0, x1, y1 = box
    g.box('roofkit', x0, y0, z, x1, y1, z + h, 'panel')
    g.box('roofkit', x0 - .03, y0 - .03, z + h - 1.1, x1 + .03, y1 + .03, z + h - .4, 'louvre')
    g.box('roofkit', x0 - .15, y0 - .15, z + h, x1 + .15, y1 + .15, z + h + .15, 'roof')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for dx in (-1, 1):
        ac_unit(g, cx + dx * min(2.2, (x1 - x0) / 4), cy, z + h + .15, 1.8, 1.4, .9)


def ac_unit(g, x, y, z, w=3.0, d=1.8, h=1.6):
    """Air-handling unit: a metal box with fans on top."""
    g.box('roofkit', x - w / 2, y - d / 2, z, x + w / 2, y + d / 2, z + h, 'panel')
    g.box('roofkit', x - w / 2 + .05, y - d / 2 - .02, z + .2, x + w / 2 - .05, y + d / 2 + .02, z + h - .3, 'louvre')
    n = max(1, round(w / 1.1))
    for k in range(n):
        fx = x - w / 2 + (k + .5) * w / n
        g.box('roofkit', fx - .4, y - .4, z + h, fx + .4, y + .4, z + h + .06, 'dark')


def roof_kit(g, s, units=(), rooms=(), skylights=()):
    """Overruns over every lift and stair core, then the listed plant rooms ((box), h),
    air units (x, y, w, d) and skylights (x0, y0, x1, y1) on the roof slab."""
    z = s.roof
    for (x0, y0, x1, y1), _side in s.lifts:
        g.box('roofkit', x0, y0, z, x1, y1, z + 1.8, 'panel')
        g.box('roofkit', x0 - .1, y0 - .1, z + 1.8, x1 + .1, y1 + .1, z + 1.95, 'roof')
    for core in s.cores:
        x0, y0, x1, y1 = core[1]
        w = min(4.0, x1 - x0)
        g.box('roofkit', x0, y0, z, x0 + w, y0 + 3.0, z + 2.5, 'panel')           # roof access
        g.box('roofkit', x0 - .1, y0 - .1, z + 2.5, x0 + w + .1, y0 + 3.1, z + 2.65, 'roof')
    for box, h in rooms:
        plant_room(g, box, z, h)
    for x, y, w, d in units:
        g.box('roofkit', x - w / 2 - .1, y - d / 2 - .1, z, x + w / 2 + .1, y + d / 2 + .1, z + .25, 'concrete')
        ac_unit(g, x, y, z + .25, w, d)
    for x0, y0, x1, y1 in skylights:
        g.box('roofkit', x0, y0, z, x1, y1, z + .4, 'panel')
        g.box('glass', x0 + .1, y0 + .1, z + .4, x1 - .1, y1 - .1, z + .7, 'glass')


# ---------------------------------------------------------------- entry point

def outline_en(s):
    o = s.origin
    return rect(o[0], o[1], o[0] + s.X, o[1] + s.Y)


def build(m, world, u, s):
    """Add a building to a MapBuilder. world(e, n, z) -> Hammer units; u = units per metre."""
    g = Builder(s, world)
    for level in s.ordered():
        build_walls(g, s, level, s.rooms(level) + s.fixed_rooms(level))
        room_lights(g, s, level)
    build_facades(g, s)
    build_slabs(g, s)
    build_core_stairs(g, s)
    build_lift_doors(g, s)
    s.extras(g, m)
    flush(g, m, u, s.name)
    return g


# Thin detail gets a coarse lightmap: the GPU bake's time per block grows with texels.
DETAIL = ('rails', 'trim', 'stairs', 'cstair', 'plaza', 'bridge', 'glass')


def flush(g, m, u, name):
    count = 0
    for bucket, solids in sorted(g.buckets.items()):
        bias = -3 if bucket.startswith(DETAIL) else 0
        for k in range(0, len(solids), 400):      # keep each Hammer mesh a manageable size
            try:
                m.mesh(solids[k:k + 400], lightmap_bias=bias)
            except ValueError as err:
                raise ValueError(f'{name} {bucket}: {err}') from err
            count += 1
    for (x, y, z), lumens, range_m in g.lights:
        m.entity('light_omni2', dict(colortemperature=4300, brightness_lumens=lumens, range=round(range_m * u),
                                     castshadows=1, showlight=0), g.W(x, y, z))   # baked; 0 leaks through walls
    print(f'{name}: {count} meshes, {sum(len(v) for v in g.buckets.values())} solids, {len(g.lights)} lights')
