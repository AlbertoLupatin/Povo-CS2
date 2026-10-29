"""Protect the native terrace runner from controlling an unrelated game."""
from unittest import TestCase
from unittest.mock import Mock

from tools.playtest_povo2_minus1_terrace import MAP, TerraceDriver
from tools.playtest_povo_survey import GuardError


def status(map_name=MAP, humans=1, bots=0, current='game'):
    return (f'@ Current : {current}\nplayers : {humans} humans, {bots} bots\n'
            f'loaded spawngroup : SV: [1: {map_name} | main lump | mapload]\n')


class NativeTerraceGuardTests(TestCase):
    def test_unrelated_or_shared_sessions_rejected_before_movement(self):
        for response in (status(map_name='trento_povo_campus'), status(humans=2),
                         status(bots=1), status(current='levelload')):
            with self.subTest(response=response):
                console = Mock(); console.command.return_value = response
                driver = TerraceDriver(console, MAP)
                with self.assertRaises(GuardError):
                    driver.execute(dict(kind='walk', path=[[0,0,0], [1,0,0]]))
                self.assertFalse(driver.authorized)
                console.command.assert_called_once_with('status', .35)
                console.pulse.assert_not_called()

    def test_unique_solo_scene_authorized(self):
        console = Mock(); console.command.return_value = status()
        driver = TerraceDriver(console, MAP)
        driver.guard()
        self.assertTrue(driver.authorized)

    def test_old_authorization_revoked_if_another_player_joins(self):
        console = Mock(); console.command.side_effect = [status(), status(humans=2)]
        driver = TerraceDriver(console, MAP)
        driver.guard()
        with self.assertRaises(GuardError):
            driver.guard()
        self.assertFalse(driver.authorized)
