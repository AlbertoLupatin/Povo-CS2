#!/usr/bin/env python3
"""Put screenshots side by side in one labelled image, to compare views at a glance.

  contact_sheet.py out.jpg <columns> <cell width px> image...

Example: contact_sheet.py out/fix_grid.jpg 3 760 out/shots/F01_*.png
"""

import os
import sys

from PIL import Image, ImageDraw, ImageOps


def sheet(out, cols, width, files):
    ims = []
    for f in files:
        im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
        im.thumbnail((width, width))
        ims.append((os.path.basename(f), im))
    h = max(i.size[1] for _, i in ims)
    rows = (len(ims) + cols - 1) // cols
    grid = Image.new('RGB', (cols * width, rows * (h + 22)), 'white')
    draw = ImageDraw.Draw(grid)
    for k, (name, im) in enumerate(ims):
        x, y = (k % cols) * width, (k // cols) * (h + 22)
        grid.paste(im, (x, y + 22))
        draw.text((x + 4, y + 5), name, fill='black')
    grid.save(out, quality=85)
    return grid.size


if __name__ == '__main__':
    print(sheet(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]))
