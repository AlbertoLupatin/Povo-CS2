"""Audit freshly registered Povo 2 geometry without requiring native CS2 tools.

Run ``python -m tools.audit_povo2_frontage`` to print a JSON report. This checks
source collision/support and connectivity; it does not execute the game engine.
"""
import json

from .build_povo_campus import build_registered_geometry, collision_boxes
from .audit_povo2_integrated import audit_stair_routes
from .audit_povo_exterior_integrated import standing
from .audit_povo_interior import audit_level
from .audit_povo_yard import audit_gardens


def audit():
    _, _, boxes, levels, _ = build_registered_geometry()
    physics = collision_boxes(boxes)
    link = next(l['connection'] for l in levels if l.get('connection'))
    p2 = link['povo2']
    exterior = levels[0]['exterior']
    floors = []
    for level in p2['levels']:
        z, prefix = level['z'], level['id']
        support = [(prefix+'_alias_'+n, lo, hi, material)
                   for n, lo, hi, material in physics
                   if n.startswith(('p2_', 'academic_first_link_p2'))
                   and material.startswith('floor_') and abs(hi[2]-z)<.02]
        report, _, _ = audit_level(physics+support,
            dict(id=prefix, floor_elevation_local=z), level['audit_stations'])
        floors.append(report)
    routes = p2['basement_rebuild']['routes'] + p2['stairs']['path']
    routes += [dict(points=points) for points in p2['gardens']['routes'].values()]
    samples, failures = audit_stair_routes(physics, routes)
    bridge = [[18.25, 9., 11.2], [18.25, 20., 11.2], [22.25, 20., 11.2],
              [22.25, 28.8, 11.2], [19.2, 28.8, 11.2]]
    bridge_samples, bridge_failures = audit_stair_routes(physics,
        [dict(points=bridge), dict(points=bridge[::-1])])
    entrance_failures = []
    for bank in exterior['entrance']['door_banks']:
        x, y, z = bank['centre']
        for xx in (x-.5, x, x+.5):
            foot, obstacles = standing(xx, y, z, physics, exterior['collision_meshes'])
            if foot is None or obstacles:
                entrance_failures.append(dict(point=[xx, y, z], foot=foot, obstacles=obstacles))
    garden = audit_gardens(boxes, levels)
    passed = (all(floor['status']=='passed' for floor in floors)
              and not failures and not bridge_failures and not entrance_failures
              and garden['status']=='passed')
    return dict(status='passed' if passed else 'failed',
        registration=p2['frontage_registration'], floors=floors,
        route_samples=samples, route_failures=failures,
        bridge_samples=bridge_samples, bridge_failures=bridge_failures,
        entrance_failures=entrance_failures, garden=garden,
        limitations='Fresh source geometry only; native CS2 compile and engine traversal not run.')


if __name__ == '__main__':
    result = audit()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status']=='passed' else 1)
