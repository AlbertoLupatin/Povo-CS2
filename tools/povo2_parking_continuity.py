"""Join the registered parking and ramp, retaining the -1 terrace apertures."""
import hashlib
import json

from .povo_room_fitout import subtract_box
from .povo2_frontage_registration import OFFSET, _carve_context


def apply(boxes, levels, root):
    p = next(l['connection']['povo2'] for l in levels if l.get('connection'))
    ext = levels[0]['exterior']
    cfg = json.loads((root/'config/povo_exterior.json').read_text())
    terrace = json.loads((root/'config/povo2_minus1_terrace.json').read_text())
    a, south, c, old_north = ext['garage_bounds']
    north = terrace['north_run']['north'][1] + OFFSET
    west, front, east, join = p['parking']['bounds']
    z = cfg['covered_parking']['z']
    result = []
    # Open only the common parking boundary, keeping the vestibule, stairs,
    # office/garden circulation and every approved -1 room/slab intact.
    portal = ((west, join-.2, z-.01), (east, south+.3, -.17))
    for box in boxes:
        name, lo, hi, material = box
        if name.startswith('exterior_garage_wall_north'):
            continue
        parts = [box]
        if name.startswith(('p2_parking_rebuilt_wall_', 'exterior_garage_wall_south_')):
            parts = [piece for part in parts for piece in subtract_box(part, portal)]
        result.extend(parts)

    def slab(name, bounds, bottom, top, material):
        x0,y0,x1,y1 = bounds
        result.append(('exterior_parking_continuous_'+name,
                       (x0,y0,bottom), (x1,y1,top), material))

    slab('join_floor', (west,join,east,south), z-.25,z,'exterior_asphalt')
    # The terrace aperture extends 45 cm west of the old inner parking slab.
    # Fill that strip up to the existing ramp retaining wall as part of the
    # same parking, rather than leaving a view down onto bare proxy ground.
    ramp = cfg['garage_ramp']
    retaining_inside = ramp['centreline'][0][0] + ramp['width']/2 + .24
    slab('west_floor', (retaining_inside,front,west,south), z-.25,z,'exterior_asphalt')
    slab('west_roof', (terrace['outer_edge']['east'],front,west,south),
         .1,.4,'exterior_concrete')
    slab('join_roof', (west,join,east,south), .1,.4,'exterior_concrete')
    slab('north_floor', (a,old_north,c,north), z-.25,z,'exterior_asphalt')
    slab('north_roof', (a,old_north,c,north), .2,.45,'exterior_concrete')
    slab('north_wall', (a,north-.22,c,north), z,.2,'exterior_concrete')
    for side,x0,x1 in [('west',a,a+.22),('east',c-.22,c)]:
        slab(side+'_wall', (x0,old_north,x1,north), z,.2,'exterior_concrete')

    # Clear the sky-to-parking shafts through all exterior proxy solids and
    # both visual/physics meshes. These are the user's existing terrace holes,
    # translated by the same final registration as the building, not new gaps
    # inferred from an aerial roof. Covered stretches keep their actual roofs.
    facade = terrace['outer_edge']['east'] + terrace['outer_edge']['width']
    apertures = [[terrace['outer_edge']['east'], s['north'][0]+OFFSET,
                  facade, s['north'][1]+OFFSET]
                 for s in terrace['west_strip']['segments'] if s['kind']=='hole']
    holes = [((x0,y0,z+.01),(x1,y1,20.)) for x0,y0,x1,y1 in apertures]
    # The later frontage road pass laid a footway across the original ramp
    # mouth. Excavate its full width again, preserving the ramp surface itself.
    ra,rb = ramp['centreline']
    ramp_hole = ((ra[0]-ramp['width']/2,ra[1],z+.01),
                 (rb[0]+ramp['width']/2,rb[1],20.))
    saved = {}
    for key in ('meshes','collision_meshes'):
        saved[key] = [m for m in ext[key] if 'garage_ramp' in m['name']]
        ext[key] = [m for m in ext[key] if 'garage_ramp' not in m['name']]
    result = _carve_context(result, ext, holes+[ramp_hole])
    for key in saved:
        ext[key].extend(saved[key])
    cleared = []
    for box in result:
        parts = [box]
        if box[0].startswith('p2_parking_rebuilt_ceiling_'):
            for hole in holes:
                parts = [piece for part in parts for piece in subtract_box(part,hole)]
        cleared.extend(parts)
    ext['garage_bounds'] = [a,south,c,north]
    for path in ('tools/povo2_parking_continuity.py','config/povo2_minus1_terrace.json'):
        ext['input_hashes'][path] = hashlib.sha256((root/path).read_bytes()).hexdigest()
    ext['integration'] += '; registered parking joined to ramp garage and extended to north terrace end'
    next(l['connection'] for l in levels if l.get('connection'))['nav_seeds'].extend(
        [[-15,29,z],[-29,33,z],[-29,north-1,z]])
    p['parking']['continuous'] = dict(
        garage_bounds=ext['garage_bounds'], connection=[west,join,east,south],
        apertures=apertures, ramp=cfg['garage_ramp'],
        source='User clarification 9 November 2026: ramp belongs to the parking; '
               'continue to the end of this side, exposed at -1 terrace openings',
        terrace_source='config/povo2_minus1_terrace.json',
        routes=[dict(id='parking_join',points=[[-15,26.5,z],[-15,33,z],[-29,33,z]]),
                dict(id='parking_full_side',points=[[-29,33,z],[-29,north-1,z]])])
    return cleared
