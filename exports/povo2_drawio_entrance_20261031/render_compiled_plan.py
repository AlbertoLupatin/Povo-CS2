"""Render the packaged static collision, with verified stair support samples."""
from pathlib import Path
import hashlib
import json
import re
import struct

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
WORK = ROOT / 'build/drawio-compiled-review'


def main():
    report = json.loads((OUT / 'compiled-layout-check.json').read_text())
    assert report['status'] == 'passed'
    data = (WORK / 'physics.txt').read_text(encoding='utf-8-sig')
    vertices = re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]', data, re.S)
    indices = re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]', data, re.S)
    assert vertices and len(vertices) == len(indices)
    triangles = []
    units = 39.37007874
    for vb, ib in zip(vertices, indices):
        vv = [(y / units, z / units, x / units)
              for x, y, z in struct.iter_unpack('<fff', bytes.fromhex(vb))]
        triangles.extend([[vv[i] for i in f]
                          for f in struct.iter_unpack('<III', bytes.fromhex(ib))])

    bounds = (8, -7, 46, 29)
    scale, left, top = 23, 75, 130
    image = Image.new('RGB', (1040, 1080), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    title = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 26)

    def pt(p):
        return left + (p[0] - bounds[0]) * scale, top + (bounds[3] - p[1]) * scale

    def local(face):
        return not (max(p[0] for p in face) < bounds[0]
                    or min(p[0] for p in face) > bounds[2]
                    or max(p[1] for p in face) < bounds[1]
                    or min(p[1] for p in face) > bounds[3])

    for face in triangles:
        if not local(face):
            continue
        for height, color in ((.4, '#e3edef'), (-3.2, '#e7f2e9')):
            if all(abs(p[2] - height) < .015 for p in face):
                draw.polygon([pt(p) for p in face], fill=color)
    for x in range(10, 46, 5):
        draw.line([pt((x, bounds[1])), pt((x, bounds[3]))], fill='#dce5e7')
    for y in range(-5, 30, 5):
        draw.line([pt((bounds[0], y)), pt((bounds[2], y))], fill='#dce5e7')
    segments = 0
    for face in triangles:
        if not local(face) or not min(p[2] for p in face) < 1.5 < max(p[2] for p in face):
            continue
        hits = []
        for a, b in zip(face, face[1:] + face[:1]):
            if (a[2] - 1.5) * (b[2] - 1.5) < 0:
                t = (1.5 - a[2]) / (b[2] - a[2])
                hits.append(tuple(a[k] + t * (b[k] - a[k]) for k in (0, 1)))
        if len(hits) == 2:
            draw.line([pt(p) for p in hits], fill='#243f49', width=2)
            segments += 1
    for prefix in ('up_support_', 'down_support_'):
        points = [pt(c['point']) for c in report['checks'] if c['name'].startswith(prefix)]
        draw.line(points, fill='#32824e', width=2)
        for x, y in points:
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill='#32824e')

    # Crop the actual PHYS plot before adding page furniture.
    corner = pt((bounds[2], bounds[1]))
    plot = image.crop((left, top, *corner))
    image.paste('white', (0, 0, image.width, image.height))
    image.paste(plot, (left, top))
    draw = ImageDraw.Draw(image)
    draw.rectangle((left, top, *corner), outline='#93a8ae')
    draw.text((28, 22), 'POVO 2 -1 / PACKAGED DRAW.IO ENTRANCE', font=title, fill='#193943')
    draw.text((28, 65), 'Actual static collision: wall section at z = 1.5 m; floor levels 0.4 / -3.2 m.', font=font, fill='#48616b')
    draw.text((28, 94), 'Green points: stair and landing support checked in the packaged model. North is up.', font=font, fill='#48616b')

    def label(text, point):
        x, y = pt(point)
        bb = draw.textbbox((0, 0), text, font=font)
        w = bb[2]
        draw.rectangle((x - w / 2 - 3, y - 10, x + w / 2 + 3, y + 11), fill='white')
        draw.text((x - w / 2, y - 10), text, font=font, fill='#193943')

    for text, point in [('MAIN STAIR', (15.7, 23.2)), ('C7', (15, 16.6)),
                        ('WI1', (13, 9.3)), ('C5', (21.8, 12.1)),
                        ('E1', (27.4, 14)), ('E2', (27.4, 7)),
                        ('Sealed end', (26, 21.08)), ('TERRACE', (15, 1.15)),
                        ('UP', (19, -3)), ('DOWN', (36.6, -1.3)),
                        ('Lower approach', (40.8, 5.6))]:
        label(text, point)
    for x in range(10, 46, 5):
        a = pt((x, bounds[1])); draw.text((a[0] - 8, a[1] + 8), str(x), font=small, fill='#48616b')
    for y in range(-5, 30, 5):
        a = pt((bounds[0], y)); draw.text((a[0] - 32, a[1] - 8), str(y), font=small, fill='#48616b')
    draw.text((28, 1005), 'Static PHYS only; movable doors and render-only glazing are excluded. Local metres.', font=font, fill='#48616b')
    draw.text((28, 1037), 'Package SHA-256: ' + report['package_sha256'][:20] + '…  |  Labels from source metadata.', font=font, fill='#48616b')
    image.save(OUT / 'compiled_plan.png')
    (OUT / 'compiled_plan.json').write_text(json.dumps(dict(
        package_sha256=report['package_sha256'], model_sha256=report['model_sha256'],
        physics_dump_sha256=hashlib.sha256((WORK / 'physics.txt').read_bytes()).hexdigest(),
        bounds=bounds, section_height=1.5, wall_segments=segments,
        limitations='Static collision; movable doors and render-only details excluded'), indent=2) + '\n')
    print(OUT / 'compiled_plan.png')


if __name__ == '__main__':
    main()
