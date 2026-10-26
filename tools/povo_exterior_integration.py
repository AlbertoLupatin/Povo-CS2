"""Merge the approved exterior around the live interiors without replacing them."""
import copy
import json

try:
    from .povo_room_fitout import subtract_box
    from .povo2_exterior_entrance import door_bank
except ImportError:
    from povo_room_fitout import subtract_box
    from povo2_exterior_entrance import door_bank


def extend(root,settings,config,boxes,levels,stair):
    path=root/'config/povo_exterior.json'
    if not path.exists() or not json.loads(path.read_text()).get('integration_enabled'):return boxes
    # Lazy import avoids the campus/exterior source cycle; pass the base snapshot.
    try:
        from .build_povo_exterior import build
    except ImportError:
        from build_povo_exterior import build
    ext,meshes,meta,_=build(root,(settings,config,boxes,levels,stair))
    entry=meta['config']['povo2_double_entrance'];z=entry['floor_z'];cy=entry['centre_y']
    portal=((34.25,cy-4.1,z-.015),(34.8,cy+4.1,z+2.82))
    parking=levels[1]['connection']['povo2']['parking']['bounds']
    garage=meta['config']['covered_parking']['bounds']
    ramp=meta['config']['garage_ramp'];ra,rb=ramp['centreline'];rh=ramp['width']/2+.2
    ramp_hole=((ra[0]-rh,ra[1]-.2,-10),(rb[0]+rh,rb[1]+.2,5))
    oldhole=((parking[0],parking[1],-10),(parking[2],parking[3],2))
    newhole=((garage[0]+.01,garage[1]+.01,-3.19),(garage[2]-.01,garage[3]-.01,.19))
    # Povo 1's 2.2 m entrance becomes one Povo 2 style sliding bank.
    landing=next(b for b in boxes if b[0]=='campus_entry_landing')
    p1y=(landing[1][1]+landing[2][1])/2;p1z=landing[2][2]
    p1bank=dict(bank_width=3.6,clear_width=1.8,door_height=2.02)
    p1hole=((23.8,p1y-p1bank['bank_width']/2,p1z-.01),(24.2,p1y+p1bank['bank_width']/2,p1z+2.15))
    result=[]
    for box in boxes:
        n,lo,hi,m=box
        # Replace the original one-line entrance and its exterior landing guards.
        if n.startswith(('campus_entry_guard_','p2_ground_entrance_')):continue
        parts=[box]
        if n.startswith('academic_ground_outer_3'):
            parts=[piece for item in parts for piece in subtract_box(item,p1hole)]
        if n.startswith('p2_ground_shell_') or (n.startswith('p2_ground_') and '_finish_skirting_' in n):
            parts=[piece for item in parts for piece in subtract_box(item,portal)]
        # Open the overlapping garage perimeters; preserve slabs, core and fixtures.
        if n.startswith('p2_parking_') and (m=='wall' or '_wall_' in n):
            parts=[piece for item in parts for piece in subtract_box(item,newhole)]
        result.extend(parts)
    occupied=[((6.8,9.8,3.7),(25.2,26.2,11.2)),
              ((9.9,19.3,3.7),(34.7,71.7,7.37)),
              ((16.3,-6.7,.1),(20.2,26.2,3.77)),
              ((4.8,-6.7,.1),(20.2,-3.3,3.77)),
              ((6.8,13.8,-3.5),(16.7,26.2,11.2))]
    lift=levels[1]['connection']['povo2'].get('lift')
    if lift:
        a,b,c,d=lift['shaft']
        # The later exterior apron must not fill the basement lift shaft.
        occupied.append(((a,b,.1),(c,d,11.2)))
    ext_kept=[]
    for item in ext:
        n,lo,hi,m=item
        if n.startswith(('povo1_context','povo1_west_glazing','povo1_front_window','povo1_front_sill','povo1_end_window','bridge_')):continue
        # Retain the source interior to the west of its inner threshold. The
        # added inner door banks are the intentional exception at that boundary.
        parts=[item]
        if n=='west_grass':parts=[p for q in parts for p in subtract_box(q,ramp_hole)]
        if n.startswith('p2_entry_') and not n.startswith('p2_entry_inner_'):
            parts=[p for q in parts for p in subtract_box(q,((0,19.3,3.7),(34.5,71.7,7.37)))]
        elif n.startswith(('povo2_context','povo2_west_glazing','povo2_front_window','povo2_front_sill','povo2_end_window','povo2_front_annex_0_')):
            for hole in occupied:parts=[p for q in parts for p in subtract_box(q,hole)]
        if n.startswith('garage_'):
            # The original basement already supplies these overlapping surfaces.
            parts=[p for q in parts for p in subtract_box(q,oldhole)]
        # Avoid a raised landscaping slab under the existing north study room.
        ext_kept.extend(('exterior_'+name,lo,hi,'exterior_'+mat) for name,lo,hi,mat in parts)
    def p1box(name,lo,hi,mat):ext_kept.append(('exterior_p1_entry_'+name,tuple(lo),tuple(hi),'exterior_'+mat))
    door_bank(p1box,'bank_0',24,p1y,p1z,**p1bank)
    # A flat prototype apron replaces conflicting old DTM triangles locally.
    ground=('exterior_ground',(-90,-116,2.5),(74,124,2.75),'exterior_concrete')
    groundparts=subtract_box(ground,ramp_hole)
    for hole in occupied:groundparts=[p for q in groundparts for p in subtract_box(q,hole)]
    ext_kept.extend(groundparts)
    # Concrete extends beyond every backdrop edge. Keep distant context visual
    # so navigation remains limited to the campus rather than this large apron.
    context=meta['config']['context_concrete'];a,b,c,d=context['bounds'];z=context['top_z']
    for i,r in enumerate(((a,b,-90,d),(74,b,c,d),(-90,b,74,-116),(-90,124,74,d))):
        ext_kept.append((f'exterior_context_concrete_{i}',(r[0],r[1],z-.2),(r[2],r[3],z),'exterior_context_concrete'))
    z=context['underlay_z']
    ext_kept.append(('exterior_context_concrete_underlay',(a,b,z-.2),(c,d,z),'exterior_context_concrete'))
    # All added mesh materials receive their own namespace and remaps.
    meshes=copy.deepcopy(meshes)
    for mesh in meshes:
        if mesh['name']=='distant_ridge_proxy':
            mesh['vertices']=[tuple(v*.65 for v in point) for point in mesh['vertices']]
        mesh['name']='exterior_'+mesh['name'];mesh['material']='exterior_'+mesh['material']
    # Small details stay visual; closed road/ramp/fence-base strips supply physics.
    physics=[m for m in meshes if len(m['vertices'])==8 and not any(s in m['name'] for s in ('_edge_','crosswalk','_top','street_end_gate_'))]
    # A continuous barrier supplies the fence collision, avoiding hundreds of
    # separate bar hulls while preserving the closed boundary at player scale.
    for mesh in meshes:
        if not mesh['name'].startswith('exterior_street_end_gate_base_'):continue
        barrier=copy.deepcopy(mesh);barrier['name']=barrier['name'].replace('_base_','_barrier_')
        barrier['vertices']=[(x,y,z+(meta['config']['street_end_gate']['height']-.4 if i>=4 else 0))
                             for i,(x,y,z) in enumerate(barrier['vertices'])]
        physics.append(barrier)
    meta=dict(bounds=[-90,-116,74,124],meshes=meshes,collision_meshes=physics,
              door_opacity=meta['material_opacity']['entry_glass'],entrance=meta['povo2_double_entrance'],
              garage_bounds=garage,original_garage_bounds=parking,
              povo1_approach=meta['config']['east_approach'],
              left_terrace=meta['config']['frontages']['povo2_left_terrace'],
              street_end_gate=meta['config']['street_end_gate'],
              context_concrete=meta['config']['context_concrete'],
              input_hashes=meta['input_hashes'],photos=meta['photos'],
              integration='Live interior retained; entrance widened; parking perimeters opened at overlap; P2 front level aligned to z4')
    levels[0]['exterior']=meta
    groundlevel=next(l for l in levels[1]['connection']['povo2']['levels'] if l['floor']==0)
    for station in groundlevel['audit_stations']:
        if station['id']=='entrance':station['point']=[33.5,cy+entry['bank_offsets_y'][0]]
    groundlevel['audit_stations'].append(dict(id='entrance_second_bank',point=[33.5,cy+entry['bank_offsets_y'][1]]))
    return result+ext_kept


def mesh_faces(metadata):
    return [(m['name'],'campus_'+m['material'],[m['vertices'][i] for i in f],None)
            for m in metadata.get('meshes',[]) for f in m['faces']]


def write_collision(stream,metadata,offset):
    count=0
    for mesh in metadata.get('collision_meshes',[]):
        stream.write('o '+mesh['name']+'\nusemtl campus_'+mesh['material']+'\n')
        for v in mesh['vertices']:stream.write('v '+' '.join(f'{x:.12g}' for x in v)+'\n')
        for f in mesh['faces']:stream.write('f '+' '.join(str(offset+i+1) for i in f)+'\n')
        offset+=len(mesh['vertices']);count+=1
    return count


def backdrop(faces):
    """The new exterior replaces old Povo 2 solids and local terrain scenery."""
    kept=[]
    for face in faces:
        n,m,points,uv=face
        if n.startswith(('povo2_','arch_povo2_')):continue
        if n=='terrain':continue
        kept.append(face)
    return kept
