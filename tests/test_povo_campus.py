import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

from tools.build_povo_campus import build_geometry, backdrop_mesh, render_obj, collision_boxes, mirror_box
from tools.cs2_campus import OBJECTIVE, T_STARTS, CT_STARTS, make_radar, world, room_sign, sign_properties
from tools.verify_cs2_package import overview_values, radar_layout
from tools.audit_povo_campus import audit
from tools.audit_povo_interior import audit_level


ROOT=Path(__file__).resolve().parents[1]


class CampusGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings,cls.config,cls.boxes,cls.levels,cls.stair=build_geometry(ROOT)

    def test_every_room_is_open_including_the_formerly_sealed_north_wing(self):
        for level in self.levels:
            z=level['floor_elevation_metres']-370
            for room in [*level['rooms'],*level.get('connection',{}).get('rooms',[])]:
                # The sealed lift room's doorway is the shaft opening instead.
                if room['kind']=='elevator':continue
                a,b,c,d=room['footprint_local_metres'];f=room['door_fraction']
                x,y={'u_min':(a+(c-a)*f,b),'u_max':(a+(c-a)*f,d),
                     'v_min':(a,b+(d-b)*f),'v_max':(c,b+(d-b)*f)}[room['door_side']]
                walls=[box for box in self.boxes if box[3] in ('wall','courtyard_wall','reception_glass')
                       and all(box[1][i]-1e-7<=v<=box[2][i]+1e-7
                               for i,v in enumerate((x,y,z+1)))]
                self.assertEqual(bool(walls),not room.get('playable',True),
                                 (level['id'],room['id'],[w[0] for w in walls]))
        ground=self.levels[0]['rooms']
        self.assertEqual({r['id'] for r in ground if not r['playable']},{'g_east1','g_east2'})
        self.assertEqual([l['user_floor'] for l in self.levels],[-1,0,1])
        self.assertEqual(sum(r.get('playable',True) for r in self.levels[-1]['rooms']),48)
        for level in self.levels:
            for room in level['rooms']:
                if room['kind']=='elevator':continue
                if level['user_floor']==1 or room['kind'] in ('office','service'):
                    self.assertIsInstance(room['fitout'],str)
                    continue
                self.assertIsInstance(room['fitout'],dict,room['id'])
                if room['kind'] not in ('reception','restroom'):
                    self.assertGreater(room['fitout']['seats'],0,room['id'])

    def test_reception_reuses_the_sealed_povo2_glazing(self):
        room=next(r for r in self.levels[0]['rooms'] if r['id']=='g_east1')
        self.assertEqual(room['label'],'RECEPTION')
        self.assertFalse(room['playable'])
        self.assertEqual(room['fitout']['staff'],3)
        self.assertEqual(room['fitout']['front_staff'],'female')
        panels=[b for b in self.boxes if b[0].startswith('academic_ground_g_east1_') and b[3]=='reception_glass']
        self.assertEqual(len(panels),2)  # Front/back glazing; shared room walls are opaque.
        self.assertTrue(any(b[0]=='academic_ground_g_east1_finish_sign_plaque' for b in self.boxes))

    def test_north_and_south_have_separate_signed_furnished_restrooms(self):
        restrooms=[r for r in self.levels[1]['rooms'] if r['kind']=='restroom']
        self.assertEqual(len(restrooms),4)
        for wing in ('north','south'):
            pair=[r for r in restrooms if wing in r['id']]
            self.assertEqual({r['label'] for r in pair},{'UOMINI','DONNE'})
            for room in pair:
                self.assertEqual(room['fitout']['toilets'],4)
                self.assertEqual(room['fitout']['washbasins'],3)
                self.assertEqual(room['fitout']['seats'],0)
                prefix='academic_first_'+room['id']
                props=[b for b in self.boxes if b[0].startswith(prefix)]
                self.assertTrue(any(b[0]==prefix+'_floor' and b[3]=='floor_circulation' for b in props))
                self.assertTrue(any(b[0]==prefix+'_sink_basin' for b in props))
                self.assertTrue(any(b[0]==prefix+'_finish_sign_plaque' for b in props))
                self.assertFalse(any('desk' in b[0] or 'blackboard' in b[0] for b in props))
                a,b,c,d=room['footprint_local_metres']
                self.assertTrue(all(a-.01<=lo[0]<hi[0]<=c+.01 and b-.01<=lo[1]<hi[1]<=d+.01
                                    for n,lo,hi,m in props if '_finish_' not in n))

    def test_every_toilet_cubicle_and_washbasin_can_be_reached_from_the_hall(self):
        stations=[dict(id='hall',point=[-3,-35.2])]
        for room in self.levels[1]['rooms']:
            if room['kind']!='restroom':continue
            for i,point in enumerate(room['fitout']['audit_points_local_metres']):
                stations.append(dict(id=room['id']+'_'+str(i),point=point))
        report,_,_=audit_level(collision_boxes(self.boxes),
            dict(id='academic_first',floor_elevation_local=7.6),stations,width=.82,height=1.85)
        self.assertEqual(report['status'],'passed',[s for s in report['stations'] if not s['reachable_from_entrance']])

    def test_north_corridors_have_rooms_on_both_sides_at_normal_width(self):
        for level in self.levels[:2]:
            corridor=next(c for c in level['circulation'] if c['id']=='north_corridor')
            a,b,c,d=corridor['bounds']
            self.assertGreater((c-a)*83,2.5)
            self.assertLess((c-a)*83,3.1)
            for v in (.38,.5,.65):
                inner=[r for r in level['rooms'] if abs(r['bounds'][2]-a)<1e-8 and r['bounds'][1]<=v<=r['bounds'][3]]
                outer=[r for r in level['rooms'] if abs(r['bounds'][0]-c)<1e-8 and r['bounds'][1]<=v<=r['bounds'][3]]
                self.assertTrue(inner,(level['id'],v,'inner'))
                self.assertTrue(outer,(level['id'],v,'outer'))

    def test_stair_is_screened_by_walls_with_clear_open_doorways_on_both_floors(self):
        for core in self.stair['cores']:
            enclosure=core['enclosure'];x0,y0,x1,y1=enclosure['bounds']
            for portal in enclosure['portals']:
                x,y,z=portal['centre']
                def opaque_at(point):
                    return [b for b in self.boxes if b[3] in ('wall','door_black')
                            and all(b[1][i]<p<b[2][i] for i,p in enumerate(point))]
                self.assertTrue(opaque_at((x,(y0+y1)/2,z+1.5)),core['id'])
                self.assertFalse(opaque_at((x,y,z+1.5)),core['id'])
        leaves=[b for b in self.boxes if b[3]=='door_black' and b[0].startswith('stair_') and ('_leaf' in b[0])]
        self.assertEqual(len(leaves),24)

    def test_four_stairs_are_identical_mirrored_copies_opposite_corner_studios(self):
        self.assertEqual({c['id'] for c in self.stair['cores']},{'se','sw','ne','nw'})
        prototype=[b for b in self.boxes if b[0].startswith('stair_se_flight') and not b[0].endswith('_upper_segment')]
        actual={b[0]:b for b in self.boxes}
        for core in self.stair['cores']:
            for box in prototype:
                expected=mirror_box(box,core['id'],core['mirror_east'],core['mirror_north'])
                self.assertEqual(actual[expected[0]],expected)
            suffix={'se':'south_east','sw':'south_west','ne':'north_east','nw':'north_west'}[core['id']]
            for level in self.levels[:2]:
                room=next(r for r in level['rooms'] if r['id'].endswith(suffix))
                a,b,c,d=room['footprint_local_metres']
                self.assertAlmostEqual(b+(d-b)*room['door_fraction'],core['enclosure']['portals'][0]['centre'][1])
                self.assertEqual(room['door_side'],'v_min' if core['mirror_east'] else 'v_max')

    def test_bridge_has_its_own_floor_and_a2xx_keep_source_positions(self):
        self.assertEqual([l['user_floor'] for l in self.levels],[-1,0,1])
        original=json.loads((ROOT/'config/povo1_interior_study.json').read_text())
        for identifier in ('a202','a203'):
            source=next(r for r in original['levels'][1]['rooms'] if r['id']==identifier)
            actual=next(r for r in self.config['levels'][1]['rooms'] if r['id']==identifier)
            self.assertEqual(actual['pixel_bounds'],source['pixel_bounds'])
            self.assertNotIn(identifier,{r['id'] for r in self.levels[0]['rooms']})
        self.assertIn('connection',self.levels[2])
        self.assertNotIn('connection',self.levels[1])

    def test_bridge_and_povo2_route_have_continuous_support_and_standing_clearance(self):
        physics=collision_boxes(self.boxes)
        for n in range(-35,26):
            x,y,z=(23.45 if 14<=n<=17 else 22.25 if n>17 else 18.25),n,self.levels[-1]['floor_elevation_metres']-370
            self.assertTrue(any(b[3].startswith('floor_') and b[1][0]<=x<=b[2][0]
                                and b[1][1]<=y<=b[2][1] and abs(b[2][2]-z)<.02
                                for b in physics),n)
            obstacles=[b[0] for b in physics if not b[3].startswith('floor_')
                       and b[1][0]<x+.41 and b[2][0]>x-.41
                       and b[1][1]<y+.41 and b[2][1]>y-.41
                       and b[2][2]>z+.03 and b[1][2]<z+1.85]
            self.assertFalse(obstacles,(n,obstacles))
        self.assertEqual(next(l['connection'] for l in self.levels if 'connection' in l)['rooms'],[])

    def test_compact_arrival_keeps_alcoves_seals_east_and_ends_before_old_second_bays(self):
        physics=collision_boxes(self.boxes)
        def solid(p,materials):
            return [b for b in physics if b[3] in materials
                    and all(b[1][i]<=v<=b[2][i] for i,v in enumerate(p))]
        z=self.levels[-1]['floor_elevation_metres']-370
        for p in ((10.5,12,z),(22,12.8,z)):
            self.assertTrue(solid(p,('floor_circulation',)),p)
        self.assertTrue(solid((24,20,z+1),('wall',)))
        self.assertTrue(solid((22.25,26,z+1),('wall',)))
        for p in ((26,20,7.6),(12,32,7.6),(22,32,7.6),(18.25,39,7.6)):
            self.assertFalse(solid(p,('floor_circulation',)),p)
        self.assertFalse(any('p2_studio_' in b[0] or 'p2_future_door' in b[0] for b in self.boxes))

    def test_compact_stairs_have_walkable_risers_clear_portals_and_headroom(self):
        stair=next(l['connection'] for l in self.levels if 'connection' in l)['stair'];physics=collision_boxes(self.boxes)
        self.assertEqual(stair['risers'],40)
        self.assertAlmostEqual(stair['rise'],.18)
        self.assertAlmostEqual(stair['tread'],.3)
        steps=[b for b in physics if 'p2_stair_upper_step_' in b[0] or 'p2_stair_lower_step_' in b[0]]
        self.assertEqual(len(steps),20)
        heights=sorted(b[2][2] for b in steps)
        for a,b in zip(heights,heights[1:]):self.assertAlmostEqual(b-a,.18)
        for portal in stair['portals']:
            x,y,z=portal['centre']
            self.assertFalse([b[0] for b in physics if b[1][0]<x+.41 and b[2][0]>x-.41
                and b[1][1]<y+.41 and b[2][1]>y-.41 and b[2][2]>z+.03 and b[1][2]<z+1.85])
        # Every tread and both turns support the walking route. Check ceiling/guard
        # clearance above the feet, allowing the neighbouring .18 m stair riser.
        for x,y,z in [stair['top'],*stair['path'],stair['bottom']]:
            self.assertTrue(any(b[3].startswith('floor_') and b[1][0]<=x<=b[2][0]
                and b[1][1]<=y<=b[2][1] and abs(b[2][2]-z)<.02 for b in physics),(x,y,z))
            obstacles=[b[0] for b in physics if b[1][0]<x+.41 and b[2][0]>x-.41
                and b[1][1]<y+.41 and b[2][1]>y-.41
                and b[2][2]>z+.37 and b[1][2]<z+1.85]
            self.assertFalse(obstacles,((x,y,z),obstacles))

    def test_fixed_upright_signs_face_the_correct_corridor_wall_and_fit_the_plaque(self):
        for side,yaw in (('u_min',90),('u_max',270),('v_min',0),('v_max',180)):
            room=dict(footprint_local_metres=[0,0,5,10],door_fraction=.5,door_side=side)
            pos,angles=room_sign(room,4)
            self.assertEqual(angles,f'0 {yaw} 90')
            self.assertAlmostEqual(pos[2],6.44)
            self.assertTrue(pos[0]<0 or pos[0]>5 or pos[1]<0 or pos[1]>10)
        for label in ('A215','Aula studio ponte'):
            props=dict(sign_properties(label))
            self.assertEqual(props['reorient_mode'],'0')
            self.assertLessEqual(len(label)*42*.58*float(props['world_units_per_pixel']),40.0001)

    def test_authorized_room_templates_and_more_upstairs_fitouts(self):
        rooms={r['id']:r for r in self.levels[0]['rooms']}
        for name in ('a103','a104','a105','a106'):
            self.assertEqual(rooms[name]['room_template'],'a103')
            self.assertIsInstance(rooms[name]['fitout'],dict)
        for name in ('a107','a108','a109','a110'):
            self.assertEqual(rooms[name]['room_template'],'a101')
            self.assertIsInstance(rooms[name]['fitout'],dict)
        self.assertGreater(sum(isinstance(r['fitout'],dict) for r in self.levels[1]['rooms']),3)

    def test_stairs_reach_both_landings_with_walkable_risers(self):
        flights=[b for b in self.boxes if b[0].startswith('stair_se_flight')]
        self.assertEqual(len(flights),40)
        heights=sorted(b[2][2] for b in flights)
        for first,second in zip([4.]+heights[:-1],heights):
            self.assertAlmostEqual(second-first,.18)
        self.assertAlmostEqual(heights[-1],11.2)
        for station in ('bottom','top'):
            p=self.stair[station]
            support=[b for b in self.boxes if b[3].startswith('floor_')
                     and b[1][0]<=p[0]<=b[2][0] and b[1][1]<=p[1]<=b[2][1]
                     and abs(b[2][2]-p[2])<.02]
            self.assertTrue(support,station)
        void=self.stair['void']
        ceilings=[b for b in self.boxes if b[0].startswith('academic_ground_ceiling')]
        self.assertFalse(any(max(b[1][0],void[0])<min(b[2][0],void[2])
                             and max(b[1][1],void[1])<min(b[2][1],void[3]) for b in ceilings))

    def test_backdrop_excludes_old_solid_building_and_terrain_under_rooms(self):
        for name,_mat,points,_uv in backdrop_mesh(ROOT):
            self.assertFalse(name.startswith(('povo1_','arch_povo1_','cover_','boundary_')))
            self.assertFalse(name.startswith(('bridge_reference_','arch_bridge_')))
            if name.startswith(('povo2_east','arch_povo2_core_')):
                self.assertGreaterEqual(min(p[1] for p in points),42)
            if name=='terrain':
                self.assertFalse(any(-24<=p[0]<=30 and -106<=p[1]<=-18 for p in points))

    def test_spawn_feet_and_objective_have_floor_support(self):
        for point in [*T_STARTS,*CT_STARTS,OBJECTIVE]:
            x,y,z=point
            support=[b for b in self.boxes if b[3].startswith('floor_')
                     and b[1][0]<=x<=b[2][0] and b[1][1]<=y<=b[2][1]
                     and 0<z-b[2][2]<1]
            self.assertTrue(support,point)
            floor=max(b[2][2] for b in support)
            obstacles=[b[0] for b in collision_boxes(self.boxes) if not b[3].startswith('floor_')
                       and b[1][0]-.41<x<b[2][0]+.41 and b[1][1]-.41<y<b[2][1]+.41
                       and b[2][2]>floor+.03 and b[1][2]<floor+1.85]
            self.assertFalse(obstacles,(point,obstacles))

    def test_three_floor_overview_sections_meet_without_altitude_gaps(self):
        metadata=dict(levels=self.levels,stair=self.stair)
        with tempfile.TemporaryDirectory() as directory, patch('tools.cs2_campus.ROOT',Path(directory)):
            output=make_radar(metadata)
            values=overview_values((output/'trento_povo_campus.txt').read_bytes(),'trento_povo_campus')
            self.assertEqual(values['verticalsections.lower.altitudemax'],values['verticalsections.middle.altitudemin'])
            self.assertEqual(values['verticalsections.middle.altitudemax'],values['verticalsections.default.altitudemin'])
            for suffix in ('_lower','_middle',''):
                self.assertTrue((output/('trento_povo_campus'+suffix+'_radar.png')).is_file())

    def test_both_side_aisles_in_every_furnished_room_are_reachable(self):
        reports=audit()
        self.assertEqual([r['id'] for r in reports[:3]],[l['id'] for l in self.levels])
        self.assertTrue(all(r['stations'] for r in reports))
        for report in reports:
            self.assertEqual(report['status'],'passed',
                             [s['id'] for s in report['stations'] if not s['reachable_from_entrance']])

    def test_render_export_shares_vertices_and_has_valid_wall_uvs(self):
        obj=render_obj([('one',(0,0,0),(1,1,1),'wall'),
                        ('two',(1,0,0),(2,1,1),'wall')],[])
        vertices=[];uvs=[];normals=[];saw_face=False
        for line in obj.splitlines():
            p=line.split()
            if not p:continue
            if p[0] in ('v','vt','vn'):
                self.assertFalse(saw_face,'All attributes must precede faces')
                {'v':vertices,'vt':uvs,'vn':normals}[p[0]].append(tuple(map(float,p[1:])))
            elif p[0]=='f':
                saw_face=True;tex=[]
                for ref in p[1:]:
                    a,b,c=map(int,ref.split('/'))
                    self.assertTrue(1<=a<=len(vertices) and 1<=b<=len(uvs) and 1<=c<=len(normals))
                    tex.append(uvs[b-1])
                a,b,c=tex
                self.assertGreater(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])),.01)
        self.assertEqual(len(vertices),12)
        self.assertEqual(len(normals),6)

    def test_world_transform_matches_live_cs2_floor_drop(self):
        x,y,z=map(float,world((21,-72,4)).split())
        self.assertAlmostEqual(x,2834.646,places=3)
        self.assertAlmostEqual(y,826.772,places=3)
        self.assertAlmostEqual(z,157.480,places=3)


if __name__=='__main__':unittest.main()
