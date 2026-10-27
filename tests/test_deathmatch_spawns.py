"""Native free-for-all: campus-wide Deathmatch spawns and the mode script."""
import json
import math
from pathlib import Path
import re
import unittest

from tools.audit_povo_exterior_integrated import standing
from tools.build_povo_campus import build_geometry, collision_boxes
from tools.cs2_campus import DM_SPAWN_NAME, FFA_SCRIPT, UNITS, add_free_for_all
from tools.povo_spawns import SPACING, VERTICAL_WEIGHT

ROOT=Path(__file__).resolve().parents[1]


class DeathmatchSpawnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spawns=json.loads((ROOT/'exports/povo_campus/provenance.json').read_text())['deathmatch_spawns']
        _,_,boxes,cls.levels,_=build_geometry()
        cls.physics=collision_boxes(boxes)

    def test_spawns_cover_the_whole_campus(self):
        self.assertGreaterEqual(len(self.spawns),48)
        areas={s['area'] for s in self.spawns}
        self.assertTrue(any(a.startswith('exterior_') for a in areas))
        for area in ('academic_ground','academic_first','p2_ground','p2_basement','p2_parking'):
            self.assertIn(area,areas)
        self.assertTrue(any(a.startswith('library_') for a in areas))
        self.assertTrue(any(a.startswith('canteen_') for a in areas))

    def test_spawns_are_spread_apart(self):
        for i,a in enumerate(self.spawns):
            for b in self.spawns[i+1:]:
                (x0,y0,z0),(x1,y1,z1)=a['point'],b['point']
                gap=math.sqrt((x0-x1)**2+(y0-y1)**2+(VERTICAL_WEIGHT*(z0-z1))**2)
                self.assertGreaterEqual(gap,SPACING,(a['id'],b['id']))

    def test_every_spawn_is_supported_with_standing_room(self):
        meshes=self.levels[0]['exterior']['collision_meshes']
        for spawn in self.spawns:
            foot,obstacles=standing(*spawn['point'],self.physics,meshes)
            self.assertIsNotNone(foot,spawn)
            self.assertAlmostEqual(foot,spawn['point'][2],delta=.02,msg=spawn)
            self.assertFalse(obstacles,spawn)

    def test_no_spawn_inside_a_ladder_shaft(self):
        ladders=[self.levels[0]['elevator']['ladder'],self.levels[1]['connection']['povo2']['lift']['ladder']]
        for spawn in self.spawns:
            x,y,z=spawn['point']
            for lo,hi in ladders:
                self.assertFalse(lo[0]-1.5<=x<=hi[0]+1.5 and lo[1]-1.5<=y<=hi[1]+1.5 and lo[2]-.5<=z<=hi[2],spawn)


class FreeForAllEntityTests(unittest.TestCase):
    def test_map_gets_one_deathmatch_spawn_per_point_and_the_script(self):
        text=('"map_asset_references" "string_array"\n[\n]\n'
              '"world" "CMapWorld"\n{\n"children" "element_array"\n[\n]\n}\n')
        spawns=[dict(id='dm_00',point=[1,2,3],yaw=90.0),dict(id='dm_01',point=[4,5,6],yaw=180.0)]
        text=add_free_for_all(text,spawns)
        self.assertEqual(text.count('"info_deathmatch_spawn"'),2)
        self.assertEqual(text.count(f'"targetname" "string" "{DM_SPAWN_NAME}"'),2)
        self.assertIn('"angles" "qangle" "0 90.0 0"',text)
        self.assertIn(f'"{-2*UNITS:.3f} {1*UNITS:.3f} {3.05*UNITS:.3f}"',text)
        self.assertEqual(text.count('"point_script"'),1)
        self.assertEqual(text.count(f'"{FFA_SCRIPT}"'),2)  # asset reference and entity key

    def test_script_only_turns_deathmatch_into_free_for_all(self):
        script=(ROOT/'cs2/content/trento_povo'/FFA_SCRIPT.replace('.vjs','.js')).read_text()
        self.assertRegex(script,r'type:\s*1,\s*mode:\s*2')
        self.assertIn('if (!isDeathmatch()) return;',script)
        settings=dict(re.findall(r'\["(\w+)",\s*"?(\w+)"?\]',script))
        self.assertEqual(settings['mp_teammates_are_enemies'],'1')
        self.assertEqual(settings['mp_randomspawn'],'1')
        self.assertEqual(settings['mp_randomspawn_los'],'1')
        self.assertEqual(settings['bot_quota'],'0')
        # Nav-generated spawns are switched off; only the named campus ones remain.
        self.assertIn(f'const CAMPUS_SPAWN = "{DM_SPAWN_NAME}";',script)
        self.assertIn('input: "SetDisabled"',script)


if __name__=='__main__':unittest.main()
