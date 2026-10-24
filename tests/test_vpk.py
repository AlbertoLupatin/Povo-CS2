from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from tools.vpk import EMBEDDED, MAGIC, Package, VPKError
from tools.verify_cs2_package import RADAR_FILES, compare_overviews, verify_package


OVERVIEW=b'''"trento_povo"
{
"material" "overviews/trento_povo"
"pos_x" "-100"
"pos_y" "200"
"scale" "5.5"
"rotate" "0"
"CTSpawn_x" "0.8"
}
'''


def one_entry(*,version=1,preload=b'pre',body=b'payload',archive=EMBEDDED,offset=0,terminator=0xffff):
    # Explicit wire-format fixture: extension / directory / basename / metadata
    # / preload / end names / end directories / end extensions.
    crc=zlib.crc32(preload+body)
    tree=(b'txt\0resource/overviews\0example\0'
          +struct.pack('<IHHIIH',crc,len(preload),archive,offset,len(body),terminator)
          +preload+b'\0\0\0')
    header=struct.pack('<III',MAGIC,version,len(tree))
    if version==2:header+=struct.pack('<IIII',len(body),0,0,0)
    return header+tree+(body if archive==EMBEDDED else b'')


def radar_fixture(files):
    # Minimal artificial VPK v1 used only for inclusion checks, not real VTEX.
    grouped={}
    for path,data in files.items():
        directory,filename=path.rsplit('/',1)
        name,extension=filename.rsplit('.',1)
        grouped.setdefault(extension,{}).setdefault(directory,[]).append((name,data))
    tree=bytearray();payload=bytearray()
    for extension,dirs in grouped.items():
        tree+=extension.encode()+b'\0'
        for directory,entries in dirs.items():
            tree+=directory.encode()+b'\0'
            for name,data in entries:
                tree+=name.encode()+b'\0'+struct.pack('<IHHIIH',zlib.crc32(data),0,EMBEDDED,len(payload),len(data),0xffff)
                payload+=data
            tree+=b'\0'
        tree+=b'\0'
    tree+=b'\0'
    return struct.pack('<III',MAGIC,1,len(tree))+tree+payload


class VPKTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.path=self.root/'sample_dir.vpk'

    def test_v1_and_v2_preload_and_embedded_offsets(self):
        for version in (1,2):
            self.path.write_bytes(one_entry(version=version))
            package=Package(self.path)
            entry=package.entries['resource/overviews/example.txt']
            self.assertEqual(package.version,version)
            self.assertEqual(entry.size,10)
            self.assertEqual(package.read(entry),b'prepayload')
            self.assertTrue(package.verify(entry))

    def test_external_chunk_is_resolved_beside_directory_and_range_checked(self):
        self.path.write_bytes(one_entry(archive=3,offset=2))
        (self.root/'sample_003.vpk').write_bytes(b'__payload')
        package=Package(self.path);entry=next(iter(package.entries.values()))
        self.assertEqual(package.read(entry),b'prepayload')
        (self.root/'sample_003.vpk').write_bytes(b'__pay')
        with self.assertRaisesRegex(VPKError,'beyond'):package.verify(entry)
        (self.root/'sample_003.vpk').unlink()
        with self.assertRaises(FileNotFoundError):package.verify(entry)

    def test_crc_corruption_and_read_limit_are_rejected(self):
        self.path.write_bytes(one_entry()[:-1]+b'X')
        package=Package(self.path);entry=next(iter(package.entries.values()))
        with self.assertRaisesRegex(VPKError,'CRC mismatch'):package.verify(entry)
        with self.assertRaisesRegex(VPKError,'read limit'):package.read(entry,max_bytes=2)

    def test_bad_headers_tree_strings_and_terminators_are_rejected(self):
        examples=[b'',b'not-vpk-file',struct.pack('<III',MAGIC,99,1)+b'\0',
                  struct.pack('<III',MAGIC,1,10)+b'x',
                  struct.pack('<III',MAGIC,1,3)+b'abc',one_entry(terminator=0)]
        for index,data in enumerate(examples):
            self.path.write_bytes(data)
            with self.subTest(index=index),self.assertRaises(VPKError):Package(self.path)

    def test_preload_only_and_root_extensionless_entry(self):
        tree=(b' \0 \0README\0'+struct.pack('<IHHIIH',zlib.crc32(b'hello'),5,EMBEDDED,0,0,0xffff)
              +b'hello\0\0\0')
        self.path.write_bytes(struct.pack('<III',MAGIC,1,len(tree))+tree)
        package=Package(self.path)
        self.assertEqual(package.read(package.entries['readme']),b'hello')

    def test_duplicate_paths_and_parent_segments_are_rejected(self):
        for files in ({'folder/a.txt':b'a','folder/A.txt':b'b'}, {'../escape/a.txt':b'x'}):
            self.path.write_bytes(radar_fixture(files))
            with self.assertRaises(VPKError):Package(self.path)

    def test_v2_entry_cannot_read_hash_or_signature_trailer_as_payload(self):
        data=one_entry(version=2,offset=3)
        # Extra trailer bytes must not enlarge the declared embedded data region.
        self.path.write_bytes(data+b'123456789')
        package=Package(self.path);entry=next(iter(package.entries.values()))
        with self.assertRaisesRegex(VPKError,'beyond'):package.read(entry)

    def test_radar_inclusion_and_semantic_overview_alignment(self):
        files={name:b'artificial texture fixture' for name in RADAR_FILES}
        files[RADAR_FILES[-1]]=OVERVIEW.replace(b'\n',b'\r\n')
        self.path.write_bytes(radar_fixture(files))
        expected=self.root/'expected.txt';expected.write_bytes(OVERVIEW)
        report=verify_package(self.path,expected,full_crc=True)
        self.assertEqual(report['status'],'passed')
        self.assertEqual(report['crc_verified_entries'],len(RADAR_FILES))
        self.assertEqual(report['signature_verification'],'not performed')
        files[RADAR_FILES[-1]]=OVERVIEW.replace(b'"5.5"',b'"6.0"')
        self.path.write_bytes(radar_fixture(files))
        report=verify_package(self.path,expected)
        self.assertEqual(report['status'],'failed')
        self.assertIn('scale',report['errors'][0])
        del files[RADAR_FILES[0]]
        self.path.write_bytes(radar_fixture(files))
        self.assertIn('Missing packaged asset',verify_package(self.path,expected)['errors'][0])

    def test_overview_rejects_duplicates_nonfinite_values_and_preserves_quoted_slashes(self):
        self.assertEqual(compare_overviews(OVERVIEW+b'// comment\n',OVERVIEW),[])
        for bad in (OVERVIEW.replace(b'"5.5"',b'"nan"'),OVERVIEW.replace(b'}',b'"scale" "5.5"\n}')):
            with self.assertRaises(VPKError):compare_overviews(bad,OVERVIEW)
        with_slashes=OVERVIEW.replace(b'overviews/trento_povo',b'overviews//trento_povo')
        self.assertEqual(compare_overviews(with_slashes,with_slashes),[])


if __name__=='__main__':unittest.main()
