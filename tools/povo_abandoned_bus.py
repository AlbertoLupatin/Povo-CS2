"""Open, weathered midi bus, broadside across the east bridge approach."""
import math
from pathlib import Path

DESTINATION = '5/ Università di Povo'


def destination_mask():
    """Small LED glyph mask; geometry keeps the destination legible without UV tiling."""
    from PIL import Image, ImageDraw, ImageFont
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    font = ImageFont.truetype(str(font_path), 15) if font_path.exists() else ImageFont.load_default()
    bounds = font.getbbox(DESTINATION)
    image = Image.new('L', (bounds[2] - bounds[0], bounds[3] - bounds[1]), 0)
    ImageDraw.Draw(image).text((-bounds[0], -bounds[1]), DESTINATION, font=font, fill=255)
    return image


def extend(box, meshes, spec):
    x, y, z = spec['centre']
    half = spec['length'] / 2
    width = spec['width'] / 2
    entry_lo, entry_hi = half - 3.70, half - 2.25

    def part(name, lo, hi, material):
        box('abandoned_bus_' + name,
            (x + lo[0], y + lo[1], z + lo[2]),
            (x + hi[0], y + hi[1], z + hi[2]), material)

    def panel(name, points, material):
        meshes.append(dict(name='abandoned_bus_' + name,
                           vertices=[(x+a, y+b, z+c) for a,b,c in points],
                           faces=[(0,i,i+1) for i in range(1,len(points)-1)], material=material))

    def side_part(name, side, start, end, bottom, top, material, thickness=.024, inset=0):
        """Keep the livery and shell clear of the actual eastern door opening."""
        spans = [(start, end)] if side < 0 else [(start, min(end, entry_lo)),
                                                       (max(start, entry_hi), end)]
        for i, (a, b) in enumerate(spans):
            if b > a:
                sx = side * (width-inset)
                part(f'{name}_{side}_{i}', (sx-thickness/2, a, bottom),
                     (sx+thickness/2, b, top), material)

    def clip_y(points, boundary, keep_below):
        result = []
        for p, q in zip(points, points[1:] + points[:1]):
            inside = p[1] <= boundary if keep_below else p[1] >= boundary
            next_inside = q[1] <= boundary if keep_below else q[1] >= boundary
            if inside:
                result.append(p)
            if inside != next_inside:
                f = (boundary-p[1])/(q[1]-p[1])
                result.append(tuple(p[k]+f*(q[k]-p[k]) for k in range(3)))
        return result

    # The chassis is the walking floor; only the perimeter is solid above it.
    part('chassis', (-width, -half, .18), (width, half, .65), 'dark')
    part('floor', (-width+.10, -half+.10, .65), (width-.10, half-.10, .67), 'bus_floor')
    part('roof', (-width, -half, 2.82), (width, half, 3.12), 'bus_paint')
    part('roof_vent', (-.6, -.9, 3.12), (.6, .7, 3.24), 'dark')
    for side in (-1, 1):
        sx = side * width
        side_part('body', side, -half, half, .65, 1.62, 'bus_green', .18, .09)
        side_part('inner_liner', side, -half+.10, half-.10, .67, 1.59, 'bus_paint', .02, .19)
        side_part('window_sill', side, -half, half, 1.62, 1.78, 'dark', .12)
        part(f'window_header_{side}', (sx-.06, -half, 2.68), (sx+.06, half, 2.82), 'dark')
        # White belt and green mountain graphics inspired by the supplied city bus.
        side_part('white_belt', side, -half, half, 1.08, 1.62, 'bus_paint')
        for i in range(8):
            yy = -half + i * spec['length']/8
            end = yy + spec['length']/8
            peak = 1.32 + (.23 if i%3==0 else .08 if i%3==1 else 0)
            points = [(sx+side*.023,yy,.7), (sx+side*.023,end,.7),
                      (sx+side*.023,(yy+end)/2,peak)]
            if side < 0:points.reverse()
            polygons = [points] if side < 0 else [clip_y(points, entry_lo, True),
                                                          clip_y(points, entry_hi, False)]
            for j, polygon in enumerate(polygons):
                if len(polygon) >= 3 and max(p[1] for p in polygon)-min(p[1] for p in polygon) > 1e-8:
                    panel(f'mountain_{side}_{i}_{j}', polygon, 'bus_lime' if i%2 else 'bus_green')
        for i in range(7):
            yy = -half + .38 + i * 1.18
            # Two broken panes leave light and sightlines into the derelict cabin.
            side_part(f'window_{i}', side, yy, yy+1.02,
                      2.47 if i in (1, 4) else 1.78, 2.68, 'bus_glass', .05)
            side_part(f'window_post_{i}', side, yy-.12, yy, 1.78, 2.68, 'dark', .12)
            if i in (1,5):
                side_part(f'rust_{i}', side, yy, yy+.22, .68, .77, 'bus_rust', .07)
        side_part('rub_strip', side, -half, half, 1.59, 1.64, 'dark', .09)
        # Circular tyres around the X axle, tucked into the broadside shell.
        for axle, yy in enumerate((-half + 1.65, half - 1.55)):
            vertices = []
            for xx in (sx - .15, sx + .15):
                vertices.extend((x + xx, y + yy + .53 * math.cos(i * math.tau / 16),
                                 z + .53 + .53 * math.sin(i * math.tau / 16)) for i in range(16))
            faces = [(0, i + 1, i) for i in range(1, 15)]
            faces += [(16, 16 + i, 17 + i) for i in range(1, 15)]
            for i in range(16):
                j = (i + 1) % 16
                faces.extend(((i, j, 16 + j), (i, 16 + j, 16 + i)))
            meshes.append(dict(name=f'abandoned_bus_wheel_{side}_{axle}',
                               vertices=vertices, faces=faces, material='dark'))
            part(f'hub_{side}_{axle}', (sx - .17, yy - .21, .32),
                 (sx + .17, yy + .21, .74), 'bus_metal')
    for end in (-1, 1):
        yy = end * half
        part(f'end_body_{end}', (-width, yy-.06, .65),
             (width, yy+.06, 1.35 if end > 0 else 1.78), 'bus_green')
        for side in (-1, 1):
            sx = side * (width-.08)
            part(f'corner_post_{end}_{side}', (sx-.08, yy-.08, 1.35),
                 (sx+.08, yy+.08, 2.82), 'dark')
        part(f'bumper_{end}', (-width - .04, yy - .07, .42),
             (width + .04, yy + .07, .68), 'dark')
        part(f'end_glass_{end}', (-width + .16, yy - .025, 1.35 if end > 0 else 1.78),
             (width - .16, yy + .025, 2.64), 'bus_glass')
        for side in (-1, 1):
            sx = side * .88
            part(f'lamp_{end}_{side}', (sx - .16, yy - .04, .85),
                 (sx + .16, yy + .04, 1.04), 'car_red' if end < 0 else 'white')
    # Double leaves stand open against the jambs, with a full-height entrance.
    for i, yy in enumerate((entry_lo-.04, entry_hi+.04)):
        part(f'open_door_{i}_lower', (width, yy-.025, .68), (width+.62, yy+.025, 1.15), 'dark')
        part(f'open_door_{i}_glass', (width+.05, yy-.02, 1.15),
             (width+.57, yy+.02, 2.58), 'bus_glass')
        for j, xx in enumerate((width, width+.59)):
            part(f'open_door_{i}_upright_{j}', (xx, yy-.03, 1.15),
                 (xx+.03, yy+.03, 2.72), 'dark')
        part(f'open_door_{i}_top', (width, yy-.03, 2.58), (width+.62, yy+.03, 2.72), 'dark')
    for i in range(3):
        xx = width + (2-i)*.30
        top = (i+1)*.65/4
        part(f'entry_step_{i}', (xx, entry_lo, .04), (xx+.30, entry_hi, top), 'bus_floor')
        part(f'entry_step_edge_{i}', (xx+.27, entry_lo, top),
             (xx+.30, entry_hi, top+.006), 'bus_metal')

    # Narrow side seats leave a 1.2 m central aisle and a clear front vestibule.
    for side in (-1, 1):
        a, b = sorted((side*.65, side*1.10))
        for row, yy in enumerate((-3.65, -2.55, -1.45, -.35, .75)):
            if side == 1 and row == 4:
                continue  # Missing seat leaves the entry vestibule clear.
            part(f'seat_frame_{side}_{row}', (a+.04, yy, .67), (b-.04, yy+.46, .91), 'bus_rust')
            torn = (side, row) in ((1, 1), (-1, 3))
            part(f'seat_cushion_{side}_{row}', (a, yy, .91),
                 (b, yy+(.23 if torn else .48), 1.02), 'bus_seat')
            part(f'seat_back_{side}_{row}', (a, yy, 1.02), (b, yy+.10, 1.64), 'bus_seat')
            if torn:
                part(f'seat_exposed_foam_{side}_{row}', (a+.04, yy+.24, .92),
                     (b-.03, yy+.44, .97), 'white')
        sx = side*.77
        part(f'grab_pole_{side}', (sx-.025, entry_lo-.35, .67),
             (sx+.025, entry_lo-.30, 2.81), 'bus_metal')
        part(f'overhead_rail_{side}', (sx-.025, -half+.25, 2.60),
             (sx+.025, entry_lo-.30, 2.65), 'bus_metal')
    part('driver_seat', (-1.02, half-1.15, .80), (-.55, half-.67, 1.09), 'bus_seat')
    part('driver_back', (-1.02, half-1.15, 1.09), (-.55, half-1.04, 1.78), 'bus_seat')
    part('dashboard', (-width+.16, half-.44, 1.02), (width-.16, half-.10, 1.34), 'dark')
    # Flat dirt, discarded papers and small fragments stay below step height.
    for i, (xx, yy) in enumerate(((-.38,-3.0), (.31,-1.95), (-.27,-.75), (.25,.55), (-.35,1.75))):
        part(f'floor_dirt_{i}', (xx-.16, yy-.22, .6701), (xx+.16, yy+.22, .674), 'bus_rust')
        part(f'discarded_paper_{i}', (xx-.09, yy+.24, .674), (xx+.08, yy+.40, .678), 'white')
    part('fallen_seat_panel', (.76, -2.30, .67), (1.05, -1.73, .74), 'bus_seat')

    # Front is the +Y end, beside the entrance doors.
    part('destination_board', (-1.14, half+.03, 2.70), (1.14, half+.07, 3.04), 'dark')
    mask = destination_mask()
    pixels = mask.load()
    for row in range(mask.height):
        col = 0
        while col < mask.width:
            if pixels[col,row] < 100:
                col += 1
                continue
            start = col
            while col < mask.width and pixels[col,row] >= 100:col += 1
            # A viewer facing the front sees +X on the left. Preserve the accent.
            xhi = 1.07 - start * 2.14 / mask.width
            xlo = 1.07 - col * 2.14 / mask.width
            zhi = 2.965 - row * .19 / mask.height
            zlo = 2.965 - (row+1) * .19 / mask.height
            panel(f'destination_glyph_{row}_{start}',
                  [(xhi,half+.075,zhi),(xhi,half+.075,zlo),
                   (xlo,half+.075,zlo),(xlo,half+.075,zhi)], 'bus_led')
    for side in (-1,1):
        sx = side*(width+.16)
        part(f'mirror_arm_{side}', (min(sx,side*width)-.03,half-.28,2.52),
             (max(sx,side*width)+.03,half-.2,2.58), 'dark')
        part(f'mirror_{side}', (sx-.08,half-.28,2.12),(sx+.08,half-.15,2.62),'dark')
        panel(f'wiper_{side}', [(side*.12,half+.035,1.47),
                              (side*.15,half+.035,1.44),
                              (side*.88,half+.035,1.85),
                              (side*.85,half+.035,1.88)], 'dark')
