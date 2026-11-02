import unittest
from pathlib import Path
from tools.retile_vrad import retile
from tools.recover_povo_lighting import select_job, recover


def script():
    return ('gpu_init\nlightmap_image_gpu 2048 2048 1024\n'
            'process_all_lightmap_blocks:\n    lightmap_image_filter_oidn 1\n    done\n'
            'compute_all_lightmap_blocks:\n    timer_start\n'+
            ''.join(f'    lightmap_load_block_gpu lightmap_info.dat {i}\n'
                    '    lightmap_compute_block_gpu 128 512 0.050\n' for i in range(4))+
            '    timer_stop\n    done\nlightmap_free_memory\n'
            'lpv_compute_block_gpu 0 0 0 96 90 11 512 1024 0.050\nexit 0\n')


class VradRetileTests(unittest.TestCase):
    def test_script_only_block_size_changes_are_rejected(self):
        for size in (128,256,512):
            with self.assertRaisesRegex(ValueError,'corrupt the atlas'):
                retile(script(),size)
        self.assertEqual(retile(script(),1024),script())

    def test_unsafe_recovery_cannot_touch_a_running_compiler(self):
        with self.assertRaisesRegex(RuntimeError,'disabled'):
            recover(Path('C:/CS2'),'trento_povo_campus',256,Path('unused'))

    def test_rejects_invalid_or_unexpected_scripts(self):
        for text in ('',script().replace('lightmap_info.dat 2','lightmap_info.dat 9'),
                     script().replace('128 512 0.050','128 256 0.050',1)):
            with self.assertRaises(ValueError):retile(text)
        with self.assertRaises(ValueError):retile(script(),255)

    def test_recovery_refuses_foreign_or_ambiguous_compilers_and_workers(self):
        root=Path('C:/CS2')
        parent=dict(Name='resourcecompiler.exe',ProcessId=10,ParentProcessId=1,
                    CommandLine='resourcecompiler.exe -i C:/CS2/content/csgo_addons/trento_povo/maps/trento_povo_campus.vmap')
        worker=dict(Name='vrad3.exe',ProcessId=11,ParentProcessId=10,
                    CommandLine='vrad3.exe -map maps/trento_povo_campus.vmap')
        self.assertEqual(select_job([parent,worker],root,'trento_povo_campus'),(parent,worker))
        for rows in ([],[parent],[parent,worker,parent],
                     [parent,dict(worker,ParentProcessId=99)],
                     [parent,dict(worker,CommandLine='vrad3.exe -map maps/de_dust2.vmap')]):
            with self.assertRaises(RuntimeError):select_job(rows,root,'trento_povo_campus')
