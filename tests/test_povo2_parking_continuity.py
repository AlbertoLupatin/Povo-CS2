"""Actual registered parking connectivity and terrace sight lines."""
import unittest

from tools.build_povo_campus import build_registered_geometry, collision_boxes
from tools.audit_povo_exterior_integrated import standing, route_points, height_at
from tools.povo_physics_surfaces import surface
from tools.povo_textures import resolve


class ParkingContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,cls.boxes,cls.levels,_ = build_registered_geometry()
        cls.p = next(l['connection']['povo2'] for l in cls.levels if l.get('connection'))
        cls.ext = cls.levels[0]['exterior']
        cls.spec = cls.p['parking']['continuous']
        cls.physics = collision_boxes(cls.boxes)

    def test_ramp_to_stairs_and_far_end_have_support_and_clearance(self):
        a,b = self.spec['ramp']['centreline']
        routes = [dict(points=[a,b,[-29,33,-3.2]])] + self.spec['routes']
        for route in routes:
            for x,y,z in route_points(route['points'],.25):
                foot,blocked = standing(x,y,z,self.physics,self.ext['collision_meshes'])
                self.assertIsNotNone(foot,(x,y,z))
                self.assertEqual(blocked,[],(x,y,z,blocked))

    def test_terrace_apertures_look_down_to_asphalt_without_false_roofs(self):
        for x0,y0,x1,y1 in self.spec['apertures']:
            for x in (x0+.2,(x0+x1)/2,x1-.2):
                for y in (y0+.5,(y0+y1)/2,y1-.5):
                    floors = [m for _,lo,hi,m in self.boxes
                              if lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1]
                              and abs(hi[2]+3.2)<.01]
                    self.assertTrue(any(surface(m)=='asphalt' for m in floors),(x,y,floors))
                    blockers = [n for n,lo,hi,m in self.boxes
                                if lo[0]<x<hi[0] and lo[1]<y<hi[1]
                                and hi[2]>-3.19 and lo[2]<20]
                    blockers += [m['name'] for m in self.ext['meshes']
                                 if any(-3.19<h<20 for h in height_at(m,x,y))]
                    self.assertEqual(blockers,[],(x,y,blockers))

    def test_covered_terrace_sections_keep_cover_and_ramp_stays_asphalt(self):
        for y in (37.4,91.5):
            self.assertTrue(any(lo[0]<-24.6<hi[0] and lo[1]<y<hi[1]
                                and -.2<=lo[2]<1 and hi[2]>.1
                                for _,lo,hi,_ in self.boxes))
        ramps = [m for m in self.ext['meshes'] if 'garage_ramp' in m['name']]
        self.assertEqual(len(ramps),2)
        for ramp in ramps:
            self.assertEqual(ramp['material'],'exterior_asphalt')
            self.assertEqual(surface(ramp['material']),'asphalt')
            self.assertEqual(resolve(ramp['material'],''),
                             'materials/asphalt/hr_c/hr_asphalt_001.vmat')
        self.assertEqual(self.spec['ramp']['centreline'],[[-29,-2.5,3.],[-29,30,-3.2]])
