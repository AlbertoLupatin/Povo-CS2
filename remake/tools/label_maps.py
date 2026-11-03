#!/usr/bin/env python3
"""Labelled maps for feedback: one per building and floor, plus the site.

Drawn from the specs exactly as the generator builds them, over the rectified plans:
numbered rooms (reading order, north to south and west to east), room doors (red),
entrances in the facade (green), glazed sides (blue), stair cores and lifts,
and a 5 m grid with letters along x and numbers along y, so a spot can be named
"C7" and a room "P1 -1 #07".

Output: data/labeled_pictures/<BUILDING>/MAPS/*.png with rooms.md, and
build/maps/room_index.json (map key -> room id -> spec, level, index) to read notes back.
"""

import json
import string
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

import east_block
import povo1
import povo2
from vmap_build import ROOT, CONFIG

Image.MAX_IMAGE_PIXELS = None
OUT = ROOT / 'data/labeled_pictures'
PX = 25                                   # pixels per metre on building maps
CELL = 5.0                                # grid cell, metres
TODAY = time.strftime('%Y-%m-%d')
KIND = dict(classroom='#f6e27a', study='#bfe3a0', office='#a9cbf0', lab='#cdb4ec', wc='#9fe0e0',
            hall='#f7c08a', service='#c8c8c8', terrace='#e2e2e2', stair='#f08080', lift='#909090',
            void='#ffffff')
PLANS = {('Povo 1', -1): 'povo1_floor-1', ('Povo 1', 0): 'povo1_floor0', ('Povo 1', 1): 'povo1_floor1',
         ('Povo 2', -1): 'povo2_floor-1', ('Povo 2', 0): 'povo2_floor0'}


def lv(level):
    """Floor as written on the plans: -1, 0, +1."""
    return f'{level:+d}' if level else '0'


def col(i):
    """Grid column letters: A..Z, AA.."""
    letters = string.ascii_uppercase
    return letters[i] if i < 26 else letters[i // 26 - 1] + letters[i % 26]


def underlay(ax, plan, origin):
    """Rectified plan (EPSG:25832 world file) faded under the map, in the spec frame."""
    path = ROOT / 'data/plans' / f'{plan}.png'
    a, _, _, e, c, f = [float(v) for v in path.with_suffix('.pgw').read_text().split()]
    im = Image.open(path).convert('L')
    w, h = im.size
    left, top = c - a / 2 - origin[0], f - e / 2 - origin[1]
    ax.imshow(im, cmap='gray', alpha=.35, extent=(left, left + w * a, top + h * e, top), zorder=0,
              interpolation='bilinear')


def grid(ax, x0, y0, x1, y1, cell=CELL, origin=(0.0, 0.0)):
    """Lines every cell; letters along x, numbers along y, counted from origin."""
    i0, j0 = int((x0 - origin[0]) // cell), int((y0 - origin[1]) // cell)
    i1, j1 = int(-(-(x1 - origin[0]) // cell)), int(-(-(y1 - origin[1]) // cell))
    for i in range(i0, i1 + 1):
        x = origin[0] + i * cell
        ax.plot([x, x], [y0, y1], color='#5a7fa8', lw=.5, alpha=.5, zorder=1)
    for j in range(j0, j1 + 1):
        y = origin[1] + j * cell
        ax.plot([x0, x1], [y, y], color='#5a7fa8', lw=.5, alpha=.5, zorder=1)
    for i in range(max(i0, 0), i1):
        x = origin[0] + (i + .5) * cell
        for y, va in ((y1 + cell * .15, 'bottom'), (y0 - cell * .15, 'top')):
            ax.text(x, y, col(i), ha='center', va=va, fontsize=9, color='#2a4f78', weight='bold')
    for j in range(max(j0, 0), j1):
        y = origin[1] + (j + .5) * cell
        for x, ha in ((x0 - cell * .15, 'right'), (x1 + cell * .15, 'left')):
            ax.text(x, y, str(j + 1), ha=ha, va='center', fontsize=9, color='#2a4f78', weight='bold')


def side_segment(box, side, a, b):
    x0, y0, x1, y1 = box
    return {'S': ((a, y0), (b, y0)), 'N': ((a, y1), (b, y1)),
            'W': ((x0, a), (x0, b)), 'E': ((x1, a), (x1, b))}[side]


def reading_order(rooms):
    return sorted(range(len(rooms)), key=lambda k: (-round((rooms[k].box[1] + rooms[k].box[3]) / 6),
                                                    rooms[k].box[0] + rooms[k].box[2]))


def draw_rooms(ax, spec, level, offset=(0.0, 0.0), prefix=''):
    """Rooms, cores, doors, facade entrances. Returns [(id, room index, room)]."""
    dx, dy = offset
    rooms = spec.rooms(level)
    listed = []
    for n, k in enumerate(reading_order(rooms), 1):
        r = rooms[k]
        rid = f'{prefix}{n:02d}'
        listed.append((rid, k, r))
        x0, y0, x1, y1 = r.box
        ax.add_patch(Rectangle((x0 + dx, y0 + dy), x1 - x0, y1 - y0, facecolor=KIND.get(r.kind, '#dddddd'),
                               alpha=.55, edgecolor='black', lw=1.2, zorder=2))
        w, h = x1 - x0, y1 - y0
        size = max(6, min(16, w * 2.2, h * 3.2))
        ax.text(x0 + dx + w / 2, y0 + dy + h / 2 + h * .08, rid, ha='center', va='center', fontsize=size,
                weight='bold', zorder=5)
        if w > 2.4 and h > 2.2:
            ax.text(x0 + dx + w / 2, y0 + dy + h / 2 - h * .16, r.name, ha='center', va='center',
                    fontsize=max(5, min(8, w * 1.1)), zorder=5, wrap=True)
        for side in r.glass:
            (ax0, ay0), (bx0, by0) = side_segment(r.box, side, *((x0, x1) if side in 'SN' else (y0, y1)))
            ax.plot([ax0 + dx, bx0 + dx], [ay0 + dy, by0 + dy], color='#1f77d0', lw=3, zorder=3)
        for side in r.open:
            (ax0, ay0), (bx0, by0) = side_segment(r.box, side, *((x0, x1) if side in 'SN' else (y0, y1)))
            ax.plot([ax0 + dx, bx0 + dx], [ay0 + dy, by0 + dy], color='white', lw=2.5, ls='--', zorder=3)
        for side, c, width in r.doors:
            (ax0, ay0), (bx0, by0) = side_segment(r.box, side, c - width / 2, c + width / 2)
            ax.plot([ax0 + dx, bx0 + dx], [ay0 + dy, by0 + dy], color='#d0021b', lw=4, zorder=4,
                    solid_capstyle='butt')
    for core in spec.cores:
        name, (x0, y0, x1, y1) = core[0], core[1]
        ax.add_patch(Rectangle((x0 + dx, y0 + dy), x1 - x0, y1 - y0, facecolor=KIND['stair'], alpha=.6,
                               hatch='//', edgecolor='black', lw=1.5, zorder=2))
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, f'STAIR\n{name}', ha='center', va='center',
                fontsize=9, weight='bold', zorder=5)
    for r in spec.fixed_rooms(level):
        for side, c, width in r.doors:
            (ax0, ay0), (bx0, by0) = side_segment(r.box, side, c - width / 2, c + width / 2)
            ax.plot([ax0 + dx, bx0 + dx], [ay0 + dy, by0 + dy], color='#d0021b', lw=4, zorder=4,
                    solid_capstyle='butt')
    for (x0, y0, x1, y1), _side in spec.lifts:
        ax.add_patch(Rectangle((x0 + dx, y0 + dy), x1 - x0, y1 - y0, facecolor=KIND['lift'], alpha=.7,
                               edgecolor='black', lw=1.2, zorder=2))
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, 'LIFT', ha='center', va='center', fontsize=7,
                color='white', weight='bold', zorder=5, rotation=90 if y1 - y0 > x1 - x0 else 0)
    frames = {f[0]: f for f in spec.frames()}
    for fname, openings in spec.doors.items():
        _n, axis, c, _a, _b, _in = frames[fname]
        for lvl, s0, s1 in openings:
            if lvl != level:
                continue
            xs, ys = ((s0, s1), (c, c)) if axis == 'y' else ((c, c), (s0, s1))
            ax.plot([x + dx for x in xs], [y + dy for y in ys], color='#18a33a', lw=7, zorder=4,
                    solid_capstyle='butt')
    X, Y = spec.X, spec.Y
    ax.add_patch(Rectangle((dx, dy), X, Y, fill=False, edgecolor='black', lw=2.5, zorder=3))
    if spec.court:
        x0, y0, x1, y1 = spec.court
        ax.add_patch(Rectangle((x0 + dx, y0 + dy), x1 - x0, y1 - y0, facecolor='#eeeeee', alpha=.5,
                               hatch='..', edgecolor='black', lw=2, zorder=2))
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, 'open to the sky', ha='center', va='center',
                fontsize=10, style='italic', zorder=5)
    return listed


def legend(ax, x, y):
    items = [('#d0021b', 'room / stair door'), ('#18a33a', 'entrance in the facade'),
             ('#1f77d0', 'glazed side')]
    for k, (color, text) in enumerate(items):
        ax.plot([x, x + 2.5], [y - k * 2, y - k * 2], color=color, lw=5)
        ax.text(x + 3.2, y - k * 2, text, va='center', fontsize=9)


def figure(x0, y0, x1, y1, px=PX):
    m = 9.0
    w, h = (x1 - x0 + 2 * m) * px / 100, (y1 - y0 + 2 * m + 4) * px / 100
    fig = plt.figure(figsize=(w, h), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(x0 - m, x1 + m)
    ax.set_ylim(y0 - m, y1 + m + 4)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def north(ax, x, y):
    ax.annotate('N', xy=(x, y + 4), xytext=(x, y), ha='center', fontsize=14, weight='bold',
                arrowprops=dict(arrowstyle='-|>', lw=2, color='black'))


def save(fig, folder, name):
    path = OUT / folder / 'MAPS' / f'{name}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


def building_maps(index):
    sheets = []
    # Povo 1
    s = povo1.SPEC
    for level in s.ordered():
        fig, ax = figure(0, 0, s.X, s.Y)
        if ('Povo 1', level) in PLANS:
            underlay(ax, PLANS['Povo 1', level], s.origin)
        grid(ax, 0, 0, s.X, s.Y)
        listed = draw_rooms(ax, s, level)
        z = s.origin[2] + s.levels[level]
        ax.text(-8, s.Y + 9, f'POVO 1  floor {lv(level)}  ({z:.2f} m)', fontsize=20, weight='bold', va='top')
        ax.text(-8, s.Y + 6.6, f'Generated {TODAY} from the current map. Name rooms "P1 {lv(level)} #07", '
                               'spots by grid cell "C7".', fontsize=10, va='top')
        legend(ax, s.X - 14, s.Y + 8.5)
        north(ax, s.X + 5, s.Y + 2)
        sheets.append((save(fig, 'POVO 1', f'P1_floor{lv(level)}'), 'POVO 1', f'P1 {lv(level)}', listed))
    # Povo 2: main block, the strip and plaza, the bridge on floor 1
    m, st = povo2.MAIN, povo2.STRIP
    off = (st.origin[0] - m.origin[0], st.origin[1] - m.origin[1])
    for level in m.ordered():
        y0 = -31.5 if level == 1 else 0
        x1 = off[0] + st.X
        fig, ax = figure(0, y0, x1, m.Y)
        if ('Povo 2', level) in PLANS:
            underlay(ax, PLANS['Povo 2', level], m.origin)
        grid(ax, 0, y0, x1, m.Y)
        listed = draw_rooms(ax, m, level)
        if level in st.levels:
            listed += draw_rooms(ax, st, level, off, 'S')
        else:
            ax.add_patch(Rectangle(off, st.X, st.Y, fill=False, edgecolor='black', lw=2, ls='--', zorder=3))
            if level == 0:
                ax.text(off[0] + st.X / 2, off[1] + 3, 'PLAZA (roof of the strip)', ha='center', fontsize=10,
                        style='italic', zorder=5)
                for name, (b0, b1) in (('GLASS BOX 1\nentrance, reception', povo2.BOX1),
                                       ('GLASS BOX 2\nAula Magna', povo2.BOX2)):
                    ax.add_patch(Rectangle((off[0], b0), 25.5, b1 - b0, facecolor='#b8e0c8', alpha=.6,
                                           edgecolor='#2a7a4a', lw=2, zorder=2))
                    ax.text(off[0] + 12.75, (b0 + b1) / 2, name, ha='center', va='center', fontsize=10,
                            weight='bold', zorder=5)
                x0c, y0c, x1c, y1c = st.court
                ax.add_patch(Rectangle((off[0] + x0c, off[1] + y0c), x1c - x0c, y1c - y0c, facecolor='#eeeeee',
                                       alpha=.6, hatch='..', edgecolor='black', lw=2, zorder=2))
                ax.text(off[0] + (x0c + x1c) / 2, off[1] + (y0c + y1c) / 2, 'HOLE 2', ha='center',
                        va='center', fontsize=11, weight='bold', zorder=5)
        if level == 1:
            bx0, bx1 = povo2.BRIDGE_X
            ax.add_patch(Rectangle((bx0, -30.8), bx1 - bx0, 30.8, facecolor='#d9d9d9', alpha=.8,
                                   edgecolor='black', lw=1.5, zorder=2))
            ax.text(bx1 + 1, -15, 'BRIDGE to Povo 1 floor +1', va='center', fontsize=10, weight='bold')
        z = m.origin[2] + m.levels[level]
        ax.text(-8, m.Y + 9, f'POVO 2  floor {lv(level)}  ({z:.2f} m)', fontsize=20, weight='bold', va='top')
        ax.text(-8, m.Y + 6.6, f'Generated {TODAY}. Main block rooms "P2 {lv(level)} #07", the strip (east, '
                               f'under the plaza) "P2 {lv(level)} #S03", spots "C7".', fontsize=10, va='top')
        legend(ax, x1 - 14, m.Y + 8.5)
        north(ax, x1 + 5, m.Y + 2)
        sheets.append((save(fig, 'POVO 2', f'P2_floor{lv(level)}'), 'POVO 2', f'P2 {lv(level)}', listed))
    # Mensa and library: their own frames
    for spec, folder, code in ((east_block.MENSA, 'MENSA', 'ME'), (east_block.LIBRARY, 'LIBRARY', 'LI')):
        for level in spec.ordered():
            fig, ax = figure(0, 0, spec.X, spec.Y, px=40)
            grid(ax, 0, 0, spec.X, spec.Y)
            listed = draw_rooms(ax, spec, level)
            z = spec.origin[2] + spec.levels[level]
            ax.text(-8, spec.Y + 9, f'{spec.name.upper()}  floor {lv(level)}  ({z:.2f} m)', fontsize=16,
                    weight='bold', va='top')
            ax.text(-8, spec.Y + 6.6, f'Generated {TODAY}. Rooms "{code} {lv(level)} #03", spots "B4".',
                    fontsize=9, va='top')
            north(ax, spec.X + 5, spec.Y + 2)
            sheets.append((save(fig, folder, f'{code}_floor{lv(level)}'), folder, f'{code} {lv(level)}', listed))
    specs = {'P1': povo1.SPEC, 'P2': povo2.MAIN, 'ME': east_block.MENSA, 'LI': east_block.LIBRARY}
    md = {}
    for path, folder, key, listed in sheets:
        code, level = key.split()
        index[key] = {}
        lines = [f'## {key}  ({path.name})', '', '| ID | Name | Kind | x0 y0 x1 y1 (m) |', '|---|---|---|---|']
        for rid, k, r in listed:
            spec = povo2.STRIP if rid.startswith('S') else specs[code]
            index[key][rid] = dict(spec=spec.name, level=int(level), index=k, name=r.name, box=r.box)
            lines.append(f'| {rid} | {r.name} | {r.kind} | {" ".join(f"{v:g}" for v in r.box)} |')
        md.setdefault(folder, []).extend(lines + [''])
    for folder, lines in md.items():
        head = [f'# {folder}: rooms on the labelled maps', '',
                f'Generated {TODAY} from the current map. IDs follow reading order on each floor '
                '(north to south, west to east), so they can change when rooms change: '
                'regenerate the maps after each round of changes.', '']
        (OUT / folder / 'MAPS' / 'rooms.md').write_text('\n'.join(head + lines), encoding='utf8')
    return sheets


def site_map(extent, cell, px, name, title, spot):
    """Outside areas over the 2024 orthophoto: OSM layers and the trees placed in the map,
    with a grid (letters west to east, numbers south to north)."""
    e0, n0, e1, n1 = extent
    layers = json.loads((ROOT / 'data/derived/site_layers.json').read_text(encoding='utf8'))
    fig, ax = figure(0, 0, e1 - e0, n1 - n0, px=px)
    ortho = ROOT / 'data/ortho/site_50cm.jpg'
    a, _, _, e, c, f = [float(v) for v in ortho.with_suffix('.jgw').read_text().split()]
    im = Image.open(ortho)
    crop = im.crop((round((e0 - c) / a), round((f - n1) / -e), round((e1 - c) / a), round((f - n0) / -e)))
    ax.imshow(crop, alpha=.55, extent=(0, e1 - e0, 0, n1 - n0), zorder=0)
    grid(ax, 0, 0, e1 - e0, n1 - n0, cell)

    def xy(points):
        return [p[0] - e0 for p in points], [p[1] - n0 for p in points]

    for p in layers['parking']:
        if 'ring' in p:
            ax.fill(*xy(p['ring']), color='#7a7aa0', alpha=.35, zorder=1)
    for r in layers['roads']:
        ax.plot(*xy(r['line']), color='#404040', lw=3, alpha=.7, zorder=2)
    for p in layers['paths']:
        ax.plot(*xy(p['line']), color='#a0522d', lw=1.5, ls='--', zorder=2)
    for p in layers['steps']:
        ax.plot(*xy(p['line']), color='#d0021b', lw=3, zorder=3)
    for b in layers['barriers']:
        ax.plot(*xy(b['line']), color='#e07000', lw=1.2, zorder=3)
    for b in layers['buildings']:
        ax.fill(*xy(b['ring']), facecolor='#ffffff', alpha=.35, edgecolor='black', lw=1.2, zorder=2)
    with open(ROOT / 'data/derived/trees.csv', encoding='utf8') as fh:
        next(fh)
        for line in fh:
            _src, _id, te, tn, *_ = line.split(',')
            te, tn = float(te), float(tn)
            if e0 < te < e1 and n0 < tn < n1:
                ax.plot(te - e0, tn - n0, 'o', color='#1a7a1a', ms=3.5, zorder=4)
    for lamp in layers['lamps']:
        x, y = lamp['xy']
        if e0 < x < e1 and n0 < y < n1:
            ax.plot(x - e0, y - n0, '*', color='#ffd000', mec='black', mew=.4, ms=7, zorder=4)
    labels = [(povo1.SPEC, 'POVO 1'), (povo2.MAIN, 'POVO 2'), (povo2.STRIP, 'plaza'),
              (east_block.MENSA, 'MENSA'), (east_block.LIBRARY, 'LIBRARY')]
    for spec, text in labels:
        x, y = spec.origin[0] - e0 + spec.X / 2, spec.origin[1] - n0 + spec.Y / 2
        ax.add_patch(Rectangle((spec.origin[0] - e0, spec.origin[1] - n0), spec.X, spec.Y, fill=False,
                               edgecolor='#0050c0', lw=2.5, zorder=5))
        ax.text(x, y, text, ha='center', va='center', fontsize=13, weight='bold', color='#0050c0', zorder=6,
                bbox=dict(facecolor='white', alpha=.75, edgecolor='none'))
    named = set()
    for r in layers['roads']:
        road = r['tags'].get('name')
        pts = [p for p in r['line'] if e0 + 20 < p[0] < e1 - 20 and n0 + 20 < p[1] < n1 - 20]
        if road and road not in named and len(pts) > 2:
            named.add(road)
            p = pts[len(pts) // 2]
            ax.text(p[0] - e0, p[1] - n0, road, fontsize=9, style='italic', color='#202020', zorder=6,
                    bbox=dict(facecolor='#ffffcc', alpha=.8, edgecolor='none'))
    clip = Rectangle((0, 0), e1 - e0, n1 - n0, transform=ax.transData)
    for artist in ax.lines + ax.patches + ax.texts:
        if artist.get_zorder() < 7:
            artist.set_clip_path(clip)
    for artist in ax.texts:                       # labels outside the frame are grid labels: keep them
        x, y = artist.get_position()
        if not (0 <= x <= e1 - e0 and 0 <= y <= n1 - n0):
            artist.set_clip_on(False)
    top = n1 - n0 + 11.5
    ax.text(-8, top, title, fontsize=22, weight='bold', va='top', zorder=8)
    ax.text(-8, top - 3.6 * 7 / px, f'Generated {TODAY}. {cell:g} m grid: name spots "{spot}". Blue: detailed '
                                    'buildings; grey: roads; brown dashed: paths; red: steps; orange: fences; '
                                    'green dots: trees in the map; yellow stars: street lamps; purple: parking.',
            fontsize=10, va='top', zorder=8)
    north(ax, e1 - e0 + 5, n1 - n0 - 10)
    return save(fig, 'EXTERNAL', name)


if __name__ == '__main__':
    index = {}
    for path, *_ in building_maps(index):
        print('wrote', path)
    print('wrote', site_map(CONFIG['site_extent_metres'], 25.0, 7, 'SITE_map', 'SITE  (outside areas)', 'site F9'))
    print('wrote', site_map((666195, 5103655, 666330, 5103950), 10.0, 12, 'CAMPUS_map',
                            'CAMPUS  (outside areas, close-up)', 'campus D12'))
    (ROOT / 'build/maps/room_index.json').write_text(json.dumps(index, indent=1), encoding='utf8')
