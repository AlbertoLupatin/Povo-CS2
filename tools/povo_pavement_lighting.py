"""Probe-lit finishing surfaces for the campus's thin exterior paving."""
import math

MODEL='povo1_campus_paving'
SURFACE_OFFSET=.003


def surface_obj(obj):
    """Retain pavement tops and exposed edges with a 3 mm finish.

    The offset prevents coplanar flicker. This model has no physics; the
    structural mesh continues to provide the original walking surface.
    """
    tables=[[],[],[]];faces=[];material='';name=''
    for line in obj.splitlines():
        if line.startswith('v '):tables[0].append(tuple(map(float,line.split()[1:])))
        elif line.startswith('vt '):tables[1].append(line[3:])
        elif line.startswith('vn '):tables[2].append(line[3:])
        elif line.startswith('usemtl '):material=line[7:]
        elif line.startswith('o '):name=line[2:]
        elif line.startswith('f '):
            eligible=material in ('campus_exterior_paving','campus_exterior_asphalt')
            eligible|=material=='campus_exterior_concrete' and 'footway' in name
            if not eligible:continue
            refs=[tuple(int(v)-1 for v in r.split('/')) for r in line.split()[1:]]
            a,b,c=[tables[0][r[0]] for r in refs[:3]]
            u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            length=math.sqrt(sum(q*q for q in n))
            # Curbs need their visible vertical risers too. Undersides stay out.
            if length and n[2]>=-.01*length:faces.append((material,refs))
    used=[sorted({r[i] for _,face in faces for r in face}) for i in range(3)]
    indices=[{old:new+1 for new,old in enumerate(ids)} for ids in used]
    vertex_keys=sorted({(r[0],r[2]) for _,face in faces for r in face})
    vertex_indices={key:i+1 for i,key in enumerate(vertex_keys)}
    lines=['# Render-only pavement finish; collision remains in povo1_campus']
    for vertex,normal in vertex_keys:
        p=tables[0][vertex];n=tuple(map(float,tables[2][normal].split()))
        lines.append('v '+' '.join(str(p[i]+SURFACE_OFFSET*n[i]) for i in range(3)))
    for i,prefix in ((1,'vt '),(2,'vn ')):
        for old in used[i]:
            value=tables[i][old]
            lines.append(prefix+value)
    lines.append('o pavement_probe_finish');last=None
    for material,face in faces:
        if material!=last:lines.append('usemtl '+material);last=material
        lines.append('f '+' '.join(f'{vertex_indices[(r[0],r[2])]}/{indices[1][r[1]]}/{indices[2][r[2]]}' for r in face))
    return '\n'.join(lines)+'\n'


def write_assets(obj,root):
    output=root/'exports/povo_campus';modeldir=root/'cs2/content/trento_povo/models/povo'
    (output/(MODEL+'.obj')).write_text(surface_obj(obj),encoding='utf-8')
    header=(modeldir/'povo_blockout.vmdl').read_text().splitlines()[0]
    remaps='\n'.join('{ from = "campus_exterior_'+m+'" to = "materials/trento/povo/campus/exterior/'+m+'.vmat" },'
                     for m in ('paving','asphalt','concrete'))
    model=header+'\n{ rootNode = { _class = "RootNode" children = [\n'+\
        '{ _class = "MaterialGroupList" children = [{ _class = "DefaultMaterialGroup" remaps = [\n'+remaps+\
        '\n] }] },\n{ _class = "RenderMeshList" children = [{ _class = "RenderMeshFile" name = "pavement" '+\
        'filename = "models/povo/'+MODEL+'.obj" import_scale = 39.37007874 }] }\n] } }\n'
    (modeldir/(MODEL+'.vmdl')).write_text(model,encoding='utf-8')


def insert_surface(source):
    try:
        from . import cs2_project as project
    except ImportError:
        import cs2_project as project
    model='models/povo/'+MODEL+'.vmdl'
    source=project._ensure_map_asset_reference(source,model)
    return project._insert_point_entity(source,'pavement-probe-finish','prop_static','0 0 0',
        (('targetname','povo_pavement_finish'),('model',model),('solid','0'),('bakelighting','0'),
         ('precomputelightprobes','1'),('disableshadows','1')),angles='-90 0 0')
