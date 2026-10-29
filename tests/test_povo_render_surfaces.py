import tempfile
import unittest
from pathlib import Path
from tools.build_povo_campus import render_obj
from tools.audit_povo_render_surfaces import audit
from tools.povo_render_surfaces import exclusive_faces,project
from tools.povo_floor_surfaces import area,subtract


class RenderSurfaceTests(unittest.TestCase):
    def test_overlapping_walls_slopes_and_negative_normals_preserve_union_and_uvs(self):
        for transform,axes in ((lambda x,y:(4,x,y),(1,2)),(lambda x,y:(x,4,y),(0,2)),(lambda x,y:(x,y,4+x*.3+y*.2),(0,1))):
            for reverse in (False,True):
                with self.subTest(transform=transform,reverse=reverse):
                    faces=[]
                    for x0,y0,x1,y1 in ((0,0,4,2),(1,-1,3,3)):
                        xy=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
                        if reverse:xy.reverse()
                        faces.append(('wall','campus_wall',[transform(x,y) for x,y in xy],[(x/2,y/3) for x,y in xy]))
                    result=list(exclusive_faces(faces))
                    normal_key=project(faces[0][2])[0]
                    projected_area=sum(area(project(f[2])[1]) for f in result)
                    self.assertAlmostEqual(projected_area,12)
                    for _,_,points,uvs in result:
                        self.assertEqual(project(points)[0],normal_key)
                        for point,uv in zip(points,uvs):
                            self.assertAlmostEqual(uv[0],point[axes[0]]/2)
                            self.assertAlmostEqual(uv[1],point[axes[1]]/3)

    def test_thin_surfaces_and_opposite_sides_stay_separate(self):
        points=[(0,0,4),(2,0,4),(2,2,4)]
        uv=[p[:2] for p in points]
        faces=[('front','campus_wall',points,uv),('back','campus_wall',list(reversed(points)),list(reversed(uv))),
               ('offset','campus_wall',[(x,y,z+.003) for x,y,z in points],uv)]
        self.assertEqual(len(list(exclusive_faces(faces))),3)

    def test_small_window_detail_owns_its_patch_of_a_large_car_body(self):
        body=[(0,0,0),(0,4,0),(0,4,3),(0,0,3)]
        glass=[(0,1,1),(0,3,1),(0,3,2),(0,1,2)]
        faces=[('body','campus_car_blue',body,[(y,z) for _,y,z in body]),
               ('window','campus_car_glass',glass,[(y,z) for _,y,z in glass])]
        result=list(exclusive_faces(faces))
        by_material={material:sum(area(project(f[2])[1]) for f in result if f[1]==material)
                     for material in ('campus_car_blue','campus_car_glass')}
        self.assertAlmostEqual(by_material['campus_car_glass'],2)
        self.assertAlmostEqual(by_material['campus_car_blue'],10)

    def test_nearly_flat_small_triangles_share_the_same_plane(self):
        points=[(-35,-11,3.12),(-34.8887,-11,3.12),(-34.8887,-11.1112,3.12+1e-14)]
        self.assertEqual(project(points)[0],(0,0,-1,-3.12))

    def test_repeated_clipped_vertices_do_not_create_false_cutting_edges(self):
        subject=[(-1,-1),(3,-1),(3,3),(-1,3)]
        cutter=[(0,0),(2,0),(2,2),(2+1e-14,2-1e-14),(0,2)]
        self.assertAlmostEqual(sum(area(p) for p in subtract(subject,cutter)),12)

    def test_export_and_audit_cover_vertical_overlaps(self):
        boxes=[('wall_a',(0,0,0),(1,4,2),'wall'),('wall_b',(0,1,-1),(1,3,3),'wall')]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'mesh.obj'
            path.write_text(render_obj(boxes,[],resolve_surfaces=False))
            before=audit(path)
            self.assertGreater(before['by_orientation']['vertical'],0)
            path.write_text(render_obj(boxes,[]))
            self.assertEqual(audit(path)['overlapping_pairs'],0)
