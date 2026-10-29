import unittest
import tempfile
from pathlib import Path

from tools.build_povo_campus import render_obj
from tools.audit_povo_floor_surfaces import audit
from tools.povo_floor_surfaces import area, exclusive_tops, subtract


def rectangle(material, x0,y0,x1,y1,z=4):
    points=[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    return 'floor',material,points,[(x/.6,y/.6) for x,y,_ in points]


class FloorSurfaceTests(unittest.TestCase):
    def test_crossing_slabs_keep_union_coverage_and_uvs_without_overlap(self):
        faces=[rectangle('campus_floor_p2_tile',0,0,4,2),
               rectangle('campus_floor_circulation',1,-1,3,3),
               rectangle('campus_exterior_paving',0,0,4,2)]
        result=list(exclusive_tops(faces))
        self.assertAlmostEqual(sum(area(f[2]) for f in result),12)
        self.assertNotIn('campus_exterior_paving',[f[1] for f in result])
        for i,(_,_,points,uvs) in enumerate(result):
            for p,uv in zip(points,uvs):
                self.assertAlmostEqual(uv[0],p[0]/.6)
                self.assertAlmostEqual(uv[1],p[1]/.6)
                self.assertEqual(p[2],4)
            for other in result[i+1:]:
                self.assertAlmostEqual(sum(area(p) for p in subtract(points,other[2])),area(points))

    def test_different_storeys_and_touching_edges_are_retained(self):
        faces=[rectangle('campus_floor_room',0,0,2,2),
               rectangle('campus_floor_room',2,0,4,2),
               rectangle('campus_floor_room',0,0,2,2,7.6)]
        self.assertAlmostEqual(sum(area(f[2]) for f in exclusive_tops(faces)),12)

    def test_export_removes_duplicate_tops_but_keeps_walls_and_undersides(self):
        obj=render_obj([('tile',(0,0,3.78),(4,2,4),'floor_p2_tile'),
                        ('circulation',(1,-1,3.78),(3,3,4),'floor_circulation'),
                        ('wall',(6,0,4),(7,2,7),'wall')],[])
        vertices=[];tops=0;bottoms=0
        for line in obj.splitlines():
            if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
            if not line.startswith('f '):continue
            points=[vertices[int(r.split('/')[0])-1] for r in line.split()[1:]]
            if all(abs(p[2]-4)<1e-9 for p in points):tops+=area(points)
            if all(abs(p[2]-3.78)<1e-9 for p in points):bottoms+=area(points)
        self.assertAlmostEqual(tops,14)  # 12 m² floor union plus 2 m² wall base
        self.assertAlmostEqual(bottoms,12)
        self.assertIn('usemtl campus_wall',obj)

    def test_audit_detects_duplicate_triangles_but_accepts_shared_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'floor.obj'
            source='v 0 0 4\nv 2 0 4\nv 2 2 4\nv 0 2 4\nusemtl campus_floor_room\nf 1 2 3\nf 1 3 4\n'
            path.write_text(source)
            self.assertEqual(audit(path)['status'],'passed')
            path.write_text(source+'f 1 2 3\n')
            self.assertEqual(audit(path)['overlapping_pairs'],1)
