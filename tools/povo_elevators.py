"""Photo-guided paired lifts, fitted to the user-reviewed corner/core locations.

Coordinates are final registered campus metres. Source geometry includes parked
cars for review; export replaces those exact boxes with native moving entities.
No ladders, teleports, timed arrival guesses or disconnected floor copies.
"""
import copy
import json
from pathlib import Path
from .povo_room_fitout import subtract_box

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'config/povo_elevators.json'
PREFIX = 'materials/trento/povo/campus/'


def overlap(lo, hi, a, b):
    return all(min(hi[i], b[i])-max(lo[i], a[i]) > 1e-7 for i in range(3))


def apply(boxes, levels, root=ROOT):
    cfg = json.loads((root/CONFIG).read_text())
    if levels[0].get('elevator_banks'):
        raise ValueError('Elevator pass must run exactly once after registration')
    result = list(boxes)
    cuts = []
    removed = []
    def carve(lo, hi):
        nonlocal result
        cuts.append((lo,hi))
        removed.extend(n for n,a,b,m in result if overlap(a,b,lo,hi))
        result = [p for item in result for p in subtract_box(item,(lo,hi))]
    def add(name, lo, hi, mat='wall'):
        if any(a >= b for a,b in zip(lo,hi)):
            raise ValueError((name,lo,hi))
        result.append((name,tuple(lo),tuple(hi),mat))

    p2 = next(l['connection']['povo2'] for l in levels if 'connection' in l)
    lobby = cfg['povo2_lobby']; a,b,c,d = lobby['bounds'];z=lobby['z'];h=lobby['ceiling_z']
    # Replace D1 and the east wall of C5 only within the agreed extension.
    # It includes the obsolete concrete apron at z2.5..2.75.
    carve((a+.02,b-.01,z-.24),(c+.02,d+.12,h+.08))
    # Overlap the excavation margin: even a thin unsupported seam disconnects
    # the conservative standing-hull audit across the entire corridor.
    add('p2_lifts_lobby_floor',(a,b-.02,z-.22),(c,d,z),'floor_p2_tile')
    add('p2_lifts_lobby_ceiling',(a,b,h-.07),(c,d,h),'ceiling_panel')
    # New space east of the old C5 wall needs an enclosed south side.
    add('p2_lifts_lobby_south',(23.1,b-.1,z),(c,b,h))
    # The existing stair wall ends at N34.8; enclose the extension beyond it.
    add('p2_lifts_lobby_west_return',(a-.1,34.8,z),(a+.02,d,h))
    dx,dy,_=lobby['d1_centre'];half=lobby['d1_width']/2
    add('p2_lifts_d1_west',(a,dy-.08,z),(dx-half,dy+.08,h))
    add('p2_lifts_d1_east',(dx+half,dy-.08,z),(c,dy+.08,h))
    add('p2_lifts_d1_header',(dx-half,dy-.08,z+2.2),(dx+half,dy+.08,h))
    for i,(u,v) in enumerate(((dx-half,dx-.006),(dx+.006,dx+half))):
        add(f'p2_lifts_d1_locked_leaf_{i}',(u,dy-.04,z),(v,dy+.04,z+2.2),'door_black')
    # Retire the unverified D2 doorway/stub absorbed by the larger bank.
    # The remaining restricted corridor is still sealed, never opened to play.
    carve((33.14,26.65,z-.24),(35.9,35.12,h+.08))
    add('p2_lifts_restricted_corridor_cap',(33.14,35.02,z),(35.9,35.18,h))
    p2['minus1_corrections']['retired_lower_junction_door']=p2['minus1_corrections'].pop('lower_junction_door')
    p2['minus1_corrections']['c5_north_junction_door'].update(centre=lobby['d1_centre'])
    p2['drawio_entrance']['areas']['c5_lift_extension']=lobby['bounds']
    p2['drawio_entrance']['areas']['restricted']=[a,d,c,d+.5]
    p2['lift_revision']=dict(lobby=copy.deepcopy(lobby),restricted_corridor_cap_north=35.1,
        status='10 November user revision of the approved basement; D1 moved, D2 stub retired and sealed')

    banks=[]
    for spec in cfg['banks']:
        bank=copy.deepcopy(spec);bank.update(cars=[],lights=[],call_panels=[])
        a,b,c,d=bank['bounds'];front=c if bank['front']=='east' else a
        inward=-1 if bank['front']=='east' else 1; depth=c-a
        zs=[s['z'] for s in bank['stops']];bottom=min(zs);top=max(zs)+2.9
        # Entire vertical shaft including old slabs, fittings and concrete.
        carve((a-.01,b-.01,bottom-.4),(c+.01,d+.01,top+.01))
        # Door approaches only remove a thin lip of the existing corridor wall.
        for stop in bank['stops']:
            carve((front-.24,b+.05,stop['z']+.01),(front+.24,d-.05,stop['z']+2.3))
        def local_box(name,lo,hi,mat='wall',dynamic=None):
            e0,e1=sorted((front+inward*lo[0],front+inward*hi[0]))
            box=(name,(e0,lo[1],lo[2]),(e1,hi[1],hi[2]),mat)
            if dynamic is not None:dynamic.append(box)
            else:add(*box)
            return box
        pre='lift_'+bank['id']
        local_box(pre+'_shaft_back',(depth-.15,b,bottom-.35),(depth,d,top))
        local_box(pre+'_shaft_south',(0,b,bottom-.35),(depth,b+.15,top))
        local_box(pre+'_shaft_north',(0,d-.15,bottom-.35),(depth,d,top))
        local_box(pre+'_shaft_divider',(0,(b+d)/2-.075,bottom-.35),(depth,(b+d)/2+.075,top))
        local_box(pre+'_pit',(0,b,bottom-.4),(depth,d,bottom-.3),'floor_circulation')
        local_box(pre+'_roof',(0,b,top),(depth,d,top+.15),'ceiling_panel')
        for car_index in range(2):
            vb=b+(d-b)*car_index/2;ve=b+(d-b)*(car_index+1)/2;mid=(vb+ve)/2
            w=bank['door_width'];dh=bank['door_height'];cid=f'{pre}_car{car_index+1}'
            car=dict(id=cid,stops=copy.deepcopy(bank['stops']),parts=[],gates=[],buttons=[],
                     origin=[front+inward*(depth/2),mid,bottom],front=bank['front'])
            # Parked complete moving cabin: no static floor through the shaft.
            def cab(n,lo,hi,mat='lift_dark_steel'):
                return local_box('lift_dynamic_'+cid+'_'+n,lo,hi,mat,car['parts'])
            cab('floor',(.28,vb+.23,bottom-.14),(depth-.23,ve-.23,bottom),'lift_rubber')
            cab('back',(depth-.29,vb+.23,bottom),(depth-.23,ve-.23,bottom+2.45))
            cab('south',(.45,vb+.23,bottom),(depth-.23,vb+.29,bottom+2.45))
            cab('north',(.45,ve-.29,bottom),(depth-.23,ve-.23,bottom+2.45))
            cab('ceiling',(.28,vb+.23,bottom+2.45),(depth-.23,ve-.23,bottom+2.52),'lift_light')
            cab('front_south',(.28,vb+.23,bottom),(.34,mid-w/2,bottom+2.45),'lift_steel')
            cab('front_north',(.28,mid+w/2,bottom),(.34,ve-.23,bottom+2.45),'lift_steel')
            cab('front_header',(.28,mid-w/2,bottom+dh),(.34,mid+w/2,bottom+2.45),'lift_steel')
            cab('handrail_back',(depth-.42,vb+.4,bottom+.95),(depth-.37,ve-.4,bottom+1.),'lift_steel')
            # Two car leaves parented to the train and two landing leaves/stop.
            for stop_index,stop in enumerate(bank['stops']):
                z=stop['z'];sp=f'{cid}_stop{stop_index}'
                local_box(sp+'_front_south',(0,vb+.15,z),(.15,mid-w/2,z+2.85))
                local_box(sp+'_front_north',(0,mid+w/2,z),(.15,ve-.15,z+2.85))
                local_box(sp+'_header',(0,mid-w/2,z+dh),(.15,mid+w/2,z+2.85))
                for j,yy in enumerate((mid-w/2-.075,mid+w/2)):
                    local_box(sp+f'_steel_jamb{j}',(-.025,yy,z),(.16,yy+.075,z+dh+.08),'lift_steel')
                local_box(sp+'_steel_head',(-.025,mid-w/2-.075,z+dh),(.26,mid+w/2+.075,z+dh+.08),'lift_steel')
                local_box(sp+'_sill',(-.17,mid-w/2,z-.08),(.26,mid+w/2,z),'lift_steel')
                # Cap the space above this stop's portal up to the next level.
                ceiling=zs[stop_index+1] if stop_index+1<len(zs) else top
                if ceiling>z+2.85:local_box(sp+'_upper_wall',(0,vb+.15,z+2.85),(.15,ve-.15,ceiling))
                bank['lights'].append([front-inward*.6,mid,z+2.6])
                # Shared call-panel strip at centre pier, one button per car.
                yy=(b+d)/2 + (-.14 if car_index==0 else .14)
                btn=local_box('lift_dynamic_'+sp+'_call',(-.10,yy-.055,z+1.02),(-.045,yy+.055,z+1.13),'lift_steel',[])
                car['buttons'].append(dict(name=sp+'_call',box=btn,stop=stop_index,parent=None))
                car.setdefault('indicators',[]).append(dict(name=sp+'_indicator',origin=[front-inward*.111,yy,z+1.42]))
                for leaf in range(2):
                    v0,v1=(mid-w/2,mid) if leaf==0 else (mid,mid+w/2)
                    gatebox=local_box('lift_dynamic_'+sp+f'_gate{leaf}',(.17,v0+.004,z+.015),(.215,v1-.004,z+dh-.01),'lift_steel',[])
                    car['gates'].append(dict(name=sp+f'_gate{leaf}',box=gatebox,stop=stop_index,parent=None,leaf=leaf))
            for leaf in range(2):
                v0,v1=(mid-w/2,mid) if leaf==0 else (mid,mid+w/2)
                box=local_box('lift_dynamic_'+cid+f'_cabin_gate{leaf}',(.35,v0+.004,bottom+.015),(.395,v1-.004,bottom+dh-.01),'lift_steel',[])
                car['gates'].append(dict(name=cid+f'_cabin_gate{leaf}',box=box,stop=None,parent=cid,leaf=leaf))
            for stop_index,stop in enumerate(bank['stops']):
                yy=mid+w/2+.14;zz=bottom+1.02+stop_index*.16
                box=local_box('lift_dynamic_'+cid+f'_inside_button{stop_index}',(.405,yy-.06,zz),(.44,yy+.06,zz+.11),'lift_steel',[])
                car['buttons'].append(dict(name=cid+f'_inside_button{stop_index}',box=box,stop=stop_index,parent=cid))
            bank['cars'].append(car)
            result.extend(car['parts']);result.extend(g['box'] for g in car['gates']);result.extend(x['box'] for x in car['buttons'])
        for stop in bank['stops']:
            z=stop['z'];mid=(b+d)/2
            local_box(pre+f'_panel_{stop["floor"]}',(-.04,mid-.29,z+.9),(-.005,mid+.29,z+1.65),'lift_steel')
            local_box(pre+f'_screen_{stop["floor"]}',(-.045,mid-.24,z+1.3),(-.04,mid+.24,z+1.57),'lift_display')
        banks.append(bank)
    # Record real bank footprints so spawns cannot be generated on moving cars.
    levels[0]['elevator_banks']=banks
    levels[0]['elevator_revision']=dict(config=CONFIG,removed_boxes=sorted(set(removed)))
    # Remove stale room functions where the Povo 1 corner pair now stands.
    p1=cfg['banks'][0]['bounds']
    for level in levels:
        for room in level['rooms']:
            if room['id'] in ('g_south_east','f_south_east'):
                old=list(room['footprint_local_metres']);old[2]=p1[0]
                room['footprint_local_metres']=old
                room['lift_corner_revision']='East portion replaced by paired lift shafts'
    # Clip exterior polygon meshes as well as boxes; bounds alone are not proof
    # of free space. Use the same solid-mesh subtraction as other campus cuts.
    from .solid_mesh import subtract as subtract_solid
    from .build_povo_campus import subtract_polygon_box
    ext=levels[0].get('exterior',{})
    for key in ('meshes','collision_meshes'):
        out=[]
        for mesh in ext.get(key,[]):
            vv=mesh['vertices'];lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)]
            holes=[h for h in cuts if overlap(lo,hi,*h)]
            if not holes:out.append(mesh);continue
            if key=='collision_meshes':
                pieces=[mesh]
                for hole in holes:pieces=[p for q in pieces for p in subtract_solid(q,hole)]
                out.extend(pieces)
            else:
                vertices=[];faces=[]
                for face in mesh['faces']:
                    polys=[[(tuple(vv[i]),(0,0)) for i in face]]
                    for hole in holes:polys=[p for q in polys for p in subtract_polygon_box(q,*hole)]
                    for poly in polys:
                        offset=len(vertices);vertices.extend(v for v,_ in poly)
                        faces.extend((offset,offset+i,offset+i+1) for i in range(1,len(poly)-1))
                if faces:out.append(dict(mesh,vertices=vertices,faces=faces))
        if key in ext:ext[key]=out
    return result


def static_boxes(boxes):
    """Native entity export owns all car, moving leaf and button geometry."""
    return [b for b in boxes if not b[0].startswith('lift_dynamic_')]
