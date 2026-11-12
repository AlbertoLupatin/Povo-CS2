"""Regrade the streets around Povo 2 to the PAT LiDAR terrain (11 November).

After tools/povo2_levels.py, Povo 2's entrance sits at 8.05 while the legacy
Via Sommarive, roundabout and north pavement were still flat at about 4.0.
The DTM puts them at 8.1-10.4. This pass lifts every *unmapped* exterior
object east of Povo 2 (and north of its north terrace) by
dz = smoothed DTM - current model surface, faded to zero at the zone edges.
The south road / library / Povo 1 side is deliberately left alone (see
Altitude_Corrections.md): changing it means re-levelling Povo 1 too.
"""
import math
from pathlib import Path

import numpy as np
from scipy import ndimage

try:
    from .povo2_levels import MAPPED, STREET, STREET_RAILS, NEW, is_ramp, _carve_exterior as _carve
    from .povo2_levels import P1_EXTERIOR, STREET_SPLIT, SPLIT_Z
    from .povo_room_fitout import subtract_box
except ImportError:
    from povo2_levels import MAPPED, STREET, STREET_RAILS, NEW, is_ramp, _carve_exterior as _carve
    from povo2_levels import P1_EXTERIOR, STREET_SPLIT, SPLIT_Z
    from povo_room_fitout import subtract_box

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (666250., 5103800., 370.)
X0, Y0, NX, NY = -60., -40., 201, 221          # 1 m grid, x -60..140, y -40..180
TILE = 4.
SOUTH_BAND = (-8., 4.1, -25., 56.)   # y0, y1, x0, x1: south road and its footways
# Graded zones (x0, y0, x1, y1); weight() fades inside them.
ZONES = ((49.5, -10., 110., 175.), (40., -10., 49.5, 9.1), (-30., 101.5, 49.5, 175.), (-25., -16., 40., 9.1))
# Surfaces that define "the ground" of the legacy model (fixtures excluded).
_GROUND = ('via', 'road', 'footway', 'verge', 'walk', 'grounds', 'gardens', 'roundabout', 'island',
           'pavement', 'paving', 'green_strip', 'crosswalk', 'approach', 'branch', 'left_terrace',
           'old_yard', 'edges_north_village')


def weight(x, y):
    """1 inside the regraded zones, fading over a few metres at their edges."""
    clip = lambda v: min(1., max(0., v))
    fade = clip((110-x)/10)*clip((175-y)/10)           # backdrop beyond stays as built
    # Fade south of N0, where the legacy via began its drop into the old 4.0
    # hollow, so the whole former slope is regraded in one piece.
    # Along the south road (below the garden edge, N9.1) the fade is gentle,
    # E40-51, so its east end rises to the junction at about 6 %.
    across = clip((x-49.5)/1.5) if y >= 9.1 else clip((x-40)/11)
    east = across*clip((y+10)/10)*fade                 # Povo 2 front and Via Sommarive north of the junction
    north = clip((y-101.5)/1.)*clip((x+30)/10)*fade   # north garden rim, pavement and beyond
    # South road (Via dei Valoni) between Povo 1/library and Povo 2's frontage,
    # fading out toward the west branch and the Povo 1 / library north edge.
    south = clip((x+25)/5)*clip((9.1-y)/.01)*clip((y+16)/3)   # west road (x < -25) left alone
    return max(east, north, south)


def _load(path):
    with open(path) as f:
        head = {}
        for _ in range(6):
            k, v = f.readline().split();head[k.lower()] = float(v)
        return head, np.loadtxt(f)


def _sunken(levels):
    """Povo 2's sunken gardens and terrace runs are not street ground."""
    p2 = next(l['connection'] for l in levels if 'connection' in l)['povo2']
    rects = [p2['gardens']['garden']]
    terrace = levels[0].get('exterior', {}).get('terrace_integration', {})
    if terrace:
        rects += [terrace['north_garden'], *(terrace['slabs'][k] for k in ('north_run', 'south_run'))]
    return rects


def _dtm_grid(root, sunken=()):
    head, dtm = _load(root/'data/raw/terrain/5h666051035_DTM.asc')
    _, dbm = _load(root/'data/raw/terrain/5h666051035_DBM.asc')
    xs = X0+np.arange(NX); ys = Y0+np.arange(NY)
    cols = np.rint((ORIGIN[0]+xs-head['xllcenter'])/head['cellsize']).astype(int)
    rows = (int(head['nrows'])-1-np.rint((ORIGIN[1]+ys-head['yllcenter'])/head['cellsize'])).astype(int)
    t = dtm[np.ix_(rows, cols)]-ORIGIN[2]; b = dbm[np.ix_(rows, cols)]-ORIGIN[2]
    t = ndimage.median_filter(t, 3)
    t = np.where(b-t < .3, t, np.nan)          # ground only: buildings/canopies are interpolated
    for a, b0, c, d in sunken:
        t[max(0, int(b0-1-Y0)):int(d+1-Y0)+1, max(0, int(a-1-X0)):int(c+1-X0)+1] = np.nan
    # The south road is graded along its length only (one height per station),
    # so its LiDAR crossfall between the banks does not tilt the carriageway.
    j0, j1 = int(SOUTH_BAND[0]-Y0), int(SOUTH_BAND[1]-Y0)
    for i in range(int(SOUTH_BAND[2]-X0), int(SOUTH_BAND[3]-X0)+1):
        column = t[j0:j1+1, i]
        if np.isfinite(column).any():t[j0:j1+1, i] = np.nanmedian(column)
    # The DTM under Povo 2's east canopy interpolates toward its courtyards;
    # anchor the facade line at the flush entrance floor instead.
    i0, i1 = int(50.5-X0), int(52-X0); j0, j1 = int(10-Y0), int(112-Y0)
    t[j0:j1+1, i0:i1+1] = NEW[0]
    return t


def _fill(a, iterations=400):
    """Fill NaNs by diffusion from known neighbours (covered ground, building cores)."""
    known = ~np.isnan(a); out = np.where(known, a, np.nanmean(a))
    for _ in range(iterations):
        smooth = ndimage.uniform_filter(out, 3)
        out = np.where(known, a, smooth)
    return out


def _model_surface(boxes, meshes):
    m = np.full((NY, NX), np.nan)

    def put(x0, y0, x1, y1, z):
        i0, i1 = int(math.ceil(x0-X0)), int(math.floor(x1-X0))
        j0, j1 = int(math.ceil(y0-Y0)), int(math.floor(y1-Y0))
        i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, NX-1), min(j1, NY-1)
        if i0 <= i1 and j0 <= j1:
            sub = m[j0:j1+1, i0:i1+1]
            m[j0:j1+1, i0:i1+1] = np.where(np.isnan(sub), z, np.fmax(sub, z))

    def ground(name):
        return _graded(name) and any(s in name for s in _GROUND)
    for n, lo, hi, _ in boxes:
        if ground(n) and hi[2] < 13 and hi[0]-lo[0] > .9 and hi[1]-lo[1] > .9:
            put(lo[0], lo[1], hi[0], hi[1], hi[2])
    for mesh in meshes:
        if not ground(mesh['name']):continue
        v = np.asarray(mesh['vertices'])
        for f in mesh['faces']:
            p = v[list(f)]
            nrm = np.cross(p[1]-p[0], p[2]-p[0])
            if nrm[2] <= .5*np.linalg.norm(nrm) or p[:, 2].max() > 13:continue
            lo, hi = p.min(0), p.max(0)
            for j in range(max(0, math.ceil(lo[1]-Y0)), min(NY-1, math.floor(hi[1]-Y0))+1):
                for i in range(max(0, math.ceil(lo[0]-X0)), min(NX-1, math.floor(hi[0]-X0))+1):
                    x, y = X0+i, Y0+j; a, b, c = p
                    den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                    if abs(den) < 1e-9:continue
                    l1 = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                    l2 = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
                    if min(l1, l2, 1-l1-l2) < -1e-6:continue
                    z = l1*a[2]+l2*b[2]+(1-l1-l2)*c[2]
                    m[j, i] = z if np.isnan(m[j, i]) else max(m[j, i], z)
    return m


class Field:
    """dz(x, y) = smoothed LiDAR ground - legacy model ground, times the zone weight."""

    def __init__(self, boxes, meshes, root=ROOT, sunken=()):
        target = _fill(_dtm_grid(root, sunken))
        model = _fill(_model_surface(boxes, meshes))
        dz = ndimage.uniform_filter(target-model, 5)
        w = np.array([[weight(X0+i, Y0+j) for i in range(NX)] for j in range(NY)])
        self.dz = dz*w; self.w = w
        # Open ground: on the LiDAR terrain, but never above the regraded paving.
        self.ground_z = np.minimum(ndimage.uniform_filter(target, 5)-.12, model+dz-.05)

    @staticmethod
    def _at(d, x, y):
        fx = min(max(x-X0, 0), NX-1.001); fy = min(max(y-Y0, 0), NY-1.001)
        i, j = int(fx), int(fy); u, v = fx-i, fy-j
        return float((1-u)*(1-v)*d[j, i]+u*(1-v)*d[j, i+1]+(1-u)*v*d[j+1, i]+u*v*d[j+1, i+1])

    def __call__(self, x, y):
        return self._at(self.dz, x, y)

    def ground(self, x, y, old):
        """Open ground sits just below the paving (12 cm curbs) on the LiDAR terrain."""
        w = self._at(self.w, x, y)
        return old+w*(self._at(self.ground_z, x, y)-old)


_WALK = ('walk', 'pavement', 'paving', 'terrace', 'yard', 'strip', 'footway', 'landing')
SHEET = 2.


def _sheet(name, a, b, bottom, top, material, field):
    """Closed terrain slab over [a, b]: top follows the field, bottom keeps its thickness."""
    nx = max(1, math.ceil((b[0]-a[0])/SHEET)); ny = max(1, math.ceil((b[1]-a[1])/SHEET))
    xs = [a[0]+(b[0]-a[0])*i/nx for i in range(nx+1)]; ys = [a[1]+(b[1]-a[1])*j/ny for j in range(ny+1)]
    verts = []; faces = []
    for layer, z0 in ((0, top), (1, bottom)):
        for y in ys:
            for x in xs:verts.append((x, y, field.ground(x, y, top)-(top-z0)))
    k = lambda layer, i, j: layer*(nx+1)*(ny+1)+j*(nx+1)+i
    for j in range(ny):
        for i in range(nx):
            p, q, r, t = k(0, i, j), k(0, i+1, j), k(0, i+1, j+1), k(0, i, j+1)
            faces += [(p, q, r), (p, r, t)]
            p, q, r, t = k(1, i, j), k(1, i+1, j), k(1, i+1, j+1), k(1, i, j+1)
            faces += [(p, r, q), (p, t, r)]
    edge = [(i, 0) for i in range(nx)]+[(nx, j) for j in range(ny)]+[(i, ny) for i in range(nx, 0, -1)]+[(0, j) for j in range(ny, 0, -1)]
    for (i, j), (u, v) in zip(edge, edge[1:]+edge[:1]):
        faces += [(k(0, i, j), k(1, i, j), k(1, u, v)), (k(0, i, j), k(1, u, v), k(0, u, v))]
    return dict(name=name, vertices=verts, faces=tuple(faces), material=material)


JUNCTION = (39., -22., 62., 20.)   # Via Sommarive / Via dei Valoni junction, inside the fade


def _in_junction(mesh):
    xs = [v[0] for v in mesh['vertices']]; ys = [v[1] for v in mesh['vertices']]
    # (footway_south strips keep their mitred top polygons intact)
    return any(k in mesh['name'] for k in ('_via_', 'registered_road_', 'corner_apron', 'footway_north')) \
        and min(xs) < JUNCTION[2] and max(xs) > JUNCTION[0] and min(ys) < JUNCTION[3] and max(ys) > JUNCTION[1]


def _densify(mesh, limit=1.):
    """Split triangles until no horizontal edge exceeds limit (shared midpoints)."""
    verts = list(mesh['vertices']); faces = [tuple(f) for f in mesh['faces']]; mids = {}

    def mid(a, b):
        key = (min(a, b), max(a, b))
        if key not in mids:
            p, q = verts[a], verts[b]
            mids[key] = len(verts); verts.append(tuple((p[k]+q[k])/2 for k in range(3)))
        return mids[key]
    out = []
    while faces:
        a, b, c = faces.pop()
        length, u, v, w = max((math.dist(verts[u][:2], verts[v][:2]), u, v, w)
                              for u, v, w in ((a, b, c), (b, c, a), (c, a, b)))
        if length <= limit:
            out.append((a, b, c));continue
        m = mid(u, v)
        faces += [(u, m, w), (m, v, w)]   # keeps the original winding
    mesh['vertices'] = verts; mesh['faces'] = tuple(out)


UP_TOP = (21.75, 4.2)          # where Povo 2's UP stair meets the south footway


def _retarget_up_stair(boxes, link, field):
    """The UP stair (from the -1 passage) now climbs to the regraded footway."""
    p2 = link['povo2']; top_old = 4.0; bottom = NEW[-1]
    top = top_old+field(*UP_TOP)
    k = (top-bottom)/(top_old-bottom)
    lin = lambda z: bottom+(z-bottom)*k
    for i, (n, lo, hi, m) in enumerate(boxes):
        if not n.startswith('p2_registered_up'):continue
        if '_step_' in n or n.endswith('_top'):
            boxes[i] = (n, (*lo[:2], lin(lo[2])), (*hi[:2], lin(hi[2])), m)
        else:
            dz = lin(lo[2])-lo[2];boxes[i] = (n, (*lo[:2], lo[2]+dz), (*hi[:2], hi[2]+dz), m)
    for rail in p2['stairs']['rails']:
        if rail['name'].startswith('registered_up'):
            for key in ('a', 'b'):rail[key] = [*rail[key][:2], lin(rail[key][2])]
    records = [p2.get('gardens', {}).get('routes', {}), p2.get('additions', {}).get('yard', {}).get('routes', {})]
    for routes in {id(r): r for r in records}.values():
        if 'up' in routes:routes['up'] = [[x, y, lin(z)] for x, y, z in routes['up']]
    p2['gardens']['up_top_z'] = round(top, 3)


def _graded(name):
    if name.startswith(STREET_SPLIT):return True
    return name.startswith('exterior_') and not is_ramp(name) and not name.startswith(P1_EXTERIOR) and \
        (not name.startswith(MAPPED) or name.startswith(STREET))


BUS = 'exterior_abandoned_bus'


def _shift(name, z, dz):
    """Library street pieces keep their yard-side (lower) heights."""
    return z if name.startswith(STREET_SPLIT) and z <= SPLIT_Z else z+dz


def apply(boxes, levels, root=ROOT):
    ext = levels[0].get('exterior', {})
    meshes = ext.get('meshes', [])
    field = Field(boxes, meshes, root, _sunken(levels))
    result = []; terrain = []
    bus = [b for b in boxes if b[0].startswith(BUS)]
    bus_dz = 0
    wheels = [m for m in ext.get('collision_meshes', []) if m['name'].startswith(BUS+'_wheel')]
    if bus and wheels:   # road lift under the wheels
        centres = [(sum(v[0] for v in m['vertices'])/len(m['vertices']), sum(v[1] for v in m['vertices'])/len(m['vertices']))
                   for m in wheels]
        bus_dz = max(field(x, y) for x, y in centres)   # rests on the highest wheel; none sink
    for box in boxes:
        n, lo, hi, m = box
        if not _graded(n) or hi[2] < 0:            # deep underlays stay put
            result.append(box);continue
        if n.startswith(BUS):                      # the bus moves as one body
            result.append((n, (*lo[:2], lo[2]+bus_dz), (*hi[:2], hi[2]+bus_dz), m));continue
        if n.startswith(STREET_SPLIT):
            dz = field((lo[0]+hi[0])/2, (lo[1]+hi[1])/2)
            a, b = _shift(n, lo[2], dz), _shift(n, hi[2], dz)
            result.append((n, (*lo[:2], a), (*hi[:2], max(b, a+1e-3)), m));continue
        pieces = [box]
        for zone in ZONES:
            rest = []
            for piece in pieces:
                pn, plo, phi, pm = piece
                a = (max(plo[0], zone[0]), max(plo[1], zone[1])); b = (min(phi[0], zone[2]), min(phi[1], zone[3]))
                if a[0] >= b[0] or a[1] >= b[1]:
                    rest.append(piece);continue
                hole = ((zone[0], zone[1], plo[2]-1), (zone[2], zone[3], phi[2]+1))
                rest += subtract_box(piece, hole)
                if (phi[0]-plo[0])*(phi[1]-plo[1]) > 2500:
                    # Large ground slabs become one smooth terrain sheet.
                    terrain.append(_sheet(f'{pn}_graded_{len(terrain)}', a, b, plo[2], phi[2], pm, field))
                    continue
                # The rest is tiled so each piece follows the terrain; walking
                # surfaces finely, so slopes become low steps.
                tile = 1. if any(k in pn for k in _WALK) else TILE
                nx = max(1, math.ceil((b[0]-a[0])/tile)); ny = max(1, math.ceil((b[1]-a[1])/tile))
                for i in range(nx):
                    for j in range(ny):
                        p = (a[0]+(b[0]-a[0])*i/nx, a[1]+(b[1]-a[1])*j/ny)
                        q = (a[0]+(b[0]-a[0])*(i+1)/nx, a[1]+(b[1]-a[1])*(j+1)/ny)
                        dz = field((p[0]+q[0])/2, (p[1]+q[1])/2)
                        name = pn if (nx*ny == 1 and p == plo[:2] and q == phi[:2]) else f'{pn}_grade_{i}_{j}'
                        result.append((name, (p[0], p[1], plo[2]+dz), (q[0], q[1], phi[2]+dz), pm))
            pieces = rest
        result.extend(pieces)
    done = set()
    for key in ('meshes', 'collision_meshes'):
        ext.setdefault(key, []).extend(terrain)
        done.update(id(t) for t in terrain)
    for key in ('meshes', 'collision_meshes'):
        for mesh in ext.get(key, []):
            if id(mesh) in done or not _graded(mesh['name']):continue
            done.add(id(mesh))
            # Big backdrop sheets reaching far outside the zones stay as built:
            # moving only their in-zone vertices would tilt whole triangles.
            ws = [weight(x, y) for x, y, _ in mesh['vertices']]
            xs = [v[0] for v in mesh['vertices']]; ys = [v[1] for v in mesh['vertices']]
            if (max(xs)-min(xs))*(max(ys)-min(ys)) > 2500 and min(ws) == 0:continue
            if _in_junction(mesh):_densify(mesh)   # sparse road strips cross the fade
            if mesh['name'].startswith(BUS):
                mesh['vertices'] = [(x, y, z+bus_dz) for x, y, z in mesh['vertices']];continue
            pinned = set(mesh.pop('pinned', ()))   # lower edges already on Povo 2's terrace
            mesh['vertices'] = [(x, y, z if i in pinned else _shift(mesh['name'], z, field(x, y)))
                                for i, (x, y, z) in enumerate(mesh['vertices'])]
    link = next(l['connection'] for l in levels if 'connection' in l)
    for rail in link['povo2']['stairs']['rails']+levels[0].get('library_stair', {}).get('rails', []):
        if rail['name'].startswith(('registered_', *STREET_RAILS)) or _graded(rail['name']):
            for k in ('a', 'b'):
                x, y, z = rail[k];rail[k] = [x, y, z+field(x, y)]
    # Lowered paving must not overhang Povo 2's sunken stairs and terraces.
    result = _carve(result, {})
    _retarget_up_stair(result, link, field)
    for tree in ext.get('edges', {}).get('stock_trees', []):   # CS2 prop trees stand on the regraded ground
        x, y, z = tree['point'];tree['point'] = [x, y, z+field(x, y)]
    ext['grade'] = dict(zones=[list(z) for z in ZONES],
                        source='PAT DTM 0.5 m, ground cells only, 5 m smoothing',
                        dz_range=[round(float(field.dz.min()), 2), round(float(field.dz.max()), 2)],
                        bus_dz=round(bus_dz, 6))
    return result
