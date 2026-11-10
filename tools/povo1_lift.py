"""Build the reception lift in Povo 1's existing three-storey shaft."""

from .povo_interactions import brush_entity, with_outputs
from .povo_room_fitout import subtract_box


SCRIPT = 'maps/scripts/povo1_lift.vjs'
PREFIX = 'povo1_lift_'
MATERIAL = 'materials/trento/povo/campus/'
CAB_FLOOR = MATERIAL + 'floor_circulation.vmat'
TRIM = MATERIAL + 'metal_dark.vmat'
BUTTON = MATERIAL + 'sign_white.vmat'
BRUSH_MATERIALS = (CAB_FLOOR, TRIM, BUTTON)


def prepare(boxes, levels, spec):
    x0, y0, x1, y1 = spec['shaft']
    y = spec['opening_centre_north_metres']
    half_width = spec['opening_width_metres'] / 2
    stops = [round(level['floor_elevation_metres'] - 370, 3) for level in levels]
    cab = (x0 + .13, y0 + .13, x1 - .115, y1 - .13)
    sill = (cab[2] + .01, y - half_width, x1 + .16, y + half_width)
    # The old ladder ledges project into the cab's travel. Lower the existing
    # bottom slab only under the platform and bridge each original doorway.
    pit = ((cab[0] - .01, cab[1] - .01, stops[0] - .19),
           (cab[2] + .005, cab[3] + .01, stops[0] + .02))
    result = [part for box in boxes
              if not (box[0].startswith(('elevator_ladder_', 'elevator_first_ledge_'))
                      or box[0].endswith('_elevator_ledge')
                      or box[0].startswith('elevator_') and box[0].endswith('_call_button'))
              for part in subtract_box(box, pit)]
    for index, z in enumerate(stops):
        parts = [(f'elevator_sill_{index}', (*sill[:2], z - .14),
                  (*sill[2:], z), 'floor_circulation')]
        for _, lo, hi, _ in result:
            if hi[2] >= z - .001:
                parts = [piece for part in parts for piece in subtract_box(part, (lo, hi))]
        result.extend(parts)
    # The corridor wall steps back at each landing. Mount on its exposed face.
    call_y = y + half_width + .28
    call_faces = [max(hi[0] for _, lo, hi, _ in result
                      if lo[0] < x1 + .2 and x1 - 1e-6 <= hi[0] < x1 + .5
                      and lo[1] < call_y < hi[1] and lo[2] < z + 1.16 < hi[2])
                  for z in stops]
    levels[0]['elevator']['service'] = dict(cab=cab, sill=sill, stops=stops,
                                         call_faces=call_faces)
    return result


def insert(source, service):
    # Imported here because cs2_campus invokes this generator.
    from .cs2_campus import connection, project, sign_properties, world

    a, b, c, d = service['cab']
    x0, y0, _, y1 = service['sill']
    stops = service['stops']
    z0 = stops[0]
    cy = (b + d) / 2
    cx = (a + c) / 2
    car = PREFIX + 'car'
    controller = PREFIX + 'controller'

    def point(name, classname, origin, props=(), angles='0 0 0'):
        nonlocal source
        source = project._insert_point_entity(source, name, classname, world(origin),
                                               (('targetname', name), *props), angles=angles)

    def solid(name, classname, parts, props=(), pivot=None):
        nonlocal source
        source = brush_entity(source, name, classname, parts,
                              (('targetname', name), *props), pivot)

    def callbacks(name, *events):
        nonlocal source
        source = with_outputs(source, name, [
            connection(f'{name}-{output}', output, controller, 'RunScriptInput', value)
            for output, value in events
        ])

    source = project._ensure_map_asset_reference(source, SCRIPT)
    point(controller, 'point_script', (cx, cy, z0), (('cs_script', SCRIPT),))

    for i, z in enumerate(stops):
        next_stop = PREFIX + f'stop_{i+1}' if i + 1 < len(stops) else ''
        point(PREFIX + f'stop_{i}', 'path_track', (cx, cy, z),
              (('target', next_stop), ('orientationtype', '0')))

    solid(car, 'func_tracktrain', [
        ((a, b, z0 - .15), (c, d, z0), CAB_FLOOR),
        ((a, b, z0), (a + .065, d, z0 + 2.1), TRIM),
        ((a + .065, b, z0), (c, b + .055, z0 + 2.1), TRIM),
        ((a + .065, d - .055, z0), (c, d, z0 + 2.1), TRIM),
    ], (('target', PREFIX + 'stop_0'), ('startspeed', '55'), ('speed', '0'),
        ('height', '0'), ('wheels', '0'), ('orientationtype', '0'), ('spawnflags', '19'),
        ('dmg', '0')), (cx, cy, z0))
    callbacks(car, ('OnArrivedAtDestinationNode', 'Arrived'))

    def button(name, lo, hi, stop, parent=''):
        solid(name, 'func_button', [(lo, hi, BUTTON)],
              (('spawnflags', '1025'), ('wait', '.2'), ('parentname', parent)))
        callbacks(name, ('OnPressed', f'Request{stop}'))

    labels = ('-1', '0', '+1')
    for i, z in enumerate(stops):
        # The leaves slide in opposite directions into the original jambs.
        for leaf, (south, north, yaw) in enumerate(((y0, cy - .003, 0), (cy + .003, y1, 180))):
            gate = PREFIX + f'gate_{i}_{leaf}'
            solid(gate, 'func_door', [
                ((x0 + .025, south, z + .015), (x0 + .085, north, z + 2.19), TRIM),
            ], (('movedir', f'0 {yaw} 0'), ('speed', '48'), ('lip', '-1'), ('wait', '-1'),
                ('spawnflags', '0'), ('forceclosed', '0'), ('dmg', '0')))
            callbacks(gate, ('OnFullyClosed', f'Closed{i}{leaf}'),
                      ('OnFullyOpen', f'Opened{i}{leaf}'), ('OnBlockedClosing', f'Blocked{i}'))

        face = service['call_faces'][i]
        button(PREFIX + f'call_{i}', (face, y1 + .18, z + 1.05),
               (face + .055, y1 + .38, z + 1.27), i)
        point(PREFIX + f'call_label_{i}', 'point_worldtext', (face + .06, y1 + .28, z + 1.42),
              sign_properties('CHIAMA'), '0 180 90')
        panel_y = cy + (i - 1) * .31
        button(PREFIX + f'panel_{i}', (a + .065, panel_y - .1, z0 + 1.05),
               (a + .11, panel_y + .1, z0 + 1.27), i, car)
        point(PREFIX + f'panel_label_{i}', 'point_worldtext', (a + .075, panel_y, z0 + 1.42),
              (*sign_properties(labels[i]), ('parentname', car)), '0 180 90')
    return source
