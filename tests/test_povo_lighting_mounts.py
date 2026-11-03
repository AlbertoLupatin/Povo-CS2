"""Regression guards for light fittings orphaned by later geometry cuts."""
import re
import unittest
from tools.build_povo_campus import build_geometry


class LightingMountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()

    def test_every_visible_ceiling_diffuser_has_a_mount(self):
        mounts=[b for b in self.boxes if b[3]=='ceiling_panel' or b[3].startswith('floor_')
                or b[3] in ('wall','exterior_white','exterior_concrete')]
        for name,lo,hi,material in self.boxes:
            if material!='light_diffuser':continue
            x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
            self.assertTrue(any(a[0]<=x<=b[0] and a[1]<=y<=b[1] and hi[2]-.02<=a[2]<=hi[2]+.18
                                for _,a,b,_ in mounts),name)

    def test_frontage_poles_reach_supported_paving_without_cut_fragments(self):
        for i,expected in ((0,4.12),(1,4.)):
            prefix=f'exterior_povo2_front_lamp_{i}'
            parts=[b for b in self.boxes if b[0]==prefix or b[0].startswith(prefix+'_windowcut_')]
            self.assertEqual(len(parts),1)
            name,lo,hi,material=parts[0]
            self.assertEqual(name,prefix)
            self.assertAlmostEqual(lo[2],expected)
            self.assertAlmostEqual(hi[0]-lo[0],.15)
            self.assertAlmostEqual(hi[1]-lo[1],.15)
            for x in (lo[0]+.001,hi[0]-.001):
                for y in (lo[1]+.001,hi[1]-.001):
                    self.assertTrue(any(a[0]<=x<=b[0] and a[1]<=y<=b[1] and abs(b[2]-lo[2])<.001
                        and m in ('exterior_paving','exterior_concrete','floor_terrace')
                        for _,a,b,m in self.boxes),(name,x,y))

    def test_obsolete_aula_lamps_do_not_survive_as_roof_or_wall_fragments(self):
        self.assertFalse([n for n,*_ in self.boxes if re.match(r'exterior_povo2_front_lamp_(?:head_)?[56](?:_|$)',n)])
        link=next(l['connection'] for l in self.levels if 'connection' in l)
        self.assertFalse([p for p in link['lights'] if abs(p[0]-11)<.3 and 18<p[1]<26
                          and abs(p[2]-(link['floor_local_metres']+2.9))<.01])


if __name__=='__main__':unittest.main()
