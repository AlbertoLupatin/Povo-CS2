"""Build the external -1 terrace of Povo 2 from plan photo 46 and the user's markup.

Reads the West Offices layout without changing it. Writes review geometry:
terrace slabs, holes down to the parking, railings, recess columns and the two
metal stairs down to -2.
"""
import hashlib
import json
import math
from html import escape

from PIL import Image, ImageDraw, ImageFont

from tools.build_povo_campus import ROOT
from tools.povo2_basements import union_rectangles

OUT = 'exports/povo2_minus1_terrace_20261029'
BAR = .12


def overlaps(a, b, eps=1e-6):
    return a[0] < b[2]-eps and b[0] < a[2]-eps and a[1] < b[3]-eps and b[1] < a[3]-eps


def solids(layout):
    """Every -1 room, core and corridor footprint the terrace must stay out of."""
    return ([(r['id'], r['bounds']) for r in layout['rooms']]
            + [(c['id'], c['bounds']) for c in layout['cores']]
            + [(c['id'], c['bounds']) for c in layout['corridors']])


def intersect(spans, keep):
    """North intervals of spans that lie inside any keep interval."""
    return [(max(u, a), min(v, b)) for u, v in spans for a, b in keep if min(v, b)-max(u, a) > 1e-6]


def hole_rails(slabs, holes, facade):
    """Rail every terrace edge that borders a hole, along the shared length.

    Slabs within half a metre of the facade belong to the strip, so a core's
    face fill is railed at a hole end even though it starts at the facade.
    """
    rails = []
    for s in slabs:
        x0, y0, x1, y1 = s['bounds']
        strip = x1 <= facade+.5
        for h0, a, h1, b in holes:
            if strip or min(x1, h1)-max(x0, h0) > 1e-6:
                e0, e1 = (x0, x1) if strip else (max(x0, h0), min(x1, h1))
                if abs(y1-a) < 1e-6:
                    rails.append([e0, y1-BAR, e1, y1])
                if abs(y0-b) < 1e-6:
                    rails.append([e0, y0, e1, y0+BAR])
            if min(y1, b)-max(y0, a) > 1e-6 and abs(x0-h1) < 1e-6:
                rails.append([x0, max(y0, a), x0+BAR, min(y1, b)])
    return [dict(kind='hole_rail', side='hole', bounds=r, evidence='guard at a hole in the slab') for r in rails]


def build(base, cfg):
    rooms = {r['id']: r['bounds'] for r in base['rooms']}
    outer = cfg['outer_edge']['east']
    # The facade is the west face shared by Room 1, Room 2, L28 and the West Offices.
    facade = min(r[0] for r in rooms.values())
    runs = {k: (cfg[k]['north'], cfg[k]['east_end']) for k in ('south_run', 'north_run')}
    segments = sorted(cfg['west_strip']['segments'], key=lambda s: s['north'][0])
    present = [tuple(s['north']) for s in segments if s['kind'] == 'present']
    holes = [[outer, *s['north'][:1], facade, s['north'][1]] for s in segments if s['kind'] == 'hole']
    slabs = [dict(id=k, bounds=[outer, n[0], e, n[1]]) for k, (n, e) in runs.items()]
    slabs += [dict(id=f'west_strip_{i}', bounds=[outer, a, facade, b]) for i, (a, b) in enumerate(present)]
    recesses = []
    for spec in cfg['recesses']:
        low, high = (rooms[i] for i in spec['between'])
        low, high = sorted((low, high), key=lambda r: r[1])
        inner = min(rooms[i][0] for i in spec['fronting'])
        r = [facade, low[3], inner, high[1]]
        recesses.append(dict(id=spec['id'], bounds=r, depth=inner-facade, labels=spec['drawing_labels'],
                             between=spec['between'], fronting=spec['fronting'], evidence=spec['evidence']))
        slabs.append(dict(id=spec['id'], bounds=r))
    # Cores sit 0.27 m inside the facade; close that sliver so their exit doors land on the terrace.
    for c in base['cores']:
        b = c['bounds']
        if facade < b[0] < facade+1:
            slabs += [dict(id=f"{c['id']}_face_{i}", bounds=[facade, u, b[0], v])
                      for i, (u, v) in enumerate(intersect([(b[1], b[3])], present))]
    edges = [dict(kind='railing', side='west', bounds=[outer, a, outer+BAR, b], evidence='outer edge of the west strip')
             for a, b in present]
    for k, (n, e) in runs.items():
        edge = [outer, n[0], e, n[0]+BAR] if k == 'south_run' else [outer, n[1]-BAR, e, n[1]]
        edges += [dict(kind='railing', side=k, bounds=edge, evidence='outer edge of the run'),
                  dict(kind='railing', side=k, bounds=[outer, n[0], outer+BAR, n[1]], evidence='west end of the run')]
    edges += hole_rails(slabs, holes, facade)
    col = cfg['columns']
    columns = [[col['east'][0], n-col['size'][1]/2, col['east'][1], n+col['size'][1]/2] for n in col['north_centres']]
    stairs = []
    for st in cfg['metal_stairs']:
        f = st['flights']; y0, y1 = f[0][1], f[0][3]
        stairs.append(dict(id=st['id'], run=st['run'], label=st['label'], flights=f, mid_landing=st['mid_landing'],
                           top_z=cfg['z'], bottom_z=st['bottom_z'], risers_per_flight=st['risers_per_flight'],
                           evidence=st['evidence'], conflict=st['conflict'],
                           rails=[[f[0][0], y0, f[1][2], y0+BAR], [f[0][0], y1-BAR, f[1][2], y1]]))
    west_exits = [e for e in base['exits'] if e['campus_point'][0] < facade+4]
    area = sum((r[2]-r[0])*(r[3]-r[1]) for r in union_rectangles([s['bounds'] for s in slabs])[0])
    return dict(status=cfg['status'], user_description=cfg['user_description'], user_markup=cfg['user_markup'],
                frame=cfg['frame'], z=cfg['z'], slab_thickness=cfg['slab_thickness'], barrier_height=cfg['barrier_height'],
                railing=cfg['railing'],
                facade_east=facade, outer_edge_east=outer, width=facade-outer, slabs=slabs, recesses=recesses,
                west_strip=segments, holes=[dict(bounds=h, view=cfg['holes_view']) for h in holes],
                edges=edges, edge_kinds=cfg['edge_kinds'], columns=columns, metal_stairs=stairs,
                served_exits=[dict(id=e['id'], campus_point=e['campus_point']) for e in west_exits],
                hole_length=sum(h[3]-h[1] for h in holes), area=area,
                unresolved=[cfg['unresolved_recess_line'], *cfg['known_gaps_in_base']],
                photo_fit=cfg['photo_fit'])


class Canvas:
    """Draw once into both a PNG and an SVG."""
    def __init__(self, view, scale, margin=(70, 150, 70, 130)):
        self.v, self.s = view, scale
        self.l, self.t, r, b = margin
        self.w = int((view[2]-view[0])*scale)+self.l+r
        self.h = int((view[3]-view[1])*scale)+self.t+b
        self.im = Image.new('RGB', (self.w, self.h), 'white')
        self.d = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">',
                    '<rect width="100%" height="100%" fill="white"/>']

    def xy(self, e, n):
        return self.l+(e-self.v[0])*self.s, self.t+(self.v[3]-n)*self.s

    def clip(self, r):
        v = self.v
        r = [max(r[0], v[0]), max(r[1], v[1]), min(r[2], v[2]), min(r[3], v[3])]
        return r if r[0] <= r[2] and r[1] <= r[3] else None

    def rect(self, r, fill, outline=None, width=1, dash=False):
        r = self.clip(r)
        if not r:
            return
        x0, y0 = self.xy(r[0], r[3]); x1, y1 = self.xy(r[2], r[1])
        self.d.rectangle((x0, y0, x1, y1), fill=fill)
        if outline and not dash:
            self.d.rectangle((x0, y0, x1, y1), outline=outline, width=width)
        elif outline:
            for p, q in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                self.dashed(p, q, outline, width)
        stroke = f' stroke="{outline}" stroke-width="{width}"'+(' stroke-dasharray="6 5"' if dash else '') if outline else ''
        self.svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" fill="{fill}"{stroke}/>')

    def dashed(self, p, q, fill, width, on=6, off=5):
        length = ((q[0]-p[0])**2+(q[1]-p[1])**2)**.5 or 1
        t = 0
        while t < length:
            u = min(t+on, length)
            self.d.line(((p[0]+(q[0]-p[0])*t/length, p[1]+(q[1]-p[1])*t/length),
                         (p[0]+(q[0]-p[0])*u/length, p[1]+(q[1]-p[1])*u/length)), fill=fill, width=width)
            t += on+off

    def line(self, a, b, fill, width=2, dash=False):
        r = self.clip([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])])
        if not r:
            return
        a, b = (r[0], r[1]), (r[2], r[3])
        p, q = self.xy(*a), self.xy(*b)
        self.dashed(p, q, fill, width) if dash else self.d.line((p, q), fill=fill, width=width)
        self.svg.append(f'<path d="M{p[0]:.1f},{p[1]:.1f} L{q[0]:.1f},{q[1]:.1f}" stroke="{fill}" stroke-width="{width}"'
                        + (' stroke-dasharray="6 5"' if dash else '')+'/>')

    def text(self, x, y, s, size=16, bold=False, fill='#233b46', anchor='la', at=None):
        if at:
            x, y = self.xy(*at)
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf', size)
        self.d.text((x, y), s, font=font, fill=fill, anchor=anchor)
        svg_anchor = {'m': 'middle', 'l': 'start', 'r': 'end'}[anchor[0]]
        base = 'central' if anchor[1] == 'm' else 'hanging'
        self.svg.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}" text-anchor="{svg_anchor}" dominant-baseline="{base}">{escape(s)}</text>')

    def save(self, path):
        self.im.save(path.with_suffix('.png'))
        path.with_suffix('.svg').write_text('\n'.join(self.svg+['</svg>'])+'\n', encoding='utf-8')


EDGE_COLOURS = {'parapet': '#2b3a42', 'unresolved': '#c98a1b', 'railing': '#6b7b84',
                'landing_rail': '#6b7b84', 'hole_rail': '#6b7b84'}
HOLE = '#7fb3d9'


def draw(base, terrace, view, scale, title, subtitle, path):
    cv = Canvas(view, scale)
    cv.text(cv.l, 28, title, 30, True)
    for i, part in enumerate(subtitle.split('|')):
        cv.text(cv.l, 70+i*24, part, 18, fill='#536773')
    for r in base['rooms']:
        office = r['id'].startswith(('west_W', 'office_outer', 'office_inner'))
        cv.rect(r['bounds'], '#e7dbef' if office else '#dcebef', '#3a4d57', 1)
    for c in base['corridors']:
        cv.rect(c['bounds'], '#dfece0')
    for c in base['cores']:
        cv.rect(c['bounds'], '#efcf9f', '#3a4d57', 1)
    for s in terrace['slabs']:
        cv.rect(s['bounds'], '#c9c3b6')
    for r in terrace['recesses']:
        cv.rect(r['bounds'], '#d8d1c2')
    for h in terrace['holes']:
        cv.rect(h['bounds'], HOLE, '#2f7fc1', 1, dash=True)
    for st in terrace['metal_stairs']:
        for f in st['flights']:
            cv.rect(f, '#5a5f63')
            n = st['risers_per_flight']
            for k in range(1, n):
                e = f[0]+(f[2]-f[0])*k/n
                cv.line((e, f[1]), (e, f[3]), '#c9ced1', 1)
        cv.rect(st['mid_landing'], '#6d7276')
        for r in st['rails']:
            cv.rect(r, '#2b3a42')
    for e in terrace['edges']:
        cv.rect(e['bounds'], EDGE_COLOURS[e['kind']])
    for c in terrace['columns']:
        cv.rect(c, '#1f2a30')
    for ex in terrace['served_exits']:
        if not cv.clip([*ex['campus_point'], *ex['campus_point']]):
            continue
        x, y = cv.xy(*ex['campus_point'])
        cv.d.regular_polygon((x, y, 7), 5, fill='#b85c4f')
        cv.svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#b85c4f"/>')
    for r in terrace['recesses'] if scale >= 15 else ():
        b = r['bounds']
        cv.text(0, 0, 'widened bay', int(scale*.8), True, '#6b5a36', 'mm', at=((b[0]+b[2])/2, (b[1]+b[3])/2))
    labels = dict(annotated_lab_e='ROOM 1', annotated_lab_w='ROOM 2', outer_center='L28')
    for rid in labels:
        b = next(r['bounds'] for r in base['rooms'] if r['id'] == rid)
        if overlaps(b, view):
            cv.text(0, 0, labels[rid], max(11, int(scale*1.2)), True, '#233b46', 'mm', at=((b[0]+b[2])/2, (b[1]+b[3])/2))
    for st in terrace['metal_stairs']:
        f = st['flights']; below = st['run'] == 'south_run'
        cv.text(0, 0, st['label'], max(11, int(scale*1.1)), True, '#3d4347', 'mm',
                at=((f[0][0]+f[1][2])/2, f[0][1]-1.6 if below else f[0][3]+1.6))
    # Legend.
    y = cv.h-100
    items = [('#c9c3b6', 'terrace slab, z 0.4'), ('#d8d1c2', 'widened bay (fills the office-row recess)'),
             (HOLE, 'hole in slab: looks down to the parking ramp'), (EDGE_COLOURS['railing'], 'railing (outer edges and hole edges)'),
             ('#1f2a30', 'column on facade line')]
    for i, (colour, label) in enumerate(items):
        x = cv.l+(i % 2)*390; yy = y+(i//2)*26
        cv.d.rectangle((x, yy, x+18, yy+18), fill=colour); cv.svg.append(f'<rect x="{x}" y="{yy}" width="18" height="18" fill="{colour}"/>')
        cv.text(x+26, yy+1, label, 15, fill='#3a4d57')
    cv.save(path)


def write_evidence(root, cfg, terrace, path):
    """Plan-46 west edge with the fitted facade, outer line and edge segments drawn on it."""
    im = Image.open(root/cfg['source_photo']).convert('RGB')
    fx, fy = cfg['photo_fit']['north_from_photo_x'], cfg['photo_fit']['east_from_photo_y']
    px = lambda n: fx['photo_x_at']+(n-fx['north_at'])/fx['metres_per_pixel']
    py = lambda e: fy['photo_y_at']+(e-fy['east_at'])/fy['metres_per_pixel']
    crop = (380, 3930, 3320, 4330)
    d = ImageDraw.Draw(im)
    for seg in terrace['edges']:
        if seg['side'] != 'west':
            continue
        b = seg['bounds']
        d.line(((px(b[1]), py(b[0])+14), (px(b[3]), py(b[0])+14)), fill=EDGE_COLOURS[seg['kind']], width=7)
    for h in terrace['holes']:
        b = h['bounds']
        d.line(((px(b[1]), py(b[0])+14), (px(b[3]), py(b[0])+14)), fill='#2f7fc1', width=7)
    for r in terrace['recesses']:
        b = r['bounds']
        d.rectangle((px(b[3]), py(b[2]), px(b[1]), py(b[0])), outline='#d08a1c', width=4)
    for c in terrace['columns']:
        d.rectangle((px(c[3]), py(c[2]), px(c[1]), py(c[0])), outline='#11aa55', width=3)
    out = im.crop(crop)
    out = out.resize((out.width//2, out.height//2), Image.Resampling.LANCZOS)
    banner = Image.new('RGB', (out.width, out.height+60), 'white')
    banner.paste(out, (0, 60))
    out = banner
    dd = ImageDraw.Draw(out)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    dd.text((10, 6), 'Plan 46, west facade (photo bottom). User-corrected strip: blue = hole in slab, grey = terrace railing.',
            font=font, fill='#203040')
    dd.text((10, 32), 'Amber boxes = widened bays; green = columns. Terrace presence follows the user markup.',
            font=font, fill='#203040')
    out.save(path)


def terrace_railing_parts(terrace):
    """Supported top/middle rails at every marked terrace and hole edge."""
    z, height, spec = terrace['z'], terrace['barrier_height'], terrace['railing']
    parts = []
    def add(name, bounds, bottom, thickness):
        parts.append(dict(name=name, bounds=bounds, bottom=bottom, height=thickness))
    for i, edge in enumerate(terrace['edges']):
        a,b,c,d = edge['bounds']; prefix = f"{edge['kind']}_{i}"
        if edge['kind'] == 'parapet':
            add(prefix, [a,b,c,d], z, height)
            continue
        add(prefix+'_top_rail', [a,b,c,d], z+height-.06, .06)
        add(prefix+'_kick', [a,b,c,d], z, .12)
        axis = 0 if c-a >= d-b else 1
        mid = [(a+c)/2, (b+d)/2]
        width = spec['mid_rail_size']
        rail = [a, mid[1]-width/2, c, mid[1]+width/2] if axis == 0 else [mid[0]-width/2,b,mid[0]+width/2,d]
        add(prefix+'_mid_rail', rail, z+spec['mid_rail_height']-width, width)
        pw = spec['post_width']; start = (a,b)[axis]; end = (c,d)[axis]-pw
        spans = max(1, math.ceil((end-start)/spec['post_spacing']))
        for j in range(spans+1):
            u = start+(end-start)*j/spans
            post = [u,mid[1]-pw/2,u+pw,mid[1]+pw/2] if axis == 0 else [mid[0]-pw/2,u,mid[0]+pw/2,u+pw]
            # Meet the kick plate and the underside of the handrail; avoid
            # coplanar faces on top of the rail itself.
            add(prefix+f'_post_{j}', post, z+.12, height-.06-.12)
    return parts


def write_obj(terrace, path):
    z, t, hb = terrace['z'], terrace['slab_thickness'], terrace['barrier_height']
    lines = ['# Povo 2 -1 external terrace; campus metres (x east, y north, z up); review geometry']
    index = 0

    def box(name, r, bottom, height, end_bottom=None):
        nonlocal index
        a, b, c, d = r[:4]; lines.append('o '+name)
        end = bottom if end_bottom is None else end_bottom
        for x, y, h in [(a, b, bottom), (c, b, end), (c, d, end), (a, d, bottom),
                        (a, b, bottom+height), (c, b, end+height), (c, d, end+height), (a, d, bottom+height)]:
            lines.append(f'v {x:.4f} {y:.4f} {h:.4f}')
        for face in [(1, 4, 3, 2), (5, 6, 7, 8), (1, 2, 6, 5), (2, 3, 7, 6), (3, 4, 8, 7), (4, 1, 5, 8)]:
            lines.append('f '+' '.join(str(index+i) for i in face))
        index += 8
    for s in terrace['slabs']:
        box('terrace_'+s['id'], s['bounds'], z-t, t)
    for part in terrace_railing_parts(terrace):
        box(part['name'], part['bounds'], part['bottom'], part['height'])
    for i, c in enumerate(terrace['columns']):
        box(f'column_{i}', c, z, 3.6)
    for st in terrace['metal_stairs']:
        n = st['risers_per_flight']; rise = (st['top_z']-st['bottom_z'])/(2*n)
        upper, lower = st['flights']
        for i in range(n):
            # Upper flight descends eastward from the terrace to the mid landing.
            e0 = upper[0]+(upper[2]-upper[0])*i/n; e1 = upper[0]+(upper[2]-upper[0])*(i+1)/n
            box(f"stair_{st['id']}_upper_{i}", [e0, upper[1]+BAR, e1, upper[3]-BAR], st['top_z']-(i+1)*rise-.05, .05)
            e0 = lower[0]+(lower[2]-lower[0])*i/n; e1 = lower[0]+(lower[2]-lower[0])*(i+1)/n
            box(f"stair_{st['id']}_lower_{i}", [e0, lower[1]+BAR, e1, lower[3]-BAR], st['top_z']-(n+i+1)*rise-.05, .05)
        box(f"stair_{st['id']}_mid_landing", st['mid_landing'], st['top_z']-n*rise-.08, .08)
        # Follow each flight with a thin handrail, level over the landing.
        # A single tall box here would close the stair with a solid wall.
        mid_z = st['top_z']-n*rise
        for side, r in enumerate(st['rails']):
            for part, footprint, start, end in (
                ('upper', upper, st['top_z'], mid_z),
                ('landing', st['mid_landing'], mid_z, mid_z),
                ('lower', lower, mid_z, st['bottom_z'])):
                rail = [footprint[0], r[1], footprint[2], r[3]]
                box(f"stair_{st['id']}_rail_{side}_{part}", rail, start+hb-.06, .06, end+hb-.06)
                middle = terrace['railing']['mid_rail_height']; size = terrace['railing']['mid_rail_size']
                cy = (r[1]+r[3])/2
                middle_rail = [rail[0],cy-size/2,rail[2],cy+size/2]
                box(f"stair_{st['id']}_mid_rail_{side}_{part}", middle_rail, start+middle-size, size, end+middle-size)
                for j in range(3):
                    f = j/2
                    x = rail[0]+(rail[2]-rail[0]-BAR)*f
                    deck = start+(end-start)*f
                    box(f"stair_{st['id']}_post_{side}_{part}_{j}", [x, r[1], x+BAR, r[3]], deck, hb)
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def export(root=ROOT):
    cfg = json.loads((root/'config/povo2_minus1_terrace.json').read_text(encoding='utf-8'))
    base = json.loads((root/cfg['base_layout']).read_text(encoding='utf-8'))
    terrace = build(base, cfg)
    terrace['source_hashes'] = {p: hashlib.sha256((root/p).read_bytes()).hexdigest()
                                for p in ('config/povo2_minus1_terrace.json', cfg['base_layout'], cfg['source_photo'],
                                          cfg['user_markup']['file'], 'tools/build_povo2_minus1_terrace.py')}
    out = root/OUT; out.mkdir(parents=True, exist_ok=True)
    (out/'terrace.json').write_text(json.dumps(terrace, indent=2)+'\n', encoding='utf-8')
    draw(base, terrace, [-30, -3, 46, 109], 9, 'POVO 2  /  FLOOR −1  /  EXTERNAL TERRACE',
         'Third draft: your markup applied to plan 46. North and south runs,|two metal stairs, three holes in the west strip. Dimensions estimated.',
         out/'minus1_with_terrace')
    draw(base, terrace, [-30, 26, 8, 96], 18, 'WEST FACADE — BAYS AND HOLES',
         'Widened bays reach the O13–O20 office face. The strip outside|both bays and L28 is a hole; room exits keep their terrace.', out/'west_facade_detail')
    draw(base, terrace, [-27, -3, 46, 20], 16, 'SOUTH RUN — FROM THE METAL STAIR',
         'Stair rises from Garden −2 to the terrace at the south-east corner.', out/'south_run_detail')
    draw(base, terrace, [-27, 92, 46, 112], 16, 'NORTH RUN — SECOND METAL STAIR',
         'North run follows the C5/C8 facade; the stair descends to −2.|Its bottom level is assumed. No north garden is modelled.', out/'north_run_detail')
    write_evidence(root, cfg, terrace, out/'plan46_terrace_evidence.png')
    write_obj(terrace, out/'terrace.obj')
    return terrace, out


if __name__ == '__main__':
    terrace, out = export()
    print(out)
    print(f"Terrace {terrace['area']:.0f} m², {len(terrace['recesses'])} widened bays, {len(terrace['holes'])} holes "
          f"({terrace['hole_length']:.1f} m of strip), {len(terrace['metal_stairs'])} metal stairs.")
