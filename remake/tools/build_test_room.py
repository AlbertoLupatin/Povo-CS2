#!/usr/bin/env python3
"""Generate povo_scale_test.vmap: one Povo corridor module at three scales.

Each module uses the same real dimensions (estimates until measured on site):
corridor 2.8 m wide with a 3.0 m ceiling and window band, a 1.0 x 2.2 m door
and a 1.8 m double door into a 12 x 7 m classroom with desk rows, and a
two-flight stair (11 risers each, 3.6 m storey) up to the corridor roof.
A 64-unit CS crate stands in each corridor as a fixed in-game reference.

Geometry is native Hammer meshes, so the map opens and edits in Hammer.
"""

import argparse

from vmap_build import MapBuilder
import vmap_mesh as vm

MAP = 'povo_scale_test'
SKY = 'materials/skybox/sky_overcast_01.vmat'
INCH = 39.37007874
SCALES = (1.0, 1.25, 1.5)
GRID = 'materials/dev/graygrid.vmat'
# Tints make floors, walls, stairs and furniture readable on the grid texture.
TINT = dict(floor=(190, 190, 185), wall=(235, 232, 222), ceiling=(250, 250, 250),
            stair=(176, 70, 60), desk=(150, 115, 80), crate=(120, 160, 90))


def module_solids(u, x0, y0):
    """Solids of one module in Hammer units; u = units per real metre."""
    out = {k: [] for k in TINT}

    def b(kind, lo, hi):
        out[kind].append(vm.box(tuple(x0 + lo[0] * u if i == 0 else y0 + lo[1] * u if i == 1 else lo[2] * u
                                      for i in range(3)),
                                tuple(x0 + hi[0] * u if i == 0 else y0 + hi[1] * u if i == 1 else hi[2] * u
                                      for i in range(3)), GRID))
    # Floor slab under corridor, classroom and stair hall.
    b('floor', (-.2, -.2, -.3), (30.2, 10.2, 0))
    # Corridor south wall: window band 1.0-2.6 m between piers every 6 m.
    b('wall', (-.2, -.2, 0), (24, 0, 1.0))
    b('wall', (-.2, -.2, 2.6), (24, 0, 3.0))
    for x in (-.2, 6, 12, 18, 23.8):
        b('wall', (x, -.2, 1.0), (x + .2, 0, 2.6))
    b('wall', (-.2, -.2, 0), (0, 3.0, 3.0))                  # west end
    # North wall with a 1.0 m door (x 4-5) and a 1.8 m double door (x 9-10.8).
    for a, c in ((0, 4), (5, 9), (10.8, 24)):
        b('wall', (a, 2.8, 0), (c, 3.0, 3.0))
    for a, c in ((4, 5), (9, 10.8)):
        b('wall', (a, 2.8, 2.2), (c, 3.0, 3.0))
    # Classroom x 2-14, y 3-10, window band on the north wall.
    b('wall', (1.8, 3.0, 0), (2.0, 10.2, 3.0))
    b('wall', (14, 3.0, 0), (14.2, 10.2, 3.0))
    b('wall', (2.0, 10, 0), (14, 10.2, 1.0))
    b('wall', (2.0, 10, 2.6), (14, 10.2, 3.0))
    for x in (2.0, 7.9, 13.8):
        b('wall', (x, 10, 1.0), (x + .2, 10.2, 2.6))
    # Ceiling slab (3.0-3.6) over corridor and classroom; walkable roof above.
    b('ceiling', (-.2, -.2, 3.0), (24, 3.0, 3.6))
    b('ceiling', (1.8, 3.0, 3.0), (14.2, 10.2, 3.6))
    # Desk rows facing west, 1.15 m pitch, central aisle at y 6-7.
    for k in range(7):
        x = 5.0 + k * 1.15
        for ya, yb in ((3.6, 6.0), (7.0, 9.4)):
            b('desk', (x, ya, 0), (x + .6, yb, .75))
            b('desk', (x + .7, ya, 0), (x + .95, yb, .45))
    # Stair hall x 24-30: open to the sky, two flights of 11 risers to 3.6 m.
    b('wall', (24, -.2, 0), (30.2, 0, 7))
    b('wall', (24, 3.0, 0), (30.2, 3.2, 7))
    b('wall', (30, 0, 0), (30.2, 3.0, 7))
    risers, tread = 11, .30
    rise = 1.8 / risers
    for i in range(risers):
        b('stair', (24.3 + i * tread, 0, 0), (24.3 + (i + 1) * tread, 1.5, (i + 1) * rise))
        b('stair', (27.6 - (i + 1) * tread, 1.5, 0), (27.6 - i * tread, 3.0, 1.8 + (i + 1) * rise))
    b('stair', (27.6, 0, 0), (30, 3.0, 1.8))                # landing
    b('ceiling', (24, 1.5, 3.0), (24.3, 3.0, 3.6))           # upper arrival
    # Fixed 64-unit CS crate (not scaled) in the corridor.
    cx, cy = x0 + 14 * u, y0 + .3 * u
    out['crate'].append(vm.box((cx, cy, 0), (cx + 64, cy + 64, 64), GRID))
    return out


def build():
    m = MapBuilder(MAP)
    y0 = 0.0
    spawn_slot = {}
    for s in SCALES:
        u = INCH * s
        for kind, solids in module_solids(u, 0.0, y0).items():
            m.mesh(solids, TINT[kind])
        m.entity('point_worldtext', dict(
            message=f'SCALE {s:.2f}   1 m = {u:.1f} u', enabled=1, fullbright=1, color='255 255 255 255',
            world_units_per_pixel=.25 * s, font_size=48, font_name='Arial Black',
            justify_horizontal=0, justify_vertical=0, reorient_mode=0),
            (.05 * u, y0 + 1.4 * u, 2.6 * u))
        # Ceiling lights: four along the corridor, two in the classroom.
        lights = [(6 * (k + .5), 1.4) for k in range(4)] + [(5, 6.5), (11, 6.5)]
        for lx, ly in lights:
            m.entity('light_omni2', dict(colortemperature=4500, brightness_lumens=round(900 * s * s),
                                         range=round(7 * u), castshadows=1, showlight=0),
                     (lx * u, y0 + ly * u, 2.85 * u))
        spawn_slot[s] = (1.0 * u, y0 + 1.4 * u, 8)
        y0 += 10.6 * u + 512
    for team, s in (('info_player_terrorist', 1.25), ('info_player_counterterrorist', 1.0)):
        x, y, z = spawn_slot[s]
        for k in range(2):
            m.entity(team, dict(enabled=1, priority=0), (x + k * 48, y - 24 + k * 48, z))
    # The template's procedural sky material is not shipped; use a stock one.
    m.set_kept('env_sky', dict(skyname=SKY))
    return m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-compile', action='store_true')
    args = parser.parse_args()
    raise SystemExit(build().deploy(not args.no_compile))
