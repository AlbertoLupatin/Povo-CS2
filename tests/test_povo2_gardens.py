from unittest import TestCase
from tools.build_povo_campus import build_geometry
from tools.audit_povo_yard import audit_gardens


class GardensTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.spec=cls.levels[-1]['connection']['povo2']

    def test_up_faces_exit_and_down_continues_straight_from_passage(self):
        g=self.spec['gardens']
        self.assertAlmostEqual(g['passage'][3]-g['passage'][1],1.71)
        self.assertLess(abs((g['up_stair'][0]+g['up_stair'][2])/2-g['exit_door'][0]),.2)
        self.assertEqual(g['up_stair'][3],g['passage'][1])
        self.assertEqual(g['down_stair'][1::2],g['passage'][1::2])
        self.assertEqual(g['down_stair'][0],g['passage'][2])
        self.assertTrue(all(abs(p[1]-(g['passage'][1]+g['passage'][3])/2)<1e-6 for p in g['routes']['down']))
        self.assertAlmostEqual(g['down_stair'][2],(g['garden'][0]+g['garden'][2])/2)
        self.assertEqual(g['garden'][:2],g['down_stair'][:2])
        self.assertAlmostEqual(g['garden'][2]-g['garden'][0],17.5)
        self.assertAlmostEqual(g['garden'][3]-g['garden'][1],11.25)
        self.assertEqual(g['routes']['garden'][0],g['routes']['down'][-1])
        self.assertEqual(g['indoor_corridor'][1],g['exit_door'][1])
        self.assertGreater(g['indoor_corridor'][3],g['indoor_turn'][3])
        self.assertEqual(g['garden_z'],next(l['z'] for l in self.spec['levels'] if l['floor']==-2))
        self.assertTrue(all(p[2]==g['passage_z'] for p in g['routes']['passage']))
        self.assertLess(g['routes']['down'][-1][2],g['routes']['down'][0][2])
        self.assertGreater(g['routes']['up'][-1][2],g['routes']['up'][0][2])
        self.assertFalse(any(n.startswith('p2_basement_exit_step_') for n,*_ in self.boxes))

    def test_routes_clear_and_removed_threshold_is_detected(self):
        report=audit_gardens(self.boxes,self.levels)
        self.assertEqual(report['status'],'passed',report['failures'][:5])
        broken=[b for b in self.boxes if b[0]!='p2_basement_drawio_terrace']
        self.assertEqual(audit_gardens(broken,self.levels)['status'],'failed')

    def test_down_stair_is_inside_garden_from_start_to_midpoint(self):
        g=self.spec['gardens'];a,b,c,d=g['garden']
        steps=[(lo,hi) for n,lo,hi,_ in self.boxes if n.startswith('p2_aligned_garden_down_step_')]
        self.assertEqual(len(steps),20)
        self.assertTrue(all(a<=lo[0]<hi[0]<=c and b<=lo[1]<hi[1]<=d for lo,hi in steps))
        self.assertAlmostEqual(max(hi[0] for lo,hi in steps),(a+c)/2)
        self.assertAlmostEqual(min(hi[2] for lo,hi in steps),g['garden_z'])
        self.assertTrue(all(q[2]<=p[2] for p,q in zip(g['routes']['down'],g['routes']['down'][1:])))
        broken=[v for v in self.boxes if v[0]!='p2_aligned_garden_down_step_5']
        self.assertEqual(audit_gardens(broken,self.levels)['status'],'failed')
