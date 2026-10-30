"""Povo 2's south front in real coordinates, after registration.

Moves the bridge road to the 2024 orthophoto carriageway and builds what the
user drew outside C5 on 30 Oct: a 2.5 m sunken terrace along the south facade,
a straight UP stair from it to the street pavement, and a metal stair from its
east end down into Garden -2, which extends west to the building as the LiDAR
shows. The old exit landing, garden exit stairs and street-side slopes go.
Numbers: config/povo2_east_entrance.json 'south_front_real'.
"""
import json
import re

ROAD_SHIFT = 5.0  # orthophoto carriageway N -3.5..+3.5; the road was built at N -5
ROAD_NAMES = re.compile(r'exterior_(road_[0-3]$|footway_[0-3]_|road_edge_[0-3]_|road_joint_[0-2]$|'
                        r'crosswalk_|abandoned_bus_)')
OLD_FRONT = ('p2_gardens_up', 'p2_gardens_passage', 'p2_gardens_down', 'p2_basement_gardens_passage',
             'p2_gardens_retaining_west', 'p2_basement_repair_garden_exit', 'p2_repair_entrance_',
             'p2_gardens_street_lawn', 'p2_gardens_street_garden_base', 'p2_gardens_office_garden_approach')


def road_shift(x):
    """Full shift along Povo 2 (E -23..32); tapers to nothing at the E -36
    bend and along the next road segment to E 50, where the unmoved
    front-road link starts. Matches the meshes' linear interpolation."""
    return ROAD_SHIFT * min(1, max(0, (x + 36) / 13)) * min(1, max(0, (50 - x) / 18))


def street_z(x):
    """Pavement top along the moved bridge road (footways sit 0.12 above it)."""
    if x < 22:
        z = 3.0 + (max(x, -23) + 23) / 45
    elif x < 32:
        z = 4.0
    else:
        z = 4.0 + (min(x, 50) - 32) / 18 * 3.6
    return z + .12


def extend(boxes, levels, root):
    from .build_povo_campus import subtract_box, subtract_polygon_box
    from .povo_stairs import railing
    from .build_povo_exterior import FACES
    cfg = json.loads((root / 'config/povo2_east_entrance.json').read_text())['south_front_real']
    ext = levels[0]['exterior']
    link = next(l['connection'] for l in levels if l.get('connection'))
    spec = link['povo2']
    rails = spec['stairs']['rails']
    result = [b for b in boxes if not b[0].startswith(OLD_FRONT)]
    rails[:] = [r for r in rails if not r['name'].startswith(('passage', 'up_', 'down_', 'p2_repair_entrance'))]

    def add(name, lo, hi, mat='wall'):
        if all(a < b for a, b in zip(lo, hi)):
            result.append(('p2_front_' + name, tuple(lo), tuple(hi), mat))

    def rail(name, a, b):
        railing(lambda n, lo, hi, m: result.append((n, tuple(lo), tuple(hi), m)), rails, 'p2_front_' + name, a, b)

    # 1. Road to the real carriageway, with its pavements, bus and crossing.
    def shifted(v): return (v[0], v[1] + road_shift(v[0]), v[2])
    moved = set()  # the same mesh object can sit in both lists
    for key in ('meshes', 'collision_meshes'):
        for mesh in ext[key]:
            if ROAD_NAMES.match(mesh['name']) and id(mesh) not in moved:
                moved.add(id(mesh))
                mesh['vertices'] = [shifted(v) for v in mesh['vertices']]
    result = [(n, shifted(lo), shifted(hi), m) if ROAD_NAMES.match(n) else (n, lo, hi, m)
              for n, lo, hi, m in result]

    # 2. Clear exterior context from every new outside volume.
    t = cfg['terrace']; s = cfg['up_stair']; g = cfg['garden_extension']; p = cfg['pavement']; v = cfg['verge']
    holes = [((p['x'][0], -4.4, 2.0), (50.0, 4.4, 9.0)),                 # moved road band
             ((t[0] - .2, p['north_edge'], .17), (t[2], t[3], 4.3)),      # terrace
             ((s[0] - .2, s[1], .17), (s[2] + .2, p['north_edge'], 4.3)),  # UP stair
             ((t[2], g[1] - .2, -3.6), (g[2], g[3] + .2, 4.3))]           # metal stair and garden
    keep = ('road', 'footway', 'crosswalk', 'abandoned_bus', 'povo2_', 'p2_entry', 'tree')
    def clear(b):
        return b[0].startswith('exterior_') and not any(k in b[0] for k in keep)
    for h in holes:
        result = [q for b in result for q in (subtract_box(b, h) if clear(b) else [b])]
    for key in ('meshes', 'collision_meshes'):
        out = []
        for mesh in ext[key]:
            if any(k in mesh['name'] for k in keep):
                out.append(mesh); continue
            vv = mesh['vertices']
            low = [min(q[i] for q in vv) for i in range(3)]; high = [max(q[i] for q in vv) for i in range(3)]
            hit = [h for h in holes if all(low[i] < h[1][i] and high[i] > h[0][i] for i in range(3))]
            if not hit:
                out.append(mesh); continue
            vertices, faces = [], []
            for face in mesh['faces']:
                polys = [[(tuple(vv[i]), (0, 0)) for i in face]]
                for lo, hi in hit:
                    polys = [q for poly in polys for q in subtract_polygon_box(poly, lo, hi)]
                for poly in polys:
                    start = len(vertices); vertices.extend(q for q, _ in poly)
                    faces.extend((start, start + j, start + j + 1) for j in range(1, len(poly) - 1))
            if faces:
                out.append(dict(mesh, vertices=vertices, faces=faces))
        ext[key] = out

    # 2b. The exterior's solid Povo 2 mass and buried ground were cut around
    # the interior's old position. Clear them wherever a moved floor slab, the
    # stair core or the bridge lobby now stands.
    rooms = [((lo[0] - .05, lo[1] - .05, hi[2] - .25), (hi[0] + .05, hi[1] + .05, hi[2] + 3.0))
             for n, lo, hi, m in result
             if n.startswith(('p2_', 'academic_first_link_p2_')) and m.startswith('floor_')
             and hi[2] - lo[2] < .5 and not n.startswith(('p2_gardens', 'p2_front'))]
    a, b, c, d = spec['stairs']['bounds']
    rooms.append(((a, b, -3.5), (c, d, 14.6)))
    a, b, c, d = link['povo2_arrival']
    rooms.append(((a + .1, b + .1, 11.2), (c - .1, d - .1, 14.5)))
    solid = ('exterior_ground', 'exterior_povo2_context', 'exterior_povo2_front_annex', 'exterior_garage_',
             'exterior_povo2_lightwell', 'exterior_povo2_front_window', 'exterior_povo2_front_sill',
             'exterior_povo2_end_window')
    def overlaps(lo, hi, h): return all(lo[i] < h[1][i] and hi[i] > h[0][i] for i in range(3))
    out = []
    for box in result:
        if box[0].startswith(solid):
            parts = [box]
            for h in rooms:
                if overlaps(box[1], box[2], h):
                    parts = [q for part in parts for q in subtract_box(part, h)]
            out.extend(parts)
        else:
            out.append(box)
    result = out

    # 3. Street pavement north of the road, and a verge on the old road strip.
    north = p['north_edge']; gap = (s[0], s[2])
    x = p['x'][0]
    while x < p['x'][1] - 1e-6:
        x1 = min(p['x'][1], x + 1.0); z = street_z((x + x1) / 2) if x1 <= 32 + 1e-6 else 4.12
        y1 = north if x1 <= g[2] + 1e-6 else 8.6
        # East of E 32 the road climbs and tapers south; an earth bank drops
        # from its footway to the pavement at garden street level.
        y0 = max(road_shift(x), road_shift(x1)) - .6
        if x1 > 32 + 1e-6:
            y0 = max(4.4, y0 + 1.85)
        for a, b in ((x, min(x1, gap[0])), (max(x, gap[1]), x1)):
            if b - a > 1e-6:
                add(f'pavement_{x:.1f}_{a:.2f}', (a, y0, 2.5), (b, y1, z), 'exterior_paving')
        x = x1
    x = v['x'][0]
    while x < v['x'][1] - 1e-6:
        x1 = min(v['x'][1], x + 1.0); z = street_z((x + x1) / 2) - .02
        top = min(road_shift(x), road_shift(x1)) - 9.4
        add(f'verge_{x:.1f}', (x, v['y'][0] if x >= 24 else -8.0, 2.5), (x1, top, z), 'floor_yard_grass')
        x = x1

    # 4. Sunken terrace along the facade, retained against the pavement.
    add('terrace_floor', (t[0], north + .16, .18), (t[2], t[3], .4), 'floor_terrace')
    x = t[0] - .16
    while x < g[2] - 1e-6:
        x1 = min(g[2], x + 1.0); top = street_z(x1)
        bottom = .4 if x1 <= t[2] + 1e-6 else -3.42
        for a, b in ((x, min(x1, gap[0])), (max(x, gap[1]), x1)):
            if b - a > 1e-6:
                add(f'retaining_{x:.2f}_{a:.2f}', (a, north, bottom), (b, north + .16, top))
        x = x1
    add('terrace_end_west', (t[0] - .16, north, .4), (t[0], t[3], street_z(t[0])))
    for a, b in ((t[0], gap[0]), (gap[1], g[2])):
        rail(f'pavement_edge_{a:.1f}', (a, north + .08, street_z(a)), (b, north + .08, street_z(b)))

    # 4b. Floor 0's south rooms reached past the real facade, over the terrace.
    # Clip them at the facade line and close them with a new south wall.
    facade = t[3] + .16
    clip = ((-1.0, -20.0, 3.75), (26.0, facade, 7.6))
    ground = [b for b in result if b[0].startswith('p2_ground_') and overlaps(b[1], b[2], clip)]
    span = (min(b[1][0] for b in ground), max(b[2][0] for b in ground)) if ground else None
    furniture = ('_chair_', '_desk_', '_teaching_', '_monitor', '_table', '_seat')
    out = []
    for box in result:
        n, lo, hi, mat = box
        if not n.startswith('p2_ground_') or not overlaps(lo, hi, clip):
            out.append(box)
        elif not any(k in n for k in furniture):
            out.extend(subtract_box(box, clip))
        elif (lo[1] + hi[1]) / 2 > facade + .4:
            out.append(box)
    result = out
    clipped = [r for l in spec['levels'] if l['floor'] == 0 for r in l.get('rooms', []) if r['bounds'][1] < facade]
    if span:
        # New south facade of floor 0, with each clipped room's window.
        edges = [span[0]]
        for room in sorted(clipped, key=lambda r: r['bounds'][0]):
            a0, c0 = max(room['bounds'][0], span[0]) + .3, min(room['bounds'][2], span[1]) - .3
            if c0 - a0 < .5:
                continue
            edges += [a0, c0]
            add(f'ground_south_sill_{room["id"]}', (a0, t[3], 4.0), (c0, facade, 4.9))
            add(f'ground_south_lintel_{room["id"]}', (a0, t[3], 6.9), (c0, facade, 7.35))
            result.append(('p2_ground_' + room['id'] + '_window_glass', (a0, t[3] + .06, 4.9), (c0, t[3] + .1, 6.9), 'window_glass'))
        edges.append(span[1])
        for i in range(0, len(edges), 2):
            add(f'ground_south_wall_{i // 2}', (edges[i], t[3], 4.0), (edges[i + 1], facade, 7.35))
    for level in spec['levels']:
        if level['floor'] == 0:
            for station in level.get('audit_stations', []):
                if station['point'][1] < facade + .8 and -1 < station['point'][0] < 26:
                    station['point'] = [station['point'][0], facade + .8, *station['point'][2:]]
    ground_rooms = [r for l in spec['levels'] if l['floor'] == 0 for r in l.get('rooms', [])]
    ground_rooms += spec.get('ground', {}).get('rooms', [])
    for room in ground_rooms:
        if True:
            for key in ('bounds', 'footprint_local_metres'):
                if key in room and room[key][1] < facade:
                    room[key][1] = facade
            fitout = room.get('fitout', {})
            if 'audit_points_local_metres' in fitout:
                fitout['audit_points_local_metres'] = [type(q)((q[0], max(q[1], facade + .8), *q[2:]))
                                                       for q in fitout['audit_points_local_metres']]
    # 4c. Registration narrows floor 0's classroom side aisles below the
    # standing hull. Carve each aisle through the seating rows again.
    keep_parts = ('wood_floor', '_floor', 'wall', 'window', 'ceiling', 'door', 'sign', 'board', 'plaque', 'light')
    def kept(name): return any(k in re.sub(r'(_windowcut_\d+)+', '', name) for k in keep_parts)
    stations = [st for l in spec['levels'] if l['floor'] == 0 for st in l.get('audit_stations', [])]
    for room in [r for l in spec['levels'] if l['floor'] == 0 for r in l.get('rooms', [])]:
        a0, b0, c0, d0 = room['bounds']
        def inside(x): return min(max(x, a0 + .63), c0 - .63)
        fitout = room.get('fitout', {})
        if fitout.get('audit_points_local_metres'):
            fitout['audit_points_local_metres'] = [type(q)((inside(q[0]), *q[1:])) for q in fitout['audit_points_local_metres']]
        points = list(fitout.get('audit_points_local_metres', []))
        for st in stations:
            if st['id'].startswith(room['id'] + '_aisle'):
                st['point'] = [inside(st['point'][0]), *st['point'][1:]]
                points.append(st['point'])
        seats = ('p2_ground_room_' + room['id'] + '_', 'p2_ground_' + room['id'] + '_tier')
        for q in points:
            hole = ((q[0] - .55, b0, 4.01), (q[0] + .55, d0, 5.95))
            result = [part for b in result for part in
                      (subtract_box(b, hole) if b[0].startswith(seats) and not kept(b[0])
                       and overlaps(b[1], b[2], hole) else [b])]
    # 5. Straight UP stair from the terrace to the pavement (user: steep, straight).
    n = cfg['up_stair_risers']; top = street_z((s[0] + s[2]) / 2); run = s[3] - s[1]
    for i in range(n):
        y0 = s[3] - (i + 1) * run / n; z = .4 + (i + 1) * (top - .4) / n
        add(f'up_step_{i}', (s[0], y0, .18), (s[2], y0 + run / n, z), 'floor_grating')
    for i, xx in enumerate((s[0] - .16, s[2])):
        add(f'up_side_{i}', (xx, s[1], .4), (xx + .16, north, top))
        rail(f'up_handrail_{i}', (xx + (.24 if i == 0 else -.08), s[3], .4), (xx + (.24 if i == 0 else -.08), s[1], top))
        rail(f'up_top_{i}', (xx + .08, s[1], top), (xx + .08, north, top))

    # 6. Metal stair from the terrace's east end down into Garden -2.
    m = cfg['metal_stair']; rise = 3.6 / (2 * m['risers_per_flight']); y0, y1 = m['y']
    x0 = m['start_x']; xs = []
    for flight in range(2):
        for i in range(m['risers_per_flight']):
            z = .4 - (flight * m['risers_per_flight'] + i + 1) * rise
            add(f'garden_step_{flight}_{i}', (x0, y0, z - .06), (x0 + m['tread'], y1, z), 'floor_grating')
            x0 += m['tread']
        xs.append(x0)
        if flight == 0:
            add('garden_landing', (x0, y0, z - .06), (x0 + m['landing'], y1, z), 'floor_grating'); x0 += m['landing']
    rail('garden_stair_north_0', (m['start_x'], y1 - .04, .4), (xs[0], y1 - .04, -1.4))
    rail('garden_stair_north_1', (xs[0], y1 - .04, -1.4), (xs[0] + m['landing'], y1 - .04, -1.4))
    rail('garden_stair_north_2', (xs[0] + m['landing'], y1 - .04, -1.4), (xs[1], y1 - .04, -3.2))
    add('garden_extension_floor', (g[0] - .45, g[1] + .16, -3.42), (g[2] + .18, g[3], -3.2), 'floor_yard_grass')
    add('garden_extension_west', (g[0] - .45, t[3], -3.42), (g[0], g[3], 4.0))
    add('garden_extension_under_terrace', (g[0] - .45, g[1] + .16, -3.42), (g[0], t[3], .34))
    add('garden_top_landing', (t[2], g[1] + .16, .34), (m['start_x'], t[3], .4), 'floor_grating')
    # The -2 corridor from the core vestibule ends at E 27, N 20.3-22.3; its
    # garden door opens into a northern bay of the extension.
    bay = (27.44, g[3], g[2], 22.4)
    add('garden_extension_north', (g[0] - .45, g[3], -3.42), (bay[0], g[3] + .16, 4.0))
    add('garden_bay_floor', (bay[0], bay[1], -3.42), (bay[2], bay[3], -3.2), 'floor_yard_grass')
    add('garden_bay_north', (bay[0], bay[3], -3.42), (bay[2] + .18, bay[3] + .16, 4.0))
    add('garden_bay_east', (bay[2], g[3] + .16, -3.42), (bay[2] + .18, bay[3], 4.0))
    rail('garden_extension_north_top', (g[0], g[3] + .08, 4.0), (bay[0], g[3] + .08, 4.0))
    rail('garden_bay_north_top', (bay[0], bay[3] + .08, 4.0), (bay[2], bay[3] + .08, 4.0))

    # 6b. The -2 parking lobe reached past the facade, under the terrace and
    # street. Clip it at the facade line and close it with a wall.
    lot = spec['parking']
    cut_south = ((-30.0, -20.0, -3.6), (9.0, facade, .17))
    lobe = [b for b in result if b[0].startswith('p2_parking_') and overlaps(b[1], b[2], cut_south)]
    if lobe:
        x0, x1 = min(b[1][0] for b in lobe), max(b[2][0] for b in lobe)
        out = []
        for box in result:
            if box[0].startswith('p2_parking_') and overlaps(box[1], box[2], cut_south):
                if '_car' in box[0] or '_column' in box[0]:
                    if (box[1][1] + box[2][1]) / 2 > facade + .4:
                        out.append(box)
                    continue
                out.extend(subtract_box(box, cut_south))
            else:
                out.append(box)
        result = out
        add('parking_south_wall', (x0, facade, -3.2), (x1, facade + .2, -.1))
    for key in ('bounds',):
        if lot.get(key) and lot[key][1] < facade:
            lot[key][1] = facade + .2
    lot['areas'] = [[a, max(b, facade + .2), c, d] for a, b, c, d in lot.get('areas', []) if d > facade + .2]
    lot['columns'] = [p for p in lot.get('columns', []) if p[1] > facade + .4]
    for level in spec['basement_rebuild']['levels']:
        if level['floor'] == -2:
            level['areas'] = [[a, max(b, facade + .2), c, d] for a, b, c, d in level['areas'] if d > facade + .2]
    for route in spec['basement_rebuild']['routes'] + lot.get('routes', []):
        for q in route['points']:
            if abs(q[2] + 3.2) < .1 and q[1] < facade + 1.2 and q[0] < 9:
                q[1] = facade + 1.2
    for level in spec['levels']:
        if level['floor'] == -2:
            for station in level.get('audit_stations', []):
                if station['point'][1] < facade + 1.2 and station['point'][0] < 9:
                    station['point'][1] = facade + 1.2

    # 3b. Earth bank from the climbing road's footway down to the pavement.
    bank = []
    for i in range(18):
        xa = 32 + i; xb = xa + 1
        ya, yb = road_shift(xa) - .6, road_shift(xb) - .6
        za, zb = street_z(xa), street_z(xb)
        quad = [(xa, ya, za), (xb, yb, zb), (xb, max(4.4, yb + 1.85), 4.12), (xa, max(4.4, ya + 1.85), 4.12)]
        bank.append(dict(name=f'exterior_p2_front_bank_{i}', vertices=[(q[0], q[1], 2.5) for q in quad] + quad,
                         faces=FACES, material='exterior_grass'))
    ext['meshes'].extend(bank); ext['collision_meshes'].extend(bank)
    # The bend's north footway now crosses the garage ramp mouth; clip it.
    ramp = ((-31.75, -8.0, 2.0), (-26.25, 30.0, 4.0))
    for key in ('meshes', 'collision_meshes'):
        out = []
        for mesh in ext[key]:
            if not mesh['name'].startswith('exterior_footway_3_'):
                out.append(mesh); continue
            vv = mesh['vertices']; vertices, faces = [], []
            for face in mesh['faces']:
                for poly in subtract_polygon_box([(tuple(vv[i]), (0, 0)) for i in face], *ramp):
                    start = len(vertices); vertices.extend(q for q, _ in poly)
                    faces.extend((start, start + j, start + j + 1) for j in range(1, len(poly) - 1))
            if faces:
                out.append(dict(mesh, vertices=vertices, faces=faces))
        ext[key] = out

    # 6c. Floor 0's east entrance hall, in the real annex, joins the registered
    # interior to the geo-registered entrance doors.
    h = cfg['east_entrance_hall']
    hall = ((h[0] - .2, h[1] + .16, 4.0), (h[2], h[3] - .16, 7.29))
    result = [q for b in result if not b[0] == 'p2_ground_outside_landing'
              for q in (subtract_box(b, hall) if (b[0].startswith('p2_ground_') or b[0].startswith('exterior_povo2_'))
                        and b[3] in ('wall', 'window_glass', 'window_frame') else [b])]
    add('east_hall_floor', (h[0], h[1], 3.78), (h[2], h[3], 4.0), 'floor_p2_tile')
    add('east_hall_ceiling', (h[0], h[1], 7.29), (h[2], h[3], 7.35), 'ceiling_panel')
    add('east_hall_south', (h[0], h[1], 4.0), (h[2], h[1] + .16, 7.35))
    add('east_hall_north', (h[0], h[3] - .16, 4.0), (h[2], h[3], 7.35))
    add('east_hall_east', (h[2] - .16, 38.8, 4.0), (h[2], h[3] - .16, 7.35))

    # 7. Metadata and walking routes (real coordinates; added after registration).
    c5x = 18.44  # C5 E 17.0-19.02; clear of the parked WI1 leaves
    spec['south_front'] = dict(cfg, source='config/povo2_east_entrance.json', road_shift_north=ROAD_SHIFT)
    gardens = spec['gardens']
    for k in ('passage', 'up_stair', 'up_top', 'down_landing', 'down_stair', 'exit_door', 'indoor_corridor', 'indoor_turn'):
        gardens.pop(k, None)
    gardens['garden'] = [g[0], g[1], gardens['garden'][2], gardens['garden'][3]]
    gardens['routes'] = dict(
        street=[[c5x, s[1] + .05, top], [c5x, 7.95, .4], [c5x, 9.4, .4]],
        garden=[[c5x, 9.0, .4], [m['start_x'] - .5, 8.9, .4], [m['start_x'], 8.9, .4], [xs[0], 8.9, -1.4],
                [xs[0] + m['landing'], 8.9, -1.4], [xs[1], 8.9, -3.2], [xs[1] + .8, 8.9, -3.2], [40.0, 14.0, -3.2]])
    spec['additions']['yard']['routes'] = gardens['routes']
    routes = spec['basement_rebuild']['routes']
    routes.append(dict(id='street_to_c5', points=[*gardens['routes']['street'], [c5x, 11.0, .4]]))
    routes.append(dict(id='terrace_to_garden', points=gardens['routes']['garden']))
    return result
