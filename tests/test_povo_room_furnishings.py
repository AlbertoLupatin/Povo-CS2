import unittest
from collections import Counter
from tools.build_povo_campus import build_geometry


class UpperFurnishingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_=build_geometry()

    def test_every_playable_upper_room_has_the_correct_kind_of_furniture(self):
        upper=self.levels[-1];rooms=[r for r in upper['rooms'] if r.get('playable',True)]
        self.assertEqual(len(rooms),48)
        self.assertEqual(Counter(r['kind'] for r in rooms),dict(office=37,laboratory=6,restroom=4,meeting=1))
        for room in rooms:
            fit=room['fitout'];prefix=upper['id']+'_'+room['id']+'_furnishing'
            actual=[b for b in self.boxes if b[0].startswith(prefix)]
            self.assertTrue(actual,room['id'])
            self.assertEqual(fit['kind'],room['kind'])
            if room['kind']=='restroom':
                self.assertGreaterEqual(fit['toilets'],1)
                self.assertGreaterEqual(fit['washbasins'],1)
                self.assertTrue(any('_toilet_' in n and '_bowl' in n for n,*_ in actual))
                self.assertTrue(any('mirror' in n for n,*_ in actual))
            else:self.assertGreaterEqual(fit['desks'],1)

    def test_new_furniture_stays_inside_each_registered_room(self):
        for level in self.levels:
            for r in level['rooms']:
                if not isinstance(r.get('fitout'),dict) or 'kind' not in r['fitout']:continue
                a,b,c,d=r['footprint_local_metres']
                for n,lo,hi,_ in self.boxes:
                    if n.startswith(level['id']+'_'+r['id']+'_furnishing'):
                        self.assertTrue(a+.099<=lo[0]<hi[0]<=c-.099 and b+.099<=lo[1]<hi[1]<=d-.099,n)
