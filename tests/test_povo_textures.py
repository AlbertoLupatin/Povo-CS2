import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from tools import povo_textures as textures
from tools.build_povo_campus import material_path, render_obj
from tools.povo_pavement_lighting import write_assets

ROOT = Path(__file__).resolve().parents[1]
INSTALLED = ROOT / 'cs2/content/trento_povo' / textures.PREFIX


def uv_metres(obj):
    """Metres of geometry per UV unit, per material, from axis-aligned edges."""
    vertices, uvs, ratios, material = [], [], {}, None
    for line in obj.splitlines():
        if line.startswith('v '):
            vertices.append(tuple(map(float, line.split()[1:])))
        elif line.startswith('vt '):
            uvs.append(tuple(map(float, line.split()[1:])))
        elif line.startswith('usemtl '):
            material = line.split()[1]
        elif line.startswith('f '):
            refs = [tuple(int(x) for x in r.split('/')[:2]) for r in line.split()[1:]]
            for (va, ta), (vb, tb) in zip(refs, refs[1:] + refs[:1]):
                length = np.linalg.norm(np.subtract(vertices[va - 1], vertices[vb - 1]))
                span = np.linalg.norm(np.subtract(uvs[ta - 1], uvs[tb - 1]))
                if length > 1e-6 and span > 1e-9:
                    ratios.setdefault(material, set()).add(round(length / span, 4))
    return ratios


class TextureSettingsTests(unittest.TestCase):
    def test_repeat_matches_the_remake_at_real_scale(self):
        # 1024 texels at 4 per Hammer unit, shown at the remake's 1.25 scale.
        self.assertAlmostEqual(textures.repeat_metres('campus_exterior_stone'), 256 / (39.37007874 * 1.25))
        self.assertAlmostEqual(textures.repeat_metres('exterior_asphalt'), 5.2019, places=4)
        self.assertAlmostEqual(textures.repeat_metres('campus_ceiling_panel'), 2.6010, places=4)
        self.assertEqual(textures.repeat_metres('campus_window_frame'), .6)
        self.assertEqual(textures.repeat_metres('campus_snow'), .6)

    def test_mapping_names_known_materials_and_generators(self):
        cfg = textures.settings()
        self.assertFalse(set(cfg['custom']) & set(cfg['stock']))
        self.assertLessEqual(set(cfg['custom'].values()), set(textures.TEXTURES))
        for path in cfg['stock'].values():
            self.assertRegex(path, r'^materials/[a-z0-9_/]+\.vmat$')
            self.assertFalse(path.startswith('materials/trento/'))

    def test_campus_material_paths_follow_the_mapping(self):
        self.assertEqual(material_path('stair_red'), textures.PREFIX + 'red_floor.vmat')
        self.assertEqual(material_path('exterior_grass'), 'materials/de_overpass/nature/wild_grass_1.vmat')
        self.assertEqual(material_path('exterior_fence'), 'materials/trento/povo/campus/exterior/fence.vmat')
        self.assertEqual(material_path('window_glass'), 'materials/trento/povo/campus/window_glass.vmat')
        self.assertEqual(material_path('metal_dark'), 'materials/trento/povo/campus/metal_dark.vmat')


class TextureImageTests(unittest.TestCase):
    def test_generators_are_deterministic_and_noise_tiles(self):
        for name in textures.TEXTURES:
            first = textures.image(name, 64)
            self.assertEqual(first.shape, (64, 64, 3))
            self.assertTrue(np.array_equal(first, textures.image(name, 64)), name)
        noise = textures.noise(np.random.default_rng(0), 256, 8)
        wrap = np.abs(noise[0] - noise[-1]).max()
        step = np.abs(np.diff(noise, axis=0)).max()
        self.assertLessEqual(wrap, step * 1.01)

    def test_committed_textures_match_the_generator(self):
        cfg = textures.settings()
        for name in sorted(set(cfg['custom'].values())):
            # Compare pixels: zlib versions may compress the same image differently.
            committed = np.asarray(Image.open(INSTALLED / (name + '.png')).convert('RGB'))
            expected = textures.image(name, cfg['texture_size_pixels'])
            self.assertTrue(np.array_equal(committed, expected), name)
            self.assertEqual((INSTALLED / (name + '.vmat')).read_text(encoding='utf-8'), textures.vmat(name))

    def test_written_materials_reference_their_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'textures'
            used = textures.write_textures(out)
            for name in used:
                text = (out / (name + '.vmat')).read_text(encoding='utf-8')
                for reference in ('.png', '_rough.png'):
                    self.assertIn(f'"{textures.PREFIX}{name}{reference}"', text)
                    self.assertTrue((out / (name + reference)).is_file())
                self.assertIn(f'"{textures.PREFIX}flat_normal.png"', text)


class TextureGeometryTests(unittest.TestCase):
    def test_textured_surfaces_repeat_at_real_size(self):
        obj = render_obj([('stone', (0, 0, 0), (3, 2, 4), 'exterior_stone'),
                          ('frame', (5, 0, 0), (6, 2, 4), 'window_frame')], [], resolve_surfaces=False)
        ratios = uv_metres(obj)
        self.assertEqual(ratios['campus_exterior_stone'], {5.2019})
        self.assertEqual(ratios['campus_window_frame'], {.6})

    def test_pavement_finish_uses_the_same_materials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / 'cs2/content/trento_povo/models/povo'
            models.mkdir(parents=True)
            (root / 'exports/povo_campus').mkdir(parents=True)
            shutil.copyfile(ROOT / 'cs2/content/trento_povo/models/povo/povo_blockout.vmdl',
                            models / 'povo_blockout.vmdl')
            write_assets('', root)
            text = (models / 'povo1_campus_paving.vmdl').read_text(encoding='utf-8')
        for name in ('paving', 'asphalt', 'concrete'):
            self.assertIn(f'from = "campus_exterior_{name}" to = "{material_path("exterior_" + name)}"', text)


if __name__ == '__main__':
    unittest.main()
