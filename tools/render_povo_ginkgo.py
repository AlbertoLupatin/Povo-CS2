"""Render the authored ginkgo asset and a local roadside preview."""
from pathlib import Path
from PIL import Image, ImageDraw

try:
    from .povo_ginkgo import tree, height_for
    from .render_povo_exterior import perspective, font
except ImportError:
    from povo_ginkgo import tree, height_for
    from render_povo_exterior import perspective, font

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT/'exports/povo_campus/ginkgo'; out.mkdir(parents=True, exist_ok=True)
    boxes = [('ground', (-7, -6, -.2), (8, 5, 0), 'paving')]; meshes = []
    for i, x in enumerate((-3, 0, 3)):
        trunk, crown, _ = tree(f'povo1_front_tree_{i}', x, 0, 0, height_for(i))
        boxes.append(trunk); meshes.extend(crown)
    image = perspective(boxes, meshes, dict(position=[6,-10,4.0], target=[0,0,1.4], fov=49), 1500, 880)
    draw = ImageDraw.Draw(image)
    draw.text((35, 28), 'GINKGO BILOBA / ROADSIDE TREES', fill='#263b37', font=font(28))
    draw.text((35, 69), 'Young branching crowns / 2.65 - 2.95 m / green fan-shaped leaves', fill='#425d50', font=font(20))
    image.save(out/'tree_preview.png')
    trunk, crown, _ = tree('povo1_front_tree_0', 0, 0, 0, 2.8)
    image = perspective([('ground',(-2,-2,-.1),(2,2,0),'grass'),trunk], crown,
                        dict(position=[3,-4,2.1],target=[0,0,1.5],fov=42), 1000, 1100)
    image.save(out/'tree_detail.png')
    print(out)


if __name__ == '__main__':
    main()
