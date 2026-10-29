"""Add the plan-traced West Offices to the approved full-plan SVG model."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image

from tools.build_povo_campus import ROOT
from tools.create_povo2_minus1_layout import Registration, perimeter_walls
from tools.povo2_basements import union_rectangles
from tools.render_povo2_full_plan_2d import render


def subtract_rect(rect, hole):
    a,b,c,d,*tail=rect;u,v,w,t=hole
    x1,y1,x2,y2=max(a,u),max(b,v),min(c,w),min(d,t)
    if x1>=x2 or y1>=y2:return [rect]
    return [[*r,*tail] for r in [(a,b,x1,d),(x2,b,c,d),(x1,b,x2,y1),(x1,y2,x2,d)] if r[0]<r[2] and r[1]<r[3]]


def overlaps(a, b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]


def cut_openings(walls, openings):
    result=walls
    for opening in openings:
        p,q=opening['points'];pad=.14
        hole=[min(p[0],q[0])-pad,min(p[1],q[1])-pad,max(p[0],q[0])+pad,max(p[1],q[1])+pad]
        result=[part for r in result for part in subtract_rect(r,hole)]
    return result


def build(base,root=ROOT):
    cfg=json.loads((root/'config/povo2_west_offices.json').read_text())
    result=copy.deepcopy(base)
    registration=base['registration']
    reg=Registration(registration['source_core'],registration['campus_core'],
                     [0,*[registration['corridor_source_band'][0]],100,registration['corridor_source_band'][1]],
                     base['alignment']['floor0_reference'])
    tw,th=cfg['local_trace']['size_pixels'];a,b,c,d=cfg['local_trace']['source_plan_bounds']
    def source(u,v):return [a+(c-a)*u/tw,b+(d-b)*v/th]
    def point(u,v):return reg.point(*source(u,v))
    def rect(r):
        p,q=point(r[0],r[1]),point(r[2],r[3])
        return [min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1])]
    def observed(points,status):return dict(points=[point(*p) for p in points],status=status,source_pixels=points)
    rooms=copy.deepcopy(cfg['inner_rooms'])
    row=cfg['outer_row'];u1,u2=row['u_bounds']
    rooms += [dict(id='W'+str(row['ids_start']+i).zfill(2),kind='office',bounds=[u1,v1,u2,v2])
              for i,(v1,v2) in enumerate(zip(row['v_partitions'],row['v_partitions'][1:]))]
    row=cfg['end_row'];v1,v2=row['v_bounds']
    rooms += [dict(id='W'+str(row['ids_start']+i).zfill(2),kind='office',bounds=[u1,v1,u2,v2])
              for i,(u1,u2) in enumerate(zip(row['u_partitions'],row['u_partitions'][1:]))]
    rooms.append(copy.deepcopy(cfg['corner_room']))
    for room in rooms:
        room['trace_bounds']=list(room['bounds']);room['bounds']=rect(room['bounds'])
        room['id']='west_'+room['id'];room['label']=room['id'].replace('west_','')
        room['source_photo']=46;room['evidence']='Partition extent traced from the uncropped photo46 west office strip'
        # Every internal frontage faces a plan passage. Where a swing is
        # unreadable, retain the distinction between a review door and a trace.
        u1,v1,u2,v2=room['trace_bounds']
        if int(room['label'][1:])<=6:side='u_max'
        elif int(room['label'][1:])<=18 or room['label']=='W23':side='u_min'
        else:side='v_min'
        r=room['bounds']
        if side in ('u_min','u_max'):
            fixed=u1 if side=='u_min' else u2
            centre=894 if room['label']=='W23' else v1+(v2-v1)*.36
            middle=point(fixed,centre);half=min(cfg['door_width_metres']/2,(r[2]-r[0])*.3)
            ends=[[middle[0]-half,middle[1]],[middle[0]+half,middle[1]]]
        else:
            centre=u1+(u2-u1)*.36;middle=point(centre,v1)
            half=min(cfg['door_width_metres']/2,(r[3]-r[1])*.3)
            ends=[[middle[0],middle[1]-half],[middle[0],middle[1]+half]]
        room['frontage_source_side']=side
        room['door']=dict(points=ends,status='estimated internal review opening; swing unreadable in plan')
        room['secondary_doors']=[]
        if room.get('public_door_pixels'):
            room['secondary_doors'].append(observed(room['public_door_pixels'],'approximately image-traced public-side doorway'))
        room['finish']=cfg['finishes'] if room['kind']=='office' else dict(floor='wood',solid_partitions='white')
    entrance=observed(cfg['main_corridor_entrance_pixels'],cfg['main_corridor_entrance_status'])
    corridors=[dict(id='WI'+str(i+1),label=label,bounds=rect(cfg[key]),trace_bounds=cfg[key],scope='internal to West Offices')
               for i,(key,label) in enumerate([('internal_spine','Internal office spine'),('return_vestibule','Office return / vestibule'),('end_return','Internal end return'),('c7_connector','Spine-to-C7 connector')])]
    corridors[-1]['evidence']=cfg['c7_connector_status']
    # The connector is open full-width onto C7 and onto the spine.
    u1,v1,u2,v2=cfg['c7_connector']
    connector_ends=[dict(points=[point(u,v1),point(u,v2)],status='open connector end; user-confirmed corridor') for u in (u1,u2)]
    # The spine's east end (v=0) is open full-width onto C5, like WI4 on C7.
    u1,_,u2,_=cfg['internal_spine']
    connector_ends.append(dict(points=[point(u1,0),point(u2,0)],status='open spine end onto C5; user-confirmed'))
    footprint=rect([0,0,tw,th])
    openings=[entrance,*connector_ends]+[o for r in rooms for o in [r['door'],*r['secondary_doors']]]
    holes=[o['points'] for o in openings]
    walls=perimeter_walls([footprint],holes);glass=[]
    for room in rooms:
        rwalls=perimeter_walls([room['bounds']],holes)
        # Select just the office's corridor-facing side as glazing; party
        # partitions and external walls stay solid.
        u1,v1,u2,v2=room['trace_bounds'];side=room['frontage_source_side']
        front_end=929 if room['label']=='W23' else v2
        p,q=(point(u2,v1),point(u2,v2)) if side=='u_max' else (point(u1,v1),point(u1,front_end)) if side=='u_min' else (point(u1,v1),point(u2,v1))
        axis=0 if abs(p[0]-q[0])<1e-7 else 1;fixed=p[axis]
        for w in rwalls:
            if room['kind']=='office' and abs((w[axis]+w[axis+2])/2-fixed)<1e-6:
                along=1-axis;lo,hi=sorted((p[along],q[along]));inside=list(w)
                inside[along]=max(w[along],lo);inside[along+2]=min(w[along+2],hi)
                if inside[along]<inside[along+2]:
                    glass.append(inside)
                    walls.extend(subtract_rect(w,inside[:4]))
                else:walls.append(w)
            else:walls.append(w)
    # C7 runs past the main stair core to C5. The registered core overlaps C7,
    # so C7 jogs south under it at its own width; the offices give way. This
    # band also covers the retained stair-door threshold.
    core=base['core'];c7=next(c for c in base['corridors'] if c['id']=='corridor_7')['bounds']
    c5=next(c for c in base['corridors'] if c['id']=='corridor_5')['bounds']
    bypass=[core[0]-cfg['c7_core_bypass']['turn_metres'],core[1]-(c7[3]-c7[1]),c5[0],core[1]]
    for room in rooms:
        r=room['bounds'];cut=[max(r[0],bypass[0]),max(r[1],bypass[1]),min(r[2],bypass[2]),min(r[3],bypass[3])]
        if cut[0]>=cut[2] or cut[1]>=cut[3]:continue
        if cut[0]<=r[0] and cut[2]>=r[2]:room['bounds'][3]=bypass[1]
        else:room['excluded_for_c7_bypass']=cut
    # Identical party-wall segments only need one body.
    walls=list(dict.fromkeys(tuple(round(v,7) for v in w) for w in walls))
    floor=next(f for f in result['floors'] if f['f']==-1)
    # C8's southern stub ran to the photo edge, not to a traced end; photo 46
    # shows the office strip there, so C8 now stops at C7's south edge.
    c8=next(c for c in result['corridors'] if c['id']=='corridor_8')
    stub=[c8['bounds'][0]-.1,footprint[1]-.1,c8['bounds'][2]+.1,footprint[3]]
    floor['walls']=[part for w in floor['walls'] for part in subtract_rect(w,stub)]
    c8['trimmed_south_from']=c8['bounds'][1];c8['bounds'][1]=footprint[3]
    c8['trim_evidence']='Source band reached the photo edge (v 0-100); photo 46 shows West Offices south of C7'
    public_holes=[entrance,connector_ends[0],connector_ends[2]]+[o for r in rooms for o in r['secondary_doors']]
    floor['walls']=cut_openings(floor['walls'],public_holes)
    floor['walls'].extend(walls);floor['glazing'].extend(glass)
    # Clear the band's interior, through C7's south wall and C5's west wall;
    # the core's south wall and its stair door are left as they are.
    t=.08;carve=[bypass[0]+t,bypass[1]+t,bypass[2]+.1,bypass[3]-t]
    floor['walls']=[part for w in floor['walls'] for part in subtract_rect(w,carve)]
    floor['glazing']=[part for w in floor['glazing'] for part in subtract_rect(w,carve)]
    bypass_walls=[[bypass[0]-t,bypass[1]-t,bypass[2],bypass[1]+t,.65],[bypass[0]-t,bypass[1]-t,bypass[0]+t,c7[1],.65]]
    floor['walls'].extend(bypass_walls)
    walls=[part for w in walls for part in subtract_rect(list(w),carve)]+bypass_walls
    glass=[part for w in glass for part in subtract_rect(list(w),carve)]
    # Floor and a clear way across the gap between the office shell and C5.
    spine=corridors[0]['bounds'];link=[footprint[2],spine[1],c5[0],spine[3]]
    floor['walls']=[part for w in floor['walls'] for part in subtract_rect(w,[link[0]-.1,link[1]+t,link[2]+.1,link[3]-t])]
    floor['slabs']=union_rectangles([*floor['slabs'],footprint,bypass,link])[0]
    spine[2]=link[2]
    floor['areas'].append(dict(label='C7 core bypass',r=bypass,kind='circulation',priority=3))
    result['corridors'].append(dict(id='c7_core_bypass',bounds=bypass,evidence=cfg['c7_core_bypass']['status']))
    floor['openings'].extend(o['points'] for o in openings)
    floor.setdefault('estimated_openings',[]).extend(r['door']['points'] for r in rooms)
    floor['areas'].extend(dict(id=r['id'],label=r['label'],r=r['bounds'],kind='study' if r['kind']=='office' else 'room',priority=1) for r in rooms)
    floor['areas'].extend(dict(label=c['label'],r=c['bounds'],kind='circulation',priority=3) for c in corridors)
    result['rooms'].extend(rooms)
    result['west_offices']=dict(rooms=rooms,corridors=corridors,footprint=footprint,entrance=entrance,
        openings=openings,walls=walls,glazing=glass,trace=cfg['local_trace'],finishes=cfg['finishes'],
        public_portals=public_holes,door_policy=cfg['estimated_door_policy'],scope=cfg['scope'])
    result['west_offices_context']=dict(bounds=footprint,label='WEST OFFICES',internal_corridor_status='Built internally from the uncropped plan; inferred doorway offsets remain approximate')
    result['layout_mode']='full_plan_with_west_offices'
    result['status']=cfg['status']
    result['source_hashes'].update({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
        ['config/povo2_west_offices.json',cfg['baseline_svg'],cfg['baseline_layout'],cfg['source_photo']]})
    result['limitations'].append(cfg['estimated_door_policy'])
    return result


def write_obj(layout,out):
    """Export the new office shell at full wall height, open at the top."""
    office=layout['west_offices'];z=.4;index=0;lines=['# Povo 2 West Offices; campus metres; review geometry']
    def box(name,r,bottom,height):
        nonlocal index
        a,b,c,d=r[:4];lines.append('o '+name)
        for x,y,t in [(a,b,bottom),(c,b,bottom),(c,d,bottom),(a,d,bottom),(a,b,bottom+height),(c,b,bottom+height),(c,d,bottom+height),(a,d,bottom+height)]:lines.append(f'v {x:.6f} {y:.6f} {t:.6f}')
        for face in [(1,4,3,2),(5,6,7,8),(1,2,6,5),(2,3,7,6),(3,4,8,7),(4,1,5,8)]:lines.append('f '+' '.join(str(index+i) for i in face))
        index+=8
    box('west_offices_floor',office['footprint'],z-.22,.22)
    for i,r in enumerate(office['walls']):box('solid_partition_'+str(i),r,z,3.1)
    for i,r in enumerate(office['glazing']):box('glazed_frontage_'+str(i),r,z,2.9)
    for i,o in enumerate(office['openings']):
        p,q=o['points'];r=[min(p[0],q[0])-.08,min(p[1],q[1])-.08,max(p[0],q[0])+.08,max(p[1],q[1])+.08]
        box('door_head_'+str(i),r,z+2.2,.9)
    (out/'west_offices_shell.obj').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def export(root=ROOT):
    cfg=json.loads((root/'config/povo2_west_offices.json').read_text())
    base=json.loads((root/cfg['baseline_layout']).read_text(encoding='utf-8'))
    layout=build(base,root);out=root/'exports/povo2_west_offices_20261029';out.mkdir(exist_ok=True)
    (out/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    render(layout,out)
    for suffix in ('png','svg'):
        (out/f'minus1_with_west_offices.{suffix}').write_bytes((out/f'minus1_full_plan_restored.{suffix}').read_bytes())
    write_obj(layout,out)
    # Keep a source crop from the complete photograph as trace provenance.
    im=Image.open(root/cfg['source_photo']);tw,th=cfg['local_trace']['size_pixels']
    im.transform((tw*3,th*3),Image.Transform.QUAD,cfg['local_trace']['quad_original_pixels_ul_ll_lr_ur'],resample=Image.Resampling.BICUBIC).save(out/'west_offices_plan_trace.png')
    (out/'registration.json').write_text(json.dumps(dict(baseline_svg=cfg['baseline_svg'],
        main_corridors_unchanged_except_c8_stub=[c for c in layout['corridors'] if c['id']!='corridor_8'][:len(base['corridors'])-1]==[c for c in base['corridors'] if c['id']!='corridor_8'],
        added_corridors=[c['id'] for c in layout['corridors'][len(base['corridors']):]],
        corridor_8_south_edge=dict(before=next(c for c in base['corridors'] if c['id']=='corridor_8')['bounds'][1],
                                   after=next(c for c in layout['corridors'] if c['id']=='corridor_8')['bounds'][1]),
        other_floors_unchanged=all(next(f for f in layout['floors'] if f['f']==n)==next(f for f in base['floors'] if f['f']==n) for n in (-2,0)),
        new_rooms=len(layout['west_offices']['rooms']),internal_corridors=len(layout['west_offices']['corridors']),
        public_entrances=len(layout['west_offices']['public_portals']),
        approximate_internal_doors=len(layout['west_offices']['rooms'])),indent=2)+'\n',encoding='utf-8')
    return layout,out


if __name__=='__main__':
    layout,out=export()
    print(out)
    print('Added',len(layout['west_offices']['rooms']),'West Office/service rooms; main corridors retained.')
