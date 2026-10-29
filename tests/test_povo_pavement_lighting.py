import unittest
from tools.build_povo_campus import render_obj
from tools.povo_exterior_integration import mesh_faces
from tools.povo_pavement import apron_normal,smooth_apron_lighting
from tools.build_povo_exterior import FACES
from tools.povo_pavement_lighting import surface_obj,SURFACE_OFFSET


def geometry(obj):
    vertices=[];uvs=[];faces=[]
    for line in obj.splitlines():
        if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
        elif line.startswith('vt '):uvs.append(tuple(map(float,line.split()[1:])))
        elif line.startswith('f '):
            refs=[r.split('/') for r in line.split()[1:]]
            faces.append(tuple((vertices[int(r[0])-1],uvs[int(r[1])-1]) for r in refs))
    return sorted(faces)


class PavementLightingTests(unittest.TestCase):
    def test_probe_finish_preserves_uvs_and_leaves_buildings_and_undersides_out(self):
        before=render_obj([
            ('paving',(0,0,0),(2,2,.22),'exterior_paving'),
            ('road',(3,0,0),(5,2,.16),'exterior_asphalt'),
            ('building',(6,0,0),(8,2,3),'wall')],[])
        after=surface_obj(before)
        original=geometry(before);finish=geometry(after)
        self.assertEqual(len(finish),20)
        for face in finish:
            a,b,c=[p for p,uv in face]
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            length=sum(q*q for q in n)**.5;n=tuple(q/length for q in n)
            self.assertGreaterEqual(n[2],0)
            structural=tuple((tuple(round(p[i]-SURFACE_OFFSET*n[i],10) for i in range(3)),uv) for p,uv in face)
            self.assertIn(structural,original)
        self.assertNotIn('usemtl campus_wall',after)

    def test_connected_strips_share_upward_normals_without_moving_any_face(self):
        meshes=[]
        for i,(a,c) in enumerate(((-3,0),(0,3))):
            def z(x,y):return 4+(3+(x+23)/45+.12-4)*(y+20)/12
            top=[(x,y,z(x,y)) for x,y in ((a,-20),(c,-20),(c,-8),(a,-8))]
            meshes.append(dict(name=f'exterior_paving_bridge_apron_{i}',material='exterior_paving',
                               vertices=[(x,y,h-.22) for x,y,h in top]+top,faces=FACES))
        before=render_obj([('unrelated_wall',(10,10,4),(11,11,7),'wall')],mesh_faces(dict(meshes=meshes)))
        after=smooth_apron_lighting(before)
        self.assertEqual(geometry(before),geometry(after))
        self.assertEqual(after.count('o backdrop_exterior_paving_bridge_apron_top\n'),1)
        self.assertIn('\ns 1\n',after)
        vertices=[];normals=[];in_top=False;at_seam={}
        for line in after.splitlines():
            if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
            elif line.startswith('vn '):normals.append(tuple(map(float,line.split()[1:])))
            elif line.startswith('o '):in_top=line.endswith('bridge_apron_top')
            elif line.startswith('f ') and in_top:
                for r in line.split()[1:]:
                    v,_,n=map(int,r.split('/'));point=vertices[v-1];normal=normals[n-1]
                    self.assertGreater(normal[2],.99)
                    if abs(point[0])<1e-8:at_seam.setdefault(point,set()).add(normal)
        self.assertEqual(len(at_seam),2)
        self.assertTrue(all(len(n)==1 for n in at_seam.values()))

    def test_non_apron_geometry_is_not_rewritten(self):
        obj=render_obj([('floor',(0,0,0),(2,2,.2),'floor_room')],[])
        self.assertEqual(smooth_apron_lighting(obj),obj)

    def test_grade_normal_matches_the_existing_height_gradient(self):
        n=apron_normal(0,-14)
        self.assertAlmostEqual(sum(v*v for v in n),1,places=9)
        self.assertLess(n[0],0)
        self.assertGreater(n[1],0)
        self.assertEqual(apron_normal(23,-14)[0],0)
