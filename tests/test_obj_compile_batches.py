from pathlib import Path
import tempfile
import unittest

from tools.obj_compile_batches import geometry_signature, rebatch_obj, split_obj, surface_signature, split_render_model, coalesce_collision_obj, split_collision_objects, split_obj_materials, rebatch_render_model


class ObjCompileBatchTests(unittest.TestCase):
    def test_render_rebatch_refuses_implicit_normals_without_mutating_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            content = Path(folder)
            mesh = content / 'mesh.obj'
            original = 'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n'
            mesh.write_text(original)
            model = content / 'model.vmdl'
            model_text = '{ _class = "RenderMeshFile" filename = "mesh.obj" exception_list = [] }'
            model.write_text(model_text)
            with self.assertRaisesRegex(ValueError, 'explicit corner normals'):
                rebatch_render_model(content, model)
            self.assertEqual(mesh.read_text(), original)
            self.assertEqual(model.read_text(), model_text)

    def test_material_partitions_keep_shared_vertices_object_names_and_face_order(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'mesh.obj'
            original = ('v 0 0 0\nv 1 0 0\nv 0 1 0\n'
                        'vt 0 0\nvt 1 0\nvt 0 1\nvn 0 0 1\ns off\n'
                        'o first\nusemtl wall\nf 1/1/1 2/2/1 3/3/1\n'
                        'o second\nusemtl glass\nf 1/1/1 3/3/1 2/2/1\n'
                        'o third\nusemtl wall\nf 3/3/1 2/2/1 1/1/1\n')
            source.write_text(original)
            result = split_obj_materials(source)
            self.assertEqual(result['faces'], 3)
            self.assertEqual(len(result['parts']), 2)
            self.assertEqual(result['materials']['wall']['faces'], 2)
            wall = Path(result['parts'][0]).read_text()
            self.assertIn('o first\nusemtl wall\ns off\nf 1/1/1 2/2/1 3/3/1', wall)
            self.assertIn('o third\nusemtl wall\ns off\nf 3/3/1 2/2/1 1/1/1', wall)
            self.assertEqual(sum(line.startswith('v ') for line in wall.splitlines()), 3)
            self.assertEqual(sum(line.startswith('vn ') for line in wall.splitlines()), 1)
            self.assertNotIn('o second', wall)
            self.assertIn('o second', Path(result['parts'][1]).read_text())
            self.assertEqual(source.read_text(), original)

    def test_reduces_groups_preserving_corner_attributes_and_face_state(self):
        text = ('v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nvn 0 0 1\ns off\n'
                'o first\nusemtl wall\nf 1/1/1 2/2/1 3/3/1\n'
                'o second\nusemtl wall\nf 3/3/1 2/2/1 1/1/1\n'
                'g third\no third\nusemtl glass\ns 1\nf -3/1/1 -2/2/1 -1/3/1\n')
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'source.obj', Path(folder) / 'out.obj'
            source.write_text(text)
            report = rebatch_obj(source, target)
            self.assertEqual(report['before']['sha256'], report['after']['sha256'])
            self.assertEqual(report['after']['objects'], 2)
            self.assertEqual(report['after']['faces'], 3)
            self.assertEqual(source.read_text(), text)
            self.assertEqual(target.read_text().count('usemtl wall'), 1)

    def test_bounds_each_import_object_and_supports_in_place_conversion(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'mesh.obj'
            path.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl wall\n' + 'f 1 2 3\n' * 7)
            before = geometry_signature(path)
            result = rebatch_obj(path, path, faces_per_object=2)
            self.assertEqual(result['after']['objects'], 4)
            self.assertEqual(before['sha256'], geometry_signature(path)['sha256'])

    def test_rejects_oversized_polygon_without_replacing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / 'source.obj', Path(folder) / 'out.obj'
            source.write_text('f 1 2 3 4\n')
            target.write_text('keep existing output')
            with self.assertRaises(ValueError):
                rebatch_obj(source, target, corners_per_object=3)
            self.assertEqual(target.read_text(), 'keep existing output')
            self.assertFalse(target.with_suffix('.obj.partial').exists())

    def test_partitions_reindex_attributes_preserving_order_materials_and_normals(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.obj'
            source.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nvn 0 0 1\nusemtl wall\ns 1\nf 1/1/1 2/2/1 3/3/1\nusemtl glass\nf -1/3/1 -2/2/1 -3/1/1\n')
            expected = surface_signature([source])
            result = split_obj(source, Path(folder) / 'parts', faces_per_part=1)
            self.assertEqual(len(result['parts']), 2)
            self.assertEqual(surface_signature(result['parts']), expected)
            self.assertEqual(surface_signature([source]), expected)

    def test_modeldoc_partition_preserves_physics_and_import_transform(self):
        with tempfile.TemporaryDirectory() as folder:
            content = Path(folder)
            (content / 'models').mkdir()
            (content / 'models/mesh.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\nf 3 2 1\n')
            model = content / 'model.vmdl'
            physics = '{ _class = "PhysicsMeshFile" filename = "models/collision.obj" surface_prop = "tile" }'
            model.write_text('{ children = [' + physics + ',{ _class = "RenderMeshFile" name = "mesh" filename = "models/mesh.obj" import_scale = 39.37007874 import_rotation = [0,0,0] import_filter = { exclude_by_default = false exception_list = [] } }] }')
            result = split_render_model(content, model, faces_per_part=1)
            updated = model.read_text()
            self.assertIn(physics, updated)
            self.assertEqual(updated.count('import_scale = 39.37007874'), 2)
            self.assertEqual(updated.count('_class = "RenderMeshFile"'), 2)
            self.assertTrue(result['physics_unchanged'])

    def test_refuses_to_change_object_name_filtered_model(self):
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / 'model.vmdl'
            text = '{ _class = "RenderMeshFile" filename = "mesh.obj" exclude_by_default = true exception_list = [] }'
            model.write_text(text)
            with self.assertRaises(ValueError):
                split_render_model(folder, model)
            self.assertEqual(model.read_text(), text)

    def test_collision_coalescing_preserves_triangles_and_explicit_surface(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'collision.obj'
            path.write_text('o a\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl wall\nf 1 2 3\no b\nusemtl wall\nf 3 2 1\nusemtl ceiling\nf 1 3 2\n')
            before = surface_signature([path], include_material=False)
            result = coalesce_collision_obj(path, surface_prop='concrete')
            self.assertEqual(surface_signature([path], include_material=False), before)
            self.assertEqual(path.read_text().count('usemtl '), 1)
            self.assertEqual(path.read_text().count('o collision_surface'), 1)
            self.assertEqual(result['surface_prop'], 'concrete')
            self.assertEqual(result['original_material_directives'], 3)

    def test_collision_objects_remain_intact_and_original_file_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'collision.obj'
            text = 'o a\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl wall\nf 1 2 3\no b\nv 0 0 1\nv 1 0 1\nv 0 1 1\nusemtl floor\nf 4 5 6\n'
            source.write_text(text)
            expected = surface_signature([source])
            report = split_collision_objects(source)
            self.assertEqual(len(report['parts']), 2)
            self.assertEqual(surface_signature(report['parts']), expected)
            self.assertEqual(source.read_text(), text)

    def test_collision_partition_refuses_shared_connected_vertices(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'collision.obj'
            source.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\no a\nf 1 2 3\no b\nf 3 2 1\n')
            with self.assertRaisesRegex(ValueError, 'share vertices'):
                split_collision_objects(source)


if __name__ == '__main__':
    unittest.main()
