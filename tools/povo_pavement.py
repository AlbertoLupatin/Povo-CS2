"""Continuous plaza paving and closed collision at road/pavement joins."""
import json
import math
from pathlib import Path
try:
    from .povo_room_fitout import subtract_box
    from .build_povo_interior import subtract_rectangles
except ImportError:
    from povo_room_fitout import subtract_box
    from build_povo_interior import subtract_rectangles


def extend(boxes, levels, root=Path(__file__).resolve().parents[1]):
    result=list(boxes);ext=levels[0]['exterior'];spec=levels[1]['connection']['povo2']
    yard=spec['additions']['yard']['bounds']
    # Fill the whole lower plaza, rather than a collection of disconnected
    # narrow entrance paths. The upper street and existing stairs stay above it.
    zones=[('povo1_lower_plaza',[24,-116,36,-13],4),
           ('povo1_south_pavement',[36,-116,58,-110],7.6),
           ('povo2_north_pavement',[25,112,58,120],4)]
    for name,r,z in zones:
        parts=[('exterior_paving_'+name,(r[0],r[1],z-.22),(r[2],r[3],z),'exterior_paving')]
        parts=[p for box in parts for p in subtract_box(box,((yard[0]-.12,yard[1]-.12,-1),(yard[2]+.12,yard[3]+.12,4.4)))]
        result.extend(parts)
    # North of Povo 1, smoothly meet the sloping bridge road. Cut the moved
    # yard out in plan before building closed prisms, so it remains sunken.
    def height(x,y):
        road=3+min(1,max(0,(x+23)/45))+.12
        return 4+(road-4)*min(1,max(0,(y+20)/12))
    def prism(name,top,material='exterior_paving',thickness=.22):
        vertices=[(x,y,z-thickness) for x,y,z in top]+top
        faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),
               (0,1,5),(0,5,4),(1,2,6),(1,6,5),
               (2,3,7),(2,7,6),(3,0,4),(3,4,7)]
        mesh=dict(name=name,vertices=vertices,faces=faces,material=material)
        ext['meshes'].append(mesh);ext['collision_meshes'].append(mesh)
    exclusions=[(yard[0]-.12,yard[1]-.12,yard[2]+.12,yard[3]+.12)]
    # Avoid a single twisted quad: subdivide the bilinear grade into small
    # triangles; the render and collision share the very same surface.
    for i in range(24):
        a=-23+47*i/24;c=-23+47*(i+1)/24
        for j,r in enumerate(subtract_rectangles((a,-20,c,-8),exclusions)):
            a0,b,c0,d=r
            prism(f'exterior_paving_bridge_apron_{i}_{j}',
                  [(a0,b,height(a0,b)),(c0,b,height(c0,b)),
                   (c0,d,height(c0,d)),(a0,d,height(a0,d))])
    # Road junction disks used to be render-only, with no supporting collision
    # between the straight strips. Give each disk closed, matching physics.
    for mesh in list(ext['meshes']):
        if '_joint_' not in mesh['name'] or len(mesh['vertices'])!=17:continue
        top=mesh['vertices'][1:];n=len(top)
        vertices=[(x,y,z-.16) for x,y,z in top]+top
        faces=[]
        for i in range(1,n-1):faces.extend([(0,i+1,i),(n,n+i,n+i+1)])
        for i in range(n):
            j=(i+1)%n;faces.extend([(i,j,n+j),(i,n+j,n+i)])
        mesh.update(vertices=vertices,faces=faces)
        ext['collision_meshes'].append(mesh)
    # Fill outer footway wedges at flat road bends. Sloping breaks are kept as
    # their original strips: a flat ring there would itself create a drop.
    cfg=json.loads((root/'config/povo_exterior.json').read_text())
    for roadname in ('road','north_road','front_road'):
        road=cfg[roadname]
        for k,(a,p,b) in enumerate(zip(road['points'],road['points'][1:],road['points'][2:])):
            if max(abs(a[2]-p[2])/math.dist(a[:2],p[:2]),abs(b[2]-p[2])/math.dist(b[:2],p[:2]))>.03:continue
            u=[p[i]-a[i] for i in range(2)];v=[b[i]-p[i] for i in range(2)]
            if abs(u[0]*v[1]-u[1]*v[0])<1e-7:continue
            inner=road['width']/2;outer=inner+road['footway_width']
            for i in range(24):
                t=i*math.tau/24;s=(i+1)*math.tau/24
                top=[(p[0]+r*math.cos(q),p[1]+r*math.sin(q),p[2]+.12)
                     for r,q in ((inner,t),(outer,t),(outer,s),(inner,s))]
                prism(f'exterior_paving_{roadname}_corner_{k}_{i}',top)
    ext['pavement_repairs']=dict(zones=[dict(id=n,bounds=r,z=z) for n,r,z in zones],
                                bridge_apron=[-23,-20,24,-8],yard_exclusion=yard,
                                junctions='Closed collision matches rendered road disks; flat footway bends filled')
    return result
