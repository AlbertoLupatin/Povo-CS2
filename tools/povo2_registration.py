"""Register the assembled Povo 2 interior to the real building.

The interior passes (planimetry, basements, West Offices, repairs) work in a
frame that sits about 8 m south and, on -1, stretched east-west compared with
the LiDAR roof outline and the 2024 orthophoto. The exterior shell, Garden -2,
Povo 1 and the bridge are already right. This pass moves only the interior and
its metadata, using config/povo2_registration.json.
"""
from bisect import bisect_right
import json
from pathlib import Path

CONFIG = 'config/povo2_registration.json'
# Metadata keys whose numbers are pixels, trace units, inputs or counts.
SKIP_KEYS = {'trace_bounds', 'source_bounds', 'source_pixel_bounds_approx', 'rectified_pixel_bounds',
             'public_door_pixels', 'source_pixels', 'trace', 'dimensional_inference', 'references',
             'flight_counts', 'table_rows_y', 'placement', 'source_anchor', 'target_anchor', 'config',
             'yard', 'gardens', 'lift', 'input_hashes',
             'entrance_world'}  # the outdoor door bank, already in world coordinates


class Registration:
    def __init__(self, root):
        cfg = json.loads((Path(root) / CONFIG).read_text())
        self.knots = sorted(cfg['x_knots']['pairs'])
        self.yknots = sorted(cfg['y_knots']['pairs'])
        lobby = cfg['bridge_lobby']
        self.pinned, self.core_south, self.x_from = lobby['pinned_north'], lobby['core_south'], lobby['x_from_north']
        self.unmoved = tuple(cfg['unmoved_prefixes'])

    @staticmethod
    def _piecewise(k, v):
        i = min(max(bisect_right([p[0] for p in k], v) - 1, 0), len(k) - 2)
        (v0, e0), (v1, e1) = k[i], k[i + 1]
        return e0 + (v - v0) * (e1 - e0) / (v1 - v0)

    def fx(self, x):
        return self._piecewise(self.knots, x)

    def fy(self, y):
        return self._piecewise(self.yknots, y)

    def gy(self, y):
        """Bridge-lobby north: pinned at the facade, stretched to the core."""
        if y <= self.pinned:
            return y
        if y >= self.core_south:
            return self.fy(y)
        f = (y - self.pinned) / (self.core_south - self.pinned)
        return self.pinned + f * (self.fy(self.core_south) - self.pinned)

    # Points and boxes -----------------------------------------------------
    def point(self, p, lobby=False):
        q = list(p)
        if lobby:
            if q[1] >= self.x_from:
                q[0] = self.fx(q[0])
            q[1] = self.gy(q[1])
        else:
            q[0], q[1] = self.fx(q[0]), self.fy(q[1])
        return type(p)(q) if isinstance(p, tuple) else q

    def rect(self, r, lobby=False):
        a, b = self.point([r[0], r[1]], lobby), self.point([r[2], r[3]], lobby)
        if lobby and r[1] < self.x_from:
            a[0], b[0] = r[0], r[2]
        out = [a[0], a[1], b[0], b[1], *r[4:]]
        return type(r)(out) if isinstance(r, tuple) else out

    def box(self, box, lobby=False):
        n, lo, hi, m = box
        x0, y0, x1, y1 = self.rect([lo[0], lo[1], hi[0], hi[1]], lobby)
        return (n, (x0, y0, lo[2]), (x1, y1, hi[2]), m)

    # Metadata -------------------------------------------------------------
    def meta(self, value, lobby=False, key=None, seen=None):
        """Transform coordinates in place. Containers shared between the Povo 2
        spec and the bridge link are visited once."""
        seen = set() if seen is None else seen
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                return value
            seen.add(id(value))
        if isinstance(value, dict):
            for k, v in value.items():
                if k not in SKIP_KEYS:
                    value[k] = self.meta(v, lobby, k, seen)
            return value
        if isinstance(value, (list, tuple)) and value and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
            if len(value) in (2, 3):
                new = self.point(value, lobby)
            elif len(value) in (4, 5):
                new = self.rect(value, lobby)
            else:
                return value
            if isinstance(value, list):
                value[:] = new
                return value
            return new
        if isinstance(value, list):
            value[:] = [self.meta(v, lobby, key, seen) for v in value]
            return value
        if isinstance(value, tuple):
            return tuple(self.meta(v, lobby, key, seen) for v in value)
        return value


def extend(boxes, levels, root):
    reg = Registration(root)
    link = next(l['connection'] for l in levels if l.get('connection'))
    widths = door_widths(link['povo2'])
    out = []
    for box in boxes:
        name = box[0]
        if name.startswith('p2_') and not name.startswith(reg.unmoved):
            out.append(reg.box(box))
        elif name.startswith('academic_first_link_p2_'):
            out.append(reg.box(box, lobby=True))
        else:
            out.append(box)
    link = next(l['connection'] for l in levels if l.get('connection'))
    spec = link['povo2']
    # The link's own entries use the lobby rule; visit them first so that
    # objects it shares with the Povo 2 spec are moved only once.
    seen = {id(spec)}
    for k in list(link):
        if k not in ('povo2', 'povo1_corridor', 'bridge') and k not in SKIP_KEYS:
            link[k] = reg.meta(link[k], lobby=True, key=k, seen=seen)
    for k in list(spec):
        if k not in SKIP_KEYS and k != 'footprint':
            spec[k] = reg.meta(spec[k], key=k, seen=seen)
    spec['registration'] = dict(source=CONFIG, x_knots=reg.knots, y_knots=reg.yknots)
    out = keep_door_widths(out, spec, widths)
    return keep_stair_headroom(out, link, spec)


def keep_stair_headroom(boxes, link, spec):
    """The east-west scale narrows stair wells. Cut slab edges out of the
    standing hull above every tread of the stair walking paths."""
    from .povo_room_fitout import subtract_box
    routes = [[link['stair']['top'], *link['stair']['path'], link['stair']['bottom']]]
    routes += [r['points'] for r in spec['stairs'].get('path', []) if isinstance(r, dict)]
    holes = []
    for route in routes:
        for a, b in zip(route, route[1:]):
            n = max(1, int(sum((p - q) ** 2 for p, q in zip(a, b)) ** .5 / .2))
            for i in range(n + 1):
                x, y, z = [p + (q - p) * i / n for p, q in zip(a, b)]
                holes.append(((x - .45, y - .45, z + .37), (x + .45, y + .45, z + 1.85)))
    slab = ('floor', 'ceiling', 'slab')
    def carve(box):
        if not box[0].startswith(('p2_internal', 'academic_first_link_p2_')) or not any(s in box[0] for s in slab):
            return [box]
        parts = [box]
        for lo, hi in holes:
            if all(box[1][k] < hi[k] and box[2][k] > lo[k] for k in range(3)):
                parts = [p for part in parts for p in subtract_box(part, (lo, hi))]
        return parts
    return [p for b in boxes for p in carve(b)]


DOOR_CUT = ('wall', 'window_glass', 'reception_glass', 'window_frame', 'office_frost')


def door_widths(spec):
    """Leaf-pair widths before registration, keyed by door name."""
    pairs = {}
    for d in spec.get('repair_doors', []):
        pairs.setdefault(d['id'][3:-2], {})[d['id'][-1]] = d['pivot']
    widths = {}
    for name, hinge in pairs.items():
        if set(hinge) == {'0', '1'}:
            a = 0 if abs(hinge['0'][0] - hinge['1'][0]) > abs(hinge['0'][1] - hinge['1'][1]) else 1
            widths[name] = (a, abs(hinge['0'][a] - hinge['1'][a]))
    return widths


def keep_door_widths(boxes, spec, widths):
    """Registration scales plan distances, door openings included. Re-centre
    each interactive leaf pair at its new position with its original width,
    and re-cut the surrounding wall or glazing to match."""
    from .povo_room_fitout import subtract_box
    doors = {}
    for d in spec.get('repair_doors', []):
        doors.setdefault(d['id'][3:-2], {})[d['id'][-1]] = d
    index = {b[0]: i for i, b in enumerate(boxes)}
    cuts = []
    for name, (a, width) in widths.items():
        pair = doors.get(name)
        if not pair or set(pair) != {'0', '1'}:
            continue
        across = 1 - a
        plane = pair['0']['pivot'][across]
        centre = (pair['0']['pivot'][a] + pair['1']['pivot'][a]) / 2
        prefix = 'p2_basement_repair_' + name
        for i, d in pair.items():
            sign = -1 if d['pivot'][a] < centre else 1
            hinge = centre + sign * width / 2
            d['pivot'][a] = hinge
            lo, hi = d['bounds']
            lo[a] = min(centre, hinge) + .018; hi[a] = max(centre, hinge) - .018
            jamb = prefix + '_jamb_' + i
            if jamb in index:
                n, blo, bhi, m = boxes[index[jamb]]
                blo, bhi = list(blo), list(bhi); blo[a], bhi[a] = hinge - .025, hinge + .025
                boxes[index[jamb]] = (n, tuple(blo), tuple(bhi), m)
            leaf = prefix + '_interactive_leaf_' + i
            if leaf in index:
                n, blo, bhi, m = boxes[index[leaf]]
                park = 1 if (blo[across] + bhi[across]) / 2 > plane else -1
                blo, bhi = list(blo), list(bhi)
                blo[a], bhi[a] = hinge - .024, hinge + .024
                blo[across] = plane + min(park * width / 2, park * .04)
                bhi[across] = plane + max(park * width / 2, park * .04)
                boxes[index[leaf]] = (n, tuple(blo), tuple(bhi), m)
        head = prefix + '_head'
        if head in index:
            n, blo, bhi, m = boxes[index[head]]
            blo, bhi = list(blo), list(bhi); blo[a], bhi[a] = centre - width / 2 - .05, centre + width / 2 + .05
            boxes[index[head]] = (n, tuple(blo), tuple(bhi), m)
        lo = [plane - .2, plane - .2, .39]; hi = [plane + .2, plane + .2, 2.65]
        lo[a], hi[a] = centre - width / 2 - .03, centre + width / 2 + .03
        cuts.append((prefix, (tuple(lo), tuple(hi))))
    out = boxes
    for prefix, hole in cuts:
        out = [p for b in out for p in (subtract_box(b, hole)
               if b[0].startswith('p2_') and not b[0].startswith(prefix) and b[3] in DOOR_CUT else [b])]
    return out
