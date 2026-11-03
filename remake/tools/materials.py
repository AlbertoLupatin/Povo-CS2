#!/usr/bin/env python3
"""Procedural custom materials for surfaces no stock CS2 material matches.

Each material is a 1024 px tileable colour texture (one repeat = 256 Hammer units,
the vmap_mesh texture scale) plus a csgo_complex .vmat, written into the addon's
content tree. Colours are sampled by eye from the reference photos:
- red_floor   Povo 1 stairwells (P007, P040-P045): red rubber flooring
- red_paving  sunken entrance plaza and street stairs (P055-P060)
- dark_paving the street sidewalk along Via Sommarive
- terrazzo    corridor floors (P036-P039, 28-3): light grey with dark and white chips
- beige_stone Povo 1 upper facades (P013, P024, P057): cream slabs, 4 x 8 per repeat
- anthracite  fire doors, door frames (P040, P041, P045)
- aluminium   curtain-wall mullions and transoms (P002, P005, 27-5)
Usage: materials.py   (rewrites all; the map compile builds them)
"""

from pathlib import Path

import numpy as np
from PIL import Image

from vmap_build import CS2, ADDON

SIZE = 1024
OUT = CS2 / 'content/csgo_addons' / ADDON / 'materials/povo'


def noise(rng, scale, octaves=4):
    """Tileable value noise in [0, 1]."""
    out = np.zeros((SIZE, SIZE))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = max(2, int(scale * 2 ** o))
        grid = rng.random((n, n))
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
        # Wrap: resize of a periodic grid is close enough to tile at these scales.
        out += amp * np.asarray(img, float) / 255
        total += amp
        amp *= .5
    return out / total


def solid(rgb, rng, var=.04, scale=8):
    n = noise(rng, scale)[..., None]
    return np.clip(np.array(rgb, float)[None, None] * (1 - var + 2 * var * n), 0, 255)


def red_floor(rng):
    return solid((142, 38, 34), rng, .05, 6)


def red_paving(rng):
    img = solid((160, 70, 58), rng, .10, 12)
    chips = rng.random((SIZE, SIZE)) > .985
    img[chips] *= .75
    return img


def dark_paving(rng):
    """Street sidewalk along Via Sommarive: dark grey concrete with fine grit (user, 23-10 25-28)."""
    img = solid((92, 94, 96), rng, .08, 10)
    grit = rng.random((SIZE, SIZE)) > .97
    img[grit] *= .8
    return img


def terrazzo(rng):
    img = solid((206, 204, 198), rng, .03, 4)
    for colour, density, size in (((90, 90, 92), .006, 3), ((245, 245, 240), .010, 2), ((150, 140, 128), .004, 4)):
        ys, xs = np.nonzero(rng.random((SIZE, SIZE)) < density)
        for dy in range(size):
            for dx in range(size):
                img[(ys + dy) % SIZE, (xs + dx) % SIZE] = colour
    return img


def beige_stone(rng):
    img = solid((214, 199, 168), rng, .05, 10)
    w, h = SIZE // 4, SIZE // 8
    for i in range(4):     # each slab slightly different, like natural stone
        for j in range(8):
            img[j * h:(j + 1) * h, i * w:(i + 1) * w] *= 1 + rng.uniform(-.035, .035)
    joint = (150, 138, 116)
    for i in range(4):
        img[:, i * w:i * w + 3] = joint
    for j in range(8):
        img[j * h:j * h + 3, :] = joint
    return img


def cream_tile(rng):
    """Povo 2 floors (P074-P114): cream 40 cm ceramic tiles, 13 per repeat, light grout."""
    img = solid((222, 214, 196), rng, .03, 6)
    step = SIZE / 13
    for k in range(13):
        a = int(round(k * step))
        img[:, a:a + 2] = (190, 184, 170)
        img[a:a + 2, :] = (190, 184, 170)
    return img


def frosted_glass(rng):
    """Povo 2 street volumes (P010, P065, P067): milky green frosted panels, 1.3 x 2.6 m."""
    img = solid((176, 204, 198), rng, .04, 3)
    w, h = SIZE // 4, SIZE // 2
    for i in range(4):
        img[:, i * w:i * w + 4] = (120, 140, 138)
    for j in range(2):
        img[j * h:j * h + 4, :] = (120, 140, 138)
    return img


def anthracite(rng):
    return solid((62, 64, 68), rng, .03, 6)


def aluminium(rng):
    return solid((158, 162, 166), rng, .03, 6)


MATERIALS = {  # name: (generator, roughness 0-255, metalness, physics surface)
    'red_floor': (red_floor, 150, 0, 'rubber'),
    'red_paving': (red_paving, 200, 0, 'concrete'),
    'terrazzo': (terrazzo, 90, 0, 'tile'),
    'dark_paving': (dark_paving, 210, 0, 'concrete'),
    'beige_stone': (beige_stone, 190, 0, 'concrete'),
    'cream_tile': (cream_tile, 70, 0, 'tile'),
    'frosted_glass': (frosted_glass, 40, 0, 'glass'),
    'anthracite': (anthracite, 110, 1, 'metal'),
    'aluminium': (aluminium, 80, 1, 'metal'),
}


def write_all():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    Image.new('RGB', (256, 256), (128, 128, 255)).save(OUT / 'flat_normal.png')
    for name, (gen, rough, metal, surface) in MATERIALS.items():
        Image.fromarray(gen(rng).astype(np.uint8)).save(OUT / f'{name}.png')
        # A tiny greyscale map is ignored and the surface turns mirror-like; use a full RGB map.
        Image.new('RGB', (256, 256), (rough, rough, rough)).save(OUT / f'{name}_rough.png')
        (OUT / f'{name}.vmat').write_text(f'''Layer0
{{
    shader "csgo_complex.vfx"
    TextureColor "materials/povo/{name}.png"
    TextureNormal "materials/povo/flat_normal.png"
    TextureRoughness "materials/povo/{name}_rough.png"
    F_METALNESS_TEXTURE 0
    g_flMetalness "{metal}"
    g_vColorTint "[1 1 1 0]"
    SystemAttributes {{ PhysicsSurfaceProperties "{surface}" }}
}}
''')
    print('wrote', len(MATERIALS), 'materials to', OUT)


if __name__ == '__main__':
    write_all()
