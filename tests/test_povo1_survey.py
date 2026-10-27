"""Source-only checks of the photographed Povo1 upper level."""
import unittest
from tools.povo1_survey import build_survey_geometry
from tools.audit_povo_interior import audit_level

class Povo1SurveyTests(unittest.TestCase):
    def test_upper_source_rooms_have_open_hall_routes_without_invented_furniture(self):
        config,alignment,boxes,levels=build_survey_geometry()
        self.assertEqual([l['user_floor'] for l in levels],[-1,0,1])
        self.assertEqual([round(l['floor_elevation_metres']-370,2) for l in levels],[4,7.6,11.2])
        upper=levels[-1]
        playable=[r for r in upper['rooms'] if r.get('playable',True)]
        self.assertEqual(len(playable),48)
        self.assertEqual(len(upper['rooms']),50)
        self.assertTrue(all(isinstance(r['fitout'],str) for r in upper['rooms']))
        self.assertFalse(any(r['label'].startswith('A') for r in upper['rooms']))
        stations=[dict(id='hall',point=[-11,-60])]
        for room in playable:
            a,b,c,d=room['footprint_local_metres']
            stations.append(dict(id=room['id'],point=[(a+c)/2,(b+d)/2]))
        report,_,_=audit_level(boxes,dict(id=upper['id'],floor_elevation_local=11.2),stations,width=.82,height=1.85)
        self.assertEqual(report['status'],'passed',[s for s in report['stations'] if not s['reachable_from_entrance']])
        self.assertTrue(all(all(lo[i]<hi[i] for i in range(3)) for _,lo,hi,_ in boxes))

class AcquarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_povo_campus import build_geometry,collision_boxes
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.physics=collision_boxes(cls.boxes)

    def test_single_study_room_replaces_synthetic_west_cells(self):
        rooms=self.levels[0]['rooms']
        self.assertFalse(any(r['id'].startswith('g_west') for r in rooms))
        room=next(r for r in rooms if r['id']=='acquario')
        self.assertEqual(room['kind'],'study')
        self.assertEqual(room['source_photos'],[9,10,17,18])
        self.assertFalse(room['fitout']['teaching_front'])
        self.assertIn('provisional',room['fitout']['status'])
        a,b,c,d=room['footprint_local_metres']
        self.assertGreater(d-b,20)
        # Crossing all former synthetic partition positions remains clear.
        stations=[dict(id='door_inside',point=[a+.6,b+(d-b)*room['door_fraction']])]
        stations += [dict(id='long_aisle_'+str(i),point=[(a+c)/2,b+1+i*(d-b-2)/20]) for i in range(21)]
        report,_,_=audit_level(self.physics,dict(id='academic_ground',floor_elevation_local=4),stations,width=.82,height=1.85)
        self.assertEqual(report['status'],'passed',[s for s in report['stations'] if not s['reachable_from_entrance']])
        props=[box for box in self.boxes if box[0].startswith('academic_ground_acquario_')]
        from tools.build_povo_campus import is_breakable_glass
        self.assertTrue(any(is_breakable_glass(box) for box in props if 'corridor_glass' in box[0]))
        self.assertFalse(any('board' in box[0] or 'tier' in box[0] for box in props))
        self.assertTrue(all(lo[2]>=4-.001 for _,lo,hi,_ in props))

class Photo4ClassroomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_povo_campus import build_geometry
        from unittest.mock import patch
        cls.settings,cls.config,cls.boxes,cls.levels,_=build_geometry()
        with patch('tools.build_povo_campus.PHOTO4_CLASSROOMS',frozenset()):
            _,_,cls.baseline,cls.old_levels,_=build_geometry()

    def test_only_authorized_external_family_changes_and_other_classrooms_are_identical(self):
        family={'a103','a104','a105','a106'}
        for level in self.levels[:2]:
            for room in level['rooms']:
                if room['kind']!='classroom' or room['id'] in family:continue
                prefix=level['id']+'_room_'+room['id']+'_'
                current=[b for b in self.boxes if b[0].startswith(prefix)]
                baseline=[b for b in self.baseline if b[0].startswith(prefix)]
                self.assertEqual(current,baseline,room['id'])
                old=next(r for l in self.old_levels if l['id']==level['id'] for r in l['rooms'] if r['id']==room['id'])
                self.assertEqual(room['fitout'],old['fitout'],room['id'])

    def test_photo4_family_has_green_chairs_glazed_teaching_front_and_safe_low_platform(self):
        from tools.povo_physics_surfaces import surface
        self.assertEqual(surface('seat_green'),'wood')
        for room in self.levels[0]['rooms']:
            if room['id'] not in {'a103','a104','a105','a106'}:continue
            fit=room['fitout'];prefix='academic_ground_room_'+room['id']+'_'
            props=[b for b in self.boxes if b[0].startswith(prefix)]
            self.assertEqual(fit['source_walk_20261027'],[4])
            self.assertEqual(fit['teaching_side'],fit['window_side'])
            self.assertEqual(fit['chair_material'],'seat_green')
            self.assertTrue(any(b[3]=='seat_green' for b in props))
            self.assertFalse(any(b[0] in (prefix+'screen',prefix+'screen_case') for b in props))
            board=next(b for b in props if b[0]==prefix+'board')
            glazing=next(b for b in props if b[0]==prefix+'window_glass')
            self.assertLess(abs(board[1][1]-glazing[1][1]),.3)
            platform=next(b for b in props if b[0]==prefix+'front_platform')
            step=next(b for b in props if b[0]==prefix+'front_platform_step')
            self.assertLessEqual(platform[2][2]-step[2][2],.18)
            self.assertGreater(len(fit['rows']),1)
            for row in fit['rows']:
                lo,hi=row['bounds_local_metres']
                self.assertGreater(hi[0]-lo[0],hi[1]-lo[1])
        side=[b for b in self.boxes if '_side_window_glass' in b[0] and b[0].startswith('academic_ground_room_a10')]
        self.assertEqual([b[0] for b in side],['academic_ground_room_a103_side_window_glass'])

if __name__=='__main__':unittest.main()
