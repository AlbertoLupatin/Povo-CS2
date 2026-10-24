"""Exterior palette, explicit door opacity and isolated CS2 material sources."""
COLORS = {
    'asphalt': (91,94,95), 'paving': (167,163,151), 'marking': (229,229,215),
    'grass': (100,121,78), 'concrete': (159,160,151), 'fence': (139,152,155),
    'stone': (183,175,150), 'glass': (71,103,111), 'entry_glass': (96,126,133),
    'dark': (49,59,64), 'white': (217,215,203), 'residential_grey': (132,143,149),
    'orange': (159,70,46), 'car_blue': (55,72,87), 'car_white': (207,210,208),
    'car_red': (149,48,42), 'tree': (59,88,62), 'trunk': (94,82,66),
    'ridge': (106,124,134), 'tile': (191,188,166), 'grout': (136,137,125),
    'light': (245,237,190)
}
# 20% transmission, 80% opacity, per pane. Frames and safety bands stay opaque.
OPACITY = {'entry_glass': .8}
PREFIX = 'materials/trento/povo/campus/exterior/'


def write_materials(directory):
    try:
        from .povo_campus_finishes import png
    except ImportError:
        from povo_campus_finishes import png
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'neutral_normal.png').write_bytes(png((128,128,255),'flat',4))
    (directory/'opaque_mask.png').write_bytes(png((255,255,255),'flat',4))
    for name,color in COLORS.items():
        pattern='asphalt' if name=='asphalt' else 'plain'
        (directory/(name+'.png')).write_bytes(png(color,pattern,64))
        (directory/(name+'_rough.png')).write_bytes(png((185,)*3,'flat',4))
        transparent=name in OPACITY
        shader='csgo_lightmappedgeneric.vfx' if transparent else 'csgo_complex.vfx'
        flags=('    F_TRANSLUCENT "1"\n    F_RENDER_BACKFACES "0"\n'
               f'    g_flOpacityScale "{OPACITY[name]}"\n') if transparent else ''
        layer='Layer1' if transparent else ''
        textures=(f'    Texture{layer}Color "{PREFIX}{name}.png"\n'
                  f'    Texture{layer}Normal "{PREFIX}neutral_normal.png"\n'
                  f'    Texture{layer}Roughness "{PREFIX}{name}_rough.png"\n')
        if transparent:textures+=f'    TextureLayer1Translucency "{PREFIX}opaque_mask.png"\n'
        text=(f'Layer0\n{{\n    shader "{shader}"\n'+flags+textures+
              '    g_vColorTint "[1 1 1 0]"\n    g_flModelTintAmount "1"\n'
              '    SystemAttributes { PhysicsSurfaceProperties "'+('glass' if transparent else 'concrete')+'" }\n}\n')
        (directory/(name+'.vmat')).write_text(text,encoding='utf-8')
