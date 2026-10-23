import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib

from tools import build_povo_radar as radar
from tools.build_povo_blockout import boundary_segments


ROOT = Path(__file__).resolve().parents[1]


class PovoRadarTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config_path = self.root / "blockout.json"
        self.config_path.write_bytes((ROOT / "config/povo_blockout.json").read_bytes())
        self.config = json.loads(self.config_path.read_text())
        self.output = self.root / "radar"

    def build(self, **options):
        return radar.build_radar(self.config_path, self.output, **options)

    def test_known_world_positions_and_axis_handedness(self):
        origin = self.config["origin"]
        self.assertEqual(radar.geographic_to_world(*origin[:2], origin), (0, 0))
        north = radar.geographic_to_world(origin[0], origin[1] + 1, origin)
        east = radar.geographic_to_world(origin[0] + 1, origin[1], origin)
        self.assertAlmostEqual(north[0], radar.UNITS_PER_METRE)
        self.assertEqual(north[1], 0)
        self.assertAlmostEqual(east[1], radar.UNITS_PER_METRE)
        self.assertEqual(east[0], 0)
        # First live CT start: N0+57.25m, E0+59.25m, rounded by VMAP.
        known = radar.geographic_to_world(666309.25, 5103857.25, origin)
        self.assertAlmostEqual(known[0], 2253.937, delta=0.001)
        self.assertAlmostEqual(known[1], 2332.677, delta=0.001)
        overview = radar.overview_for(self.config, 7)
        cx, cy = radar.world_to_pixel(0, 0, overview)
        nx, ny = radar.world_to_pixel(*north, overview)
        ex, ey = radar.world_to_pixel(*east, overview)
        self.assertGreater(nx, cx)
        self.assertEqual(ny, cy)
        self.assertEqual(ex, cx)
        self.assertLess(ey, cy)
        for world in ((0, 0), known, (-2096.457, 2844.488)):
            restored = radar.pixel_to_world(*radar.world_to_pixel(*world, overview), overview)
            for actual, expected in zip(restored, world):
                self.assertAlmostEqual(actual, expected, places=9)

    def test_overview_retains_square_aspect_and_covers_the_mesh_perimeter(self):
        overview = radar.overview_for(self.config, 7)
        self.assertAlmostEqual(overview["scale"] * radar.SIZE / radar.UNITS_PER_METRE, 144)
        for _name, bounds in boundary_segments(self.config["gameplay"]["playable_bounds"],
                                               self.config["gameplay"]["boundary"]):
            left, top, right, bottom = radar.pixel_bounds(bounds, self.config["origin"], overview)
            self.assertTrue(0 < left < right < radar.SIZE)
            self.assertTrue(0 < top < bottom < radar.SIZE)
        # Coordinates serialized to overview text retain subpixel alignment.
        metadata = self.build()
        text = (self.output / "trento_povo.txt").read_text()
        for label, (x, y) in metadata["markers_pixels"].items():
            self.assertIn(f'"{label}_x" "{x / radar.SIZE:.9f}"', text)
            self.assertIn(f'"{label}_y" "{y / radar.SIZE:.9f}"', text)
        self.assertLess(metadata["markers_pixels"]["TSpawn"][0], metadata["markers_pixels"]["CTSpawn"][0])

    def test_png_alpha_dimensions_colors_and_crc(self):
        self.build()
        png = (self.output / radar.RADAR_IMAGE).read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        offset, data = 8, b""
        while offset < len(png):
            length = struct.unpack(">I", png[offset:offset + 4])[0]
            kind = png[offset + 4:offset + 8]
            payload = png[offset + 8:offset + 8 + length]
            crc = struct.unpack(">I", png[offset + 8 + length:offset + 12 + length])[0]
            self.assertEqual(crc, zlib.crc32(kind + payload))
            if kind == b"IHDR":
                self.assertEqual(struct.unpack(">IIBBBBB", payload), (1024, 1024, 8, 6, 0, 0, 0))
            if kind == b"IDAT":
                data += payload
            offset += 12 + length
        scanlines = zlib.decompress(data)
        self.assertEqual(len(scanlines), 1024 * (1024 * 4 + 1))

        def pixel(x, y):
            start = y * (1024 * 4 + 1) + 1 + x * 4
            return tuple(scanlines[start:start + 4])

        self.assertEqual(pixel(0, 0), (0, 0, 0, 0))
        self.assertEqual(pixel(500, 450), radar.FLOOR)
        overview = radar.overview_for(self.config, 7)
        for cover in self.config["gameplay"]["cover"]:
            left, top, right, bottom = radar.pixel_bounds(cover["bounds"], self.config["origin"], overview)
            expected = radar.COVER_HIGH if cover["height_metres"] >= 2 else radar.COVER_LOW
            self.assertEqual(pixel(round((left + right) / 2), round((top + bottom) / 2)), expected)

    def test_deterministic_exports_hashes_and_review_are_valid(self):
        metadata = self.build()
        original = {name: (self.output / name).read_bytes() for name in radar.OUTPUT_FILES}
        self.build(force=True)
        self.assertEqual(original, {name: (self.output / name).read_bytes() for name in radar.OUTPUT_FILES})
        for name, record in metadata["artifacts"].items():
            self.assertEqual(record["sha256"], hashlib.sha256(original[name]).hexdigest())
        svg = ET.fromstring(original["review.svg"])
        self.assertEqual(len(svg.findall(".//{http://www.w3.org/2000/svg}circle")), 13)
        for name in radar.TEXTURES:
            self.assertIn(f"panorama/images/overheadmaps/{radar.RADAR_IMAGE}" , original[name].decode())

    def test_invalid_and_stale_inputs_preserve_existing_output(self):
        self.build()
        previous = (self.output / radar.RADAR_IMAGE).read_bytes()
        (self.output / "keep.txt").write_text("manual note")
        with self.assertRaisesRegex(ValueError, "exists"):
            self.build()
        for padding in (0, float("nan"), float("inf")):
            with self.assertRaisesRegex(ValueError, "padding"):
                self.build(force=True, padding=padding)
        # Shrink to the middle, retaining cover validity but excluding the starts.
        self.config["gameplay"]["playable_bounds"] = [666305, 5103760, 666330, 5103840]
        self.config_path.write_text(json.dumps(self.config))
        with self.assertRaisesRegex(ValueError, "markers|outside"):
            self.build(force=True)
        self.assertEqual((self.output / radar.RADAR_IMAGE).read_bytes(), previous)
        self.assertEqual((self.output / "keep.txt").read_text(), "manual note")


if __name__ == "__main__":
    unittest.main()
