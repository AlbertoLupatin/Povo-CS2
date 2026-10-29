"""Document conditional plan dimensions and check their campus footprint fit."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
try:
    from .build_povo_campus import build_geometry
except ImportError:
    from build_povo_campus import build_geometry


def render():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'config/povo2_internal_dimensions.json').read_text())
    _,_,_,levels,_=build_geometry()
    spec=next(l['connection']['povo2'] for l in levels if l.get('connection'))
    geographic=json.loads((root/'config/povo_blockout.json').read_text())
    origin=geographic['origin'];roofs={}
    for building in geographic['buildings']:
        x,y,u,v=building['bounds']
        roofs[building['id']]=[x-origin[0],y-origin[1],u-origin[0],v-origin[1]]
    def contains(outer,inner):return all((inner[i]>=outer[i] if i<2 else inner[i]<=outer[i]) for i in range(4))
    core=spec['stairs']['well_bounds'];vest=spec['parking']['vestibule'];parking=spec['parking']['bounds']
    p1_north=max(r[3] for name,r in roofs.items() if name.startswith('povo1_') and r[0]<parking[2] and r[2]>parking[0])
    core_plan=cfg['trace_crop_pixels_approx']['stair_enclosure']
    vest_plan=cfg['trace_crop_pixels_approx']['vestibule']
    sx,sy=cfg['registration']['scale_metres_per_crop_pixel']
    report={
        'status':'Local geometry fits registered core; metric and full basement registration provisional',
        'scale_basis':'Existing 8 x 9.5 m core; no independent measured length',
        'trace_axis_scale_difference_percent':100*abs(sx-sy)/((sx+sy)/2),
        'vestibule_dimensions_metres':[vest[2]-vest[0],vest[3]-vest[1]],
        'inferred_depth_metres':(vest_plan[2]-vest_plan[0])*sx,
        'door_inferred_east':cfg['inferred']['door_east_coordinate_metres'],
        'door_implemented_east':spec['stairs']['portals'][2]['centre'][0],
        'core_inside_povo2_east_roof':contains(roofs['povo2_east'],core),
        'vestibule_inside_povo2_east_roof':contains(roofs['povo2_east'],vest),
        'parking_bounds':parking,
        'parking_to_povo1_north_gap_metres':parking[1]-p1_north,
        'parking_size_preserved_metres':[parking[2]-parking[0],parking[3]-parking[1]],
        'external_garage_north_gap_metres':30-parking[3],
        'limitations':['Aerial roofs cannot establish underground boundaries.',
                       'The existing larger exterior garage remains separately registered; its connection is not established by this local fit.',
                       'Trace/perspective and existing core scale uncertainty remain; estimates are not a survey.']}
    out=root/'exports/povo2_layout_audit_20261028'
    (out/'dimensional_fit.json').write_text(json.dumps(report,indent=2)+'\n')
    im=Image.new('RGB',(1720,1050),'#faf9f5');d=ImageDraw.Draw(im)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',29)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    d.text((35,25),'Povo 2: plan proportions and building fit',font=title,fill='#203b4d')
    d.text((35,72),'Conditional dimensions from photo 37, using the existing stair-core scale. No independent metric calibration.',font=font,fill='#526574')
    crop=Image.open(root/cfg['review_crop']).convert('RGB')
    cd=ImageDraw.Draw(crop)
    for bounds,color in ((core_plan,'#255baf'),(vest_plan,'#16806a')):cd.rectangle(bounds,outline=color,width=7)
    da,db=cfg['trace_crop_pixels_approx']['stair_door_wall_interval']
    cd.line((core_plan[0],da,core_plan[0],db),fill='#d06917',width=12)
    crop.thumbnail((1030,755));im.paste(crop,(35,150))
    d.text((35,920),'Blue: stair core. Green: vestibule. Orange: stair-door interval.',font=font,fill='#203b4d')
    d.text((35,955),'Plan ratios: vestibule spans the core side; depth ~3.6 m; door at ~76% from the parking end.',font=small,fill='#526574')
    d.text((1110,130),'CAMPUS FIT (north up)',font=font,fill='#203b4d')
    def xy(x,y):return (1210+(x+35)*3,200+(120-y)*3)
    def rect(r,fill,outline):
        x,y,u,v=r;a,b=xy(x,v);c,e=xy(u,y);d.rectangle((a,b,c,e),fill=fill,outline=outline,width=2)
    for name,r in roofs.items():
        if name.startswith('povo2_'):rect(r,'#dce6ee','#52728d')
    rect([-23,-30,24,-20],'#dddcd5','#888577')
    rect([16.5,-20,20,10],'#e5def0','#8b6ca5')
    rect(parking,'#f3dfb7','#bd8729')
    rect(core,'#b7d6cf','#16806a');rect(vest,'#8dc6b6','#16806a')
    for pos,text in [((1110,685),'Blue: Povo 2 roof envelopes'),((1110,715),'Gold: underground parking lobe'),
                     ((1110,745),'Green: stair / vestibule'),((1110,775),'Grey: northern edge of Povo 1')]:d.text(pos,text,font=small,fill='#526574')
    d.text((1110,825),'Vestibule: 9.5 x 3.6 m (estimate)',font=small,fill='#203b4d')
    d.text((1110,855),'Door: 2.3 m from office-side end',font=small,fill='#203b4d')
    d.text((1110,885),'Core and vestibule fit the roof outline.',font=small,fill='#203b4d')
    d.text((1110,915),'Parking stays clear of Povo 1.',font=small,fill='#203b4d')
    d.text((1110,965),'Underground extents and the larger',font=small,fill='#886329')
    d.text((1110,993),'garage connection remain unverified.',font=small,fill='#886329')
    path=out/'dimensional_fit.png';im.save(path);return path


if __name__=='__main__':print(render())
