"""Geometry and walkability checks for the plan-traced -1 West Offices."""
import json
from collections import deque
from unittest import TestCase

from tools.build_povo_campus import ROOT
from tools.build_povo2_west_offices import build


def overlaps(a, b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]


def inside(p, r, pad=0):
    return r[0]-pad<=p[0]<=r[2]+pad and r[1]-pad<=p[1]<=r[3]+pad


class WestOfficesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cfg=json.loads((ROOT/'config/povo2_west_offices.json').read_text())
        cls.base=json.loads((ROOT/cfg['baseline_layout']).read_text(encoding='utf-8'))
        cls.layout=build(cls.base)
        cls.office=cls.layout['west_offices']
        cls.floor=next(f for f in cls.layout['floors'] if f['f']==-1)
        cls.solid=[w[:4] for w in cls.floor['walls']+cls.floor['glazing']]
        cls.corridors={c['id']:c['bounds'] for c in cls.layout['corridors']}

    def walkable_from(self, start, radius=.3, step=.1):
        """Flood-fill the office block, C7, the stair threshold and C5."""
        c=self.corridors;fp=self.office['footprint']
        regions=[fp,c['corridor_7'],c['retained_stair_threshold'],c['corridor_5']]
        x0,y0=fp[0]-.5,fp[1]-.5;nx=int((c['corridor_5'][2]-x0)/step)+1;ny=int((c['corridor_7'][3]-y0)/step)+1
        blocked=set()
        for r in self.solid+[k['bounds'] for k in self.layout['cores']]:
            for i in range(max(0,int((r[0]-radius-x0)/step)),min(nx,int((r[2]+radius-x0)/step)+1)):
                for j in range(max(0,int((r[1]-radius-y0)/step)),min(ny,int((r[3]+radius-y0)/step)+1)):
                    blocked.add((i,j))
        def free(i,j):
            p=(x0+i*step,y0+j*step)
            return (i,j) not in blocked and any(inside(p,r) for r in regions)
        seed=(round((start[0]-x0)/step),round((start[1]-y0)/step))
        self.assertTrue(free(*seed),f'start {start} is not walkable')
        seen={seed};queue=deque([seed])
        while queue:
            i,j=queue.popleft()
            for n in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
                if n not in seen and 0<=n[0]<nx and 0<=n[1]<ny and free(*n):
                    seen.add(n);queue.append(n)
        return lambda p:(round((p[0]-x0)/step),round((p[1]-y0)/step)) in seen

    def test_traced_room_set_and_internal_passages(self):
        self.assertEqual([r['label'] for r in self.office['rooms']],['W'+str(i).zfill(2) for i in range(1,24) if i!=3])
        self.assertEqual([c['id'] for c in self.office['corridors']],['WI1','WI2','WI3','WI4'])
        fp=self.office['footprint']
        for room in self.office['rooms']:
            self.assertTrue(all(fp[i]-1e-6<=room['bounds'][i] if i<2 else room['bounds'][i]<=fp[i]+1e-6 for i in range(4)),room['label'])
        for a in self.office['rooms']:
            for b in self.office['rooms']:
                if a is not b:
                    self.assertFalse(overlaps(a['bounds'],b['bounds']),(a['label'],b['label']))

    def test_c8_stub_no_longer_crosses_the_offices(self):
        c8=self.corridors['corridor_8'];fp=self.office['footprint']
        self.assertAlmostEqual(c8[1],fp[3])
        self.assertAlmostEqual(c8[1],self.corridors['corridor_7'][1])
        base_c8=next(c for c in self.base['corridors'] if c['id']=='corridor_8')['bounds']
        self.assertEqual(c8[3],base_c8[3])
        base_ids={c['id'] for c in self.base['corridors']}
        others=[c for c in self.layout['corridors'] if c['id']!='corridor_8' and c['id'] in base_ids]
        self.assertEqual(others,[c for c in self.base['corridors'] if c['id']!='corridor_8'])
        self.assertEqual([c['id'] for c in self.layout['corridors'] if c['id'] not in base_ids],['c7_core_bypass'])

    def test_internal_spine_has_no_crossing_walls(self):
        for passage in self.office['corridors']:
            r=passage['bounds'];clear=[r[0]+.2,r[1]+.2,r[2]-.2,r[3]-.2]
            for w in self.solid:
                self.assertFalse(overlaps(w,clear),f'{passage["id"]} crossed by {w}')

    def test_former_w03_connects_spine_straight_to_c7(self):
        wi4=next(c for c in self.office['corridors'] if c['id']=='WI4')['bounds']
        spine=next(c for c in self.office['corridors'] if c['id']=='WI1')['bounds'];c7=self.corridors['corridor_7']
        self.assertAlmostEqual(wi4[1],spine[3]);self.assertAlmostEqual(wi4[3],c7[1])
        # Clear from mid-spine to mid-C7, the connector's width less wall margins.
        through=[wi4[0]+.2,(spine[1]+spine[3])/2,wi4[2]-.2,(c7[1]+c7[3])/2]
        for w in self.solid:
            self.assertFalse(overlaps(w,through),f'WI4 blocked by {w}')
        self.assertGreater(wi4[2]-wi4[0]-.16,1.5)

    def test_spine_east_end_opens_onto_c5(self):
        spine=next(c for c in self.office['corridors'] if c['id']=='WI1')['bounds'];c5=self.corridors['corridor_5']
        through=[(spine[0]+spine[2])/2,spine[1]+.2,(c5[0]+c5[2])/2,spine[3]-.2]
        for w in self.solid:
            self.assertFalse(overlaps(w,through),f'WI1 east end blocked by {w}')
        for x in (spine[2]+.05,(spine[2]+c5[0])/2,c5[0]-.05):
            for y in (spine[1]+.1,(spine[1]+spine[3])/2,spine[3]-.1):
                self.assertTrue(any(inside((x,y),s) for s in self.floor['slabs']),f'no floor at {(x,y)}')
        self.assertTrue(self.walkable_from(((spine[0]+spine[2])/2,(spine[1]+spine[3])/2))((23.0,9.0)))

    def test_stair_door_threshold_stays_clear_and_reaches_c5(self):
        t=self.corridors['retained_stair_threshold']
        clear=[t[0]+.1,t[1]+.1,t[2]-.2,18.0]
        for w in self.solid:
            self.assertFalse(overlaps(w,clear),f'stair threshold blocked by {w}')
        reach=self.walkable_from((19.2,17.4))
        self.assertTrue(reach((23.0,12.0)),'stair door cannot reach C5')

    def test_c7_passes_south_of_the_main_core_to_c5(self):
        bypass=self.corridors['c7_core_bypass'];core=self.layout['core'];c7=self.corridors['corridor_7']
        self.assertAlmostEqual(bypass[3],core[1])
        self.assertAlmostEqual(bypass[3]-bypass[1],c7[3]-c7[1])
        self.assertLess(bypass[0],core[0]);self.assertEqual(bypass[2],self.corridors['corridor_5'][0])
        clear=[bypass[0]+.2,bypass[1]+.2,bypass[2]+.3,bypass[3]-.2]
        for w in self.solid:
            self.assertFalse(overlaps(w,clear),f'C7 bypass blocked by {w}')
        reach=self.walkable_from((-5.0,19.0))
        self.assertTrue(reach((23.0,12.0)),'C7 cannot reach C5')
        self.assertTrue(reach((19.2,17.4)),'C7 cannot reach the stair door')
        # The offices stay closed along the bypass: solid wall at every sample.
        for i in range(int((bypass[2]-bypass[0])/.1)):
            p=(bypass[0]+.05+i*.1,bypass[1])
            self.assertTrue(any(inside(p,w) for w in self.solid),f'gap in bypass south wall at {p}')
        w01=next(r for r in self.office['rooms'] if r['label']=='W01')
        self.assertAlmostEqual(w01['bounds'][3],bypass[1])
        self.assertIn('excluded_for_c7_bypass',next(r for r in self.office['rooms'] if r['label']=='W02'))

    def test_every_room_is_reachable_from_c7(self):
        e=self.office['entrance']['points']
        self.assertTrue(all(abs(p[1]-self.corridors['corridor_7'][1])<1e-6 for p in e))
        reach=self.walkable_from((-5.0,19.0))
        for passage in self.office['corridors']:
            r=passage['bounds'];self.assertTrue(reach(((r[0]+r[2])/2,(r[1]+r[3])/2)),passage['id'])
        for room in self.office['rooms']:
            r=room['bounds'];centre=((r[0]+r[2])/2,(r[1]+r[3])/2)
            self.assertTrue(reach(centre),room['label'])

    def test_other_floors_untouched(self):
        for n in (-2,0):
            self.assertEqual(next(f for f in self.layout['floors'] if f['f']==n),next(f for f in self.base['floors'] if f['f']==n))
