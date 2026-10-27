from unittest import TestCase

from tools.build_povo_campus import ROOT, build_geometry
from tools.povo2_connection import extend_campus
from tools.audit_povo2_integrated import audit, audit_stair_routes
from tools.cs2_campus import room_sign


class Povo2IntegrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.link=next(l['connection'] for l in cls.levels if l.get('connection'))
        cls.p2=cls.link['povo2']

    def test_upper_arrival_and_stair_walking_surfaces_stay_in_place(self):
        baseline=extend_campus([], [{},{}],ROOT,3.35)
        actual={b[0]:b for b in self.boxes}
        for box in baseline:
            name,lo,hi,mat=box
            if hi[2]<self.link['floor_local_metres']-.01:continue
            from tools.povo_room_fitout import subtract_box
            shaft=self.link['lift']['shaft']
            hole=((shaft[0],shaft[1],.18),(shaft[2],shaft[3],self.link['floor_local_metres']+3.35))
            # The relocated ladder cuts the arrival slab in the east alcove.
            # Verify the exact surviving pieces, not an obsolete hole location.
            parts=subtract_box(box,hole)
            lift=self.link['lift'];sa,sb=lift['side_opening_north']
            for z in (.4,self.link['floor_local_metres']):
                sidehole=((shaft[0]-.3,sa,z-.01),(shaft[0]+.2,sb,z+2.2))
                parts=[p for item in parts for p in
                       (subtract_box(item,sidehole) if item[3] in ('wall','p2_accent_green','window_frame') else [item])]
            z=self.link['floor_local_metres']
            sidehole=((18.35,17.65,z-.01),(20.05,17.95,z+2.25))
            parts=[p for item in parts for p in
                   (subtract_box(item,sidehole) if item[3] in ('wall','p2_accent_green','window_frame') else [item])]
            for piece in parts:
                self.assertIn(piece[0],actual,piece[0])
                self.assertEqual(actual[piece[0]],piece,piece[0])

    def test_lower_floors_share_the_completed_stair_enclosure(self):
        self.assertEqual(self.p2['stairs']['bounds'],self.link['stair']['bounds'])
        self.assertEqual([p['floor'] for p in self.p2['stairs']['portals']],[0,-1,-2])
        self.assertEqual([p['centre'] for p in self.p2['stairs']['portals']],
                         [[20.5,22,4],[19.2,18,.4],[20.5,22,-3.2]])
        # The basement start stays flush with the actual enclosure end.
        self.assertEqual(self.p2['basement']['corridor'][3],self.p2['stairs']['portals'][1]['centre'][1])
        self.assertFalse(any(n.startswith('academic_first_link_p2_lower_wall_') for n,_,_,_ in self.boxes))

    def test_world_rooms_are_furnished_and_flush_with_reception(self):
        ground=next(l for l in self.p2['levels'] if l['floor']==0)
        for room in ground['rooms']:
            if room['id'] not in ('b111','b112','b113','b114'):continue
            self.assertEqual(room['bounds'][2],self.p2['ground']['reception'][2])
            self.assertEqual(room['door_side'],'v_max')
            self.assertEqual(room['board_wall'],'south')
            self.assertGreater(room['fitout']['seats'],0)
            self.assertEqual(room['fitout']['window_side'],'west')
            self.assertEqual(room['fitout']['teaching_side'],'south')
            board=next(b for b in self.boxes if b[0]=='p2_ground_'+room['id']+'_blackboard')
            self.assertLess(board[2][1],room['bounds'][1]+.2)

    def test_actual_campus_has_clear_connected_lower_floors_and_stacked_stairs(self):
        result=audit()
        self.assertEqual(result['status'],'passed',result)
        self.assertEqual([len(l['stations']) for l in result['levels']],[8,18,50])
        self.assertGreaterEqual(result['stair_samples'],96)
        self.assertFalse(result['stair_failures'])

    def test_classroom_text_planes_are_in_front_of_the_blue_plaques(self):
        ground=next(l for l in self.p2['levels'] if l['floor']==0)
        for room in ground['rooms']:
            origin,_=room_sign(room,ground['z'])
            plaque=next(b for b in self.boxes if b[0]=='p2_ground_'+room['id']+'_sign_plaque')
            axis=0 if room['door_side'].startswith('v_') else 1
            if room['door_side'].endswith('max'):
                self.assertGreater(origin[axis],plaque[2][axis]+.005)
            else:
                self.assertLess(origin[axis],plaque[1][axis]-.005)


class DoubleHeightStairTests(TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_povo_campus import collision_boxes
        _,_,boxes,levels,_=build_geometry()
        cls.physics=collision_boxes(boxes)
        cls.link=next(l['connection'] for l in levels if l.get('connection'))
        cls.stair=cls.link['stair']

    def test_four_flights_reach_the_bridge_with_two_normal_basement_rises(self):
        stair=self.stair
        self.assertEqual(stair['modules'],2)
        self.assertEqual(stair['risers'],40)
        self.assertAlmostEqual(stair['top'][2]-stair['bottom'][2],7.2)
        paths=self.link['povo2']['stairs']['path']
        for route in paths:
            self.assertAlmostEqual(route['points'][0][2]-route['points'][-1][2],3.6)
        steps=[p for p in stair['path'] if abs(p[0]-18.05)<.01]
        self.assertEqual(len(steps),4)
        self.assertGreaterEqual(len(stair['rails']),10)

    def test_intermediate_turn_landing_support_and_headroom_are_required(self):
        p=[19.2,20,7.6]
        route=[dict(points=[p])]
        _,failures=audit_stair_routes(self.physics,route)
        self.assertFalse(failures)
        missing=[b for b in self.physics if not (b[3].startswith('floor_') and
                 abs(b[2][2]-p[2])<.02 and b[1][0]<=p[0]<=b[2][0] and b[1][1]<=p[1]<=b[2][1])]
        _,failures=audit_stair_routes(missing,route)
        self.assertFalse(failures[0]['supported'])
        blocked=self.physics+[('test_low_headroom',(18.7,19.5,9.1),(19.7,20.5,9.3),'wall')]
        _,failures=audit_stair_routes(blocked,route)
        self.assertIn('test_low_headroom',failures[0]['obstacles'])

    def test_no_guessed_survey_room_grid_enters_live_geometry(self):
        self.assertFalse(any(n.startswith('p2_survey_') for n,_,_,_ in self.physics))


    def test_ct_and_objective_origins_follow_supported_upper_floor(self):
        from tools.cs2_campus import gameplay_points
        _,_,_,levels,_=build_geometry()
        _,ct,objective=gameplay_points(dict(levels=levels))
        upper=max(l['floor_elevation_metres']-370 for l in levels)
        for p,offset in [(p,.8) for p in ct]+[(objective,.6)]:
            self.assertAlmostEqual(p[2]-offset,upper)
            self.assertTrue(any(m.startswith('floor_') and abs(hi[2]-upper)<.02 and
                            lo[0]<=p[0]<=hi[0] and lo[1]<=p[1]<=hi[1]
                            for _,lo,hi,m in self.physics),p)


    def test_right_marked_lab_has_one_corridor_entrance_and_distinct_courtyard_exit(self):
        from tools.povo2_survey import load, register
        from copy import deepcopy
        survey=load()
        level=next(l for l in survey['levels'] if l['floor']==-1)
        room=next(r for r in level['rooms'] if r['id']=='annotated_lab_e')
        access=room['access_topology']
        self.assertEqual(access['corridor_entrance_count'],1)
        self.assertEqual(access['corridor_entrance_side'],'north')
        self.assertEqual(access['exterior_exit_side'],'west')
        exit=next(e for e in level['exits'] if e['id']==access['exterior_exit_id'])
        self.assertEqual(exit['destination'],'external courtyard')
        self.assertFalse(room.get('opening_trace'))
        subset=deepcopy(survey);subset['levels']=[deepcopy(level)]
        subset['levels'][0]['rooms']=[deepcopy(room)]
        with self.assertRaisesRegex(ValueError,'Unresolved door traces'):
            register(subset,(0,0),1)
