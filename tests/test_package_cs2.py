from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock
import zlib

from tools import package_cs2 as pack
from tools.vpk import EMBEDDED, MAGIC, Package, VPKError


def map_fixture(*, trailer=b''):
    body = b'compiled map fixture'
    tree = (b'vmap_c\0maps\0trento_povo\0'
            + struct.pack('<IHHIIH', zlib.crc32(body), 0, EMBEDDED,
                          0, len(body), 0xffff) + b'\0\0\0')
    return (struct.pack('<7I', MAGIC, 2, len(tree), len(body), 0, 0,
                        len(trailer)) + tree + body + trailer)


class PackageMapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cs2 = self.root / 'cs2'
        self.addon = self.cs2 / 'game/csgo_addons/trento_povo'
        self.source = self.addon / 'maps/trento_povo.vpk'
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(map_fixture())
        self.packer = self.root / 'vpkeditcli'
        self.packer.write_bytes(b'fake packer; execution is mocked')
        self.output = self.root / 'output/map.vpk'
        assets = set(pack.RADAR_FILES)
        assets.update(rel.as_posix() + '_c' for rel in pack.SYNC_CONTENT
                      if rel.suffix == '.vmat')
        assets.update(('models/povo/povo_blockout.vmdl_c',
                       'cfg/maps/trento_povo.cfg',
                       'materials/trento/povo/terrain.vtex_c'))
        for name in assets:
            target = self.addon / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'compiled addon fixture')
        self.overview = self.addon / pack.RADAR_FILES[-1]
        self.overview.write_bytes(
            (pack.REPO_ROOT / 'exports/povo_radar/trento_povo.txt').read_bytes())

    def test_accepts_cs2_empty_signature_descriptor_and_rejects_signed_trailer(self):
        self.source.write_bytes(map_fixture(trailer=struct.pack('<5I', MAGIC, 1, 0, 0, 0)))
        pack.require_unsigned(Package(self.source))
        self.source.write_bytes(map_fixture(trailer=struct.pack('<5I', MAGIC, 1, 1, 0, 0)))
        with self.assertRaisesRegex(VPKError, 'signed or unknown'):
            pack.require_unsigned(Package(self.source))

    def test_missing_radar_and_stale_overview_stop_before_packer_runs(self):
        with mock.patch.object(pack.subprocess, 'run') as run:
            original = self.overview.read_bytes()
            self.overview.write_bytes(original.replace(b'5.536417323', b'6.536417323'))
            with self.assertRaisesRegex(VPKError, 'overview differs'):
                pack.package_map(self.cs2, self.packer, self.output)
            self.overview.write_bytes(original)
            (self.addon / pack.RADAR_FILES[0]).unlink()
            with self.assertRaisesRegex(VPKError, 'missing or empty'):
                pack.package_map(self.cs2, self.packer, self.output)
            run.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_corrupt_input_does_not_overwrite_last_good_build(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b'previous good build')
        self.source.write_bytes(map_fixture()[:-1] + b'!')
        with mock.patch.object(pack.subprocess, 'run') as run:
            with self.assertRaisesRegex(VPKError, 'CRC mismatch'):
                pack.package_map(self.cs2, self.packer, self.output, force=True)
            run.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b'previous good build')

    def test_packer_failure_and_dropped_assets_preserve_source_and_last_build(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b'previous good build')
        report = self.output.with_suffix('.json')
        report.write_bytes(b'previous report')
        original = self.source.read_bytes()

        def incomplete_pack(command, **kwargs):
            Path(command[command.index('--output') + 1]).write_bytes(map_fixture())

        for effect, error in ((subprocess.CalledProcessError(1, 'packer'),
                               subprocess.CalledProcessError),
                              (incomplete_pack, VPKError)):
            with mock.patch.object(pack.subprocess, 'run', side_effect=effect):
                with self.assertRaises(error):
                    pack.package_map(self.cs2, self.packer, self.output, force=True)
            self.assertEqual(self.source.read_bytes(), original)
            self.assertEqual(self.output.read_bytes(), b'previous good build')
            self.assertEqual(report.read_bytes(), b'previous report')

    def test_output_cannot_replace_installed_compiler_package(self):
        with self.assertRaisesRegex(VPKError, 'outside the installed addon'):
            pack.package_map(self.cs2, self.packer, self.source, force=True)

    def test_source2_chunk_table_preserves_payload_and_rebuilds_checksums(self):
        try:
            # Official BLAKE3 empty-input test vector, truncated to 128 bits.
            self.assertEqual(pack.blake3_digest(b'').hex(),
                             'af1349b9f5f9a1a6a0404dea36dcc949')
        except VPKError:
            self.skipTest('Optional blake3 packaging dependency is not installed')
        original = Package(self.source)
        original_data = original.read(original.entries['maps/trento_povo.vmap_c'])
        pack.source2_hashes(self.source)
        rebuilt = Package(self.source)
        self.assertEqual(rebuilt.read(rebuilt.entries['maps/trento_povo.vmap_c']),
                         original_data)
        raw = self.source.read_bytes()
        header = struct.unpack('<7I', raw[:28])
        self.assertEqual(header[4:], (28, 48, 20))
        start = rebuilt.data_offset + rebuilt.embedded_size
        archive, kind, offset, length, checksum = struct.unpack(
            '<HHII16s', raw[start:start + 28])
        self.assertEqual((archive, kind, offset, length),
                         (EMBEDDED, 1, 0, len(original_data)))
        self.assertEqual(checksum, pack.blake3_digest(original_data))
        footer = start + 28
        self.assertEqual(raw[footer:footer + 16],
                         pack.hashlib.md5(raw[28:rebuilt.data_offset]).digest())
        self.assertEqual(raw[footer + 16:footer + 32],
                         pack.hashlib.md5(raw[start:footer]).digest())
        self.assertEqual(raw[footer + 32:footer + 48],
                         pack.hashlib.md5(raw[:footer + 32]).digest())
        pack.require_unsigned(rebuilt)


if __name__ == '__main__':
    unittest.main()
