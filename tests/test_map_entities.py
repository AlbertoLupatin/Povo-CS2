from pathlib import Path
import re
import unittest

from tools import cs2_project as project
from tools.build_povo_campus import build_geometry, is_breakable_glass, split_auto_doors
from tools.cs2_campus import LADDER_MATERIAL, TRIGGER_MATERIAL, UNITS, add_auto_doors, add_breakable_glass, add_ladder

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
                       'canteen_0_west_glass_', 'library_0_west_glass_'):
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
    def test_entrance_banks_close_over_their_openings_and_slide_apart(self):
        doors, rest = split_auto_doors(build_geometry(ROOT)[2])
        self.assertEqual([d['name'] for d in doors], ['canteen_inner_entry_bank_0', 'canteen_outer_entry_bank_0',
                                                      'canteen_upper_entry_bank_0', 'library_entry_bank_0', 'p1_entry_bank_0', 'p2_entry_inner_bank_0', 'p2_entry_inner_bank_1',
                                                      'p2_entry_outer_bank_0', 'p2_entry_outer_bank_1'])
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
        # Clients, bots included: 4096 is Source's "Disallow Bots" trigger flag.
        flags = int(re.search(r'"spawnflags"\s+"string"\s+"(\d+)"', trigger)[1])
        self.assertTrue(flags & 1)
        self.assertFalse(flags & 4096)


class LadderTests(unittest.TestCase):
    def test_lift_ladders_clear_the_standing_player_at_every_floor_ledge(self):
        from tools.build_povo_campus import collision_boxes
        _, _, boxes, levels, _ = build_geometry(ROOT)
        physics = collision_boxes(boxes)
        ladders = (levels[0]['elevator']['ladder'],
                   next(l['connection'] for l in levels if 'connection' in l)['povo2']['lift']['ladder'])
        for lo, hi in ladders:
            axis = min(range(2), key=lambda i: hi[i] - lo[i])
            centre = [(a + b) / 2 for a, b in zip(lo, hi)]
            # The engine holds the standing hull just outside the climb face.
            # The native Povo 1 check measured a 0.4072 m centre offset.
            centre[axis] = hi[axis] + .4072
            for step in range(round((hi[2]-1.65 - lo[2]) / .1) + 1):
                z = lo[2] + step * .1
                hits = [name for name, a, b, _ in physics
                        if all(a[i] < centre[i] + .41 and b[i] > centre[i] - .41
                               for i in range(2))
                        and b[2] > z + .02 and a[2] < z + 1.85]
                self.assertEqual(hits, [], (lo, z, hits))

    def test_lift_shaft_ladder_is_a_world_mesh_with_the_ladder_material(self):
        corners = ',\n'.join(f'"{x} {y} {z}"' for x in (-1, 1) for y in (-1, 1) for z in (-1, 1))
        volume = f'''"CMapMesh"
{{
"id" "elementid" "44444444-4444-4444-4444-444444444444"
"nodeID" "int" "9"
"materials" "string_array" [ "materials/tools/toolslightmapres.vmat" ]
"name" "string" "position:0"
"data" "vector3_array" [
{corners}
]
"origin" "vector3" "0 0 0"
}}'''
        source = ('"map_asset_references" "string_array" [ ]\n"world" "CMapWorld"\n{\n'
                  '"children" "element_array" [\n' + volume + '\n]\n}\n')
        text = add_ladder(source, 'ladder', [[0, 0, 0], [.2, .6, 4]])
        self.assertEqual(text.count('"CMapMesh"'), 2)
        self.assertIn(LADDER_MATERIAL, text.split('"world"')[1])
        self.assertIn(f'"{LADDER_MATERIAL}"', text.split('"world"')[0])
        self.assertIn(f'"{.3*UNITS:g} {.1*UNITS:g} {2*UNITS:g}"', text)
        elevator = build_geometry(ROOT)[3][0]['elevator']
        lo, hi = elevator['ladder']
        self.assertGreater(hi[2] - lo[2], 3.6)


if __name__ == '__main__':
    unittest.main()
