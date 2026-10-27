"""Reviewable Povo2 photo trace. Does not replace the live campus automatically.

Photo coordinates are deliberately kept independent of guessed metric dimensions.
Only explicit registration can produce metric geometry; every assumed opening
retains its uncertainty in the returned spec.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(root=ROOT):
    spec = json.loads((root/'config/povo2_survey.json').read_text())
    for level in spec['levels']:
        seen=set()
        for room in level['rooms']:
            if room['id'] in seen:raise ValueError('Duplicate room '+room['id'])
            seen.add(room['id'])
            a,b,c,d=room['bounds']
            if not(0<=a<c<=100 and 0<=b<d<=100):raise ValueError('Invalid bounds '+room['id'])
    return spec


def register(spec, origin, scale_metres, rotation_degrees=0, *, allow_provisional=False):
    """Return metric geometry using explicit caller calibration, never hidden fit.

    origin is campus XY of photo (0,0); scale is metres per photo-plan unit.
    Rotation is restricted to quarter-turns so partitions remain axis aligned.
    Unresolved rooms fail closed. Centred review portals require the caller's
    explicit allow_provisional=True; they must never enter a faithful build.
    """
    if rotation_degrees not in (0,90,180,270):raise ValueError('Quarter-turn registration required')
    sx,sy=(scale_metres,scale_metres) if isinstance(scale_metres,(int,float)) else scale_metres
    if sx<=0 or sy<=0:raise ValueError('Positive measured scales required')
    unresolved=[f'{level["floor"]}/{room["id"]}' for level in spec['levels']
                for room in level['rooms'] if not room.get('opening_trace') and not room.get('no_portal')]
    if unresolved and not allow_provisional:
        raise ValueError('Unresolved door traces: '+', '.join(unresolved))
    result=copy.deepcopy(spec);boxes=[];opening_holes=[]
    def pt(x,y):
        x*=sx;y*=sy
        x,y={0:(x,y),90:(-y,x),180:(-x,-y),270:(y,-x)}[rotation_degrees]
        return x+origin[0],y+origin[1]
    def add(n,a,b,z,h,m):
        p=pt(*a);q=pt(*b)
        boxes.append((n,(min(p[0],q[0]),min(p[1],q[1]),z),(max(p[0],q[0]),max(p[1],q[1]),z+h),m))
    h=spec['wall_height_estimate'];t=.16/min(sx,sy)
    for level in result['levels']:
        z=level['z'];prefix='p2_survey_'+str(level['floor'])
        for i,r in enumerate(level['corridors']):
            a,b,c,d=r;add(prefix+f'_corridor_{i}',(a,b),(c,d),z-.2,.2,'floor_p2_tile')
        for room in level['rooms']:
            a,b,c,d=room['bounds'];n=prefix+'_'+room['id']
            trace=room.get('opening_trace');side=trace['side'] if trace else None if room.get('no_portal') else room['door_side']
            add(n+'_floor',(a,b),(c,d),z-.2,.2,'floor_p2_asphalt' if room['kind']=='parking' else 'floor_p2_tile')
            for s,fixed,lo,hi in [('north',b,a,c),('south',d,a,c),('west',a,b,d),('east',c,b,d)]:
                ranges=[(lo,hi)]
                if s==side:
                    along_scale=sx if s in ('north','south') else sy
                    dw=spec['door_width_estimate']/along_scale
                    if trace:
                        start,end=trace['start'],trace['end']
                        if not lo<=start<end<=hi:raise ValueError('Opening outside room '+room['id'])
                        mid=(start+end)/2;half=(end-start)/2
                    else:
                        mid=(lo+hi)/2;half=min(dw/2,(hi-lo)*.3)
                    ranges=[(lo,mid-half),(mid+half,hi)]
                    room['door']=dict(side=s,position_plan_units=[mid,fixed] if s in ('north','south') else [fixed,mid],width_metres=half*2*along_scale,status='image-traced' if trace else 'estimated; explicit provisional opt-in')
                    p,q=(pt(mid-half,fixed-t),pt(mid+half,fixed+t)) if s in ('north','south') else (pt(fixed-t,mid-half),pt(fixed+t,mid+half))
                    opening_holes.append(((min(p[0],q[0]),min(p[1],q[1]),z-.01),(max(p[0],q[0]),max(p[1],q[1]),z+2.2)))
                    if s in ('north','south'):add(n+'_door_head',(mid-half,fixed-t/2),(mid+half,fixed+t/2),z+2.2,h-2.2,'wall')
                    else:add(n+'_door_head',(fixed-t/2,mid-half),(fixed+t/2,mid+half),z+2.2,h-2.2,'wall')
                for j,(start,end) in enumerate(ranges):
                    if end-start<1e-8:continue
                    if s in ('north','south'):add(n+'_'+s+str(j),(start,fixed-t/2),(end,fixed+t/2),z,h,'wall')
                    else:add(n+'_'+s+str(j),(fixed-t/2,start),(fixed+t/2,end),z,h,'wall')
            room['campus_centre']=list(pt((a+c)/2,(b+d)/2))
    # Shared boundaries may be represented by both rooms: carve every traced
    # opening from the complete wall union so the neighbour cannot seal it.
    try:
        from .povo_room_fitout import subtract_box
    except ImportError:
        from povo_room_fitout import subtract_box
    for hole in opening_holes:
        boxes=[p for box in boxes for p in (subtract_box(box,hole) if box[3]=='wall' else [box])]
    result['registration']=dict(origin=origin,scale_metres=scale_metres,rotation_degrees=rotation_degrees,status='caller-supplied calibration; openings still provisional')
    return boxes,result


def write_review(root=ROOT):
    """Save source-space overlays, keeping observed ink and candidate data distinct."""
    import base64
    from html import escape

    spec=load(root);out=root/'exports/povo2_survey';out.mkdir(parents=True,exist_ok=True)
    for level in spec['levels']:
        observed=level['floor']==-1
        rooms=level['rooms'];doors=sum(bool(r.get('opening_trace')) for r in rooms)
        mode='PHOTO 46 OBSERVED TRACE' if observed else 'CANDIDATE DIAGRAM / NOT AN OBSERVED COMPLETE PLAN'
        elements=['<svg xmlns="http://www.w3.org/2000/svg" width="2376" height="2706" viewBox="-4 -10 108 123">',
                  '<rect x="-4" y="-10" width="108" height="123" fill="white"/>']
        def text(x,y,label,size=1.1,color='#193441',anchor='start'):
            elements.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" paint-order="stroke" stroke="white" stroke-width=".11">{escape(str(label))}</text>')
        def rect(bounds,fill,stroke='#2870a6',opacity=.13,dashed=False,title=None):
            a,b,c,d=bounds
            dash=' stroke-dasharray=".55 .4"' if dashed else ''
            elements.append(f'<rect x="{a}" y="{b}" width="{c-a}" height="{d-b}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width=".12"{dash}>')
            if title:elements.append('<title>'+escape(title)+'</title>')
            elements.append('</rect>')
        text(0,-7,f'Povo 2 floor {level["floor"]:+d} / source photo {level["source_photo"]} / {mode}',1.6)
        if observed:
            raster=out/'rectified_46.png'
            encoded=base64.b64encode(raster.read_bytes()).decode('ascii')
            elements.append(f'<image x="0" y="0" width="100" height="100" href="data:image/png;base64,{encoded}"/>')
            text(0,-4.5,f'{len(rooms)} room bounds / {doors} observed door segments / {len(level["exits"])} red-star exits / source coordinates, not metres',1.15)
            text(0,-2.5,'Photo perspective corrected for review only; every untraced source detail remains visible beneath the overlay.',.95)
        else:
            text(0,-4.5,'Dashed outlines are candidate extents. Door sides and room subdivisions need source verification.',1.05,'#8a5900')
            text(0,-2.5,'No centred door marks are generated. This diagram does not replace the active model or prove dimensions.',.95)
        for i,bounds in enumerate(level['corridors'],1):
            rect(bounds,'#ffe34b','#b59500',.26,not observed,f'C{i}: circulation bound; '+('photo trace' if observed else 'candidate'))
            a,b,c,d=bounds;text((a+c)/2,(b+d)/2,f'C{i}',.8,'#775e00','middle')
        for room in rooms:
            a,b,c,d=room['bounds'];rid=room['id']
            rect(room['bounds'],'#61a9e5','#22699a',.10,not observed,rid+' / '+room.get('evidence','candidate extent'))
            size=min(.95,max(.36,(c-a)*1.5/max(1,len(rid))))
            text((a+c)/2,(b+d)/2+.2,rid,size,'#124c7a','middle')
            trace=room.get('opening_trace') if observed else None
            if trace:
                side=trace['side'];lo,hi=trace['start'],trace['end']
                x0,y0,x1,y1=(lo,b,hi,b) if side=='north' else (lo,d,hi,d) if side=='south' else (a,lo,a,hi) if side=='west' else (c,lo,c,hi)
                elements.append(f'<path d="M{x0},{y0} L{x1},{y1}" fill="none" stroke="white" stroke-width=".65"/>')
                elements.append(f'<path data-kind="observed-door" d="M{x0},{y0} L{x1},{y1}" fill="none" stroke="#00a651" stroke-width=".34"><title>{escape(rid+": observed "+side+" door segment")}</title></path>')
            elif observed and room.get('access_topology'):
                # Highlight the room, never a guessed point/gap on its north edge.
                rect(room['bounds'],'none','#d88700',0,True,rid+': one north corridor entrance confirmed; exact position obscured; no segment drawn')
                text((a+c)/2,b+1.2,'? NORTH DOOR',.64,'#a45c00','middle')
        for i,bounds in enumerate(level['stairs'],1):
            rect(bounds,'#49bc77','#176b3a',.24,not observed,f'S{i}: stair/core '+('source bound' if observed else 'candidate'))
            a,b,c,d=bounds;text((a+c)/2,(b+d)/2,f'S{i}',.9,'#12572b','middle')
        for i,bounds in enumerate(level['voids'],1):
            rect(bounds,'#c3c7cc','#656c72',.17,not observed,f'V{i}: void/courtyard '+('source bound' if observed else 'candidate'))
            a,b,c,d=bounds;text((a+c)/2,(b+d)/2,f'V{i} / VOID',.85,'#555c62','middle')
        for i,exit_info in enumerate(level['exits'],1):
            x,y=exit_info['point'];label=f'X{i:02d}'
            elements.append(f'<circle data-kind="exit" cx="{x}" cy="{y}" r=".52" fill="#d92b32" fill-opacity=".88" stroke="white" stroke-width=".16"><title>{escape(exit_info["id"]+": "+exit_info.get("evidence","candidate exit position"))}</title></circle>')
            text(x+.7,y-.15,label,.7,'#ac1325')
        text(0,103,'BLUE room extents + IDs | GREEN door segments | YELLOW C circulation | GREEN S stair/core | GREY V void | RED X exits',.98)
        if observed:
            text(0,105.5,'Right circled lab: exactly ONE north corridor entrance; its precise position is obscured by blue annotation. No synthetic gap.',1.05,'#8c5200')
            text(0,107.5,'The WEST red-star opening is a separate exit to the EXTERNAL COURTYARD, confirmed by the user.',1.05,'#8c5200')
            text(0,109.5,'Bounds follow manual image traces, not measured walls. Faint/occluded details and fine subdivisions remain incomplete.',.98)
        else:
            text(0,105.5,'Candidate rooms/corridors/cores/exits only. Solid source ink has not been fully traced for this floor.',1.05,'#8a5900')
            text(0,107.5,'Review hypotheses remain separate from the active compact Povo 2 geometry; no complete reconstruction is asserted.',1.02)
        elements.append('</svg>')
        (out/f'floor_{level["floor"]}.svg').write_text('\n'.join(elements),encoding='utf-8')
    return out


def extend_confirmed_basement(boxes, levels, root=ROOT):
    """Integrate photo46 rooms at the existing -1 core, using provisional XY.

    Registration keeps the photograph's measured-on-image aspect ratio. This
    updates the confirmed semibasement only; other floors remain incomplete.
    """
    try:
        from .povo_room_fitout import subtract_box
    except ImportError:
        from povo_room_fitout import subtract_box
    link=next(l['connection'] for l in levels if l.get('connection'))
    p2=link['povo2'];survey=load(root)
    source=next(l for l in survey['levels'] if l['floor']==-1)
    source=copy.deepcopy(source)
    # One circled lab portal is covered by the annotation. Keep its enclosure
    # closed until that actual doorway is supplied; never synthesize a portal.
    unresolved=[r['id'] for r in source['rooms'] if not r.get('opening_trace')]
    for room in source['rooms']:
        if not room.get('opening_trace'):room['no_portal']=True
    survey['levels']=[source]
    portal=next(p['centre'] for p in p2['stairs']['portals'] if p['floor']==-1)
    sx,sy=.72,.55
    origin=[portal[0]-84.7*sx,portal[1]-48.75*sy]
    generated,registered=register(survey,origin,(sx,sy))
    fixed=('p2_basement_core_','p2_basement_lift_')
    result=[b for b in boxes if not b[0].startswith(('p2_basement_','p2_yard_')) or b[0].startswith(fixed)]
    core=p2['stairs']['bounds'];z=source['z']
    hole=((core[0]-.1,core[1]-.1,z-.3),(core[2]+.1,core[3]+.1,z+3.4))
    generated=[part for box in generated for part in subtract_box(box,hole)]
    # Preserve the true core/landing and connect its south doorway to the
    # traced cross corridor, cutting the complete wall union at that portal.
    x,y=portal[:2]
    generated.append(('p2_survey_-1_core_threshold',(x-.85,y-1.2,z-.2),(x+.85,y+.5,z),'floor_p2_tile'))
    door_hole=((x-.85,y-1.3,z-.01),(x+.85,y+.6,z+2.2))
    generated=[part for box in generated for part in (subtract_box(box,door_hole) if box[3]=='wall' else [box])]
    # Excavate axis-aligned scenery only within actual new occupied rooms.
    for _,lo,hi,mat in generated:
        if mat not in ('floor_p2_tile','floor_p2_asphalt'):continue
        volume=((lo[0]-.12,lo[1]-.12,z-.25),(hi[0]+.12,hi[1]+.12,z+3.4))
        result=[part for box in result for part in
                (subtract_box(box,volume) if box[0].startswith('exterior_') else [box])]
    result.extend(generated)
    target=next(l for l in p2['levels'] if l['floor']==-1)
    target['superseded_route_rooms']=target.get('rooms',[])
    target['rooms']=[];target['audit_stations']=[]
    for room in registered['levels'][0]['rooms']:
        a,b,c,d=room['bounds'];corners=[(origin[0]+a*sx,origin[1]+b*sy),(origin[0]+c*sx,origin[1]+d*sy)]
        bounds=[*corners[0],*corners[1]]
        target['rooms'].append(dict(id=room['id'],label=room['label'],bounds=bounds,footprint_local_metres=bounds,
            playable=not room.get('no_portal'),source_photo=46,door_trace=room.get('opening_trace'),door_width_metres=room.get('door',{}).get('width_metres'),
            status='Photo46 partitions/door positions; metric scale provisional; fitout unobserved'))
        target['audit_stations'].append(dict(id=room['id']+'_centre',point=room['campus_centre']))
    p2['survey_semibasement']=dict(registration=registered['registration'],unresolved_rooms=unresolved,
        source_photo=46,status='Integrated individual partitions and79traced portals; remaining perimeter rooms/service partitions incomplete',
        observed_door_count=len(target['rooms']),geometry_scale_status='Provisional72x55m footprint; actual span unmeasured')
    return result

if __name__=='__main__':
    print(write_review())
