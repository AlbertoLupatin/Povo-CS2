#!/usr/bin/env python3
"""Side-by-side section of a Povo corridor at candidate gameplay scales.

The CS2 player stays fixed in game units; the building is scaled. This shows
how doors, corridors and storeys read around the player at each factor.
Real dimensions marked (est.) are placeholders until measured on site.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parents[1] / 'out'
INCH = 39.37007874  # Hammer units per real metre at 1:1
# CS2 player (Hammer units): hull 32 wide, 72 standing, eye 64, step 18.
PLAYER_W, PLAYER_H, EYE, STEP = 32, 72, 64, 18
REAL = dict(corridor_w=2.8, door_w=1.0, door_h=2.2, ceiling=3.0, floor_to_floor=3.6,
            riser=0.17, tread=0.30)
SCALES = (1.0, 1.25, 1.5)


def panel(ax, s):
    u = INCH * s
    cw, dw, dh = REAL['corridor_w'] * u, REAL['door_w'] * u, REAL['door_h'] * u
    ceil, ftf = REAL['ceiling'] * u, REAL['floor_to_floor'] * u
    wall = .2 * u
    ax.add_patch(Rectangle((-wall, -.3 * u), cw + 2 * wall + 120, .3 * u, color='#8a8a8a'))
    ax.add_patch(Rectangle((-wall, ftf - .3 * u), cw + 2 * wall + 120, .3 * u, color='#8a8a8a'))
    ax.add_patch(Rectangle((-wall, 0), wall, ceil, color='#c9c8bd'))
    ax.add_patch(Rectangle((cw, 0), wall, ceil, color='#c9c8bd'))
    ax.add_patch(Rectangle((0, ceil), cw, ftf - .3 * u - ceil, color='#e4e4dc', alpha=.6))
    # Door in the right wall, drawn as an elevation inset beside the section.
    dx = cw + wall + 20
    ax.add_patch(Rectangle((dx, 0), dw, dh, fill=False, ec='#6a4430', lw=2))
    # Stair profile: three steps.
    sx = dx + dw + 20
    for i in range(3):
        ax.add_patch(Rectangle((sx + i * REAL['tread'] * u, 0), REAL['tread'] * u * (3 - i),
                               REAL['riser'] * u, color='#9b2b26', alpha=.85))
    for x in (cw * .5 - PLAYER_W / 2, dx + dw / 2 - PLAYER_W / 2):
        ax.add_patch(Rectangle((x, 0), PLAYER_W, PLAYER_H, color='#e09a2c', alpha=.85))
        ax.plot([x, x + PLAYER_W], [EYE, EYE], color='k', lw=1)
    ax.set_title(f'scale {s:.2f}  (1 m = {u:.1f} u)', fontsize=11)
    notes = [f'corridor {cw:.0f} u = {cw / PLAYER_W:.1f} players wide',
             f'door {dw:.0f} x {dh:.0f} u ({dw / PLAYER_W:.1f} players)',
             f'storey {ftf:.0f} u, riser {REAL["riser"] * u:.1f} u (max step {STEP})']
    ax.text(0, -60, '\n'.join(notes), va='top', fontsize=9)
    ax.set_xlim(-30, 480)
    ax.set_ylim(-150, 330)
    ax.set_aspect('equal')
    ax.axis('off')


def main():
    OUT.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, len(SCALES), figsize=(16, 6.2))
    for ax, s in zip(axes, SCALES):
        panel(ax, s)
    fig.suptitle('Povo corridor section vs CS2 player (orange, eye line black). '
                 'Real dims are estimates until measured: corridor 2.8 m, door 1.0 x 2.2 m, '
                 'ceiling 3.0 m, storey 3.6 m', fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / 'scale_study.png', dpi=110)


if __name__ == '__main__':
    main()
