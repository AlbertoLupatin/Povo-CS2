"""Deathmatch spawns spread over the whole playable campus.

Candidates come only from places the source audits already prove walkable:
the reachable standing-clearance grids of every storey (Povo 1, both wings,
the bridge, Povo 2 and its yard) and the supported outdoor walking routes.
Farthest-point sampling then spreads the chosen spawns across all of them.
"""
import math

try:
    from .audit_povo_interior import audit_level
    from .audit_povo_exterior_integrated import exterior_routes, route_points, standing
except ImportError:
    from audit_povo_interior import audit_level
    from audit_povo_exterior_integrated import exterior_routes, route_points, standing

WIDTH=.82;HEIGHT=1.85
# Leave a margin around the standing envelope so nobody spawns against a wall.
MARGIN=.3
SPACING=7.0
LIMIT=64
# Storeys stack 3.6 m apart; weight height so floors count as separate places.
VERTICAL_WEIGHT=3.0
EYE=1.4
# Between the two buildings, where the bridge crosses the street.
CENTRE=(18,-5)


def _aliased(physics,prefix,z,match):
    """Treat matching floors at this height as the storey's own support."""
    return [(prefix+'_alias_'+n,lo,hi,'floor_route') for n,lo,hi,m in physics
            if match(n,m) and abs(hi[2]-z)<.02]


def storeys(physics,levels):
    """(id, floor z, seed station) for every walkable storey of the campus."""
    result=[]
    link=next((l['connection'] for l in levels if 'connection' in l),{})
    for level in levels:
        seed=[22,-73.73] if level['id']=='academic_ground' else [13.95,-83.8]
        z=level['floor_elevation_metres']-370
        support=_aliased(physics,level['id'],z,lambda n,m:n.startswith('academic_first_link_')
                         and m.startswith('floor_')) if abs(z-link.get('floor_local_metres',-999))<.02 else []
        result.append((level['id'],z,seed,support))
    ground=link.get('ground')
    if ground:result.append((ground['id'],ground['floor_elevation_local'],ground['audit_stations'][0]['point'],[]))
    spec=link.get('povo2')
    if spec:
        for level in spec['levels']:
            z=level['z']
            support=_aliased(physics,level['id'],z,lambda n,m:n.startswith(('p2_','academic_first_link_p2'))
                             and m.startswith('floor_'))
            result.append((level['id'],z,level['audit_stations'][0]['point'],support))
        yard=spec.get('additions',{}).get('yard')
        if yard:
            support=_aliased(physics,'p2_yard',yard['z'],lambda n,m:n.startswith('p2_gardens_') and m.startswith('floor_'))
            result.append(('p2_yard',yard['z'],yard['audit_stations'][0]['point'],support))
    for level in levels[0].get('wings',{}).get('levels',[]):
        z=level['z'];building=level['building']
        support=_aliased(physics,level['id'],z,lambda n,m:(n.startswith(building+'_') and m.startswith('floor_'))
                         or n=='exterior_povo1_front_walk')
        result.append((level['id'],z,level['audit_stations'][0]['point'],support))
    return result


def interior_candidates(physics,levels,stride=1.0):
    """Reachable grid cells with room to spare, about one per square metre."""
    points=[]
    for storey,z,seed,support in storeys(physics,levels):
        report,free,visited=audit_level(physics+support,dict(id=storey,floor_elevation_local=z),
                                        [dict(id='seed',point=seed)],width=WIDTH,height=HEIGHT)
        nx,ny=report['grid_dimensions'];x0,y0=report['grid_bounds_local'][:2];cell=report['cell_metres']
        step=max(1,round(stride/cell));pad=math.ceil(MARGIN/cell)
        # The flood grid can include an opening with a floor on another storey.
        # Spawn feet must be supported at this storey's exact elevation.
        surfaces=[(lo,hi) for _,lo,hi,m in physics if m.startswith('floor_') and abs(hi[2]-z)<.02]
        for iy in range(pad,ny-pad,step):
            for ix in range(pad,nx-pad,step):
                if all(visited[(iy+dy)*nx+ix+dx] for dx in (-pad,0,pad) for dy in (-pad,0,pad)):
                    x,y=x0+(ix+.5)*cell,y0+(iy+.5)*cell
                    if any(lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] for lo,hi in surfaces):
                        points.append((storey,(x,y,z)))
    return points


def exterior_candidates(physics,meshes,step=2.0):
    """Supported, unobstructed points along the audited outdoor routes."""
    points=[]
    for name,path in exterior_routes().items():
        for x,y,z in route_points(path,step):
            foot,obstacles=standing(x,y,z,physics,meshes)
            if foot is None or obstacles:continue
            # The same envelope, widened by the margin, must also be clear.
            wide=[n for n,lo,hi,m in physics if lo[0]<x+.4+MARGIN and hi[0]>x-.4-MARGIN
                  and lo[1]<y+.4+MARGIN and hi[1]>y-.4-MARGIN and hi[2]>foot+.2 and lo[2]<foot+HEIGHT]
            if not wide:points.append(('exterior_'+name,(x,y,foot)))
    return points


def spread(candidates,*,limit=LIMIT,spacing=SPACING,start=None):
    """Farthest-point sampling: each pick is as far as possible from the others."""
    def gap(a,b):return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2+(VERTICAL_WEIGHT*(a[2]-b[2]))**2)
    if not candidates:return []
    first=min(range(len(candidates)),key=lambda i:math.dist(candidates[i][1][:2],start)) if start else 0
    chosen=[candidates[first]];nearest=[gap(p,chosen[0][1]) for _,p in candidates]
    while len(chosen)<limit:
        index=max(range(len(candidates)),key=nearest.__getitem__)
        if nearest[index]<spacing:break
        chosen.append(candidates[index])
        point=candidates[index][1]
        nearest=[min(d,gap(p,point)) for d,(_,p) in zip(nearest,candidates)]
    return chosen


def _ray_length(origin,direction,boxes,reach):
    best=reach
    for lo,hi in boxes:
        near,far=0.,best
        for k in range(3):
            if abs(direction[k])<1e-9:
                if not lo[k]<=origin[k]<=hi[k]:break
                continue
            a=(lo[k]-origin[k])/direction[k];b=(hi[k]-origin[k])/direction[k]
            if a>b:a,b=b,a
            near=max(near,a);far=min(far,b)
            if near>far:break
        else:best=min(best,near)
    return best


def facing(point,physics,reach=25.0,directions=16,centre=CENTRE):
    """Source yaw towards the longest clear sightline at eye height.

    Equally open directions (common outdoors) prefer facing the campus centre.
    """
    x,y,z=point;eye=(x,y,z+EYE)
    nearby=[(lo,hi) for _,lo,hi,_ in physics if lo[2]<eye[2]<hi[2]
            and lo[0]<x+reach and hi[0]>x-reach and lo[1]<y+reach and hi[1]>y-reach]
    inward=math.atan2(centre[0]-x,centre[1]-y)
    def score(i):
        angle=2*math.pi*i/directions
        length=_ray_length(eye,(math.sin(angle),math.cos(angle),0.),nearby,reach)
        return round(length,1),math.cos(angle-inward),angle
    *_,angle=max(map(score,range(directions)))
    dx,dy=math.sin(angle),math.cos(angle)
    # world() sends local north to -Source X and east to +Source Y.
    return round(math.degrees(math.atan2(dx,-dy))%360,1)


def deathmatch_spawns(physics,levels):
    ladders=[l for l in (levels[0].get('elevator',{}).get('ladder'),
                         next((q['connection'] for q in levels if 'connection' in q),{}).get('povo2',{}).get('lift',{}).get('ladder')) if l]
    meshes=levels[0].get('exterior',{}).get('collision_meshes',[])
    candidates=[(area,p) for area,p in interior_candidates(physics,levels)+exterior_candidates(physics,meshes)
                if not any(lo[0]-1.5<=p[0]<=hi[0]+1.5 and lo[1]-1.5<=p[1]<=hi[1]+1.5
                           and lo[2]-.5<=p[2]<=hi[2] for lo,hi in ladders)]
    chosen=spread(candidates,start=(22,-73.73))
    return [dict(id=f'dm_{i:02d}',area=area,point=[round(v,3) for v in p],yaw=facing(p,physics))
            for i,(area,p) in enumerate(chosen)]
