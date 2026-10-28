"""Generated wall slices beside the photographed plans, for the second audit pass.

Each sheet puts a top-down cut of the generated walls (1.5 m above the floor)
next to the plan photo, rotated into the same orientation. Plans are scaled
to fill their panel; this is a visual comparison, not a registration.
"""
from pathlib import Path
import sys
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT/'tools'))
import build_povo_campus

ARCHIVE = ROOT/'data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300'
FURNITURE = ('seat', 'desk', 'office', 'canteen', 'sanitary', 'teaching', 'projection')
GLASS = {'window_glass', 'exterior_glass', 'exterior_entry_glass'}


def slice_image(boxes, rooms, z, bounds, scale):
    x0, x1, y0, y1 = bounds
    im = Image.new('RGB', (int((y1-y0)*scale), int((x1-x0)*scale)), 'white')
    d = ImageDraw.Draw(im)
    def point(x, y): return ((y-y0)*scale, (x-x0)*scale)
    def rect(lo, hi, **kw):
        a, c = point(lo[0], lo[1]), point(hi[0], hi[1])
        d.rectangle((min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1])), **kw)
    for name, lo, hi, material in boxes:
        if abs(hi[2]-(z-1.5)) < .25 and hi[2]-lo[2] < .6 and ('floor' in material or 'terrace' in material):
            rect(lo, hi, fill='#e8eef8')
    for name, lo, hi, material in boxes:
        if not lo[2] <= z <= hi[2]:
            continue
        colour = ('#aaa' if material.startswith(FURNITURE) else '#2a9ad8' if material in GLASS
                  else '#c84000' if 'stair' in name or 'elevator' in name else 'black')
        rect(lo, hi, fill=colour)
    for room in rooms:
        f = room.get('footprint_local_metres')
        if f:
            rect(f[:2], f[2:], outline='#0a8a0a', width=1)
            a, c = point(f[0], f[1]), point(f[2], f[3])
            d.text((min(a[0], c[0])+4, min(a[1], c[1])+4), f"{room['label']}\n{room['kind']}", fill='#066')
    return im


def plan_image(number, crop, rotate):
    photo = ImageOps.exif_transpose(Image.open(ARCHIVE/f'image{number:05}.jpeg'))
    k = photo.width/1200 if photo.width < photo.height else photo.width/1600
    photo = photo.crop(tuple(int(v*k) for v in crop))
    return photo.rotate(rotate, expand=True) if rotate else photo


def sheet(name, generated, plan, caption):
    width = 1600
    generated = generated.resize((width, round(generated.height*width/generated.width)))
    plan = plan.resize((width, round(plan.height*width/plan.width)))
    out = Image.new('RGB', (width, generated.height+plan.height+60), 'white')
    d = ImageDraw.Draw(out)
    d.text((8, 6), 'Generated walls, 1.5 m above floor (green = room metadata, blue = glass, orange = stairs/lift)', fill='black')
    out.paste(generated, (0, 24))
    d.text((8, generated.height+32), caption, fill='black')
    out.paste(plan, (0, generated.height+54))
    out.save(OUT/name, quality=90)


settings, config, boxes, levels, stair = build_povo_campus.build_geometry(ROOT)
rooms = {level['id']: level['rooms'] for level in levels}
povo1 = (-24.5, 25.5, -104.5, -18.5)
sheet('floor-1_vs_plan17.jpg', slice_image(boxes, rooms['academic_ground'], 5.5, povo1, 16),
      plan_image(17, (150, 150, 960, 1500), -90), '27 Oct photo 17 (Povo 1 floor -1), rotated 90 degrees clockwise')
sheet('floor0_vs_plan19.jpg', slice_image(boxes, rooms['academic_first'], 9.1, povo1, 16),
      plan_image(19, (130, 330, 1400, 1070), 0), '27 Oct photo 19 (Povo 1 floor 0)')
sheet('floor+1_vs_plan22.jpg', slice_image(boxes, rooms['academic_upper'], 12.7, povo1, 16),
      plan_image(22, (205, 175, 985, 1490), -90), '27 Oct photo 22 (Povo 1 floor +1), rotated 90 degrees clockwise')
sheet('library0_vs_plan15.jpg', slice_image(boxes, [], 5.5, (35, 53, -70, -12), 24),
      plan_image(15, (270, 115, 730, 1530), -90), '27 Oct photo 15 (library local 0), rotated 90 degrees clockwise')
sheet('canteen0_vs_plan13.jpg', slice_image(boxes, [], 5.5, (35, 53, -111, -76), 30),
      plan_image(13, (55, 330, 1260, 800), 180), '27 Oct photo 13 (canteen local 0), rotated 180 degrees')
sheet('canteen1_vs_plan12.jpg', slice_image(boxes, [], 9.1, (35, 53, -111, -76), 30),
      plan_image(12, (295, 110, 870, 1510), 90),
      '27 Oct photo 12 (canteen local 1), rotated 90 degrees anticlockwise: bar end left, exit-door side at the bottom (street side, x=52)')
sheet('library1_slice.jpg', slice_image(boxes, [], 9.1, (35, 53, -70, -12), 24),
      plan_image(16, (440, 500, 900, 1280), 0), '27 Oct photo 16 (library directory): floor 1 has two reading rooms and group-study rooms')
print('Saved seven generated-versus-plan sheets.')
