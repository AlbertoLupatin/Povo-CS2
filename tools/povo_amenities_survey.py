"""Render image-space amenities traces independently of provisional campus registration."""
import base64
import json
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def render():
    cfg=json.loads((ROOT/'config/povo_amenities_survey.json').read_text(encoding='utf-8'))
    out=ROOT/'exports/povo_amenities_survey';out.mkdir(exist_ok=True)
    for key,num in [('library0',15),('canteen0',13),('canteen1',12)]:
        plan=cfg[key];raster=ROOT/f'exports/amenity_{num}.jpg'
        encoded=base64.b64encode(raster.read_bytes()).decode('ascii')
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1700 1275"><title>{key} photograph trace - unregistered review</title>',f'<image width="1700" height="1275" href="data:image/jpeg;base64,{encoded}"/>', '<style>text{font:16px sans-serif;paint-order:stroke;stroke:white;stroke-width:4px;stroke-linejoin:round}.wall{fill:none;stroke:#ee2244;stroke-width:3}.gap{stroke:#00b966;stroke-width:6}.stair{fill:#e8b523;fill-opacity:.18;stroke:#a07b00;stroke-width:3}.zone{fill:#238bd5;fill-opacity:.05;stroke:#238bd5;stroke-dasharray:8 6;stroke-width:2}</style>']
        def label(x,y,text):parts.append(f'<text x="{x}" y="{y}">{escape(text)}</text>')
        def line(points,cls):
            assert len(points)>=2
            assert all(0<=x<=1700 and 0<=y<=1275 for x,y in points)
            parts.append(f'<polyline class="{cls}" points="'+ ' '.join(f'{x},{y}' for x,y in points)+'"/>')
        def rect(bounds,cls,text):
            a,b,c,d=bounds;assert a<c and b<d
            parts.append(f'<rect class="{cls}" x="{a}" y="{b}" width="{c-a}" height="{d-b}"/>');label(a+5,b+19,text)
        line(plan['outline']+[plan['outline'][0]],'wall')
        for item in plan.get('walls',[]):
            line(item['points'],'wall');label(item['points'][0][0]+3,item['points'][0][1]-7,item['id'])
            gaps=item.get('door_gaps',[])
            if isinstance(gaps,list):
                for gap in gaps:line(gap,'gap')
        for item in plan.get('zones',[]):rect(item['bounds'],'zone',item['label']+' (zone only)')
        for name,bounds in plan.get('core',{}).items():rect(bounds,'zone',name+' (bounds, not wall trace)')
        for i,item in enumerate(plan.get('stairs',[])):rect(item['bounds'],'stair',item['kind'])
        for item in plan.get('exterior_doors',[]):
            points=item['segment'] if isinstance(item,dict) else item
            line(points,'gap')
        for item in plan.get('interior_openings',[]):line(item['gap'],'gap')
        label(60,80,key+' | RED visible wall trace; GREEN observed opening; BLUE zone bounds; YELLOW stair')
        label(60,110,'Review only: approximate image pixels. No metric registration. Untraced details remain visible in photograph.')
        parts.append('</svg>');(out/f'{key}.svg').write_text('\n'.join(parts),encoding='utf-8')
    return out

if __name__=='__main__':print(render())
