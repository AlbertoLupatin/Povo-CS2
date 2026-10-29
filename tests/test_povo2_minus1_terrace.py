"""Geometry checks for the user-corrected plan-46 external -1 terrace."""
import copy
import json
from collections import deque
from unittest import TestCase

from tools.build_povo_campus import ROOT
from tools.build_povo2_minus1_terrace import build, overlaps, solids


def near(p, r, pad):
    return r[0]-pad <= p[0] <= r[2]+pad and r[1]-pad <= p[1] <= r[3]+pad


class TerraceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT/'config/povo2_minus1_terrace.json').read_text(encoding='utf-8'))
        cls.base = json.loads((ROOT/cls.cfg['base_layout']).read_text(encoding='utf-8'))
        cls.before = copy.deepcopy(cls.base)
        cls.t = build(cls.base, cls.cfg)
        cls.slabs = [s['bounds'] for s in cls.t['slabs']]
        cls.rooms = {r['id']: r['bounds'] for r in cls.base['rooms']}
        cls.strip = [s['bounds'] for s in cls.t['slabs'] if s['id'].startswith('west_strip')]
        cls.south = next(s['bounds'] for s in cls.t['slabs'] if s['id'] == 'south_run')
        cls.north = next(s['bounds'] for s in cls.t['slabs'] if s['id'] == 'north_run')
        cls.holes = [h['bounds'] for h in cls.t['holes']]

    def on_terrace(self, p, pad=0.):
        return any(near(p, r, pad) for r in self.slabs)

    def test_base_layout_untouched(self):
        self.assertEqual(self.base, self.before)

    def test_terrace_stays_outside_the_building(self):
        for name, r in solids(self.base):
            for s in self.t['slabs']:
                self.assertFalse(overlaps(s['bounds'], r), f"{s['id']} overlaps {name}")

    def reachable(self, start, step=.1):
        """Cells a 0.1 m flood fill reaches over the terrace from start."""
        e0 = min(r[0] for r in self.slabs); n0 = min(r[1] for r in self.slabs)
        cell = lambda p: (round((p[0]-e0)/step), round((p[1]-n0)/step))
        free = lambda c: self.on_terrace((e0+c[0]*step, n0+c[1]*step))
        first = cell(start); self.assertTrue(free(first), start)
        seen = {first}; queue = deque([first])
        while queue:
            i, j = queue.popleft()
            for c in ((i+1, j), (i-1, j), (i, j+1), (i, j-1)):
                if c not in seen and free(c):
                    seen.add(c); queue.append(c)
        return seen, cell

    def test_both_stairs_reach_their_run_and_holes_interrupt_the_west(self):
        for stair in self.t['metal_stairs']:
            run = next(s['bounds'] for s in self.t['slabs'] if s['id'] == stair['run'])
            top = stair['flights'][0]
            seen, cell = self.reachable((top[0]-.15, (top[1]+top[3])/2))
            self.assertIn(cell((run[0]+.15, (run[1]+run[3])/2)), seen)
            for strip in self.strip:
                self.assertNotIn(cell(((strip[0]+strip[2])/2, (strip[1]+strip[3])/2)), seen)

    def test_bays_remain_accessible_but_do_not_bridge_the_hole(self):
        for r in self.t['recesses']:
            b = r['bounds']; bay, _ = self.reachable(((b[0]+b[2])/2, (b[1]+b[3])/2))
            self.assertGreater(len(bay), 1000, r['id'])
            self.assertFalse(self.on_terrace(((self.t['outer_edge_east']+b[0])/2, (b[1]+b[3])/2)))

    def test_user_markup_has_two_red_strips_and_three_blue_holes(self):
        self.assertEqual([(s[1], s[3]) for s in self.strip], [(19.2, 38.06), (73.3, 92.15)])
        self.assertEqual([(h[1], h[3]) for h in self.holes[:2]], [(2., 19.2), (38.06, 73.3)])
        self.assertAlmostEqual(self.holes[2][1], 92.15)
        self.assertAlmostEqual(self.holes[2][3], self.north[1])

    def test_holes_are_cut_out_of_the_slab(self):
        self.assertEqual(len(self.holes), 3)
        for h in self.holes:
            for s in self.t['slabs']:
                self.assertFalse(overlaps(h, s['bounds']), (h, s['id']))
            self.assertAlmostEqual(h[0], self.t['outer_edge_east']); self.assertAlmostEqual(h[2], self.t['facade_east'])

    def assert_hole_rails(self, rails):
        for h in self.holes:
            for s in self.slabs:
                touch = []
                if s[0] < h[2]-1e-6 and h[0] < s[2]-1e-6:
                    touch += [((max(s[0], h[0])+min(s[2], h[2]))/2, y) for y in (h[1], h[3]) if abs(s[3]-y) < 1e-6 or abs(s[1]-y) < 1e-6]
                if abs(s[0]-h[2]) < 1e-6 and s[1] < h[3]-1e-6 and h[1] < s[3]-1e-6:
                    touch.append((h[2], (max(s[1], h[1])+min(s[3], h[3]))/2))
                for p in touch:
                    self.assertTrue(any(near(p, r, 1e-6) for r in rails), (h, s, p))

    def test_every_hole_edge_is_railed(self):
        rails = [e['bounds'] for e in self.t['edges'] if e['kind'] == 'hole_rail']
        self.assert_hole_rails(rails)

    def test_hole_guard_check_detects_a_missing_rail(self):
        rails = [e['bounds'] for e in self.t['edges'] if e['kind'] == 'hole_rail']
        with self.assertRaises(AssertionError):
            self.assert_hole_rails(rails[1:])

    def test_facade_doors_keep_the_full_red_strip_outside(self):
        facade = self.t['facade_east']
        for e in self.t['served_exits']:
            p = e['campus_point']
            if p[0] < facade+.5:
                self.assertTrue(any(near(p, l, .35) and l[3]-l[1] >= 1.8-1e-6 for l in self.strip), e['id'])
                self.assertFalse(any(near(p, h, 0) for h in self.holes), e['id'])

    def test_bays_fill_the_office_row_recess(self):
        self.assertEqual(len(self.t['recesses']), 2)
        for r in self.t['recesses']:
            b = r['bounds']
            self.assertAlmostEqual(b[0], self.t['facade_east'])
            for office in r['fronting']:
                self.assertAlmostEqual(b[2], self.rooms[office][0])
                self.assertTrue(b[1] <= self.rooms[office][1] and self.rooms[office][3] <= b[3], office)
            low, high = sorted((self.rooms[i] for i in r['between']), key=lambda q: q[1])
            self.assertAlmostEqual(b[1], low[3]); self.assertAlmostEqual(b[3], high[1])
            self.assertAlmostEqual(r['depth'], 6.24, places=2)

    def test_every_west_facade_exit_lands_on_the_terrace(self):
        self.assertEqual(len(self.t['served_exits']), 8)
        for e in self.t['served_exits']:
            self.assertTrue(self.on_terrace(e['campus_point'], .35), e['id'])

    def test_outer_edge_closes_the_whole_west_run(self):
        west = sorted([e['bounds'] for e in self.t['edges'] if e['side'] == 'west']+self.holes+
                      [[self.t['outer_edge_east'], r[1], self.t['facade_east'], r[3]] for r in (self.south, self.north)], key=lambda r: r[1])
        self.assertAlmostEqual(west[0][1], self.south[1]); self.assertAlmostEqual(west[-1][3], self.north[3])
        for a, b in zip(west, west[1:]):
            self.assertAlmostEqual(a[3], b[1])
        self.assertNotIn('aperture', [e['kind'] for e in self.t['edges']])
        self.assertIn('north_run', [e['side'] for e in self.t['edges']])

    def test_two_metal_stairs_extend_the_north_and_south_runs(self):
        self.assertEqual({s['id'] for s in self.t['metal_stairs']}, {'north', 'south'})
        for st in self.t['metal_stairs']:
            run = next(s['bounds'] for s in self.t['slabs'] if s['id'] == st['run'])
            upper, lower = st['flights']
            self.assertAlmostEqual(upper[0], run[2])
            self.assertEqual((upper[1], upper[3]), (run[1], run[3]))
            self.assertAlmostEqual(st['mid_landing'][0], upper[2]); self.assertAlmostEqual(st['mid_landing'][2], lower[0])
            self.assertEqual(st['bottom_z'], -3.2)
            self.assertAlmostEqual(run[3]-run[1], self.t['width'], places=2)

    def test_north_run_is_flush_with_corridor_ends(self):
        for corridor in self.base['corridors']:
            if corridor['id'] in ('corridor_5', 'corridor_8'):
                self.assertAlmostEqual(self.north[1], corridor['bounds'][3])

    def test_columns_stand_on_the_facade_line_inside_the_bays(self):
        for c in self.t['columns']:
            self.assertTrue(any(r['bounds'][0] <= c[0] and c[2] <= r['bounds'][2] and r['bounds'][1] <= c[1] and c[3] <= r['bounds'][3]
                                for r in self.t['recesses']), c)
            self.assertLess(c[0]-self.t['facade_east'], .5)
