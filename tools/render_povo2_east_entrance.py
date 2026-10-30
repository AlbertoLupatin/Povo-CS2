"""Draw the photo-46 plan of the Povo 2 -1 eastern terrace entrance.

Reads config/povo2_east_entrance.json (also built by povo2_playtest_repairs)
and the West Offices layout. Writes
exports/povo2_walkthrough_20261029/east_entrance_photo46.png.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, BG = '#203844', '#496474', '#f4f6f7'
FILL = dict(corridor='#dce6e5', wood='#e2c59f', closed_room='#ebe6df', restricted='#dbcacb',
            terrace='#b7d5cf', provisional_terrace='#d7e9e5', stair='#9aa5ab', context='#e6e9ea')
WALL, AMBER, CLOSED, CODEX = '#424e57', '#db871e', '#b03a2e', '#d4483a'


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('segoeuib.ttf' if bold else 'segoeui.ttf'), size)


def dashed(draw, a, b, fill, width=3, dash=12):
    (x0, y0), (x1, y1) = a, b
    n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** .5 / dash))
    for i in range(0, n, 2):
        draw.line([(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n),
                   (x0 + (x1 - x0) * min(n, i + 1) / n, y0 + (y1 - y0) * min(n, i + 1) / n)], fill=fill, width=width)


def main():
    cfg = json.loads((ROOT / 'config/povo2_east_entrance.json').read_text())
    lay = json.loads((ROOT / 'exports/povo2_west_offices_20261029/layout.json').read_text())
    out = ROOT / 'exports/povo2_walkthrough_20261029/east_entrance_photo46.png'
    im = Image.new('RGB', (2200, 1300), BG); draw = ImageDraw.Draw(im)
    X0, X1, Y0, Y1, K, OX, OY = 8.5, 42.5, -1.5, 27.5, 30, 60, 175

    def xy(x, y): return (OX + (min(max(x, X0), X1) - X0) * K, OY + (Y1 - min(max(y, Y0), Y1)) * K)

    def rect(r, fill=None, outline=None, width=4):
        draw.rectangle((*xy(r[0], r[3]), *xy(r[2], r[1])), fill=fill, outline=outline, width=width)

    def label(text, x, y, size=17, color=INK):
        draw.text(xy(x, y), text, anchor='mm', align='center', font=font(size, True), fill=color)

    draw.rectangle((*xy(X0, Y1), *xy(X1, Y0)), fill='#fbfcfc')
    for gx in range(9, 43):
        draw.line([xy(gx, Y0), xy(gx, Y1)], fill='#e3e8ea' if gx % 5 else '#c9d2d6')
    for gy in range(-1, 28):
        draw.line([xy(X0, gy), xy(X1, gy)], fill='#e3e8ea' if gy % 5 else '#c9d2d6')

    # Existing, unchanged context.
    ctx = cfg['existing_context']
    rect(ctx['exit_corridor'], FILL['context'], WALL, 3)
    rect(ctx['garden_landing'], FILL['context'])
    rect(ctx['up_stair_to_street'], FILL['stair'])
    for i in range(1, 12):
        y = 2.75 + i * .5; draw.line([xy(33.25, y), xy(35.75, y)], fill='#6f7b81', width=1)
    rooms = {r['id']: r['bounds'] for r in lay['rooms']}
    rect(rooms['core_e_store'], FILL['closed_room'], WALL, 3)
    # Stair core, with the retained door on its south face.
    core = lay['core']; rect(core, '#ffffff', WALL, 5)
    for i in range(12):
        x = 11.4 + i * .3; draw.line([xy(x, 19.0), xy(x, 21.8)], fill='#9aa5ab', width=2)
        draw.line([xy(x, 22.2), xy(x, 25.0)], fill='#9aa5ab', width=2)
    label('STAIR CORE\n(fixed)', 17.6, 23.6, 16)

    # C7: west part, the bypass under the core, and the WI1 spine.
    rect([X0, 17.69, 11.0, 20.46], FILL['corridor'])
    rect([9.5, 15.23, 20.5, 18.0], FILL['corridor'])
    rect([X0, 8.09, 20.5, 10.43], FILL['wood'])
    for room in lay['rooms']:
        if not room['id'].startswith('west_'):
            continue
        a, b, c, d = room['bounds']
        if c < X0:
            continue
        if a < X0:
            rect(room['bounds'], FILL['wood'], WALL, 3)
            continue
        rect(room['bounds'], FILL['wood'], WALL, 3)
        label(room['id'][5:], (max(a, X0) + c) / 2, (b + d) / 2, 15, '#354b55')
    # W02 loses its corner to the bypass.
    rect([9.5, 15.23, 11.72, 17.69], FILL['corridor'])
    draw.line([xy(9.5, 15.23), xy(9.5, 17.69)], fill=WALL, width=3)
    draw.line([xy(9.5, 15.23), xy(11.72, 15.23)], fill=WALL, width=3)
    draw.line([xy(X0, 20.46), xy(11.0, 20.46)], fill=WALL, width=4)

    # The corrected eastern entrance.
    areas = {a['id']: a for a in cfg['areas']}
    for key in ('terrace_south_run', 'c5', 'c7_east', 'restricted_north'):
        rect(areas[key]['bounds'], FILL[areas[key]['kind']])
    for r in areas['terrace_link']['bounds']:
        rect(r, FILL['provisional_terrace'])
    for r in areas['terrace_link']['bounds']:
        a, b, c, d = r
        for p, q in (((a, b), (a, d)), ((c, b), (c, d)), ((a, d), (c, d))):
            dashed(draw, xy(*p), xy(*q), '#5d9a8f', 2, 9)
    st = areas['terrace_stair_to_garden']['bounds']; rect(st, FILL['stair'])
    for i in range(1, 21):
        x = st[0] + i * (st[2] - st[0]) / 21; draw.line([xy(x, st[1]), xy(x, st[3])], fill='#6f7b81', width=1)
    for key in ('e1', 'e2'):
        rect(areas[key]['bounds'], FILL['closed_room'], WALL, 4)
    a, b, c, d = areas['c7_east']['bounds']
    draw.line([xy(a, b), xy(33.25, b)], fill=WALL, width=4)
    draw.line([xy(24.5, b), xy(24.5, d)], fill=WALL, width=4)
    # C5 walls; the west side is the office facade, already drawn.
    draw.line([xy(23.1, 2.0), xy(23.1, 15.23)], fill=WALL, width=4)
    draw.line([xy(20.5, 2.0), xy(23.1, 2.0)], fill=WALL, width=4)
    draw.line([xy(20.5, 18.0), xy(33.25, 18.0)], fill=WALL, width=4)
    draw.line([xy(24.3, 18.0), xy(24.3, 26.0)], fill=WALL, width=4)
    # Terrace outer edge (railing) and clipped west end.
    draw.line([xy(X0, .29), xy(31.8, .29)], fill='#5d7f88', width=3)
    label('E1 · closed room', 26.9, 14.0, 15, MUTED)
    label('E2 · closed room', 26.4, 4.6, 15, MUTED)
    label('RESTRICTED\nbeyond door', 22.4, 22.0, 14, '#7b5257')
    label('TERRACE (south run, approved terrace plan)', 15.5, 1.15, 15)
    label('metal stair ↓ Garden −2', 37.1, -.6, 15, MUTED)
    label('existing UP stair\nto street', 38.9, 5.6, 15, MUTED)
    label('existing exit\ncorridor', 34.5, 18.5, 14, MUTED)
    label('C5', 21.8, 12.6, 22)
    label('WI1', 10.6, 9.26, 20)
    label('C7', 9.8, 19.1, 20)
    label('provisional\nlink', 30.9, 5.4, 13, '#3f7d72')

    for o in cfg['openings']:
        p, q = o['line']
        if o['kind'] == 'open':
            continue
        if o['kind'] in ('glass_door_pair', 'existing_door', 'door_pair'):
            draw.line([xy(*p), xy(*q)], fill=BG, width=7)
            draw.line([xy(*p), xy(*q)], fill=AMBER, width=6)
        else:
            draw.line([xy(*p), xy(*q)], fill=CLOSED, width=9)

    # Walking order from the terrace.
    path = [xy(21.8, .9), xy(21.8, 17.3)]
    draw.line(path, fill='#2f7dd1', width=4)
    draw.polygon([(path[1][0] - 10, path[1][1] + 16), (path[1][0] + 10, path[1][1] + 16), path[1]], fill='#2f7dd1')
    for n, (x, y, tx, ty, text) in enumerate([
            (20.5, 9.26, 15.6, 9.26, 'WI1 on the left'),
            (20.5, 16.6, 15.4, 16.6, 'C7 on the left'),
            (21.8, 18.0, 16.0, 27.0, 'closed door ahead')], 1):
        px, py = xy(x, y); lx, ly = xy(tx, ty)
        draw.line([(px, py), (lx, ly)], fill=MUTED, width=2)
        draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill='#2f7dd1')
        t = f'{n} · {text}'; bb = draw.textbbox((lx, ly), t, anchor='mm', font=font(17, True))
        draw.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill='#ffffff', outline='#2f7dd1', width=2)
        draw.text((lx, ly), t, anchor='mm', font=font(17, True), fill=INK)
    px, py = xy(21.85, 2.0); lx, ly = xy(26.0, -1.0)
    draw.line([(px, py), (lx, ly)], fill=MUTED, width=2)
    t = 'Terrace door (exit star)'; bb = draw.textbbox((lx, ly), t, anchor='lm', font=font(17, True))
    draw.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill='#ffffff', outline=AMBER, width=2)
    draw.text((lx, ly), t, anchor='lm', font=font(17, True), fill=INK)

    # Codex's current eastern approach, for comparison.
    cur = cfg['codex_current']
    for r in [cur['c5'], cur['exit_arm'], *cur['arrival_terrace']]:
        a, b, c, d = r
        for p, q in (((a, b), (c, b)), ((c, b), (c, d)), ((c, d), (a, d)), ((a, d), (a, b))):
            dashed(draw, xy(*p), xy(*q), CODEX, 3)
    label('previous build (Codex): C5 5 m wide,\nwrong terrace door, invented arm', 30.3, 27.0, 14, CODEX)
    label('C7 → exit corridor', 29.0, 16.6, 15)

    for gx in range(10, 43, 5):
        draw.text(xy(gx, Y0), str(gx), anchor='mt', font=font(13), fill=MUTED)
    for gy in range(0, 28, 5):
        draw.text((OX - 8, xy(X0, gy)[1]), str(gy), anchor='rm', font=font(13), fill=MUTED)

    # Photo 46, rotated north up, with the same features named.
    pc = cfg['photo_crop']
    photo = Image.open(ROOT / cfg['source_photo']).crop(tuple(pc['box'])).transpose(Image.Transpose.ROTATE_270)
    a, b, c, d = pc['panel']; s = 1.2
    photo = photo.crop((a, b, c, d)).resize((int((c - a) * s), int((d - b) * s)))
    PX, PY = 1130, 175; im.paste(photo, (PX, PY))
    draw.rectangle((PX, PY, PX + photo.width, PY + photo.height), outline='#9aa5ab', width=2)

    def pp(x, y): return (PX + (x - a) * s, PY + (y - b) * s)
    for text, x, y in [('C5', 1233, 870), ('WI1', 1040, 848), ('C7', 1040, 626), ('CORE', 1110, 470),
                       ('E1', 1360, 690), ('E2', 1360, 900), ('1', 1200, 848), ('2', 1200, 626),
                       ('3', 1240, 597), ('door', 1222, 1012), ('W01', 1090, 745), ('W07', 1163, 930)]:
        p = pp(x, y); bb = draw.textbbox(p, text, anchor='mm', font=font(18, True))
        draw.rectangle((bb[0] - 5, bb[1] - 3, bb[2] + 5, bb[3] + 3), fill='#ffffffd0', outline='#2f7dd1', width=2)
        draw.text(p, text, anchor='mm', font=font(18, True), fill=INK)
    draw.text((PX, PY + photo.height + 12), 'Photo 46 (emergency plan), rotated north up. Numbers match the walk order.',
              font=font(17), fill=MUTED)

    draw.text((60, 30), 'POVO 2 −1 / EAST ENTRANCE TO THE W CORRIDORS', font=font(33, True), fill=INK)
    draw.text((60, 82), 'Retraced from photo 46 · campus metres, north up · amber: usable doors · red: closed doors · '
              'dashed red: previous build', font=font(21), fill=MUTED)
    draw.text((60, 118), 'Core, W offices, WI1 and the C7 bypass keep their fitted positions. '
              'Room footprints E1/E2 and the terrace link are estimates.', font=font(21), fill=MUTED)
    notes = ['C5 is a 2.6 m corridor on the offices\' east facade, running from the facade line (N 2.0) to C7.',
             'The terrace door sits at C5\'s south end, on the approved terrace south run, not at N 6.9.',
             'C7 meets C5 full width under the core\'s south face: no door, no stub.',
             'The closed door is right after C7, at N 18. Codex\'s arm north of C7 is not on the plan.',
             'East of C5 are two closed rooms (E1, E2), not garden or terrace.',
             'C7 carries on east through a door to the exit corridor, as the 29 Oct markup asked.']
    for i, t in enumerate(notes):
        draw.text((60, 1080 + i * 32), '•  ' + t, font=font(19), fill=INK)
    im.save(out)
    print(out)


if __name__ == '__main__':
    main()
