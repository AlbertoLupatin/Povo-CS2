import unittest
from unittest.mock import patch

from tools.cs2_explore import campus_loaded, explore


READY = '@ Current  :  game\n[1: trento_povo_campus | main lump | mapload]'
SOLO = 'players  : 1 humans, 0 bots (not hibernating)\nsetpos_exact 2800 800 158'


class ExplorationTests(unittest.TestCase):
    def test_does_not_configure_loading_or_another_map(self):
        self.assertFalse(campus_loaded(READY.replace('game\n', 'levelload\n')))
        self.assertFalse(campus_loaded(READY.replace('trento_povo_campus', 'de_dust2')))
        with patch('tools.cs2_explore.run', side_effect=[
            OSError('not listening yet'), READY.replace('trento_povo_campus', 'de_dust2'),
            READY, 'configured', SOLO,
        ]) as send, patch('tools.cs2_explore.time.sleep'):
            explore(timeout=30)
        self.assertEqual([c.args[0] for c in send.call_args_list[:3]], [['status']]*3)
        self.assertIn('jointeam 2', send.call_args_list[3].args[0])
        self.assertIn('noclip 0', send.call_args_list[4].args[0])

    def test_reports_failure_if_bots_are_still_present(self):
        with patch('tools.cs2_explore.run', side_effect=[READY, '', SOLO.replace('0 bots', '3 bots')]):
            with self.assertRaisesRegex(RuntimeError, 'solo session'):
                explore(timeout=5)

    def test_flight_is_opt_in(self):
        with patch('tools.cs2_explore.run', side_effect=[READY, '', SOLO]) as send:
            explore(timeout=5, fly=True)
        self.assertIn('noclip 1', send.call_args_list[-1].args[0])


if __name__ == '__main__':
    unittest.main()
