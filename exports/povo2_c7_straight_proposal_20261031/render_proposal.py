"""Draw the current -1 game section beside the proposed straight-C7 layout.

Review drawing only: no configuration, export or installed package is changed.
The top panel is sliced from exports/povo_campus collision at z = 1.5 m with the
-1 floor (z = 0.4 m) filled. The bottom panel is the proposal, in the same
local metres: C7 runs straight at N 15.23-18.0 (the stair core's south wall)
from its west end to C5, and the terrace partition at E 20.2-20.36 is gone.
"""
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
EXP = ROOT / 'exports/povo_campus'
B = (-26, -7, 44, 30)
S, L, T, GAP = 15, 46, 112, 120
PW, PH = int((B[2] - B[0]) * S), int((B[3] - B[1]) * S)

C7 = [-14.9, 15.23, 20.5, 18.0]

# Proposal: (label, rect, kind, changed)
ROOMS = [
    ('C7  (straight)', C7, 'corridor', True),
    ('C5', [20.5, 2.0, 23.1, 21.08], 'corridor', False),
    ('restricted', [20.5, 21.08, 23.1, 26.0], 'locked', False),
    ('WI1', [-14.41, 8.09, 20.5, 10.43], 'corridor', False),
    ('WI2', [-17.24, 8.09, -13.04, 17.69], 'corridor', False),
    ('WI3', [-17.24, 5.75, -14.41, 8.09], 'corridor', False),
    ('WI4', [1.3, 10.43, 3.32, 15.23], 'corridor', True),
    ('MAIN STAIR', [11.0, 18.0, 20.5, 26.0], 'core', False),
    ('CIBIO lab', [-13.8, 18.0, -5.3, 26.5], 'room', True),
    ('research\n(restricted)', [-3.7, 18.0, -0.56, 30.0], 'locked', True),
    ('not built\n(void)', [-0.56, 18.0, 11.0, 20.46], 'void', True),
    ('W01', [11.72, 10.43, 20.28, 15.23], 'office', False),
    ('W02', [3.32, 10.43, 11.72, 15.23], 'office', True),
    ('W04', [-5.16, 10.43, 1.3, 15.23], 'office', True),
    ('W05', [-10.21, 10.43, -5.16, 15.23], 'office', True),
    ('W06', [-13.04, 10.43, -10.21, 15.23], 'office', True),
    ('W19', [-23.74, 14.69, -17.24, 17.69], 'office', False),
    ('W20', [-23.74, 11.7, -17.24, 14.69], 'office', False),
    ('W21', [-23.74, 8.7, -17.24, 11.7], 'office', False),
    ('W22', [-23.74, 5.75, -17.24, 8.7], 'office', False),
    ('W23', [-23.74, 2.0, -14.41, 5.75], 'office', False),
    ('E1', [23.1, 12.8, 31.8, 15.23], 'closed', False),
    ('E2', [23.1, 2.0, 31.8, 12.8], 'closed', False),
    ('TERRACE  (continuous)', [8.5, 0.29, 31.8, 2.0], 'terrace', True),
    ('UP', [20.5, -5.71, 23.0, 0.29], 'stair', False),
    ('DOWN to Garden -2', [31.8, 0.29, 42.3, 2.0], 'stair', False),
]
OUTER = [-14.41, -11.26, -8.43, -5.57, -2.78, 0.05, 2.96, 5.86, 8.69, 11.72, 14.47, 17.37, 20.28]
for i, (a, b) in enumerate(zip(OUTER, OUTER[1:])):
    ROOMS.append(('W%02d' % (18 - i), [a, 2.0, b, 8.09], 'office', False))

FILL = dict(corridor='#d6ebe6', office='#ecd9bb', core='#efcf9c', room='#e9e3da', closed='#e9e3da',
            locked='#ead6d6', void='#f4f4f4', terrace='#c4e2dc', stair='#c3cbd0')
# Door marks on the proposal: (p, q, colour)
DOORS = [((20.95, 2.0), (22.75, 2.0), '#e0901a'), ((20.5, 8.31), (20.5, 10.21), '#e0901a'),
         ((18.6, 18.0), (19.8, 18.0), '#e0901a'), ((20.92, 21.08), (22.58, 21.08), '#b03030'),
         ((23.1, 8.65), (23.1, 9.55), '#b03030'), ((-14.74, 15.23), (-13.45, 15.23), '#e0901a'),
         ((1.3, 15.23), (3.32, 15.23), '#e0901a'), ((-5.3, 24.4), (-5.3, 25.4), '#e0901a')]


def load(name):
    verts, faces = [], []
    with open(EXP / name, encoding='utf-8') as f:
        for line in f:
            if line.startswith('v '):
                verts.append(tuple(map(float, line.split()[1:4])))
            elif line.startswith('f '):
                idx = [int(t.split('/')[0]) for t in line.split()[1:]]
                faces += [(idx[0], idx[i], idx[i + 1]) for i in range(1, len(idx) - 1)]
    t = np.array(verts)[np.array(faces) - 1]
    keep = ~((t[:, :, 0].max(1) < B[0]) | (t[:, :, 0].min(1) > B[2]) |
             (t[:, :, 1].max(1) < B[1]) | (t[:, :, 1].min(1) > B[3]))
    return t[keep]


def main():
    names = ['povo1_campus_collision.obj'] + ['povo1_campus_collision_%s.obj' % m for m in
             ('asphalt', 'concrete', 'glass', 'grass', 'metal', 'tile', 'wood')] + ['povo1_campus_paving.obj']
    tris = np.concatenate([load(n) for n in names])
    W, H = PW + 2 * L + 330, 2 * PH + 2 * T + GAP + 40
    img = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(img)
    font = lambda s, b=False: ImageFont.truetype('C:/Windows/Fonts/%s.ttf' % ('arialbd' if b else 'arial'), s)
    f11, f13, f15, f22 = font(11), font(13), font(15), font(24, True)
    tops = [T, T + PH + GAP]

    def pt(p, top):
        return (p[0] - B[0]) * S, (B[3] - p[1]) * S

    def grid(top):
        for x in range(-25, B[2] + 1, 5):
            dr.line([pt((x, B[1]), top), pt((x, B[3]), top)], fill='#ececec')
            page.text((L + pt((x, B[1]), top)[0] - 7, top + PH + 4), str(x), font=f11, fill='#777')
        for y in range(-5, B[3] + 1, 5):
            dr.line([pt((B[0], y), top), pt((B[2], y), top)], fill='#ececec')
            page.text((L - 26, top + pt((0, y), top)[1] - 6), str(y), font=f11, fill='#777')

    def rect(r, top, **kw):
        a, b = pt((r[0], r[3]), top), pt((r[2], r[1]), top)
        dr.rectangle([a, b], **kw)

    def label(text, r, top, fnt=f13, fill='#1d3a44'):
        cx, cy = pt(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), top)
        bb = dr.multiline_textbbox((0, 0), text, font=fnt, align='center')
        dr.multiline_text((cx - bb[2] / 2, cy - bb[3] / 2), text, font=fnt, fill=fill, align='center')

    page = dr
    panels = [Image.new('RGB', (PW, PH), 'white') for _ in tops]
    # --- current game geometry
    top = tops[0]
    dr = ImageDraw.Draw(panels[0])
    grid(top)
    floor = tris[(np.abs(tris[:, :, 2] - 0.4) < .02).all(1)]
    for f in floor:
        dr.polygon([pt(p, top) for p in f], fill='#dbe7e9')
    z = 1.5
    cut = tris[(tris[:, :, 2].min(1) < z) & (tris[:, :, 2].max(1) > z)]
    for f in cut:
        hits = []
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            if (a[2] - z) * (b[2] - z) < 0:
                s = (z - a[2]) / (b[2] - a[2])
                hits.append(a[:2] + s * (b[:2] - a[:2]))
        if len(hits) == 2:
            dr.line([pt(hits[0], top), pt(hits[1], top)], fill='#1b2b30', width=2)
    # Red marks only where the export still has the old jog or terrace partition.
    lo, hi = tris.min(1), tris.max(1)

    def solid(x0, y0, x1, y1):
        return bool(((lo[:, 0] < x1) & (hi[:, 0] > x0) & (lo[:, 1] < y1) & (hi[:, 1] > y0)
                     & (lo[:, 2] < 2.3) & (hi[:, 2] > .5)).any())
    c7_ok = not solid(C7[0] + .4, C7[1] + .17, C7[2] - .3, C7[3] - .15)
    terrace_ok = not solid(8.8, .45, 31.5, 1.85)
    if not c7_ok:
        rect(C7, top, outline='#d0342c', width=3)
        label('C7 blocked', C7, top, f15, '#b0261f')
    if not terrace_ok:
        rect([8.5, 0.29, 31.8, 2.0], top, outline='#d0342c', width=3)
    for text, r in [('MAIN STAIR', [11, 18, 20.5, 26]), ('C5', [20.5, 2, 23.1, 21]), ('E2', [23.1, 2, 31.8, 12.8]),
                    ('E1', [23.1, 12.8, 31.8, 15.23]), ('WI1', [-14.4, 8.09, 20.3, 10.43]), ('CIBIO lab', [-13.8, 18, -5.3, 26.5]),
                    ('C7', C7), ('W02', [3.32, 10.43, 11.72, 15.23]), ('W01', [11.72, 10.43, 20.28, 15.23]),
                    ('W04', [-5.16, 10.43, 1.3, 15.23]), ('terrace', [8.5, 0.29, 20.5, 2.0])]:
        label(text, r, top)
    built = datetime.fromtimestamp((EXP / 'povo1_campus_collision.obj').stat().st_mtime).strftime('%d %b %H:%M')

    # --- proposal
    top = tops[1]
    dr = ImageDraw.Draw(panels[1])
    grid(top)
    order = ['void', 'locked', 'room', 'closed', 'office', 'core', 'stair', 'terrace', 'corridor']
    for kind in order:
        for text, r, k, changed in ROOMS:
            if k == kind:
                rect(r, top, fill=FILL[k], outline='#2f4850', width=2)
    for text, r, k, changed in ROOMS:
        if changed:
            rect(r, top, outline='#e0701a', width=4)
    # WI2 opens into C7's west end; WI4 open onto C7 and WI1.
    rect([-14.86, 15.15, -13.08, 15.31], top, fill=FILL['corridor'])
    rect([1.36, 15.15, 3.26, 15.31], top, fill=FILL['corridor'])
    rect([1.36, 10.35, 3.26, 10.51], top, fill=FILL['corridor'])
    for p, q, c in DOORS:
        dr.line([pt(p, top), pt(q, top)], fill=c, width=6)
    for text, r, k, changed in ROOMS:
        if r[2] - r[0] > 1.5 and r[3] - r[1] > 1.2:
            label(text, r, top, f15 if text.startswith(('C7', 'TERRACE')) else f13)
    for y in (-5.71 + 0.5 * i for i in range(12)):
        dr.line([pt((20.5, y), top), pt((23.0, y), top)], fill='#8e9aa1')
    for x in (31.8 + 0.5 * i for i in range(22)):
        dr.line([pt((x, 0.29), top), pt((x, 2.0), top)], fill='#8e9aa1')

    dr = page
    for panel, top in zip(panels, tops):
        img.paste(panel, (L, top))
        dr.rectangle([L - 1, top - 1, L + PW, top + PH], outline='#b8c6ca')
    # --- text
    dr.text((L, 18), 'POVO 2 -1 / STRAIGHT C7 AND CONTINUOUS TERRACE: AS EXPORTED VS APPROVED', font=f22, fill='#173742')
    dr.text((L, 52), 'Top: the map as now exported (walls cut at 1.5 m; grey = -1 floor). Bottom: the approved layout. North up; local metres.',
            font=f15, fill='#4a626b')
    dr.text((L, tops[0] - 24), 'AS EXPORTED (collision of %s)' % built, font=font(16, True), fill='#173742')
    dr.text((L, tops[1] - 24), 'APPROVED', font=font(16, True), fill='#173742')
    notes = [
        ('AS EXPORTED', '#1d7a4c' if c7_ok and terrace_ok else '#b0261f', [
            'C7 band N 15.23-18.0 clear' if c7_ok else 'C7 band N 15.23-18.0 BLOCKED',
            'from its west end to C5.' if c7_ok else '(red outline).',
            '',
            'Terrace E 8.5-31.8 clear,' if terrace_ok else 'Terrace E 8.5-31.8 BLOCKED',
            'one strip.' if terrace_ok else '(red outline).',
            '',
            'Probe: no collision between',
            'z 0.5 and 2.3 m in either band.']),
        ('APPROVED', '#c65f12', [
            'Orange outline = changed.',
            '',
            'C7: one straight band,',
            'N 15.23-18.0, from its west',
            'end (E -14.9) to C5. Its north',
            'wall lines up with the stair',
            "core's south wall (N 18.0).",
            '',
            'Offices on C7 (W02, WI4, W04,',
            'W05, W06) end at N 15.23,',
            'like W01 in your drawing.',
            'W19-W23, WI2 and the south',
            'row are unchanged; WI2 opens',
            "into C7's west end.",
            '',
            'North side: CIBIO lab and the',
            'restricted research corridor',
            'extend south to C7 (N 18.0).',
            'Strip E -0.56-11 stays closed',
            '(full-plan rooms, not built).',
            '',
            'Terrace: one strip, E 8.5-31.8.']),
    ]
    x0 = L + PW + 24
    for (title, colour, lines), top in zip(notes, tops):
        dr.text((x0, top), title, font=font(16, True), fill=colour)
        for i, line in enumerate(lines):
            dr.text((x0, top + 26 + i * 19), line, font=f13, fill='#2f4850')
    img.save(OUT / 'as_built_vs_proposal.png')
    print(OUT / 'as_built_vs_proposal.png')


if __name__ == '__main__':
    main()
