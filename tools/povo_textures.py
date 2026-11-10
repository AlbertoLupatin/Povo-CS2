"""Photo-matched surface textures adopted from RoanS77's remake (branch shaders-mod).

The remake (remake/tools/materials.py) paints a few surfaces no stock CS2
material matches as 1024 px tileable procedural textures, with colours sampled
by eye from the reference photos, and uses stock CS2 materials for the rest.
config/povo_textures.json chooses which campus OBJ materials take which:

- custom: one of the generators below, written next to the campus materials;
- stock:  a stock CS2 material, referenced directly by the ModelDoc remap.

Both kinds are drawn for one texture repeat per 1024 texels at 4 texels per
Hammer unit, which the remake shows at its 1.25 gameplay scale, i.e. about
5.2 real metres. This map is at real scale and its OBJ UVs are in metres, so
these materials get that repeat length instead of the 0.6 m used by the flat
finishes; slabs, tiles and boards then keep their real sizes.
Unlisted materials are unchanged.
"""

import json
import re
import struct
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np

try:
    from .povo_campus_finishes import write_png
except ImportError:
    from povo_campus_finishes import write_png

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'config/povo_textures.json'
PREFIX = 'materials/trento/povo/campus/textures/'
HAMMER_UNITS_PER_METRE = 39.37007874
DEFAULT_REPEAT_METRES = .6


@lru_cache(maxsize=8)
def _load(path, _mtime):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def settings(root=ROOT):
    path = Path(root) / CONFIG
    return _load(str(path), path.stat().st_mtime_ns)


def repeat_for_texels(texels, cfg=None):
    """Real metres covered by one repeat of a texture of this many texels."""
    cfg = cfg or settings()
    units = texels / cfg['texels_per_hammer_unit']
    return units / (HAMMER_UNITS_PER_METRE * cfg['remake_gameplay_scale'])


def repeat_metres(material, cfg=None):
    """Texture repeat length for one OBJ material ('campus_' prefix optional)."""
    cfg = cfg or settings()
    name = material.removeprefix('campus_')
    if name in cfg['custom']:
        return repeat_for_texels(cfg['texture_size_pixels'], cfg)
    if name in cfg['stock']:
        path = cfg['stock'][name]
        return repeat_for_texels(cfg['stock_texels'].get(path, cfg['texture_size_pixels']), cfg)
    return DEFAULT_REPEAT_METRES


def resolve(name, default, cfg=None):
    """Material source for a campus material name, or the given default."""
    cfg = cfg or settings()
    if name in cfg['stock']:
        return cfg['stock'][name]
    if name in cfg['custom']:
        return PREFIX + cfg['custom'][name] + '.vmat'
    return default


def renamed(name, material, cfg=None):
    """Render material for a named box or mesh after the configured renames.

    Renames give one part of a shared material its own finish (e.g. the Via
    Sommarive sidewalk out of all paving). Names and materials may carry the
    OBJ 'campus_' prefix; it is kept on the result.
    """
    cfg = cfg or settings()
    prefix = 'campus_' if material.startswith('campus_') else ''
    bare = material.removeprefix(prefix)
    for rule in cfg.get('renames', []):
        if bare == rule['material'] and re.search(rule['names'], name.removeprefix('backdrop_')):
            return prefix + rule['to']
    return material


def edge_trees_enabled(cfg=None):
    cfg = cfg or settings()
    return bool(cfg.get('edge_trees', {}).get('enabled'))


def edge_tree(ident, point, height, cfg=None):
    """One stock tree prop for a scenery tree: model by height band, fixed yaw.

    The model and yaw follow the remake's deterministic choice from position.
    """
    cfg = cfg or settings()
    bands = cfg['edge_trees']['bands']
    models = next((b['models'] for b in bands if height <= b['max_height_metres']), bands[-1]['models'])
    x, y = point[0], point[1]
    return dict(id=ident, point=[round(v, 4) for v in point], height_metres=round(height, 4),
                model=models[int(abs(x) * 7 + abs(y) * 13) % len(models)],
                yaw=int(abs(x) * 37 + abs(y) * 11) % 360)


def facade_frames(boxes, cfg=None):
    """Outline of each configured facade: [(pattern, wall, outside, bounds)].

    A rule names the boxes of a building's perimeter walls (a regex) and their
    material; their faces towards the outside take the facade material instead.
    """
    cfg = cfg or settings()
    frames = []
    for rule in cfg.get('facades', []):
        pattern = re.compile(rule['boxes'])
        hits = [(lo, hi) for name, lo, hi, material in boxes
                if material == rule['material'] and pattern.search(name)]
        if hits:
            bounds = (min(lo[0] for lo, _ in hits), min(lo[1] for lo, _ in hits),
                      max(hi[0] for _, hi in hits), max(hi[1] for _, hi in hits))
            frames.append((pattern, rule['material'], rule['outside'], bounds))
    return frames


def face_material(name, material, lo, hi, points, frames, cfg=None):
    """Facade material for a wall box's outside face, else the box material.

    The outside face is the one across the wall's thickness that looks towards
    the nearest edge of the building outline. Ends, reveals, tops and the inside
    keep the wall material.
    """
    material = renamed(name, material, cfg)
    for pattern, wall, outside, bounds in frames:
        if material != wall or not pattern.search(name):
            continue
        centre = [(lo[i] + hi[i]) / 2 for i in range(2)]
        gaps = {(0, -1): centre[0] - bounds[0], (0, 1): bounds[2] - centre[0],
                (1, -1): centre[1] - bounds[1], (1, 1): bounds[3] - centre[1]}
        axis, side = min(gaps, key=gaps.get)
        a, b, c = points[:3]
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = sum(n * n for n in normal) ** .5
        return outside if length and normal[axis] * side > .99 * length else material
    return material


# --- Procedural textures (ported from remake/tools/materials.py) -------------
# Same recipes and photo-sampled colours. The value noise is made exactly
# periodic here (the remake's resize was "close enough" to tile), and each
# texture has its own seed so adding one never changes another.

def noise(rng, size, scale, octaves=4):
    """Tileable value noise in [0, 1]."""
    out = np.zeros((size, size))
    amp, total = 1., 0.
    for o in range(octaves):
        n = max(2, int(scale * 2 ** o))
        grid = rng.random((n, n))
        t = np.arange(size) * n / size
        i0 = np.floor(t).astype(int) % n
        i1 = (i0 + 1) % n
        f = t - np.floor(t)
        f = f * f * (3 - 2 * f)
        rows = grid[i0] * (1 - f)[:, None] + grid[i1] * f[:, None]
        out += amp * (rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :])
        total += amp
        amp *= .5
    return out / total


def solid(rgb, rng, size, var=.04, scale=8):
    n = noise(rng, size, scale)[..., None]
    return np.clip(np.array(rgb, float)[None, None] * (1 - var + 2 * var * n), 0, 255)


def red_floor(rng, size):
    """Povo 1 stairwells (P007, P040-P045): red rubber flooring."""
    return solid((142, 38, 34), rng, size, .05, 6)


def red_paving(rng, size):
    """Sunken entrance plaza and street stairs (P055-P060)."""
    img = solid((160, 70, 58), rng, size, .10, 12)
    img[rng.random((size, size)) > .985] *= .75
    return img


def dark_paving(rng, size):
    """Via Sommarive sidewalk: dark grey concrete with fine grit."""
    img = solid((92, 94, 96), rng, size, .08, 10)
    img[rng.random((size, size)) > .97] *= .8
    return img


def terrazzo(rng, size):
    """Corridor floors (P036-P039): light grey with dark and white chips."""
    img = solid((206, 204, 198), rng, size, .03, 4)
    for colour, density, chip in (((90, 90, 92), .006, 3), ((245, 245, 240), .010, 2),
                                  ((150, 140, 128), .004, 4)):
        ys, xs = np.nonzero(rng.random((size, size)) < density)
        for dy in range(chip):
            for dx in range(chip):
                img[(ys + dy) % size, (xs + dx) % size] = colour
    return img


def beige_stone(rng, size):
    """Povo 1 facades (P013, P024, P057): cream slabs, 4 x 8 per repeat."""
    img = solid((214, 199, 168), rng, size, .05, 10)
    w, h = size // 4, size // 8
    for i in range(4):          # each slab slightly different, like natural stone
        for j in range(8):
            img[j * h:(j + 1) * h, i * w:(i + 1) * w] *= 1 + rng.uniform(-.035, .035)
    joint = (150, 138, 116)
    for i in range(4):
        img[:, i * w:i * w + 3] = joint
    for j in range(8):
        img[j * h:j * h + 3, :] = joint
    return img


def cream_tile(rng, size):
    """Povo 2 floors (P074-P114): cream 40 cm ceramic tiles, 13 per repeat."""
    img = solid((222, 214, 196), rng, size, .03, 6)
    step = size / 13
    for k in range(13):
        a = int(round(k * step))
        img[:, a:a + 2] = (190, 184, 170)
        img[a:a + 2, :] = (190, 184, 170)
    return img


def frosted_glass(rng, size):
    """Povo 2 street volumes (P010, P065, P067): milky green panels, 1.3 x 2.6 m."""
    img = solid((176, 204, 198), rng, size, .04, 3)
    w, h = size // 4, size // 2
    for i in range(4):
        img[:, i * w:i * w + 4] = (120, 140, 138)
    for j in range(2):
        img[j * h:j * h + 4, :] = (120, 140, 138)
    return img


def anthracite(rng, size):
    """Fire doors and door frames (P040, P041, P045)."""
    return solid((62, 64, 68), rng, size, .03, 6)


def aluminium(rng, size):
    """Curtain-wall mullions and transoms (P002, P005)."""
    return solid((158, 162, 166), rng, size, .03, 6)


TEXTURES = {  # name: (generator, seed, roughness 0-255, metalness, physics surface)
    'red_floor': (red_floor, 1, 150, 0, 'rubber'),
    'red_paving': (red_paving, 2, 200, 0, 'concrete'),
    'dark_paving': (dark_paving, 3, 210, 0, 'concrete'),
    'terrazzo': (terrazzo, 4, 90, 0, 'tile'),
    'beige_stone': (beige_stone, 5, 190, 0, 'concrete'),
    'cream_tile': (cream_tile, 6, 70, 0, 'tile'),
    'frosted_glass': (frosted_glass, 7, 40, 0, 'glass'),
    'anthracite': (anthracite, 8, 110, 1, 'metal'),
    # Retain the remake's brushed colour/roughness. Fully metallic ModelDoc
    # frames render black without Hammer's reflection setup in this addon;
    # a diffuse contribution keeps the photographed silver finish readable.
    'aluminium': (aluminium, 9, 80, .25, 'metal'),
}


# Glass that stays see-through: the campus's tested translucent glass setup
# (povo_exterior_materials), at the opacity of its frosted entrance glass.
TRANSLUCENT = {'frosted_glass': .84}


def image(name, size):
    generator, seed = TEXTURES[name][:2]
    return np.clip(np.rint(generator(np.random.default_rng(seed), size)), 0, 255).astype(np.uint8)


def encode_png(pixels):
    """Deterministic RGB PNG, independent of the installed imaging library."""
    height, width, _ = pixels.shape
    raw = b''.join(b'\0' + pixels[y].tobytes() for y in range(height))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def vmat(name):
    _gen, _seed, _rough, metal, surface = TEXTURES[name]
    if name in TRANSLUCENT:
        return ('Layer0\n{\n    shader "csgo_lightmappedgeneric.vfx"\n'
                '    F_TRANSLUCENT "1"\n    F_RENDER_BACKFACES "1"\n'
                f'    g_flOpacityScale "{TRANSLUCENT[name]}"\n'
                f'    TextureLayer1Color "{PREFIX}{name}.png"\n'
                f'    TextureLayer1Normal "{PREFIX}flat_normal.png"\n'
                f'    TextureLayer1Roughness "{PREFIX}{name}_rough.png"\n'
                f'    TextureLayer1Translucency "{PREFIX}opaque_mask.png"\n'
                '    g_vColorTint "[1 1 1 0]"\n'
                f'    SystemAttributes {{ PhysicsSurfaceProperties "{surface}" }}\n}}\n')
    return ('Layer0\n{\n    shader "csgo_complex.vfx"\n'
            f'    TextureColor "{PREFIX}{name}.png"\n'
            f'    TextureNormal "{PREFIX}flat_normal.png"\n'
            f'    TextureRoughness "{PREFIX}{name}_rough.png"\n'
            '    F_METALNESS_TEXTURE 0\n'
            f'    g_flMetalness "{metal}"\n'
            '    g_vColorTint "[1 1 1 0]"\n'
            f'    SystemAttributes {{ PhysicsSurfaceProperties "{surface}" }}\n}}\n')


def write_textures(directory, root=ROOT):
    """Write the custom textures in use; return their names."""
    cfg = settings(root)
    used = sorted(set(cfg['custom'].values()))
    directory.mkdir(parents=True, exist_ok=True)
    flat = lambda rgb: encode_png(np.full((256, 256, 3), rgb, np.uint8))
    write_png(directory / 'flat_normal.png', flat((128, 128, 255)))
    if TRANSLUCENT.keys() & set(used):
        write_png(directory / 'opaque_mask.png', flat((255, 255, 255)))
    for name in used:
        write_png(directory / (name + '.png'), encode_png(image(name, cfg['texture_size_pixels'])))
        # A tiny greyscale roughness map is ignored and the surface turns
        # mirror-like (remake); use a full-size RGB map.
        write_png(directory / (name + '_rough.png'), flat((TEXTURES[name][2],) * 3))
        text = vmat(name)
        path = directory / (name + '.vmat')
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')
    return used


if __name__ == '__main__':
    out = ROOT / 'cs2/content/trento_povo' / PREFIX
    print('wrote', ', '.join(write_textures(out)), 'to', out)
