"""Register the complete traced -1 plan to the current core and floor-0 spine.

Produces a review model, not an implicit replacement of the installed campus.
The core fit and the local corridor-width normalization are explicit in the
export. Door intervals are transformed with the same mapping as room walls.
"""
import hashlib
import json
from html import escape
from pathlib import Path

from tools.build_povo_campus import ROOT, build_geometry
from tools.povo2_basements import union_rectangles
from tools.povo2_survey import load


class Registration:
    def __init__(self, source_core, target_core, source_corridor, target_corridor):
        self.sc = source_core
        self.tc = target_core
        self.sy = (target_core[3]-target_core[1])/(source_core[2]-source_core[0])
        self.sx = (target_core[2]-target_core[0])/(source_core[3]-source_core[1])
        self.source_band = source_corridor[1], source_corridor[3]
        self.target_band = target_corridor[0], target_corridor[2]
        if abs(self.source_band[1]-source_core[1]) > 1e-8:
            raise ValueError('The traced corridor must touch the selected core')
        if abs(self.target_band[0]-target_core[2]) > 1e-8:
            raise ValueError('The reference corridor must touch the retained core')

    def point(self, x, y):
        lo, hi = self.source_band
        west, east = self.target_band
        if y < lo:
            e = east+(lo-y)*self.sx
        elif y <= hi:
            e = east-(y-lo)/(hi-lo)*(east-west)
        else:
            e = west-(y-hi)*self.sx
        n = self.tc[3]-(x-self.sc[0])*self.sy
        return [e,n]

    def rect(self, r):
        a,b = self.point(r[0],r[1]), self.point(r[2],r[3])
        return [min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]

    def door(self, room):
        trace = room.get('opening_trace')
        if not trace:
            return None
        a,b,c,d = room['bounds']
        side,start,end = trace['side'],trace['start'],trace['end']
        if side in ('north','south'):
            fixed = b if side=='north' else d
            ends = [self.point(start,fixed), self.point(end,fixed)]
        else:
            fixed = a if side=='west' else c
            ends = [self.point(fixed,start), self.point(fixed,end)]
        return dict(points=ends, source=trace, status='image-traced; metric placement estimated')


def perimeter_walls(rectangles, holes=(), thickness=.16):
    """Rectangle-union shell with source doorway intervals carved from walls."""
    _,edges = union_rectangles(rectangles)
    walls=[]
    for axis,fixed,lo,hi in edges:
        spans=[(lo,hi)]
        for p,q in holes:
            # Constant east walls have north-running portals, and conversely.
            if abs(p[axis]-q[axis])>1e-7 or abs(p[axis]-fixed)>.21:
                continue
            start,end=sorted((p[1-axis],q[1-axis]))
            spans=[part for u,v in spans for part in ((u,min(v,start)),(max(u,end),v)) if part[1]-part[0]>1e-7]
        for u,v in spans:
            r=[fixed-thickness/2,u,fixed+thickness/2,v] if axis==0 else [u,fixed-thickness/2,v,fixed+thickness/2]
            walls.append([*r,.65])
    return walls


def create_layout(spec, boxes, root=ROOT):
    cfg=json.loads((root/'config/povo2_minus1_layout_review.json').read_text())
    source=next(l for l in load(root)['levels'] if l['floor']==-1)
    reg=Registration(source['annotated_corridor_exit_core'],spec['stairs']['well_bounds'],
                     source['corridors'][cfg['source_aligned_corridor_index']],cfg['floor0_reference_corridor'])
    rooms=[]
    for r in source['rooms']:
        room=dict(id=r['id'],label=r['id'].replace('_',' '),kind=r['kind'],
                  bounds=reg.rect(r['bounds']),source_bounds=r['bounds'],door=reg.door(r),
                  evidence=r['evidence'],source_photo=r['source_photo'])
        if not room['door']:
            room['door_status']=r['door_status']
            room['access_topology']=r['access_topology']
        rooms.append(room)
    corridors=[dict(id='corridor_'+str(i+1),bounds=reg.rect(r),source_bounds=r) for i,r in enumerate(source['corridors'])]
    cores=[dict(id='core_'+str(i+1),bounds=reg.rect(r),source_bounds=r) for i,r in enumerate(source['stairs'])]
    core=spec['stairs']['well_bounds']
    # Retain the actual south stair-door position and connect it into the
    # aligned passage; the registered plan's core envelope remains unchanged.
    portal=next(p for p in spec['stairs']['portals'] if p['floor']==-1)
    px,py,_=portal['centre']
    threshold=[px-.825,py-1.2,cfg['floor0_reference_corridor'][2],py+.15]
    corridors.append(dict(id='retained_stair_threshold',bounds=threshold,
                          evidence='Short connection from the unchanged campus stair door to the registered main corridor'))
    holes=[r['door']['points'] for r in rooms if r['door']]
    holes.append([[px-.825,py],[px+.825,py]])
    # The east core threshold aligns with floor 0. Door positions for the
    # other plan cores are shown only as enclosures, without invented flights.
    holes.append([[core[2],21.175],[core[2],22.825]])
    circulation=[r['bounds'] for r in corridors]+[r['bounds'] for r in cores]
    wallrects=perimeter_walls(circulation,holes)
    glasswalls=[]
    for room in rooms:
        walls=perimeter_walls([room['bounds']],holes)
        wallrects.extend(walls)
    # The current south door must remain open through the shared threshold
    # and core boundary, even though their rectangle union may hide the seam.
    slabs,_=union_rectangles(circulation+[r['bounds'] for r in rooms])
    areas=[dict(label='Aligned main corridor',r=corridors[cfg['source_aligned_corridor_index']]['bounds'],kind='circulation',priority=5)]
    areas += [dict(label='Stair core' if i==1 else 'Plan core '+str(i+1),r=r['bounds'],kind='core',priority=5 if i==1 else 3) for i,r in enumerate(cores)]
    lab_labels={'annotated_lab_e':'Lab / Room 1 · door unresolved','annotated_lab_w':'Lab / Room 2'}
    for r in rooms:
        office=r['kind']=='office'
        areas.append(dict(label=lab_labels.get(r['id'],r['label']),id=r['id'],r=r['bounds'],
                          kind='study' if office else 'room',priority=4 if r['id'] in lab_labels else 1,
                          finish='Plan outline only; photo corridor is internal to West Offices, with exact location unresolved'))
    minus1=dict(f=-1,z=.4,slabs=slabs,walls=wallrects,glazing=glasswalls,areas=areas,details=[])
    minus1['openings']=[r['door']['points'] for r in rooms if r['door']]
    # Show the retained real stair treads, rather than fabricating flights in
    # the three additional plan cores.
    for n,lo,hi,m in boxes:
        if n.startswith('p2_internal_-1_') and '_step_' in n:
            minus1['details'].append([*lo[:2],*hi[:2],'stair'])
    # The -2 branch is already nearly aligned: move its centreline 0.75 m
    # east, extend the vestibule by the same amount, keep parking/garden/core.
    target=cfg['floor0_reference_corridor'];axis=(target[0]+target[2])/2
    width=cfg['minus2_aligned_branch_width'];before=cfg['minus2_aligned_branch_bounds_before']
    branch=[axis-width/2,before[1],axis+width/2,before[3]]
    vestibule=list(spec['parking']['vestibule']);vestibule[2]=branch[0]
    garden_route=[branch[2],12.5,38,14.5]
    p_areas=[spec['parking']['bounds'],vestibule,branch,garden_route,core,spec['gardens']['garden']]
    p_slabs,_=union_rectangles(p_areas)
    p_holes=[[[17.375,18],[19.025,18]],[[11,15.2],[11,16.9]],
             [[branch[0],15.2],[branch[0],16.9]],[[38,12.65],[38,14.35]]]
    parking=dict(f=-2,z=-3.2,slabs=p_slabs,walls=perimeter_walls(p_areas,p_holes),details=[],areas=[
        dict(label='Stair core',r=core,kind='core',priority=5),
        dict(label='Parking',r=spec['parking']['bounds'],kind='parking',priority=3),
        dict(label='Vestibule',r=vestibule,kind='circulation',priority=4),
        dict(label='Aligned office corridor',r=branch,kind='circulation',priority=4),
        dict(label='Garden corridor',r=garden_route,kind='circulation',priority=2),
        dict(label='Garden −2',r=spec['gardens']['garden'],kind='garden',priority=3)])
    for n,lo,hi,m in boxes:
        if n.startswith(('p2_parking_car_','p2_parking_rebuilt_column_')):
            parking['details'].append([*lo[:2],*hi[:2],'detail'])
        elif n.startswith('p2_internal_-2_') and '_step_' in n:
            parking['details'].append([*lo[:2],*hi[:2],'stair'])
    g=spec['ground'];ground_slabs=[];ground_walls=[]
    for n,lo,hi,m in boxes:
        if not n.startswith('p2_'):continue
        if m.startswith('floor_') and abs(hi[2]-4)<.04 and '_step_' not in n:
            ground_slabs.append([*lo[:2],*hi[:2]])
        if m in ('wall','window_frame','reception_frosted','reception_glass','door_closed') and lo[2]<4.65 and hi[2]>4.15:
            ground_walls.append([*lo[:2],*hi[:2],min(.65,hi[2]-4)])
    ground_slabs += [spec['gardens'][k] for k in ('street_garden','entrance_courtyard','up_top','street_side_walk')]
    ground_slabs,_=union_rectangles(ground_slabs)
    ground=dict(f=0,z=4,slabs=ground_slabs,walls=ground_walls,details=[],areas=[
        dict(label='Stair core',r=core,kind='core',priority=5),
        dict(label='Aligned main corridor',r=target,kind='circulation',priority=5),
        *[dict(label=r['label'],r=r['bounds'],kind='room',priority=4) for r in g['rooms']],
        dict(label='Reception',r=g['reception'],kind='room',priority=3),
        dict(label='Study tables',r=g['tables'],kind='study',priority=3),
        dict(label='Street garden',r=spec['gardens']['street_garden'],kind='garden',priority=3),
        dict(label='Entrance courtyard',r=spec['gardens']['entrance_courtyard'],kind='garden',priority=2)])
    return dict(status=cfg['status'],rooms=rooms,corridors=corridors,cores=cores,
        voids=[reg.rect(r) for r in source['voids']],
        exits=[dict(e,campus_point=reg.point(*e['point'])) for e in source['exits']],
        registration=dict(source_core=source['annotated_corridor_exit_core'],campus_core=core,
            photo_x_to_campus_north_scale=-reg.sy,photo_y_to_campus_east_scale_outside_corridor=-reg.sx,
            corridor_source_band=list(reg.source_band),corridor_campus_band=list(reg.target_band),
            basis=cfg['registration'],metric_status=cfg['metric_status']),
        alignment=dict(axis='campus east coordinate of north/south corridor centreline',
            floor0_reference=target,centreline=axis,minus1=corridors[4]['bounds'],
            minus2_before=before,minus2_after=branch,minus2_translation_east=axis-(before[0]+before[2])/2),
        new_walk=dict(photos=cfg['new_walk_photos'],evidence=cfg['office_finish_evidence'],
                      exact_photo_to_room_identification='unconfirmed',corridor_scope=cfg['photo_corridor_scope']),
        limitations=[cfg['metric_status'],cfg['door_policy'],cfg['build_scope'],
            'Other stair cores are plan enclosures; their flights have not been inferred.',
            'Photo46 covers more of the building than the current partial floor-0 model.'],
        floors=[parking,minus1,ground],core=core,
        source_hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in
            ['config/povo2_minus1_layout_review.json',cfg['source_plan'],cfg['source_image'],*cfg['new_walk_photos']]})


def restore_full_plan(layout,root=ROOT):
    """Annotate the chosen full plan without another corridor transformation."""
    cfg=json.loads((root/'config/povo2_minus1_layout_review.json').read_text())
    source=next(l for l in load(root)['levels'] if l['floor']==-1)
    reg=Registration(source['annotated_corridor_exit_core'],layout['core'],source['corridors'][4],cfg['floor0_reference_corridor'])
    layout['layout_mode']='full_plan_restored'
    layout['west_offices_context']=dict(bounds=reg.rect(cfg['west_offices_context_source_bounds']),
        source_bounds=cfg['west_offices_context_source_bounds'],label='WEST OFFICES',
        internal_corridor_status='Photographed corridor is internal to this office area; exact location and subdivisions unresolved',
        boundary_status='Context outline from the cropped plan edge, not a surveyed complete office boundary')
    layout['lab_access_status']='Restricted laboratory access remains closed; do not infer public access from plan door symbols.'
    layout['closed_door_registration']='The two existing fixed doors remain in the installed layout. Their exact transfer into this full-plan registration is unresolved; no replacement positions are invented.'
    layout['limitations'].append('The photo corridor is internal to West Offices. The rejected western public-route refit and 6.7 m -2 vestibule shift are not applied.')
    return layout


def focus_west_corridor(layout,spec,root=ROOT):
    """Build the user's western office route; keep research wings restricted.

    This supersedes the first review's mistaken north/south corridor focus.
    The western branch is fitted to the transverse floor-0 corridor above
    B106/PC. The retained core stays fixed and has a short south approach.
    """
    cfg=json.loads((root/'config/povo2_minus1_layout_review.json').read_text())
    src=next(l for l in load(root)['levels'] if l['floor']==-1)
    source_band=src['corridors'][cfg['source_west_corridor_index']]
    reference=cfg['floor0_west_corridor'];north=(reference[1]+reference[3])/2
    core=layout['core'];reg=Registration(src['annotated_corridor_exit_core'],core,src['corridors'][4],cfg['floor0_reference_corridor'])
    a,c=source_band[0],source_band[2]
    def point(x,y):
        e=reg.point(x,y)[0]
        if x<a:n=reference[3]+(a-x)*reg.sy
        elif x<=c:n=reference[3]-(x-a)/(c-a)*(reference[3]-reference[1])
        else:n=reference[1]-(x-c)*reg.sy
        return [e,n]
    def rectangle(r):
        p,q=point(r[0],r[1]),point(r[2],r[3])
        return [min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1])]
    def door(source_room):
        t=source_room.get('opening_trace')
        if not t:return None
        r=source_room['bounds'];side=t['side']
        if side in ('west','east'):
            x=r[0] if side=='west' else r[2]
            ends=[point(x,t['start']),point(x,t['end'])]
        else:
            y=r[1] if side=='north' else r[3]
            ends=[point(t['start'],y),point(t['end'],y)]
        return dict(points=ends,status='Approximate observed leaf interval; core-relative metric placement',source=t)
    newrooms=[]
    for rid,label,kind in [('side_e1','West office 1','office'),('side_e2','West office 2','office'),
                            ('core_e_store','West service room','service'),('wc_lower_e','West WC','sanitary')]:
        r=next(r for r in src['rooms'] if r['id']==rid)
        bounds=rectangle(r['bounds']);bounds[1]=reference[3]
        opening=door(r)
        if opening:
            for p in opening['points']:p[1]=reference[3]
        newrooms.append(dict(id='west_'+rid,label=label,kind=kind,bounds=bounds,source_bounds=r['bounds'],
            source_room=rid,door=opening,evidence='Western side-room extent on photo46; user identified western office route'))
    for i,r in enumerate(cfg['west_outer_rooms'],3):
        source_room=dict(bounds=r['source_bounds'],opening_trace=r.get('opening_trace'))
        bounds=rectangle(r['source_bounds']);bounds[3]=reference[1]
        newrooms.append(dict(id=r['id'],label='West office '+str(i),kind='office',bounds=bounds,
            source_bounds=r['source_bounds'],door=door(source_room),door_status=r.get('door_status'),
            evidence=cfg['western_trace_status']))
    west=rectangle(source_band);west[2]=25.5
    # Public stair exit turns west after the short south approach. Other
    # connections from this office route terminate at two solid locked doors.
    south_portal=next(p for p in spec['stairs']['portals'] if p['floor']==-1)
    px,py,_=south_portal['centre']
    approach=[px-1.15,reference[3],px+1.15,py]
    return_x=reg.rect(src['corridors'][7])
    lab_return=[return_x[0],reference[3],return_x[2],17.5]
    corridors=[dict(id='western_office_corridor',bounds=west),dict(id='retained_stair_approach',bounds=approach),
               dict(id='locked_lab_return',bounds=lab_return)]
    holes=[r['door']['points'] for r in newrooms if r['door']]
    holes.append([[px-.825,py],[px+.825,py]])
    public_areas=[west,approach,lab_return,core]+[r['bounds'] for r in newrooms]
    slabs,_=union_rectangles(public_areas)
    walls=perimeter_walls([west,approach,lab_return,core],holes)
    # Core east face is a wall on -1; the ground-floor east door must not
    # accidentally become another public entrance to the restricted labs.
    walls.extend(perimeter_walls([core],holes))
    glass=[]
    for r in newrooms:
        (glass if r['kind']=='office' else walls).extend(perimeter_walls([r['bounds']],holes))
    closed=[dict(id='west_east_labs',centre=[west[2],north,.4],axis=0,width=west[3]-west[1],height=2.25,
                 status='permanently closed',destination='restricted laboratories'),
            dict(id='west_north_labs',centre=[(lab_return[0]+lab_return[2])/2,lab_return[3],.4],axis=1,
                 width=lab_return[2]-lab_return[0],height=2.25,status='permanently closed',destination='restricted laboratories')]
    public=dict(f=-1,z=.4,slabs=slabs,walls=walls,glazing=glass,details=layout['floors'][1]['details'],
        openings=holes,closed_doors=closed,areas=[
            dict(label='WEST office corridor',r=west,kind='study',priority=5),
            dict(label='Stair core',r=core,kind='core',priority=5),
            dict(label='Stair approach',r=approach,kind='circulation',priority=3),
            dict(label='Locked · labs',r=lab_return,kind='closed',priority=3),
            *[dict(label=r['label']+(' · door unresolved' if not r['door'] else ''),id=r['id'],r=r['bounds'],
                   kind='study' if r['kind']=='office' else 'room',priority=3) for r in newrooms]])
    layout['restricted_lab_context']=dict(status='Restricted laboratories; two access doors permanently closed',
        rooms=layout['rooms'],floor=layout['floors'][1])
    layout['floors'][1]=public
    # Align the westward -2 vestibule to the same transverse axis. The
    # north/south branch from the first draft is no longer the reference.
    parking=layout['floors'][0];old=spec['parking']['vestibule'];delta=north-(old[1]+old[3])/2
    vestibule=[old[0],old[1]+delta,old[2],old[3]+delta]
    branch=[20.5,min(vestibule[1],12.5),24,23.5]
    stair_approach=[17.375,vestibule[3],19.025,18]
    garden_route=[24,12.5,38,14.5]
    p_areas=[spec['parking']['bounds'],vestibule,branch,stair_approach,core,garden_route,spec['gardens']['garden']]
    parking['slabs']=union_rectangles(p_areas)[0]
    parking['walls']=perimeter_walls(p_areas,[[[17.375,18],[19.025,18]],[[11,vestibule[1]+.8],[11,vestibule[3]-.8]],
        [[20.5,vestibule[1]+.8],[20.5,vestibule[3]-.8]],[[38,12.65],[38,14.35]]])
    parking['areas']=[dict(label='Stair core',r=core,kind='core',priority=5),
        dict(label='Parking',r=spec['parking']['bounds'],kind='parking',priority=3),
        dict(label='Aligned WEST corridor / vestibule',r=vestibule,kind='circulation',priority=5),
        dict(label='Stair approach',r=stair_approach,kind='circulation',priority=3),
        dict(label='Office branch',r=branch,kind='circulation',priority=3),
        dict(label='Garden corridor',r=garden_route,kind='circulation',priority=2),
        dict(label='Garden −2',r=spec['gardens']['garden'],kind='garden',priority=3)]
    ground=layout['floors'][2]
    ground['areas']=[r for r in ground['areas'] if r['label']!='Aligned main corridor']
    ground['areas'].append(dict(label='WEST corridor · ground reference',r=reference,kind='circulation',priority=5))
    layout['alignment']=dict(axis='campus north coordinate of the WEST east/west corridor centreline',
        floor0_reference=reference,centreline=north,minus1=west,minus2_before=old,minus2_after=vestibule,
        minus2_translation_north=delta)
    layout['western_office_rooms']=newrooms
    layout['western_corridors']=corridors
    layout['closed_lab_doors']=closed
    layout['status']=cfg['status']
    layout['western_registration']=dict(source_corridor=source_band,campus_corridor=west,
        north_axis_fit=[reference[1],reference[3]],status=cfg['western_trace_status'])
    layout['limitations'].append('User correction: the west/bottom office corridor is the focus; the full research wings are restricted context, not publicly accessible offices.')
    return layout


def write_plan(layout,out):
    """Inspectable north-up drawing; metric geometry matches the 3D review."""
    f=layout['floors'][1];all_r=f['slabs'];xmin=min(r[0] for r in all_r);xmax=max(r[2] for r in all_r)
    ymin=min(r[1] for r in all_r);ymax=max(r[3] for r in all_r);scale=9
    width=(xmax-xmin)*scale+160;height=(ymax-ymin)*scale+170
    def xy(x,y):return 75+(x-xmin)*scale,100+(ymax-y)*scale
    elements=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial,sans-serif" fill="#26363f"><text x="30" y="30" font-size="22">Povo 2 / WEST −1 office corridor</text>',
        '<text x="30" y="57" font-size="13">Core and main corridor registered to floor 0 · dimensions estimated · north up</text>']
    def rect(r,fill,stroke='none',sw=.6):
        x,y=xy(r[0],r[3]);elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{(r[2]-r[0])*scale:.2f}" height="{(r[3]-r[1])*scale:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    for r in f['slabs']:rect(r,'#eceff0')
    for a in f['areas']:
        palette=dict(core='#efc087',room='#cee2f4',study='#e5d7ed',circulation='#d9eadf',closed='#d9b8ae')
        rect(a['r'],palette[a['kind']])
    for r in f['walls']:rect(r,'#344957')
    for r in f['glazing']:rect(r,'#6d9eaa')
    for room in layout.get('western_office_rooms',layout['rooms']):
        a,b,c,d=room['bounds'];x,y=xy((a+c)/2,(b+d)/2)
        name=room.get('label',room['id'])
        if room['id']=='annotated_lab_w':name='LAB / ROOM 2'
        if room['id']=='annotated_lab_e':name='LAB / ROOM 1 ?DOOR'
        elements.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="8" text-anchor="middle">{escape(name)}<title>{escape(room["id"]+": "+room["evidence"])}</title></text>')
    for room in layout.get('western_office_rooms',layout['rooms']):
        if room['door']:
            p,q=room['door']['points'];a,b=xy(*p);c,d=xy(*q)
            elements.append(f'<path d="M{a:.2f},{b:.2f} L{c:.2f},{d:.2f}" stroke="#178276" stroke-width="2"/>')
    for i,core in enumerate([dict(bounds=layout['core'])] if 'western_office_rooms' in layout else layout['cores']):
        a,b,c,d=core['bounds'];x,y=xy((a+c)/2,(b+d)/2)
        elements.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="11" text-anchor="middle">EXISTING CORE</text>')
    elements+=['</g></svg>']
    (out/'minus1_new_layout.svg').write_text('\n'.join(elements),encoding='utf-8')


def export(root=ROOT):
    _,_,boxes,levels,_=build_geometry(root=root)
    spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
    layout=restore_full_plan(create_layout(spec,boxes,root),root)
    out=root/'exports/povo2_minus1_layout_20261029';out.mkdir(parents=True,exist_ok=True)
    (out/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    from tools.render_povo2_full_plan_2d import render
    render(layout,out)
    (out/'minus1_new_layout.svg').write_bytes((out/'minus1_full_plan_restored.svg').read_bytes())
    template=(root/'tools/templates/povo2_layout_review.html').read_text(encoding='utf-8')
    packed=json.dumps({k:layout[k] for k in ('floors','core','alignment')},separators=(',',':'),ensure_ascii=False)
    (out/'review-3d.html').write_text(template.replace('__LAYOUT_DATA__',packed),encoding='utf-8')
    return layout,out


if __name__=='__main__':
    layout,out=export()
    print(out)
    print(json.dumps(dict(layout_mode=layout['layout_mode'],rooms=len(layout['rooms']),
        alignment=layout['alignment']),indent=2))
