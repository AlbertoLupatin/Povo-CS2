"""Fit the marked Povo 2 exterior terrace to the assembled campus."""
import hashlib
import json

from .build_povo2_minus1_terrace import build as build_terrace
from .povo2_roadside_closure import _along_y, _hexa
from .povo_floor_surfaces import area, subtract
from .povo_room_fitout import subtract_box
from .povo_stairs import railing
from .povo_street_footways import is_street_footway, prism, tops

CONFIG = 'config/povo2_minus1_terrace.json'
PLAN = 'exports/povo2_west_offices_20261029/layout.json'
PREFIX = 'exterior_p2_terrace_'
CONCRETE = 'exterior_concrete'


def clear_ramp_footways(ext, left, right, mouth, portal):
    """Terminate the crossing curb at the garage driveway, with closed ends."""
    cut = [(left, mouth), (right, mouth), (right, portal), (left, portal)]
    replacements = {}
    for mesh in ext['meshes']:
        if not is_street_footway(mesh):
            continue
        vv = mesh['vertices']
        if (max(v[0] for v in vv) <= left or min(v[0] for v in vv) >= right
                or max(v[1] for v in vv) <= mouth or min(v[1] for v in vv) >= portal):
            continue
        caps = tops(mesh)
        parts = [p for cap in caps for p in subtract(cap, cut)]
        if sum(map(area, caps)) - sum(map(area, parts)) < 1e-8:
            continue
        thickness = vv[len(vv) // 2][2] - vv[0][2]
        replacements[mesh['name']] = [
            piece for i, part in enumerate(parts)
            if (piece := prism(f"{mesh['name']}_terrace_cut_{i}", part, mesh['material'], thickness))
        ]
    for key in ('meshes', 'collision_meshes'):
        ext[key] = [piece for mesh in ext[key] for piece in replacements.get(mesh['name'], [mesh])]


def extend(boxes, levels, root):
    ext = levels[0]['exterior']
    link = next(level['connection'] for level in levels if 'connection' in level)
    p2 = link['povo2']
    cfg = json.loads((root / CONFIG).read_text())
    plan = json.loads((root / PLAN).read_text())
    terrace = build_terrace(plan, cfg)
    slabs = {s['id']: s['bounds'] for s in terrace['slabs']}
    west, facade = terrace['outer_edge_east'], terrace['facade_east']
    z = terrace['z']
    underside = z - .22
    approved = p2['drawio_entrance']['areas']['terrace']
    join, south, _, front = approved
    _, portal, _, north = ext['garage_bounds']
    old_south = cfg['south_run']['north'][1]
    old_north = slabs['north_run'][1]
    north_edge = north + cfg['outer_edge']['width']
    old_offices_end = max(r['bounds'][3] for r in plan['west_offices']['rooms'])
    offset = front - old_south

    def registered(y):
        # The office windows keep their installed registration. Fit the
        # unsurveyed remainder between that datum and the existing north facade.
        if y <= old_offices_end:
            return y + offset
        start = old_offices_end + offset
        return start + (north - start) * (y - old_offices_end) / (old_north - old_offices_end)

    def rect(r):
        return [r[0], registered(r[1]), r[2], registered(r[3])]

    slabs = {name: rect(r) for name, r in slabs.items()}
    slabs['south_run'] = [west, south, join, front]
    slabs['north_run'][3] = north_edge
    slabs['recess_room1_l28'][1] = slabs['west_strip_0'][3]
    south_garden = p2['gardens']
    mirror = north + front
    garden_x, _, garden_east, garden_far = south_garden['garden']
    garden_south = mirror - garden_far
    low = south_garden['garden_z']
    base = low - .25
    street = 3.06
    ramp = json.loads((root / 'config/povo_exterior.json').read_text())['garage_ramp']
    mouth, portal_point = ramp['centreline']
    ramp_left, ramp_right = (mouth[0] + sign * ramp['width'] / 2 for sign in (-1, 1))
    clear_ramp_footways(ext, ramp_left, ramp_right, mouth[1], portal)
    # The garage deck and facade-side strip share one level. Connect the
    # south corner, both recesses and the north run while keeping the middle
    # and north openings over the garage and the open driveway below.
    first, second = (slabs[f'west_strip_{i}'] for i in range(2))
    near, far = slabs['recess_room1_l28'], slabs['recess_l28_room2']
    slabs.update(west_south_join=[west, front, facade, first[1]],
                 west_near_bay_join=[west, first[3], facade, near[1]+2.],
                 west_far_bay_join=[west, far[3]-2., facade, second[1]],
                 west_north_join=[west, north-2., facade, north])
    holes = [[west, near[1]+2., facade, far[3]-2.], [west, second[3], facade, north-2.]]
    labs = [r['bounds'] for level in p2['levels'] if level['floor'] == -1
            for r in level['rooms'] if r['id'].startswith('cibio_office_')]
    # The corner carriageway crosses the first part of the former slope.
    # Keep the driveway flush across that junction before it starts to descend.
    descent = 1.
    west_walk = -33.6
    verge_edge = 4.09
    coping = .16
    bend = next(m for m in ext['meshes'] if m['name'] == 'exterior_road_north_footway_3_-1_roadcut_0')
    curb = tops(bend)[0]
    curb_start = min(curb, key=lambda v: v[1])
    curb_end = min((v for v in curb if v[0] > west), key=lambda v: v[1])
    curb_slope = (curb_end[1] - curb_start[1]) / (curb_end[0] - curb_start[0])

    def curb_y(x):
        return curb_start[1] + (x - curb_start[0]) * curb_slope

    def curb_x(y):
        return curb_start[0] + (y - curb_start[1]) / curb_slope

    # Remove only the old context surface and the parking roof within the
    # marked lightwells. Keep the live rooms, their windows and the garage floor.
    context = ('exterior_ground', 'exterior_west_grass')
    road = next(m for m in ext['meshes'] if m['name'] == 'exterior_registered_footway_north_4_terminal_0')
    (corner_x, corner_y, corner_z), (end_x, _, end_z) = sorted(
        v for v in tops(road)[0] if abs(v[1] - verge_edge) < 1e-7)
    corner_west_y = corner_y + (west - corner_x) * 10. / 11.
    cuts = [(context, ((west, south, underside), (join, front, 4.))),
            (context, ((west, verge_edge, base), (join, south, 4.))),
            (context, ((west, corner_west_y, z), (corner_x, verge_edge, 4.))),
            (context, ((west_walk, 0., base), (ramp_left, north, street))),
            (context, ((ramp_left, portal, .45), (ramp_right, north, street))),
            (context, ((ramp_right, verge_edge, base), (west, portal, street))),
            (context, ((west, front, underside), (-13.92, north, 3.5))),
            (context, ((ramp_right, front, .45), (west, north, street))),
            (context, ((west, north, base), (garden_x, north_edge + .16, 4.))),
            (context, ((garden_x - .16, garden_south - .16, base),
                       (garden_east + .16, north_edge + .16, 4.))),
            (('exterior_garage_roof',), ((west_walk, portal, .18), (west, north, .46)))]
    for r in (*slabs.values(), *holes):
        cuts.append((('exterior_garage_roof',), ((r[0], r[1], underside), (r[2], r[3], .46))))
    # Finish the exposed garage roof at the CIBIO glass line. The old site
    # cap was visible as a floating strip through the middle of the windows.
    for x, a, _, b in labs:
        cuts.extend([(context, ((-17.32, a, z), (x+.12, b, 3.5))),
                     (('exterior_garage_roof',), ((-17.32, a, .2), (x+.12, b, .46)))])
    result = []
    for item in boxes:
        if item[0] == 'p2_basement_drawio_terrace_retaining_west_end':
            continue
        parts = [item]
        for prefixes, cut in cuts:
            if item[0].startswith(prefixes):
                parts = [piece for part in parts for piece in subtract_box(part, cut)]
        result.extend(parts)

    def box(name, lo, hi, material=CONCRETE):
        result.append((PREFIX + name, tuple(lo), tuple(hi), material))

    def plate(name, r, floor, material='floor_terrace'):
        a, b, c, d = r
        box(name, (a, b, floor - .22), (c, d, floor), material)

    def add_mesh(part):
        ext['meshes'].append(part)
        ext['collision_meshes'].append(part)

    rails = p2['stairs']['rails']

    def guard(name, a, b):
        railing(box, rails, PREFIX + name, a, b, height=terrace['barrier_height'], bars=2)

    # Build the extension to the approved south strip and both marked west
    # sections, with the two wider recesses set back to the office-row line.
    for name, r in slabs.items():
        plate(name, r, z)
    for i, (x, a, _, b) in enumerate(labs):
        plate(f'cibio_window_apron_{i}', [-17.32, a, x, b], z)
    for i, (a, b, c, d) in enumerate(holes):
        guard(f'lightwell_{i}_west', (a-.06, b, z), (a-.06, d, z))
        guard(f'lightwell_{i}_south', (a, b-.06, z), (c, b-.06, z))
        guard(f'lightwell_{i}_north', (a, d+.06, z), (c, d+.06, z))
        for j, (_, y0, _, y1) in enumerate((near, far)):
            if max(b, y0) < min(d, y1):
                guard(f'lightwell_{i}_bay_{j}', (c+.06, max(b, y0), z), (c+.06, min(d, y1), z))
    guard('south_corner_west', (west + .06, south, z), (west + .06, portal + .06, z))
    guard('north_corner_west', (west + .06, north, z), (west + .06, north_edge, z))

    # The south terrace joins the original -1 strip. A narrow retaining wall
    # takes the grade change at the sidewalk, including its diagonal corner.
    sections = [(west, corner_west_y, corner_z),
                (corner_x, corner_y, corner_z),
                (join, verge_edge, corner_z + (end_z - corner_z) * (join - corner_x) / (end_x - corner_x))]
    for i, ((x0, y0, z0), (x1, y1, z1)) in enumerate(zip(sections, sections[1:])):
        wall = [(x0, y0), (x1, y1), (x1, y1 + coping), (x0, y0 + coping)]
        deck = [(x0, y0 + coping), (x1, y1 + coping), (x1, south), (x0, south)]
        add_mesh(_hexa(PREFIX + f'south_sidewalk_retaining_{i}', wall, [base] * 4,
                       [z0, z1, z1, z0], CONCRETE))
        add_mesh(_hexa(PREFIX + f'south_deck_{i}', deck, [base] * 4, [z] * 4, 'floor_terrace'))
        guard(f'south_sidewalk_guard_{i}', (x0, y0 + coping / 2, z0), (x1, y1 + coping / 2, z1))
    # Close the cut against the existing planted bank where the terrace ends.
    bank = next(m for m in ext['meshes'] if m['name'] == 'exterior_registered_grass_0_0')
    (_, bank_road, bank_top), (_, bank_toe, bank_bottom) = sorted(
        v for v in tops(bank)[0] if abs(v[0] - join) < 1e-7)
    bank_grade = (bank_bottom - bank_top) / (bank_toe - bank_road)
    add_mesh(_along_y(PREFIX + 'south_bank_return', bank_road + coping, bank_toe,
                      join - coping, join,
                      (z, bank_top + bank_grade * coping), (z, bank_bottom), CONCRETE))

    # Retain the driveway and the road. The deck above the garage roof is at
    # the office threshold, with a separate wall supporting the higher street.
    ramp_parts = ('exterior_ramp_retaining_', 'exterior_garage_ramp_straight')
    for key in ('meshes', 'collision_meshes'):
        ext[key] = [m for m in ext[key] if not m['name'].startswith(ramp_parts)]
    for name, y0, y1, z0, z1 in (
            ('driveway', mouth[1], descent, mouth[2], mouth[2]),
            ('garage_ramp', descent, portal, mouth[2], portal_point[2])):
        mesh = _along_y(PREFIX + name, y0, y1, ramp_left, ramp_right,
                        (z0 - .25, z0), (z1 - .25, z1), 'exterior_asphalt')
        ext['meshes'].append(mesh)
        ext['collision_meshes'].append(mesh)
    box('ramp_west_abutment', (west_walk, 0., base), (ramp_left, portal, street))
    box('ramp_east_abutment', (ramp_right, verge_edge, base), (west, front, z))
    box('portal_deck', (west_walk + coping, portal, .2), (west, north, z), 'floor_terrace')
    box('portal_west_foundation', (west_walk + coping, portal, base), (-32.5, north, .2))
    box('west_sidewalk_retaining', (west_walk, portal, base), (west_walk + coping, north, 3.12))
    guard('ramp_west_guard', (ramp_left - .06, 1., street), (ramp_left - .06, portal - .06, street))
    guard('ramp_west_return', (west_walk + coping / 2, portal - .06, street),
          (ramp_left - .06, portal - .06, street))
    guard('west_sidewalk_guard', (west_walk + coping / 2, portal - .06, 3.12),
          (west_walk + coping / 2, curb_y(west_walk + coping), 3.12))
    guard('portal_edge_guard', (west_walk + coping + .06, portal + .06, z),
          (west + .06, portal + .06, z))

    # Close the inside of the raised sidewalk where it curves above the
    # north end of the deck. This backing starts above the garage ceiling.
    north_turn = curb_x(north)
    sidewalk_end = curb_y(west_walk + coping)
    add_mesh(prism(PREFIX + 'west_bend_retaining',
                   [(west_walk + coping, sidewalk_end, 3.12), (north_turn, north, 3.12),
                    (west_walk + coping, north, 3.12)], CONCRETE, thickness=3.12 - z))
    box('west_deck_north_retaining', (north_turn, north - coping, z), (ramp_right, north, 2.75))
    guard('west_bend_guard', (west_walk + coping / 2, sidewalk_end, 3.12),
          (north_turn - .06, north, 3.12))
    guard('west_deck_north_guard', (north_turn, north - coping / 2, 2.75),
          (ramp_right, north - coping / 2, 2.75))

    # The first lightwell is beside the descending ramp and the existing
    # parking wall. Its gutter meets the live ramp without widening its portal.
    def ramp_grade(y):
        fraction = (y - descent) / (portal - descent)
        return mouth[2] + (portal_point[2] - mouth[2]) * fraction

    verge_grade, front_grade = ramp_grade(verge_edge), ramp_grade(front)
    add_mesh(_along_y(PREFIX + 'ramp_east_curb', verge_edge, front, ramp_right, ramp_right + coping,
                      (z, verge_grade + .12), (z, front_grade + .12), CONCRETE))
    guard('ramp_east_guard', (ramp_right + coping / 2, verge_edge, verge_grade + .12),
          (ramp_right + coping / 2, front, front_grade + .12))
    guard('ramp_east_return', (ramp_right + coping / 2, front - .06, z), (west, front - .06, z))
    add_mesh(_along_y(PREFIX + 'ramp_gutter', front, portal, ramp_right, -25.1,
                      (front_grade - .25, front_grade), (base, low), 'exterior_asphalt'))
    parking_end = max(hi[1] for name, _, hi, _ in boxes if name.startswith('p2_parking_rebuilt_wall_0'))
    box('ramp_gutter_return', (-25.1, parking_end, base), (facade, portal, -.1))

    # Enclose the unmodelled building behind the terrace. The floor 0 shell
    # and the existing -1 office glazing retain their own positions.
    recesses = sorted((r for n, r in slabs.items() if n.startswith('recess_')), key=lambda r: r[1])
    west_start = registered(old_offices_end)
    spans = [(west_start, recesses[0][1], facade),
             (recesses[0][1], recesses[0][3], recesses[0][2]),
             (recesses[0][3], recesses[1][1], facade),
             (recesses[1][1], recesses[1][3], recesses[1][2]),
             (recesses[1][3], north, facade)]
    for i, (a, b, x) in enumerate(spans):
        box(f'podium_west_{i}', (x, a, z), (x + .18, b, 3.78))
        box(f'soffit_west_{i}', (min(x, -23.), a, 3.78), (max(-23., x + .18), b, 4.))
    for i, (_, a, x, b) in enumerate(recesses):
        box(f'podium_return_south_{i}', (facade + .18, a - .18, z), (x + .18, a, 3.78))
        box(f'podium_return_north_{i}', (facade + .18, b, z), (x + .18, b + .18, 3.78))
    for i, r in enumerate(terrace['columns']):
        a, b, c, d = rect(r)
        box(f'bay_column_{i}', (a, b, z), (c, d, 3.78))
    box('soffit_west_offices', (facade, front, 3.5), (-23., west_start, 4.))
    # Bridge the narrow registration offset between the basement glazing and
    # the old floor-0 facade. Existing solids take precedence at the seam.
    cap = (PREFIX + 'soffit_south', (facade, 10., 3.5), (join, 11.2, 4.), CONCRETE)
    caps = [cap]
    for _, lo, hi, _ in result:
        if all(lo[i] < cap[2][i] and hi[i] > cap[1][i] for i in range(3)):
            caps = [part for piece in caps for part in subtract_box(piece, (lo, hi))]
    result.extend(caps)

    # The north garden repeats the built south garden, including the floor,
    # lawn, stair landings, treads and handrails. Its retaining rim meets the
    # north context grade. The south garden's interior portal is site-specific.
    garden_prefix = 'p2_aligned_garden_'
    for name, lo, hi, material in boxes:
        if not name.startswith(garden_prefix):
            continue
        part = name.removeprefix(garden_prefix)
        if part in ('floor', 'lawn', 'upper_landing', 'midlanding') or part.startswith('down_'):
            box('north_garden_' + part, (lo[0], mirror - hi[1], lo[2]),
                (hi[0], mirror - lo[1], hi[2]), material)

    def reflect(point):
        x, y, h = point
        return [x, mirror - y, h]

    stairs = [r for r in rails if r['name'].startswith(garden_prefix + 'down_')]
    rails.extend(dict(r, name=PREFIX + 'north_garden_' + r['name'].removeprefix(garden_prefix),
                      a=reflect(r['a']), b=reflect(r['b'])) for r in stairs)
    box('north_terrace_base', (west, north, base), (garden_x, north_edge, underside))
    box('north_podium', (facade, north - .16, z), (25., north, 4.))
    box('north_podium_return', (25., north - .16, z), (garden_x - .16, north, 2.75))
    box('north_retaining', (west, north_edge, base), (garden_east + .16, north_edge + .16, 2.75))
    box('north_garden_east', (garden_east, garden_south, base),
        (garden_east + .16, north_edge, 2.75))
    box('north_garden_south', (garden_x - .16, garden_south - .16, base),
        (garden_east + .16, garden_south, 2.75))
    box('north_garden_west', (garden_x - .16, garden_south, base),
        (garden_x, north, 2.75))
    # The north road bends over the west tip of the sunken terrace. Follow
    # its inside curb so the railing does not run across the sidewalk.
    start_y = curb_y(west)
    turn_y = north_edge + .23
    turn = curb_x(turn_y)
    curb_z = curb_start[2]
    bend_cap = prism(PREFIX + 'north_bend_cap',
                     [(west, start_y - .22, curb_z), (turn, turn_y - .22, curb_z),
                      (turn, turn_y, curb_z), (west, start_y, curb_z)], CONCRETE)
    add_mesh(bend_cap)
    guard('north_street_bend', (west + .06, curb_y(west + .06) - .15, curb_z),
          (turn, north_edge + .08, curb_z))
    rim = [(25., north - .08), (garden_x - .08, north - .08),
           (garden_x - .08, garden_south - .08), (garden_east + .08, garden_south - .08),
           (garden_east + .08, north_edge + .08), (turn, north_edge + .08)]
    for i, (a, b) in enumerate(zip(rim, rim[1:])):
        guard(f'north_garden_rim_{i}', (*a, 2.75), (*b, 2.75))
    landing = south_garden['down_landing']
    routes = south_garden['routes']
    ext['terrace_integration'] = dict(source=cfg['user_markup']['file'], slabs=slabs, holes=holes,
                                     driveway=[mouth, [mouth[0], descent, mouth[2]], portal_point],
                                     north_landing=[landing[0], north, landing[2], north_edge],
                                     north_garden=[garden_x, garden_south, garden_east, north_edge],
                                     north_routes=dict(down=[reflect(q) for q in routes['down']],
                                                       garden=[reflect(q) for q in routes['garden'][:-1]]))
    inputs = (CONFIG, PLAN, cfg['user_markup']['file'], 'tools/build_povo2_minus1_terrace.py',
              'tools/povo2_terrace_integration.py')
    ext['input_hashes'].update({p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in inputs})
    return result
