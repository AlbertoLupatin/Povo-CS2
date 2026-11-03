"""Native Hammer meshes (CMapMesh / CDmePolygonMesh) for closed solids.

Layout reverse-engineered from Valve's template maps:
  - half-edges come in opposite pairs (2k, 2k+1);
  - edgeVertexIndices[h] is the vertex h points TO, vertexEdgeIndices[v] is
    one half-edge leaving v, edgeNextIndices walks each face loop;
  - faces wind counter-clockwise seen from outside;
  - faceVertexData (uv, normal, tangent) is stored per half-edge, for the
    corner at its destination vertex;
  - uv = (dot(world_pos, axis.xyz) / scale + axis.w) / texture_size.
Solids are given in Hammer units, in world coordinates.
"""

import copy
import itertools
import math
import uuid

try:
    from .kv2 import Element
except ImportError:
    from kv2 import Element

NAMESPACE = uuid.UUID('6c1f3a52-4b55-4f0e-9d4a-2b7c0e6a9f10')
TEXTURE_SCALE = 0.25


# Repeat sizes that differ from the default, checked in game against real dimensions.
TEXTURE_SIZE = {'materials/ceiling/hr_c/hr_ceiling_tile_001_color.vmat': 512}   # 60 cm tiles


def texture_size(material):
    """Texels per texture repeat: dev grids are 128, stock surfaces ~1024."""
    if material in TEXTURE_SIZE:
        return TEXTURE_SIZE[material]
    return 128 if material.startswith('materials/dev/') else 1024


class Ids:
    """Deterministic element ids, node ids and reference ids."""

    def __init__(self, seed, first_node):
        self.seed = seed
        self.count = itertools.count()
        self.node = itertools.count(first_node)

    def element(self):
        return str(uuid.uuid5(NAMESPACE, f'{self.seed}:{next(self.count)}'))

    def node_id(self):
        return str(next(self.node))

    def reference(self):
        return '0x' + uuid.uuid5(NAMESPACE, f'{self.seed}:ref:{next(self.count)}').hex[:16]


def fmt(x):
    if isinstance(x, int):
        return str(x)
    s = f'{x:.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    length = math.sqrt(sum(x * x for x in a)) or 1
    return tuple(x / length for x in a)


def face_normal(points):
    # Newell's method: robust for any planar polygon.
    n = [0.0, 0.0, 0.0]
    for (x1, y1, z1), (x2, y2, z2) in zip(points, points[1:] + points[:1]):
        n[0] += (y1 - y2) * (z1 + z2)
        n[1] += (z1 - z2) * (x1 + x2)
        n[2] += (x1 - x2) * (y1 + y2)
    return norm(n)


def texture_axes(n):
    """World-aligned projection like Hammer's default, from the face normal."""
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 2:
        return (1, 0, 0), (0, -1, 0)
    if ax == 0:
        return (0, 1 if n[0] > 0 else -1, 0), (0, 0, -1)
    return (-1 if n[1] > 0 else 1, 0, 0), (0, 0, -1)


def box(lo, hi, material):
    """Axis-aligned box as (vertices, faces) with outward CCW loops."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    loops = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, [(loop, material) for loop in loops]


def hexa(v, material):
    """Six-sided solid from 8 corners ordered like box(): bottom quad then the top
    quad above it. The bottom quad is reordered to wind CCW seen from above."""
    bottom, top = list(v[:4]), list(v[4:])
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(bottom, bottom[1:] + bottom[:1]))
    if area < 0:
        bottom, top = bottom[::-1], top[::-1]
    loops = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return bottom + top, [(loop, material) for loop in loops]


def extrude(footprint, z0, z1, material, top=None, bottom=None):
    """Vertical prism from a CCW footprint [(x, y), ...]."""
    n = len(footprint)
    v = [(x, y, z0) for x, y in footprint] + [(x, y, z1) for x, y in footprint]
    faces = [(tuple(reversed(range(n))), bottom or material), (tuple(range(n, 2 * n)), top or material)]
    for i in range(n):
        j = (i + 1) % n
        faces.append(((i, j, n + j, n + i), material))
    return v, faces


def prism(poly, z0, z1, side, top, bottom, to_world):
    """Closed prism over a shapely polygon with holes; caps are constrained-Delaunay
    triangles. to_world(x, y, z) maps plan coordinates to Hammer units."""
    import shapely
    from shapely.geometry.polygon import orient
    poly = orient(poly, 1.0)
    rings = [list(poly.exterior.coords)[:-1]] + [list(h.coords)[:-1] for h in poly.interiors]
    verts, key = [], {}
    for ring in rings:
        for x, y in ring:
            key[(round(x, 4), round(y, 4))] = len(verts)
            verts.append(to_world(x, y, z0))
            verts.append(to_world(x, y, z1))
    faces = []
    for ring in rings:
        idx = [key[(round(x, 4), round(y, 4))] for x, y in ring]
        for a, b in zip(idx, idx[1:] + idx[:1]):
            faces.append(((a, b, b + 1, a + 1), side))
    for tri in shapely.constrained_delaunay_triangles(poly).geoms:
        t = orient(tri, 1.0)
        ids = [key[(round(x, 4), round(y, 4))] for x, y in list(t.exterior.coords)[:-1]]
        faces.append((tuple(i + 1 for i in ids), top))
        faces.append((tuple(reversed(ids)), bottom))
    return verts, faces


def stream(ids, name, flags, type_, values):
    """Each vectorN item is one "x y z" string; scalars are one item each."""
    base = name.split(':')[0]
    width = {'vector2_array': 2, 'vector3_array': 3, 'vector4_array': 4}.get(type_, 1)
    items = [' '.join(fmt(x) for x in values[i:i + width]) for i in range(0, len(values), width)]
    return Element('CDmePolygonMeshDataStream', [
        ['id', 'elementid', ids.element()],
        ['name', 'string', name],
        ['standardAttributeName', 'string', base],
        ['semanticName', 'string', base],
        ['semanticIndex', 'int', '0'],
        ['vertexBufferLocation', 'int', '0'],
        ['dataStateFlags', 'int', str(flags)],
        ['subdivisionBinding', 'element', ''],
        ['data', type_, items],
    ])


def data_array(ids, size, streams):
    return Element('CDmePolygonMeshDataArray', [
        ['id', 'elementid', ids.element()],
        ['size', 'int', str(size)],
        ['streams', 'element_array', streams],
    ])


def polygon_mesh(ids, vertices, faces, origin, lightmap_bias=0, closed=True):
    """CDmePolygonMesh for one or more closed solids sharing a local origin.
    closed=False also accepts open sheets (terrain): their border half-edges have no face
    and are linked to each other round the border."""
    materials = sorted({m for _loop, m in faces})
    half = {}           # (a, b) -> half-edge index
    used = set()
    edge_vertex, edge_face = [], []
    for f, (loop, _m) in enumerate(faces):
        for a, b in zip(loop, loop[1:] + loop[:1]):
            if (a, b) in used:
                raise ValueError(f'Edge {a}->{b} used twice: faces are not consistently wound')
            used.add((a, b))
            if (b, a) in half:
                h = half[(b, a)] ^ 1
            else:
                h = len(edge_vertex)
                edge_vertex += [b, a]
                edge_face += [-1, -1]
                half[(b, a)] = h + 1
            half[(a, b)] = h
            edge_face[h] = f
    if closed and -1 in edge_face:
        raise ValueError('Mesh is not closed')
    count = len(edge_vertex)
    edge_next = [0] * count
    border = {edge_vertex[h ^ 1]: h for h in range(count) if edge_face[h] == -1}   # origin -> border half-edge
    if len(border) < edge_face.count(-1):
        raise ValueError('Open mesh border touches itself at a vertex')
    for h in border.values():
        edge_next[h] = border[edge_vertex[h]]
    face_edge = []
    for loop, _m in faces:
        hs = [half[(a, b)] for a, b in zip(loop, loop[1:] + loop[:1])]
        face_edge.append(hs[0])
        for h, n in zip(hs, hs[1:] + hs[:1]):
            edge_next[h] = n
    vertex_edge = [0] * len(vertices)
    for (a, _b), h in half.items():
        vertex_edge[a] = h
    local = [sub(p, origin) for p in vertices]
    uv, normals, tangents = [(0, 0)] * count, [(0, 0, 1)] * count, [(1, 0, 0, -1)] * count
    scales, axis_u, axis_v, mat_index = [], [], [], []
    for f, (loop, material) in enumerate(faces):
        pts = [vertices[i] for i in loop]
        n = face_normal(pts)
        u_axis, v_axis = texture_axes(n)
        size = texture_size(material)
        scales += [TEXTURE_SCALE, TEXTURE_SCALE]
        axis_u += [*u_axis, 0]
        axis_v += [*v_axis, 0]
        mat_index.append(materials.index(material))
        for a, b in zip(loop, loop[1:] + loop[:1]):
            h = half[(a, b)]
            p = vertices[b]
            uv[h] = (sum(p[i] * u_axis[i] for i in range(3)) / TEXTURE_SCALE / size,
                     sum(p[i] * v_axis[i] for i in range(3)) / TEXTURE_SCALE / size)
            normals[h] = n
            tangents[h] = (*u_axis, -1)
    flat = lambda rows: [x for r in rows for x in r]
    return Element('CDmePolygonMesh', [
        ['id', 'elementid', ids.element()],
        ['name', 'string', 'meshData'],
        ['vertexEdgeIndices', 'int_array', [str(h) for h in vertex_edge]],
        ['vertexDataIndices', 'int_array', [str(i) for i in range(len(vertices))]],
        ['edgeVertexIndices', 'int_array', [str(v) for v in edge_vertex]],
        ['edgeOppositeIndices', 'int_array', [str(h ^ 1) for h in range(count)]],
        ['edgeNextIndices', 'int_array', [str(h) for h in edge_next]],
        ['edgeFaceIndices', 'int_array', [str(f) for f in edge_face]],
        ['edgeDataIndices', 'int_array', [str(h // 2) for h in range(count)]],
        ['edgeVertexDataIndices', 'int_array', [str(h) for h in range(count)]],
        ['faceEdgeIndices', 'int_array', [str(h) for h in face_edge]],
        ['faceDataIndices', 'int_array', [str(f) for f in range(len(faces))]],
        ['materials', 'string_array', materials],
        ['vertexData', 'CDmePolygonMeshDataArray', data_array(ids, len(vertices), [
            stream(ids, 'position:0', 3, 'vector3_array', flat(local))])],
        ['faceVertexData', 'CDmePolygonMeshDataArray', data_array(ids, count, [
            stream(ids, 'texcoord:0', 1, 'vector2_array', flat(uv)),
            stream(ids, 'normal:0', 1, 'vector3_array', flat(normals)),
            stream(ids, 'tangent:0', 1, 'vector4_array', flat(tangents))])],
        ['edgeData', 'CDmePolygonMeshDataArray', data_array(ids, count // 2, [
            stream(ids, 'flags:0', 3, 'int_array', [0] * (count // 2))])],
        ['faceData', 'CDmePolygonMeshDataArray', data_array(ids, len(faces), [
            stream(ids, 'textureScale:0', 0, 'vector2_array', scales),
            stream(ids, 'textureAxisU:0', 0, 'vector4_array', axis_u),
            stream(ids, 'textureAxisV:0', 0, 'vector4_array', axis_v),
            stream(ids, 'materialindex:0', 8, 'int_array', mat_index),
            stream(ids, 'flags:0', 3, 'int_array', [0] * len(faces)),
            stream(ids, 'lightmapScaleBias:0', 1, 'int_array', [lightmap_bias] * len(faces))])],
        ['subdivisionData', 'CDmePolygonMeshSubdivisionData', Element('CDmePolygonMeshSubdivisionData', [
            ['id', 'elementid', ids.element()],
            ['subdivisionLevels', 'int_array', ['0'] * count],
            ['streams', 'element_array', []]])],
    ])


def merge(solids):
    """Combine several (vertices, faces) solids into one vertex/face list."""
    vertices, faces = [], []
    for v, f in solids:
        base = len(vertices)
        vertices += v
        faces += [(tuple(i + base for i in loop), m) for loop, m in f]
    return vertices, faces


def map_mesh(template, ids, solids, tint=(255, 255, 255), lightmap_bias=0, closed=True):
    """A CMapMesh cloned from a template mesh, holding the given solids.
    lightmap_bias < 0 lowers the lightmap resolution of its faces (thin detail)."""
    vertices, faces = merge(solids)
    lo = [min(p[i] for p in vertices) for i in range(3)]
    hi = [max(p[i] for p in vertices) for i in range(3)]
    origin = tuple(round((a + b) / 2, 3) for a, b in zip(lo, hi))
    mesh = copy.deepcopy(template)
    mesh.set('id', ids.element(), 'elementid')
    mesh.set('nodeID', ids.node_id(), 'int')
    mesh.set('referenceID', ids.reference(), 'uint64')
    mesh.set('children', [], 'element_array')
    mesh.set('tintColor', f'{tint[0]} {tint[1]} {tint[2]} 255', 'color')
    mesh.set('meshData', polygon_mesh(ids, vertices, faces, origin, lightmap_bias, closed), 'CDmePolygonMesh')
    mesh.set('origin', ' '.join(fmt(x) for x in origin), 'vector3')
    mesh.set('angles', '0 0 0', 'qangle')
    mesh.set('scales', '1 1 1', 'vector3')
    return mesh
