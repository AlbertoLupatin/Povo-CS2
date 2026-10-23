import copy
import unittest

from tools.povo_architecture import architecture_boxes, validate_architecture


class ArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.building = {"id": "campus", "bounds": [100,200,120,230],
                         "base_elevation": 10, "roof_elevation": 25}
        self.facade = {"id": "test", "building": "campus", "face": "east",
                       "style": "stone_windows", "bays": 5, "rows": 3,
                       "bottom_elevation": 11, "top_elevation": 24,
                       "frame_width": .06, "depth": .06, "edge_margin": .4,
                       "reference_ids": ["P001"], "placement_note": "Synthetic placement"}
        self.spec = {"reference_manifest": "photos.json", "assumptions": "Synthetic",
                     "facades": [self.facade]}

    def boxes(self, spec=None):
        validated = validate_architecture(spec or self.spec, [self.building])
        return architecture_boxes({"architecture": validated, "buildings": [self.building],
                                   "origin": [100,200,10]})

    def test_facades_are_local_finite_closed_box_extents_on_all_four_faces(self):
        for face, axis, sign, plane in (("east",0,1,20),("west",0,-1,0),
                                         ("north",1,1,30),("south",1,-1,0)):
            self.facade["face"] = face
            boxes=self.boxes()
            for _name, minimum, maximum, _material in boxes:
                self.assertTrue(all(a < b for a,b in zip(minimum,maximum)))
                if sign>0:self.assertGreater(minimum[axis],plane)
                else:self.assertLess(maximum[axis],plane)
        self.assertEqual(self.boxes(), self.boxes())

    def test_invalid_dimensions_duplicate_faces_and_part_budget_are_rejected(self):
        for field,value in (("bays",True),("rows",101),("frame_width",5),
                            ("depth",float("nan")),("bottom_elevation",30),
                            ("style","unsupported"),("reference_ids",[])):
            spec=copy.deepcopy(self.spec);spec["facades"][0][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):self.boxes(spec)
        spec=copy.deepcopy(self.spec)
        spec["facades"].append({**self.facade,"id":"other"})
        with self.assertRaisesRegex(ValueError,"Only one facade"):self.boxes(spec)
        spec=copy.deepcopy(self.spec)
        spec["facades"][0].update(bays=100,rows=100,frame_width=.0001)
        with self.assertRaisesRegex(ValueError,"budget"):self.boxes(spec)

    def test_bridge_keeps_open_centre_and_has_explicit_deck_and_roof(self):
        spec={**self.spec,"facades":[],"bridge":{
            "building":"campus","deck_elevation":15,"roof_elevation":18.2,
            "post_spacing":3,"louver_spacing":.24,"reference_ids":["P013","P015"],
            "placement_note":"Synthetic bridge dimensions"}}
        boxes=self.boxes(spec)
        by_name={name:(lo,hi) for name,lo,hi,_mat in boxes}
        self.assertEqual(by_name["arch_bridge_deck"],((0,0,4.75),(20,30,5)))
        self.assertAlmostEqual(by_name["arch_bridge_roof"][1][2],8.2)
        point=(10,15,6.5)
        self.assertFalse(any(all(lo[i]<point[i]<hi[i] for i in range(3))
                             for _name,lo,hi,_mat in boxes))


if __name__ == "__main__":
    unittest.main()
