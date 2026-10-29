import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.audit_povo_exterior_visibility import VIEWS,audit,inspect_ground


class ExteriorVisibilityTests(unittest.TestCase):
    def test_black_pavement_is_rejected_but_blue_shadow_is_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ground.png'
            Image.new('RGB',(100,100),(0,0,0)).save(p)
            self.assertFalse(inspect_ground(p,(.1,.5,.9,.9))['passed'])
            Image.new('RGB',(100,100),(25,40,55)).save(p)
            self.assertTrue(inspect_ground(p,(.1,.5,.9,.9))['passed'])

    def test_dark_sky_or_windows_outside_the_ground_region_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'ground.png'
            image=Image.new('RGB',(100,100),(0,0,0))
            image.paste((150,150,150),(0,50,100,100));image.save(p)
            self.assertTrue(inspect_ground(p,(.1,.55,.9,.95))['passed'])

    def test_wrong_view_and_fullbright_cannot_prove_visible_pavement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);records=[]
            for name,(feet,pitch,yaw,_) in VIEWS.items():
                Image.new('RGB',(100,100),(150,150,150)).save(root/(name+'.png'))
                records.append(dict(name=name,actual_feet=feet,pitch=pitch,yaw=yaw))
            (root/'captures.json').write_text(json.dumps(records))
            (root/'console.log').write_text('> mat_fullbright 0\n')
            self.assertEqual(audit(root)['status'],'passed')
            records[0]['yaw']=0
            (root/'captures.json').write_text(json.dumps(records))
            self.assertEqual(audit(root)['status'],'failed')
            (root/'console.log').write_text('> mat_fullbright 1\n> mat_fullbright 0\n')
            with self.assertRaises(ValueError):audit(root)
