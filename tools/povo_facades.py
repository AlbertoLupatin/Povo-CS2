"""Replace the academic perimeter shell with an explicit photo-guided facade.

Windows belong to the elevation, independently of a classroom furniture kit.
The south-end design approved by the user also applies to both bridge facades.
Coordinates remain in the established local metre frame; no bridge relocation.
"""
import hashlib
import json
import math

from .povo_room_fitout import subtract_box


def intersect(a, b):
    return all(max(a[0][i], b[0][i]) < min(a[1][i], b[1][i])-1e-8 for i in range(3))


def frame_box(axis, plane, inward, a, b, d0, d1, z0, z1):
    lo, hi = [0., 0., z0], [0., 0., z1]
    lo[axis], hi[axis] = sorted((plane+inward*d0, plane+inward*d1))
    lo[1-axis], hi[1-axis] = a, b
    return tuple(lo), tuple(hi)


def schedule(spec):
    w, s, e, n = spec['povo1_bounds']
    a, b = spec['long_central_span']
    narrow = spec['narrow_module']
    long = [(s, a, max(1, round((a-s)/narrow)), 'narrow'),
            (a, b, spec['long_central_bays'], 'broad'),
            (b, n, max(1, round((n-b)/narrow)), 'narrow')]
    p2w, p2s, p2e, _ = spec['povo2_south_bounds']
    return [dict(id='p1_east', axis=0, plane=e, inward=-1, a=s, b=n, segments=long),
            dict(id='p1_west', axis=0, plane=w, inward=1, a=s, b=n, segments=long),
            dict(id='p1_south', axis=1, plane=s, inward=1, a=w, b=e,
                 segments=[(w, e, spec['short_bays'], 'broad')]),
            dict(id='p1_north', axis=1, plane=n, inward=-1, a=w, b=e,
                 segments=[(w, e, spec['short_bays'], 'broad')]),
            dict(id='p2_south', axis=1, plane=p2s, inward=1, a=p2w, b=p2e,
                 segments=[(p2w, p2e, spec['short_bays'], 'broad')])]


def extend(boxes, levels, root):
    path = root/'config/povo_facades.json'
    spec = json.loads(path.read_text())
    faces = schedule(spec)
    link = next(l['connection'] for l in levels if 'connection' in l)
    bridge = link['bridge']
    # E16.5..20 lies within the easternmost of the six short-end bays.
    if not (spec['povo1_bounds'][2]-(47/spec['short_bays']) < bridge[0] < bridge[2] < spec['povo1_bounds'][2]):
        raise ValueError('Bridge must remain in the eastern outer facade bay')
    entrance = next(b for b in boxes if b[0] == 'campus_entry_landing')
    entry_y = (entrance[1][1]+entrance[2][1])/2
    floors = spec['floors']
    result = list(boxes)
    # Replace only shell depth. Interior partitions terminate against the new
    # glazing instead of being cut through the room. Structural slabs stay put.
    replace_materials = {'wall', 'window_glass', 'window_frame', 'reception_glass',
                         'exterior_stone', 'exterior_glass', 'metal_dark'}
    for f in faces:
        p2 = f['id'].startswith('p2')
        shell = frame_box(f['axis'], f['plane'], f['inward'], f['a'], f['b'],
                          -.36, 1.2 if p2 else .24, floors[0], spec['roof']+.001)
        kept = []
        for box in result:
            name, lo, hi, material = box
            eligible = (name.startswith(('academic_first_link_p2_', 'p2_ground_', 'exterior_povo2_')) if p2
                        else name.startswith(('academic_', 'stair_')) and not name.startswith('academic_first_link_'))
            if eligible and material in replace_materials and intersect((lo, hi), shell):
                cut = shell
                if not p2 and material == 'wall' and hi[f['axis']]-lo[f['axis']] > hi[1-f['axis']]-lo[1-f['axis']]:
                    # Perpendicular room partitions meet the inner glass face;
                    # only the parallel perimeter shell is removed in full.
                    cut = frame_box(f['axis'], f['plane'], f['inward'], f['a'], f['b'],
                                    -.36, spec['glass_inset']+.025, floors[0], spec['roof']+.001)
                kept.extend(subtract_box(box, cut))
            else:
                kept.append(box)
        result = kept

    records = []
    for f in faces:
        prefix = 'facade_'+f['id']
        axis, plane, inward = f['axis'], f['plane'], f['inward']
        p2 = f['id'] == 'p2_south'

        def add(name, a, b, d0, d1, z0, z1, material):
            if b-a < 1e-7 or z1-z0 < 1e-7:
                return
            lo, hi = frame_box(axis, plane, inward, a, b, d0, d1, z0, z1)
            result.append((prefix+'_'+name, lo, hi, material))

        def pieces(a, b, cuts):
            spans = [(a, b)]
            for c, d in cuts:
                spans = [(u, v) for x, y in spans for u, v in ((x, min(y, c)), (max(x, d), y)) if v-u > 1e-7]
            return spans

        for floor, z in enumerate(floors):
            top = floors[floor+1] if floor < 2 else spec['roof']
            head = z+spec['window_head']
            sill = z+(.06 if floor == 0 else spec['upper_sill'])
            portal = []
            if floor == 2 and f['id'] in ('p1_north', 'p2_south'):
                portal = [(bridge[0]-.03, bridge[2]+.03)]
            if floor == 0 and f['id'] == 'p1_east':
                # Keep the original functioning automatic bank at its existing
                # position. Its frame, leaves and sensors are supplied upstream.
                portal = [(entry_y-1.86, entry_y+1.86)]
            if floor == 0 and p2:
                # The approved left extension crosses the old south context
                # line. A facade cannot seal that existing ground-floor route.
                portal = [(1.88, 6.8)]
            segments = ([(f['a'], f['b'], math.ceil((f['b']-f['a'])/1.5), 'curtain')]
                        if floor == 0 else f['segments'])
            add(f'l{floor}_head', f['a'], f['b'], -.25, .025, head, top, 'stone_facade')
            for a, b in pieces(f['a'], f['b'], portal):
                add(f'l{floor}_sill_{a:.3f}', a, b, -.25 if floor else -.03, .025, z, sill, 'stone_facade')
            for segment, (a, b, count, kind) in enumerate(segments):
                pier = (.07 if kind == 'curtain' else spec['narrow_pier_width'] if kind == 'narrow'
                        else spec['broad_pier_width'])
                for bay in range(count+1):
                    at = a+(b-a)*bay/count
                    for c, d in pieces(max(a, at-pier/2), min(b, at+pier/2), portal):
                        add(f'l{floor}_s{segment}_pier{bay}_{c:.3f}', c, d, -.25 if floor else -.03,
                            .025, z, head, 'stone_facade' if floor else 'window_frame')
                for bay in range(count):
                    left, right = a+(b-a)*bay/count+pier/2, a+(b-a)*(bay+1)/count-pier/2
                    for part, (c, d) in enumerate(pieces(left, right, portal)):
                        ident = f'l{floor}_s{segment}_b{bay}_p{part}'
                        # The P2 western backdrop has no surveyed playable rooms.
                        # A genuine recess replaces its solid front; its glazing
                        # stays sealed, as do the existing reception boundaries.
                        sealed = p2 and (floor != 2 or c < 7)
                        material = 'window_glass'
                        depth = spec['glass_inset']
                        add(ident+('_sealed_glass' if sealed else '_glass'), c, d, depth, depth+.025, sill, head, material)
                        count_panes = max(1, round((d-c)/1.1))
                        for k in range(count_panes+1):
                            at = c+(d-c)*k/count_panes
                            add(ident+f'_mullion{k}', max(c-.025, at-.025), min(d+.025, at+.025),
                                -.04, .06, sill, head, 'window_frame')
                        for k, h in enumerate((sill, z+1.05, z+2.55, head-.05)):
                            add(ident+f'_transom{k}', c, d, -.04, .06, h, h+.05, 'window_frame')
                        if floor:
                            # Shallow sill and horizontal window guards, not a
                            # new projecting balcony or an external corridor.
                            add(ident+'_ledge', c, d, -.13, .025, sill-.06, sill, 'stone_facade')
                            for k in range(max(1, math.ceil((d-c)/1.3))+1):
                                at = c+(d-c)*k/max(1, math.ceil((d-c)/1.3))
                                add(ident+f'_guard_post{k}', at-.018, at+.018, -.105, -.065,
                                    sill, z+spec['guard_height'], 'window_frame')
                            for k, h in enumerate((.40, .57, .74, .91, spec['guard_height'])):
                                add(ident+f'_guard_bar{k}', c, d, -.11, -.06, z+h, z+h+.027, 'window_frame')
                        records.append(dict(face=f['id'], floor=floor-1, bay=ident,
                                            span=[c, d], glass=frame_box(axis, plane, inward, c, d, depth, depth+.025, sill, head),
                                            material=material, sealed=sealed))
            if portal:
                for a, b in portal:
                    # Leave clear headroom through bridge ends / entrance.
                    add(f'l{floor}_portal_head', a, b, -.25, .025, z+2.80, head, 'stone_facade')
                    if floor == 2 or f['id'] == 'p1_east':
                        bottom = z+(2.65 if floor == 2 else 2.15)
                        add(f'l{floor}_portal_clerestory', a, b, 0, .025, bottom, z+2.80, 'window_glass')
        if p2:
            # Close the new upper shell's short returns against the retained
            # unplayable backdrop, without touching any floor below local z4.
            for side, at in (('west', f['a']), ('east', f['b'])):
                add('upper_return_'+side, at, at+.16, .025, 1.2, 11.0, spec['roof'], 'stone_facade')
            add('upper_cap', f['a'], f['b'], .025, 1.2, spec['roof']-.12, spec['roof'], 'stone_facade')
            add('upper_backdrop_back', f['a'], 7, 1.04, 1.2, 11.0, spec['roof'], 'wall')

    # The real bridge is screened in fine horizontal aluminium louvers; keep
    # the existing glazed enclosure and route but replace the coarse spacing.
    result = [b for b in result if not b[0].startswith('academic_first_link_bridge_finish_louver_')]
    z = link['floor_local_metres']
    for side, x, sign in (('west', bridge[0], -1), ('east', bridge[2], 1)):
        for k in range(28):
            h = z+.22+k*.105
            result.append((f'facade_bridge_louver_{side}_{k}',
                           (x+sign*.16-.035, bridge[1], h),
                           (x+sign*.16+.035, bridge[3], h+.035), 'window_frame'))
    levels[0]['facades'] = dict(status=spec['status'], faces=faces, openings=records,
                               bridge_bounds=bridge, bridge_corner='east (viewer-left from north)',
                               input_hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest(),
                                             'tools/povo_facades.py':hashlib.sha256((root/'tools/povo_facades.py').read_bytes()).hexdigest()})
    return result
