"""Restore frontage lamp assemblies after the final building/yard excavations."""
import re


def repair_frontage_lamps(boxes,levels):
    # Posts 5/6 are obsolete: the aula now occupies their registered positions.
    # Keep the other heads, and rebuild 0/1 down to the actual surviving paving.
    result=[b for b in boxes if not re.match(
        r'exterior_povo2_front_lamp_(?:head_)?[56](?:_|$)',b[0])]
    for i in (0,1):
        name=f'exterior_povo2_front_lamp_{i}'
        parts=[b for b in result if b[0]==name or b[0].startswith(name+'_windowcut_')]
        if not parts:raise ValueError('Missing frontage lamp '+name)
        lo=tuple(min(b[1][k] for b in parts) for k in range(3))
        hi=tuple(max(b[2][k] for b in parts) for k in range(3))
        x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
        supports=[top[2] for _,bottom,top,material in result
                  if material in ('exterior_paving','exterior_concrete','floor_terrace')
                  and bottom[0]<=x<=top[0] and bottom[1]<=y<=top[1]
                  and 3.7<=top[2]<=4.3]
        if not supports:raise ValueError('No paving under frontage lamp '+name)
        floor=max(supports)
        result=[b for b in result if b[0]!=name and not b[0].startswith(name+'_windowcut_')]
        result.append((name,(lo[0],lo[1],floor),hi,parts[0][3]))
    return result
