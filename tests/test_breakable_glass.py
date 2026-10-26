from pathlib import Path
import re
import unittest

from tools import cs2_project as project
from tools.build_povo_campus import build_geometry, is_breakable_glass
from tools.cs2_campus import TRIGGER_MATERIAL, UNITS, add_breakable_glass

ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == '__main__':
    unittest.main()
