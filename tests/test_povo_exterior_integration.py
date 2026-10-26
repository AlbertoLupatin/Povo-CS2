"""Regression coverage for exterior integration beside independently edited interiors."""
from pathlib import Path
import re
import tempfile
import unittest

from tools.build_povo_campus import build_geometry
from tools.povo_exterior_materials import write_materials,OPACITY
from tools.audit_povo_exterior_integrated import audit
from tools import cs2_project as project
from tools.cs2_campus import UNITS,skip_nav_analysis


class ExteriorIntegrationTests(unittest.TestCase):
    def test_approved_routes_have_support_and_standing_clearance(self):
        report=audit()
        self.assertEqual(report['status'],'passed',report)
        self.assertGreaterEqual(report['samples'],1200)
        self.assertEqual(len(report['routes']),9)

    def test_other_chat_office_restroom_furniture_is_preserved(self):
        base=build_geometry(include_exterior=False)[2]
        combined=build_geometry()[2]
        def fixtures(boxes):
            return {b[0]:b for b in boxes if any(s in b[0] for s in
                    ('_front_desk','_back_desk','_visitor_chair',
                     '_female_toilet_','_male_toilet_','_male_sink','_female_sink'))}
        self.assertGreater(len(fixtures(base)),50)
        self.assertEqual(fixtures(base),fixtures(combined))

    def test_compiled_glass_is_more_opaque_and_visible_from_both_sides(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_materials(root)
            text=(root/'entry_glass.vmat').read_text()
            self.assertEqual(OPACITY['entry_glass'],.84)
            self.assertIn('F_TRANSLUCENT "1"',text)
            self.assertIn('g_flOpacityScale "0.84"',text)
            self.assertIn('F_RENDER_BACKFACES "1"',text)
            self.assertIn('g_flOpacityScale "0.32"',(root/'glass.vmat').read_text())
            self.assertIn('TextureLayer1Color',text)
            self.assertIn('TextureLayer1Translucency',text)
            self.assertNotIn('F_TRANSLUCENT',(root/'fence.vmat').read_text())


    def test_exterior_map_skips_open_area_bot_analysis(self):
        corners=',\n'.join(f'"{x} {y} {z}"' for x in (-1,1) for y in (-1,1) for z in (-1,1))
        trigger=f'''"CMapEntity"
{{
"id" "elementid" "11111111-1111-1111-1111-111111111111"
"nodeID" "int" "7"
"referenceID" "uint64" "0x1234"
"children" "element_array" [
"CMapMesh"
{{
"id" "elementid" "22222222-2222-2222-2222-222222222222"
"nodeID" "int" "8"
"origin" "vector3" "0 0 0"
"name" "string" "position:0"
"data" "vector3_array" [
{corners}
]
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
        source='"world" "CMapWorld"\n{\n"children" "element_array" [\n'+trigger+'\n]\n}\n'
        text=skip_nav_analysis(source)
        entities=project._entity_ranges(text)
        block=next(b for _,_,c,b in entities if c=='trigger_survival_playarea')
        self.assertEqual([c for _,_,c,_ in entities].count('func_buyzone'),1)
        self.assertNotIn('TeamNum',block)
        ids=re.findall(r'"elementid"\s+"([^"]+)"',text)
        nodes=re.findall(r'"nodeID"\s+"int"\s+"(\d+)"',text)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len(nodes),len(set(nodes)))
        self.assertIn(f'"{124*UNITS:g} {86*UNITS:g} {14*UNITS:g}"',block)
        self.assertEqual(skip_nav_analysis(source),text)


if __name__=='__main__':unittest.main()
