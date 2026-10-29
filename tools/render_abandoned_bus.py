"""Render the bus placement from current campus source without running CS2."""
from PIL import Image, ImageDraw

try:
    from .build_povo_campus import build_geometry
    from .build_povo_exterior import ROOT, build
    from .render_povo_exterior import perspective, font
except ImportError:
    from build_povo_campus import build_geometry
    from build_povo_exterior import ROOT, build
    from render_povo_exterior import perspective, font


def main():
    geometry = build_geometry()
    _, _, boxes, levels, _ = geometry
    exterior, meshes, _, _ = build(campus_geometry=geometry)
    selected = [b for b in exterior if b[0].startswith(('abandoned_bus_', 'bridge_'))]
    meshes = [m for m in meshes if m['name'].startswith(('road_', 'footway_', 'abandoned_bus_'))]
    view = perspective(selected, meshes,
                       dict(position=[35, 9, 8.5], target=[24.5, -4, 5.7], fov=66), 1050, 680)
    image = Image.new('RGB', (1500, 790), '#edf0ec')
    image.paste(view, (20, 85))
    d = ImageDraw.Draw(image)
    d.text((25, 20), 'Abandoned bus / east approach to the bridge', font=font(28), fill='#243d43')
    d.text((25, 57), 'Placement detail (surrounding buildings hidden) / 9 m bus across the road and footways',
           font=font(18), fill='#526468')
    left, top, scale = 1100, 170, 19
    def pt(x, y):
        return left + (x - 13) * scale, top + (14 - y) * scale
    def rect(a, b, c, e, fill):
        d.rectangle((*pt(a, e), *pt(c, b)), fill=fill)
    rect(13, -20, 32, 14, '#c3c7b7')
    rect(13, -9.4, 32, -.6, '#bcb8a9')
    rect(13, -8, 32, -2, '#666c6e')
    bridge = next(l['connection']['bridge'] for l in levels if l.get('connection'))
    rect(*bridge, '#799da3')
    rect(23.75, -9.5, 26.25, -.5, '#dadfd7')
    d.text((1100, 105), 'Placement / north up', font=font(21), fill='#243d43')
    d.text(pt(16, 12), 'BRIDGE', font=font(14), fill='#243d43')
    d.text((1100, 760), 'Bus is east of the bridge', font=font(19), fill='#243d43')
    out = ROOT / 'exports/povo_campus/abandoned_bus_review.png'
    image.save(out)
    print(out)
    # A larger front detail makes the actual mesh lettering reviewable.
    detail = Image.new('RGB', (1500,790), '#edf0ec')
    detail.paste(view, (20,85))
    front = perspective([b for b in exterior if b[0].startswith('abandoned_bus_')],
                        [m for m in meshes if m['name'].startswith('abandoned_bus_')],
                        dict(position=[26,5,6.6],target=[25,-.5,5.95],fov=36),410,560)
    detail.paste(front,(1080,150))
    dd=ImageDraw.Draw(detail)
    dd.text((25,20),'Povo bus / reference-inspired white and green livery',font=font(28),fill='#243d43')
    dd.text((25,57),'Source geometry preview / destination: 5/ Università di Povo',font=font(20),fill='#526468')
    dd.text((1080,105),'Front destination display',font=font(22),fill='#243d43')
    detail_out=ROOT/'exports/povo_campus/abandoned_bus_livery_review.png'
    detail.save(detail_out)
    print(detail_out)

    bus_boxes = [b for b in exterior if b[0].startswith('abandoned_bus_')]
    bus_meshes = [m for m in meshes if m['name'].startswith('abandoned_bus_')]
    review = Image.new('RGB', (1500, 1160), '#edf0ec')
    draw = ImageDraw.Draw(review)
    draw.text((25, 20), 'Open abandoned bus / preserved exterior livery', font=font(28), fill='#243d43')
    draw.text((25, 60), 'Source geometry preview / open doors, worn seating and clear central aisle', font=font(20), fill='#526468')
    views = [
        ('Exterior / original mountain graphics', dict(position=[35,9,8.5], target=[25,-4,5.7], fov=66)),
        ('Entrance / doors parked open', dict(position=[29,-2.8,6.4], target=[25.2,-3.475,5.6], fov=65)),
        ('Inside / looking towards the rear', dict(position=[25,-2.05,6.27], target=[25,-7,5.7], fov=82)),
        ('Inside / looking towards the open entrance', dict(position=[25,-7.7,6.27], target=[25.25,-1.8,5.9], fov=82)),
    ]
    for i, (title, camera) in enumerate(views):
        left, top = 15+(i%2)*745, 115+(i//2)*515
        draw.text((left+10, top), title, font=font(21), fill='#243d43')
        review.paste(perspective(bus_boxes, bus_meshes, camera, 730, 470), (left, top+32))
    draw.text((25, 1130), 'Full roof and walls shown in every view. Offline source review; native engine traversal remains to be checked.',
              font=font(17), fill='#526468')
    review_out = ROOT/'exports/povo_campus/abandoned_bus_open_review.png'
    review.save(review_out)
    print(review_out)


if __name__ == '__main__':
    main()
