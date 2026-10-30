"""Exterior palette, explicit door opacity and isolated CS2 material sources."""
COLORS = {
    'bus_paint': (218,224,215), 'bus_rust': (113,65,43), 'bus_glass': (27,45,49),
    'bus_green': (92,153,53), 'bus_lime': (146,193,66),
    'bus_metal': (147,157,156), 'bus_led': (246,205,102),
    'bus_seat': (73,87,69), 'bus_floor': (78,75,65),
    'asphalt': (91,94,95), 'paving': (167,163,151), 'marking': (229,229,215),
    'fbk_blue': (82,139,181), 'fbk_window': (48,78,99),
    'grass': (100,121,78), 'concrete': (159,160,151), 'fence': (139,152,155),
    'stone': (183,175,150), 'glass': (71,103,111), 'entry_glass': (96,126,133),
    'dark': (49,59,64), 'white': (217,215,203), 'residential_grey': (132,143,149),
    'orange': (159,70,46), 'car_blue': (55,72,87), 'car_white': (207,210,208),
    'car_red': (149,48,42), 'tree': (59,88,62), 'trunk': (94,82,66),
    'ginkgo_leaf': (103,143,58), 'ginkgo_leaf_light': (137,166,72), 'ginkgo_leaf_dark': (71,112,45),
    'ridge': (106,124,134), 'tile': (191,188,166), 'grout': (136,137,125),
    'light': (245,237,190), 'canopy_glass': (135,171,180), 'context_concrete': (159,160,151)
}
# 20% transmission, 80% opacity, per pane. Frames and safety bands stay opaque.
OPACITY = {'glass': .32, 'entry_glass': .84, 'canopy_glass': .40}
PREFIX = 'materials/trento/povo/campus/exterior/'


def write_materials(directory):
    try:
        from .povo_campus_finishes import png, write_png
    except ImportError:
        from povo_campus_finishes import png, write_png
    directory.mkdir(parents=True,exist_ok=True)
    write_png(directory/'neutral_normal.png', png((128,128,255),'flat',4))
    write_png(directory/'opaque_mask.png', png((255,255,255),'flat',4))
    for name,color in COLORS.items():
        pattern='asphalt' if name=='asphalt' else 'plain'
        write_png(directory/(name+'.png'), png(color,pattern,64))
        write_png(directory/(name+'_rough.png'), png((185,)*3,'flat',4))
        transparent=name in OPACITY
        shader=('csgo_lightmappedgeneric.vfx' if transparent else
                'csgo_unlitgeneric.vfx' if name in ('context_concrete','bus_led') else 'csgo_complex.vfx')
        flags=('    F_TRANSLUCENT "1"\n    F_RENDER_BACKFACES "1"\n'
               f'    g_flOpacityScale "{OPACITY[name]}"\n') if transparent else ''
        if name.startswith('ginkgo_leaf'):flags+='    F_RENDER_BACKFACES "1"\n'
        layer='Layer1' if transparent else ''
        textures=(f'    Texture{layer}Color "{PREFIX}{name}.png"\n'
                  f'    Texture{layer}Normal "{PREFIX}neutral_normal.png"\n'
                  f'    Texture{layer}Roughness "{PREFIX}{name}_rough.png"\n')
        if transparent:textures+=f'    TextureLayer1Translucency "{PREFIX}opaque_mask.png"\n'
        surface=('glass' if transparent else 'asphalt' if name=='asphalt' else
                 'tile' if name=='tile' else 'metal' if name in ('fence','dark','fbk_blue') or name.startswith('bus_') else
                 'grass' if name in ('grass','tree') or name.startswith('ginkgo_leaf') else 'wood' if name=='trunk' else 'concrete')
        text=(f'Layer0\n{{\n    shader "{shader}"\n'+flags+textures+
              '    g_vColorTint "[1 1 1 0]"\n    g_flModelTintAmount "1"\n'
              '    SystemAttributes { PhysicsSurfaceProperties "'+surface+'" }\n}\n')
        (directory/(name+'.vmat')).write_text(text,encoding='utf-8')
