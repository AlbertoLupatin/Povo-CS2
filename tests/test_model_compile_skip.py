import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import tools.cs2_campus as campus

VMDL = '''{ filename = "models/povo/povo1_campus.obj"
  to = "materials/trento/povo/campus/wall.vmat" }'''
VMAT = 'Layer0 { TextureColor "materials/trento/povo/campus/wall.png" }'


class ModelCompileSkipTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cs2 = self.root/'cs2'
        self.content = self.cs2/'content/csgo_addons/trento_povo'
        self.game = self.cs2/'game/csgo_addons/trento_povo'
        for relative, text in (('models/povo/povo1_campus.vmdl', VMDL), ('models/povo/povo1_campus.obj', 'v 0 0 0'),
                               ('materials/trento/povo/campus/wall.vmat', VMAT),
                               ('materials/trento/povo/campus/wall.png', 'png')):
            (self.content/relative).parent.mkdir(parents=True, exist_ok=True)
            (self.content/relative).write_text(text)
        compiler = self.cs2/'game/bin/win64/resourcecompiler.exe'
        compiler.parent.mkdir(parents=True)
        compiler.write_bytes(b'tool')
        self.compiled = []

    def tearDown(self):
        self.tmp.cleanup()

    def fake_compile(self, command, check):
        resource = Path(command[command.index('-i')+1])
        self.compiled.append(resource.name)
        if resource.suffix == '.vmdl':
            output = self.game/resource.relative_to(self.content).with_suffix('.vmdl_c')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text('compiled '+resource.read_text())

    def build(self, **options):
        self.compiled.clear()
        metadata = {'interactions': {'doors': []}}
        with patch.object(campus, 'ROOT', self.root), patch.object(campus, 'export', return_value=metadata), \
             patch.object(campus, 'prepare_map'), patch.object(campus, 'make_radar', return_value=self.root), \
             patch.object(campus, 'deploy_assets'), patch.object(campus, 'package_map'), \
             patch.object(campus.shutil, 'copyfile'), patch('builtins.print'), \
             patch.object(campus.subprocess, 'run', side_effect=self.fake_compile):
            campus.build(self.cs2, pack=False, **options)
        return 'povo1_campus.vmdl' in self.compiled

    def test_unchanged_model_is_reused_and_any_input_change_recompiles(self):
        self.assertTrue(self.build())
        self.assertFalse(self.build())
        self.assertIn('trento_povo_campus.vmap', self.compiled)
        for relative in ('models/povo/povo1_campus.obj', 'materials/trento/povo/campus/wall.vmat',
                         'materials/trento/povo/campus/wall.png', 'models/povo/povo1_campus.vmdl'):
            with self.subTest(changed=relative):
                path = self.content/relative
                path.write_text(path.read_text()+' ')
                self.assertTrue(self.build())
                self.assertFalse(self.build())

    def test_replaced_output_missing_output_and_force_recompile(self):
        self.build()
        output = self.game/'models/povo/povo1_campus.vmdl_c'
        output.write_text('compiled elsewhere')
        self.assertTrue(self.build())
        output.unlink()
        self.assertTrue(self.build())
        self.assertTrue(self.build(force_models=True))

    def test_failed_compile_leaves_no_reusable_stamp(self):
        self.build()
        (self.content/'models/povo/povo1_campus.obj').write_text('v 1 1 1')
        with self.assertRaises(RuntimeError), patch.object(campus, 'ROOT', self.root), \
             patch.object(campus, 'export', return_value={'interactions': {'doors': []}}), \
             patch.object(campus, 'prepare_map'), patch.object(campus, 'make_radar', return_value=self.root), \
             patch.object(campus, 'deploy_assets'), \
             patch.object(campus.subprocess, 'run', side_effect=RuntimeError('compiler crashed')):
            campus.build(self.cs2, pack=False)
        self.assertFalse((self.root/'build/compile_stamps/povo1_campus.vmdl.json').exists())
        self.assertTrue(self.build())
