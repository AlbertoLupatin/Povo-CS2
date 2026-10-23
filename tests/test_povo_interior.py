import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import build_povo_interior as interior
from tools import audit_povo_interior as audit
from tools import povo_room_fitout as fitout


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
        photo_manifest=self.root/self.config['photo_reference']['manifest']
        source=json.loads((ROOT/self.config['photo_reference']['manifest']).read_text())
        photos=[]
        for entry in source['images']:
            if entry['id'] not in self.config['photo_reference']['ids']:continue
            photo=photo_manifest.parent/entry['file'];photo.parent.mkdir(parents=True,exist_ok=True)
            photo.write_bytes(png);entry['sha256']=hashlib.sha256(png).hexdigest();photos.append(entry)
        photo_manifest.write_text(json.dumps({'images':photos}))

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
            if case=='disconnected':config['levels'][0]['circulation'][0]['pixel_bounds']=[1000,500,1100,530]
            if case=='height':config['levels'][1]['height_offset_metres']=2
            if case=='door':config['levels'][0]['rooms'][0]['door_width_metres']=100
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

    def test_exported_mesh_clearance_audit_reaches_both_levels_circulation(self):
        self.build()
        result=audit.run_audit(self.config_path,self.output,self.root/'audit',root=self.root)
        self.assertEqual(result['status'],'passed')
        self.assertEqual(len(result['levels']),2)
        self.assertEqual([len(level['stations']) for level in result['levels']],[16,32])
        self.assertGreater(len(audit.read_box_mesh(self.output/'povo1_interior_study.obj')),164)
        svg=(self.root/'audit/review.svg').read_text()
        self.assertIn('data:image/png;base64,',svg)

    def test_room_inventory_varies_by_floor_and_doors_are_actual_mesh_openings(self):
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        self.assertEqual({r['label'] for r in levels[0]['rooms']},{f'A{i}' for i in range(101,111)})
        self.assertEqual({r['label'] for r in levels[1]['rooms']},{f'A{i}' for i in range(201,225)}|{'LAB'})
        for level in levels:
            z=level['floor_elevation_metres']-self.origin[2]
            self.assertGreater(len({tuple(r['approximate_dimensions_metres']) for r in level['rooms']}),1)
            for room in level['rooms']:
                a,b,c,d=room['bounds'];fraction=room['door_fraction'];side=room['door_side']
                u,v=(a if side=='u_min' else c,b+(d-b)*fraction) if side.startswith('u_') else (a+(c-a)*fraction,b if side=='v_min' else d)
                x,y=interior.local_point(u,v,self.alignment['geographic_bounds'],self.origin)
                with self.subTest(room=room['label']):
                    self.assertFalse(any(self.contains_box(box,(x,y,z+1)) for box in boxes))
                    self.assertTrue(any(self.contains_box(box,(x,y,z+2.5)) for box in boxes))
        # The first floor's former cloned exterior entrance now crosses A212;
        # it must remain a closed outer wall until the real access is established.
        p=self.alignment['profiles'][1];u=(p['entry'][0]-p['outer'][0])/(p['outer'][2]-p['outer'][0])
        x,y=interior.local_point(u,1,self.alignment['geographic_bounds'],self.origin)
        z=levels[1]['floor_elevation_metres']-self.origin[2]
        self.assertTrue(any(self.contains_box(box,(x,y,z+1)) for box in boxes))

    def test_overlapping_rooms_and_shared_wall_duplicates_are_rejected_or_merged(self):
        config=copy.deepcopy(self.config)
        config['levels'][0]['rooms'][0]['pixel_bounds']=config['levels'][0]['rooms'][1]['pixel_bounds']
        with self.assertRaisesRegex(ValueError,'overlap'):interior.build_boxes(config,self.alignment,self.origin)
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        rooms={r['label']:r for r in levels[0]['rooms']}
        a=rooms['A109']['bounds'];b=rooms['A110']['bounds']
        self.assertEqual(a[2],b[0])
        x,y=interior.local_point(a[2],(a[1]+a[3])/2,self.alignment['geographic_bounds'],self.origin)
        z=levels[0]['floor_elevation_metres']-self.origin[2]+1
        self.assertEqual(sum(self.contains_box(box,(x,y,z)) for box in boxes),1)

    def test_pilot_window_cuts_the_real_wall_and_furniture_stays_in_its_room(self):
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        level=levels[1];room=next(r for r in level['rooms'] if r['id']=='a224')
        x0,y0,x1,y1=room['footprint_local_metres'];z=level['floor_elevation_metres']-self.origin[2]
        walls=[b for b in boxes if b[3] in ('wall','courtyard_wall')]
        self.assertFalse(any(self.contains_box(b,(x0,(y0+y1)/2,z+1)) for b in walls))
        self.assertTrue(any(self.contains_box(b,(x0,(y0+y1)/2,z+.05)) for b in walls))
        self.assertTrue(any(self.contains_box(b,(x0,(y0+y1)/2,z+2.85)) for b in walls))
        furniture=[b for b in boxes if b[0].startswith('academic_first_room_a224_') and b[3] in ('desk_dark','seat_wood')]
        self.assertTrue(furniture)
        for _name,lo,hi,_material in furniture:
            self.assertTrue(x0<lo[0]<hi[0]<x1 and y0<lo[1]<hi[1]<y1)
        self.assertGreater(room['fitout']['seats'],0)
        self.assertTrue(any(b[3]=='ceiling_panel' for b in boxes))
        self.assertTrue(any(b[3]=='floor_wood' for b in boxes))

    def test_window_subtraction_preserves_solid_volume_and_has_no_overlaps(self):
        box=('wall',(0,0,0),(3,4,5),'wall');hole=((1,1,1),(2,3,4))
        pieces=fitout.subtract_box(box,hole)
        def volume(lo,hi):return (hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2])
        self.assertEqual(sum(volume(lo,hi) for _,lo,hi,_ in pieces),54)
        for i,(_,lo,hi,_) in enumerate(pieces):
            for _,other_lo,other_hi,_ in pieces[i+1:]:
                self.assertFalse(all(max(lo[a],other_lo[a])<min(hi[a],other_hi[a]) for a in range(3)))
            self.assertFalse(all(max(lo[a],hole[0][a])<min(hi[a],hole[1][a]) for a in range(3)))

    def test_photo_change_requires_catalogue_update_and_rebuild(self):
        self.build()
        photo_path=self.root/self.config['photo_reference']['manifest']
        entry=json.loads(photo_path.read_text())['images'][0]
        (photo_path.parent/entry['file']).write_bytes(b'changed photo')
        before=(self.output/'povo1_interior_study.obj').read_bytes()
        with self.assertRaisesRegex(ValueError,'Photo reference hash mismatch'):self.build(force=True)
        self.assertEqual((self.output/'povo1_interior_study.obj').read_bytes(),before)
        with self.assertRaisesRegex(ValueError,'Photo source changed'):
            audit.run_audit(self.config_path,self.output,self.root/'audit',root=self.root)

    def test_pilot_cannot_silently_move_to_an_interior_room_or_nonclassroom(self):
        for target in ('lab','a217'):
            config=copy.deepcopy(self.config);config['classroom_fitouts'][0]['room']=target
            with self.subTest(room=target),self.assertRaises(ValueError):
                interior.build_boxes(config,self.alignment,self.origin)

    def test_corrected_rows_span_the_room_with_one_metre_side_aisles_and_rear_windows(self):
        boxes,levels=interior.build_boxes(self.config,self.alignment,self.origin)
        half=self.config['wall_thickness_metres']/2
        for identifier in ('a224','a223'):
            room=next(r for r in levels[1]['rooms'] if r['id']==identifier)
            x0,y0,x1,y1=room['footprint_local_metres']
            prefix='academic_first_room_'+identifier+'_'
            rows=[b for b in boxes if b[0].startswith(prefix+'desk_row_') and b[0].endswith('_top')]
            self.assertTrue(rows)
            for _,lo,hi,_ in rows:
                self.assertAlmostEqual(lo[1]-(y0+half),1.0)
                self.assertAlmostEqual((y1-half)-hi[1],1.0)
                self.assertLess(lo[1],(y0+y1)/2)
                self.assertGreater(hi[1],(y0+y1)/2)
            glass=next(b for b in boxes if b[0]==prefix+'window_glass')
            board=next(b for b in boxes if b[0]==prefix+'board')
            self.assertLess(glass[2][0],min(b[1][0] for b in rows))
            self.assertGreater(board[1][0],max(b[2][0] for b in rows))
            chair=next(b for b in boxes if b[0]==prefix+'chair_0_0_back')
            self.assertLess(chair[2][0],rows[0][1][0])
        duplicate=self.config['classroom_fitouts'][1]
        self.assertIn('not identification',duplicate['location_status'])

    def test_impossible_window_orientation_and_blocked_front_door_are_rejected(self):
        for case in ('window','door','duplicate'):
            config=copy.deepcopy(self.config)
            if case=='window':config['classroom_fitouts'][0]['teaching_side']='south'
            if case=='door':next(r for r in config['levels'][1]['rooms'] if r['id']=='a224')['door_fraction']=.5
            if case=='duplicate':config['classroom_fitouts'].append(copy.deepcopy(config['classroom_fitouts'][0]))
            with self.subTest(case=case),self.assertRaises(ValueError):
                interior.build_boxes(config,self.alignment,self.origin)

    def test_clearance_audit_accounts_for_width_and_door_headers(self):
        boxes=[('ground_slab_0',(0,0,-.2),(10,10,0),'floor_room'),
               ('ground_wall_0',(4.9,0,0),(5.1,4.4,2.9),'wall'),
               ('ground_wall_1',(4.9,5.6,0),(5.1,10,2.9),'wall'),
               ('ground_header',(4.9,4.4,2.15),(5.1,5.6,2.9),'wall')]
        level={'id':'ground','floor_elevation_local':0}
        stations=[{'id':'entrance','point':(1,5)},{'id':'destination','point':(9,5)}]
        report,*_=audit.audit_level(boxes,level,stations)
        self.assertEqual(report['status'],'passed')
        for params in ({'width':1.4},{'height':2.3}):
            report,*_=audit.audit_level(boxes,level,stations,**params)
            self.assertEqual(report['status'],'failed')
            self.assertFalse(report['stations'][1]['reachable_from_entrance'])

    def test_clearance_audit_cannot_cross_an_actual_missing_floor_strip(self):
        boxes=[('ground_slab_0',(0,0,-.2),(4.9,10,0),'floor_room'),
               ('ground_slab_1',(5.1,0,-.2),(10,10,0),'floor_room')]
        level={'id':'ground','floor_elevation_local':0}
        stations=[{'id':'entrance','point':(1,5)},{'id':'destination','point':(9,5)}]
        report,*_=audit.audit_level(boxes,level,stations)
        self.assertEqual(report['status'],'failed')
        self.assertTrue(report['stations'][1]['has_clearance'])
        self.assertFalse(report['stations'][1]['reachable_from_entrance'])

    def test_clearance_audit_rejects_stale_sources_and_output_over_source_assets(self):
        self.build()
        with self.assertRaisesRegex(ValueError,'separate directory'):
            audit.run_audit(self.config_path,self.output,self.output,root=self.root)
        self.config_path.write_text(self.config_path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'rebuild'):
            audit.run_audit(self.config_path,self.output,self.root/'audit',root=self.root)
        with self.assertRaisesRegex(ValueError,'half the standing width'):
            audit.audit_level([],{'id':'ground','floor_elevation_local':0},[],cell=1)


if __name__=='__main__':unittest.main()
