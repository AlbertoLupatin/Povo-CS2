import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_povo_blockout import OUTPUT_FILES, build_blockout


class PovoBlockoutTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "config").mkdir()
        self.config_path = self.root / "config/blockout.json"
        self.output = self.root / "export"
        self.write_grid("dtm.asc")
        self.write_grid("dbm.asc", elevation=20)
        (self.root / "image.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aDTsAAAAASUVORK5CYII="))
        self.config = {
            "origin": [102, 202, 10], "horizontal_crs_label": "synthetic projected metre grid",
            "vertical_datum": "synthetic", "terrain_bounds": [101, 201, 104, 204],
            "sampling_step": 2, "dtm": "dtm.asc", "dbm": "dbm.asc", "orthophoto": "image.png",
            "orthophoto_bounds": [100, 200, 105, 205],
            "buildings": [{"id": "campus", "bounds": [102, 202, 103, 203],
                           "base_elevation": 9, "roof_elevation": 20, "evidence": "Synthetic box"}],
            "attribution": {"terrain": "Synthetic fixture; not actual PAT data"},
        }

    def write_grid(self, filename, *, elevation=10, nodata_index=None, x_center=100.5):
        values = [str(elevation)] * 25
        if nodata_index is not None:
            values[nodata_index] = "-9999"
        (self.root / filename).write_text(
            f"ncols 5\nnrows 5\nxllcenter {x_center}\nyllcenter 200.5\ncellsize 1\nnodata_value -9999\n"
            + "\n".join(" ".join(values[i:i + 5]) for i in range(0, 25, 5)) + "\n")

    def export(self, **options):
        self.config_path.write_text(json.dumps(self.config))
        return build_blockout(self.config_path, self.output, **options)

    def read_mesh(self):
        vertices, uvs, objects = [], [], {}
        for line in (self.output / "povo_blockout.obj").read_text().splitlines():
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "o":
                current = parts[1]
                objects[current] = []
            elif parts[0] == "v":
                vertices.append(tuple(map(float, parts[1:])))
            elif parts[0] == "vt":
                uvs.append(tuple(map(float, parts[1:])))
            elif parts[0] == "f":
                objects[current].append(tuple(tuple(map(int, ref.split("/"))) for ref in parts[1:]))
        return vertices, uvs, objects

    def test_crop_preserves_centres_global_uvs_and_upward_faces(self):
        result = self.export()
        vertices, uvs, objects = self.read_mesh()
        terrain_indices = {ref[0] for face in objects["terrain"] for ref in face}
        terrain_vertices = [vertices[i - 1] for i in sorted(terrain_indices)]
        self.assertEqual(terrain_vertices, [(-0.5, 1.5, 0), (1.5, 1.5, 0),
                                           (-0.5, -0.5, 0), (1.5, -0.5, 0)])
        self.assertEqual(uvs, [(0.3, 0.7), (0.7, 0.7), (0.3, 0.3), (0.7, 0.3)])
        for face in objects["terrain"]:
            self.assertTrue(all(ref[0] == ref[1] for ref in face))
            a, b, c = [vertices[ref[0] - 1] for ref in face]
            self.assertGreater((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]), 0)
        self.assertEqual(result["terrain"]["cropped_sample_center_bounds"], (101.5, 201.5, 103.5, 203.5))
        self.assertEqual(result["terrain"]["sampled_source_bounds"], [[101.5, 201.5, 10], [103.5, 203.5, 10]])
        self.assertEqual((self.output / "orthophoto_reference.png").read_bytes(), (self.root / "image.png").read_bytes())
        self.assertIn("map_Kd orthophoto_reference.png", (self.output / "povo_blockout.mtl").read_text())

    def test_building_normals_closed_volume_and_calibration(self):
        self.export()
        vertices, _, objects = self.read_mesh()
        for name, expected_minimum, expected_maximum in (
            ("campus", (0, 0, -1), (1, 1, 10)),
            ("calibration_1m", (-120, -170, 0), (-119, -169, 1)),
        ):
            faces = objects[name]
            indices = {ref[0] for face in faces for ref in face}
            self.assertEqual(len(indices), 8)
            self.assertEqual(len(faces), 12)
            self.assertEqual(tuple(min(vertices[i - 1][axis] for i in indices) for axis in range(3)), expected_minimum)
            self.assertEqual(tuple(max(vertices[i - 1][axis] for i in indices) for axis in range(3)), expected_maximum)
            centre = tuple((a + b) / 2 for a, b in zip(expected_minimum, expected_maximum))
            edges = {}
            for face in faces:
                refs = [ref[0] for ref in face]
                a, b, c = [vertices[i - 1] for i in refs]
                ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
                self.assertGreater(sum(normal[i] * (a[i] - centre[i]) for i in range(3)), 0)
                for edge in zip(refs, refs[1:] + refs[:1]):
                    key = tuple(sorted(edge))
                    edges[key] = edges.get(key, 0) + 1
            self.assertTrue(all(count == 2 for count in edges.values()))

    def test_boundary_samples_retained_on_uneven_stride(self):
        self.config["terrain_bounds"] = [100, 200, 105, 205]
        self.config["sampling_step"] = 3
        result = self.export()
        self.assertEqual(result["terrain"]["statistics"]["vertices"], 9)
        self.assertEqual(result["terrain"]["statistics"]["triangles"], 8)
        self.assertEqual(result["terrain"]["sampled_source_bounds"], [[100.5, 200.5, 10], [104.5, 204.5, 10]])

    def test_decimation_never_bridges_hidden_nodata(self):
        self.config["terrain_bounds"] = [100, 200, 105, 205]
        self.write_grid("dtm.asc", nodata_index=6)  # Hidden inside northwest coarse quad.
        result = self.export()
        self.assertEqual(result["terrain"]["statistics"]["triangles"], 6)
        self.assertEqual(result["terrain"]["statistics"]["skipped_triangles"], 2)

    def test_provenance_hashes_and_material_artifacts(self):
        result = self.export()
        self.assertEqual(set(path.name for path in self.output.iterdir()), set(OUTPUT_FILES))
        record = json.loads((self.output / "provenance.json").read_text())
        self.assertEqual(record["config"]["sha256"], hashlib.sha256(self.config_path.read_bytes()).hexdigest())
        for role, filename in (("dtm", "dtm.asc"), ("dbm", "dbm.asc"), ("orthophoto", "image.png")):
            self.assertEqual(record["sources"][role]["sha256"], hashlib.sha256((self.root / filename).read_bytes()).hexdigest())
        for filename, entry in record["artifacts"].items():
            self.assertEqual(entry["sha256"], hashlib.sha256((self.output / filename).read_bytes()).hexdigest())
        self.assertEqual(record["attribution"], self.config["attribution"])
        self.assertFalse(record["coordinate_transform"]["declarations_verified_by_builder"])
        self.assertEqual(result["statistics"], {"vertices": 20, "triangles": 26, "building_modules": 1, "objects": 3})

    def test_invalid_config_publishes_nothing(self):
        initial = json.loads(json.dumps(self.config))
        cases = [
            {"origin": [0, 0, float("inf")]}, {"sampling_step": 0}, {"sampling_step": True},
            {"terrain_bounds": [104, 201, 101, 204]}, {"terrain_bounds": [99, 201, 104, 204]},
            {"orthophoto_bounds": [102, 202, 104, 204]}, {"horizontal_crs_label": ""},
            {"buildings": [{**initial["buildings"][0], "base_elevation": 20}]},
            {"buildings": [{**initial["buildings"][0], "bounds": [100, 200, 103, 203]}]},
            {"buildings": [{**initial["buildings"][0], "id": "bad\no injected"}]},
            {"buildings": initial["buildings"] * 2},
        ]
        for values in cases:
            with self.subTest(values=values):
                self.config = {**initial, **values}
                with self.assertRaises(ValueError):
                    self.export()
                self.assertFalse(self.output.exists())

    def test_source_grid_misalignment_is_rejected(self):
        self.write_grid("dbm.asc", x_center=100.6)
        with self.assertRaisesRegex(ValueError, "identical"):
            self.export()
        self.assertFalse(self.output.exists())

    def test_source_extent_and_empty_terrain_are_rejected(self):
        self.config["terrain_bounds"] = [99, 199, 105, 205]
        self.config["orthophoto_bounds"] = [99, 199, 105, 205]
        with self.assertRaisesRegex(ValueError, "outside the source grid"):
            self.export()
        self.config["terrain_bounds"] = [101, 201, 104, 204]
        self.write_grid("dtm.asc", elevation=-9999)
        with self.assertRaisesRegex(ValueError, "No valid terrain"):
            self.export()
        self.assertFalse(self.output.exists())

    def test_existing_output_requires_force_and_failed_force_preserves_export(self):
        self.export()
        original = {p.name: p.read_bytes() for p in self.output.iterdir()}
        with self.assertRaisesRegex(ValueError, "exists"):
            self.export()
        self.config["origin"] = [102, 202, 11]
        self.export(force=True)
        self.assertNotEqual((self.output / "povo_blockout.obj").read_bytes(), original["povo_blockout.obj"])
        current = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.config["origin"] = [102, 202, float("nan")]
        with self.assertRaises(ValueError):
            self.export(force=True)
        self.assertEqual(current, {p.name: p.read_bytes() for p in self.output.iterdir()})


if __name__ == "__main__":
    unittest.main()
