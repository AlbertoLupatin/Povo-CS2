from unittest import TestCase
from tools.build_povo_campus import build_geometry
from tools.audit_povo_yard import audit_gardens


class GardensTests(TestCase):
    """The user's 30 Oct front: C5 is the only exit. Its terrace has a straight
    UP stair to the street and a metal stair down into Garden -2."""
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.spec=cls.levels[-1]['connection']['povo2']

    def test_terrace_stairs_and_garden_follow_the_user_front(self):
        f=self.spec['south_front'];g=self.spec['gardens'];c5=self.spec['walkthrough_repairs']['c5']
        t=f['terrace'];s=f['up_stair']
        self.assertTrue(2<=t[3]-t[1]<=3)
        self.assertAlmostEqual(s[3],t[1])
        self.assertAlmostEqual(s[1],f['pavement']['south_edge'])
        self.assertTrue(c5[0]-.05<=s[0] and s[2]<=c5[2]+.05)
        self.assertLessEqual(f['metal_stair']['start_x'],f['garden_extension'][0])
        self.assertEqual(g['garden'][0],f['garden_extension'][0])
        for key in ('passage','up_stair','exit_door','indoor_corridor'):self.assertNotIn(key,g)
        street,garden=g['routes']['street'],g['routes']['garden']
        self.assertGreater(street[0][2],street[-1][2]+3)
        self.assertLess(garden[-1][2],garden[0][2]-3)
        self.assertFalse(any(n.startswith(('p2_gardens_up','p2_gardens_passage','p2_basement_gardens_passage'))
                             for n,*_ in self.boxes))

    def test_routes_clear_and_removed_terrace_is_detected(self):
        report=audit_gardens(self.boxes,self.levels)
        self.assertEqual(report['status'],'passed',report['failures'][:5])
        broken=[b for b in self.boxes if b[0]!='p2_front_terrace_floor']
        self.assertEqual(audit_gardens(broken,self.levels)['status'],'failed')
