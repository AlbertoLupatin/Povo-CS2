#!/usr/bin/env python3
"""Build a separate photo-guided exterior OBJ, plan and west-facing room studies.

Only exports/povo_exterior is written. No map, installed addon or interior source
is changed. Pillow/numpy are needed only by the companion renderer.
"""
import hashlib
import json
import math
from pathlib import Path

try:
    from .build_povo_blockout import write_box
    from .build_povo_campus import build_geometry
    from .povo2_exterior_entrance import extend as add_double_entrance
    from .povo_exterior_materials import COLORS, OPACITY
    from .povo_room_fitout import subtract_box
except ImportError:
    from build_povo_blockout import write_box
    from build_povo_campus import build_geometry
    from povo2_exterior_entrance import extend as add_double_entrance
    from povo_exterior_materials import COLORS, OPACITY
    from povo_room_fitout import subtract_box

ROOT = Path(__file__).resolve().parents[1]
FACES = ((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
         (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7))


def strip(name, a, b, width, material, thickness=.16):
    """Closed, genuinely sloping strip, with shared exact end elevations."""
    dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
    if length <= 0 or width <= 0: raise ValueError('Degenerate strip')
    nx,ny=-dy/length*width/2,dx/length*width/2
    top=[(a[0]+nx,a[1]+ny,a[2]),(a[0]-nx,a[1]-ny,a[2]),
         (b[0]-nx,b[1]-ny,b[2]),(b[0]+nx,b[1]+ny,b[2])]
    # This order is counterclockwise when seen from above.
    vertices=[(x,y,z-thickness) for x,y,z in top]+top
    return dict(name=name,vertices=vertices,faces=FACES,material=material)


def build(root=ROOT, campus_geometry=None):
    cfg=json.loads((root/'config/povo_exterior.json').read_text())
    _settings,interior,live_boxes,levels,_stairs=campus_geometry or build_geometry(root,include_exterior=False)
    boxes=[];meshes=[]
    def box(name,lo,hi,mat):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError(name)
        boxes.append((name,tuple(lo),tuple(hi),mat))
    def slab(name,r,z,mat,t=.18):box(name,(r[0],r[1],z-t),(r[2],r[3],z),mat)
    def fence(name,a,b,z,height=1.7):
        meshes.append(strip(name+'_base',(*a,z+.45),(*b,z+.45),.18,'concrete',.45))
        length=math.dist(a,b);n=math.ceil(length/.45)
        for i in range(n+1):
            f=i/n;x=a[0]+(b[0]-a[0])*f;y=a[1]+(b[1]-a[1])*f
            box(name+f'_bar_{i}',(x-.025,y-.025,z+.45),(x+.025,y+.025,z+height),'fence')
        meshes.append(strip(name+'_top',(*a,z+height),(*b,z+height),.05,'fence',.05))
    def tree(name,x,y,z,h=7):
        box(name+'_trunk',(x-.16,y-.16,z),(x+.16,y+.16,z+h*.7),'trunk')
        box(name+'_crown',(x-1.5,y-1.5,z+h*.4),(x+1.5,y+1.5,z+h),'tree')
    def road_run(prefix,settings):
        for i,(a,b) in enumerate(zip(settings['points'],settings['points'][1:])):
            meshes.append(strip(f'{prefix}_{i}',a,b,settings['width'],'asphalt'))
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
            for side in (-1,1):
                shift=side*(settings['width']/2+settings['footway_width']/2)
                meshes.append(strip(f'{prefix}_footway_{i}_{side}',(a[0]+nx*shift,a[1]+ny*shift,a[2]+.12),
                                    (b[0]+nx*shift,b[1]+ny*shift,b[2]+.12),settings['footway_width'],'paving'))
                shift=side*(settings['width']/2-.12)
                meshes.append(strip(f'{prefix}_edge_{i}_{side}',(a[0]+nx*shift,a[1]+ny*shift,a[2]+.012),
                                    (b[0]+nx*shift,b[1]+ny*shift,b[2]+.012),.10,'marking',.008))
        for i,p in enumerate(settings['points'][1:-1]):
            n=16;v=[(p[0],p[1],p[2]+.002)]+[(p[0]+settings['width']/2*math.cos(k*2*math.pi/n),p[1]+settings['width']/2*math.sin(k*2*math.pi/n),p[2]+.002) for k in range(n)]
            meshes.append(dict(name=f'{prefix}_joint_{i}',vertices=v,faces=[(0,k+1,(k+1)%n+1) for k in range(n)],material='asphalt'))
    def glass_block(name,r,z,roof,panes=False):
        """Opaque study glazing on all faces, with visible frames and roof.

        With panes, each frame bay gets two separate glass panes (one per rail
        band) in front of an opaque core, so single panes can break in game.
        """
        a,b,c,d=r
        if not panes:box(name+'_mass',(a,b,z),(c,d,roof),'glass')
        else:
            # ponytail: opaque core until these interiors are modelled.
            box(name+'_core',(a+.35,b+.35,z),(c-.35,d-.35,roof),'dark')
            for lo_z,hi_z in ((z,z+2.2),(z+2.26,roof)):
                for x in (a,c):
                    for i in range(math.ceil((d-b)/2.7)):
                        y0,y1=b+i*2.7,min(d,b+(i+1)*2.7)
                        box(f'{name}_pane_x_{x}_{i}_{lo_z:g}',(x-.03,y0+.04,lo_z),(x+.03,y1-.04,hi_z),'glass')
                for y in (b,d):
                    for i in range(math.ceil((c-a)/2.7)):
                        x0,x1=a+i*2.7,min(c,a+(i+1)*2.7)
                        box(f'{name}_pane_y_{y}_{i}_{lo_z:g}',(x0+.04,y-.03,lo_z),(x1-.04,y+.03,hi_z),'glass')
        slab(name+'_roof',(a-.15,b-.15,c+.15,d+.15),roof+.15,'dark')
        for x in (a,c):
            for i in range(math.ceil((d-b)/2.7)+1):
                y=min(d,b+i*2.7)
                box(f'{name}_frame_x_{x}_{i}',(x-.06,y-.04,z),(x+.06,y+.04,roof),'fence')
            for zz in (z+.18,z+2.2,roof-.15):
                box(f'{name}_rail_x_{x}_{zz}',(x-.06,b,zz),(x+.06,d,zz+.06),'fence')
        for y in (b,d):
            for i in range(math.ceil((c-a)/2.7)+1):
                x=min(c,a+i*2.7)
                box(f'{name}_frame_y_{y}_{i}',(x-.04,y-.06,z),(x+.04,y+.06,roof),'fence')
            for zz in (z+.18,z+2.2,roof-.15):
                box(f'{name}_rail_y_{y}_{zz}',(a,y-.06,zz),(c,y+.06,zz+.06),'fence')
    # Grass apron is scenery, kept below road/parking surfaces.
    slab('west_grass',(-87,-109,-23,4),2.84,'grass')
    road=cfg['road'];points=road['points']
    for i,(a,b) in enumerate(zip(points,points[1:])):
        meshes.append(strip(f'road_{i}',a,b,road['width'],'asphalt'))
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
        for side in (-1,1):
            shift=side*(road['width']/2+road['footway_width']/2)
            aa=(a[0]+nx*shift,a[1]+ny*shift,a[2]+.12)
            bb=(b[0]+nx*shift,b[1]+ny*shift,b[2]+.12)
            meshes.append(strip(f'footway_{i}_{side}',aa,bb,road['footway_width'],'paving'))
            shift=side*(road['width']/2-.12)
            meshes.append(strip(f'road_edge_{i}_{side}',(a[0]+nx*shift,a[1]+ny*shift,a[2]+.012),
                                (b[0]+nx*shift,b[1]+ny*shift,b[2]+.012),.10,'marking',.008))
    # Shared segment ends get round junction fills; avoids gaps at the bend.
    for i,p in enumerate(points[1:-1]):
        n=16;v=[(p[0],p[1],p[2]+.002)]+[(p[0]+3*math.cos(k*2*math.pi/n),p[1]+3*math.sin(k*2*math.pi/n),p[2]+.002) for k in range(n)]
        meshes.append(dict(name=f'road_joint_{i}',vertices=v,faces=[(0,k+1,(k+1)%n+1) for k in range(n)],material='asphalt'))
    road_run('road_north',cfg['north_road'])
    road_run('road_front',cfg['front_road'])
    # Match the actual bridge-road/front-road height. The old hardcoded
    # 5.8 m connector left a 1.8 m drop after the street was raised to 7.6 m.
    join_z=cfg['road']['points'][0][2]
    meshes.append(strip('road_front_link',(50,-5,join_z),(62,-5,join_z),6,'asphalt'))
    # Crossing follows the actual first road segment's grade.
    x,cy,_=cfg['crosswalk']['centre']
    half=cfg['crosswalk']['width']/2
    for j in range(7):
        yy=cy-2.7+j*.8
        z=lambda xx:4+(xx-32)*.1
        meshes.append(strip(f'crosswalk_{j}',(x-half,yy,z(x-half)+.02),(x+half,yy,z(x+half)+.02),.45,'marking',.01))
    p=cfg['surface_parking'];z=p['z'];slab('surface_parking',p['bounds'],z,'asphalt')
    palette=['car_blue','car_white','car_white','dark','car_red','car_white']
    for row,x in enumerate(p['rows_x']):
        for i in range(p['count_per_row']):
            y=-94+i*p['bay_width'];mat=palette[(i+row*2)%len(palette)]
            slab(f'bay_{row}_{i}',(x-2.5,y-1.25,x+2.5,y-1.19),z+.012,'marking',.008)
            if i in (3,10,14):continue
            box(f'car_{row}_{i}_body',(x-2.12,y-.91,z+.23),(x+2.12,y+.91,z+1.10),mat)
            box(f'car_{row}_{i}_cabin',(x-1.15,y-.79,z+1.10),(x+1.1,y+.79,z+1.65),'glass')
            for xx in (x-1.4,x+1.4):
                for yy in (y-.9,y+.9):box(f'car_{row}_{i}_wheel_{xx}_{yy}',(xx-.30,yy-.12,z+.08),(xx+.30,yy+.12,z+.63),'dark')
    fence('parking_west',(-62,-98),(-62,-43),z)
    fence('parking_east',(-34,-98),(-34,-43),z)
    fence('parking_north_west',(-62,-40),(-53,-40),z)
    fence('parking_north_east',(-44,-40),(-34,-40),z)
    # Fixed gate leaves stand at the sides of a clear 9 m entrance.
    for x in (-53,-44):box('parking_gate_'+str(x),(x-.12,-43,z),(x+.12,-40,z+2),'fence')
    r=cfg['residential'];a,b,c,d=r['bounds'];z=r['z'];h=r['height']
    box('residential_mass',(a,b,z),(c,d,z+h),'white')
    slab('residential_roof',(a-.7,b-.6,c+.8,d+.6),z+h+.18,'dark')
    for i in range(9):
        y=b+1+i*6
        for floor in range(3):
            zz=z+.3+floor*3.15
            box(f'residential_panel_{i}_{floor}',(c,y,zz),(c+.08,y+4.8,zz+2.9),'residential_grey' if i%3 else 'white')
            box(f'residential_window_{i}_{floor}',(c+.09,y+1,zz+.75),(c+.14,y+3.4,zz+2.2),'glass')
            if i%3==1:
                box(f'residential_recess_{i}_{floor}',(c+.15,y+.15,zz+.2),(c+.18,y+.9,zz+2.8),'orange')
                slab(f'residential_balcony_{i}_{floor}',(c,y,c+1.2,y+4.8),zz+.3,'concrete',.15)
                fence(f'residential_guard_{i}_{floor}',(c+1.1,y),(c+1.1,y+4.8),zz+.3,.95)
    # Use the accepted bridge location/height; core masses are context only.
    link=levels[1]['connection'];a,b,c,d=link['bridge'];z=link['floor_local_metres']
    slab('bridge_deck',(a,b,c,d),z,'concrete',.25)
    slab('bridge_roof',(a-.15,b,c+.15,d),z+3.1,'dark')
    for y in range(math.ceil(b),math.floor(d)+1,3):
        for x in (a,c):box(f'bridge_post_{x}_{y}',(x-.06,y-.06,z),(x+.06,y+.06,z+3),'fence')
    for zz in (z+.8,z+1.05,z+1.3,z+1.55,z+1.8,z+2.05,z+2.3,z+2.55):
        for x in (a,c):box(f'bridge_louver_{x}_{zz}',(x-.06,b,zz),(x+.06,d,zz+.06),'fence')
    for ident,bounds in [('povo1',(-23,-103,24,-20)),('povo2',(-23,10,25,112))]:
        a,b,c,d=bounds;box(ident+'_context',(a,b,4),(c,d,11),'stone')
        # West glazing is laid on the visible plane; exact bays are not a survey.
        for y in range(math.ceil(b)+1,math.floor(d)-1,3):
            for zz in (4.5,8.0):box(f'{ident}_west_glazing_{y}_{zz}',(a-.10,y,zz),(a-.05,y+2.5,zz+2.6),'glass')
        # East and road-facing end facades were missing from the first study.
        for y in range(math.ceil(b)+1,math.floor(d)-1,3):
            for zz in (4.4,7.9):
                box(f'{ident}_front_window_{y}_{zz}',(c+.02,y,zz),(c+.09,y+1.7,zz+2.7),'glass')
                box(f'{ident}_front_sill_{y}_{zz}',(c,y-.05,zz-.1),(c+.2,y+1.75,zz),'concrete')
        for y in (b,d):
            for x in range(math.ceil(a)+1,math.floor(c)-1,3):
                for zz in (4.4,7.9):
                    box(f'{ident}_end_window_{x}_{y}_{zz}',(x,y-.08,zz),(x+1.75,y+.08,zz+2.7),'glass')
    ramp=cfg['garage_ramp'];aa,bb=ramp['centreline']
    meshes.append(strip('garage_ramp_apron',(-29,-8,3),aa,ramp['width'],'asphalt',.20))
    meshes.append(strip('garage_ramp_straight',aa,bb,ramp['width'],'asphalt',.25))
    # Opening remains clear; side retaining walls descend with the ramp.
    for side in (-1,1):
        x=aa[0]+side*(ramp['width']/2+.12)
        start=aa[1]+2.5;startz=aa[2]+(bb[2]-aa[2])*2.5/(bb[1]-aa[1])
        meshes.append(strip(f'ramp_retaining_{side}',(x,start,startz+1.1),(x,bb[1],bb[2]+1.1),.24,'concrete',1.35))
    # Covered basement belongs to Povo 2; its south wall has a real clear portal
    # at the unchanged straight ramp endpoint. Roof is omitted only in cutaways.
    garage=cfg['covered_parking'];ga,gb,gc,gd=garage['bounds'];gz=garage['z'];roof=garage['ceiling_z'];gw=.22
    slab('garage_floor',garage['bounds'],gz,'asphalt',.25)
    slab('garage_roof',garage['bounds'],roof+garage['slab_thickness'],'concrete',garage['slab_thickness'])
    box('garage_wall_west',(ga,gb,gz),(ga+gw,gd,roof),'concrete')
    box('garage_wall_east',(gc-gw,gb,gz),(gc,gd,roof),'concrete')
    box('garage_wall_north',(ga,gd-gw,gz),(gc,gd,roof),'concrete')
    portal_left=bb[0]-garage['portal_width']/2;portal_right=bb[0]+garage['portal_width']/2
    box('garage_wall_south_west',(ga,gb,gz),(portal_left,gb+gw,roof),'concrete')
    box('garage_wall_south_east',(portal_right,gb,gz),(gc,gb+gw,roof),'concrete')
    for x in (-13,9):
        for y in (43,63,83,103):box(f'garage_column_{x}_{y}',(x-.25,y-.25,gz),(x+.25,y+.25,roof),'concrete')
    for row,x in enumerate((-21,18)):
        for i,y in enumerate(range(39,108,6)):
            slab(f'garage_bay_{row}_{i}',(x-2.5,y-1.2,x+2.5,y-1.14),gz+.012,'marking',.008)
            if i%3==1:continue
            box(f'garage_car_{row}_{i}',(x-2,y-.9,gz+.25),(x+2,y+.9,gz+1.05),palette[(i+row)%len(palette)])
            box(f'garage_cabin_{row}_{i}',(x-1,y-.75,gz+1.05),(x+1,y+.75,gz+1.65),'glass')
    e=cfg['east_approach'];slab('povo1_entry_plaza',e['lower_plaza'],e['lower_z'],'paving')
    a,b,c,d=e['stairs'];count=math.ceil((e['upper_z']-e['lower_z'])/.18-1e-9);rise=(e['upper_z']-e['lower_z'])/count
    for i in range(count):
        x=a+(c-a)*i/count
        box(f'entry_stair_{i}',(x,b,e['lower_z']-.15),(a+(c-a)*(i+1)/count,d,e['lower_z']+(i+1)*rise),'orange')
    front=cfg['frontages'];fz=front['street_level']
    for i,r in enumerate(front['povo1_library_wings']):glass_block(f'povo1_library_{i}',r,4,10.9,panes=True)
    slab('povo1_front_walk',front['povo1_walk'],fz,'paving')
    # The Povo 1 frontage used to end at N=-13, five metres before the bridge
    # road. Close that missing strip across its full width, then follow the
    # same grade as the adjacent footway down to the Povo 2 pavement.
    slab('povo1_street_corner',(52,-13,56.7,0),fz,'paving')
    grade_z=front.get('povo2_level',fz)+(fz-front.get('povo2_level',fz))/3+.12
    meshes.append(strip('povo1_street_grade',(54.35,0,fz+.12),
                        (54.35,10,grade_z),4.7,'paving'))
    fence('povo1_street_yard_guard',(52,10),(56.7,10),grade_z,1.05)
    # Continuous passage between two front wings, open from street to stairs.
    slab('povo1_passage_upper',(c,-77,58,-69),fz,'paving')
    # A continuous glazed cover begins immediately outside the entrance,
    # follows the straight rise and stops before the street pavement.
    cy=e['entrance_y'];clearance=e['canopy_clearance'];end=e['canopy_end_x']
    canopy_points=[(24,cy,e['lower_z']+clearance),(a,cy,e['lower_z']+clearance),
          (c,cy,fz+clearance),(end,cy,fz+clearance)]
    for i,(start,finish) in enumerate(zip(canopy_points,canopy_points[1:])):
        meshes.append(strip(f'entry_canopy_roof_{i}',start,finish,6.2,'canopy_glass',.04))
        for side in (-1,1):
            meshes.append(strip(f'entry_canopy_side_beam_{i}_{side}',
                                (start[0],cy+side*3.1,start[2]),(finish[0],cy+side*3.1,finish[2]),.08,'fence',.10))
    for x in (24.3,a,c,44,end-.2):
        floor=e['lower_z'] if x<=a else fz
        for side in (-1,1):
            y=cy+side*3.1
            box(f'canopy_post_{x}_{side}',(x-.05,y-.05,floor),(x+.05,y+.05,floor+clearance),'fence')
    p2z=front.get('povo2_level',fz)
    for i,r in enumerate(front['povo2_annexes']):glass_block(f'povo2_front_annex_{i}',r,p2z,11.8)
    slab('povo2_front_walk',front['povo2_walk'],p2z,'paving')
    slab('povo2_terrace',front['povo2_terrace'],p2z,'paving')
    # Basement lightwell between the raised terrace and main stone block.
    box('povo2_lightwell_wall',(25,45,0),(25.25,77,p2z),'concrete')
    slab('povo2_lightwell_grass',(21,45,25,77),.15,'grass')
    fence('povo2_terrace_guard',(25.2,45),(25.2,77),p2z,1.1)
    fence('povo2_terrace_street_guard',(50.9,45),(50.9,77),p2z,1.1)
    for x,y in ((30,53),(30,69),(40,60)):
        slab(f'povo2_table_top_{x}_{y}',(x-1.5,y-.5,x+1.5,y+.5),p2z+.78,'dark',.12)
        for yy in (y-.85,y+.85):
            slab(f'povo2_table_bench_{x}_{yy}',(x-1.5,yy-.18,x+1.5,yy+.18),p2z+.45,'dark',.1)
        for xx in (x-1,x+1):box(f'povo2_table_leg_{xx}_{y}',(xx-.06,y-.3,p2z),(xx+.06,y+.3,p2z+.72),'fence')
    for ident,y0,y1,x0,x1 in (('povo1',-110,-13,58,58.4),('povo2',10,112,58,58.4)):
        levelz=p2z if ident=='povo2' else fz
        slab(ident+'_front_green_strip',(x0,y0,x1+1.2,y1),levelz-.04,'grass')
        for i,y in enumerate(range(y0+5,y1,13)):
            tree(f'{ident}_front_tree_{i}',59,y,levelz,6)
            box(f'{ident}_front_lamp_{i}',(55.5,y+.5,levelz),(55.65,y+.65,levelz+5),'fence')
            box(f'{ident}_front_lamp_head_{i}',(55.5,y+.5,levelz+4.9),(56.5,y+.75,levelz+5.1),'white')
    for i,y in enumerate(range(-99,-20,12)):
        tree(f'west_tree_{i}',-83,y,3,6+(i%3))
        box(f'parking_lamp_{i}',(-33.1,y,3),(-32.95,y+.15,9),'fence')
        box(f'parking_lamp_head_{i}',(-33.1,y,8.85),(-31.8,y+.25,9.05),'white')
    for i,x in enumerate(range(-17,48,10)):tree(f'road_tree_{i}',x,-11,3,6)
    boxes,entry_metadata=add_double_entrance(boxes,cfg['povo2_double_entrance'],
                                           link.get('povo2',{}).get('ground',{}).get('entrance_world'))
    terrace=front['povo2_left_terrace'];a,b,c,d=terrace
    hole=((a-.01,b-.01,p2z-.01),(c+.01,d,12.1))
    boxes=[part for item in boxes for part in
           (subtract_box(item,hole) if item[0].startswith('povo2_front_annex_0_') else [item])]
    slab('povo2_left_terrace',terrace,p2z,'paving')
    fence('povo2_left_terrace_guard',(a,b),(51,b),p2z,1.1)
    # Delimit the far side of the road, opposite both entrances, leaving the
    # street connecting the buildings open along its entire length.
    gate=cfg['street_end_gate'];h=gate['height']
    for segment,(start,finish) in enumerate(zip(gate['points'],gate['points'][1:])):
        meshes.append(strip(f'street_end_gate_base_{segment}',
                            (start[0],start[1],start[2]+.4),(finish[0],finish[1],finish[2]+.4),.3,'concrete',4))
        count=math.ceil(math.dist(start[:2],finish[:2])/.28)
        for i in range(count+1):
            t=i/count;x,y,z=(start[j]+t*(finish[j]-start[j]) for j in range(3))
            box(f'street_end_gate_bar_{segment}_{i}',(x-.035,y-.035,z+.4),(x+.035,y+.035,z+h),'dark')
        for i,offset in enumerate((.5,h*.5,h-.08)):
            meshes.append(strip(f'street_end_gate_rail_{segment}_{i}',
                                (start[0],start[1],start[2]+offset),(finish[0],finish[1],finish[2]+offset),.10,'dark',.08))
    # Deliberately schematic ridge: no photo pixels, no claim of a measured DEM.
    ridge=[(-360,12),(-320,30),(-280,23),(-230,65),(-185,100),(-150,79),(-110,95),(-65,63),(-20,74),(30,43),(90,49),(150,17)]
    rv=[];rf=[]
    for y,z in ridge:rv.extend([(-900,y,0),(-900,y,z*2.5)])
    for i in range(len(ridge)-1):k=i*2;rf.extend([(k,k+2,k+3),(k,k+3,k+1)])
    meshes.append(dict(name='distant_ridge_proxy',vertices=rv,faces=rf,material='ridge'))
    cameras=[]
    for room in levels[1]['rooms']:
        if room['id'] not in cfg['review_rooms']:continue
        a,b,c,d=room['footprint_local_metres'];floor=levels[1]['floor_elevation_metres']-cfg['origin'][2]
        cameras.append(dict(room=room['label'],position=[a+1.8,(b+d)/2,floor+1.6],target=[-73,(b+d)/2,5.9],fov=70,
                            source_room_bounds=room['footprint_local_metres']))
    refs=[]
    for entry in cfg['new_photos']:
        path=root/cfg['photo_directory']/entry['file']
        refs.append(dict(entry,file=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
    prior=[]
    manifest_path=root/'data/reference/povo_photos/manifest.json'
    manifest=json.loads(manifest_path.read_text())['images']
    for identifier in cfg['existing_evidence']:
        if not identifier.startswith('P'):continue
        item=next(p for p in manifest if p['id']==identifier)
        path=manifest_path.parent/item['file'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=item['sha256']:raise ValueError('Reference photo changed: '+identifier)
        prior.append(dict(id=identifier,file=path.relative_to(root).as_posix(),sha256=digest))
    walk_numbers=set()
    for identifier in cfg['existing_evidence']:
        if identifier.startswith('walk_'):
            _,start,_,end=identifier.split('_')
            walk_numbers.update(range(min(int(start),int(end)),max(int(start),int(end))+1))
    for number in sorted(walk_numbers):
        path=root/cfg['photo_directory']/f'image{number:05}.jpeg'
        prior.append(dict(id=f'walk_{number}',file=path.relative_to(root).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    actual=link.get('povo2',{}).get('parking',{}).get('bounds')
    endpoint=bb
    gap=None if actual is None else math.hypot(max(actual[0]-endpoint[0],0,endpoint[0]-actual[2]),max(actual[1]-endpoint[1],0,endpoint[1]-actual[3]))
    metadata=dict(config=cfg,photos=refs,prior_photo_evidence=prior,cameras=cameras,boxes=boxes,meshes=meshes,material_opacity=OPACITY,
                  povo2_double_entrance=entry_metadata,
                  garage_integration=dict(endpoint=endpoint,exterior_parking_bounds=garage['bounds'],exterior_gap_metres=0,
                                          portal=dict(centre=bb,width=garage['portal_width'],headroom=roof-gz),
                                          current_parking_bounds=actual,horizontal_gap_metres=gap,
                                          status='Straight ramp meets covered Povo 2 exterior basement; separate interior source still requires alignment'),
                  input_hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['config/povo_exterior.json','config/povo1_campus.json','config/povo1_interior_study.json','config/povo2_planimetry.json','config/povo2_connection.json','config/povo1_plan_alignment.json']})
    return boxes,meshes,metadata,live_boxes


def export(root=ROOT):
    boxes,meshes,metadata,live_boxes=build(root);out=root/'exports/povo_exterior';out.mkdir(exist_ok=True)
    with (out/'povo_exterior.obj').open('w',encoding='utf-8') as stream:
        stream.write('# Exterior study; shared campus coordinates in metres.\nmtllib povo_exterior.mtl\n');offset=0
        for name,lo,hi,mat in boxes:
            write_box(stream,name,lo,hi,offset,mat);offset+=8
        for mesh in meshes:
            stream.write(f"o {mesh['name']}\nusemtl {mesh['material']}\n")
            for v in mesh['vertices']:stream.write('v '+' '.join(map(str,v))+'\n')
            for f in mesh['faces']:stream.write('f '+' '.join(str(offset+i+1) for i in f)+'\n')
            offset+=len(mesh['vertices'])
    with (out/'povo_exterior.mtl').open('w') as stream:
        for name,rgb in COLORS.items():stream.write(f'newmtl {name}\nKd '+ ' '.join(str(v/255) for v in rgb)+f'\nd {OPACITY.get(name,1)}\n\n')
    metadata['geometry_counts']=dict(boxes=len(boxes),custom_meshes=len(meshes),triangles=12*len(boxes)+sum(len(m['faces']) for m in meshes))
    metadata['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'povo_exterior.obj',out/'povo_exterior.mtl')}
    (out/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata['geometry_counts']));print('Exterior ramp/garage gap: 0 m; separate interior alignment gap (m):',metadata['garage_integration']['horizontal_gap_metres'])
    return boxes,meshes,metadata,live_boxes


if __name__=='__main__':export()
