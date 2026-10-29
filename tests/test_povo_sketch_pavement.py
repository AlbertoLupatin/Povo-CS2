"""User drawing topology and full-width pavement support regressions."""
from collections import Counter
import math
from unittest import TestCase
from tools.build_povo_campus import build_geometry,collision_boxes
from tools.audit_povo_pavement import audit
from tools.povo2_sketch import rotate_point,rotate_rect


class SketchPavementTests(TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()
        cls.spec=next(l['connection'] for l in cls.levels if l.get('connection'))['povo2']

    def test_rigid_placement_precedes_later_lab_gap_correction(self):
        p=self.spec['basement_placement'];cfg=self.spec['additions']['config']
        self.assertEqual(p['degrees_clockwise'],90)
        old=rotate_rect(cfg['cibio_corridor'],p);new=self.spec['basement']['cibio_corridor']
        shift=self.spec['minus1_corrections']['room2_north_shift_metres']
        self.assertEqual(new,old[:3]+[old[3]+shift])
        for i,r in enumerate(cfg['cibio_offices']):
            expected=rotate_rect(r,p)
            if i==1:expected=[expected[0],expected[1]+shift,expected[2],expected[3]+shift]
            self.assertEqual(self.spec['basement'][f'cibio_office_{i}'],expected)
        # The later Gardens sketch supersedes only the old exterior yard.
        self.assertNotIn('yard',self.spec['basement'])
        self.assertEqual(self.spec['additions']['yard']['user_floor'],-2)
        a=[17.5,-5];b=[18.5,27.5]
        self.assertAlmostEqual(math.dist(a,b),math.dist(rotate_point(a,p),rotate_point(b,p)))
        south=next(p for p in self.spec['stairs']['portals'] if p['floor']==-1)
        self.assertEqual(south['side'],'u_min')

    def test_reception_stair_alignment_and_six_bar_tables(self):
        self.assertEqual(self.spec['ground']['reception'],[12.5,26,20.5,35.5])
        self.assertEqual(self.spec['stairs']['bounds'][2],20.5)
        tables=[b for b in self.boxes if b[0].startswith('canteen_0_bar_sketch_table_') and b[0].endswith('_top')]
        self.assertEqual(len(tables),6)
        self.assertTrue(all(b[3]=='canteen_orange' for b in tables))
        self.assertFalse(any(b[0].startswith('canteen_0_bar_high_table_') for b in self.boxes))

    def test_entire_repaired_paving_has_visual_and_physical_support(self):
        r=audit(self.boxes,self.levels)
        self.assertGreater(r['samples'],7000)
        self.assertEqual(r['status'],'passed',r['failures'][:10])
        # A removed slab must be caught, not silently treated as base ground.
        without=[b for b in self.boxes if not b[0].startswith('exterior_paving_povo2_north_pavement')]
        self.assertEqual(audit(without,self.levels)['status'],'failed')

    def test_road_joint_colliders_are_closed_and_match_rendered_geometry(self):
        ext=self.levels[0]['exterior'];physics={m['name']:m for m in ext['collision_meshes']}
        joints=[m for m in ext['meshes'] if '_joint_' in m['name']]
        self.assertTrue(joints)
        for m in joints:
            self.assertEqual(m,physics[m['name']])
            edges=Counter(tuple(sorted((a,b))) for f in m['faces'] for a,b in zip(f,(*f[1:],f[0])))
            self.assertTrue(all(n==2 for n in edges.values()),m['name'])
