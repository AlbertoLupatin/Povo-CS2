"""Registration and evidence checks for the complete -1 layout review."""
import copy
from unittest import TestCase

from tools.build_povo_campus import build_geometry
from tools.create_povo2_minus1_layout import Registration, create_layout, restore_full_plan
from tools.povo2_survey import load


class Minus1LayoutReviewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,levels,_=build_geometry()
        cls.spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
        cls.before=copy.deepcopy(cls.spec)
        cls.layout=create_layout(cls.spec,cls.boxes)
        cls.restored=restore_full_plan(copy.deepcopy(cls.layout))
        cls.source=next(l for l in load()['levels'] if l['floor']==-1)

    def test_both_lower_corridor_axes_match_floor_zero(self):
        a=self.restored['alignment']
        for key in ('floor0_reference','minus1','minus2_after'):
            r=a[key]
            self.assertAlmostEqual((r[0]+r[2])/2,23)
        self.assertAlmostEqual(a['minus2_translation_east'],.75)
        self.assertAlmostEqual(a['minus2_after'][2]-a['minus2_after'][0],3.5)

    def test_registration_preserves_core_and_is_continuous_at_corridor_edges(self):
        s=self.source;c=self.layout['registration']['campus_core']
        reg=Registration(s['annotated_corridor_exit_core'],c,s['corridors'][4],self.layout['alignment']['floor0_reference'])
        for a,b in zip(reg.rect(s['annotated_corridor_exit_core']),c):
            self.assertAlmostEqual(a,b)
        for y in reg.source_band:
            p,q=reg.point(50,y-1e-7),reg.point(50,y+1e-7)
            self.assertLess(abs(p[0]-q[0]),1e-5)
        self.assertEqual(self.spec,self.before,'Review must not mutate installed-layout metadata')

    def test_complete_source_room_set_and_all_four_cores_are_present(self):
        self.assertEqual({r['id'] for r in self.layout['rooms']},{r['id'] for r in self.source['rooms']})
        self.assertEqual(len(self.layout['rooms']),80)
        self.assertEqual(len(self.layout['cores']),4)
        self.assertEqual(len(self.layout['exits']),14)
        # The former two-room model entirely omitted both research wings.
        self.assertTrue(any(r['id']=='research_e_inner1' for r in self.layout['rooms']))
        self.assertTrue(any(r['id']=='research_w1' for r in self.layout['rooms']))

    def test_door_intervals_are_traced_and_the_obscured_door_is_not_invented(self):
        rooms=self.layout['rooms']
        self.assertEqual(sum(bool(r['door']) for r in rooms),79)
        unknown=[r for r in rooms if not r['door']]
        self.assertEqual([r['id'] for r in unknown],['annotated_lab_e'])
        self.assertEqual(unknown[0]['access_topology']['corridor_entrance_count'],1)
        floor=next(f for f in self.layout['floors'] if f['f']==-1)
        # A traced opening must not be sealed by another room's shared wall.
        for room in rooms:
            if not room['door']:continue
            p,q=room['door']['points'];x=(p[0]+q[0])/2;y=(p[1]+q[1])/2
            self.assertFalse(any(a<x<c and b<y<d for a,b,c,d,_ in floor['walls']+floor['glazing']),room['id'])

    def test_central_void_is_not_filled_and_room_floors_are_supported(self):
        floor=next(f for f in self.layout['floors'] if f['f']==-1)
        for a,b,c,d in self.layout['voids']:
            for tx in (.2,.5,.8):
                for ty in (.2,.5,.8):
                    x=a+(c-a)*tx;y=b+(d-b)*ty
                    self.assertFalse(any(u<x<w and v<y<t for u,v,w,t in floor['slabs']))
        for room in self.layout['rooms']:
            a,b,c,d=room['bounds'];x=(a+c)/2;y=(b+d)/2
            self.assertTrue(any(u<=x<=w and v<=y<=t for u,v,w,t in floor['slabs']),room['id'])

    def test_new_walk_finish_study_has_evidence_and_no_fabricated_photo_locations(self):
        self.assertEqual(len(self.layout['new_walk']['photos']),3)
        self.assertEqual(self.layout['new_walk']['exact_photo_to_room_identification'],'unconfirmed')
        self.assertFalse(next(f for f in self.restored['floors'] if f['f']==-1)['glazing'])
        self.assertIn('Internal circulation',self.restored['new_walk']['corridor_scope'])

    def test_restore_preserves_all_full_plan_floor_geometry(self):
        self.assertEqual(self.restored['floors'],self.layout['floors'])
        self.assertEqual(self.restored['corridors'],self.layout['corridors'])
        self.assertEqual(self.restored['rooms'],self.layout['rooms'])
        self.assertNotIn('western_office_rooms',self.restored)

    def test_no_rejected_lab_door_or_vestibule_relocation_is_applied(self):
        self.assertNotIn('closed_lab_doors',self.restored)
        self.assertNotIn('minus2_translation_north',self.restored['alignment'])
        self.assertEqual(self.restored['floors'][0],self.layout['floors'][0])

    def test_internal_photo_corridor_does_not_become_a_main_corridor(self):
        f=next(f for f in self.restored['floors'] if f['f']==-1)
        self.assertFalse(any(a['label'] in ('WEST office corridor','Glazed office corridor') for a in f['areas']))
        context=self.restored['west_offices_context']
        a,b,c,d=context['bounds']
        west=self.restored['corridors'][6]['bounds']
        self.assertAlmostEqual(d,west[1])
        self.assertLess(b,d)
