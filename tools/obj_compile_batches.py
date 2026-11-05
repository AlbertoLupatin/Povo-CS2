"""Rebatch OBJ faces for import without changing attributes or face assignments.

OBJ object/group names carry no transforms. Static ModelDoc inputs with no
object-name filters can therefore use fewer, bounded objects while retaining
the exact vertex, UV, normal, face, material and smoothing data. This is an
opt-in compiler input transformation, not a geometry simplifier. Face-value
equivalence does not prove native welding or lightmap-chart equivalence. Render
partition helpers are experimental: the production optimized campus build keeps
one render input with all shared indices and partitions whole collision objects.
"""
from pathlib import Path
import hashlib
import json
import re
import time


def geometry_signature(path):
    digest = hashlib.sha256()
    material = ''
    smoothing = ''
    counts = dict(vertices=0, uvs=0, normals=0, faces=0, objects=0)
    with Path(path).open(encoding='utf-8') as source:
        for line in source:
            value = line.strip()
            token = value.split(maxsplit=1)[0] if value else ''
            if token in ('v', 'vt', 'vn'):
                digest.update((value + '\n').encode())
                counts[{'v': 'vertices', 'vt': 'uvs', 'vn': 'normals'}[token]] += 1
            elif token == 'usemtl':
                material = value.partition(' ')[2].strip()
            elif token == 's':
                smoothing = value.partition(' ')[2].strip()
            elif token == 'f':
                digest.update(('face\0' + material + '\0' + smoothing + '\0' + value + '\n').encode())
                counts['faces'] += 1
            elif token == 'o':
                counts['objects'] += 1
    return dict(sha256=digest.hexdigest(), **counts)


def rebatch_obj(source, destination, *, faces_per_object=4096, corners_per_object=32768):
    """Keep face order and indices; coalesce redundant object/material changes."""
    if faces_per_object < 1 or corners_per_object < 3:
        raise ValueError('Positive face capacity and at least three corners required')
    source, destination = Path(source), Path(destination)
    before = geometry_signature(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + '.partial')
    material = smoothing = ''
    emitted_material = None
    group_faces = group_corners = number = 0
    started = time.monotonic()
    try:
        with source.open(encoding='utf-8') as incoming, temporary.open('w', encoding='utf-8', newline='\n') as output:
            for line in incoming:
                value = line.strip()
                token = value.split(maxsplit=1)[0] if value else ''
                if token in ('o', 'g'):
                    continue
                if token == 'usemtl':
                    material = value.partition(' ')[2].strip()
                    continue
                if token == 's':
                    smoothing = value.partition(' ')[2].strip()
                if token == 'f':
                    corners = len(value.split()) - 1
                    if corners > corners_per_object:
                        raise ValueError('A single polygon exceeds the configured corner capacity')
                    if not number or material != emitted_material or group_faces >= faces_per_object or group_corners + corners > corners_per_object:
                        output.write(f'o compile_batch_{number:05d}\n')
                        number += 1
                        group_faces = group_corners = 0
                        emitted_material = material
                        if material:
                            output.write('usemtl ' + material + '\n')
                        if smoothing:
                            output.write('s ' + smoothing + '\n')
                    group_faces += 1
                    group_corners += corners
                output.write(line.rstrip('\r\n') + '\n')
        after = geometry_signature(temporary)
        if {k: v for k, v in before.items() if k != 'objects'} != {k: v for k, v in after.items() if k != 'objects'}:
            raise ValueError('OBJ geometry/material/smoothing equivalence check failed')
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return dict(before=before, after=after, seconds=time.monotonic() - started,
                faces_per_object=faces_per_object, corners_per_object=corners_per_object)


def _faces(path, tables, *, with_objects=False):
    material = smoothing = ''
    object_id = 0
    with Path(path).open(encoding='utf-8') as incoming:
        for line in incoming:
            fields = line.split()
            if not fields:
                continue
            token = fields[0]
            if token in tables:
                tables[token].append(' '.join(fields[1:]))
            elif token == 'o':
                object_id += 1
            elif token == 'usemtl':
                material = ' '.join(fields[1:])
            elif token == 's':
                smoothing = ' '.join(fields[1:])
            elif token == 'mtllib':
                raise ValueError('External MTL libraries require explicit handling; generated campus OBJs have none')
            elif token == 'f':
                corners = []
                for corner in fields[1:]:
                    values = corner.split('/')
                    indices = []
                    for index, kind in enumerate(('v', 'vt', 'vn')):
                        raw = values[index] if index < len(values) else ''
                        if not raw:
                            indices.append(None)
                            continue
                        value = int(raw)
                        resolved = value - 1 if value > 0 else len(tables[kind]) + value
                        if value == 0 or not 0 <= resolved < len(tables[kind]):
                            raise ValueError('Face references an undefined OBJ attribute')
                        indices.append(resolved)
                    if indices[0] is None:
                        raise ValueError('Face corner has no position')
                    corners.append(tuple(indices))
                if smoothing not in ('', 'off', '0') and any(c[2] is None for c in corners):
                    raise ValueError('Cannot split smooth faces without explicit normals')
                face = material, smoothing, corners
                yield (object_id, face) if with_objects else face


def _hash_face(digest, face, tables):
    material, smoothing, corners = face
    digest.update(('face\0' + material + '\0' + smoothing + '\0').encode())
    for corner in corners:
        for kind, index in zip(('v', 'vt', 'vn'), corner):
            digest.update((kind + '\0' + (tables[kind][index] if index is not None else '<absent>') + '\0').encode())
    digest.update(b'\n')


def surface_signature(paths, *, include_material=True):
    """Hash ordered surface corners by values, independent of OBJ reindexing."""
    digest = hashlib.sha256()
    count = 0
    for path in paths:
        tables = {kind: [] for kind in ('v', 'vt', 'vn')}
        for face in _faces(path, tables):
            if not include_material:
                face = ('', face[1], face[2])
            _hash_face(digest, face, tables)
            count += 1
    return dict(sha256=digest.hexdigest(), faces=count)


def coalesce_collision_obj(path, *, surface_prop):
    """Keep collision triangles; use one import group for an explicit surface.

    PhysicsMeshFile.surface_prop controls the entire input's physical surface;
    render-material changes in that OBJ do not assign physical surface types.
    Repeated usemtl directives cause the importer to create thousands of names.
    """
    if not surface_prop:
        raise ValueError('An explicit whole-file physical surface is required')
    path = Path(path)
    before = surface_signature([path], include_material=False)
    temporary = path.with_suffix('.obj.coalesced')
    first_material = None
    emitted = False
    removed_material_changes = 0
    with path.open(encoding='utf-8') as source, temporary.open('w', encoding='utf-8', newline='\n') as output:
        for line in source:
            fields = line.split(maxsplit=1)
            token = fields[0] if fields else ''
            if token in ('o', 'g'):
                continue
            if token == 'usemtl':
                first_material = first_material or fields[1].strip()
                removed_material_changes += 1
                continue
            if token == 'f' and not emitted:
                output.write('o collision_surface\n')
                if first_material:
                    output.write('usemtl ' + first_material + '\n')
                emitted = True
            output.write(line.rstrip('\r\n') + '\n')
    after = surface_signature([temporary], include_material=False)
    if after != before:
        temporary.unlink()
        raise ValueError('Collision surface geometry changed')
    temporary.replace(path)
    return dict(surface_prop=surface_prop, signature=before,
                original_material_directives=removed_material_changes,
                import_groups=1 if emitted else 0)


def coalesce_model_collision(content, model):
    """Process each PhysicsMeshFile using its existing, unchanged surface_prop."""
    content, model = Path(content), Path(model)
    text = model.read_text(encoding='utf-8')
    reports = {}
    for match in re.finditer(r'_class\s*=\s*"PhysicsMeshFile"', text):
        opening = text.rfind('{', 0, match.start())
        block = text[opening:_block_end(text, opening)]
        filename = re.search(r'filename\s*=\s*"([^"]+)"', block)[1]
        surface = re.search(r'surface_prop\s*=\s*"([^"]+)"', block)[1]
        if filename in reports:
            raise ValueError('A collision source is shared by multiple ModelDoc nodes')
        reports[filename] = coalesce_collision_obj(content / filename, surface_prop=surface)
    if not reports:
        raise ValueError('No explicit PhysicsMeshFile surface nodes found')
    if model.read_text(encoding='utf-8') != text:
        raise ValueError('Physics ModelDoc configuration changed')
    return reports


def _write_part(path, faces, tables, *, object_names=None):
    indices = {kind: {} for kind in ('v', 'vt', 'vn')}
    for _material, _smoothing, corners in faces:
        for corner in corners:
            for kind, index in zip(('v', 'vt', 'vn'), corner):
                if index is not None:
                    indices[kind].setdefault(index, len(indices[kind]) + 1)
    with path.open('w', encoding='utf-8', newline='\n') as output:
        output.write('# Campus compiler partition; original coordinates and corner attributes\n')
        for kind, remap in indices.items():
            for index in remap:
                output.write(kind + ' ' + tables[kind][index] + '\n')
        last = None
        objects = 0
        used = 0
        for face_number, (material, smoothing, corners) in enumerate(faces):
            name = object_names[face_number] if object_names is not None else None
            state = name, material, smoothing
            if state != last or (object_names is None and used >= 4096):
                output.write('o ' + (name if name is not None else f'mesh_{objects:04d}') + '\n')
                objects += 1
                used = 0
                if material:
                    output.write('usemtl ' + material + '\n')
                if smoothing:
                    output.write('s ' + smoothing + '\n')
                last = state
            values = []
            for corner in corners:
                values.append('/'.join(str(indices[kind][index]) if index is not None else '' for kind, index in zip(('v', 'vt', 'vn'), corner)).rstrip('/'))
            output.write('f ' + ' '.join(values) + '\n')
            used += 1
    return objects


def split_obj(source, output_directory, *, stem=None, faces_per_part=32768):
    """Partition faces and compact each file's index tables; verify every corner."""
    if faces_per_part < 1:
        raise ValueError('faces_per_part must be positive')
    source, output_directory = Path(source), Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    stem = stem or source.stem
    tables = {kind: [] for kind in ('v', 'vt', 'vn')}
    digest = hashlib.sha256()
    paths = []
    pending = []
    count = objects = 0
    started = time.monotonic()
    for face in _faces(source, tables):
        _hash_face(digest, face, tables)
        pending.append(face)
        count += 1
        if len(pending) == faces_per_part:
            path = output_directory / f'{stem}_part{len(paths):03d}.obj'
            objects += _write_part(path, pending, tables)
            paths.append(path)
            pending = []
    if pending:
        path = output_directory / f'{stem}_part{len(paths):03d}.obj'
        objects += _write_part(path, pending, tables)
        paths.append(path)
    expected = dict(sha256=digest.hexdigest(), faces=count)
    actual = surface_signature(paths)
    if actual != expected:
        raise ValueError('Partitioned OBJ surfaces differ from the source')
    return dict(source=str(source), parts=[str(p) for p in paths], signature=expected,
                output_objects=objects, seconds=time.monotonic() - started)


def split_obj_materials(source):
    """Keep all faces of each material together, retaining original object names."""
    source = Path(source)
    started = time.monotonic()
    names = ['default']
    with source.open(encoding='utf8') as stream:
        for line in stream:
            fields = line.split(maxsplit=1)
            if fields and fields[0] == 'o':
                names.append(fields[1].strip())
    tables = {kind: [] for kind in ('v', 'vt', 'vn')}
    groups = {}
    digests = {}
    counts = {}
    for object_id, face in _faces(source, tables, with_objects=True):
        material = face[0]
        groups.setdefault(material, []).append((object_id, face))
        _hash_face(digests.setdefault(material, hashlib.sha256()), face, tables)
        counts[material] = counts.get(material, 0) + 1
    if not groups:
        raise ValueError('Render input has no faces')
    reports = {}
    paths = []
    for material, items in groups.items():
        path = source.with_name(f'{source.stem}_material{len(paths):03d}.obj')
        _write_part(path, [face for _, face in items], tables,
                    object_names=[names[index] for index, _ in items])
        expected = dict(sha256=digests[material].hexdigest(), faces=counts[material])
        if surface_signature([path]) != expected:
            raise ValueError('Material partition changed face corners or assignments')
        reports[material] = expected
        paths.append(str(path))
    return dict(source=str(source), parts=paths, materials=reports,
                faces=sum(counts.values()), partitioning='whole_material',
                original_object_names_preserved=True, seconds=time.monotonic() - started)


def _block_end(text, opening):
    depth = 0
    quoted = escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError('Unterminated ModelDoc block')


def split_render_model(content, model, *, faces_per_part=32768):
    """Replace one unfiltered render input with exact partitions; keep physics."""
    return _split_render_input(content, model, lambda source: split_obj(source, source.parent, faces_per_part=faces_per_part))


def split_render_materials_model(content, model):
    """Partition render imports by whole material without cutting its surfaces."""
    return _split_render_input(content, model, split_obj_materials)


def rebatch_render_model(content, model):
    """Keep one render file and all shared indices; reduce importer group count."""
    content, model = Path(content), Path(model)
    text = model.read_text(encoding='utf8')
    matches = list(re.finditer(r'_class\s*=\s*"RenderMeshFile"', text))
    if len(matches) != 1:
        raise ValueError('Expected exactly one RenderMeshFile')
    opening = text.rfind('{', 0, matches[0].start())
    template = text[opening:_block_end(text, opening)]
    if re.search(r'exclude_by_default\s*=\s*true', template) or not re.search(r'exception_list\s*=\s*\[\s*\]', template):
        raise ValueError('Cannot rebatch object-name filtered render input')
    source = content / re.search(r'filename\s*=\s*"([^"]+)"', template)[1]
    with source.open(encoding='utf8') as stream:
        for line in stream:
            fields = line.split()
            if fields and fields[0] == 'f' and any(len(ref.split('/')) != 3 or not ref.split('/')[2] for ref in fields[1:]):
                raise ValueError('Render rebatching requires explicit corner normals')
    report = rebatch_obj(source, source)
    if model.read_text(encoding='utf8') != text:
        raise ValueError('Render ModelDoc changed during rebatching')
    report.update(partitioned=False, shared_indices_preserved=True,
                  modeldoc_sha256=hashlib.sha256(text.encode()).hexdigest())
    return report


def _split_render_input(content, model, partitioner):
    content, model = Path(content), Path(model)
    text = model.read_text(encoding='utf-8')
    matches = list(re.finditer(r'_class\s*=\s*"RenderMeshFile"', text))
    if len(matches) != 1:
        raise ValueError('Expected exactly one RenderMeshFile')
    opening = text.rfind('{', 0, matches[0].start())
    end = _block_end(text, opening)
    template = text[opening:end]
    if re.search(r'exclude_by_default\s*=\s*true', template) or not re.search(r'exception_list\s*=\s*\[\s*\]', template):
        raise ValueError('Object-name import filters cannot be preserved by repartitioning')
    filename = re.search(r'filename\s*=\s*"([^"]+)"', template)[1]
    source = content / filename
    report = partitioner(source)
    nodes = []
    for number, part in enumerate(report['parts']):
        relative = Path(part).relative_to(content).as_posix()
        node = re.sub(r'(\bfilename\s*=\s*)"[^"]+"', lambda m: m[1] + '"' + relative + '"', template, count=1)
        node = re.sub(r'(\bname\s*=\s*)"[^"]*"', lambda m: m[1] + '"compile_part_' + str(number) + '"', node, count=1)
        nodes.append(node)
    updated = text[:opening] + ',\n'.join(nodes) + text[end:]
    model.write_text(updated, encoding='utf-8')
    report['original_modeldoc_sha256'] = hashlib.sha256(text.encode()).hexdigest()
    report['partitioned_modeldoc_sha256'] = hashlib.sha256(updated.encode()).hexdigest()
    report['physics_unchanged'] = True  # Only the single RenderMeshFile block above is replaced.
    return report


def split_collision_objects(source):
    """Keep each original object intact, with no shared vertices across parts."""
    source = Path(source)
    tables = {kind: [] for kind in ('v', 'vt', 'vn')}
    paths = []
    pending = []
    current = None
    owners = {}
    expected = hashlib.sha256()
    count = 0
    for object_id, face in _faces(source, tables, with_objects=True):
        for vertex, _uv, _normal in face[2]:
            if vertex in owners and owners[vertex] != object_id:
                raise ValueError('Collision objects share vertices; refusing to cut connected geometry')
            owners[vertex] = object_id
        if current is not None and object_id != current and pending:
            path = source.with_name(f'{source.stem}_part{len(paths):03d}.obj')
            _write_part(path, pending, tables)
            paths.append(path)
            pending = []
        current = object_id
        _hash_face(expected, face, tables)
        count += 1
        pending.append(face)
    if pending:
        path = source.with_name(f'{source.stem}_part{len(paths):03d}.obj')
        _write_part(path, pending, tables)
        paths.append(path)
    signature = dict(sha256=expected.hexdigest(), faces=count)
    if surface_signature(paths) != signature:
        raise ValueError('Partitioned collision geometry or face assignments changed')
    return dict(parts=[str(p) for p in paths], signature=signature, connected_objects_preserved=True)


def split_model_collision(content, model):
    """Clone physics nodes for intact source objects, retaining all node options."""
    content, model = Path(content), Path(model)
    text = model.read_text(encoding='utf-8')
    replacements = []
    reports = {}
    for match in re.finditer(r'_class\s*=\s*"PhysicsMeshFile"', text):
        opening = text.rfind('{', 0, match.start())
        end = _block_end(text, opening)
        template = text[opening:end]
        if re.search(r'exclude_by_default\s*=\s*true', template) or not re.search(r'exception_list\s*=\s*\[\s*\]', template):
            raise ValueError('Filtered collision objects require explicit handling')
        filename = re.search(r'filename\s*=\s*"([^"]+)"', template)[1]
        surface = re.search(r'surface_prop\s*=\s*"([^"]+)"', template)[1]
        if filename in reports:
            raise ValueError('Shared collision sources require explicit handling')
        source = content / filename
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        report = split_collision_objects(source)
        if hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
            raise ValueError('Original collision source changed')
        report.update(surface_prop=surface, source_sha256=original_hash)
        reports[filename] = report
        nodes = []
        for number, part in enumerate(report['parts']):
            relative = Path(part).relative_to(content).as_posix()
            node = re.sub(r'(\bfilename\s*=\s*)"[^"]+"', lambda m: m[1] + '"' + relative + '"', template, count=1)
            node = re.sub(r'(\bname\s*=\s*)"[^"]*"', lambda m: m[1] + '"physics_' + surface + '_' + str(number) + '"', node, count=1)
            nodes.append(node)
        replacements.append((opening, end, ',\n'.join(nodes)))
    if not reports:
        raise ValueError('No physics files to partition')
    for opening, end, replacement in reversed(replacements):
        text = text[:opening] + replacement + text[end:]
    model.write_text(text, encoding='utf-8')
    return reports


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--faces-per-object', type=int, default=4096)
    args = parser.parse_args()
    print(json.dumps(rebatch_obj(args.source, args.destination, faces_per_object=args.faces_per_object), indent=2))
