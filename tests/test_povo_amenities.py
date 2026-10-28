import math
from unittest import TestCase

from tools.build_povo_campus import build_geometry, render_obj
from tools.povo_interior_fixtures import reception_boxes, reception_staff_mesh, office_frame


class AmenitiesTests(TestCase):
    def test_both_office_orientations_have_three_complete_workstations(self):
        for bounds,front in [((7.33,-77.34,12.72,-69.42),'east'),((21,26,29,32),'west')]:
            boxes=reception_boxes('office',bounds,4,3.35,front)
            a,b,c,d=bounds
            for suffix in ('front_desk','back_desk_0','back_desk_1'):
                for prop in ('top','monitor','keyboard','chair_seat'):
                    self.assertTrue(any(n=='office_'+suffix+'_'+prop for n,_,_,_ in boxes))
            for n,lo,hi,mat in boxes:
                if mat=='reception_glass' or '_frame_' in n or '_rail_' in n:continue
                self.assertTrue(a<=lo[0]<hi[0]<=c and b<=lo[1]<hi[1]<=d,(n,lo,hi))

    def test_three_rounded_typing_staff_include_a_front_receptionist(self):
        bounds=(7.33,-77.34,12.72,-69.42)
        faces=reception_staff_mesh('office',bounds,4,'east')
        self.assertGreater(len(faces),2000)
        for staff in ('staff_0_female','staff_1_male','staff_2_male'):
            for part in ('head','shirt','hand_-1','hand_1','shoe_-1','shoe_1'):
                self.assertTrue(any(staff+'_'+part in f[0] for f in faces),(staff,part))
        for _,_,vertices,_ in faces:
            for x,y,z in vertices:
                self.assertTrue(all(math.isfinite(v) for v in (x,y,z)))
                self.assertTrue(bounds[0]<x<bounds[2] and bounds[1]<y<bounds[3] and 4<=z<5.7)
        self.assertTrue(render_obj([],faces).startswith('# Povo 1'))

    def test_restrooms_have_complete_accessories_and_male_urinals(self):
        _,_,boxes,levels,_=build_geometry()
        for room in levels[1]['rooms']:
            if room['kind']!='restroom':continue
            prefix='academic_first_'+room['id']+'_'
            names={n[len(prefix):] for n,_,_,_ in boxes if n.startswith(prefix)}
            for prop in ('privacy_screen','basin_counter','mirror','hand_dryer','waste_bin','cleaning_cabinet'):
                self.assertIn(prop,names)
            self.assertIn(room['fitout']['toilets'],(2,4))
            for i in range(room['fitout']['toilets']):
                self.assertIn(f'cubicle_{i}_paper_roll',names)
                self.assertIn(f'cubicle_{i}_bin',names)
                self.assertIn(f'toilet_{i}_tank',names)
            self.assertEqual(room['fitout']['urinals'],2 if room['sex']=='male' else 0)
            if room['sex']=='male':self.assertIn('urinal_privacy_divider',names)
