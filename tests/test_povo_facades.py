"""The approved elevation must create real apertures and preserve circulation."""
import json
from pathlib import Path
import unittest

from tools.build_povo_campus import build_geometry, collision_boxes, is_breakable_glass
from tools.povo_facades import intersect, schedule

ROOT = Path(__file__).resolve().parents[1]


class FacadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings, cls.config, cls.boxes, cls.levels, cls.stair = build_geometry()
        cls.spec = json.loads((ROOT/'config/povo_facades.json').read_text())
        cls.facades = cls.levels[0]['facades']

    def test_short_ends_share_six_broad_bays_and_long_sides_match(self):
        faces = {f['id']:f for f in schedule(self.spec)}
        for name in ('p1_north', 'p1_south', 'p2_south'):
            self.assertEqual([(s[2], s[3]) for s in faces[name]['segments']], [(6, 'broad')])
        self.assertEqual(faces['p1_east']['segments'], faces['p1_west']['segments'])
        for face in ('p1_south', 'p2_south'):
            actual = [p for p in self.facades['openings'] if p['face']==face and p['floor']==0]
            self.assertEqual(len(actual), 6)

    def test_every_new_pane_has_no_opaque_shell_in_its_aperture(self):
        opaque = [b for b in self.boxes if b[3] in ('wall', 'stone_facade', 'exterior_stone')]
        for p in self.facades['openings']:
            lo, hi = p['glass']
            # Interior room partitions can terminate at a pane; inspect its
            # central region rather than claiming the rooms lack partitions.
            f = next(f for f in self.facades['faces'] if f['id']==p['face'])
            axis = f['axis']; sample = [(lo[i]+hi[i])/2 for i in range(3)]
            sample[2] = lo[2]+(hi[2]-lo[2])*.6
            # Sample five horizontal positions so a narrow wall fragment cannot
            # hide behind a large pane's single midpoint.
            for t in (.1, .3, .5, .7, .9):
                sample[1-axis] = lo[1-axis]+t*(hi[1-axis]-lo[1-axis])
                hit = [b[0] for b in opaque if all(b[1][i]+1e-6 < sample[i] < b[2][i]-1e-6 for i in range(3))]
                self.assertFalse(hit, (p['face'], p['bay'], sample, hit))

    def test_bridge_remains_east_and_both_portals_have_clear_headroom(self):
        bridge = self.facades['bridge_bounds']
        self.assertEqual(bridge, [16.5, -20., 20., 10.])
        for y in (-20., 10.):
            for x in (16.9, 18.25, 19.6):
                for z in (11.3, 12.2, 13.7):
                    hits = [b[0] for b in collision_boxes(self.boxes)
                            if all(b[1][i]+1e-6 < p < b[2][i]-1e-6 for i,p in enumerate((x,y,z)))]
                    self.assertFalse(hits, (x,y,z,hits))

    def test_new_glazing_and_guards_have_deliberate_physics(self):
        pane = next(b for b in self.boxes if b[0].startswith('facade_p1_south_l2_') and b[0].endswith('_glass'))
        self.assertTrue(is_breakable_glass(pane))
        sealed = next(b for b in self.boxes if b[0].startswith('facade_p2_south_l2_') and b[0].endswith('_sealed_glass'))
        self.assertEqual(sealed[3], pane[3])  # Same appearance, distinct access policy.
        self.assertFalse(is_breakable_glass(sealed))
        bars = [b for b in self.boxes if b[0].startswith('facade_p1_') and '_guard_bar' in b[0]]
        physical = {b[0] for b in collision_boxes(bars)}
        self.assertEqual(len(physical), len(bars))
        self.assertTrue(bars)

    def test_automatic_entrance_is_not_backed_by_new_glass(self):
        entry = next(b for b in self.boxes if b[0]=='campus_entry_landing')
        cy = (entry[1][1]+entry[2][1])/2
        door = ((23.7,cy-.9,4.02),(24.3,cy+.9,6.0))
        self.assertFalse([b[0] for b in self.boxes if b[0].startswith('facade_p1_east')
                          and intersect((b[1],b[2]),door)])

    def test_upper_backdrop_return_meets_the_inner_skin_without_a_side_gap(self):
        for side in ('west','east'):
            box=next(b for b in self.boxes if b[0]=='facade_p2_south_upper_return_'+side)
            self.assertAlmostEqual(box[1][1],10.025)


if __name__ == '__main__':
    unittest.main()
