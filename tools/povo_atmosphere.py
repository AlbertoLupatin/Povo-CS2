"""Deterministic seasonal dress, area soundscapes and lighting profiles."""
import copy
import json
import math
from pathlib import Path

try:
    from . import cs2_project as project
    from .povo_interactions import set_property, world
    from .povo_room_fitout import subtract_box
    from .povo_campus_finishes import png
except ImportError:
    import cs2_project as project
    from povo_interactions import set_property, world
    from povo_room_fitout import subtract_box
    from povo_campus_finishes import png

ROOT=Path(__file__).resolve().parents[1]
PREFIX='materials/trento/povo/campus/seasonal/'


def settings(root=ROOT):
    return json.loads((root/'config/povo_atmosphere.json').read_text())


def tune_map(source, season='standard', root=ROOT):
    cfg=settings(root);s=cfg[season];inside=cfg['interior'];replacements=[]
    for a,b,c,block in project._entity_ranges(source):
        updated=block
        props={}
        if c=='env_cubemap_fog':
            props=dict(cubemapfogstartdistance=s['fog_start'],cubemapfogenddistance=s['fog_end'],
                       cubemapfogmaxopacity=s['fog_opacity'],cubemapheightfog=0)
        elif c=='env_sky' and s.get('sky_material'):
            props=dict(skyname=s['sky_material'],brightnessscale=1)
        elif c=='light_environment':
            props=dict(brightness=s['sun_brightness'],color=s['sun_color'],
                       skyintensity=s['sky_intensity'],skycolor=s['sky_color'],
                       angulardiameter=4 if season=='winter' else 1.1)
        elif c=='post_processing_volume':
            props=dict(minexposure=inside['exposure_min'],maxexposure=inside['exposure_max'],
                       exposurespeedup=2,exposurespeeddown=2)
        elif c=='light_omni2':
            import re
            p=re.search(r'"origin"\s+"vector3"\s+"([^"]+)"',block)
            garage=p and float(p[1].split()[2])<0
            props=dict(brightness_lumens=inside['garage_lumens'] if garage else inside['light_lumens'],
                       color=inside['light_color'],range=600 if garage else 470)
        elif c=='env_soundscape':
            # Retire the inherited sample ambience; local zones below own audio.
            props=dict(StartDisabled=1,soundevent='Povo.Outside',radius=1)
        for key,value in props.items():updated=set_property(updated,key,value)
        if updated!=block:replacements.append((a,b,updated))
    for a,b,block in reversed(replacements):source=source[:a]+block+source[b:]
    return source


def sound_zones(metadata):
    zones=[]
    def add(name,point,radius,event):zones.append(dict(id=name,point=list(point),radius=radius,event=event))
    for level in metadata['levels']:
        z=level['floor_elevation_metres']-370
        for room in level['rooms']:
            a,b,c,d=room['footprint_local_metres']
            event='Povo.Bathroom' if room.get('kind')=='restroom' else 'Povo.Room'
            add(level['id']+'_'+room['id'],((a+c)/2,(b+d)/2,z+1.4),
                min(480,math.hypot(c-a,d-b)*39.37007874/2+40),event)
        for corridor in level['circulation']:
            a,b,c,d=corridor['bounds']
            e0,e1=-23+b*47,-23+d*47;n0,n1=-103+a*83,-103+c*83
            along_n=(n1-n0)>(e1-e0);length=max(n1-n0,e1-e0)
            count=max(1,math.ceil(length/7))
            for i in range(count):
                point=((e0+e1)/2,n0+(i+.5)*(n1-n0)/count,z+1.4) if along_n else (
                       e0+(i+.5)*(e1-e0)/count,(n0+n1)/2,z+1.4)
                add(f'{level["id"]}_{corridor["id"]}_{i}',point,230,'Povo.Hall')
    for core in metadata.get('stair',{}).get('cores',[]):
        a,b,c,d=core['enclosure']['bounds']
        for floor,z in enumerate((4,7.6)):
            add(f'stair_{core["id"]}_{floor}',((a+c)/2,(b+d)/2,z+1.4),300,'Povo.Hall')
    for n in range(-13,17,7):add('bridge_'+str(n),(18.25,n,9),220,'Povo.Hall')
    for e,n,z in ((18,29,5.4),(18,42,5.4),(18,56,5.4),(18,68,5.4),(41,31.35,5.4),(41,35.65,5.4),
                  (18,20,1.8),(18,9,1.8),(18,-3,1.8),(9,-5,1.8)):
        add(f'p2_{e}_{n}_{z}',(e,n,z),260,'Povo.Hall')
    for e in (-24,0,22):
        for n in (40,66,92):add(f'garage_{e}_{n}',(e,n,-1.6),650,'Povo.Garage')
    for n in range(-105,117,18):add('street_'+str(n),(62,n,7.2 if n<5 else 5.4),650,'Povo.Outside')
    for n in (-90,-65,-45):add('parking_'+str(n),(-48,n,4.4),600,'Povo.Outside')
    return zones


def insert_soundscapes(source,metadata,season):
    for zone in sound_zones(metadata):
        event=zone['event']
        if season=='winter' and event=='Povo.Outside':event='Povo.Winter'
        source=project._insert_point_entity(source,'sound-'+zone['id'],'env_soundscape',
            ' '.join(f'{v:.3f}' for v in world(zone['point'])),
            (('targetname','sound_'+zone['id']),('radius',str(zone['radius'])),('StartDisabled','0'),
             ('soundscape','Nothing'),('enablesoundevent','1'),('soundevent',event)))
    return source


def write_soundevents(root=ROOT):
    base=(root/'data/templates/povo_sound_bases.kv3').read_text().rstrip()
    events={
        'Povo.Vent':dict(base='amb.looping.stereo.base',volume=.045,
                         vsnd_files_track_01='sounds/ambient/common/machines/vent_01.vsnd'),
        'Povo.GarageHum':dict(base='amb.looping.stereo.base',volume=.065,
                              vsnd_files_track_01='sounds/ambient/common/machines/office_garage_vent_01.vsnd'),
        'Povo.Traffic':dict(base='amb.looping.stereo.base',volume=.07,
                            vsnd_files_track_01='sounds/ambient/office/office_outside_traffic_lp_02.vsnd'),
        'Povo.Wind':dict(base='amb.looping.stereo.base',volume=.055,
                         vsnd_files_track_01='sounds/ambient/common/wind/mountain_wind_lp_01.vsnd'),
        'Povo.Door.Move':dict(type='csgo_mega',volume=.45,
                              vsnd_files_track_01='sounds/doors/metal_door_move_01.vsnd'),
        'Povo.Door.Stop':dict(type='csgo_mega',volume=.35,
                              vsnd_files_track_01='sounds/doors/metal_door_full_close_01.vsnd'),
    }
    for name,reverb,children in (
        ('Room','reverb_6_largeRoom',['Povo.Vent']),('Hall','reverb_14_brightHallway',['Povo.Vent']),
        ('Bathroom','reverb_23_smallBathroom',['Povo.Vent']),
        ('Garage','reverb_19_largeConcrete',['Povo.GarageHum']),
        ('Outside','reverb_21_outsideStreet',['Povo.Traffic','Povo.Wind']),
        ('Winter','reverb_22_outsideOpen',['Povo.Traffic','Povo.Wind'])):
        events['Povo.'+name]=dict(base='amb.soundscapeParent.base',enable_child_events=True,
                                dsp_preset=reverb,soundevent_01=children)
    def value(v):
        if isinstance(v,bool):return str(v).lower()
        return json.dumps(v)
    text=base[:-1]+'\n'+''.join('"'+n+'" = {\n'+''.join('  '+k+' = '+value(v)+'\n' for k,v in e.items())+'}\n' for n,e in events.items())+'}\n'
    path=root/'cs2/content/trento_povo/soundevents/soundevents_addon.vsndevts'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return path


def winter_layers(boxes,exterior):
    """Thin outdoor dressing; sheltered/interior floors receive no overlay."""
    snow=[];wet=[]
    # Roof/canopy bounds form vertical blockers. The large building footprints
    # also keep cosmetic aprons from showing through low indoor floors.
    shelters=[((-23,-103,-20),(24,-20,11.4)),((7,10,-20),(25,26,11.4)),
              ((10,19.3,-20),(34.5,71.7,7.5)),((34.5,28.3,-20),(51.3,38.7,7.5)),
              ((24,-76.83,-20),(52,-70.63,10))]
    for name,lo,hi,mat in boxes:
        if ('roof' in name or 'ceiling' in name) and hi[2]>3:
            shelters.append(((lo[0],lo[1],-20),(hi[0],hi[1],hi[2])))
    for name,lo,hi,mat in boxes:
        if not name.startswith('exterior_') or 'underlay' in name:continue
        if any(k in name for k in ('joint','_band','_light','_bar','_frame','_wheel','_mat','_column','_wall','_mass','_trunk')):continue
        cap=any(k in name for k in ('_roof','_crown','_grass','_hedge','context_concrete'))
        ground=mat in ('exterior_paving','exterior_concrete','exterior_tile','exterior_asphalt') and hi[2]<=6.1 and hi[0]-lo[0]>.6 and hi[1]-lo[1]>.6
        if not cap and not ground:continue
        layer=('winter_'+name,(lo[0],lo[1],hi[2]+.002),(hi[0],hi[1],hi[2]+.009),
               'snow_context' if 'context_concrete' in name else 'snow' if cap else 'wet')
        parts=[layer]
        for a,b in shelters:
            if b[2]<=hi[2]+.05:continue
            parts=[p for q in parts for p in subtract_box(q,(a,b))]
        (snow if cap else wet).extend(parts)
    # Snow along the exposed footway edges; the centre remains wet and clear.
    for i,(n0,n1,z) in enumerate(((-110,-13,5.92),(15,112,4.12))):
        for e in (52.04,57.65):
            snow.append((f'winter_footway_edge_{i}_{e}',(e,n0,z+.002),(e+.28,n1,z+.009),'snow'))
    return snow,wet


def write_winter_assets(root,boxes,metadata,render_obj):
    try:
        from .povo_physics_surfaces import write_groups,modeldoc_groups
    except ImportError:
        from povo_physics_surfaces import write_groups,modeldoc_groups
    snow,wet=winter_layers(boxes,metadata.get('exterior',{}));layers=snow+wet
    out=root/'exports/povo_campus/winter';out.mkdir(parents=True,exist_ok=True)
    mesh=render_obj(layers,[])
    (out/'povo_winter.obj').write_text(mesh,encoding='utf-8')
    # Only ground-level films need surface footsteps; high roof/foliage caps
    # stay visual, preserving the original architecture's collision.
    physical=[b for b in layers if b[2][2]<6.2 and 'context_concrete' not in b[0]]
    (out/'povo_winter_collision.obj').write_text(render_obj(physical,[]),encoding='utf-8')
    physical_groups=write_groups(out,'povo_winter',physical)
    colors={'snow':(226,231,234),'snow_context':(205,212,219),'wet':(133,139,140)}
    directory=root/'cs2/content/trento_povo/materials/trento/povo/campus/seasonal';directory.mkdir(parents=True,exist_ok=True)
    for name,color in colors.items():
        (directory/(name+'.png')).write_bytes(png(color,'asphalt'))
        (directory/(name+'_rough.png')).write_bytes(png((220,)*3 if name=='snow' else (105,)*3,'flat',4))
        shader='csgo_unlitgeneric.vfx' if name=='snow_context' else 'csgo_complex.vfx'
        (directory/(name+'.vmat')).write_text('Layer0\n{\n shader "'+shader+'"\n'+
            f' TextureColor "{PREFIX}{name}.png"\n TextureNormal "materials/trento/povo/campus/neutral_normal.png"\n'+
            f' TextureRoughness "{PREFIX}{name}_rough.png"\n'+
            ' SystemAttributes { PhysicsSurfaceProperties "'+('snow' if name.startswith('snow') else 'concrete')+'" }\n}\n')
    model=(root/'cs2/content/trento_povo/models/povo/povo_blockout.vmdl').read_text().replace('povo_blockout','povo_winter')
    marker='\t\t\t\t\t\tremaps =\n\t\t\t\t\t\t['
    remaps=''.join(f'\n {{ from = "campus_{n}" to = "{PREFIX}{n}.vmat" }},' for n in colors)
    model=model.replace(marker,marker+remaps,1)
    model=modeldoc_groups(model,physical_groups)
    (root/'cs2/content/trento_povo/models/povo/povo_winter.vmdl').write_text(model,encoding='utf-8')
    (out/'layers.json').write_text(json.dumps(dict(snow=snow,wet=wet,collision=physical,physics_surface_groups=physical_groups,
        source='P024 light accumulation; wet cleared routes; roofs shelter floors below'),indent=2)+'\n')
    write_snow_particle(root)
    return out


def write_snow_particle(root=ROOT):
    header='<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf54:version{326b1595-45e8-4004-aa5a-3e08655ff51f} -->\n'
    text='''{
 _class = "CParticleSystemDefinition"
 m_nMaxParticles = 512
 m_BoundingBoxMin = [ -300.0, -300.0, -420.0 ]
 m_BoundingBoxMax = [ 300.0, 300.0, 80.0 ]
 m_Renderers = [{ _class = "C_OP_RenderSprites" m_flMaxSize = 0.015
   m_vecTexturesInput = [{ m_hTexture = resource:"materials/particle/smoke1/smoke1.vtex" }]
   m_nOutputBlendMode = "PARTICLE_OUTPUT_BLEND_MODE_ALPHA" }]
 m_Operators = [
   { _class = "C_OP_Decay" },
   { _class = "C_OP_BasicMovement" m_Gravity = [ 1.5, 0.5, -3.0 ] },
   { _class = "C_OP_FadeIn" m_flFadeInTimeMax = 0.15 },
   { _class = "C_OP_FadeOut" m_flFadeOutTimeMax = 0.2 }
 ]
 m_Initializers = [
   { _class = "C_INIT_CreateWithinSphereTransform" m_fRadiusMax = 245.0
     m_vecDistanceBias = [ 1.0, 1.0, 0.0 ]
     m_LocalCoordinateSystemSpeedMin = [ -2.0, -1.0, -65.0 ]
     m_LocalCoordinateSystemSpeedMax = [ 3.0, 1.0, -50.0 ] },
   { _class = "C_INIT_InitFloat" m_nOutputField = 1
     m_InputValue = { m_nType = "PF_TYPE_RANDOM_UNIFORM" m_flRandomMin = 4.0 m_flRandomMax = 5.5 } },
   { _class = "C_INIT_InitFloat" m_nOutputField = 3
     m_InputValue = { m_nType = "PF_TYPE_RANDOM_UNIFORM" m_flRandomMin = 0.45 m_flRandomMax = 1.0 } },
   { _class = "C_INIT_InitFloat" m_nOutputField = 7
     m_InputValue = { m_nType = "PF_TYPE_LITERAL" m_flLiteralValue = 0.6 } },
   { _class = "C_INIT_RtEnvCull" m_bCullOnMiss = true },
   { _class = "C_INIT_RtEnvCull" m_bLifeAdjust = true m_bUseVelocity = true }
 ]
 m_Emitters = [{ _class = "C_OP_ContinuousEmitter"
   m_flEmitRate = { m_nType = "PF_TYPE_LITERAL" m_flLiteralValue = 55.0 } }]
 m_nBehaviorVersion = 5
}
'''
    path=root/'cs2/content/trento_povo/particles/povo/snow.vpcf';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(header+text,encoding='utf-8')


def insert_winter(source,root=ROOT):
    source=project._insert_point_entity(source,'winter-dressing','prop_static','0 0 0',
        (('targetname','povo_winter_dressing'),('model','models/povo/povo_winter.vmdl'),
         ('solid','6'),('bakelighting','1'),('lightmapscalebias','1')),angles='-90 0 0')
    for i,region in enumerate(settings(root)['winter']['snowfall_regions']):
        a,b,c,d=region['bounds'];nx=max(1,math.ceil((c-a)/11));ny=max(1,math.ceil((d-b)/11))
        for x in range(nx):
            for y in range(ny):
                p=(a+(x+.5)*(c-a)/nx,b+(y+.5)*(d-b)/ny,region['floor']+7)
                source=project._insert_point_entity(source,f'winter-snow-{i}-{x}-{y}','info_particle_system',
                    ' '.join(f'{v:.3f}' for v in world(p)),
                    (('effect_name','particles/povo/snow.vpcf'),('start_active','1'),
                     ('targetname',f'winter_snow_{i}_{x}_{y}')))
    return source
