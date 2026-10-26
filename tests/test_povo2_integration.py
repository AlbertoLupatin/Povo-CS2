from unittest import TestCase

from tools.build_povo_campus import ROOT, build_geometry
from tools.povo2_connection import extend_campus
from tools.audit_povo2_integrated import audit
from tools.cs2_campus import room_sign


class Povo2IntegrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.p2=cls.levels[1]['connection']['povo2']

    def test_upper_arrival_and_stair_walking_surfaces_stay_in_place(self):
        baseline=extend_campus([], [{},{}],ROOT,3.35)
        actual={b[0]:b for b in self.boxes}
        for box in baseline:
            name,lo,hi,mat=box
            if hi[2]<7.59:continue
            from tools.povo_room_fitout import subtract_box
            shaft=self.levels[1]['connection']['lift']['shaft']
            hole=((shaft[0],shaft[1],.18),(shaft[2],shaft[3],10.95))
            # The relocated ladder cuts the arrival slab in the east alcove.
            # Verify the exact surviving pieces, not an obsolete hole location.
            for piece in subtract_box(box,hole):
                self.assertIn(piece[0],actual,piece[0])
                self.assertEqual(actual[piece[0]],piece,piece[0])

    def test_lower_floors_share_the_completed_stair_enclosure(self):
        self.assertEqual(self.p2['stairs']['bounds'],self.levels[1]['connection']['stair']['bounds'])
        self.assertEqual([p['floor'] for p in self.p2['stairs']['portals']],[0,-1,-2])
        self.assertEqual([p['centre'] for p in self.p2['stairs']['portals']],
                         [[16.5,22,4],[16.5,22,.4],[16.5,22,-3.2]])
        # The basement start stays flush with the actual enclosure end.
        self.assertEqual(self.p2['basement']['corridor'][3],self.p2['stairs']['bounds'][3])
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
        self.assertEqual(result['stair_samples'],72)
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
