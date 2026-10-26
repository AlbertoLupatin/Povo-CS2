"""Shared native doors and deliberately limited breakable glazing.

Geometry stays in metres until VMAP insertion. The permanent campus mesh omits
only the static leaves/panes replaced here; jambs, thresholds and walls remain.
"""
import copy
import re
import uuid

try:
    from . import cs2_project as project
except ImportError:
    import cs2_project as project

UNITS = 39.37007874
PREFIX = 'materials/trento/povo/campus/'


def world(point):
    e,n,z=point
    return (-n*UNITS,e*UNITS,z*UNITS)


def door_selection(levels, stair, *, automatic_entrances=False):
    doors=[]
    def pair(name, centre, width, height, kind='fire'):
        x,y,z=centre
        for sign in (-1,1):
            edge=y+sign*width/2
            doors.append(dict(id=f'{name}_{"south" if sign<0 else "north"}',
                kind=kind,pivot=[x,edge,z],bounds=[[x-.024,min(y,edge)+.018,z+.025],
                [x+.024,max(y,edge)-.018,z+height-.025]],reverse=sign>0,
                material=PREFIX+'door_black.vmat'))
    # The black fire doors use the original fixed 90-degree open geometry.
    # They have no moving entity and cannot swing shut across a route.
    # Four photo-referenced teaching rooms; the rest retain clear openings.
    for level in levels:
        z=level['floor_elevation_metres']-370
        for room in level['rooms']:
            if room['id'] not in ('a208','a215','a223','a224'):continue
            a,b,c,d=room['footprint_local_metres'];f=room['door_fraction'];w=room['door_width_metres']
            side=room['door_side']
            x,y={'u_min':(a+(c-a)*f,b),'u_max':(a+(c-a)*f,d),
                 'v_min':(a,b+(d-b)*f),'v_max':(c,b+(d-b)*f)}[side]
            along_e=side.startswith('u_')
            lo=[x-w/2+.025,y-.024,z+.025] if along_e else [x-.024,y-w/2+.025,z+.025]
            hi=[x+w/2-.025,y+.024,z+2.075] if along_e else [x+.024,y+w/2-.025,z+2.075]
            pivot=[lo[0],y,z] if along_e else [x,lo[1],z]
            doors.append(dict(id='classroom_'+room['id'],kind='classroom',bounds=[lo,hi],pivot=pivot,
                              reverse=side in ('u_max','v_min'),material=PREFIX+'door_closed.vmat'))
    ext=levels[0].get('exterior',{})
    for bank in (() if automatic_entrances else ext.get('entrance',{}).get('door_banks',[])):
        x,y,z=bank['centre'];half=bank['clear_width']/2
        for sign in (-1,1):
            lo=y-half+.015 if sign<0 else y+.015
            hi=y-.015 if sign<0 else y+half-.015
            doors.append(dict(id=f'p2_entry_{bank["line"]}_{bank["index"]}_{sign}',kind='sliding',
                bounds=[[x+.033,lo,z+.035],[x+.073,hi,z+bank['height']-.055]],
                direction='0 180 0' if sign>0 else '0 0 0',
                material=PREFIX+'exterior/entry_glass.vmat'))
    # Povo 1's central entrance opening, clear of the red stair's lower landing.
    x,y,z=24,-73.72946859896183,4
    if not automatic_entrances:pair('p1_main',(x,y,z),2.2,2.15,'entrance')
    for d in doors:
        if d['kind']=='entrance':d['material']=PREFIX+'exterior/entry_glass.vmat'
    return doors


def extract_static_leaves(boxes, levels, stair, *, automatic_entrances=False):
    """Retain fixed-open fire doors and extract two small stair window panes."""
    result=[];panes=[]
    for box in boxes:
        name,lo,hi,mat=box
        # Keep these leaves in their generated open position. Only classroom
        # doors and the glazed entrance banks remain interactive.
        if name.startswith('exterior_') and '_parked_leaf' in name:continue
        # One framed pane on each ground-level east stair window. The other
        # panes and the entire large curtain wall remain structural glazing.
        if name in ('stair_window_0','stair_ne_window_0'):
            cut=lo[1]+(hi[1]-lo[1])/6
            pane_hi=(hi[0],cut-.025,hi[2])
            panes.append(dict(id='glass_'+name,bounds=[list(lo),list(pane_hi)],health=20))
            result.append((name,(lo[0],cut+.025,lo[2]),hi,mat))
        else:result.append(box)
    spec=dict(doors=door_selection(levels,stair,automatic_entrances=automatic_entrances),glass=panes,
              policy='Black fire doors fixed open; native classroom doors and automatic glazed entrances')
    levels[0]['interactions']=spec
    return result


def set_property(block,key,value):
    pattern=r'("'+re.escape(key)+r'"\s+"string"\s+")[^"]*(")'
    if re.search(pattern,block):return re.sub(pattern,lambda m:m[1]+str(value)+m[2],block,count=1)
    at=block.index('"classname" "string"')
    return block[:at]+f'"{key}" "string" "{value}"\n\t\t\t\t\t'+block[at:]


def brush_entity(source, token, classname, parts, properties=(), pivot=None):
    """Clone proven Hammer box topology; all child transforms are world-space."""
    template=next(b for _,_,c,b in project._entity_ranges(source) if c=='func_buyzone' and '"CMapMesh"' in b)
    all_lo=[min(p[0][i] for p in parts) for i in range(3)]
    all_hi=[max(p[1][i] for p in parts) for i in range(3)]
    center=tuple((a+b)/2 for a,b in zip(all_lo,all_hi))
    meshes=[]
    mesh_at=template.index('"CMapMesh"');start=template.index('{',mesh_at)
    mesh_template=template[mesh_at:project._matching_brace(template,start)+1]
    maxid=max(map(int,re.findall(r'"nodeID"\s+"int"\s+"(\d+)"',source)),default=1)
    for i,(lo,hi,material) in enumerate(parts):
        a,b=world(lo),world(hi)
        half=tuple(abs(y-x)/2 for x,y in zip(a,b))
        origin=' '.join(f'{(x+y)/2:.6f}' for x,y in zip(a,b))
        mesh=project.resize_trigger_mesh(mesh_template,half)
        mesh=project._replace_entity_transform(mesh,origin,angles='0 0 0',scales='1 1 1')
        mesh=re.sub(r'"elementid"\s+"([0-9a-f-]+)"',
                    lambda m:'"elementid" "'+str(uuid.uuid5(uuid.NAMESPACE_URL,f'povo:{token}:{i}:{m[1]}'))+'"',mesh)
        mesh=re.sub(r'("nodeID"\s+"int"\s+")\d+("\s*)',lambda m:m[1]+str(maxid+i+2)+m[2],mesh)
        mesh=re.sub(r'materials/[^"\s]+\.vmat',material,mesh)
        mesh=mesh.replace('"bakelighting" "bool" "1"','"bakelighting" "bool" "0"')
        mesh=mesh.replace('"renderwithdynamic" "bool" "0"','"renderwithdynamic" "bool" "1"')
        meshes.append(mesh)
        source=project._ensure_map_asset_reference(source,material)
    point=' '.join(f'{v:.6f}' for v in world(pivot or center))
    source=project._insert_point_entity(source,token,classname,point,tuple(properties))
    stable=str(uuid.uuid5(uuid.NAMESPACE_URL,'trento-povo:'+token))
    for a,b,c,block in project._entity_ranges(source):
        if stable not in block:continue
        replacement=block.replace('"children" "element_array" [ ]','"children" "element_array" [\n'+',\n'.join(meshes)+'\n]')
        return source[:a]+replacement+source[b:]
    raise ValueError('Inserted brush entity missing: '+token)


def insert_entities(source, spec):
    for door in spec['doors']:
        lo,hi=door['bounds'];mat=door['material'];sliding=door['kind']=='sliding'
        props=[('targetname',door['id']),('speed','120' if sliding else '100'),
               ('spawnpos','1'),('spawnflags','1280'),('wait','4' if sliding else '-1'),
               ('dmg','0'),('forceclosed','0'),('noise1','Povo.Door.Move'),('noise2','Povo.Door.Stop')]
        parts=[(lo,hi,mat)]
        if sliding:
            props.extend((('movedir',door['direction']),('lip','-2'),('CreateNavObstacle','1')))
            # Etched waist band remains attached to the sliding leaf.
            parts.append(([lo[0]-.003,lo[1],lo[2]+1.08],[hi[0]+.003,hi[1],lo[2]+1.12],PREFIX+'exterior/white.vmat'))
        else:
            props.extend((('distance','90'),('solidbsp','0')))
            props=[(k,('1314' if door['reverse'] else '1312') if k=='spawnflags' else v) for k,v in props]
            if hi[0]-lo[0]<hi[1]-lo[1]:
                bar=([lo[0]-.045,lo[1]+.09,lo[2]+.99],[hi[0]+.045,hi[1]-.09,lo[2]+1.035])
            else:
                bar=([lo[0]+.09,lo[1]-.045,lo[2]+.99],[hi[0]-.09,hi[1]+.045,lo[2]+1.035])
            parts.append((*bar,PREFIX+'door_pushbar.vmat'))
        source=brush_entity(source,'interactive-'+door['id'],
                'func_door' if sliding else 'func_door_rotating',parts,props,door.get('pivot'))
    for pane in spec['glass']:
        source=brush_entity(source,'interactive-'+pane['id'],'func_breakable',
            [(*pane['bounds'],'materials/glass/glass01.vmat')],
            [('targetname',pane['id']),('health',str(pane['health'])),('material','0'),
             ('spawnflags','0'),('explosion','0'),('minhealthdmg','0')])
    return source
