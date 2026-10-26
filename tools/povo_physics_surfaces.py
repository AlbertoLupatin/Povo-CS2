"""ModelDoc collision groups with explicit, native physical surface properties.

Material tags on a render mesh do not override PhysicsMeshFile.surface_prop.
Each group therefore gets its own collision OBJ and explicit ModelDoc surface.
"""
import io
import re

try:
    from .build_povo_blockout import write_box
    from .cs2_project import _matching_brace
except ImportError:
    from build_povo_blockout import write_box
    from cs2_project import _matching_brace


def surface(material):
    if material.startswith('exterior_'):
        m=material.removeprefix('exterior_')
        return ('glass' if m in ('entry_glass','canopy_glass','glass') else
                'asphalt' if m=='asphalt' else 'tile' if m=='tile' else
                'metal' if m in ('fence','dark') else 'grass' if m in ('grass','tree') else
                'wood' if m=='trunk' else 'concrete')
    return ('snow' if material=='snow' else 'concrete' if material=='wet' else
            'tile' if material in ('floor_room','floor_circulation','floor_p2_tile') else
            'wood' if material in ('floor_wood','seat_wood','desk_dark','desk_panel') else
            'metal' if material in ('metal_dark','window_frame','stair_red','stair_nosing','door_black','door_pushbar') else
            'asphalt' if material=='floor_p2_asphalt' else
            'grass' if material=='courtyard_ground' else
            'glass' if material in ('window_glass','reception_glass') else 'concrete')


def write_groups(output,stem,boxes,meshes=()):
    groups=sorted({surface(b[3]) for b in boxes}|{surface(m['material']) for m in meshes})
    results={}
    for material in groups:
        selected=[b for b in boxes if surface(b[3])==material]
        selected_meshes=[m for m in meshes if surface(m['material'])==material]
        stream=io.StringIO();offset=0
        for index,(name,lo,hi,mat) in enumerate(selected):
            if index%64==0:stream.write(f'o physics_{material}_{index//64}\n')
            part=io.StringIO();write_box(part,name,lo,hi,offset,'campus_'+mat)
            for line in part.getvalue().splitlines():
                if not line.startswith('o '):stream.write(line+'\n')
            offset+=8
        for mesh in selected_meshes:
            stream.write('o '+mesh['name']+'\nusemtl campus_'+mesh['material']+'\n')
            for v in mesh['vertices']:stream.write('v '+' '.join(f'{x:.12g}' for x in v)+'\n')
            for f in mesh['faces']:stream.write('f '+' '.join(str(offset+i+1) for i in f)+'\n')
            offset+=len(mesh['vertices'])
        path=output/(stem+'_collision_'+material+'.obj')
        path.write_text(stream.getvalue(),encoding='utf-8')
        results[material]=dict(file=path.name,boxes=len(selected),meshes=len(selected_meshes))
    return results


def modeldoc_groups(model,groups):
    at=model.index('_class = "PhysicsMeshFile"');a=model.rfind('{',0,at);b=_matching_brace(model,a)
    template=model[a:b+1]
    nodes=[]
    for material,spec in groups.items():
        node=re.sub(r'(surface_prop\s*=\s*)"[^"]*"',lambda m:m[1]+'"'+material+'"',template)
        node=re.sub(r'(filename\s*=\s*)"[^"]*"',lambda m:m[1]+'"models/povo/'+spec['file']+'"',node)
        node=re.sub(r'(name\s*=\s*)"[^"]*"',lambda m:m[1]+'"physics_'+material+'"',node,count=1)
        nodes.append(node)
    return model[:a]+',\n'.join(nodes)+model[b+1:]
