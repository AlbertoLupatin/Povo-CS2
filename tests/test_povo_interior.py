import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import build_povo_interior as interior


ROOT=Path(__file__).resolve().parents[1]


class InteriorStudyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.config=json.loads((ROOT/'config/povo1_interior_study.json').read_text())
        self.alignment=json.loads((ROOT/self.config['alignment']).read_text())
        self.campus=json.loads((ROOT/self.config['campus_config']).read_text())
        self.origin=self.campus['origin']
        self.output=self.root/'exports'
        self.config_path=self.root/'config/study.json'
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aDTsAAAAASUVORK5CYII=')
        for profile in self.alignment['profiles']:
            image=self.root/profile['source_file']
            image.parent.mkdir(parents=True,exist_ok=True)
            image.write_bytes(png)
            profile['sha256']=hashlib.sha256(png).hexdigest()
        for name,data in ((self.config['alignment'],self.alignment),(self.config['campus_config'],self.campus)):
            file=self.root/name;file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(json.dumps(data))

    def build(self,force=False):
        self.config_path.write_text(json.dumps(self.config))
        return interior.build_study(self.config_path,self.output,root=self.root,force=force)

    @staticmethod
    def contains_box(box,point):
        _name,lo,hi,_material=box
        return all(lo[i]<point[i]<hi[i] for i in range(3))

    def test_subtract_overlapping_voids_preserves_area_without_overlap(self):
        holes=[(2,2,6,6),(4,4,8,8)]
        pieces=list(interior.subtract_rectangles((0,0,10,10),holes))
        area=sum((r[2]-r[0])*(r[3]-r[1]) for r in pieces)
        self.assertAlmostEqual(area,72)
        for i,rect in enumerate(pieces):
            self.assertFalse(any(interior.intersects(rect,hole) for hole in holes))
            self.assertFalse(any(interior.intersects(rect,other) for other in pieces[i+1:]))

    def test_source_orientation_maps_north_to_local_y_and_east_to_local_x(self):
        bounds=self.alignment['geographic_bounds']
        southwest=interior.local_point(0,0,bounds,self.origin)
        northwest=interior.local_point(1,0,bounds,self.origin)
        southeast=interior.local_point(0,1,bounds,self.origin)
        self.assertEqual(northwest[0],southwest[0])
        self.assertAlmostEqual(northwest[1]-southwest[1],83)
        self.assertEqual(southeast[1],southwest[1])
        self.assertAlmostEqual(southeast[0]-southwest[0],47)

    def test_courtyard_and_upper_stair_reservations_are_actual_slab_holes(self):
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        for level in levels:
            z=level['floor_elevation_metres']-self.origin[2]-.1
            slabs=[b for b in boxes if b[0].startswith(level['id']+'_slab_')]
            self.assertEqual(len(level['voids_local_metres']),5 if level['id']=='academic_first' else 1)
            for rect in level['voids_local_metres']:
                point=((rect[0]+rect[2])/2,(rect[1]+rect[3])/2,z)
                self.assertFalse(any(self.contains_box(b,point) for b in slabs))
                self.assertFalse(any(interior.intersects((b[1][0],b[1][1],b[2][0],b[2][1]),rect) for b in slabs))
        first=levels[1]
        stair=first['voids_local_metres'][1]
        ground_point=((stair[0]+stair[2])/2,(stair[1]+stair[3])/2,levels[0]['floor_elevation_metres']-self.origin[2]-.1)
        self.assertTrue(any(self.contains_box(b,ground_point) for b in boxes if b[0].startswith('academic_ground_slab_')))

    def test_entrance_is_open_at_player_height_and_has_a_header(self):
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        profile=self.alignment['profiles'][0]
        fraction=(profile['entry'][0]-profile['outer'][0])/(profile['outer'][2]-profile['outer'][0])
        x,y=interior.local_point(fraction,1,self.alignment['geographic_bounds'],self.origin)
        z=levels[0]['floor_elevation_metres']-self.origin[2]
        wall=[b for b in boxes if b[0].startswith('academic_ground_outer_3_')]
        self.assertFalse(any(self.contains_box(b,(x,y,z+1)) for b in wall))
        self.assertTrue(any(self.contains_box(b,(x,y,z+2.5)) for b in wall))

    def test_floor_height_is_adjustable_without_moving_the_ground_level(self):
        _boxes,before=interior.build_boxes(self.config,self.alignment,self.origin)
        self.config['levels'][1]['height_offset_metres']+=.4
        _boxes,after=interior.build_boxes(self.config,self.alignment,self.origin)
        self.assertEqual(before[0]['floor_elevation_metres'],after[0]['floor_elevation_metres'])
        self.assertAlmostEqual(after[1]['floor_elevation_metres']-before[1]['floor_elevation_metres'],.4)

    def test_deterministic_mesh_uvs_materials_and_artifact_hashes(self):
        metadata=self.build()
        original={name:(self.output/name).read_bytes() for name in interior.OUTPUTS}
        self.build(force=True)
        self.assertEqual(original,{name:(self.output/name).read_bytes() for name in interior.OUTPUTS})
        mesh=original['povo1_interior_study.obj'].decode().splitlines()
        vertices=[line for line in mesh if line.startswith('v ')]
        uvs=[line for line in mesh if line.startswith('vt ')]
        self.assertEqual(len(vertices),len(uvs))
        for line in mesh:
            if line.startswith('f '):
                for ref in line.split()[1:]:
                    vertex,uv=map(int,ref.split('/'))
                    self.assertEqual(vertex,uv)
                    self.assertTrue(1<=vertex<=len(vertices))
        for name,record in metadata['artifacts'].items():
            self.assertEqual(record['sha256'],hashlib.sha256(original[name]).hexdigest())
        mtl=original['povo1_interior_study.mtl'].decode()
        for name in ('floor_room.png','floor_circulation.png'):
            self.assertIn('map_Kd '+name,mtl)
            self.assertTrue(original[name].startswith(b'\x89PNG\r\n\x1a\n'))

    def test_invalid_route_height_and_door_dimensions_are_rejected(self):
        for case in ('disconnected','height','door','stair','nan'):
            config=copy.deepcopy(self.config)
            if case=='disconnected':config['circulation'][0]['bounds']=[.01,.01,.04,.04]
            if case=='height':config['levels'][1]['height_offset_metres']=2
            if case=='door':config['partitions'][0]['door_width_metres']=100
            if case=='stair':config['stair_opening_inset_metres']=5
            if case=='nan':config['tile_pitch_metres']=float('nan')
            with self.subTest(case=case),self.assertRaises(ValueError):
                interior.build_boxes(config,self.alignment,self.origin)

    def test_failed_regeneration_preserves_previous_export_and_manual_files(self):
        self.build()
        original=(self.output/'povo1_interior_study.obj').read_bytes()
        (self.output/'notes.txt').write_text('Keep this field note')
        with self.assertRaisesRegex(ValueError,'exists'):self.build()
        image=self.root/self.alignment['profiles'][0]['source_file']
        image.write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.build(force=True)
        self.assertEqual((self.output/'povo1_interior_study.obj').read_bytes(),original)
        self.assertEqual((self.output/'notes.txt').read_text(),'Keep this field note')


if __name__=='__main__':unittest.main()
