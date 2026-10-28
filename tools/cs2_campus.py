#!/usr/bin/env python3
"""Prepare, compile and package the separate two-floor Povo 1 campus map."""

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

try:
    from . import cs2_project as project
    from . import build_povo_radar as radar
    from .build_povo_campus import export, MATERIAL_PREFIX
    from .package_cs2 import package_map
except ImportError:
    import cs2_project as project
    import build_povo_radar as radar
    from build_povo_campus import export, MATERIAL_PREFIX
    from package_cs2 import package_map

ROOT=Path(__file__).resolve().parents[1]
MAP='trento_povo_campus'
MODEL='povo1_campus'
UNITS=39.37007874
# Terrorists start in the Povo 2 entrance hall, between the reception and the
# entrance doors, clear of the door sensors. Counter-terrorists hold Povo 1.
T_STARTS=[(x,y,4.8) for y in (29,30.5,32) for x in (24.5,26.3)]
CT_STARTS=[(x,-35.2,12.0) for x in (-2,0,2,4,6,8)]
OBJECTIVE=(13.96,-57.6,11.8)


def world(point):
    x,y,z=point
    # Verified by live floor drops: the OBJ import plus -90 pitch maps north
    # to NEGATIVE Source X. The outdoor arena's symmetric footprint hid this.
    return f'{-y*UNITS:.3f} {x*UNITS:.3f} {z*UNITS:.3f}'


def property_value(block,key,value):
    pattern=r'("'+re.escape(key)+r'"\s+"string"\s+")[^"]*(")'
    changed,count=re.subn(pattern,lambda m:m[1]+value+m[2],block,count=1)
    if not count:raise ValueError('Missing entity property '+key)
    return changed


def node_ids(source):
    return iter(range(max(map(int,re.findall(r'"nodeID"\s+"int"\s+"(\d+)"',source)),default=1)+1,1<<31))


def clone_block(template,token,classname,origin,half_extents,ids):
    """A box trigger's entity block under fresh deterministic IDs, as another solid class."""
    serial=iter(range(1<<31))
    def element(m):return m[1]+str(uuid.uuid5(uuid.NAMESPACE_URL,f'trento-povo:{token}:{next(serial)}'))+m[2]
    block=re.sub(r'("elementid"\s+")[0-9a-f-]{36}(")',element,template)
    block=re.sub(r'("nodeID"\s+"int"\s+")\d+(")',lambda m:m[1]+str(next(ids))+m[2],block)
    reference=uuid.uuid5(uuid.NAMESPACE_URL,'trento-povo:'+token).int&((1<<64)-1)
    block=re.sub(r'("referenceID"\s+"uint64"\s+")0x[0-9a-f]+(")',lambda m:m[1]+f'0x{reference:x}'+m[2],block,count=1)
    block=re.sub(r'\n[ \t]*"(TeamNum|targetname)"\s+"string"\s+"[^"]*"','',block)
    block=re.sub(r'("classname"\s+"string"\s+")[^"]+(")',lambda m:m[1]+classname+m[2],block,count=1)
    return project.resize_trigger_mesh(project._replace_entity_transform(block,origin),half_extents)


def clone_trigger(source,token,template,classname,origin,half_extents):
    block=clone_block(template,token,classname,origin,half_extents,node_ids(source))
    opening=project._world_children_opening(source)
    return source[:opening+1]+'\n'+block+','+source[opening+1:]


TRIGGER_MATERIAL='materials/tools/toolstrigger.vmat'
# BreakableBrush keys from the installed base.fgd: material 0 is Glass.
GLASS_PROPERTIES=(('health','1'),('material','0'),('propdata','0'),('PerformanceMode','PM_NORMAL'))


def add_breakable_glass(source,panes):
    """One func_breakable glass box per pane, cloned from a buy-zone mesh."""
    if not panes:return source
    template=next(block for _,_,classname,block in project._entity_ranges(source)
                  if classname=='func_buyzone' and '"CMapMesh"' in block)
    if TRIGGER_MATERIAL not in template:raise ValueError('Buy-zone mesh has no trigger material')
    ids=node_ids(source)
    blocks=[box_entity(template,'glass-'+p['name'],'func_breakable',(p['lo'],p['hi']),ids,
                       (*GLASS_PROPERTIES,('targetname','povo_glass_'+p['name'])),p['material'])
            for p in panes]
    for material in sorted({p['material'] for p in panes}):
        source=project._ensure_map_asset_reference(source,material)
    opening=project._world_children_opening(source)
    return source[:opening+1]+'\n'+',\n'.join(blocks)+','+source[opening+1:]


LADDER_MATERIAL='materials/tools/toolsinvisibleladder.vmat'


def add_ladder(source,token,box):
    """A world mesh with CS2's invisible-ladder tool material is climbable.

    Cloned from the lightmap density volume, the map's one world-level box mesh.
    """
    template=next((source[m.start():project._matching_brace(source,source.index('{',m.end()))+1]
                   for m in re.finditer(r'(?m)^[ \t]*"CMapMesh"[ \t]*$',source)
                   if 'materials/tools/toolslightmapres.vmat' in
                   source[m.start():project._matching_brace(source,source.index('{',m.end()))+1]),None)
    if template is None:raise ValueError('No world box mesh to clone for the ladder')
    lo,hi=box
    centre=tuple((a+b)/2 for a,b in zip(lo,hi))
    half=((hi[1]-lo[1])/2*UNITS,(hi[0]-lo[0])/2*UNITS,(hi[2]-lo[2])/2*UNITS)
    block=clone_block(template,token,'',world(centre),half,node_ids(source))
    block=block.replace('materials/tools/toolslightmapres.vmat',LADDER_MATERIAL)
    source=project._ensure_map_asset_reference(source,LADDER_MATERIAL)
    opening=project._world_children_opening(source)
    return source[:opening+1]+'\n'+block+','+source[opening+1:]


def box_entity(template,token,classname,box,ids,properties,material=None):
    lo,hi=box
    centre=tuple((a+b)/2 for a,b in zip(lo,hi))
    # world() swaps axes: Source X is local north, Source Y local east.
    half=((hi[1]-lo[1])/2*UNITS,(hi[0]-lo[0])/2*UNITS,(hi[2]-lo[2])/2*UNITS)
    block=clone_block(template,token,classname,world(centre),half,ids)
    if material:block=block.replace(TRIGGER_MATERIAL,material)
    props=''.join(f'\n\t\t\t\t\t"{k}" "string" "{v}"' for k,v in properties)
    return re.sub(r'("classname"\s+"string"\s+"'+classname+'")',lambda m:m[1]+props,block,count=1)


def connection(token,output,target,inputname):
    """Hammer I/O row, with the field types of Valve's own cs_script_demo.vmap."""
    return (f'"DmeConnectionData"\n{{\n"id" "elementid" "{uuid.uuid5(uuid.NAMESPACE_URL,"trento-povo:"+token)}"\n'
            f'"outputName" "string" "{output}"\n"targetType" "int" "7"\n"targetName" "string" "{target}"\n'
            f'"inputName" "string" "{inputname}"\n"overrideParam" "string" ""\n'
            '"delay" "float" "0"\n"timesToFire" "int" "-1"\n}')


def add_auto_doors(source,doors):
    """Sliding func_door leaves, opened by a trigger in front of each bank.

    The trigger's spawnflags are 1 (clients), which includes bots. 4096 is
    Source's "Disallow Bots" trigger flag, so the former 4097 kept bots from
    opening the doors except by touching a leaf.
    """
    if not doors:return source
    template=next(block for _,_,classname,block in project._entity_ranges(source)
                  if classname=='func_buyzone' and '"CMapMesh"' in block)
    ids=node_ids(source);blocks=[]
    for door in doors:
        target='trento_door_'+door['name']
        for part in door['parts']:
            # wait -1: only the trigger closes them. Touch Opens (1024) is a fallback.
            blocks.append(box_entity(template,'door-'+part['name'],'func_door',(part['lo'],part['hi']),ids,
                (('targetname',target),('movedir',f"0 {part['yaw']} 0"),('speed','60'),('wait','-1'),
                 ('lip','0'),('spawnpos','0'),('spawnflags','1024'),('forceclosed','0'),('dmg','0')),part['material']))
        trigger=box_entity(template,'door-trigger-'+door['name'],'trigger_multiple',door['trigger'],ids,
            (('targetname',target+'_sensor'),('spawnflags','1'),('wait','1'),('StartDisabled','0')))
        rows=',\n'.join((connection(f"door-io-{door['name']}-open",'OnStartTouch',target,'Open'),
                         connection(f"door-io-{door['name']}-close",'OnEndTouchAll',target,'Close')))
        trigger,count=re.subn(r'("connectionsData"\s+"element_array"\s*\[)\s*(\])',lambda m:m[1]+'\n'+rows+'\n'+m[2],trigger,count=1)
        if not count:raise ValueError('Trigger template has no empty connectionsData')
        blocks.append(trigger)
    for material in sorted({p['material'] for d in doors for p in d['parts']}):
        source=project._ensure_map_asset_reference(source,material)
    opening=project._world_children_opening(source)
    return source[:opening+1]+'\n'+',\n'.join(blocks)+','+source[opening+1:]


def skip_nav_analysis(source):
    """Mark the exterior as a large open map so CS2 skips bot nav analysis.

    In CS2 server.dll this class is read only by the map compiler's "Compute AI
    Data" step. On the open exterior's ~9,200 mutually visible nav areas its
    approach-area pass ran for over 80 minutes without finishing (9 s indoors).
    Navigation itself is still generated; only hiding/encounter/approach spots
    and early occupy times are omitted, which bots treat as missing hints.
    """
    template=next(block for _,_,classname,block in project._entity_ranges(source)
                  if classname=='func_buyzone' and '"CMapMesh"' in block)
    return clone_trigger(source,'exterior-survival-playarea',template,'trigger_survival_playarea',
                         world((-8,4,4)),(124*UNITS,86*UNITS,14*UNITS))


def gameplay_points(metadata):
    """Keep CT and the objective on the highest occupied Povo 1 storey."""
    zs=[l['floor_elevation_metres']-370 for l in metadata['levels']]
    ground,upper=min(zs),max(zs)
    return ([(x,y,ground+.8) for x,y,_ in T_STARTS],
            [(x,y,upper+.8) for x,y,_ in CT_STARTS],
            (OBJECTIVE[0],OBJECTIVE[1],upper+.6))


def map_text(source,metadata,season='standard'):
    source=source.replace('models/povo/povo_blockout.vmdl',f'models/povo/{MODEL}.vmdl')
    t_starts,ct_starts,objective=gameplay_points(metadata)
    ground=min(l['floor_elevation_metres']-370 for l in metadata['levels'])
    upper=max(l['floor_elevation_metres']-370 for l in metadata['levels'])
    spawns={'info_player_terrorist':iter(t_starts),'info_player_counterterrorist':iter(ct_starts)}
    buy={'2':(25.4,30.5,ground+.6),'3':(3,-35.2,upper+.6),'0':objective}
    replacements=[]
    for start,end,classname,block in project._entity_ranges(source):
        updated=block
        if classname in spawns:
            point=next(spawns[classname]);angle='0 0 0' if classname.endswith('terrorist') and not classname.endswith('counterterrorist') else '0 180 0'
            updated=project._replace_entity_transform(block,world(point),angle)
        elif classname=='func_buyzone':
            team=re.search(r'"TeamNum"\s+"string"\s+"([^"]+)"',block)[1]
            updated=project._replace_entity_transform(block,world(buy[team]))
            if team in ('2','3'):updated=project.resize_trigger_mesh(updated,(220,300,95))
        elif classname=='func_bomb_target':
            updated=project._replace_entity_transform(block,world(objective))
            updated=project.resize_trigger_mesh(updated,(140,46,95))
        elif classname in ('counterterrorist_wingman_intro','terrorist_wingman_intro','end_of_match'):
            point=buy['3'] if classname.startswith('counterterrorist') else buy['2'] if classname.startswith('terrorist') else objective
            updated=project._replace_entity_transform(block,world(point))
        elif classname=='post_processing_volume':
            updated=project._replace_entity_transform(block,world((0,-30,8)),scales='75 80 25')
            updated=property_value(updated,'minexposure','0.08')
            updated=property_value(updated,'maxexposure','0.22')
            updated=property_value(updated,'master','1')
        elif classname=='prop_static' and 'models/povo/povo1_campus.vmdl' in block:
            updated=property_value(updated,'bakelighting','1')
            updated=property_value(updated,'lightmapscalebias','2')
        elif classname=='env_combined_light_probe_volume':
            updated=project._replace_entity_transform(block,world((4,-15,4)))
            updated=property_value(updated,'box_mins','-5200 -3800 -400' if metadata.get('exterior') else '-4000 -1800 -400')
            updated=property_value(updated,'box_maxs','4900 3400 450' if metadata.get('exterior') else '4300 1800 450')
            updated=property_value(updated,'voxel_size','80')
        elif classname=='point_nav_walkable':
            updated=project._replace_entity_transform(block,world((21,-72,4.15)))
        elif classname=='env_soundscape':updated=project._replace_entity_transform(block,world((0,-60,7)))
        elif classname=='cs_minimap_boundary':
            p=((76,-118,12) if '2559.055' in block and '-2559.055' not in block else (-92,126,-5)) if metadata.get('exterior') else ((36,-109,12) if '2559.055' in block and '-2559.055' not in block else (-28,78,-5))
            updated=project._replace_entity_transform(block,world(p))
        if updated!=block:replacements.append((start,end,updated))
    for start,end,replacement in reversed(replacements):source=source[:start]+replacement+source[end:]
    # Move the world-level density volume independently of entity children.
    replacements=[]
    for match in re.finditer(r'(?m)^[ \t]*"CMapMesh"[ \t]*$',source):
        a=source.index('{',match.end());b=project._matching_brace(source,a)
        block=source[match.start():b+1]
        if 'materials/tools/toolslightmapres.vmat' in block:
            # This is a density guide, not the enormous post-process shell.
            # Keep its surfaces close to both occupied floors in Source units.
            updated=project.resize_trigger_mesh(block,(4900,3400,340) if metadata.get('exterior') else (3900,1500,340))
            updated=project._replace_entity_transform(updated,world((5,-15,4)),scales='1 1 1')
            replacements.append((match.start(),b+1,updated))
    for a,b,s in reversed(replacements):source=source[:a]+s+source[b:]
    if metadata.get('exterior'):source=skip_nav_analysis(source)
    source=project._insert_point_entity(source,'campus-upper-nav','point_nav_walkable',world((0,-35.2,upper+.15)))
    source=add_free_for_all(source,metadata.get('deathmatch_spawns',[]))
    for core in metadata['stair']['cores']:
        source=project._insert_point_entity(source,'campus-stair-'+core['id']+'-nav','point_nav_walkable',world(core['mid']))
    lights=[]
    # Four distributed ceiling lights per furnished room, plus ceiling-height lights
    # along the real corridor centres; keys come from installed lights2.fgd.
    for level in metadata['levels']:
        z=level['floor_elevation_metres']-370
        for room in level['rooms']:
            x0,y0,x1,y1=room['footprint_local_metres']
            if room.get('playable',True) or room.get('kind')=='reception':
                for fx in (.3,.7):
                    for fy in (.3,.7):lights.append((x0+(x1-x0)*fx,y0+(y1-y0)*fy,z+2.9))
        for corridor in level['circulation']:
            # Normalized plan axes: u is north, v is east.
            a,b,c,d=corridor['bounds'];x0,x1=-23+b*47,-23+d*47;y0,y1=-103+a*83,-103+c*83
            if y1-y0>x1-x0:
                count=max(1,math.ceil((y1-y0)/6))
                lights.extend(((x0+x1)/2,y0+(i+.5)*(y1-y0)/count,z+2.9) for i in range(count))
            else:
                count=max(1,math.ceil((x1-x0)/6))
                lights.extend((x0+(i+.5)*(x1-x0)/count,(y0+y1)/2,z+2.9) for i in range(count))
        # A worldtext plane starts in local XY. Roll 90 makes it upright;
        # yaw points its front into this doorway's corridor, with no billboard.
        for room in [*level['rooms'],*level.get('connection',{}).get('rooms',[])]:
            origin,angles=room_sign(room,z)
            source=project._insert_point_entity(source,'campus-sign-'+level['id']+'-'+room['id'],
                'point_worldtext',world(origin),sign_properties(room['label']),angles=angles)
    if metadata.get('connection'):
        lights.extend(metadata['connection']['lights'])
        for i,p in enumerate(metadata['connection']['nav_seeds']):
            source=project._insert_point_entity(source,'campus-link-nav-'+str(i),'point_nav_walkable',world(p))
        for i,portal in enumerate(metadata['connection']['stair']['portals']):
            x,y,z=portal['centre']
            source=project._insert_point_entity(source,'p2-compact-stair-sign-'+str(i),'point_worldtext',
                world((x+.15,y,z+2.44)),sign_properties('SCALE'),angles='0 180 90')
        for name,text,n,yaw in (('p1-to-p2','POVO 2',-20.13,90),('p2-arrival','POVO 2 - PIANO 1',9.87,90),('p2-to-p1','POVO 1',-19.87,270)):
            source=project._insert_point_entity(source,name,'point_worldtext',world((18.25,n,metadata['connection']['floor_local_metres']+3.04)),
                sign_properties(text,white=False),angles=f'0 {yaw} 90')
    if metadata.get('povo2'):
        p2=metadata['povo2'];lights.extend(p2['lights'])
        if p2.get('lift'):source=add_ladder(source,'p2-lift-ladder',p2['lift']['ladder'])
        for level in p2['levels']:
            for i,station in enumerate(level['audit_stations']):
                source=project._insert_point_entity(source,f"p2-nav-{level['floor']}-{i}",
                    'point_nav_walkable',world((*station['point'],level['z']+.15)))
            for room in level.get('rooms',[]):
                origin,angles=room_sign(room,level['z'])
                source=project._insert_point_entity(source,'p2-sign-'+room['id'],
                    'point_worldtext',world(origin),sign_properties(room['label']),angles=angles)
        yard=p2.get('additions',{}).get('yard')
        if yard:
            for i,station in enumerate(yard['audit_stations']):
                source=project._insert_point_entity(source,f'p2-yard-nav-{i}','point_nav_walkable',
                    world((*station['point'],yard['z']+.15)))
            for i,p in enumerate(yard['top_path']):
                source=project._insert_point_entity(source,f'p2-yard-street-nav-{i}','point_nav_walkable',
                    world((p[0],p[1],p[2]+.15)))
        for portal in p2['stairs']['portals']:
            x,y,z=portal['centre'];f=portal['floor']
            source=project._insert_point_entity(source,'p2-floor-sign-'+str(f),'point_worldtext',
                world((x+.13,y,z+2.5)),sign_properties('PIANO '+str(f),white=False),angles='0 180 90')
        for path in p2['stairs']['path']:
            mid=path['points'][12]
            source=project._insert_point_entity(source,'p2-stair-mid-nav-'+str(path['lower_floor']),
                'point_nav_walkable',world((mid[0],mid[1],mid[2]+.15)))
        source=project._insert_point_entity(source,'p2-reception-sign','point_worldtext',
            world(p2['ground'].get('reception_front_sign',(20.9,29,6.5))),sign_properties('RECEPTION POVO 2',white=False),angles='0 180 90')
    for core in metadata['stair']['cores']:
        lights.append((*core['mid'][:2],core['mid'][2]+2.5))
        for portal in core['enclosure']['portals']:
            x,y,z=portal['centre'];lights.append((x+(-2 if core['mirror_east'] else 2),y,z+2.8))
    elevator=metadata.get('elevator')
    if elevator:
        lights.extend(elevator['lights'])
        source=project._insert_point_entity(source,'campus-elevator-first-sign','point_worldtext',
            world(elevator['sign']),sign_properties('ASCENSORE'),angles='0 180 90')
        source=add_ladder(source,'campus-elevator-ladder',elevator['ladder'])
    if metadata.get('exterior'):
        lights.extend((x,y,6.8) for x in (37,42,47) for y in (30.5,36.5))
        lights.extend(((26,-73.73,7),(32,-73.73,8),(40,-73.73,8.8),(49,-73.73,8.8)))
        lights.extend((x,y,-.25) for x in (-23,2,18) for y in (40,60,80,100))
        upper=metadata['exterior']['povo1_approach']['upper_z']
        for i,p in enumerate(((26.5,-73.73,4.15),(38,-73.73,upper+.15),(54,-50,upper+.15),(57.5,-5,upper+.15),
                              (54,31.35,4.15),(42,31.35,4.15),(-29,0,1.85),(-29,30,-3.05),
                              (-29,60,-3.05),(-5,36,-3.05),(-38,65,3.15),(-48,-65,3.15))):
            source=project._insert_point_entity(source,f'exterior-nav-{i}','point_nav_walkable',world(p))
    wings=metadata.get('wings',{})
    lights.extend(wings.get('lights',[]))
    for level in wings.get('levels',[]):
        for i,station in enumerate(level['audit_stations']):
            source=project._insert_point_entity(source,f"wing-nav-{level['id']}-{i}",
                'point_nav_walkable',world((*station['point'],level['z']+.15)))
    for i,sign in enumerate(wings.get('signs',[])):
        source=project._insert_point_entity(source,f'wing-sign-{i}','point_worldtext',
            world(sign['point']),sign_properties(sign['text']),angles=sign['angles'])
    for i,p in enumerate(lights):
        source=project._insert_point_entity(source,f'campus-light-{i}','light_omni2',world(p),
            (('enabled','1'),('directlight','1'),('brightness_units','1'),('brightness_lumens','1800'),
             ('color','255 244 220'),('colormode','0'),('range','430'),('bouncelight','1'),
             ('bouncescale','1'),('shape','0'),('size_params','6 24 0.15')))
    try:
        from .povo_interactions import insert_entities
        from .povo_atmosphere import tune_map, insert_soundscapes, insert_winter
    except ImportError:
        from povo_interactions import insert_entities
        from povo_atmosphere import tune_map, insert_soundscapes, insert_winter
    source=insert_entities(source,metadata['interactions'])
    # Add brush banks/panes after the point entities to avoid repeatedly
    # scanning hundreds of mesh blocks during each light/sign insertion.
    source=add_breakable_glass(source,metadata.get('breakable_glass',[]))
    source=add_auto_doors(source,metadata.get('auto_doors',[]))
    source=tune_map(source,season)
    source=insert_soundscapes(source,metadata,season)
    if season=='winter':source=insert_winter(source)
    return source


FFA_SCRIPT='maps/scripts/povo_ffa.vjs'
# The script keeps only these audited spawns; CS2 adds unnamed nav-generated ones.
DM_SPAWN_NAME='povo_dm_spawn'


def add_free_for_all(source,spawns):
    """Campus-wide Deathmatch spawns and the script that makes Deathmatch FFA."""
    for spawn in spawns:
        x,y,z=spawn['point']
        source=project._insert_point_entity(source,'campus-'+spawn['id'].replace('_','-'),'info_deathmatch_spawn',
            world((x,y,z+.05)),(('targetname',DM_SPAWN_NAME),('enabled','1')),angles=f"0 {spawn['yaw']} 0")
    if spawns:
        source=project._ensure_map_asset_reference(source,FFA_SCRIPT)
        source=project._insert_point_entity(source,'campus-ffa-script','point_script',world((18,-5,9)),
            (('targetname','povo_ffa'),('cs_script',FFA_SCRIPT)))
    return source


def room_sign(room,z):
    a,b,c,d=room['footprint_local_metres'];f=room['door_fraction'];side=room['door_side']
    offset=room.get('sign_offset_metres',.13)
    x,y={'u_min':(a+(c-a)*f,b-offset),'u_max':(a+(c-a)*f,d+offset),
         'v_min':(a-offset,b+(d-b)*f),'v_max':(c+offset,b+(d-b)*f)}[side]
    yaw={'u_min':90,'u_max':270,'v_min':0,'v_max':180}[side]
    return (x,y,z+2.44),f'0 {yaw} 90'


def sign_properties(label,white=True):
    scale=min(.25,40/(max(1,len(label))*42*.58))
    return (('message',label),('enabled','1'),('fullbright','1'),
            ('color','245 245 235 255' if white else '30 58 70 255'),
            ('font_size','42'),('world_units_per_pixel',str(scale)),('font_name','Arial'),
            ('justify_horizontal','1'),('justify_vertical','1'),('reorient_mode','0'),
            ('depth_render_offset','0.03'))


def prepare_map(cs2_root,metadata,season='standard',map_name=MAP):
    converter=cs2_root/'game/bin/win64/dmxconvert.exe'
    source=ROOT/'cs2/content/trento_povo/maps/trento_povo.vmap'
    target=source.with_name(map_name+'.vmap')
    with tempfile.TemporaryDirectory(prefix='povo-campus-map-') as tmp:
        decoded=Path(tmp)/'base.vmap';encoded=Path(tmp)/'campus.vmap'
        subprocess.run([str(converter),'-i',str(source),'-o',str(decoded),'-oe','keyvalues2','-of','vmap'],check=True)
        text=map_text(decoded.read_text(encoding='utf-8'),metadata,season)
        decoded.write_text(text,encoding='utf-8')
        subprocess.run([str(converter),'-i',str(decoded),'-o',str(encoded),'-oe','binary','-of','vmap'],check=True)
        if not target.exists() or target.read_bytes()!=encoded.read_bytes():shutil.copyfile(encoded,target)
    print('Prepared '+str(target))


def make_radar(metadata,map_name=MAP):
    MAP=map_name
    out=ROOT/'exports/povo_campus/radar';out.mkdir(parents=True,exist_ok=True)
    overview=(dict(pos_x=-130*UNITS,pos_y=90*UNITS,scale=250*UNITS/1024,rotate=0,zoom=1)
              if metadata.get('exterior') else dict(pos_x=-80*UNITS,pos_y=82*UNITS,scale=196*UNITS/1024,rotate=0,zoom=1))
    def pixel(e,n):return ((-n*UNITS-overview['pos_x'])/overview['scale'],(overview['pos_y']-e*UNITS)/overview['scale'])
    def bounds(rect):
        x0,y0,x1,y1=rect;left,top=pixel(x1,y1);right,bottom=pixel(x0,y0);return left,top,right,bottom
    for level in metadata['levels']:
        shapes=[('floor',bounds((-23,-103,24,-20)),(84,97,104,255))]
        if metadata.get('exterior'):
            ext=metadata['exterior']
            if level['id'].startswith('academic_'):
                shapes.extend((m['name'],bounds((min(v[0] for v in m['vertices']),min(v[1] for v in m['vertices']),max(v[0] for v in m['vertices']),max(v[1] for v in m['vertices']))),(115,126,127,255))
                              for m in ext['meshes'] if m['name'].startswith('exterior_road_') and len(m['vertices'])==8)
                shapes.extend((name,bounds(r),(152,163,162,255)) for name,r in
                              [('surface_lot',(-62,-98,-35,-43)),('p2_lobby',(34.5,28.3,51.3,38.7)),('p2_front',(51,10,58,112)),('p1_front',(52,-110,58,-13))])
                shapes.extend((name,bounds(r),color) for name,r,color in
                              [('p1_entrance',(24,-76.43,52,-71.03),(180,186,182,255)),
                               ('p1_straight_stairs',(27,-76.43,36,-71.03),(181,77,66,255)),
                               ('p2_left_terrace',ext['left_terrace'],(152,163,162,255)),
                               ('street_end_gate',(67.85,-122,68.15,126),(49,59,64,255))])
        for room in level['rooms']:
            color=(160,175,181,255) if room.get('playable',True) else (49,56,61,255)
            shapes.append((room['id'],bounds(room['footprint_local_metres']),color))
        a,b,c,d=level['courtyard'];shapes.append(('courtyard',bounds((-23+b*47,-103+a*83,-23+d*47,-103+c*83)),(83,110,91,255)))
        for path in level['circulation']:
            a,b,c,d=path['bounds'];shapes.append((path['id'],bounds((-23+b*47,-103+a*83,-23+d*47,-103+c*83)),(200,210,209,255)))
        for core in metadata['stair']['cores']:
            shapes.append(('stairs_'+core['id'],bounds(core['void']),(181,77,66,255)))
        if level.get('connection'):
            link=level['connection']
            for name in ('povo1_corridor','bridge'):
                shapes.append((name,bounds(link[name]),(200,210,209,255)))
            for i,r in enumerate(link['povo2_floor_parts']):
                shapes.append(('p2_arrival_'+str(i),bounds(r),(200,210,209,255)))
            shapes.append(('p2_compact_stair',bounds(link['stair']['bounds']),(158,160,156,255)))
            for room in link['rooms']:
                shapes.append((room['id'],bounds(room['bounds']),(160,175,181,255)))
        if level['id']==max(metadata['levels'],key=lambda l:l['floor_elevation_metres'])['id']:
            shapes.extend(radar.objective_glyph(pixel(*OBJECTIVE[:2])))
        if level['id']=='academic_ground' and metadata.get('connection',{}).get('ground'):
            shapes.append(('p2_lower_landing',bounds((7,14,20,26)),(200,210,209,255)))
            shapes.append(('p2_compact_stair',bounds(metadata['connection']['stair']['bounds']),(158,160,156,255)))
        p2=metadata.get('povo2')
        if p2:
            floor=0 if level.get('user_floor',-1)==-1 else 1 if level.get('user_floor')==1 else None
            if floor==0:
                shapes.append(('p2_ground',bounds(p2['footprint']),(200,210,209,255)))
                shapes.append(('reception',bounds(p2['ground']['reception']),(83,109,117,255)))
                shapes.append(('service',bounds((16.5,23.5,20.5,29.5)),(49,56,61,255)))
                for i,r in enumerate(p2.get('additions',{}).get('ground_areas',[])):
                    shapes.append(('p2_extension_'+str(i),bounds(r),(200,210,209,255)))
                for room in p2['ground']['rooms']:
                    shapes.append((room['id'],bounds(room['bounds']),(160,175,181,255)))
            shapes.append(('p2_stairs',bounds(p2['stairs']['bounds']),(181,155,108,255)))
        for wing in metadata.get('wings',{}).get('levels',[]):
            if wing['floor']!=level.get('user_floor',-1)+1:continue
            shapes.append((wing['id'],bounds(wing['bounds']),(200,210,209,255)))
            for room in wing['rooms']:
                shapes.append((wing['id']+room['id'],bounds(room['bounds']),(160,175,181,255)))
        suffix={-1:'_lower',0:'_middle',1:''}[level.get('user_floor',-1)]
        image=MAP+suffix+'_radar.png';(out/image).write_bytes(radar.png_bytes(shapes))
        for spectate in ('','_spectate'):
            texture=MAP+suffix+'_radar'+spectate+'_tga.vtex'
            (out/texture).write_text(radar.texture_text().replace('trento_povo_radar.png',image),encoding='utf-8')
    p2=metadata.get('povo2')
    if p2:
        for level in p2['levels'][:2]:
            shapes=[]
            areas=[p2['parking']['bounds']] if level['floor']==-2 else list(p2['basement'].values())
            if level['floor']==-2 and metadata.get('exterior'):areas=[*areas,metadata['exterior']['garage_bounds']]
            for i,r in enumerate(areas):shapes.append((str(i),bounds(r),(160,175,181,255)))
            if metadata.get('exterior'):
                shapes.append(('garage_ramp',bounds((-31.75,-8,-26.25,30)),(116,146,149,255)))
            shapes.append(('stairs',bounds(p2['stairs']['bounds']),(181,155,108,255)))
            section='basement2' if level['floor']==-2 else 'basement1'
            image=MAP+'_'+section+'_radar.png';(out/image).write_bytes(radar.png_bytes(shapes))
            for spectate in ('','_spectate'):
                texture=MAP+'_'+section+'_radar'+spectate+'_tga.vtex'
                (out/texture).write_text(radar.texture_text().replace('trento_povo_radar.png',image),encoding='utf-8')
    text=['// Campus overview: upper, ground and optional Povo 2 basements.',f'"{MAP}"','{',f' "material" "overviews/{MAP}"']
    text.extend(f' "{k}" "{v:.9f}"' for k,v in overview.items())
    zs=sorted(l['floor_elevation_metres']-370 for l in metadata['levels'])
    threshold=(zs[0]+zs[1])/2*UNITS
    upper_threshold=(zs[-2]+zs[-1])/2*UNITS
    ground_min=str(2.2*UNITS) if p2 else '-10000'
    text.extend([' "verticalsections"',' {','  "default" { "AltitudeMin" "'+str(upper_threshold)+'" "AltitudeMax" "10000" }',
                 '  "middle" { "AltitudeMin" "'+str(threshold)+'" "AltitudeMax" "'+str(upper_threshold)+'" }',
                 '  "lower" { "AltitudeMin" "'+ground_min+'" "AltitudeMax" "'+str(threshold)+'" }'])
    if p2:
        text.extend(['  "basement1" { "AltitudeMin" "'+str(-1.4*UNITS)+'" "AltitudeMax" "'+ground_min+'" }',
                     '  "basement2" { "AltitudeMin" "-10000" "AltitudeMax" "'+str(-1.4*UNITS)+'" }'])
    text.append(' }')
    t_starts,ct_starts,objective=gameplay_points(metadata)
    for label,p in [('CTSpawn',ct_starts[2]),('TSpawn',t_starts[2]),('bombA',objective)]:
        x,y=pixel(*p[:2]);text.extend((f' "{label}_x" "{x/1024:.9f}"',f' "{label}_y" "{y/1024:.9f}"'))
    text.append('}');(out/(MAP+'.txt')).write_text('\n'.join(text)+'\n',encoding='utf-8')
    return out


def deploy_assets(cs2_root,radar_dir,map_name=MAP):
    MAP=map_name
    project.deploy(cs2_root)
    content=cs2_root/'content/csgo_addons/trento_povo';game=cs2_root/'game/csgo_addons/trento_povo'
    for path in (ROOT/'exports/povo_campus').glob(MODEL+'*.obj'):
        shutil.copyfile(path,content/'models/povo'/path.name)
    for path in (ROOT/'exports/povo_campus/winter').glob('*.obj'):
        shutil.copyfile(path,content/'models/povo'/path.name)
    images=content/'panorama/images/overheadmaps';images.mkdir(parents=True,exist_ok=True)
    for p in radar_dir.iterdir():
        if p.suffix in ('.png','.vtex'):shutil.copyfile(p,images/p.name)
    cfg=ROOT/'cs2/game/trento_povo/cfg/maps'/(MAP+'.cfg')
    cfg.write_text('// Povo 1 campus gameplay defaults.\nbot_quota 4\nbot_quota_mode fill\n',encoding='utf-8')
    (game/'cfg/maps').mkdir(parents=True,exist_ok=True);shutil.copyfile(cfg,game/'cfg/maps'/cfg.name)
    (game/'resource/overviews').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(radar_dir/(MAP+'.txt'),game/'resource/overviews'/(MAP+'.txt'))


def build(cs2_root,*,compile_map=True,pack=True,season='standard',skip_model=False):
    metadata=export()
    seasons=('standard','winter') if season=='both' else (season,)
    content=cs2_root/'content/csgo_addons/trento_povo'
    compiler=cs2_root/'game/bin/win64/resourcecompiler.exe'
    prepared=[]
    for chosen in seasons:
        map_name=MAP+('_winter' if chosen=='winter' else '')
        prepare_map(cs2_root,metadata,chosen,map_name);radar_dir=make_radar(metadata,map_name)
        deploy_assets(cs2_root,radar_dir,map_name);prepared.append((chosen,map_name,radar_dir))
    if not compile_map:return
    def compile_resource(resource):
        print('Compiling '+str(resource),flush=True)
        options=['-lightmapVRadQuality','1'] if resource.suffix=='.vmap' else []
        subprocess.run([str(compiler),'-nop4','-fshallow2',*options,'-game',str(cs2_root/'game/csgo'),'-i',str(resource)],check=True)
    if not skip_model:compile_resource(content/'models/povo'/(MODEL+'.vmdl'))
    # Brush-only materials may be absent from the static model, so its compile
    # cannot seed them in a clean addon. Generated entity meshes load compiled
    # materials directly; build those sources before compiling the VMAP.
    brush_materials={p['material'] for p in metadata.get('breakable_glass',[])}
    brush_materials.update(p['material'] for d in metadata.get('auto_doors',[]) for p in d['parts'])
    brush_materials.update(d['material'] for d in metadata['interactions']['doors'])
    for material in sorted(brush_materials):
        path=content/material
        if path.is_file():compile_resource(path)
    compile_resource(content/'soundevents/soundevents_addon.vsndevts')
    compile_resource(content/FFA_SCRIPT.replace('.vjs','.js'))
    if 'winter' in seasons:
        compile_resource(content/'models/povo/povo_winter.vmdl')
        compile_resource(content/'particles/povo/snow.vpcf')
    for chosen,map_name,radar_dir in prepared:
        compile_resource(content/'maps'/(map_name+'.vmap'))
        radar_pattern=re.compile(re.escape(map_name)+r'(?:_(?:lower|middle|basement1|basement2))?_radar(?:_spectate)?_tga\.vtex')
        for p in sorted(p for p in radar_dir.glob('*.vtex') if radar_pattern.fullmatch(p.name)):
            compile_resource(content/'panorama/images/overheadmaps'/p.name)
        game=cs2_root/'game/csgo_addons/trento_povo'
        shutil.copyfile(radar_dir/(map_name+'.txt'),game/'resource/overviews'/(map_name+'.txt'))
        if pack:
            extras=['soundevents/soundevents_addon.vsndevts_c','maps/scripts/povo_ffa.vjs_c']
            if chosen=='winter':extras+=['models/povo/povo_winter.vmdl_c','particles/povo/snow.vpcf_c']
            result=package_map(cs2_root,ROOT/'build/tools/vpkedit-4.4.2/vpkeditcli.exe',
                ROOT/'build/package'/(map_name+'.vpk'),force=True,map_name=map_name,model_name=MODEL,
                overview_source=radar_dir/(map_name+'.txt'),extra_assets=extras)
            print(f"Packaged {chosen}: {result['package_bytes']} bytes, {result['package_entries']} entries",flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cs2-root',type=Path);parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--season',choices=('standard','winter','both'),default='standard')
    parser.add_argument('--skip-model',action='store_true',help='Reuse already compiled shared campus model after entity-only changes')
    parser.add_argument('--no-package',action='store_true');args=parser.parse_args()
    build(project.discover_cs2_root(args.cs2_root),compile_map=not args.prepare_only,pack=not args.no_package,
          season=args.season,skip_model=args.skip_model)
