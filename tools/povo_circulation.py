#!/usr/bin/env python3
"""Validate and review the user-confirmed Povo walk and bridge-floor relation.

This models connectivity, not traversable collision or measured storey heights.
"""
import argparse
from collections import deque
import hashlib
from html import escape
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def validate(config):
    levels=config['levels'];by_id={l['id']:l for l in levels}
    if len(by_id)!=len(levels):raise ValueError('Duplicate level IDs')
    for level in levels:
        if level['building'] not in ('povo1','povo2') or type(level['floor']) is not int:
            raise ValueError('Invalid building/floor')
    bridge=config['bridge_connection']
    if bridge.get('relation')!='same_elevation':raise ValueError('Bridge requires equal endpoint elevations')
    if bridge['from_level'] not in by_id or bridge['to_level'] not in by_id:raise ValueError('Unknown bridge level')
    endpoints={(by_id[bridge[k]]['building'],by_id[bridge[k]]['floor']) for k in ('from_level','to_level')}
    if endpoints!={('povo2',1),('povo1',2)}:
        raise ValueError('Confirmed bridge is Povo 2 floor 1 to Povo 1 floor 2')
    photos=[n for section in config['segments'] for n in section['photos']]
    if len(photos)!=66 or set(photos)!=set(range(1,67)) or any(type(n) is not int for n in photos):
        raise ValueError('Walk must assign each photo 01–66 exactly once')
    sections={s['id']:s for s in config['segments']}
    if len(sections)!=len(config['segments']):raise ValueError('Duplicate walk segment IDs')
    stairs=config['stair_connections'];ids=set()
    for stair in stairs:
        if stair['id'] in ids:raise ValueError('Duplicate stair IDs')
        ids.add(stair['id'])
        try:a,b=(by_id[stair[k]] for k in ('from_level','to_level'))
        except KeyError as error:raise ValueError('Unknown stair level') from error
        if a['building']!=b['building'] or a['building']!=stair['building'] or abs(a['floor']-b['floor'])!=1:
            raise ValueError('Stairs must join adjacent named floors in one building')
    p1={s['id']:s for s in stairs if s['building']=='povo1'}
    if p1['povo1_ne_2_to_1']['core']!='stair_northeast' or p1['povo1_se_1_to_0']['core']!='stair_southeast':
        raise ValueError('The two Povo 1 descents use different confirmed stair cores')
    if sections['a211_or_a212'].get('possible_rooms')!=['A211','A212'] or sections['a211_or_a212'].get('room'):
        raise ValueError('A211/A212 photo identity must remain explicitly ambiguous')
    edges=[(s['from_level'],s['to_level']) for s in stairs]+[(bridge['from_level'],bridge['to_level'])]
    seen={levels[0]['id']};pending=deque(seen)
    while pending:
        current=pending.popleft()
        for a,b in edges:
            other=b if a==current else a if b==current else None
            if other and other not in seen:seen.add(other);pending.append(other)
    if seen!=set(by_id):raise ValueError('Route contains disconnected named levels')
    return by_id


def resolve_elevations(config, anchors):
    """Propagate only the confirmed bridge equality; never infer other rises."""
    by_id=validate(config)
    if any(k not in by_id or type(v) not in (int,float) or not math.isfinite(v) for k,v in anchors.items()):
        raise ValueError('Elevation anchors must be finite values for known levels')
    result={k:anchors.get(k) for k in by_id}
    bridge=config['bridge_connection'];a,b=(bridge[k] for k in ('from_level','to_level'))
    if result[a] is not None and result[b] is not None and not math.isclose(result[a],result[b],abs_tol=1e-6):
        raise ValueError('Bridge endpoints have conflicting elevation anchors')
    shared=result[a] if result[a] is not None else result[b]
    result[a]=result[b]=shared
    return result


def review_svg(config):
    validate(config)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1050">',
           '<rect width="1500" height="1050" fill="#edf1f2"/>','<g font-family="DejaVu Sans, sans-serif" fill="#193441">',
           '<text x="45" y="55" font-size="30" font-weight="bold">POVO / CONFIRMED WALK CONNECTIONS</text>',
           '<text x="45" y="95" font-size="18">Connections and named floors confirmed by the user. Diagram spacing is not a height measurement.</text>',
           '<text x="130" y="150" font-size="26" font-weight="bold">POVO 1</text>',
           '<text x="1080" y="150" font-size="26" font-weight="bold">POVO 2</text>']
    positions={'povo1_2':(260,245),'povo1_1':(260,500),'povo1_0':(260,765),
               'povo2_1':(1200,245),'povo2_0':(1200,675),'povo2_minus1':(1200,870)}
    def line(points,color,width=5,dash=''):
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'
    parts.append(line('260,245 1200,245','#438e9c',9))
    for y,text in [(185,'BRIDGE / photos 60–56'),(215,'Povo 2 floor 1 = Povo 1 floor 2')]:
        parts.append(f'<text x="710" y="{y}" text-anchor="middle" font-size="20" font-weight="bold">{text}</text>')
    parts.extend([line('260,245 260,500','#a64f4d'),line('310,500 310,765','#c97b42'),
                  line('1200,245 1200,675','#69767c',5,'8 6'),line('1200,675 1200,870','#69767c',5,'8 6')])
    labels=[(335,345,'NE red stairwell / A209–A216','Photos 51–47: floor 2 → 1'),
            (365,615,'SE red stairwell / A212–A213','Photos 39–38: floor 1 → ground'),
            (815,470,'Povo 2 stairs / photos 66–64','Floor 0 → 1; metric rise unknown'),
            (810,790,'Povo 2 stairs / photos 08–04','Ground → −1; core not located')]
    for x,y,a,b in labels:
        parts.append(f'<text x="{x}" y="{y}" font-size="18">{escape(a)}</text>')
        parts.append(f'<text x="{x}" y="{y+28}" font-size="16">{escape(b)}</text>')
    for level in config['levels']:
        x,y=positions[level['id']]
        parts.append(f'<rect x="{x-120}" y="{y-25}" width="240" height="50" rx="8" fill="#ffffff" stroke="#193441" stroke-width="2"/>')
        label='Ground / 0' if level['floor']==0 else f"Floor {level['floor']}"
        parts.append(f'<text x="{x}" y="{y+7}" text-anchor="middle" font-size="22">{label}</text>')
    for y,text in [(970,'A215 = photos 44–43. Photos 42–41 = A211 OR A212; exact room remains unresolved.'),
                   (1005,'Only the bridge floors are equated across buildings. Povo 2 ground and basement heights remain unassigned.')]:
        parts.append(f'<text x="45" y="{y}" font-size="18">{text}</text>')
    return '\n'.join(parts+['</g></svg>'])+'\n'


def build(config_path, output, *, root=ROOT):
    config_path,output,root=Path(config_path).resolve(),Path(output),Path(root).resolve()
    config=json.loads(config_path.read_text(encoding='utf-8'));validate(config)
    campus_path=root/'config/povo_blockout.json';interior_path=root/'config/povo1_interior_study.json'
    campus=json.loads(campus_path.read_text(encoding='utf-8'));interior=json.loads(interior_path.read_text(encoding='utf-8'))
    if campus['architecture']['bridge'].get('connected_levels')!=['povo2_1','povo1_2']:
        raise ValueError('Exterior bridge must bind the confirmed named floors')
    manifest_path=root/config['photo_manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    photos=[p for p in manifest['images'] if 'walk_photo_number' in p]
    if len(photos)!=66 or {p['walk_photo_number'] for p in photos}!=set(range(1,67)):
        raise ValueError('Photo catalogue must contain the complete walk')
    for photo in photos:
        if hashlib.sha256((manifest_path.parent/photo['file']).read_bytes()).hexdigest()!=photo['sha256']:
            raise ValueError('Walk photo hash mismatch')
    anchors={'povo1_'+str(l['user_floor']):interior['reference_elevation_metres']+l['height_offset_metres'] for l in interior['levels']}
    anchors['povo1_2']=campus['architecture']['bridge']['deck_elevation']
    elevations=resolve_elevations(config,anchors)
    report={'status':'confirmed_connectivity_validated','scope':'Named-level graph and existing estimate consistency; not game traversal',
            'estimated_elevations_metres':elevations,'elevation_note':'Existing prototype/scenery estimates only; unknown heights remain null. Bridge equality is user-confirmed, absolute heights are not.',
            'povo1_estimated_rises_metres':{'0_to_1':round(elevations['povo1_1']-elevations['povo1_0'],6),'1_to_2':round(elevations['povo1_2']-elevations['povo1_1'],6)},
            'metric_rise_warning':'Independent prototype and bridge estimates imply unequal Povo 1 rises. Do not freeze stairs or bake collision until heights are calibrated.',
            'verified_walk_photos':len(photos),'inputs':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (config_path,campus_path,interior_path,manifest_path)}}
    if output.is_symlink() or (output.exists() and not output.is_dir()):raise ValueError('Output must be a directory')
    targets=[output/'report.json',output/'review.svg']
    if any(p.is_symlink() or p.is_dir() for p in targets):raise ValueError('Output path is occupied')
    inputs={p.resolve() for p in (config_path,campus_path,interior_path,manifest_path)}
    if any(p.resolve() in inputs for p in targets):raise ValueError('Outputs cannot replace inputs')
    output.mkdir(parents=True,exist_ok=True)
    targets[0].write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    targets[1].write_text(review_svg(config),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config/povo_circulation.json')
    parser.add_argument('--output',type=Path,default=ROOT/'exports/povo_circulation')
    args=parser.parse_args()
    try:report=build(args.config,args.output)
    except (ValueError,KeyError,OSError) as error:parser.exit(2,f'error: {error}\n')
    print(f"Validated {report['verified_walk_photos']} walk photos; bridge Povo 2 floor 1 ↔ Povo 1 floor 2")


if __name__=='__main__':main()
