import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.asc_to_obj import export, read_grid, sample_indices


class TerrainExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "input.asc"
        self.output = Path(self.directory.name) / "terrain.obj"

    def grid(self, samples="1 2\n3 4", *, coords="xllcorner 100\nyllcorner 200", extra=""):
        self.source.write_text(f"NCOLS 2\nnrows 2\n{coords}\ncellsize 2\n{extra}{samples}\n")

    def run_export(self, **options):
        arguments = dict(origin=(100, 200, 1), step=1,
                         crs="synthetic projected metre grid", vertical_datum="synthetic")
        arguments.update(options)
        return export(self.source, self.output, **arguments)

    def mesh(self):
        lines = self.output.read_text().splitlines()
        vertices = [tuple(map(float, line.split()[1:])) for line in lines if line.startswith("v ")]
        faces = [tuple(map(int, line.split()[1:])) for line in lines if line.startswith("f ")]
        return vertices, faces

    def test_corner_samples_north_first_and_upward_faces(self):
        self.grid()
        self.run_export()
        vertices, faces = self.mesh()
        self.assertEqual(vertices, [(1, 3, 0), (3, 3, 1), (1, 1, 2), (3, 1, 3)])
        for face in faces:
            a, b, c = [vertices[i - 1] for i in face]
            cross_z = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            self.assertGreater(cross_z, 0)
        metadata = json.loads(self.output.with_suffix(".json").read_text())
        self.assertEqual(metadata["source"]["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertFalse(metadata["coordinate_transform"]["declarations_verified"])

    def test_center_header_has_no_half_cell_shift(self):
        self.grid(coords="XLLCENTER 100\nYLLCENTER 200")
        self.run_export()
        self.assertEqual(self.mesh()[0][0], (0, 2, 0))
        self.assertEqual(self.mesh()[0][2], (0, 0, 2))

    def test_nodata_removes_only_touching_triangle(self):
        self.grid(samples="1 -9999\n3 4", extra="NODATA_value -9999\n")
        result = self.run_export()
        vertices, faces = self.mesh()
        self.assertEqual(len(vertices), 3)
        self.assertEqual(faces, [(1, 2, 3)])
        self.assertEqual(result["statistics"]["skipped_triangles"], 1)

    def test_decimation_preserves_last_row_and_column(self):
        self.assertEqual(sample_indices(6, 4), [0, 4, 5])
        self.source.write_text("ncols 4\nnrows 4\nxllcenter 0\nyllcenter 0\ncellsize 1\n" + "1 " * 16)
        self.run_export(step=2, origin=(0, 0, 0))
        vertices, faces = self.mesh()
        self.assertEqual(len(vertices), 9)
        self.assertEqual(len(faces), 8)
        self.assertEqual({v[0] for v in vertices}, {0, 2, 3})
        self.assertEqual({v[1] for v in vertices}, {0, 1, 3})

    def test_decimation_does_not_bridge_discarded_nodata(self):
        self.source.write_text("ncols 5\nnrows 3\nxllcenter 0\nyllcenter 0\ncellsize 1\n"
                               "nodata_value -9999\n1 1 1 1 1\n1 -9999 1 1 1\n1 1 1 1 1\n")
        result = self.run_export(step=2)
        self.assertEqual(result["statistics"]["triangles"], 2)
        self.assertEqual(result["statistics"]["skipped_triangles"], 2)

    def test_invalid_sources_publish_nothing(self):
        self.grid()
        valid = self.source.read_text()
        cases = [valid.replace("nrows 2", "nrows 0"),
                 valid.replace("NCOLS 2", "NCOLS 2.5"),
                 valid.replace("cellsize 2", "cellsize 0"),
                 valid.replace("cellsize 2", "cellsize nan"),
                 valid.replace("xllcorner 100", "xllcenter 100"),
                 valid.replace("1 2\n3 4", "1 2 3"), valid + "5\n",
                 valid.replace("1 2\n3 4", "1 inf 3 4"),
                 valid.replace("nrows 2", "nrows 2\nnrows 2"),
                 valid.replace("NCOLS 2", "NCOLS 999999999")]
        for content in cases:
            with self.subTest(content=content):
                self.source.write_text(content)
                with self.assertRaises(ValueError):
                    self.run_export()
                self.assertFalse(self.output.exists())
                self.assertFalse(self.output.with_suffix(".json").exists())

    def test_invalid_options_and_empty_mesh_publish_nothing(self):
        self.grid()
        for options in ({"step": 0}, {"origin": (0, 0, float("nan"))}, {"crs": " "}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.run_export(**options)
        self.grid(samples="-9999 -9999\n-9999 -9999", extra="NODATA_value -9999\n")
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertEqual(sorted(p.name for p in self.source.parent.iterdir()), ["input.asc"])

    def test_existing_sidecar_blocks_output_and_force_replaces_both(self):
        self.grid()
        sidecar = self.output.with_suffix(".json")
        sidecar.write_text("keep me")
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertFalse(self.output.exists())
        self.assertEqual(sidecar.read_text(), "keep me")
        self.run_export(force=True)
        self.assertEqual(read_grid(self.source).rows, 2)
        self.assertEqual(json.loads(sidecar.read_text())["statistics"]["triangles"], 2)


if __name__ == "__main__":
    unittest.main()
