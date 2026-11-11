"""Re-level Povo 2 to the 11 November evidence and rebuild its reception stair.

Basis (Altitude_Corrections.md, section 5b): -2 from the flat garden DTM,
-1 and 0 from 30 measured 16 cm risers per basement storey, closing on the
street DTM at the flush entrance. Povo 1 and the bridge (+1) stay fixed.

The historical Povo 2 passes still build at 4.0 / 0.4 / -3.2. This final
pass maps their heights through one monotonic profile, so every module moves
together: storeys translate up to door-head height and the remainder of each
storey stretches (basements, 3.6 -> 4.8 m) or compresses (0 -> +1, 7.2 ->
3.15 m). Flights crossing those bands cannot be mapped, so the reception
stair is rebuilt here from the user's counts and the approved plan:
two lanes with a 0.2 m gap, 2 m end landings (1.1 m far landing for 0-+1),
doors 0 and +1 stacked on the east wall, -1 at the west end and -2 at the
east end of the south wall.
"""
import bisect

try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing

OLD = {-2: -3.2, -1: .4, 0: 4., 1: 11.2}
NEW = {-2: -1.55, -1: 3.25, 0: 8.05, 1: 11.2}
# (old z, new z) knots: translate to old+2.6 m, then stretch/compress.
_KNOTS = [(-0.6, 1.05), (0.4, 3.25), (3.0, 5.85), (4.0, 8.05), (6.6, 10.65), (11.2, 11.2)]
_XS = [k[0] for k in _KNOTS]

MAPPED = ('p2_', 'exterior_p2_', 'exterior_povo2_', 'facade_p2', 'exterior_garage_',
          'exterior_parking_continuous', 'academic_first_link_p2_')
# Street-level frontage pieces built by the Povo 2 passes: they follow the
# regraded street (tools/povo2_exterior_grade.py), not the storey profile.
STREET = ('exterior_povo2_front_walk', 'exterior_povo2_front_green_strip', 'exterior_povo2_front_tree',
          'exterior_povo2_front_lamp', 'exterior_povo2_left_terrace', 'exterior_povo2_old_yard',
          'exterior_paving_povo2_north', 'exterior_p2_terrace_north_street', 'exterior_p2_terrace_north_bend',
          'exterior_p2_terrace_exterior_p2_terrace_north_street', 'exterior_p2_terrace_exterior_p2_terrace_north_corner',
          'exterior_p2_terrace_exterior_p2_terrace_north_garden_rim')
STREET_RAILS = tuple(p.replace('exterior_p2_terrace_exterior_', 'exterior_') for p in STREET)
RAMP_WORDS = ('ramp', 'driveway')
# Ramp profile: road junction (N1, Z3.0) to the garage portal (N30, old Z-3.2).
RAMP_TOP, RAMP_Y0, RAMP_Y1 = 3.0, 1., 30.

# Stair well in the registered frame (inner faces).
WELL_X0, WELL_X1, WELL_Y0, WELL_Y1 = 11.11, 20.39, 26.9, 34.7
WEST, EAST_EDGE = 13.69, 18.39          # new west inner face; east landing edge
SPLIT, GAP = 30.8, .2
LANE = {'south': (WELL_Y0, SPLIT-GAP/2), 'north': (SPLIT+GAP/2, WELL_Y1)}
TREAD = .3
DOOR_Y = 30.8                            # doors 0 and +1, stacked
DOOR_M1_X = (WEST+WEST+2)/2              # west landing centre
DOOR_M2_X = 19.2
SOUTH_WALL_Y = 26.8
STAIR_PREFIXES = ('p2_internal_', 'p2_basement_new_core_floor_', 'p2_parking_new_core_floor_',
                  'p2_repair_landing_', 'p2_repair_turn_', 'p2_basement_core_door_south_',
                  'p2_basement_core_south_panic_', 'p2_basement_core_south_threshold',
                  'p2_parking_south_landing')


def remap_z(z):
    """Old Povo 2 height -> adopted height (monotonic, identity above +1)."""
    if z >= _XS[-1]:return z
    if z <= _XS[0]:return round(z+(_KNOTS[0][1]-_KNOTS[0][0]), 9)
    i = bisect.bisect_right(_XS, z)
    (a, b), (c, d) = _KNOTS[i-1], _KNOTS[i]
    return round(b+(z-a)*(d-b)/(c-a), 9)


# Outdoor stairs whose ends meet two re-levelled surfaces (or a fixed street)
# keep their step count and plan; their rise is spread uniformly instead.
STAIR_GROUPS = [
    # ponytail: the south footway is still the legacy road (about 4.0, DTM ~5.3);
    # retarget the top when the altitude plan regrades that road.
    (('p2_registered_up', 'registered_up'), (OLD[-1], 4.0), (NEW[-1], 4.0)),
]
# Garden DOWN stairs (south, and its north mirror) are rebuilt: 4.8 m over the
# old 20 risers would be 24 cm, so they get 27 (17.8 cm) on the same 0.3525 m
# treads and run 2.5 m further into the garden.
GARDEN_STAIRS = (('p2_aligned_garden', 9.09, 10.8), ('exterior_p2_terrace_north_garden', 112.0, 113.71))
GARDEN_X0, GARDEN_TREAD, GARDEN_RISERS, GARDEN_SPLIT, GARDEN_MID = 32.4, .3525, 27, 13, 1.1


def _group(name):
    return next((g for g in STAIR_GROUPS if name.startswith(g[0])), None)


def _linear(z, group):
    (a, b), (c, d) = group[1], group[2]
    return c+(z-a)*(d-c)/(b-a)


def unmap_z(z):
    """Inverse of remap_z (the profile is strictly increasing)."""
    if z >= _KNOTS[-1][1]:return z
    if z <= _KNOTS[0][1]:return z-(_KNOTS[0][1]-_KNOTS[0][0])
    ys = [k[1] for k in _KNOTS]; i = bisect.bisect_right(ys, z)
    (a, b), (c, d) = _KNOTS[i-1], _KNOTS[i]
    return a+(z-b)*(c-a)/(d-b)


def ramp_shift(y):
    t = min(1., max(0., (y-RAMP_Y0)/(RAMP_Y1-RAMP_Y0)))
    return t*(NEW[-2]-OLD[-2])


def _ramp_z(z, y):
    return z if z >= RAMP_TOP-.1 else z+ramp_shift(y)


def is_ramp(name):
    return name.startswith(('exterior_', 'p2_')) and any(w in name for w in RAMP_WORDS)


def _map_box(box):
    n, lo, hi, m = box
    group = _group(n)
    if group:
        if '_step_' in n or 'landing' in n or n.endswith('_top'):
            return (n, (*lo[:2], _linear(lo[2], group)), (*hi[:2], _linear(hi[2], group)), m)
        dz = _linear(lo[2], group)-lo[2]   # posts/clips keep their height
        return (n, (*lo[:2], lo[2]+dz), (*hi[:2], hi[2]+dz), m)
    if is_ramp(n):
        y = (lo[1]+hi[1])/2
        return (n, (*lo[:2], _ramp_z(lo[2], y)), (*hi[:2], max(_ramp_z(hi[2], y), _ramp_z(lo[2], y)+1e-3)), m)
    if not n.startswith(MAPPED) or n.startswith(STREET) or lo[2] >= 10.9:
        return box
    a, b = remap_z(lo[2]), remap_z(hi[2])
    return (n, (*lo[:2], a), (*hi[:2], max(b, a+1e-3)), m)


def _map_mesh(mesh):
    n = mesh['name']
    if is_ramp(n):
        mesh['vertices'] = [(x, y, _ramp_z(z, y)) for x, y, z in mesh['vertices']]
    elif n.startswith(STREET):
        return
    elif n.startswith(MAPPED):
        mesh['vertices'] = [(x, y, remap_z(z)) for x, y, z in mesh['vertices']]
    elif n.startswith('exterior_registered_'):
        # Frontage banks, grates and forecourt: their lower edges sit on the
        # Povo 2 terrace/garden; the street-side edges (>= 2.6) are road.
        mesh['vertices'] = [(x, y, remap_z(z) if z < 2.6 else z) for x, y, z in mesh['vertices']]


_SKIP_KEYS = {'entrance', 'source_entrance', 'flight_counts', 'outward_direction',
              'dimensional_inference', 'references', 'stairs', 'continuous'}
_Z_KEYS = {'z', 'floor_z', 'ceiling_z', 'yard_z', 'street_z', 'top', 'floor_elevation_local'}


def _map_meta(obj, key='', seen=None):
    """Map z of every 3-D point and z-valued field; XY records are untouched.

    Records are shared between spec sections (e.g. gardens/yard routes), so
    each container is mapped once and its replacement reused.
    """
    if seen is None:seen = {}
    if key in _SKIP_KEYS:return obj
    if id(obj) in seen:return seen[id(obj)][1]
    if isinstance(obj, dict):
        seen[id(obj)] = (obj, obj)
        for k, v in list(obj.items()):
            if k in _Z_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                obj[k] = remap_z(v)
            else:
                obj[k] = _map_meta(v, k, seen)
        return obj
    if isinstance(obj, (list, tuple)):
        if len(obj) == 3 and all(isinstance(v, (int, float)) for v in obj):
            point = [obj[0], obj[1], remap_z(obj[2])]
            result = tuple(point) if isinstance(obj, tuple) else point
        else:
            items = [_map_meta(v, key, seen) for v in obj]
            result = tuple(items) if isinstance(obj, tuple) else items
        seen[id(obj)] = (obj, result)  # keep obj alive: ids must not be reused
        return result
    return obj


def _in_povo2(p):
    return p[1] > 12 and p[0] > -40


def apply(boxes, levels):
    link = next(l['connection'] for l in levels if 'connection' in l)
    spec = link['povo2']
    boxes = [b for b in boxes if not b[0].startswith(STAIR_PREFIXES)]
    boxes = [_map_box(b) for b in boxes]
    ext = levels[0].get('exterior', {})
    done = set()   # render and collision lists share mesh records
    for key in ('meshes', 'collision_meshes'):
        for mesh in ext.get(key, []):
            if id(mesh) not in done:done.add(id(mesh));_map_mesh(mesh)
    # Metadata. Stair records are rebuilt below.
    spec['stairs']['rails'] = [r for r in spec['stairs'].get('rails', [])
                               if not r['name'].startswith(STAIR_PREFIXES)]
    for r in spec['stairs']['rails']:
        group = _group(r['name'])
        for k in ('a', 'b'):
            x, y, zz = r[k]
            r[k] = [x, y, zz if r['name'].startswith(STREET_RAILS) else _linear(zz, group) if group
                    else _ramp_z(zz, y) if is_ramp(r['name']) else remap_z(zz)]
    _map_meta(spec)
    # Ramp records follow the ramp profile, not the storey profile.
    cont = spec['parking'].get('continuous')
    if cont:
        for key in ('driveway',):cont[key] = [[x, y, _ramp_z(z, y)] for x, y, z in cont[key]]
        cont['ramp']['centreline'] = [[x, y, _ramp_z(z, y)] for x, y, z in cont['ramp']['centreline']]
        for route in cont.get('routes', []):route['points'] = [[x, y, remap_z(z)] for x, y, z in route['points']]
    if ext.get('entrance'):_map_meta(ext['entrance'])   # Povo 2 double entrance
    terrace = ext.get('terrace_integration')
    if terrace:
        terrace['driveway'] = [[x, y, _ramp_z(z, y)] for x, y, z in terrace['driveway']]
        routes = terrace.get('north_routes', {})
        for key, pts in routes.items():routes[key] = [[x, y, remap_z(z)] for x, y, z in pts]
    # Route records along the uniformly re-risen UP stair.
    up = STAIR_GROUPS[0]
    records = [spec.get('gardens', {}).get('routes', {}), spec.get('additions', {}).get('yard', {}).get('routes', {})]
    for routes in {id(r): r for r in records}.values():   # often the same record
        if 'up' in routes:
            routes['up'] = [[x, y, _linear(unmap_z(z), up)] for x, y, z in routes['up']]
    for level in spec['levels']:level['z'] = NEW[level['floor']]
    link['ground']['floor_elevation_local'] = NEW[0]
    for key in ('lights', 'nav_seeds'):
        link[key] = [[p[0], p[1], remap_z(p[2])] if _in_povo2(p) else p for p in link.get(key, [])]
    boxes = _rebuild_garden_stairs(boxes, spec, terrace)
    boxes = _carve_exterior(boxes, spec)
    boxes = _rebuild_stair(boxes, link, spec)
    spec['level_profile'] = dict(old=OLD, new=NEW, knots=_KNOTS,
        basis='Altitude_Corrections.md section 5b: garden DTM, 16 cm measured risers, street DTM; +1 fixed')
    return boxes


def _rebuild_garden_stairs(boxes, spec, terrace):
    r = (NEW[-1]-NEW[-2])/GARDEN_RISERS
    first = GARDEN_X0+GARDEN_SPLIT*GARDEN_TREAD; second = first+GARDEN_MID
    end = second+(GARDEN_RISERS-GARDEN_SPLIT)*GARDEN_TREAD
    landing = (end, end+1.2)
    rails_meta = spec['stairs']['rails']
    for prefix, y0, y1 in GARDEN_STAIRS:
        old = (prefix+'_down_', prefix+'_midlanding')
        boxes = [b for b in boxes if not b[0].startswith(old)]
        rails_meta[:] = [rl for rl in rails_meta if not rl['name'].startswith(old)]
        add = lambda n, lo, hi, m: boxes.append((n, tuple(lo), tuple(hi), m))
        yc = (y0+y1)/2; route = [[31.2, yc, NEW[-1]], [32.1, yc, NEW[-1]]]
        for i in range(GARDEN_RISERS):
            x = GARDEN_X0+i*GARDEN_TREAD+(GARDEN_MID if i >= GARDEN_SPLIT else 0)
            top = NEW[-1]-r*(i+1)
            add(f'{prefix}_down_step_{i}', (x, y0, top-.16), (x+GARDEN_TREAD, y1, top), 'floor_grating')
            route.append([x+GARDEN_TREAD/2, yc, top])
            if i == GARDEN_SPLIT-1:
                add(prefix+'_midlanding', (first, y0, top-.22), (second, y1, top), 'floor_grating')
                route.append([(first+second)/2, yc, top])
        mid = NEW[-1]-r*GARDEN_SPLIT
        for y in (y0, y1):
            for part, a, b in (('first', (GARDEN_X0, y, NEW[-1]), (first, y, mid)),
                               ('middle', (first, y, mid), (second, y, mid)),
                               ('second', (second, y, mid), (end, y, NEW[-2]))):
                railing(add, rails_meta, f'{prefix}_down_{part}_{y:g}', a, b)
        route.append([sum(landing)/2, yc, NEW[-2]])
        if prefix == 'p2_aligned_garden':
            g = spec['gardens']
            g['down_stair'] = [31.8, y0, end, y1]; g['down_landing'] = [landing[0], y0, landing[1], y1]
            g['routes']['down'] = route
            g['routes']['garden'][0] = [route[-1][0], *g['routes']['garden'][0][1:]]
            yard = spec.get('additions', {}).get('yard', {})
            if 'down_path' in yard:yard['down_path'] = route
        elif terrace:
            terrace['north_landing'] = [landing[0], y0, landing[1], y1]
            terrace['north_routes']['down'] = route
            terrace['north_routes']['garden'][0] = [route[-1][0], *terrace['north_routes']['garden'][0][1:]]
    return boxes


def _carve_exterior(boxes, spec):
    """Unmapped exterior scenery must leave the raised basement volumes."""
    holes = [((lo[0]-.02, lo[1]-.02, hi[2]+.01), (hi[0]+.02, hi[1]+.02, hi[2]+2.4))
             for n, lo, hi, m in boxes if n.startswith(('p2_', 'exterior_p2_'))
             and m.startswith('floor') and hi[2] < NEW[0]-1 and hi[0]-lo[0] > .25 and hi[1]-lo[1] > .25]
    result = []
    for box in boxes:
        n, lo, hi, m = box
        if not n.startswith('exterior_') or (n.startswith(MAPPED) and not n.startswith(STREET)) or is_ramp(n):
            result.append(box);continue
        parts = [box]
        for h in holes:
            if lo[0] < h[1][0] and hi[0] > h[0][0] and lo[1] < h[1][1] and hi[1] > h[0][1] \
                    and lo[2] < h[1][2] and hi[2] > h[0][2]:
                parts = [p for q in parts for p in subtract_box(q, h)]
        result.extend(parts)
    return result


def _rebuild_stair(boxes, link, spec):
    z = NEW
    # Clear the well of everything mapped into it, below the +1 floor plate.
    well = ((WELL_X0, WELL_Y0, z[-2]-.3), (WELL_X1, WELL_Y1, z[1]+.01))
    boxes = [p for b in boxes for p in subtract_box(b, well)]
    result = list(boxes); rails = []

    def add(n, lo, hi, m='wall'):
        if any(a >= b for a, b in zip(lo, hi)):raise ValueError(n)
        result.append((n, tuple(lo), tuple(hi), m))

    def slab(n, x0, x1, h, y0=WELL_Y0, y1=WELL_Y1, m='floor_p2_tile'):
        add(n, (x0, y0, h-.22), (x1, y1, h), m)

    def cut(hole, materials=('wall', 'window_frame', 'exterior_stone', 'door_black', 'door_pushbar')):
        nonlocal result
        result = [p for b in result for p in (subtract_box(b, hole) if b[3] in materials else [b])]

    # Enclosure, full height, keeps closing the old west strip.
    bottom, top = z[-2]-.22, 14.55
    add('p2_stair_well_wall_south', (WELL_X0-.11, SOUTH_WALL_Y-.1, bottom), (WELL_X1+.21, SOUTH_WALL_Y+.1, top))
    add('p2_stair_well_wall_north', (WELL_X0-.11, WELL_Y1, bottom), (WELL_X1+.21, WELL_Y1+.2, top))
    add('p2_stair_well_wall_east', (WELL_X1+.01, WELL_Y0, bottom), (WELL_X1+.21, WELL_Y1, top))
    add('p2_stair_well_wall_west', (WEST-.1, WELL_Y0, bottom), (WEST, WELL_Y1, top))
    slab('p2_stair_well_bottom', WEST, WELL_X1, z[-2])
    portals = []
    for floor, x, y, wall in ((1, WELL_X1+.11, DOOR_Y, 'east'), (0, WELL_X1+.11, DOOR_Y, 'east'),
                              (-1, DOOR_M1_X, SOUTH_WALL_Y, 'south'), (-2, DOOR_M2_X, SOUTH_WALL_Y, 'south')):
        h = z[floor]
        if wall == 'east':
            cut(((x-.4, y-.825, h-.01), (x+.4, y+.825, h+2.25)))
            add(f'p2_stair_door_{floor}_threshold', (x-.3, y-.825, h-.22), (x+.4, y+.825, h), 'floor_p2_tile')
            for s in (-1, 1):
                add(f'p2_stair_door_{floor}_{s}', (x+.15, y+s*.825-.025, h+.02), (x+.95, y+s*.825+.025, h+2.18), 'door_black')
        else:
            cut(((x-.825, y-.4, h-.01), (x+.825, y+.4, h+2.25)))
            add(f'p2_stair_door_{floor}_threshold', (x-.825, y-.4, h-.22), (x+.825, y+.3, h), 'floor_p2_tile')
            # -1 leaves open onto its landing, clear of the corridor approach.
            near, far = (y+.15, y+.95) if floor == -1 else (y-.95, y-.15)
            for s in (-1, 1):
                add(f'p2_stair_door_{floor}_{s}', (x+s*.825-.025, near, h+.02), (x+s*.825+.025, far, h+2.18), 'door_black')
        portals.append(dict(floor=floor, centre=[x if wall == 'south' else WELL_X1+.11, y, h],
                            side='v_max' if wall == 'east' else 'u_min'))
    # Storeys, descending. Each flight: (lane, heading, risers).
    storeys = [(1, 0, [('south', 'west', 13), ('north', 'east', 13)]),
               (0, -1, [('south', 'west', 10), ('north', 'east', 10), ('south', 'west', 10)]),
               (-1, -2, [('north', 'east', 10), ('south', 'west', 10), ('north', 'east', 10)])]
    flights_meta = []; routes = []
    slab('p2_stair_landing_east_1', EAST_EDGE, WELL_X1, z[1])
    for upper, lower, flights in storeys:
        rise = (z[upper]-z[lower])/sum(c for _, _, c in flights)
        far = EAST_EDGE-TREAD*(flights[0][2]-1)          # west end of the flights
        h = z[upper]; path = []
        start_side = 'east' if flights[0][1] == 'west' else 'west'
        for j, (lane, heading, count) in enumerate(flights):
            y0, y1 = LANE[lane]; yc = (y0+y1)/2
            x_start = EAST_EDGE if heading == 'west' else far
            sign = -1 if heading == 'west' else 1
            path.append([x_start-sign*.6, yc, h])
            for i in range(1, count):
                a = x_start+sign*TREAD*(i-1); b = x_start+sign*TREAD*i
                top_z = h-rise*i
                add(f'p2_stair_{lower}_flight{j+1}_step_{i}', (min(a, b), y0, top_z-.22), (max(a, b), y1, top_z),
                    'floor_p2_tile')
                path.append([(a+b)/2, yc, top_z])
                flights_meta.append(dict(lower_floor=lower, flight=j+1, step=i, rise=rise, top=top_z))
            end = x_start+sign*TREAD*(count-1)
            edge = y1 if lane == 'south' else y0
            railing(lambda n, lo, hi, m: result.append((n, tuple(lo), tuple(hi), m)), rails,
                    f'p2_stair_{lower}_rail{j+1}', (x_start, edge, h), (end, edge, h-rise*count))
            h -= rise*count
            path.append([end+sign*.6, yc, h])
            landing_floor = lower if j == len(flights)-1 else None
            name = f'p2_stair_landing_{"west" if heading == "west" else "east"}_{lower}_{j+1}'
            if heading == 'west':slab(name, WEST, far, h)
            else:slab(name, EAST_EDGE, WELL_X1, h)
        routes.append(dict(lower_floor=lower, points=path, flight_counts=[c for _, _, c in flights], rise=rise))
    # Metadata consumed by audits, CS2 export and survey harnesses.
    spec['stairs'].update(bounds=[WELL_X0-.11, SOUTH_WALL_Y-.1, WELL_X1+.21, WELL_Y1+.2],
        well_bounds=[WEST, WELL_Y0, WELL_X1, WELL_Y1], portals=[p for p in portals if p['floor'] <= 0],
        path=[r for r in routes if r['lower_floor'] < 0], flights=flights_meta,
        rails=spec['stairs']['rails']+rails, flight_width=round(LANE['south'][1]-LANE['south'][0], 3),
        tread=TREAD, gap=GAP, flight_counts={'0': [13, 13], '-1': [10, 10, 10], '-2': [10, 10, 10]},
        door_y=DOOR_Y, levels=dict(NEW),
        metric_status='Counts user-confirmed; 16 cm basement risers iPhone-measured; levels from DTM (11 Nov)')
    upper = routes[0]
    link['stair'].update(path=upper['points'][1:-1], prototype_path=upper['points'][1:-1], rails=[],
        risers=26, rise=upper['rise'], tread=TREAD, top=upper['points'][0], bottom=upper['points'][-1],
        middle=[(WEST+EAST_EDGE-TREAD*12)/2, SPLIT, z[0]+13*upper['rise']],
        portals=[p for p in portals if p['floor'] >= 0], module_height=z[1]-z[0],
        bounds=spec['stairs']['bounds'],
        shaft=[[WEST, WELL_Y0, z[0]], [WELL_X1, WELL_Y1, z[0]]])
    for s in link['audit_stations']:
        if s['id'] == 'stair_upper_inside':s['point'] = [19.39, DOOR_Y]
        if s['id'] == 'stair_upper_hall':s['point'] = [21.2, DOOR_Y]
    moves = {-1: {'core_landing': [DOOR_M1_X, DOOR_Y], 'core_door': [DOOR_M1_X, 26.0],
                  'stair_approach': [DOOR_M1_X, 26.0]},
             -2: {'core_landing': [19.39, DOOR_Y], 'core_door': [DOOR_M2_X, 25.8],
                  'vestibule': [DOOR_M2_X, 24.85]},
             0: {'core_landing': [19.39, DOOR_Y]}}
    for level in spec['levels']:
        for s in level['audit_stations']:
            if s['id'] in moves.get(level['floor'], {}):s['point'] = moves[level['floor']][s['id']]
    for route in spec['parking'].get('routes', []):
        route['points'] = [[DOOR_M2_X if abs(p[0]-18.2) < .01 else p[0], *p[1:]] for p in route['points']]
    # -1 routes left the core through the old east door: start at the west landing.
    for route in spec.get('basement_rebuild', {}).get('routes', []):
        pts = route['points']
        if pts and abs(pts[0][0]-19.2) < .01 and pts[0][1] > WELL_Y0 and abs(pts[0][2]-z[-1]) < .01:
            out = next(p for p in pts if p[1] < SOUTH_WALL_Y-.5)
            route['points'] = [[DOOR_M1_X, DOOR_Y, z[-1]], [DOOR_M1_X, out[1], z[-1]],
                               *pts[pts.index(out):]]
    return result
