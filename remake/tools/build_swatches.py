#!/usr/bin/env python3
"""Generate povo_swatches.vmap: stock-material candidates side by side in daylight.

Each candidate is an L of a wall and a floor patch, eight per row, one row per group,
so in-engine screenshots can be compared with the reference photos.
Writes build/maps/swatch_views.json (one view per row) and build/maps/swatches.json (labels).
"""

import argparse
import json

from vmap_build import MapBuilder, ROOT, CONFIG
import vmap_mesh as vm

MAP = 'povo_swatches'
U = CONFIG['hammer_units_per_metre_real'] * CONFIG['gameplay_scale']
GROUPS = {
    'stone': ['materials/cs_italy/stone/italy_stone_cladding_01.vmat',
              'materials/de_mirage/stone/stone_cladding_01a.vmat',
              'materials/de_overpass/construction/stone_cladding_1.vmat',
              'materials/anubis/sandstone01.vmat',
              'materials/anubis/sandstone_wall01.vmat',
              'materials/cs_italy/hpe_plaster_tan_wall.vmat',
              'materials/de_cache/concrete/ch2_concrete_siding_001.vmat',
              'materials/de_mirage/marble/marble_01.vmat'],
    'wall': ['materials/ar_baggage/baggage_plaster_wall_smooth_01.vmat',
             'materials/concrete/hr_c/hr_concrete_ceiling_painted_001.vmat',
             'materials/de_overpass/concrete/concrete_1_painted_white_hs.vmat',
             'materials/cs_italy/plasterwall04.vmat',
             'materials/metal/hr_metal/hr_metal_panel_001.vmat',
             'materials/metal/hr_metal/hr_metal_panel_002.vmat',
             'materials/de_train/hr_train_s2/metal/hrts2_metal_panelling_01_paint.vmat',
             'materials/de_mirage/metal/metal_siding_hs01a.vmat'],
    'floor': ['materials/de_cache/floor/ch2_floor_vinyl_01.vmat',
              'materials/shared_base/tile/floor_tile_vinyl_001.vmat',
              'materials/concrete/hr_c/hr_concrete_floor_001.vmat',
              'materials/de_train/hr_train_s2/concrete/hrts2_concrete_floor_colored_epoxy_01.vmat',
              'materials/de_inferno/tile/inferno_tile_floor_04b_red.vmat',
              'materials/de_inferno/wood/inferno_wood_floor_01_varnished.vmat',
              'materials/de_train/hr_train_s2/wood/hrts2_wood_floor_boards_01.vmat',
              'materials/ar_baggage/baggage_rubber_floor_dots_01.vmat'],
    'misc': ['materials/glass/hr_g/hr_glass_window_frame_001.vmat',
             'materials/ar_baggage/baggage_glass_clear_01.vmat',
             'materials/ar_baggage/baggage_glass_frosted_01.vmat',
             'materials/shared_base/glass/building_windows_01a.vmat',
             'materials/ceiling/hr_c/hr_ceiling_tile_001_color.vmat',
             'materials/de_overpass/buildings/office_ceiling_tiles_1.vmat',
             'materials/de_cache/concrete/ch2_concrete_paving_001.vmat',
             'materials/metal/hr_metal/hr_metal_grating_001.vmat'],
}
WIDTH, GAP = 3.0, 1.0


def build():
    m = MapBuilder(MAP)
    views, labels = [], {}
    for row, (group, mats) in enumerate(GROUPS.items()):
        y = row * 12.0
        for i, mat in enumerate(mats):
            x = i * (WIDTH + GAP)
            m.mesh([vm.box((x * U, (y + 3) * U, 0), ((x + WIDTH) * U, (y + 3.3) * U, 3 * U), mat),
                    vm.box((x * U, y * U, -.2 * U), ((x + WIDTH) * U, (y + 3) * U, 0), mat)])
        labels[group] = mats
        span = len(mats) * (WIDTH + GAP) - GAP
        views.append(dict(name=f'swatch_{group}', pos=[round(span / 2 * U), round((y - 9) * U), round(1.2 * U)],
                          ang=[8, 90, 0]))
    ground = 'materials/dev/graygrid.vmat'
    m.mesh([vm.box((-10 * U, -15 * U, -1 * U), (45 * U, 50 * U, -.2 * U), ground)])
    for k, team in enumerate(('info_player_terrorist', 'info_player_counterterrorist')):
        m.entity(team, dict(enabled=1, priority=0), (-5 * U, (k * 3 - 8) * U, 0))
    m.set_kept('env_sky', dict(skyname='materials/skybox/sky_overcast_01.vmat'))
    (ROOT / 'build/maps/swatch_views.json').write_text(json.dumps(views, indent=1))
    (ROOT / 'build/maps/swatches.json').write_text(json.dumps(labels, indent=1))
    return m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-compile', action='store_true')
    args = parser.parse_args()
    raise SystemExit(build().deploy(not args.no_compile, 0, vis=False))
