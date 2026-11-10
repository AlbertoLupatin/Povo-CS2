"""Join the registered parking and ramp, retaining the -1 terrace apertures."""
import hashlib
import json

from .povo_room_fitout import subtract_box
from .povo2_frontage_registration import _carve_context


def apply(boxes, levels, root):
    link = next(l['connection'] for l in levels if l.get('connection'))
    p = link['povo2']
    ext = levels[0]['exterior']
    cfg = json.loads((root/'config/povo_exterior.json').read_text())
    terrace = ext['terrace_integration']
    a, south, c, old_north = ext['garage_bounds']
    terrace_west, _, _, north = terrace['slabs']['north_run']
    west, front, east, join = p['parking']['bounds']
    z = cfg['covered_parking']['z']
    result = []
    # Open only the common parking boundary, keeping the vestibule, stairs,
    # office/garden circulation and every approved -1 room/slab intact.
    portal = ((west, join-.2, z-.01), (east, south+.3, -.17))
    under_north_terrace = ((a, old_north, z), (c, north, .18))
    for box in boxes:
        name, lo, hi, material = box
        if name.startswith('exterior_garage_wall_north'):
            continue
        parts = [box]
        if name.startswith(('p2_parking_rebuilt_wall_', 'exterior_garage_wall_south_')):
            parts = [piece for part in parts for piece in subtract_box(part, portal)]
        if name == 'exterior_p2_terrace_north_terrace_base':
            parts = subtract_box(box, under_north_terrace)
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
    slab('join_roof', (west,join,east,south), .1,.18,'exterior_concrete')
    slab('north_floor', (a,old_north,c,north), z-.25,z,'exterior_asphalt')
    slab('north_roof', (a,old_north,terrace_west,north), .18,.4,'exterior_concrete')
    slab('north_wall', (a,north-.22,c,north), z,.18,'exterior_concrete')
    for side,x0,x1 in [('west',a,a+.22),('east',c-.22,c)]:
        slab(side+'_wall', (x0,old_north,x1,north), z,.18,'exterior_concrete')

    # Clear the sky-to-parking shafts through all exterior proxy solids and
    # both visual/physics meshes. Use the guarded openings from the assembled
    # terrace so that the connected walking deck keeps its registered bounds.
    apertures = terrace['holes']
    holes = [((x0,y0,z+.01),(x1,y1,20.)) for x0,y0,x1,y1 in apertures]
    result = _carve_context(result, ext, holes)
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
    far_end = [-29,north-.75,z]
    link['nav_seeds'].extend([[-15,29,z],[-29,33,z],far_end])
    p['parking']['continuous'] = dict(
        garage_bounds=ext['garage_bounds'], connection=[west,join,east,south],
        apertures=apertures, ramp=ramp, driveway=terrace['driveway'],
        source='User clarification 9 November 2026: ramp belongs to the parking; '
               'continue to the end of this side, exposed at -1 terrace openings',
        terrace_source='config/povo2_minus1_terrace.json',
        routes=[dict(id='parking_join',points=[[-15,26.5,z],[-15,33,z],[-29,33,z]]),
                dict(id='parking_full_side',points=[[-29,33,z],far_end])])
    return cleared
