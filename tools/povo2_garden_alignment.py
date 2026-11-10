"""Align the exterior DOWN stair with the retained -1 corridor.

Only exterior pieces are replaced. The garden keeps its previous dimensions;
its near corner is anchored to the corridor end, with the lower landing at
half its length. Absolute facade/road registration still requires a survey.
"""
from .povo_room_fitout import subtract_box
from .build_povo2_west_offices import subtract_rect
from .povo_stairs import railing


def extend(boxes, levels):
    from .build_povo_campus import subtract_polygon_box
    p = levels[1]['connection']['povo2']
    ext = levels[0]['exterior']
    g = p['gardens']
    terrace = g['passage']
    old = g['garden']
    z, low = g['passage_z'], g['garden_z']
    a, b = terrace[2], terrace[1]
    c, d = a + old[2] - old[0], b + old[3] - old[1]
    middle = (a+c)/2
    # Preserve the terrace centreline and width: no turn at the upper landing.
    width = terrace[3]-terrace[1]
    y = b+width/2
    garden = [a,b,c,d]
    down = [a,b,middle,b+width]
    remove = ('p2_basement_drawio_down_', 'p2_basement_drawio_garden_',
              'p2_basement_drawio_drawio_down_',
              'p2_basement_drawio_drawio_garden_approach_',
              'p2_gardens_garden_', 'p2_gardens_retaining_',
              'p2_gardens_office_garden_approach',
              'p2_roadside_approach_', 'p2_roadside_garden_',
              'p2_roadside_stair_north', 'p2_roadside_landing_east')
    result = [q for q in boxes if not q[0].startswith(remove)]
    rail_remove = ('drawio_down_', 'drawio_garden_approach_',
                   'garden_guard_', 'p2_roadside_garden_',
                   'p2_roadside_stair_north', 'p2_roadside_landing_east')
    p['stairs']['rails'][:] = [r for r in p['stairs']['rails']
                              if not r['name'].startswith(rail_remove)]

    def add(name, lo, hi, material='exterior_concrete'):
        if any(v>=w for v,w in zip(lo,hi)):
            raise ValueError(name)
        result.append(('p2_aligned_garden_'+name,tuple(lo),tuple(hi),material))

    def plate(name, rect, height, material='floor_terrace'):
        x0,y0,x1,y1=rect
        add(name,(x0,y0,height-.22),(x1,y1,height),material)

    # Close the old exterior excavation except where the new garden overlaps.
    # Keep the original interior exit and replace only its outdoor connection.
    approach=[34.5,d,37.5,14.5]
    for i,r in enumerate(subtract_rect(old,garden)):
        for j,s in enumerate(subtract_rect(r,approach)):
            add(f'old_infill_{i}_{j}',(s[0],s[1],low-.22),(s[2],s[3],4.))
    holes=[((a,b,low-.23),(c,d,10.)),
           ((approach[0],d,low-.23),(approach[2],14.5,-.1))]
    for hole in holes:
        result=[part for q in result for part in
                (subtract_box(q,hole) if q[0].startswith(('exterior_', 'p2_roadside_',
                    'p2_gardens_', 'p2_basement_drawio_old_up_infill',
                    'p2_aligned_garden_old_infill')) else [q])]
    for key in ('meshes','collision_meshes'):
        clipped=[]
        for mesh in ext[key]:
            vv=mesh['vertices'];lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
            relevant=[h for h in holes if all(lo[i]<h[1][i] and hi[i]>h[0][i] for i in range(3))]
            if not relevant:
                clipped.append(mesh);continue
            vertices=[];faces=[]
            for face in mesh['faces']:
                polys=[[(tuple(vv[i]),(0,0)) for i in face]]
                for hole in relevant:
                    polys=[r for poly in polys for r in subtract_polygon_box(poly,*hole)]
                for poly in polys:
                    start=len(vertices);vertices.extend(v for v,_ in poly)
                    faces.extend((start,start+i,start+i+1) for i in range(1,len(poly)-1))
            if faces:clipped.append(dict(mesh,vertices=vertices,faces=faces,surface_clipped=True))
        ext[key]=clipped
    plate('floor',garden,low)
    plate('office_approach',approach,low)
    # Paved edge at the bottom of the stair; grass stays clear of the route.
    add('lawn',(a+3,b+3,low),(c-2,d-2,low+.025),'floor_yard_grass')
    count=20;landing=1.1;top_landing=.6;step=(middle-a-top_landing-landing)/count
    plate('upper_landing',[a,b,a+top_landing,b+width],z)
    route=[[a-.6,y,z],[a+top_landing/2,y,z]]
    rails=[]
    for i in range(count):
        x=a+top_landing+i*step+(landing if i>=10 else 0)
        h=z-(z-low)*(i+1)/count
        add('down_step_'+str(i),(x,b,h-.16),(x+step,b+width,h),'floor_grating')
        route.append([x+step/2,y,h])
        if i==9:
            plate('midlanding',[x+step,b,x+step+landing,b+width],h,'floor_grating')
            route.append([x+step+landing/2,y,h])
    route.append([middle+.6,y,low])
    for yy in (b,b+width):
        mid=a+top_landing+10*step
        for name,start,end in [('first',(a+top_landing,yy,z),(mid,yy,(z+low)/2)),
                               ('middle',(mid,yy,(z+low)/2),(mid+landing,yy,(z+low)/2)),
                               ('second',(mid+landing,yy,(z+low)/2),(middle,yy,low))]:
            railing(add,rails,f'down_{name}_{yy}',start,end)
    # Retaining walls live outside the footprint. Leave both access mouths open.
    add('wall_road',(a,b-.16,low-.22),(c,b,4.))
    add('wall_east',(c,b,low-.22),(c+.16,d,4.))
    add('wall_west',(a-.16,b+width,low-.22),(a,d,z))
    for x0,x1 in ((a,approach[0]),(approach[2],c)):
        add('wall_north_'+str(x0),(x0,d,low-.22),(x1,d+.16,4.))
    for x0 in (approach[0]-.16,approach[2]):
        add('approach_wall_'+str(x0),(x0,d,low-.22),(x0+.16,14.5,-.1))
    portal=((34.2,12.65,low-.01),(34.9,14.35,low+2.25))
    result=[part for q in result for part in
            (subtract_box(q,portal) if q[0].startswith('p2_aligned_garden_approach_wall_') else [q])]
    plate('approach_ceiling',approach,-.1,'ceiling_panel')
    for name,start,end in [('east',(c+.08,b,4.),(c+.08,d,4.)),
                           ('north',(a,d+.08,4.),(c,d+.08,4.))]:
        railing(add,rails,'guard_'+name,start,end)
    # Add the already prefixed rail names used by the rendering metadata.
    for r in rails:r['name']='p2_aligned_garden_'+r['name']
    p['stairs']['rails'].extend(rails)
    routes=dict(g['routes'])
    routes['passage']=[[22.,y,z],[a-.6,y,z]]
    routes['down']=route
    routes['garden']=[route[-1],[c-1,y,low],[c-1,d-1,low],[36.,d-1,low],[36.,13.5,low]]
    routes['office_exit']=[[34.8,13.5,low],[36.,13.5,low],[36.,d-1,low]]
    for path in p['basement_rebuild']['routes']:
        if path['id']=='minus2_garden_exit':
            path['points']=[*path['points'][:-1],[36.,13.5,low],[36.,d-1,low]]
    g.update(garden=garden,down_stair=down,down_landing=[middle,b,middle+1.2,b+width],routes=routes)
    p['additions']['yard'].update(bounds=garden,routes=routes,down_path=route,indoor_path=routes['passage'],
        audit_stations=[dict(id='garden_'+str(i),point=q[:2]) for i,q in enumerate(routes['garden'])],
        status='Straight corridor to garden-start upper landing; lower landing at garden midpoint')
    g['source']='Accepted exterior connection, 5 November 2026'
    g['excavations']=holes
    ext['roadside_closure']['garden_alignment']='Superseded locally by povo2_garden_alignment; road and footway retained'
    p['drawio_entrance']['areas']['down']=down
    ext['pavement_repairs']['garden_exclusions'].extend([[*lo[:2],*hi[:2]] for lo,hi in holes])
    p['garden_alignment']=dict(garden=garden,previous_garden=old,stair=down,
        source='Accepted corridor/garden connection, 5 November 2026',
        status='Corridor-anchored implementation; original garden dimensions retained, absolute registration provisional',
        preserve='All interior rooms, corridors and internal stair directions; existing UP stair to street')
    return result
