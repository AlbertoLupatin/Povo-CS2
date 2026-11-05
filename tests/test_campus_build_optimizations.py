from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import cs2_campus as campus
from tools.campus_build_optimizations import optimized_inputs
from tools.obj_compile_batches import geometry_signature


class CampusBuildOptimizationTests(unittest.TestCase):
    def test_clean_package_compiles_base_material_not_used_by_campus_model(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            material = Path('materials/trento/povo/gameplay_cover.vmat')
            content = root / 'content/csgo_addons/trento_povo'
            (content / material).parent.mkdir(parents=True)
            (content / material).write_text('material fixture')
            overview = root / 'radar'
            overview.mkdir()
            (overview / 'trento_povo_campus.txt').write_text('overview fixture')
            (root / 'game/csgo_addons/trento_povo/resource/overviews').mkdir(parents=True)
            metadata = {'interactions': {'doors': []}}
            with mock.patch.object(campus, 'ROOT', root), \
                 mock.patch.object(campus, 'export', return_value=metadata), \
                 mock.patch.object(campus, 'prepare_map'), \
                 mock.patch.object(campus, 'make_radar', return_value=overview), \
                 mock.patch.object(campus, 'deploy_assets'), \
                 mock.patch.object(campus.project, 'SYNC_CONTENT', (material,)), \
                 mock.patch.object(campus.subprocess, 'run') as compile_call, \
                 mock.patch.object(campus, 'package_map', return_value={'package_bytes': 1, 'package_entries': 1}) as package:
                campus.build(root, skip_model=True)
            inputs = [Path(call.args[0][call.args[0].index('-i') + 1]) for call in compile_call.call_args_list]
            self.assertIn(content / material, inputs)
            self.assertLess(inputs.index(content / material), inputs.index(content / 'maps/trento_povo_campus.vmap'))
            package.assert_called_once()

    def test_deployed_partitions_keep_collision_options_and_restore_hooks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            content = root / 'content/csgo_addons/trento_povo'
            content.mkdir(parents=True)
            text = 'o a\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\nf 1//1 2//1 3//1\no b\nv 0 0 1\nv 1 0 1\nv 0 1 1\nf 4//1 5//1 6//1\n'
            (content / 'render.obj').write_text(text)
            render_signature = geometry_signature(content / 'render.obj')['sha256']
            (content / 'collision.obj').write_text(text)
            model = content / 'models/povo/povo1_campus.vmdl'
            model.parent.mkdir(parents=True)
            render = '{ _class = "RenderMeshFile" filename = "render.obj" exception_list = [] }'
            model.write_text('{ children = [ ' + render + ', '
                '{ _class = "PhysicsMeshFile" filename = "collision.obj" surface_prop = "tile" '
                'import_scale = 39.37007874 translation = [1,2,3] exception_list = [] } ] }')
            deploy = mock.Mock(return_value='deployed')
            fake = SimpleNamespace(project=campus.project, deploy_assets=deploy,
                                   MODEL='povo1_campus', ROOT=root)
            original_brace = campus.project._matching_brace
            original_insert = campus.project._insert_point_entity
            with optimized_inputs(fake):
                self.assertEqual(fake.deploy_assets(root, 'radar'), 'deployed')
                self.assertIsNot(campus.project._matching_brace, original_brace)
                updated = model.read_text()
                self.assertIn(render, updated)
                self.assertEqual(updated.count('_class = "RenderMeshFile"'), 1)
                self.assertEqual(geometry_signature(content / 'render.obj')['sha256'], render_signature)
                self.assertFalse(list(content.glob('render_part*.obj')))
                self.assertEqual(updated.count('surface_prop = "tile"'), 2)
                self.assertEqual(updated.count('translation = [1,2,3]'), 2)
                self.assertEqual(updated.count('import_scale = 39.37007874'), 2)
                self.assertEqual((content / 'collision.obj').read_text(), text)
                self.assertTrue((root / 'build/compile_partitions/povo1_campus.json').is_file())
            deploy.assert_called_once_with(root, 'radar')
            self.assertIs(fake.deploy_assets, deploy)
            self.assertIs(campus.project._matching_brace, original_brace)
            self.assertIs(campus.project._insert_point_entity, original_insert)

    def test_build_failure_restores_original_process_functions(self):
        original = campus.project._matching_bracket
        original_re = campus.project.re
        original_deploy = campus.deploy_assets
        with mock.patch.object(campus, 'export', side_effect=RuntimeError('export failed')):
            with self.assertRaisesRegex(RuntimeError, 'export failed'):
                campus.build(Path('unused'), optimize_import=True, force_models=True)
        self.assertIs(campus.project._matching_bracket, original)
        self.assertIs(campus.project.re, original_re)
        self.assertIs(campus.deploy_assets, original_deploy)
