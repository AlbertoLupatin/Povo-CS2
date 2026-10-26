import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import playtest_povo_exterior as walking
from tools.cs2_campus import world


READY='@ Current : game\n[1: trento_povo_campus | main lump | mapload]\nplayers : 1 humans, 0 bots'


class ExteriorWalkingTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.package=self.root/'campus.vpk'
        self.package.write_bytes(b'package identity fixture')
        self.output=self.root/'nested/review'

    def playtest(self, routes):
        return walking.playtest(routes=routes,package=self.package,output=self.output)

    def report(self):
        return json.loads((self.output/'exterior-runtime-walk.json').read_text())

    def test_refuses_other_maps_and_multiplayer_without_moving_player(self):
        for status in (READY.replace('trento_povo_campus','de_dust2'),
                       READY.replace('1 humans','2 humans'),READY.replace('0 bots','1 bots')):
            with self.subTest(status=status),patch.object(walking,'run',return_value=status) as send:
                with self.assertRaisesRegex(RuntimeError,'solo exploration'):
                    self.playtest([('route',(0,0,0),[(1,0,0)])])
                self.assertEqual(send.call_count,1)
                self.assertEqual(send.call_args.args[0],['status'])
                self.assertEqual(self.report()['status'],'failed')

    def test_disconnect_during_movement_keeps_original_error_and_failure_evidence(self):
        with patch.object(walking,'run',side_effect=[READY,'placed',
                    OSError('position connection lost'),OSError('cleanup connection lost')]):
            with self.assertRaisesRegex(OSError,'position connection lost'):
                self.playtest([('route',(0,0,0),[(1,0,0)])])
        report=self.report()
        self.assertEqual(report['status'],'failed')
        self.assertIn('cleanup connection lost',report['cleanup_error'])
        self.assertEqual(report['package_sha256'],hashlib.sha256(self.package.read_bytes()).hexdigest())
        self.assertTrue(report['finished_at_utc'])
        self.assertIn('getpos_exact',(self.output/'exterior-runtime-walk.log').read_text())

    def test_matching_xy_on_wrong_floor_is_a_failure(self):
        position='setpos_exact '+world((1,0,-3.2))
        with patch.object(walking,'run',side_effect=[READY,'placed',position,position,'stopped']):
            with self.assertRaisesRegex(RuntimeError,'Unexpected floor height'):
                self.playtest([('route',(0,0,4.1),[(1,0,4)])])
        self.assertFalse(self.report()['checks'][0]['passed'])


if __name__=='__main__':unittest.main()
