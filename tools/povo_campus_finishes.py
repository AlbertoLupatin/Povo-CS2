"""Original, deterministic finish maps for the photo-guided campus interior."""

import math
import struct
import zlib


def png(color, pattern='plain', size=256):
    def pixel(x, y):
        # Small, stable variation avoids the conspicuous repeating noise of a
        # generic default material. No pixels from reference photos are used.
        noise = ((x * 73856093 ^ y * 19349663) & 255) / 255
        offset = (noise - .5) * 2
        if pattern == 'terrazzo':
            offset = (noise - .5) * 9
            if noise > .95:
                offset += 15
            elif noise < .045:
                offset -= 18
            if x < 2 or y < 2:
                offset -= 14
        elif pattern == 'tile':
            offset = (noise-.5)*3
            if x < 3 or y < 3:
                offset -= 42
        elif pattern == 'asphalt':
            offset = (noise-.5)*13
        elif pattern == 'wood':
            board = x // 64
            offset += 3 * math.sin(x * .7 + math.sin(y * .035))
            offset += (board % 3 - 1) * 4
            if x % 64 < 1 or (y + (board % 2) * 128) % 256 < 1:
                offset -= 17
        elif pattern == 'ceiling':
            if x < 3 or y < 3:
                offset -= 30
            elif x % 5 == 2 and y % 5 == 2:
                offset -= 8
        elif pattern == 'perforated':
            if (x % 12 - 6) ** 2 + (y % 12 - 6) ** 2 < 5:
                offset -= 25
        elif pattern == 'grating':
            # Open steel grating: dark gaps between 4 px bars.
            offset = (noise-.5)*4
            if x % 16 > 3 and y % 6 > 1:
                offset -= 70
        elif pattern == 'flat':
            offset = 0
        return bytes(round(max(0, min(255, c + offset))) for c in color)

    raw = b''.join(b'\0' + b''.join(pixel(x, y) for x in range(size)) for y in range(size))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def write_materials(directory, prefix, colors):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'neutral_normal.png').write_bytes(png((128, 128, 255), 'flat', 4))
    for name, color in colors.items():
        pattern = {'floor_circulation': 'terrazzo', 'floor_room': 'terrazzo',
                   'floor_wood': 'wood', 'seat_wood': 'wood',
                   'ceiling_panel': 'ceiling', 'desk_panel': 'perforated',
                   'floor_p2_tile': 'tile', 'floor_p2_asphalt': 'asphalt',
                   'floor_terrace': 'tile', 'floor_grating': 'grating'}.get(name, 'plain')
        (directory / (name + '.png')).write_bytes(png(color, pattern))
        roughness = 215 if name in ('wall', 'ceiling_panel', 'courtyard_wall') else 175
        if name in ('metal_dark', 'window_frame', 'floor_grating'):
            roughness = 135
        (directory / (name + '_rough.png')).write_bytes(png((roughness,) * 3, 'flat', 4))
        surface = ('wood' if name in ('floor_wood', 'seat_wood', 'seat_green', 'desk_dark', 'desk_panel')
                   else 'metal' if name in ('metal_dark', 'window_frame', 'floor_grating')
                   else 'asphalt' if name == 'floor_p2_asphalt'
                   else 'tile' if name in ('floor_room','floor_circulation','floor_p2_tile','floor_terrace')
                   else 'metal' if name in ('stair_red','stair_nosing','door_black','door_pushbar') else 'concrete')
        if name in ('window_glass','reception_glass'):
            # Deliberately tinted panes remain readable from indoors and out.
            # Use the same tested translucent shader as the entrance banks.
            (directory/'glass_mask.png').write_bytes(png((255,255,255),'flat',4))
            opacity=.32 if name=='window_glass' else .60
            text=(f'Layer0\n{{\n    shader "csgo_lightmappedgeneric.vfx"\n'
                  '    F_TRANSLUCENT "1"\n    F_RENDER_BACKFACES "1"\n'
                  f'    g_flOpacityScale "{opacity}"\n'
                  f'    TextureLayer1Color "{prefix}{name}.png"\n'
                  f'    TextureLayer1Normal "{prefix}neutral_normal.png"\n'
                  f'    TextureLayer1Roughness "{prefix}{name}_rough.png"\n'
                  f'    TextureLayer1Translucency "{prefix}glass_mask.png"\n'
                  '    g_vColorTint "[1 1 1 0]"\n'
                  '    SystemAttributes { PhysicsSurfaceProperties "glass" }\n}\n')
            (directory/(name+'.vmat')).write_text(text,encoding='utf-8')
            continue
        text = (f'Layer0\n{{\n    shader "csgo_complex.vfx"\n'
                f'    TextureColor "{prefix}{name}.png"\n'
                f'    TextureNormal "{prefix}neutral_normal.png"\n'
                f'    TextureRoughness "{prefix}{name}_rough.png"\n'
                '    g_vColorTint "[1 1 1 0]"\n    g_flModelTintAmount "1"\n'
                f'    SystemAttributes {{ PhysicsSurfaceProperties "{surface}" }}\n}}\n')
        (directory / (name + '.vmat')).write_text(text, encoding='utf-8')
