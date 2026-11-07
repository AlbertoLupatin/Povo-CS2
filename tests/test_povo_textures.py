import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from tools import povo_textures as textures
from tools.build_povo_campus import material_path, render_obj
from tools.povo_pavement_lighting import write_assets
from tools.povo_edges import build as build_edges
from tools.cs2_campus import add_edge_trees, world
from tests.test_map_entities import minimal_map

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
        self.assertEqual(textures.repeat_metres('campus_metal_dark'), .6)
        self.assertEqual(textures.repeat_metres('campus_snow'), .6)

    def test_mapping_names_known_materials_and_generators(self):
        cfg = textures.settings()
        self.assertFalse(set(cfg['custom']) & set(cfg['stock']))
        self.assertLessEqual(set(cfg['custom'].values()), set(textures.TEXTURES))
        for path in cfg['stock'].values():
            self.assertRegex(path, r'^materials/[a-z0-9_/]+\.vmat$')
            self.assertFalse(path.startswith('materials/trento/'))

    def test_repaired_sidewalks_and_plaza_joins_use_the_adjacent_finish(self):
        cases = (
            ('exterior_registered_via_footway_north_2','exterior_paving','exterior_dark_sidewalk'),
            ('exterior_registered_via_footway_south_0_junction_2','exterior_paving','exterior_dark_sidewalk'),
            ('exterior_registered_via_footway_south_1','exterior_paving','exterior_paving'),
            ('exterior_registered_via_verge_2_1','exterior_concrete','exterior_paving'),
            ('exterior_registered_footway_south_0','exterior_concrete','exterior_paving'),
            ('exterior_registered_library_verge_2_1','exterior_concrete','exterior_concrete'),
            ('campus_entry_landing','floor_circulation','exterior_paving'),
            ('library_0_access_join','floor_p2_tile','exterior_paving'),
            ('canteen_0_access','floor_p2_tile','exterior_paving'),
            ('canteen_0_access_join','floor_p2_tile','exterior_paving'),
        )
        for name,source,expected in cases:
            with self.subTest(name=name):
                self.assertEqual(textures.renamed(name,source),expected)

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

    def test_frosted_glass_stays_translucent_like_the_campus_glass(self):
        text = textures.vmat('frosted_glass')
        for line in ('shader "csgo_lightmappedgeneric.vfx"', 'F_TRANSLUCENT "1"', 'F_RENDER_BACKFACES "1"',
                     'g_flOpacityScale "0.84"', f'TextureLayer1Translucency "{textures.PREFIX}opaque_mask.png"',
                     'PhysicsSurfaceProperties "glass"'):
            self.assertIn(line, text)
        self.assertIn('shader "csgo_complex.vfx"', textures.vmat('aluminium'))
        self.assertIn('g_flMetalness "0.25"', textures.vmat('aluminium'))

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
                if name in textures.TRANSLUCENT:
                    self.assertTrue((out / 'opaque_mask.png').is_file())


class TextureGeometryTests(unittest.TestCase):
    def test_textured_surfaces_repeat_at_real_size(self):
        obj = render_obj([('stone', (0, 0, 0), (3, 2, 4), 'exterior_stone'),
                          ('frame', (5, 0, 0), (6, 2, 4), 'metal_dark')], [], resolve_surfaces=False)
        ratios = uv_metres(obj)
        self.assertEqual(ratios['campus_exterior_stone'], {5.2019})
        self.assertEqual(ratios['campus_metal_dark'], {.6})

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



def box_faces(lo, hi):
    """The six outward-wound quads of an axis-aligned box."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    return {'-x': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            '+x': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            '+y': [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
            '-z': [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
            '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]}


class FacadeAndRenameTests(unittest.TestCase):
    WALLS = [('academic_ground_outer_0', (0, 0, 0), (.3, 40, 4), 'wall'),      # west wall
             ('academic_ground_outer_1', (19.7, 0, 0), (20, 40, 4), 'wall'),   # east wall
             ('academic_ground_outer_2', (0, 39.7, 0), (20, 40, 4), 'wall'),   # north wall
             ('academic_ground_room_1', (5, 5, 0), (5.3, 20, 4), 'wall')]      # interior

    def test_only_outside_faces_of_perimeter_walls_take_stone(self):
        frames = textures.facade_frames(self.WALLS)
        self.assertEqual(frames[0][3], (0, 0, 20, 40))
        expected = {'academic_ground_outer_0': '-x', 'academic_ground_outer_1': '+x',
                    'academic_ground_outer_2': '+y', 'academic_ground_room_1': None}
        for name, lo, hi, material in self.WALLS:
            for side, quad in box_faces(lo, hi).items():
                finish = textures.face_material(name, material, lo, hi, quad, frames)
                self.assertEqual(finish, 'stone_facade' if side == expected[name] else 'wall', (name, side))

    def test_renames_pick_named_parts_of_a_shared_material(self):
        self.assertEqual(textures.renamed('exterior_road_front_footway_2_1_roadcut', 'campus_exterior_paving'),
                         'campus_exterior_dark_sidewalk')
        self.assertEqual(textures.renamed('backdrop_exterior_edges_south_sommarive_walk_0', 'campus_exterior_paving'),
                         'campus_exterior_dark_sidewalk')
        self.assertEqual(textures.renamed('exterior_road_front_campus_paving_2', 'campus_exterior_paving'),
                         'campus_exterior_paving')
        self.assertEqual(textures.renamed('exterior_entry_stair_3', 'exterior_orange'), 'exterior_red_paving')
        self.assertEqual(textures.renamed('exterior_p2_entry_locker', 'exterior_orange'), 'exterior_orange')
        self.assertEqual(textures.renamed('exterior_povo2_front_annex_1_mass_windowcut_2', 'campus_exterior_glass'),
                         'campus_exterior_frosted_glass')
        self.assertEqual(textures.renamed('exterior_povo2_front_annex_1_roof', 'campus_exterior_dark'),
                         'campus_exterior_dark')
        self.assertEqual(textures.renamed('exterior_povo1_library_0_pane_x_1', 'campus_exterior_glass'),
                         'campus_exterior_glass')
        self.assertEqual(material_path('exterior_frosted_glass'), textures.PREFIX + 'frosted_glass.vmat')
        self.assertEqual(material_path('window_frame'), textures.PREFIX + 'aluminium.vmat')
        self.assertEqual(material_path('exterior_dark_sidewalk'), textures.PREFIX + 'dark_paving.vmat')
        self.assertEqual(material_path('stone_facade'), textures.PREFIX + 'beige_stone.vmat')

    def test_renamed_and_facade_faces_reach_the_render_obj(self):
        obj = render_obj([*self.WALLS, ('exterior_entry_stair_0', (30, 0, 0), (31, 2, .2), 'exterior_orange')],
                         [('exterior_road_front_footway_0_1', 'campus_exterior_paving',
                           [(40, 0, 0), (42, 0, 0), (42, 2, 0)], None)], resolve_surfaces=False)
        used = {line.split()[1] for line in obj.splitlines() if line.startswith('usemtl ')}
        self.assertLessEqual({'campus_stone_facade', 'campus_wall', 'campus_exterior_red_paving',
                              'campus_exterior_dark_sidewalk'}, used)
        self.assertNotIn('campus_exterior_orange', used)
        self.assertAlmostEqual(min(uv_metres(obj)['campus_exterior_dark_sidewalk']), 5.2019, places=4)


class EdgeTreeTests(unittest.TestCase):
    def test_tree_belts_become_stock_props_without_placeholder_crowns(self):
        meshes, meta = build_edges()
        trees = meta['stock_trees']
        self.assertGreater(len(trees), 40)
        self.assertFalse([m['name'] for m in meshes if m['name'].startswith('exterior_edges_tree_')])
        self.assertEqual(len(trees), len({t['id'] for t in trees}))
        models = {m for band in textures.settings()['edge_trees']['bands'] for m in band['models']}
        for tree in trees:
            self.assertIn(tree['model'], models)
            self.assertTrue(0 <= tree['yaw'] < 360)
        # 8-11 m belts fall in the remake's maple band.
        self.assertTrue(all('maple' in t['model'] for t in trees))
        self.assertEqual(trees, build_edges()[1]['stock_trees'])

    def test_disabled_setting_keeps_the_placeholders(self):
        cfg = dict(textures.settings(), edge_trees=dict(textures.settings()['edge_trees'], enabled=False))
        from unittest.mock import patch
        with patch('tools.povo_textures.settings', return_value=cfg):
            meshes, meta = build_edges()
        self.assertEqual(meta['stock_trees'], [])
        self.assertTrue(any(m['name'].startswith('exterior_edges_tree_') for m in meshes))

    def test_props_are_upright_non_solid_and_stable(self):
        tree = textures.edge_tree('exterior_edges_tree_0_1', (-105, -92.4, 3), 9)
        source = add_edge_trees(minimal_map(), [tree])
        self.assertEqual(source, add_edge_trees(source, [tree]))
        self.assertIn('"classname" "string" "prop_static"', source)
        self.assertIn(f'"model" "string" "{tree["model"]}"', source)
        self.assertIn('"solid" "string" "0"', source)
        self.assertIn('"bakelighting" "string" "0"', source)
        self.assertIn('"precomputelightprobes" "string" "1"', source)
        self.assertIn('"disableshadows" "string" "0"', source)
        self.assertIn(f'"origin" "vector3" "{world(tree["point"])}"', source)
        self.assertIn(f'"angles" "qangle" "0 {tree["yaw"]} 0"', source)


if __name__ == '__main__':
    unittest.main()
