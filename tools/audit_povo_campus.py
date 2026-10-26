#!/usr/bin/env python3
"""Check standing clearance to both classroom side aisles in the campus build."""

import json
from pathlib import Path

try:
    from .build_povo_campus import build_geometry, collision_boxes
    from .audit_povo_interior import audit_level, map_png
except ImportError:
    from build_povo_campus import build_geometry, collision_boxes
    from audit_povo_interior import audit_level, map_png

ROOT=Path(__file__).resolve().parents[1]


def audit():
    settings,config,boxes,levels,stair=build_geometry()
    reports=[]
    boxes=collision_boxes(boxes)
    output=ROOT/'exports/povo_campus';output.mkdir(parents=True,exist_ok=True)
    for level in levels:
        z=level['floor_elevation_metres']-370
        stations=[dict(id='entry',point=[22,-73.73] if level['id']=='academic_ground' else [13.95,-83.8])]
        end='bottom' if level['id']=='academic_ground' else 'top'
        for core in stair['cores']:
            stations.append(dict(id='stair_'+core['id']+'_'+end,point=core[end][:2]))
            portal=core['enclosure']['portals'][0 if end=='bottom' else 1]
            x,y,_=portal['centre']
            for side,offset in (('hall',-.65),('inside',.65)):
                if core['mirror_east']:offset=-offset
                stations.append(dict(id='stair_'+core['id']+'_'+side,point=[x+offset,y]))
        for room in level['rooms']:
            if not room.get('playable',True):continue
            if isinstance(room['fitout'],dict):
                for i,p in enumerate(room['fitout']['audit_points_local_metres']):
                    stations.append(dict(id=room['id']+f'_aisle{i}',point=p))
            else:
                a,b,c,d=room['footprint_local_metres']
                stations.append(dict(id=room['id'],point=[(a+c)/2,(b+d)/2]))
        stations.extend(level.get('connection',{}).get('audit_stations',[]))
        elevator=levels[0].get('elevator')
        if elevator:
            floor='ground' if level['id']=='academic_ground' else 'first'
            stations.append(dict(id='elevator_'+floor,point=elevator['stations'][floor]))
        report,free,visited=audit_level(boxes,dict(id=level['id'],floor_elevation_local=z),
                                      stations,width=.82,height=1.85)
        report['vertical_traversal']='Separate CS2 stair traversal test required'
        reports.append(report)
        (output/(level['id']+'_clearance.png')).write_bytes(map_png(report,free,visited))
    ground=levels[1].get('connection',{}).get('ground')
    if ground:
        report,free,visited=audit_level(boxes,ground,ground['audit_stations'],width=.82,height=1.85)
        report['vertical_traversal']='Separate CS2 stair traversal test required'
        reports.append(report)
        (output/(ground['id']+'_clearance.png')).write_bytes(map_png(report,free,visited))
    (output/'clearance.json').write_text(json.dumps(reports,indent=2)+'\n')
    return reports


if __name__=='__main__':
    reports=audit()
    for report in reports:
        print(report['id'],report['status'],len(report['stations']),'stations')
        for station in report['stations']:
            if not station['reachable_from_entrance']:print('UNREACHABLE',station['id'])
    raise SystemExit(0 if all(r['status']=='passed' for r in reports) else 1)
