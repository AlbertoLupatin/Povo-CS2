import unittest

from tools import cs2_project as project
from tools.fast_point_entities import enable


BASE = '"world" "CMapWorld" { "children" "element_array" [ "CMapEntity" { "nodeID" "int" "21" } ] }'


class FastPointEntityTests(unittest.TestCase):
    def test_serialization_and_node_ids_match_original_for_a_sequence(self):
        original = project._insert_point_entity
        expected = BASE
        for number in range(25):
            expected = original(expected, str(number), 'light_omni2', f'{number} 0 1', (('name', str(number)),))
        stats, undo = enable(project)
        try:
            actual = BASE
            for number in range(25):
                actual = project._insert_point_entity(actual, str(number), 'light_omni2', f'{number} 0 1', (('name', str(number)),))
            self.assertEqual(actual, expected)
            self.assertEqual(stats['full_scans'], 1)
            self.assertEqual(stats['cached_insertions'], 24)
            self.assertIs(project._insert_point_entity(actual, '1', 'light_omni2', '0 0 0'), actual)
        finally:
            undo()

    def test_external_text_edits_invalidate_cached_allocation(self):
        stats, undo = enable(project)
        try:
            text = project._insert_point_entity(BASE, 'first', 'point_nav_walkable', '0 0 0')
            text = text.replace('"nodeID" "int" "21"', '"nodeID" "int" "999"')
            result = project._insert_point_entity(text, 'second', 'point_nav_walkable', '1 0 0')
            self.assertIn('"nodeID" "int" "1000"', result)
            self.assertEqual(stats['full_scans'], 2)
        finally:
            undo()

    def test_quoted_properties_keep_original_behavior_and_plain_string(self):
        original = project._insert_point_entity
        properties = (('message', 'quoted " value'),)
        expected = original(BASE, 'bad', 'point_worldtext', '0 0 0', properties)
        _stats, undo = enable(project)
        try:
            result = project._insert_point_entity(BASE, 'bad', 'point_worldtext', '0 0 0', properties)
            self.assertEqual(result, expected)
            self.assertIs(type(result), str)
        finally:
            undo()
