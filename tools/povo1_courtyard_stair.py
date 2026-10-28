"""Povo 1 courtyard: steel emergency stair, open floor-1 terraces and planters.

Fire plans 10/19/22 draw one stadium-shaped emergency stair at the courtyard's
south end. Its landings stack at one plan point: outside A107 on -1, the coffee
room on 0 and the short ICT-panel corridor on 1 (photos 26-28). Photos 5-8 and
23-25 show an exposed galvanised frame with cross bracing and grating treads.
On floor 1 the courtyard's long sides are two separate open-air paved terraces
behind glass, with railings over the court and no doors (photos 23, 24, 30).
Planters with small trees stand on the -1 courtyard paving (photos 5-8).

Dimensions are scaled from the fire plans, not photogrammetry: two 12-riser
flights per storey, 1.5 m flights, 3.3 m treads run plus landings.
"""
import math

try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing

# Stair frame measured on fire plan 19: on the courtyard's centre line, 3.1 m
# wide and about 8.3 m long. The doors share one plan point inside the
# floor-1 ICT corridor (E1.02-4.05).
WEST, CENTRE, EAST = -.85, .7, 2.25
DOOR = (1.1, 2.2)
TREAD, FLIGHT_TREADS, NORTH_LANDING = .30, 11, 1.9
LANDING_EDGE = -74.1  # north edge of the stacked south landings
GRATING = 'floor_grating'
# (x, y) planter centres on the -1 court, clear of the stair and both glazed sides.
PLANTERS = ((-3.6, -70.5), (4.9, -64.0), (-3.6, -56.5), (4.9, -50.5))
PLANTER_SIZE = 1.4
WEST_TERRACE, EAST_TERRACE = (-10.73, -6.39), (7.99, 12.6)
# The Povo 1 lift shaft rises through the east terrace; it stays enclosed.
LIFT_SPAN = (-69.3, -67.0)


def _clear(boxes, hole, materials=('wall', 'courtyard_wall', 'window_glass', 'window_frame')):
    return [p for b in boxes for p in (subtract_box(b, hole) if b[3] in materials else [b])]


def stair(boxes, levels, origin):
    result = list(boxes); rails = []
    def add(name, lo, hi, mat='metal_dark'):
        result.append(('p1_courtyard_stair_'+name, tuple(lo), tuple(hi), mat))
    zs = [l['floor_elevation_metres']-origin[2] for l in levels]
    walls = [l['voids_local_metres'][0][1] for l in levels]
    north = LANDING_EDGE+FLIGHT_TREADS*TREAD
    cap = north+NORTH_LANDING
    # A door in the courtyard wall at the same plan point on every floor.
    for i, (z, wall) in enumerate(zip(zs, walls)):
        result = _clear(result, ((DOOR[0], wall-.35, z-.01), (DOOR[1], wall+.35, z+2.2)))
        add(f'{i}_finish_door_jamb_west', (DOOR[0]-.06, wall-.12, z), (DOOR[0], wall+.12, z+2.26))
        add(f'{i}_finish_door_jamb_east', (DOOR[1], wall-.12, z), (DOOR[1]+.06, wall+.12, z+2.26))
        add(f'{i}_finish_door_head', (DOOR[0]-.06, wall-.12, z+2.2), (DOOR[1]+.06, wall+.12, z+2.26))
        if i:  # -1 starts on the courtyard paving itself
            add(f'{i}_landing', (WEST, wall, z-.1), (EAST, LANDING_EDGE, z), GRATING)
            railing(add, rails, f'{i}_landing_west', (WEST, wall, z), (WEST, LANDING_EDGE, z))
            railing(add, rails, f'{i}_landing_east', (EAST, wall, z), (EAST, LANDING_EDGE, z))
    # A grating base plate at the foot, flush with floor -1 (photo 5).
    add('base', (WEST, LANDING_EDGE-1.2, zs[0]-.02), (EAST, LANDING_EDGE, zs[0]), GRATING)
    segments = []
    for floor, (lo, hi) in enumerate(zip(zs, zs[1:])):
        rise = (hi-lo)/(2*FLIGHT_TREADS+2); mid = lo+(FLIGHT_TREADS+1)*rise
        up, down = (CENTRE+.05, EAST), (WEST, CENTRE-.05)
        for i in range(FLIGHT_TREADS):
            top = lo+(i+1)*rise
            add(f'{floor}_up_{i}', (up[0], LANDING_EDGE+i*TREAD, top-.05),
                (up[1], LANDING_EDGE+(i+1)*TREAD, top), GRATING)
            top = mid+(i+1)*rise
            add(f'{floor}_down_{i}', (down[0], north-(i+1)*TREAD, top-.05),
                (down[1], north-i*TREAD, top), GRATING)
        add(f'{floor}_turn', (WEST, north, mid-.1), (EAST, cap, mid), GRATING)
        railing(add, rails, f'{floor}_up_outer', (EAST, LANDING_EDGE, lo), (EAST, north, mid))
        railing(add, rails, f'{floor}_up_well', (CENTRE, LANDING_EDGE, lo), (CENTRE, north, mid))
        railing(add, rails, f'{floor}_turn_east', (EAST, north, mid), (EAST, cap, mid))
        railing(add, rails, f'{floor}_turn_end', (EAST, cap, mid), (WEST, cap, mid))
        railing(add, rails, f'{floor}_turn_west', (WEST, cap, mid), (WEST, north, mid))
        railing(add, rails, f'{floor}_down_outer', (WEST, north, mid), (WEST, LANDING_EDGE, hi))
        railing(add, rails, f'{floor}_down_well', (CENTRE, north, mid), (CENTRE, LANDING_EDGE, hi))
        upper = (CENTRE+WEST)/2; lower = (CENTRE+EAST)/2; door = sum(DOOR)/2
        path = [[door, walls[floor]-.6, lo], [door, LANDING_EDGE-.5, lo], [lower, LANDING_EDGE-.5, lo],
                [lower, LANDING_EDGE-.3, lo],
                *[[lower, LANDING_EDGE+(i+.5)*TREAD, lo+(i+1)*rise] for i in range(FLIGHT_TREADS)],
                [lower, north+NORTH_LANDING/2, mid], [upper, north+NORTH_LANDING/2, mid],
                *[[upper, north-(i+.5)*TREAD, mid+(i+1)*rise] for i in range(FLIGHT_TREADS)],
                [upper, LANDING_EDGE-.3, hi], [upper, LANDING_EDGE-.5, hi], [door, LANDING_EDGE-.5, hi],
                [door, walls[floor+1]-.6, hi]]
        segments.append(dict(path=path, from_floor=floor-1, to_floor=floor, flights=2,
                             risers=2*FLIGHT_TREADS+2, rise_metres=rise, flight_width_metres=CENTRE-.05-WEST,
                             bottom=path[0], top=path[-1], mid=[CENTRE, north+NORTH_LANDING/2, mid]))
    # Nothing climbs past the top landing over the last up flight.
    railing(add, rails, 'top_edge', (CENTRE, LANDING_EDGE, zs[-1]), (EAST, LANDING_EDGE, zs[-1]))
    top = zs[-1]+1.1
    for x in (WEST-.1, EAST+.1):
        for y in (LANDING_EDGE-.05, cap+.05):
            add(f'column_{x:.2f}_{y:.2f}', (x-.06, y-.06, zs[0]), (x+.06, y+.06, top))
        # Galvanised cross bracing on both long faces; visual only.
        face = x+(-.06 if x < CENTRE else .06)
        for storey, (lo, hi) in enumerate(zip(zs, zs[1:])):
            for diagonal, (y0, y1) in enumerate(((LANDING_EDGE, cap), (cap, LANDING_EDGE))):
                steps = math.ceil(math.hypot(y1-y0, hi-lo)/.1)
                for k in range(steps):
                    t = (k+.5)/steps; y = y0+(y1-y0)*t; z = lo+(hi-lo)*t
                    add(f'{storey}_{x:.2f}_{diagonal}_finish_brace_{k}', (face-.035, y-.05, z-.05), (face+.035, y+.05, z+.05))
    return result, dict(source_photos=[5, 6, 7, 8, 10, 19, 22, 23, 24, 25, 26, 27, 28],
                        floors=[-1, 0, 1], segments=segments, rails=rails,
                        bounds=[WEST-.2, walls[0], EAST+.2, cap+.11], door=list(DOOR),
                        status='Emergency switchback stair from the fire plans; landings stack outside A107, '
                               'the coffee room and the ICT corridor; metric fit provisional')


def _glass_wall(add, prefix, start, end, z, axis):
    """Full-height breakable glazing in 2.4 m bays along one axis."""
    other = 1-axis
    span = end[axis]-start[axis]; bays = max(1, math.ceil(abs(span)/2.4))
    def box(name, a, b, z0, z1, mat, thick=.05):
        lo = [0, 0, z0]; hi = [0, 0, z1]
        lo[axis], hi[axis] = min(a, b), max(a, b)
        lo[other], hi[other] = start[other]-thick, start[other]+thick
        add(prefix+'_'+name, lo, hi, mat)
    box('sill', start[axis], end[axis], z, z+.1, 'wall', .09)
    box('head', start[axis], end[axis], z+3.05, z+3.35, 'wall', .09)
    for i in range(bays):
        a = start[axis]+span*i/bays; b = start[axis]+span*(i+1)/bays
        box(f'glass_{i}', a, b, z+.1, z+3.05, 'window_glass')
    for i in range(bays+1):
        a = start[axis]+span*i/bays
        box(f'frame_{i}', a-.025, a+.025, z+.1, z+3.05, 'window_frame', .07)


def terraces(boxes, levels, origin, rails):
    """Floor-1 courtyard bands become open, paved terraces behind glass."""
    upper = levels[-1]; z = upper['floor_elevation_metres']-origin[2]
    x0, y0, x1, y1 = upper['voids_local_metres'][0]
    result = [b for b in boxes if not (b[0].startswith(('academic_upper_west_terrace_finish_fixture',
                                                         'academic_upper_east_terrace_finish_fixture')))]
    for (a, b) in (WEST_TERRACE, EAST_TERRACE):
        # Open sky: no ceiling over either terrace.
        result = _clear(result, ((a, y0, z+3.2), (b, y1, z+3.4)), ('ceiling_panel',))
    # The long courtyard sides lose their glazing; railings guard the drop.
    for x in (x0, x1):
        result = _clear(result, ((x-.12, y0+.09, z-.01), (x+.12, y1-.09, z+3.4)))
    result = [(n, lo, hi, 'floor_terrace') if n.startswith(('academic_upper_west_terrace_0',
              'academic_upper_east_terrace_0')) else (n, lo, hi, m) for n, lo, hi, m in result]
    def add(name, lo, hi, mat='metal_dark'):
        result.append(('p1_courtyard_terrace_'+name, tuple(lo), tuple(hi), mat))
    for side, x, inward in (('west', x0, -1), ('east', x1, 1)):
        edge = x+inward*.1
        add(side+'_upstand', (min(x, x+inward*.2), y0+.09, z), (max(x, x+inward*.2), y1-.09, z+.25), 'wall')
        railing(add, rails, side+'_edge', (edge, y0+.09, z+.25), (edge, y1-.09, z+.25))
    # Glass towards each corridor and across both terrace ends; no doors.
    (wa, wb), (ea, eb) = WEST_TERRACE, EAST_TERRACE
    _glass_wall(add, 'west_corridor', (wa, y0), (wa, y1), z, 1)
    _glass_wall(add, 'east_corridor_south', (eb, y0), (eb, LIFT_SPAN[0]), z, 1)
    _glass_wall(add, 'east_corridor_north', (eb, LIFT_SPAN[1]), (eb, y1), z, 1)
    for i, y in enumerate(LIFT_SPAN):  # close the strip between shaft and glazing
        add(f'east_lift_closer_{i}', (12.45, y-.05, z), (eb+.05, y+.05, z+3.35), 'wall')
    for side, (a, b) in (('west', (wa+.05, wb)), ('east', (ea, eb-.05))):
        _glass_wall(add, side+'_south_end', (a, y0), (b, y0), z, 0)
        _glass_wall(add, side+'_north_end', (a, y1), (b, y1), z, 0)
    # Benches against the glazing (photos 23, 30).
    for side, xs, ys in (('west', (wa+.15, wa+.6), (-66.0, -56.0)), ('east', (eb-.6, eb-.15), (-60.0, -52.0))):
        for i, y in enumerate(ys):
            add(f'{side}_bench_{i}_seat', (xs[0], y, z+.43), (xs[1], y+1.6, z+.48), 'seat_wood')
            for j, yy in enumerate((y+.1, y+1.42)):
                add(f'{side}_bench_{i}_leg_{j}', (xs[0]+.05, yy, z), (xs[1]-.05, yy+.08, z+.43))
    return result, dict(west=list(WEST_TERRACE), east=list(EAST_TERRACE), y=[y0, y1], z=z,
                        status='Open-air paved terraces; glazed towards the corridors, no doors')


def planters(boxes, levels, origin):
    """Concrete planters with small trees on the -1 courtyard paving."""
    result = list(boxes)
    z = levels[0]['floor_elevation_metres']-origin[2]; h = PLANTER_SIZE/2
    def add(name, lo, hi, mat):
        result.append(('p1_courtyard_planter_'+name, tuple(lo), tuple(hi), mat))
    for i, (x, y) in enumerate(PLANTERS):
        for side, lo, hi in (('south', (x-h, y-h), (x+h, y-h+.12)), ('north', (x-h, y+h-.12), (x+h, y+h)),
                             ('west', (x-h, y-h+.12), (x-h+.12, y+h-.12)), ('east', (x+h-.12, y-h+.12), (x+h, y+h-.12))):
            add(f'{i}_curb_{side}', (*lo, z), (*hi, z+.18), 'exterior_concrete')
        add(f'{i}_soil', (x-h+.12, y-h+.12, z), (x+h-.12, y+h-.12, z+.12), 'floor_yard_grass')
        add(f'{i}_trunk', (x-.07, y-.07, z+.12), (x+.07, y+.07, z+2.0), 'exterior_trunk')
        add(f'{i}_canopy_low', (x-.8, y-.8, z+1.7), (x+.8, y+.8, z+2.5), 'exterior_tree')
        add(f'{i}_canopy_top', (x-.55, y-.55, z+2.5), (x+.55, y+.55, z+3.1), 'exterior_tree')
    return result, [dict(centre=[x, y], size=PLANTER_SIZE, z=z) for x, y in PLANTERS]


# Coffee area from 28 October photos 2-5: water dispenser, four snack/drink
# machines and a green one along the side wall; four recycling bins under the
# courtyard window; two light-wood tables. Machine labels are not reproduced.
VENDING = ('office_dark',)*5+('p2_accent_green',)
BINS = ('canteen_orange', 'door_closed', 'canteen_blue', 'p2_accent_green')


def coffee_room(boxes, levels, origin):
    """Fit out the floor-0 coffee area behind the courtyard stair door."""
    level = levels[1]; z = level['floor_elevation_metres']-origin[2]
    room = next((r for r in level['rooms'] if r['id'] == 'f_south_coffee'), None)
    if room is None:
        return boxes
    a, b, c, d = room['footprint_local_metres']
    result = list(boxes)
    def add(name, lo, hi, mat):
        result.append(('academic_first_f_south_coffee_'+name, tuple(lo), tuple(hi), mat))
    # Pillar left of the stair door; bins under the window beside it; machines
    # on the east wall, set back from the window so the door stays clear.
    add('pillar', (DOOR[0]-.45, d-.5, z), (DOOR[0]-.07, d, z+3.3), 'wall')
    for i, mat in enumerate(BINS):
        x = DOOR[0]-.55-i*.33
        add(f'recycling_bin_{i}', (x-.3, d-.45, z), (x, d-.05, z+.8), mat)
    y = d-1.5
    for i, mat in enumerate(VENDING):
        width = .45 if i == 0 else .75
        add(f'vending_{i}', (c-.85, y-width, z), (c-.05, y, z+1.85), mat)
        add(f'vending_{i}_finish_display', (c-.87, y-width+.08, z+.9), (c-.85, y-.08, z+1.75), 'office_screen')
        y -= width+.03
    for i, y in enumerate((b+4.4, b+1.6)):
        lo, hi = (a+.25, y), (a+1.45, y+1.6)
        add(f'table_{i}_top', (lo[0], lo[1], z+.71), (hi[0], hi[1], z+.75), 'floor_wood')
        for j, (x, yy) in enumerate(((lo[0]+.05, lo[1]+.05), (hi[0]-.09, lo[1]+.05),
                                     (lo[0]+.05, hi[1]-.09), (hi[0]-.09, hi[1]-.09))):
            add(f'table_{i}_leg_{j}', (x, yy, z), (x+.04, yy+.04, z+.71), 'window_frame')
    add('extinguisher', (a, b+.6, z+.15), (a+.12, b+.75, z+.7), 'door_pushbar')
    return result


def locale_office(boxes, levels, origin):
    """The Locale beside the coffee area: a semi-empty office, two tables on its long side."""
    level = levels[1]; z = level['floor_elevation_metres']-origin[2]
    room = next((r for r in level['rooms'] if r['id'] == 'f_south_centre'), None)
    if room is None:
        return boxes
    a, b, c, d = room['footprint_local_metres']
    result = list(boxes)
    for i, y in enumerate(((b+d)/2+.2, (b+d)/2-1.8)):
        lo, hi = (a+.15, y), (a+.95, y+1.6)
        result.append((f'academic_first_f_south_centre_table_{i}_top', (lo[0], lo[1], z+.71), (hi[0], hi[1], z+.75), 'floor_wood'))
        for j, (x, yy) in enumerate(((lo[0]+.05, lo[1]+.05), (hi[0]-.09, lo[1]+.05),
                                     (lo[0]+.05, hi[1]-.09), (hi[0]-.09, hi[1]-.09))):
            result.append((f'academic_first_f_south_centre_table_{i}_leg_{j}', (x, yy, z), (x+.04, yy+.04, z+.71), 'window_frame'))
    return result


def extend(boxes, levels, origin):
    result, metadata = stair(boxes, levels, origin)
    result, metadata['terraces'] = terraces(result, levels, origin, metadata['rails'])
    result, metadata['planters'] = planters(result, levels, origin)
    result = coffee_room(result, levels, origin)
    result = locale_office(result, levels, origin)
    levels[0]['courtyard_stair'] = metadata
    return result, metadata
