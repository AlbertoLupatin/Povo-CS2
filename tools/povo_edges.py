"""Aerial-traced outer scenery in the shared campus frame, without physics."""
import hashlib
import json
import math
from pathlib import Path

try:
    from .build_povo_exterior import strip
except ImportError:
    from build_povo_exterior import strip

ROOT = Path(__file__).resolve().parents[1]


def triangulate(points):
    """Ear clipping preserves concave ground outlines; returns CCW triangles."""
    cross = lambda a,b,c: (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    indices = list(range(len(points)))
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))
    if area < 0: indices.reverse()
    triangles = []
    while len(indices) > 3:
        for k,b in enumerate(indices):
            a,c = indices[k-1],indices[(k+1)%len(indices)]
            if cross(points[a],points[b],points[c]) <= 1e-9: continue
            if any(all(cross(points[u],points[v],points[p]) >= -1e-9
                       for u,v in ((a,b),(b,c),(c,a))) for p in indices if p not in (a,b,c)):
                continue
            triangles.append((a,b,c));indices.pop(k);break
        else: raise ValueError('Invalid scenery polygon')
    triangles.append(tuple(indices))
    return triangles


def build(root=ROOT):
    cfg = json.loads((root/'config/povo_edges.json').read_text())
    meshes = []
    def polygon(name, points, z, material, height=0):
        points = [tuple(p) for p in points]
        faces = triangulate(points)
        vertices = [(x,y,z) for x,y in points]
        if height:
            n=len(points);vertices += [(x,y,z+height) for x,y in points]
            top=[tuple(i+n for i in f) for f in faces]
            # Wind side walls using the same CCW order as the polygon.
            order=list(range(n))
            if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))<0:order.reverse()
            walls=[]
            for i,j in zip(order,order[1:]+order[:1]):walls.extend(((i,j,j+n),(i,j+n,i+n)))
            faces=[tuple(reversed(f)) for f in faces]+top+walls
        meshes.append(dict(name='exterior_edges_'+name,vertices=vertices,faces=faces,material='exterior_'+material))
    def box(name,lo,hi,mat):
        polygon(name,[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])],lo[2],mat,hi[2]-lo[2])
    def line(name,a,b,width,mat,thickness=.15):
        m=strip('exterior_edges_'+name,a,b,width,'exterior_'+mat,thickness);meshes.append(m)
    for land in cfg['landscape']:
        polygon(land['id'],land['footprint'],land['z'],'grass')
    for road in cfg['roads']:
        footway_width=road.get('footway_width',1.6)
        for i,(a,b) in enumerate(zip(road['points'],road['points'][1:])):
            line(road['id']+f'_{i}',a,b,road['width'],'asphalt')
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            nx,ny=-dy/length,dx/length
            for side in (-1,1):
                shift=side*(road['width']/2+footway_width/2)
                line(road['id']+f'_walk_{i}_{side}',
                     (a[0]+nx*shift,a[1]+ny*shift,a[2]+.12),
                     (b[0]+nx*shift,b[1]+ny*shift,b[2]+.12),footway_width,'paving')
    r=cfg['roundabout'];x,y,z=r['centre']
    # Annular carriageway keeps the island exposed and avoids layered disks.
    for i in range(48):
        a,b=i*math.tau/48,(i+1)*math.tau/48
        polygon(f'roundabout_{i}',[(x+radius*math.cos(t),y+radius*math.sin(t))
                for radius,t in ((r['inner_radius'],a),(r['outer_radius'],a),(r['outer_radius'],b),(r['inner_radius'],b))],z,'asphalt')
    polygon('roundabout_island',[(x+r['inner_radius']*math.cos(i*math.tau/48),y+r['inner_radius']*math.sin(i*math.tau/48)) for i in range(48)],z+.18,'grass')
    for item in cfg['buildings']:
        name=item['id'];p=item['footprint'];z=item['base_z'];h=item['height']
        polygon(name+'_mass',p,z,'residential_grey' if item['style']=='silver' else 'white',h)
        # Roof is the same polygon, 15 cm above the body, with a visible fascia.
        polygon(name+'_roof',p,z+h+.015,'dark',.18)
        # Opaque blue window bands follow every actual polygon edge.
        for k,(a,b) in enumerate(zip(p,p[1:]+p[:1])):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            nx,ny=dy/length,-dx/length
            for floor in range(max(1,int(h//3.6))):
                zz=z+2+floor*3.6
                if zz+1.15>=z+h:continue
                start=(a[0]+nx*.045,a[1]+ny*.045,zz+1.15)
                end=(b[0]+nx*.045,b[1]+ny*.045,zz+1.15)
                line(name+f'_windows_{k}_{floor}',start,end,.045,'fbk_window',1.15)
            for j in range(1,math.ceil(length/3)):
                t=j/math.ceil(length/3);xx=a[0]+dx*t+nx*.08;yy=a[1]+dy*t+ny*.08
                box(name+f'_panel_{k}_{j}',(xx-.035,yy-.035,z+.1),(xx+.035,yy+.035,z+h-.1),'fence')
    # Rolled metal roof lip on the photographed west face of the northern FBK.
    for i in range(10):
        a,b=i*math.pi/20,(i+1)*math.pi/20
        polygon_points=[(101-2*math.sin(a),-8),(101-2*math.sin(b),-8),
                        (101-2*math.sin(b),65),(101-2*math.sin(a),65)]
        vertices=[(xx,yy,20.195+1.5*(math.cos(a if k in (0,3) else b)-1)) for k,(xx,yy) in enumerate(polygon_points)]
        meshes.append(dict(name=f'exterior_edges_fbk_rolled_eave_{i}',vertices=vertices,
                           faces=[(0,1,2),(0,2,3)],material='exterior_fence'))
    for label in ('hedge','blue_fence'):
        item=cfg[label]
        for k,(a,b) in enumerate(zip(item['points'],item['points'][1:])):
            line(label+f'_stone_{k}',(a[0],a[1],a[2]+.85),(b[0],b[1],b[2]+.85),.5,'stone',.85)
            if label=='hedge':
                line('hedge_crown_'+str(k),(a[0],a[1],a[2]+.85+item['height']),
                     (b[0],b[1],b[2]+.85+item['height']),item['width'],'tree',item['height'])
            else:
                count=math.ceil(math.dist(a[:2],b[:2])/.65)
                for j in range(count+1):
                    t=j/count;xx,yy,zz=[a[q]+(b[q]-a[q])*t for q in range(3)]
                    box(f'blue_fence_post_{k}_{j}',(xx-.03,yy-.03,zz+.85),(xx+.03,yy+.03,zz+.85+item['height']),'fbk_blue')
                line(f'blue_fence_rail_{k}',(a[0],a[1],a[2]+1.3),(b[0],b[1],b[2]+1.3),.06,'fbk_blue',.06)
    for i,(x,y,h) in enumerate(cfg['village_houses']):
        box(f'village_{i}',(x-6,y-7,4),(x+6,y+7,4+h),'white')
        # Simple pitched roofs keep the outer silhouette residential.
        vv=[(x-6.6,y-7.6,4+h),(x+6.6,y-7.6,4+h),(x+6.6,y+7.6,4+h),(x-6.6,y+7.6,4+h),(x,y-7.6,7+h),(x,y+7.6,7+h)]
        meshes.append(dict(name=f'exterior_edges_village_roof_{i}',vertices=vv,
                           faces=[(0,1,4),(3,5,2),(0,4,5),(0,5,3),(4,1,2),(4,2,5)],material='exterior_orange'))
    for row,entry in enumerate(cfg['tree_rows']):
        for i in range(entry['count']):
            t=i/(entry['count']-1);x,y=[entry['start'][k]+(entry['end'][k]-entry['start'][k])*t for k in range(2)]
            z=entry['z'];h=entry['height']*(.9+.1*math.sin(i*2.3+row));radius=h*.28
            # Keep trunks and crowns clear where the new straight road crosses
            # an existing scenery tree belt.
            blocked=False
            for road in cfg['roads']:
                if not road.get('clear_vegetation'):continue
                for a,b in zip(road['points'],road['points'][1:]):
                    dx,dy=b[0]-a[0],b[1]-a[1]
                    f=min(1,max(0,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
                    distance=math.hypot(x-a[0]-f*dx,y-a[1]-f*dy)
                    if distance<road['width']/2+road.get('footway_width',1.6)+radius:blocked=True
            if blocked:continue
            box(f'tree_{row}_{i}_trunk',(x-.15,y-.15,z),(x+.15,y+.15,z+h*.55),'trunk')
            for tier in range(3):
                rr=radius*(1-tier*.24);zz=z+h*(.38+tier*.18)
                p=[(x+rr*math.cos(k*math.tau/8),y+rr*math.sin(k*math.tau/8)) for k in range(8)]
                polygon(f'tree_{row}_{i}_crown_{tier}',p,zz,'tree',h*.23)
    paths=['config/povo_edges.json','tools/povo_edges.py','tools/povo_exterior_materials.py',cfg['aerial'],cfg['aerial_manifest']]
    photos=[]
    for photo in cfg['photos']:
        path=(Path(cfg['photo_directory'])/photo['file']).as_posix();paths.append(path)
        photos.append(dict(photo,path=path,sha256=hashlib.sha256((root/path).read_bytes()).hexdigest()))
    hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
    return meshes,dict(config=cfg,photos=photos,input_hashes=hashes,visual_meshes=len(meshes),
                       collision_meshes=0,status=cfg['status'])


def extend(root, levels):
    """Append only render meshes, leaving gameplay collision and bounds intact."""
    path=root/'config/povo_edges.json'
    if not path.exists() or not json.loads(path.read_text()).get('enabled'):return
    exterior=levels[0].get('exterior')
    if exterior is None:return
    meshes,metadata=build(root)
    exterior['meshes'].extend(meshes)
    exterior['edges']=metadata
    exterior['input_hashes'].update(metadata['input_hashes'])
