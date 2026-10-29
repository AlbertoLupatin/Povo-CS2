"""Check that the handoff wrapper stops safely and records build failures."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from tools.cs2_campus import map_lighting_options

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('build_on_windows', TOOLS / 'build_on_windows.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


class BuildHandoffTests(unittest.TestCase):
    def test_small_atlas_keeps_normal_quality_bake_for_visible_pavements(self):
        self.assertEqual(map_lighting_options(fast_lighting=True),
                         ['-lightmapVRadQuality','1','-lightmapMaxResolution','2048'])
        self.assertEqual(map_lighting_options(),['-lightmapVRadQuality','1'])
        self.assertEqual(map_lighting_options(fast_lighting=True,quality=0),
                         ['-lightmapVRadQuality','0','-lightmapMaxResolution','2048'])
        with self.assertRaises(ValueError):map_lighting_options(quality=2)

    def test_fast_lighting_reaches_compiler_and_build_record(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(handoff, 'ROOT', Path(folder)), \
             patch.object(handoff, 'preflight', return_value=Path('C:/CS2')), \
             patch.object(handoff.subprocess, 'check_output', return_value=''), \
             patch.object(handoff, 'run_logged') as run:
            self.assertEqual(handoff.main(['--fast-lighting','--lighting-quality','0']), 0)
            self.assertIn('--fast-lighting',run.call_args_list[1].args[0])
            arguments=run.call_args_list[1].args[0]
            self.assertEqual(arguments[arguments.index('--lighting-quality')+1],'0')
            self.assertIn('--full-crc',run.call_args_list[2].args[0])
            report,=Path(folder).glob('build/handoff/*/build.json')
            self.assertTrue(json.loads(report.read_text())['fast_lighting'])
            self.assertEqual(json.loads(report.read_text())['lighting_quality'],0)

    def test_check_never_starts_build(self):
        with patch.object(handoff, 'preflight', return_value=Path('C:/CS2')), \
             patch.object(handoff.subprocess, 'check_output') as command, \
             patch.object(handoff, 'run_logged') as run:
            self.assertEqual(handoff.main(['--check']), 0)
            command.assert_not_called()
            run.assert_not_called()

    def test_existing_compiler_stops_build(self):
        with patch.object(handoff, 'preflight', return_value=Path('C:/CS2')), \
             patch.object(handoff.subprocess, 'check_output', return_value='"resourcecompiler.exe"'), \
             patch.object(handoff, 'run_logged') as run:
            self.assertEqual(handoff.main([]), 1)
            run.assert_not_called()

    def test_failed_tests_stop_compile_and_save_failed_status(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(handoff, 'ROOT', Path(folder)), \
             patch.object(handoff, 'preflight', return_value=Path('C:/CS2')), \
             patch.object(handoff.subprocess, 'check_output', return_value=''), \
             patch.object(handoff, 'run_logged', side_effect=RuntimeError('test failure')) as run:
            self.assertEqual(handoff.main([]), 1)
            self.assertEqual(run.call_count, 1)
            report, = Path(folder).glob('build/handoff/*/build.json')
            self.assertEqual(json.loads(report.read_text())['status'], 'failed')

    def test_logged_command_propagates_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'command.log'
            with self.assertRaises(RuntimeError):
                handoff.run_logged([sys.executable, '-c', 'print("failure evidence"); raise SystemExit(7)'], log)
            self.assertIn('failure evidence', log.read_text())


if __name__ == '__main__':
    unittest.main()
