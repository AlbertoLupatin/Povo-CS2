import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import povo_circulation as circulation

ROOT=Path(__file__).resolve().parents[1]


class CirculationTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'config/povo_circulation.json').read_text(encoding='utf-8'))

    def test_confirmed_walk_covers_all_photos_and_uses_different_red_stair_cores(self):
        levels=circulation.validate(self.config)
        self.assertEqual(len(levels),6)
        stairs={s['id']:s for s in self.config['stair_connections']}
        self.assertNotEqual(stairs['povo1_ne_2_to_1']['core'],stairs['povo1_se_1_to_0']['core'])
        self.assertEqual(stairs['povo1_se_1_to_0']['photos'],[39,38])

    def test_only_bridge_equality_propagates_and_unmeasured_levels_remain_unknown(self):
        levels=circulation.resolve_elevations(self.config,{'povo1_0':374,'povo1_1':377.6,'povo1_2':382.49})
        self.assertEqual(levels['povo2_1'],382.49)
        self.assertIsNone(levels['povo2_0'])
        self.assertIsNone(levels['povo2_minus1'])
        with self.assertRaisesRegex(ValueError,'conflicting'):
            circulation.resolve_elevations(self.config,{'povo1_2':382.49,'povo2_1':377.6})

    def test_wrong_bridge_floor_duplicate_photo_and_false_room_identity_are_rejected(self):
        for case in ('bridge','photo','room','stairs'):
            config=copy.deepcopy(self.config)
            if case=='bridge':config['bridge_connection']['to_level']='povo1_1'
            if case=='photo':config['segments'][0]['photos'].append(65)
            if case=='room':next(s for s in config['segments'] if s['id']=='a211_or_a212')['room']='A211'
            if case=='stairs':config['stair_connections'][1]['core']='stair_northeast'
            with self.subTest(case=case),self.assertRaises(ValueError):circulation.validate(config)

    def test_complete_report_uses_verified_photo_hashes_and_rejects_stale_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'config').mkdir()
            config=copy.deepcopy(self.config);config['photo_manifest']='photos/manifest.json'
            config_path=root/'config/povo_circulation.json';config_path.write_text(json.dumps(config),encoding='utf-8')
            for name in ('povo_blockout.json','povo1_interior_study.json'):
                (root/'config'/name).write_bytes((ROOT/'config'/name).read_bytes())
            photos=root/'photos';photos.mkdir();image=photos/'fixture.jpeg';image.write_bytes(b'synthetic photo bytes')
            entries=[dict(id=f'P{25+i:03d}',file='fixture.jpeg',walk_photo_number=66-i,sha256=hashlib.sha256(image.read_bytes()).hexdigest()) for i in range(66)]
            (photos/'manifest.json').write_text(json.dumps({'images':entries}),encoding='utf-8')
            result=circulation.build(config_path,root/'review',root=root)
            self.assertEqual(result['verified_walk_photos'],66)
            self.assertIsNone(result['estimated_elevations_metres']['povo2_0'])
            svg=(root/'review/review.svg').read_text(encoding='utf-8')
            self.assertIn('Povo 2 floor 1 = Povo 1 floor 2',svg)
            image.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                circulation.build(config_path,root/'review',root=root)


if __name__=='__main__':unittest.main()
