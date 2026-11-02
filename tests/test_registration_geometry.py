"""Registration must change real silhouettes, leaving courtyard caps open."""
import json
import math
import unittest

from tools.polygon_mesh import prism
from tools.povo_edges import ROOT, build


def cap_area(mesh):
    top=max(p[2] for p in mesh['vertices'])
    area=0
    for face in mesh['faces']:
        a,b,c=[mesh['vertices'][i] for i in face]
        if all(abs(p[2]-top)<1e-8 for p in (a,b,c)):
            area+=((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
    return area


def cap_covers(mesh, point):
    top=max(p[2] for p in mesh['vertices'])
    for face in mesh['faces']:
        p=[mesh['vertices'][i] for i in face]
        if not all(abs(v[2]-top)<1e-8 for v in p):continue
        if any(point[i]<min(v[i] for v in p)-1e-8 or point[i]>max(v[i] for v in p)+1e-8 for i in (0,1)):continue
        crosses=[(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
                 for a,b in zip(p,p[1:]+p[:1])]
        if min(crosses)>=-1e-8:return True
    return False


class RegistrationGeometryTests(unittest.TestCase):
    def test_concave_prism_with_multiple_holes_has_correct_area_and_volume(self):
        outer=[(0,0),(12,0),(12,8),(8,8),(8,12),(0,12)]
        holes=[[(1,1),(3,1),(3,4),(1,4)],[(5,5),(7,5),(7,7),(5,7)]]
        for reverse in (False,True):
            rings=[r[::-1] if reverse else r for r in [outer,*holes]]
            # Exercise closed OSM rings, independent of their winding.
            m=prism('test',[r+[r[0]] for r in rings],2,5,'white')
            self.assertAlmostEqual(cap_area(m),118)
            volume=0
            for face in m['faces']:
                a,b,c=[m['vertices'][i] for i in face]
                cross=(b[1]*c[2]-b[2]*c[1],b[2]*c[0]-b[0]*c[2],b[0]*c[1]-b[1]*c[0])
                volume+=sum(a[i]*cross[i] for i in range(3))/6
            self.assertAlmostEqual(volume,590)
            for point in ((2,2),(6,6),(10,10)):
                self.assertFalse(cap_covers(m,point),point)
            self.assertTrue(cap_covers(m,(10,2)))

    def test_fbk_roofs_leave_all_five_courtyards_open(self):
        meshes,meta=build();byname={m['name']:m for m in meshes}
        count=0
        for item in meta['config']['buildings']:
            mass=byname['exterior_edges_'+item['id']+'_mass']
            roof=byname['exterior_edges_'+item['id']+'_roof']
            self.assertAlmostEqual(cap_area(mass),cap_area(roof),places=6)
            ground=8 if item['id']=='fbk_south_link' else item['base_z']
            self.assertAlmostEqual(max(p[2] for p in roof['vertices'])-ground,
                                   item['registration']['lidar_height_above_ground_m'])
            for ring in item['courtyards']:
                point=tuple(sum(p[i] for p in ring)/len(ring) for i in (0,1))
                self.assertFalse(cap_covers(mass,point),item['id'])
                self.assertFalse(cap_covers(roof,point),item['id'])
                count+=1
        self.assertEqual(count,5)
        self.assertNotIn('fbk_far_south_south',{b['id'] for b in meta['config']['buildings']})
        ring=next(b for b in meta['config']['buildings'] if b['id']=='fbk_far_south_ring')
        self.assertFalse(cap_covers(byname['exterior_edges_fbk_far_south_ring_roof'],(185,-220)))
        bridge=byname['exterior_edges_fbk_south_link_mass']
        self.assertGreaterEqual(min(p[2] for p in bridge['vertices'])-8,4)
        self.assertLess(cap_area(bridge),60)

    def test_corrected_northern_road_tracks_cached_osm(self):
        data=json.loads((ROOT/'data/reference/osm/povo_osm_overture.geojson').read_text())
        reference=[f for f in data['features'] if f['properties']['osm'] in ('w1120770362','w1394224846')]
        segments=[(a,b) for f in reference for a,b in zip(f['geometry']['coordinates'],f['geometry']['coordinates'][1:])]
        front=json.loads((ROOT/'config/povo_exterior.json').read_text())['front_road']['points'][2:]
        _,meta=build()
        approach=next(r for r in meta['config']['roads'] if r['id']=='north_roundabout_approach')['points']
        def distance(p,a,b):
            d=[b[i]-a[i] for i in (0,1)]
            t=max(0,min(1,sum((p[i]-a[i])*d[i] for i in (0,1))/sum(v*v for v in d)))
            return math.hypot(*(p[i]-a[i]-t*d[i] for i in (0,1)))
        for x,y,z in front+approach:
            self.assertLess(min(distance((x+666250,y+5103800),a,b) for a,b in segments),.1)
            self.assertEqual(z,4)

    def test_roundabout_and_branch_are_exposed_above_scenery_ground(self):
        meshes,meta=build();r=meta['config']['roundabout'];x,y,z=r['centre']
        radius=(r['outer_radius']+r['inner_radius'])/2
        points=[(x+radius*math.cos(i*math.tau/24),y+radius*math.sin(i*math.tau/24)) for i in range(24)]
        points.append((103.9,110.71))
        grass=[m for m in meshes if m['material']=='exterior_grass']
        for point in points:
            for m in grass:
                if max(v[2] for v in m['vertices'])>=z:
                    self.assertFalse(cap_covers(m,point),(m['name'],point))
        # The retained hedge terminates before the roundabout carriageway.
        for point in meta['config']['hedge']['points']:
            self.assertGreater(math.dist(point[:2],r['centre'][:2]),r['outer_radius']+1.25)


if __name__=='__main__':unittest.main()
