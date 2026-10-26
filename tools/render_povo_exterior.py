#!/usr/bin/env python3
"""Render the exterior study with Pillow/numpy; no graphics driver required."""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from .build_povo_exterior import ROOT, COLORS, FACES, build, export
    from .povo_exterior_materials import OPACITY
except ImportError:
    from build_povo_exterior import ROOT, COLORS, FACES, build, export
    from povo_exterior_materials import OPACITY


def font(size):
    for name in ('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)


def triangles(boxes,meshes):
    vertices=[];colors=[];opacity=[]
    for name,lo,hi,mat in boxes:
        x,y,z=lo;a,b,c=hi
        vv=np.array([(x,y,z),(a,y,z),(a,b,z),(x,b,z),(x,y,c),(a,y,c),(a,b,c),(x,b,c)])
        for face in FACES:
            vertices.append(vv[list(face)]);colors.append(COLORS.get(mat,(150,151,145)));opacity.append(OPACITY.get(mat,1))
    for mesh in meshes:
        vv=np.array(mesh['vertices'])
        for face in mesh['faces']:
            vertices.append(vv[list(face)]);colors.append(COLORS[mesh['material']]);opacity.append(OPACITY.get(mesh['material'],1))
    return np.array(vertices),np.array(colors,dtype=float),np.array(opacity)


def perspective(boxes,meshes,camera,width=1100,height=660):
    tris,colors,opacity=triangles(boxes,meshes)
    eye=np.array(camera['position'],dtype=float);forward=np.array(camera['target'],dtype=float)-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    local=np.stack(((tris-eye)@right,-(tris-eye)@up,(tris-eye)@forward),axis=-1)
    focal=width/(2*math.tan(math.radians(camera.get('fov',70))/2))
    result=np.zeros((height,width,3),dtype=np.uint8)
    for y in range(height):result[y]=np.array([181,197,204])+(np.array([226,229,223])-np.array([181,197,204]))*y/height
    depth=np.full((height,width),np.inf)
    normal=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
    colors*= (.72+.28*np.abs(normal@np.array([.4,-.3,.866])))[:,None]
    # Opaque depth first, then back-to-front alpha panes with outward faces.
    opaque=np.where(opacity>=1)[0]
    translucent=np.where((opacity<1)&(np.sum(normal*(eye-tris.mean(axis=1)),axis=1)>0))[0]
    translucent=translucent[np.argsort(local[translucent,:,2].mean(axis=1))[::-1]]
    for index in np.concatenate((opaque,translucent)):
        vv,color,alpha=local[index],colors[index],opacity[index]
        # Clip in camera space against a 10 cm near plane, then triangulate.
        poly=[]
        for i,p in enumerate(vv):
            q=vv[(i+1)%3];pi=p[2]>=.1;qi=q[2]>=.1
            if pi:poly.append(p)
            if pi!=qi:poly.append(p+(q-p)*((.1-p[2])/(q[2]-p[2])))
        for i in range(1,len(poly)-1):
            pp=np.array([poly[0],poly[i],poly[i+1]])
            xy=pp[:,:2]/pp[:,2,None]*focal+[width/2,height/2]
            x0,y0=np.maximum(np.floor(xy.min(axis=0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(xy.max(axis=0)).astype(int),[width-1,height-1])
            if x0>x1 or y0>y1:continue
            a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
            invz=wa/pp[0,2]+wb/pp[1,2]+wc/pp[2,2]
            z=1/np.maximum(invz,1e-12);region=depth[y0:y1+1,x0:x1+1]
            mask=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(z<region)
            pixels=result[y0:y1+1,x0:x1+1]
            if alpha>=1:
                region[mask]=z[mask];pixels[mask]=np.clip(color,0,255).astype(np.uint8)
            else:pixels[mask]=np.clip(alpha*color+(1-alpha)*pixels[mask],0,255).astype(np.uint8)
    return Image.fromarray(result)


def plan(boxes,meshes,meta,out):
    im=Image.new('RGB',(1800,1700),'#eef1ed');d=ImageDraw.Draw(im)
    d.text((55,35),'POVO / EXTERIOR PLANIMETRY',font=font(36),fill='#203e46')
    d.text((55,90),'Both frontages / north road continuation / covered Povo 2 parking | 24 October 2026',font=font(22),fill='#536b70')
    bounds=(-90,-116,74,124);s=5;top=175
    def pt(x,y,left):return (left+(x-bounds[0])*s,top+(bounds[3]-y)*s)
    aerial=Image.open(ROOT/'data/reference/povo_ortho_2024.png')
    # Existing aerial covers E666000..666500 / N5103500..5104000.
    w,so,e,n=bounds
    crop=aerial.crop(((w+250)*2,(200-n)*2,(e+250)*2,(200-so)*2)).resize((round((e-w)*s),round((n-so)*s)))
    im.paste(crop,(35,top));d.text((35,140),'2024 AERIAL / approximate shared registration',font=font(20),fill='#203e46')
    d.text((935,140),'GENERATED SOURCE / north up; local metres',font=font(20),fill='#203e46')
    left=935
    def rect(r,fill,outline=None,width=1):
        a,b,c,e=r;d.rectangle((*pt(a,e,left),*pt(c,b,left)),fill=fill,outline=outline,width=width)
    rect(bounds,'#dbe3d5')
    for name,lo,hi,mat in boxes:
        if name.startswith(('car_','bay_','residential_','povo1_context','povo2_context','surface_parking','west_grass','entry_','povo1_entry')):
            if '_wheel_' in name:continue
            rect((lo[0],lo[1],hi[0],hi[1]),COLORS[mat])
    front=meta['config']['frontages']
    for key in ('povo1_walk','povo2_walk','povo2_terrace','povo1_passage'):
        rect(front[key],'#c6bfae','#89918b')
    for key in ('povo1_library_wings','povo2_annexes'):
        for r in front[key]:rect(r,'#69919a','#203e46',2)
    for mesh in meshes:
        if mesh['name'].startswith(('road_','footway_','crosswalk_')):
            v=mesh['vertices'];poly=v[4:8] if len(v)==8 else v[1:]
            d.polygon([pt(x,y,left) for x,y,z in poly],fill=COLORS[mesh['material']])
    garage=meta['config']['covered_parking'];ga,gb,gc,gd=garage['bounds']
    for l in (35,left):
        # Outline the underground building footprint; above-ground masses stay visible.
        for a,b in (((ga,gb),(ga,gd)),((ga,gd),(gc,gd)),((gc,gd),(gc,gb)),((gc,gb),(ga,gb))):
            p=pt(*a,l);q=pt(*b,l);length=math.dist(p,q)
            for start in range(0,math.ceil(length),16):
                f=start/length;g=min(1,(start+9)/length)
                d.line((p[0]+(q[0]-p[0])*f,p[1]+(q[1]-p[1])*f,p[0]+(q[0]-p[0])*g,p[1]+(q[1]-p[1])*g),fill='#167f96',width=3)
    ramp=meta['config']['garage_ramp'];a,b=ramp['centreline']
    for l in (35,left):
        d.line((*pt(a[0],a[1],l),*pt(b[0],b[1],l)),fill='#37b1c4',width=round(ramp['width']*s))
        aa=pt(a[0],a[1],l);bb=pt(b[0],b[1],l);d.line((*aa,*bb),fill='#143f4c',width=3)
        d.polygon([bb,(bb[0]-6,bb[1]+13),(bb[0]+6,bb[1]+13)],fill='#143f4c')
        for cam in meta['cameras']:
            x,y,z=cam['position'];p=pt(x,y,l);q=pt(-63,y,l)
            d.line((*p,*q),fill='#ffd777',width=2);d.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill='#ffd777')
    bridge=meta['bridge_bounds']
    rect(bridge,'#a8b5b7','#203e46',2)
    ent=meta['config']['povo2_double_entrance']
    rect(ent['lobby_bounds'],'#dbd6bd','#89918b')
    for side in ('outer','inner'):
        x=ent[side+'_x'];d.line((*pt(x,ent['lobby_bounds'][1],left),*pt(x,ent['lobby_bounds'][3],left)),fill='#254f60',width=3)
        for offset in ent['bank_offsets_y']:
            y=ent['centre_y']+offset;half=ent['clear_width']/2
            d.line((*pt(x,y-half,left),*pt(x,y+half,left)),fill='#eef1ed',width=4)
    for cam in meta['cameras']:
        x,y,z=cam['position'];p=pt(-20,y,left)
        d.text(p,cam['room'],font=font(17),fill='#183f4a',stroke_width=2,stroke_fill='#e9e5d1')
    labels=[('POVO 2',0,95),('POVO 1',0,-38),('BRIDGE',18,-16),('SURFACE\nPARKING',-48,-66),('RESIDENTIAL\nBACKDROP',-72,-64),('STRAIGHT\nRAMP',-82,24),('CROSSWALK',34,4),('LIBRARY /\nGLASS FRONT',29,-99),('P1 ENTRANCE',25,-80),('P2 ENTRANCE',26,31),('TERRACE',29,62),('COVERED PARKING\ninside Povo 2 / below',-24,79),('ROAD TO\nNORTH END',-83,104)]
    for text,x,y in labels:
        p=pt(x,y,left);d.multiline_text(p,text,font=font(17),fill='#173e47',stroke_width=2,stroke_fill='#eef1ed',spacing=4)
    for l in (35,left):
        p=pt(-83,109,l);d.text((p[0]-6,p[1]-35),'N',font=font(22),fill='#fff5d1',stroke_width=1,stroke_fill='#203e46')
        d.line((p[0],p[1]+35,p[0],p[1]),fill='#fff5d1',width=4)
        p=pt(-83,-106,l);q=pt(-63,-106,l);d.line((*p,*q),fill='#fff5d1',width=5);d.text((p[0],p[1]-30),'20 m',font=font(18),fill='#fff5d1',stroke_width=1,stroke_fill='#203e46')
    # New-photo stations are schematic route markers, never claimed as a survey.
    stations=[('64/65',5,-5),('66',-23,-5),('67',-43,-24),('68',-48,-35),('69',-48,-44)]
    for label,x,y in stations:
        p=pt(x,y,35);d.ellipse((p[0]-13,p[1]-13,p[0]+13,p[1]+13),fill='#173e47');d.text((p[0]+16,p[1]-10),'IMG 23'+label,font=font(17),fill='white',stroke_width=2,stroke_fill='#173e47')
    lines=[
        'Gold: A221-A224 view axes. Cyan: straight ramp. Dashed blue: covered basement inside the Povo 2 building.',
        'Added: west road to Povo 2 north end; both glazed frontages, entrance passage, terrace and front street.',
        'Campus integration now joins the covered exterior garage to the preserved interior parking through their overlap.',
        'Approximate footprints / elevations / bay counts. Standalone review only; no CS2 compilation, collision or traversal validation.',
        'Aerial: Comune di Trento 2024 (CC0). Photos: user references; originals preserved. No photo pixels in model textures.'
    ]
    for i,t in enumerate(lines):d.text((55,1470+i*37),t,font=font(20 if i<3 else 18),fill='#3d555e')
    im.save(out/'layout_review.png')


def front_reviews(boxes,meshes,out):
    """Dedicated front and garage views, so new geometry is actually reviewable."""
    views=[
        ('Whole campus / fronts and street',dict(position=[205,-100,170],target=[12,5,4],fov=68),'full'),
        ('Povo 1 / straight stair and glass cover from threshold',dict(position=[24.7,-73.73,5.65],target=[42,-73.73,7.0],fov=88),'full'),
        ('Povo 2 / entrance and left terrace to street',dict(position=[63,13,19],target=[41,31,5],fov=78),'full'),
        ('Povo 2 parking / roof removed for inspection',dict(position=[-65,4,28],target=[-5,70,-1.5],fov=72),'garage')
    ]
    sheet=Image.new('RGB',(2240,1550),'#eef1ed');d=ImageDraw.Draw(sheet)
    d.text((35,24),'BUILDING FRONTS / ROAD / COVERED PARKING',font=font(34),fill='#203e46')
    d.text((35,76),'Photo-guided exterior geometry. Parking roof exists in the OBJ; removed only in the labelled cutaway.',font=font(22),fill='#536b70')
    for i,(title,cam,kind) in enumerate(views):
        if kind=='garage':
            selected=[b for b in boxes if b[0].startswith('garage_') and b[0]!='garage_roof']
            selected_meshes=[m for m in meshes if m['name'].startswith(('garage_ramp','ramp_retaining','road_north'))]
        else:
            selected=boxes
            selected_meshes=[m for m in meshes if m['name']!='distant_ridge_proxy']
        view=perspective(selected,selected_meshes,cam)
        view.save(out/('front_view_'+str(i+1)+'.png'))
        x=20+(i%2)*1120;y=130+(i//2)*700
        sheet.paste(view,(x,y+30));d.text((x,y),title,font=font(22),fill='#203e46')
    d.text((35,1530),'Approximate footprints, facade bays and exterior levels. Offline source views; engine validation is recorded separately.',font=font(18),fill='#536b70')
    sheet.save(out/'fronts_review.png')


def entrance_reviews(boxes,meshes,meta,out):
    spec=meta['config']['povo2_double_entrance'];z=spec['floor_z'];cy=spec['centre_y']
    views=[
        ('Outer line / recessed street entrance',dict(position=[56,cy,z+1.6],target=[49.4,cy,z+1.45],fov=86)),
        ('Entrance lobby / looking towards reception',dict(position=[47.5,cy-2.15,z+1.6],target=[34.5,cy-1,z+1.6],fov=86)),
        ('Lobby / looking back towards the street',dict(position=[36.5,cy+2.15,z+1.6],target=[50,cy,z+1.6],fov=86)),
        ('Inner line / paired doors and central column',dict(position=[40,cy,z+1.6],target=[34.5,cy,z+1.45],fov=88))
    ]
    sheet=Image.new('RGB',(2240,1550),'#eef1ed');d=ImageDraw.Draw(sheet)
    d.text((35,24),'POVO 2 / OUTER DOORS > LOBBY > INNER DOORS',font=font(34),fill='#203e46')
    d.text((35,76),'Photos 24-23, 17-14 and 13. Paired sliding doors parked open; glass 20% transparent / 80% opaque.',font=font(22),fill='#536b70')
    for i,(title,cam) in enumerate(views):
        view=perspective(boxes,[m for m in meshes if m['name']!='distant_ridge_proxy'],cam)
        view.save(out/f'povo2_entrance_view_{i+1}.png')
        x=20+(i%2)*1120;y=130+(i//2)*700;sheet.paste(view,(x,y+30))
        d.text((x,y),title,font=font(22),fill='#203e46')
    d.text((35,1530),'Photo-guided dimensions. Door XY and floor now align with the live Povo 2 interior; native engine review follows compilation.',font=font(18),fill='#536b70')
    sheet.save(out/'povo2_double_entrance_review.png')


def render():
    boxes,meshes,meta,live=export();out=ROOT/'exports/povo_exterior'
    # Bridge is an exact geometry record, not a duplicate hand-entered coordinate.
    bridge=next(b for b in boxes if b[0]=='bridge_deck');meta['bridge_bounds']=[*bridge[1][:2],*bridge[2][:2]]
    plan(boxes,meshes,meta,out)
    front_reviews(boxes,meshes,out)
    entrance_reviews(boxes,meshes,meta,out)
    sheet=Image.new('RGB',(2240,1550),'#eef1ed');d=ImageDraw.Draw(sheet)
    d.text((35,24),'A221-A224 / WEST-FACING WINDOW STUDIES',font=font(34),fill='#203e46')
    d.text((35,76),'Cameras and window frames from current campus source; approved exterior is included in the campus build.',font=font(22),fill='#536b70')
    for i,cam in enumerate(sorted(meta['cameras'],key=lambda c:c['room'])):
        room=cam['room'].lower()
        frames=[b for b in live if f'_room_{room}_window_' in b[0] and b[3]!='window_glass']
        framed=[(n,lo,hi,'fence') for n,lo,hi,mat in frames]
        visible=[b for b in boxes if not b[0].startswith(('povo1_','entry_','canopy_'))]
        view=perspective(visible+framed,meshes,cam)
        view.save(out/f"view_{cam['room']}.png")
        x=20+(i%2)*1120;y=130+(i//2)*700
        sheet.paste(view,(x,y+30));d.text((x,y),cam['room']+' / parking and opposite facade',font=font(22),fill='#203e46')
    d.text((35,1530),'Geometry proxy; ridge, car distribution and facade bay counts are estimates. Offline renders, not game screenshots.',font=font(18),fill='#536b70')
    sheet.save(out/'window_views.png')
    # Keep originals stable; produce a named review catalogue with EXIF metadata.
    photos=[]
    for item in meta['photos']:
        p=ROOT/item['file'];im=Image.open(p);exif=im.getexif();gps=exif.get_ifd(34853)
        native={str(k):str(v) for k,v in gps.items()}
        photos.append(dict(item,capture_time=str(exif.get(306,'')),gps_native=native))
    (out/'photo_catalogue.json').write_text(json.dumps(photos,indent=2)+'\n',encoding='utf-8')
    print(out/'layout_review.png');print(out/'window_views.png')


if __name__=='__main__':render()
