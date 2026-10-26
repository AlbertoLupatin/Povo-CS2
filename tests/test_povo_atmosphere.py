import json
from pathlib import Path
import re
import tempfile
import unittest

from tools.build_povo_campus import build_geometry
from tools.povo_atmosphere import winter_layers, sound_zones, settings, tune_map
from tools.povo_interactions import extract_static_leaves, brush_entity
from tools.cs2_project import _entity_ranges
from tools.cs2_explore import campus_loaded
from tools.povo_physics_surfaces import write_groups,modeldoc_groups,surface

ROOT=Path(__file__).resolve().parents[1]


class SeasonalCampusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.original,cls.levels,cls.stair=build_geometry()
        cls.boxes=extract_static_leaves(cls.original,cls.levels,cls.stair)
        cls.interactions=cls.levels[0]['interactions']

    def test_replaced_leaves_have_no_static_collision_and_keep_actual_frames(self):
        names={b[0] for b in self.boxes}
        self.assertFalse(any('_parked_leaf' in n for n in names))
        self.assertFalse(any(n.startswith('p2_basement_core_door_') for n in names))
        self.assertTrue(any('stair_door_0_head' in n for n in names))
        self.assertTrue(any('p2_entry_outer_bank_0_head' in n for n in names))
        doors=self.interactions['doors']
        self.assertEqual(len({d['id'] for d in doors}),len(doors))
        self.assertEqual({d['id'] for d in doors if d['kind']=='classroom'},
                         {'classroom_a208','classroom_a215','classroom_a223','classroom_a224'})
        for d in doors:
            lo,hi=d['bounds']
            self.assertTrue(all(a<b for a,b in zip(lo,hi)),d['id'])
            if 'pivot' in d:
                p=d['pivot']
                # Hinges sit at a vertical edge, rather than the panel centre.
                self.assertLess(min(abs(p[0]-lo[0]),abs(p[1]-lo[1]),abs(p[1]-hi[1])),.05)

    def test_only_two_framed_stair_panes_are_breakable(self):
        self.assertEqual(len(self.interactions['glass']),2)
        self.assertTrue(any(b[3]=='window_glass' and 'bridge' in b[0] for b in self.boxes))
        for pane in self.interactions['glass']:
            a,b=pane['bounds']
            self.assertLess(b[1]-a[1],1.6)
            self.assertGreater(a[2],4.4)

    def test_automatic_banks_replace_the_older_entrance_leaves(self):
        from tools.povo_interactions import door_selection
        doors=door_selection(self.levels,self.stair,automatic_entrances=True)
        self.assertTrue(any(d['kind']=='fire' for d in doors))
        self.assertFalse(any(d['kind'] in ('sliding','entrance') for d in doors))

    def test_door_leaves_fit_existing_structural_openings(self):
        walls=[b for b in self.boxes if b[3] in ('wall','courtyard_wall')]
        for door in self.interactions['doors']:
            lo,hi=door['bounds']
            hits=[n for n,a,b,m in walls if all(min(hi[i],b[i])-max(lo[i],a[i])>.002 for i in range(3))]
            self.assertEqual(hits,[],door['id'])

    def test_winter_layers_do_not_cover_indoor_or_sheltered_entrance_floors(self):
        snow,wet=winter_layers(self.boxes,self.levels[0]['exterior'])
        self.assertGreater(len(snow),10);self.assertGreater(len(wet),10)
        for p in ((28,-73.73,4),(45,-73.73,5.8),(40,31.35,4),(18,32,4)):
            layers=[n for n,lo,hi,m in snow+wet if lo[0]<=p[0]<=hi[0] and lo[1]<=p[1]<=hi[1]
                    and abs(hi[2]-p[2])<.1]
            self.assertEqual(layers,[],p)
        for name,lo,hi,mat in snow+wet:
            self.assertLess(hi[2]-lo[2],.011)
            if 'context_concrete' in name:self.assertEqual(mat,'snow_context')

    def test_rooms_halls_garage_and_outdoors_receive_distinct_soundscapes(self):
        metadata={'levels':self.levels}
        zones=sound_zones(metadata)
        self.assertEqual({z['event'] for z in zones},
                         {'Povo.Room','Povo.Hall','Povo.Bathroom','Povo.Garage','Povo.Outside'})
        self.assertEqual(len({z['id'] for z in zones}),len(zones))
        self.assertTrue(all(z['point'][2]<0 for z in zones if z['event']=='Povo.Garage'))

    def test_season_selector_keeps_map_readiness_checks_strict(self):
        status='@ Current : game\n[1: trento_povo_campus_winter | main lump | mapload]'
        self.assertFalse(campus_loaded(status))
        self.assertTrue(campus_loaded(status,'trento_povo_campus_winter'))
        self.assertFalse(campus_loaded(status.replace('game','levelload'),'trento_povo_campus_winter'))
        self.assertNotEqual(settings()['standard']['map'],settings()['winter']['map'])

    def test_physics_groups_preserve_geometry_and_set_actual_contact_surfaces(self):
        fixtures=[('tile',(0,0,0),(1,1,.1),'floor_room'),
                  ('stair',(2,0,0),(3,1,.1),'stair_red'),
                  ('snow',(4,0,0),(5,1,.007),'snow')]
        with tempfile.TemporaryDirectory() as temporary:
            groups=write_groups(Path(temporary),'test',fixtures)
            self.assertEqual(set(groups),{'tile','metal','snow'})
            self.assertEqual(sum(g['boxes'] for g in groups.values()),len(fixtures))
            for g in groups.values():
                text=(Path(temporary)/g['file']).read_text()
                self.assertEqual(len(re.findall(r'^v ',text,re.M)),8)
            source=(ROOT/'cs2/content/trento_povo/models/povo/povo_blockout.vmdl').read_text()
            model=modeldoc_groups(source,groups)
            self.assertEqual(model.count('_class = "PhysicsMeshFile"'),3)
            self.assertEqual(set(re.findall(r'surface_prop\s*=\s*"([^"]+)"',model)),{'tile','metal','snow'})
            self.assertIn('models/povo/test_collision_snow.obj',model)

    def test_brush_cloning_keeps_world_bounds_unique_ids_and_named_material(self):
        points=' '.join(f'"{x} {y} {z}"' for x in (-1,1) for y in (-1,1) for z in (-1,1))
        text='''"world" "CMapWorld" { "children" "element_array" [
"CMapEntity"
{ "id" "elementid" "00000000-0000-0000-0000-000000000001"
 "nodeID" "int" "1"
 "children" "element_array" [
 "CMapMesh" { "id" "elementid" "00000000-0000-0000-0000-000000000002"
 "nodeID" "int" "2" "origin" "vector3" "0 0 0" "angles" "qangle" "0 0 0" "scales" "vector3" "1 1 1"
 "name" "string" "position:0" "data" "vector3_array" [ POINTS ]
 "materials" "string_array" [ "materials/dev/reflectivity_30.vmat" ] } ]
 "entity_properties" "EditGameClassProps" { "classname" "string" "func_buyzone" }
 "origin" "vector3" "0 0 0" "angles" "qangle" "0 0 0" "scales" "vector3" "1 1 1"
 } ] } "map_asset_references" "string_array" [ ]'''.replace('POINTS',points)
        result=brush_entity(text,'test-door','func_door_rotating',
                [([24,-75,4],[24.05,-74,6.2],'materials/test/door.vmat')],
                [('targetname','test_door')],pivot=[24,-75,4])
        entity=next(b for a,z,c,b in _entity_ranges(result) if c=='func_door_rotating')
        self.assertIn('materials/test/door.vmat',entity)
        self.assertNotIn('toolstrigger',entity)
        self.assertNotIn('reflectivity_30',entity)
        ids=re.findall(r'"elementid" "([0-9a-f-]+)"',result)
        self.assertEqual(len(ids),len(set(ids)))


if __name__=='__main__':unittest.main()
