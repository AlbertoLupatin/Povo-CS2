from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import playtest_povo_features as features
from tools import playtest_povo_match as match


class NativeFeatureGuardTests(unittest.TestCase):
    def test_match_checks_refuse_other_humans_without_mutations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'build/package').mkdir(parents=True)
            (root/'build/package/trento_povo_campus.vpk').write_bytes(b'package fixture')
            status='@ Current : game\n[1: trento_povo_campus | main lump | mapload]\nplayers : 2 humans, 0 bots'
            with patch.object(match,'ROOT',root),patch.object(match,'run',return_value=status) as send:
                with self.assertRaisesRegex(RuntimeError,'exactly one human'):
                    match.playtest()
                self.assertEqual(send.call_count,1)
                self.assertEqual(send.call_args.args[0],['status'])

    def test_refuses_wrong_map_or_other_players_without_mutating_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'build/package').mkdir(parents=True)
            (root/'build/package/trento_povo_campus.vpk').write_bytes(b'package fixture')
            for status in ('@ Current : game\n[1: de_dust2 | main lump | mapload]\nplayers : 1 humans, 0 bots',
                           '@ Current : game\n[1: trento_povo_campus | main lump | mapload]\nplayers : 2 humans, 0 bots'):
                with patch.object(features,'ROOT',root),patch.object(features,'run',return_value=status) as send:
                    with self.assertRaisesRegex(RuntimeError,'Matching solo exploration required'):
                        features.playtest(output=root/'report')
                    self.assertEqual(send.call_count,1)
                    self.assertEqual(send.call_args.args[0],['status'])


if __name__=='__main__':unittest.main()
