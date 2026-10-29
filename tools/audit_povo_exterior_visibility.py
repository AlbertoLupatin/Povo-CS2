"""Check matched native pavement screenshots for the reported black patches.

This checks visible pixels under normal lighting. It complements the separate
floor/collision audits; it cannot establish geometry or route coverage alone.
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image,ImageChops

# Keep foreground ground areas clear of the buildings, trees and dark windows.
VIEWS = {
    'bridge_courtyard_join': ((0,-14,3.83),35,-90,(.15,.55,.85,.95)),
    'povo1_street': ((54.5,-40,7.6),30,90,(.05,.52,.95,.95)),
    'povo1_lower_plaza': ((25.5,-64,4),30,0,(.15,.55,.75,.95)),
    'povo1_inner_courtyard': ((1,-60,3.98),25,0,(.15,.6,.85,.95)),
    'povo2_entry_approach': ((54,35.65,4),25,-90,(.15,.65,.85,.95)),
    'povo2_north_approach': ((35,116,4),25,0,(.15,.6,.85,.95)),
    'west_street': ((-48,-60,3),30,0,(.15,.6,.85,.95)),
    'front_street_pavement': ((56.5,-35,7.72),30,0,(.15,.6,.85,.95)),
    'bridge_footway': ((38,-8.7,5.4),30,-90,(.4,.6,.85,.95)),
}


def inspect_ground(path, roi, maximum=.02):
    with Image.open(path) as source:
        image=source.convert('RGB')
        bounds=tuple(round(v*(image.width if i%2==0 else image.height)) for i,v in enumerate(roi))
        crop=image.crop(bounds)
        red,green,blue=crop.split()
        brightest=ImageChops.lighter(ImageChops.lighter(red,green),blue)
        dark=sum(brightest.histogram()[:17]);samples=crop.width*crop.height
    fraction=dark/samples
    return dict(passed=fraction<=maximum,roi_pixels=list(bounds),samples=samples,
                nearly_black_pixels=dark,nearly_black_fraction=fraction,maximum_fraction=maximum)


def audit(folder):
    folder=Path(folder)
    records={r['name']:r for r in json.loads((folder/'captures.json').read_text())}
    log=(folder/'console.log').read_text()
    if '> mat_fullbright 0' not in log or '> mat_fullbright 1' in log:
        raise ValueError('Requires normal-lighting engine captures, with the console transcript')
    checks=[]
    for name,(feet,pitch,yaw,roi) in VIEWS.items():
        record=records.get(name)
        if record is None:
            checks.append(dict(name=name,passed=False,error='Required view missing'));continue
        position=record['actual_feet']
        pose=(math.dist(position[:2],feet[:2])<.3 and abs(position[2]-feet[2])<.3
              and abs(record['pitch']-pitch)<.1 and abs(record['yaw']-yaw)<.1)
        if not pose:
            checks.append(dict(name=name,passed=False,error='View position/angle does not match the audited ground region'));continue
        checks.append(dict(name=name,**inspect_ground(folder/(name+'.png'),roi)))
    return dict(status='passed' if all(c['passed'] for c in checks) else 'failed',checks=checks,
                scope='Foreground ground pixels in nine matched normal-lighting engine views; geometry and walking checks are separate')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();result=audit(args.captures)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
    for check in result['checks']:print(check['name'],check.get('nearly_black_fraction',check.get('error')))
    raise SystemExit(0 if result['status']=='passed' else 1)
