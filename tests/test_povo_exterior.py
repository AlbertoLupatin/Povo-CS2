"""Exterior geometry contracts that matter when merging this study later."""
import math
import unittest

from tools.build_povo_exterior import build, strip


class ExteriorStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boxes,cls.meshes,cls.meta,_=build()

    def test_ramp_is_straight_and_reaches_declared_parking_level(self):
        ramp=next(m for m in self.meshes if m['name']=='garage_ramp_straight')
        a,b=self.meta['config']['garage_ramp']['centreline']
        top=ramp['vertices'][4:]
        for indices,endpoint in (((0,1),a),((2,3),b)):
            midpoint=[sum(top[i][axis] for i in indices)/2 for axis in range(3)]
            for actual,want in zip(midpoint,endpoint):self.assertAlmostEqual(actual,want)
        self.assertEqual(a[0],b[0])
        self.assertAlmostEqual(b[2],-3.2)
        self.assertGreater(self.meta['garage_integration']['horizontal_gap_metres'],0)
        self.assertEqual(self.meta['garage_integration']['exterior_gap_metres'],0)

    def test_covered_parking_meets_ramp_and_leaves_portal_clear(self):
        g=self.meta['config']['covered_parking'];a,b,c,d=g['bounds']
        x,y,z=self.meta['garage_integration']['endpoint']
        self.assertTrue(a<x<c);self.assertEqual(y,b);self.assertEqual(z,g['z'])
        self.assertGreaterEqual(g['ceiling_z']-z,3)
        # Walk a standing player from the final ramp section into the garage.
        for yy in (y-.3,y,y+.3,y+1,y+3):
            sample=((x-.4,yy-.1,z+.03),(x+.4,yy+.1,z+1.85))
            for name,lo,hi,mat in self.boxes:
                if not name.startswith('garage_'):continue
                overlap=all(lo[i]<sample[1][i] and hi[i]>sample[0][i] for i in range(3))
                self.assertFalse(overlap,name)
        roof=next(box for box in self.boxes if box[0]=='garage_roof')
        self.assertEqual(roof[1][:2],(a,b));self.assertEqual(roof[2][:2],(c,d))

    def test_north_road_reaches_povo2_end_without_descending_with_ramp(self):
        points=self.meta['config']['north_road']['points']
        self.assertEqual(points[0][0],self.meta['config']['garage_ramp']['centreline'][0][0])
        self.assertLess(points[0][1],self.meta['config']['garage_ramp']['centreline'][0][1])
        self.assertGreaterEqual(max(p[1] for p in points),112)
        self.assertTrue(all(p[2]==3 for p in points))

    def test_povo1_front_passage_is_open_at_standing_height(self):
        # The gap between the library wings must remain a real entrance passage.
        z=self.meta['config']['frontages']['street_level']
        for x in (36,40,45,50,53):
            for name,lo,hi,mat in self.boxes:
                if not name.startswith(('povo1_library_','povo1_passage_')):continue
                self.assertFalse(lo[0]<x<hi[0] and lo[1]<-73<hi[1] and lo[2]<z+1.7<hi[2],name)

    def test_bridge_has_vehicle_clearance_at_road_crossing(self):
        deck=next(b for b in self.boxes if b[0]=='bridge_deck')
        road=next(m for m in self.meshes if m['name']=='road_2')
        road_z=road['vertices'][4][2]
        self.assertGreaterEqual(deck[1][2]-road_z,3.0)

    def test_review_cameras_remain_inside_the_named_live_rooms(self):
        self.assertEqual({c['room'] for c in self.meta['cameras']},{'A221','A222','A223','A224'})
        for cam in self.meta['cameras']:
            a,b,c,d=cam['source_room_bounds'];x,y,z=cam['position']
            self.assertTrue(a<x<c and b<y<d)
            self.assertLess(cam['target'][0],x)
            # Surface lot lies between the west facade and residential backdrop.
            self.assertLess(self.meta['config']['surface_parking']['bounds'][2],a)
            self.assertLess(self.meta['config']['residential']['bounds'][2],self.meta['config']['surface_parking']['bounds'][0])

    def test_closed_sloping_surfaces_have_positive_outward_volume(self):
        for mesh in self.meshes:
            if len(mesh['vertices'])!=8:continue
            volume=0
            for i,j,k in mesh['faces']:
                a,b,c=[mesh['vertices'][idx] for idx in (i,j,k)]
                cross=(b[1]*c[2]-b[2]*c[1],b[2]*c[0]-b[0]*c[2],b[0]*c[1]-b[1]*c[0])
                volume+=sum(a[t]*cross[t] for t in range(3))/6
            self.assertGreater(volume,0,mesh['name'])

    def test_all_mesh_coordinates_are_finite(self):
        for mesh in self.meshes:
            self.assertTrue(all(math.isfinite(v) for point in mesh['vertices'] for v in point),mesh['name'])
            self.assertTrue(all(0<=i<len(mesh['vertices']) for face in mesh['faces'] for i in face))

    def test_strip_rejects_zero_length(self):
        with self.assertRaises(ValueError):strip('bad',(0,0,0),(0,0,1),5,'asphalt')

    def test_both_lobby_routes_clear_outer_and_inner_door_lines(self):
        spec=self.meta['config']['povo2_double_entrance'];z=spec['floor_z']
        banks=self.meta['povo2_double_entrance']['door_banks']
        self.assertEqual({(b['line'],b['index']) for b in banks},
                         {('outer',0),('outer',1),('inner',0),('inner',1)})
        for offset in spec['bank_offsets_y']:
            y=spec['centre_y']+offset
            for x in (53,51.1,spec['outer_x'],47,44,40,37,spec['inner_x'],31,27):
                lo=(x-.34,y-.34,z+.035);hi=(x+.34,y+.34,z+1.85)
                for name,a,b,mat in self.boxes:
                    self.assertFalse(all(a[k]<hi[k] and b[k]>lo[k] for k in range(3)),
                                     f'{name} obstructs lobby at {(x,y)}')
                supported=any(a[0]<=x<=b[0] and a[1]<=y<=b[1] and abs(b[2]-z)<.03
                              for name,a,b,mat in self.boxes)
                self.assertTrue(supported,f'No threshold/floor support at {(x,y)}')

    def test_inner_column_and_entrance_xy_match_reference_topology(self):
        e=self.meta['povo2_double_entrance'];s=self.meta['config']['povo2_double_entrance']
        self.assertGreater(e['outer_x'],e['inner_x'])
        self.assertEqual([e['inner_x'],s['centre_y']],e['source_entrance_xy'])
        column=next(b for b in self.boxes if b[0]=='p2_entry_inner_central_column')
        self.assertAlmostEqual(column[2][1]-column[1][1],s['inner_column_width'])
        self.assertIn('walk_13',{p['id'] for p in self.meta['prior_photo_evidence']})
        self.assertIn('walk_17',{p['id'] for p in self.meta['prior_photo_evidence']})


if __name__=='__main__':unittest.main()
