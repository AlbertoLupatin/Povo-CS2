import unittest
from tools.povo_glass_tiles import split_tiles


class GlassTileTests(unittest.TestCase):
    def test_visible_mullions_and_transoms_make_independent_tiles(self):
        glass=[('facet',(0,-.012,0),(3,.012,3),'window_glass')]
        frames=[('window_mullion_1',(.975,-.05,0),(1.025,.05,3),'window_frame'),
                ('window_mullion_2',(1.975,-.05,0),(2.025,.05,3),'window_frame'),
                ('window_transom_1',(0,-.05,1.475),(3,.05,1.525),'window_frame')]
        panes=split_tiles(glass,frames)
        self.assertEqual(len(panes),6)
        self.assertEqual(len({p['name'] for p in panes}),6)
        self.assertEqual({p['source_facet'] for p in panes},{'facet'})
        self.assertTrue(all(p['hi'][0]-p['lo'][0]<=1.001 and p['hi'][2]-p['lo'][2]<=1.501 for p in panes))
        self.assertAlmostEqual(sum((p['hi'][0]-p['lo'][0])*(p['hi'][2]-p['lo'][2]) for p in panes),9)
        # Removing one tile leaves every other tile and the original frames.
        intact=[p for p in panes if p['name']!=panes[0]['name']]
        self.assertEqual(len(intact),5)
        self.assertEqual(len(frames),3)

    def test_decorative_louvers_and_remote_frames_do_not_split_a_pane(self):
        glass=[('facet',(0,-.012,0),(3,.012,3),'window_glass')]
        frames=[('bridge_louver_0',(0,-.14,1),(3,.14,1.08),'window_frame'),
                ('remote_mullion',(.9,10,0),(1.1,10.1,3),'window_frame')]
        panes=split_tiles(glass,frames)
        self.assertEqual(len(panes),1)
        self.assertEqual(panes[0]['name'],'facet')


if __name__=='__main__':unittest.main()
