from pathlib import Path
import re
import unittest

from tools import cs2_project as project
from tools.build_povo_campus import build_geometry, is_breakable_glass, split_auto_doors
from tools.cs2_campus import TRIGGER_MATERIAL, UNITS, add_auto_doors, add_breakable_glass

ROOT = Path(__file__).resolve().parents[1]


def minimal_map():
    """A CMapWorld holding one box buy-zone mesh, the entity template the map step clones."""
    corners = ',\n'.join(f'"{x} {y} {z}"' for x in (-1, 1) for y in (-1, 1) for z in (-1, 1))
    trigger = f'''"CMapEntity"
{{
"id" "elementid" "11111111-1111-1111-1111-111111111111"
"nodeID" "int" "7"
"referenceID" "uint64" "0x1234"
"children" "element_array" [
"CMapMesh"
{{
"id" "elementid" "22222222-2222-2222-2222-222222222222"
"nodeID" "int" "8"
"materials" "string_array" [ "{TRIGGER_MATERIAL}" ]
"name" "string" "position:0"
"data" "vector3_array" [
{corners}
]
"origin" "vector3" "0 0 0"
}}
]
"connectionsData" "element_array" [ ]
"entity_properties" "EditGameClassProps"
{{
"id" "elementid" "33333333-3333-3333-3333-333333333333"
"classname" "string" "func_buyzone"
"TeamNum" "string" "2"
}}
"origin" "vector3" "0 0 0"
}}'''
    source = ('"map_asset_references" "string_array" [ ]\n"world" "CMapWorld"\n{\n'
              '"children" "element_array" [\n' + trigger + '\n]\n}\n')
    return source


class BreakableGlassSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boxes = build_geometry(ROOT)[2]
        cls.glass = [b for b in boxes if 'glass' in b[3]]
        cls.breakable = [b for b in cls.glass if is_breakable_glass(b)]

    def test_receptions_vehicles_screens_and_backdrops_stay_sealed(self):
        for name, _, _, material in self.breakable:
            self.assertNotEqual(material, 'reception_glass')
            self.assertFalse(any(t in name for t in ('_cabin', '_screen_', 'residential_', 'povo2_west_glazing')), name)
        self.assertTrue(any(m == 'reception_glass' and not is_breakable_glass(b) for b in self.glass for m in [b[3]]))

    def test_playable_windows_doors_bridge_and_front_wings_break(self):
        names = [b[0] for b in self.breakable]
        for prefix in ('academic_first_room_a224_window', 'academic_first_link_bridge_east_glass',
                       'exterior_p2_entry_outer_bank_', 'stair_ne_window_',
                       'exterior_povo1_library_0_pane_', 'exterior_povo1_library_1_pane_'):
            self.assertTrue(any(n.startswith(prefix) for n in names), prefix)
        # The library/canteen wings are separate panes over an opaque core, not one glass mass.
        self.assertFalse(any('povo1_library' in n and n.endswith('_mass') for n, *_ in self.glass))
        for _, lo, hi, _ in self.breakable:
            self.assertTrue(all(a < b for a, b in zip(lo, hi)))


class BreakableGlassEntityTests(unittest.TestCase):
    def test_each_pane_becomes_one_func_breakable_glass_box(self):
        source = minimal_map()
        panes = [dict(name='a', lo=[0, 0, 0], hi=[2, .05, 3], material='materials/glass/glass01.vmat'),
                 dict(name='b', lo=[5, 5, 1], hi=[5.05, 7, 2], material='materials/x/glass.vmat')]
        text = add_breakable_glass(source, panes)
        blocks = [b for _, _, c, b in project._entity_ranges(text) if c == 'func_breakable']
        self.assertEqual(len(blocks), 2)
        self.assertIn('materials/glass/glass01.vmat', blocks[0])
        self.assertNotIn(TRIGGER_MATERIAL, blocks[0])
        self.assertIn('"health" "string" "1"', blocks[0])
        self.assertIn('"material" "string" "0"', blocks[0])
        self.assertNotIn('TeamNum', blocks[0])
        # Local east/north extents swap into Source X/Y.
        self.assertIn(f'"{.025*UNITS:g} {1*UNITS:g} {1.5*UNITS:g}"', blocks[0])
        ids = re.findall(r'"elementid"\s+"([^"]+)"', text)
        nodes = re.findall(r'"nodeID"\s+"int"\s+"(\d+)"', text)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(nodes), len(set(nodes)))
        self.assertIn('"materials/x/glass.vmat"', text.split('"world"')[0])
        self.assertEqual(add_breakable_glass(source, []), source)


class AutoDoorTests(unittest.TestCase):
    def test_povo2_banks_close_over_their_openings_and_slide_apart(self):
        doors, rest = split_auto_doors(build_geometry(ROOT)[2])
        self.assertEqual(len(doors), 4)
        self.assertFalse(any('_parked_leaf' in b[0] or '_leaf_bottom_' in b[0] for b in rest))
        for door in doors:
            self.assertEqual(len(door['parts']), 6)
            leaves = sorted((p for p in door['parts'] if p['name'].endswith(('leaf_-1', 'leaf_1'))), key=lambda p: p['lo'][1])
            self.assertEqual([p['yaw'] for p in leaves], [0, 180])
            # Closed leaves meet in the middle of the 1.8 m opening.
            self.assertAlmostEqual(leaves[0]['hi'][1], leaves[1]['lo'][1], places=6)
            self.assertAlmostEqual(leaves[1]['hi'][1] - leaves[0]['lo'][1], 1.8, places=6)
            lo, hi = door['trigger']
            for p in door['parts']:
                self.assertTrue(all(a <= b for a, b in zip(lo, p['lo'])) and all(a >= b for a, b in zip(hi, p['hi'])))

    def test_trigger_opens_and_closes_the_named_doors(self):
        source = minimal_map()
        parts = [dict(name='leaf_-1', lo=[0, 0, 0], hi=[.03, .9, 2.5], material='materials/x/entry.vmat', yaw=0),
                 dict(name='leaf_1', lo=[0, .9, 0], hi=[.03, 1.8, 2.5], material='materials/x/entry.vmat', yaw=180)]
        text = add_auto_doors(source, [dict(name='bank', parts=parts, trigger=([-2, -1, 0], [2, 3, 2.6]))])
        entities = project._entity_ranges(text)
        doors = [b for _, _, c, b in entities if c == 'func_door']
        trigger = next(b for _, _, c, b in entities if c == 'trigger_multiple')
        self.assertEqual(len(doors), 2)
        self.assertIn('"movedir" "string" "0 180 0"', doors[1])
        self.assertIn('materials/x/entry.vmat', doors[0])
        self.assertIn(TRIGGER_MATERIAL, trigger)
        rows = re.findall(r'"outputName" "string" "(\w+)"\n"targetType" "int" "7"\n"targetName" "string" "([^"]+)"\n"inputName" "string" "(\w+)"', trigger)
        self.assertEqual(rows, [('OnStartTouch', 'trento_door_bank', 'Open'), ('OnEndTouchAll', 'trento_door_bank', 'Close')])
        self.assertTrue(all('"targetname" "string" "trento_door_bank"' in d for d in doors))
        ids = re.findall(r'"elementid"\s+"([^"]+)"', text)
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':
    unittest.main()
