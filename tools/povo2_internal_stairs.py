"""Reception stair correction from the user's 28 October walkthrough/sketches.

Counts and connectivity are confirmed. Metric registration and elevations are
still estimates; retain the bridge and the accepted -1 corridor interface.
"""
import json
from pathlib import Path

try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing


def extend(boxes, levels, root=None):
    root=Path(root) if root is not None else Path(__file__).resolve().parents[1]
    dimensions=json.loads((root/'config/povo2_internal_dimensions.json').read_text())
    measured=dimensions['implementation']
    door_x=measured['stair_door_east']
    vestibule_west=measured['vestibule_parking_end_east']
    vestibule_front=measured['vestibule_front_north']
    link = levels[1]['connection']; spec = link['povo2']
    old = link['stair']; a, b, c, d = old['bounds']
    dx = a - 11
    def point(p):
        return [p[0] + dx, p[1], p[2]]
    # Remove the obsolete two-module stack, including its physical rail clips.
    obsolete = ('academic_first_link_p2_stair_', 'p2_extended_',
                'p2_ground_core_slab', 'p2_basement_core_slab', 'p2_parking_core_',
                'p2_basement_core_old_door_infill')
    result = [box for box in boxes if not box[0].startswith(obsolete)]
    # Reverse the parking wing about the vestibule centreline: the approach
    # must continue forward (up in the exit-facing review), not behind the core.
    parking_level=next(l for l in spec['levels'] if l['floor']==-2)
    reflection=32.1
    pa,pb,pc,pd=spec['parking']['bounds']
    target=measured['parking_bounds']
    east_shift=target[2]+dx-pc
    north_shift=target[1]-(reflection-pd)
    result=[(n,(lo[0]+east_shift,reflection-hi[1]+north_shift,lo[2]),
               (hi[0]+east_shift,reflection-lo[1]+north_shift,hi[2]),m)
            if n.startswith('p2_parking_') else (n,lo,hi,m) for n,lo,hi,m in result]
    for station in parking_level['audit_stations']:
        station['point']=[station['point'][0]+east_shift,reflection-station['point'][1]+north_shift]
    spec['parking']['bounds']=[pa+east_shift,reflection-pd+north_shift,pc+east_shift,reflection-pb+north_shift]
    spec['parking']['cars']=[[x+east_shift,reflection-y+north_shift,m] for x,y,m in spec['parking']['cars']]
    # The exterior pass previously removed its garage surfaces where the old
    # interior parking supplied them. Restore that vacated overlap after moving
    # the lobe, rather than leaving holes in the independent larger garage.
    if levels[0].get('exterior'):
        garage=json.loads((root/'config/povo_exterior.json').read_text())['covered_parking']
        ga,gb,gc,gd=garage['bounds'];gz=garage['z'];roof=garage['ceiling_z'];th=garage['slab_thickness']
        x,y,u,v=max(pa,ga),max(pb,gb),min(pc,gc),min(pd,gd)
        if x<u and y<v:
            result += [
                ('exterior_garage_relocated_infill_floor',(x,y,gz-th),(u,v,gz),'floor_p2_asphalt'),
                ('exterior_garage_relocated_infill_roof',(x,y,roof),(u,v,roof+th),'wall')]
            if pc>=gc and pa<gc:
                result.append(('exterior_garage_relocated_infill_east',(gc-.22,y,gz),(gc,v,roof),'wall'))
            if pb<=gb and pd>gb:
                result.append(('exterior_garage_relocated_infill_south',(x,gb,gz),(u,gb+.22,roof),'wall'))
    # Excavate the new well, including old slabs, ceilings and internal trim.
    # The accepted -1 circulation south of y=18 stays in its existing frame.
    hole = ((a+.11, 18.001, -3.21), (c-.11, d-.11, link['floor_local_metres']+3.3))
    result = [p for box in result for p in subtract_box(box, hole)]
    preserved_rails = [r for r in spec['stairs'].get('rails',[])
                       if not r['name'].startswith(('p2_extended_', 'academic_first_link_p2_stair_'))]
    rails = []
    def add(n, lo, hi, mat='wall'):
        lo, hi = point(lo), point(hi)
        if any(x >= y for x, y in zip(lo, hi)):
            raise ValueError(n)
        result.append((n, tuple(lo), tuple(hi), mat))
    def slab(n, r, z, mat='floor_p2_tile'):
        x,y,u,v = r; add(n, (x,y,z-.22), (u,v,z), mat)
    def cut(lo, hi, materials=None):
        nonlocal result
        h = (point(lo), point(hi))
        result = [p for box in result for p in
                  (subtract_box(box,h) if materials is None or box[3] in materials else [box])]
    def rail(n, p, q):
        railing(lambda n,lo,hi,m: result.append((n,tuple(lo),tuple(hi),m)),
                rails, n, point(p), point(q))
    floor_z = {-2:-3.2, -1:.4, 0:4., 1:link['floor_local_metres']}
    # Retain the original -1 approach plate south of the replaced well.
    slab('p2_basement_retained_approach',(11.11,14.1,20.39,18),.4)
    # A continuous east landing connects every flight to the existing doors.
    shaft = ((11.11,18.25), (18.2,25.65))
    for floor,z in floor_z.items():
        prefix = 'p2_parking' if floor == -2 else 'p2_basement' if floor == -1 else 'p2_internal'
        slab(prefix+f'_new_core_floor_{floor}', (11.11,18,20.39,25.89), z)
        if floor != -2:
            cut((*shaft[0],z-.25), (*shaft[1],z+.01), ('floor_p2_tile','floor_p2_asphalt','floor_circulation'))
        wall_top=floor_z.get(floor+1,z+3.35)
        for side,lo,hi in (
            ('west',(10.9,18,z),(11.1,26,wall_top)),
            ('east',(20.4,18,z),(20.6,26,wall_top)),
            ('north',(11,25.9,z),(20.5,26.1,wall_top)),
            ('south',(11,17.9,z),(20.5,18.1,wall_top))):
            add(f'p2_internal_shell_{floor}_{side}',lo,hi)
    for floor in (-1,0,1):
        rail(f'p2_internal_landing_guard_{floor}',(18.28,20.5,floor_z[floor]),
             (18.28,23.2,floor_z[floor]))
    upper_mid=(floor_z[0]+floor_z[1])/2
    rail('p2_internal_upper_turn_guard',(14.25,20.5,upper_mid),(14.25,23.2,upper_mid))
    routes=[]; flights=[]
    for lower,counts in ((0,(13,13)),(-1,(10,10,10)),(-2,(10,10,10))):
        upper=lower+1; top=floor_z[upper]; bottom=floor_z[lower]
        rise=(top-bottom)/sum(counts); prefix=f'p2_internal_{lower}'
        path=[point((19.2,22,top)),point((19.2,19.35,top))]
        if lower == 0:
            segments=[((18.2,19.35),(14.3,19.35),2.),
                      ((14.3,24.35),(18.2,24.35),2.)]
            landings=[(11.11,18.35,14.3,25.35)]
        else:
            segments=[((18.2,19.35),(15.2,19.35),2.),
                      ((13.15,20.35),(13.15,23.35),2.),
                      ((15.2,24.35),(18.2,24.35),2.)]
            landings=[(12.15,18.35,15.2,20.35),(12.15,23.35,15.2,25.35)]
        h=top
        for j,((start,end,width),count) in enumerate(zip(segments,counts)):
            axis=0 if start[0]!=end[0] else 1; cross=1-axis
            step=[(end[k]-start[k])/count for k in range(2)]
            for i in range(count):
                p=[start[k]+step[k]*i for k in range(2)]
                q=[p[k]+step[k] for k in range(2)]
                lo=[min(p[k],q[k]) for k in range(2)]
                hi=[max(p[k],q[k]) for k in range(2)]
                lo[cross]-=width/2;hi[cross]+=width/2
                z=h-rise*(i+1)
                add(f'{prefix}_flight{j+1}_step_{i}',(*lo,z-.22),(*hi,z),'floor_p2_tile')
                path.append(point(((p[0]+q[0])/2,(p[1]+q[1])/2,z)))
                flights.append(dict(lower_floor=lower,flight=j+1,step=i,rise=rise,top=z))
            # Inner-edge rails leave both end landings unobstructed.
            offset=[0,0];offset[cross]=width/2 if j==0 else -width/2
            rail(f'{prefix}_rail{j+1}',
                 (start[0]+offset[0],start[1]+offset[1],h),
                 (end[0]+offset[0],end[1]+offset[1],h-rise*count))
            h-=rise*count
            if j<len(landings):
                slab(f'{prefix}_turn{j+1}',landings[j],h)
                nxt=segments[j+1][0]
                if lower==0:
                    path.extend([point((13.15,19.35,h)),point((13.15,24.35,h))])
                else:
                    path.extend([point((13.15,end[1],h)),point((13.15,nxt[1],h))])
        path.extend([point((19.2,24.35,bottom)),point((19.2,22,bottom))])
        routes.append(dict(lower_floor=lower,points=path,flight_counts=list(counts),rise=rise))
    # Preserve the accepted -1 portal. -2 is on the same south-facing wall,
    # offset west, and opens into a separate vestibule rather than parking.
    portals=[]
    for floor,x,y,wall in ((1,20.5,20,'east'),(0,20.5,22,'east'),
                           (-1,19.2,18,'south'),(-2,door_x,18,'south')):
        z=floor_z[floor]
        if wall=='east':cut((x-.3,y-.825,z-.01),(x+.3,y+.825,z+2.25))
        else:cut((x-.825,y-.3,z-.01),(x+.825,y+.3,z+2.25))
        portals.append(dict(floor=floor,centre=point((x,y,z)),side='v_max' if wall=='east' else 'u_min'))
        # Door leaves remain open along the travel direction.
        for s in (-1,1):
            if floor==-1:continue  # Keep the accepted -1 leaves and panic bars.
            if wall=='east':lo=(x+.05,y+s*.825-.025,z+.02);hi=(x+.85,y+s*.825+.025,z+2.18)
            else:
                near,far=(y+.05,y+.85) if floor==-1 else (y-.85,y-.05)
                lo=(x+s*.825-.025,near,z+.02);hi=(x+s*.825+.025,far,z+2.18)
            add(f'p2_internal_door_{floor}_{s}',lo,hi,'door_black')
    # Bottom landing spans the whole well; connect its shifted portal.
    slab('p2_parking_south_landing',(14.3,18,20.39,19.35),-3.2)
    z=-3.2
    areas={
        'vestibule':(vestibule_west,vestibule_front,20.5,18),
        'right_branch':(8.5,vestibule_front,vestibule_west,18),
        'right_turn':(8.5,11.3,10.8,16.05),
        'office_corridor':(20.5,12.5,24,23.5),
        'garden_corridor':(24,12.5,34.5,14.5),
    }
    # Remove conflicting old parking surfaces/walls along the new corridors.
    for key in ('office_corridor','garden_corridor','right_turn'):
        x,y,u,v=areas[key]
        cut((x+.01,y+.01,z+.01),(u-.01,v-.01,z+2.3))
    for name,r in areas.items():
        slab('p2_parking_'+name,r,z)
        slab('p2_parking_'+name+'_ceiling',r,z+3.1,'ceiling_panel')
    walls=[
        ('vestibule_front',(10.8,vestibule_front-.1),(20.5,vestibule_front)),
        ('parking_back',(8.4,18),(vestibule_west,18.1)),
        ('parking_west',(8.4,11.3),(8.5,18)),
        ('parking_east',(10.8,11.3),(10.9,vestibule_front)),
        ('junction_west',(20.4,12.5),(20.5,23.6)),
        # This is the wall directly ahead after the left vestibule door.
        ('junction_facing_wall',(24,14.5),(24.1,23.6)),
        ('office_end',(20.5,23.5),(24,23.6)),
        ('garden_south',(20.5,12.4),(34.5,12.5)),
        ('garden_north',(24,14.5),(34.5,14.6)),
    ]
    for name,lo,hi in walls:
        add('p2_parking_'+name,(*lo,z),(*hi,z+3.1))
    # Open the reflected parking shell where the forward approach joins it.
    cut((8.6,12.35,z-.01),(10.7,12.85,z+2.25))
    for name,x in (('parking',vestibule_west),('offices',20.5)):
        add('p2_parking_'+name+'_partition',(x-.08,vestibule_front,z),(x+.08,18,z+3.1))
        cut((x-.22,15.2,z-.01),(x+.22,16.9,z+2.25))
        slab('p2_parking_'+name+'_threshold',(x-.3,15.2,x+.3,16.9),z)
        for i,y in enumerate((15.2,16.9)):
            add(f'p2_parking_{name}_door_{i}',(x+.12,y-.025,z+.02),(x+.92,y+.025,z+2.18),'door_black')
    # Other offices are to the left at the T. Unsurveyed interiors stay closed.
    for i,y in enumerate((20,22)):
        add(f'p2_parking_office_closed_door_{i}',(23.96,y-.5,z+.02),
            (24,y+.5,z+2.15),'door_closed')
    # Right at the T, then left along the garden corridor to its exit door.
    add('p2_parking_garden_partition',(34.42,12.5,z),(34.58,14.5,z+3.1))
    cut((34.28,12.65,z-.01),(34.8,14.35,z+2.25))
    slab('p2_parking_garden_threshold',(34.2,12.65,34.8,14.35),z)
    for i,y in enumerate((12.65,14.35)):
        add(f'p2_parking_garden_door_{i}',(34.62,y-.025,z+.02),(35.42,y+.025,z+2.18),'door_black')
    spec['stairs'].update(portals=[next(p for p in portals if p['floor']==f) for f in (0,-1,-2)],
        path=[r for r in routes if r['lower_floor']<0],flights=flights,rails=preserved_rails+rails,
        flight_width=2.,tread=.3,well_bounds=[a,18,c,d],
        flight_counts={'0':[13,13],'-1':[10,10,10],'-2':[10,10,10]},
        metric_status='Estimated footprint/elevations; confirmed counts and topology')
    spec['stairs'].pop('risers_per_storey',None)
    old.update(path=routes[0]['points'],prototype_path=routes[0]['points'],rails=[],
               risers=26,modules=1,module_height=floor_z[1]-floor_z[0],
               rise=routes[0]['rise'],tread=.3,width=2.,portals=portals[:2],
               middle=point((13.15,22,upper_mid)),
               shaft=[point((11.11,18.25,4)),point((18.2,25.65,4))])
    for station in link['audit_stations']:
        if station['id']=='stair_upper_inside':station['point']=point((19.2,20,floor_z[1]))[:2]
    spec['parking']['vestibule']=[vestibule_west+dx,vestibule_front,20.5+dx,18]
    spec['parking']['dimensional_inference']=dimensions
    spec['parking']['branches']={'right':'parking_forward','left':{'left':'offices','right_then_left':'garden'}}
    spec['parking']['junction_wall']=[24+dx,14.5,24.1+dx,23.6]
    spec['parking']['routes']=[dict(points=[point(p) for p in pts]) for pts in [
        [(19.2,22,z),(19.2,18.6,z),(door_x,18.6,z),(door_x,16.05,z)],
        [(door_x,16.05,z),(9.65,16.05,z),(9.65,11.3,z)],
        [(door_x,16.05,z),(22.5,16.05,z),(22.5,13.5,z),(35.3,13.5,z)],
        [(door_x,16.05,z),(22.5,16.05,z),(22.5,22.5,z)]]]
    parking=next(l for l in spec['levels'] if l['floor']==-2)
    parking['audit_stations']=[s for s in parking['audit_stations'] if s['id'] not in ('core_door','core_landing','stair_approach')]
    parking['audit_stations'] += [dict(id=n,point=[x+dx,y]) for n,x,y in
        [('core_landing',19.2,22),('core_door',door_x,17),('vestibule',door_x,16.05),
         ('parking_branch',12,16.05),('office_branch',22.5,22.5),('garden_door',34,13.5),('junction',22.5,16.05)]]
    return result
