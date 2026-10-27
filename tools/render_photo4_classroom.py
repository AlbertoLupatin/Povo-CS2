"""Offline A103 photo4 review from current in-memory campus geometry."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont

try:
    from .build_povo_campus import ROOT,build_geometry,COLORS
except ImportError:
    from build_povo_campus import ROOT,build_geometry,COLORS


def cutaway(triangles,colors,view,width=1500,height=1150):
    """Orthographic depth-buffer rasterization of source triangles."""
    elevation,azimuth=np.radians(view)
    camera=np.array([np.cos(elevation)*np.cos(azimuth),np.cos(elevation)*np.sin(azimuth),np.sin(elevation)])
    right=np.cross([0.,0.,1.],camera);right/=np.linalg.norm(right)
    up=np.cross(camera,right)
    projected=np.stack((triangles@right,-triangles@up,triangles@camera),axis=-1)
    low=projected[:,:,:2].reshape(-1,2).min(axis=0);high=projected[:,:,:2].reshape(-1,2).max(axis=0)
    scale=min((width-60)/(high[0]-low[0]),(height-50)/(high[1]-low[1]))
    projected[:,:,:2]=(projected[:,:,:2]-(low+high)/2)*scale+[width/2,height/2]
    result=np.full((height,width,3),[237,241,242],dtype=np.uint8);depth=np.full((height,width),-np.inf)
    for points,color in zip(projected,colors):
        x0,y0=np.maximum(np.floor(points[:,:2].min(axis=0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(points[:,:2].max(axis=0)).astype(int),[width-1,height-1])
        if x1<x0 or y1<y0:continue
        a,b,c=points;denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator)<1e-8:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator;wc=1-wa-wb
        zz=wa*a[2]+wb*b[2]+wc*c[2];region=depth[y0:y1+1,x0:x1+1]
        mask=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(zz>region)
        region[mask]=zz[mask];result[y0:y1+1,x0:x1+1][mask]=np.clip(color*255,0,255).astype(np.uint8)
    return Image.fromarray(result)


def render(output=ROOT/'exports/povo_campus/a103_photo4_review.png'):
    _,_,boxes,levels,_=build_geometry()
    level=next(l for l in levels if l.get('user_floor')==-1)
    room=next(r for r in level['rooms'] if r['id']=='a103')
    x0,y0,x1,y1=room['footprint_local_metres'];z=level['floor_elevation_metres']-370
    prefix=level['id']+'_room_a103_'
    selected=[];glass=[]
    for name,lo,hi,material in boxes:
        if not name.startswith(prefix):continue
        lo=(max(lo[0],x0-.06),max(lo[1],y0-.06),lo[2])
        hi=(min(hi[0],x1+.06),min(hi[1],y1+.06),hi[2])
        if any(a>=b for a,b in zip(lo,hi)):continue
        if any(s in name for s in ('ceiling','projector','diffuser')):continue
        if material=='window_glass':
            glass.append((name,lo,hi,material));continue
        if material in ('wall','courtyard_wall'):
            # Low cut edges identify the footprint without hiding the glazing/front.
            if lo[2]>z+.16:continue
            hi=(*hi[:2],min(hi[2],z+.16))
        if any(a>=b for a,b in zip(lo,hi)):continue
        selected.append((name,lo,hi,material))
    if not selected or not glass:raise ValueError('A103 furniture and glazing are required')
    colors=dict(COLORS,review_glass=(70,156,194))
    # Edge-only panes: actual source extents, no opaque replacement glass plane.
    edges=[]
    for name,lo,hi,_ in glass:
        axis=0 if hi[0]-lo[0]<hi[1]-lo[1] else 1
        other=1-axis
        for fixed in (lo[other],hi[other]):
            a=list(lo);b=list(hi);a[other]=fixed-.012;b[other]=fixed+.012
            edges.append((name+'_edge_v',tuple(a),tuple(b),'review_glass'))
        for fixed in (lo[2],hi[2]):
            a=list(lo);b=list(hi);a[2]=fixed-.012;b[2]=fixed+.012
            edges.append((name+'_edge_h',tuple(a),tuple(b),'review_glass'))
    indices=np.array([(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
                      (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)])
    triangles=[];tints=[]
    for _,lo,hi,material in selected+edges:
        vertices=np.array([(x,y,h) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for h in (lo[2],hi[2])])
        faces=vertices[indices];triangles.extend(faces);tints.extend([np.array(colors[material])/255]*12)
    triangles=np.array(triangles);tints=np.array(tints)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    shade=.74+.26*np.abs(normals@np.array([.35,-.3,.887]))
    image=Image.new('RGB',(2500,1600),'#edf1f2');draw=ImageDraw.Draw(image)
    title=ImageFont.truetype('arial.ttf',44);heading=ImageFont.truetype('arial.ttf',27);font=ImageFont.truetype('arial.ttf',24)
    def text(x,y,label,face=font,color='#193441'):draw.text((x,y),label,font=face,fill=color)
    text(70,45,'A103 / PHOTO 4 CLASSROOM REVIEW',title)
    text(70,115,'User-confirmed A103; current source geometry. A103-A106 family correction only.',heading,'#54707b')
    text(70,190,'Cutaway / ceiling hidden; glass shown by blue pane edges',heading)
    image.paste(cutaway(triangles,tints*shade[:,None],(38,65)),(20,240))
    text(1640,190,'Top view / two glazed faces',heading)
    scale=min(680/(x1-x0),920/(y1-y0));left,top=1650,300
    def point(x,y):return (left+(x-x0)*scale,top+(y1-y)*scale)
    for name,lo,hi,material in sorted(selected,key=lambda b:(0 if b[3].startswith('floor_') else 1,b[1][2])):
        if material=='window_frame':continue
        draw.rectangle((*point(lo[0],hi[1]),*point(hi[0],lo[1])),fill=colors[material])
    for _,lo,hi,_ in glass:
        if hi[0]-lo[0]<hi[1]-lo[1]:ends=(*point((lo[0]+hi[0])/2,lo[1]),*point((lo[0]+hi[0])/2,hi[1]))
        else:ends=(*point(lo[0],(lo[1]+hi[1])/2),*point(hi[0],(lo[1]+hi[1])/2))
        draw.line(ends,fill='#2688b4',width=4)
    text(1670,top+(y1-y0)*scale+25,'GLAZED TEACHING FRONT',font,'#267b9e')
    fitout=room['fitout']
    text(70,1360,'Green chairs and straight dark shared rows; freestanding board before the glazed teaching front.')
    text(70,1400,'Wood teacher desk and low platform; opaque wall faces are cut down for this review only.')
    text(70,1450,f"{len(fitout['rows'])} rows / {fitout['seats']} seats in the source estimate; footprint {x1-x0:.1f} x {y1-y0:.1f} m is provisional.",font,'#54707b')
    text(70,1490,'Counts, dimensions, compass placement and glazing subdivisions remain approximate; room identity is confirmed.',font,'#54707b')
    text(70,1540,'Offline geometry review without game lighting. This is not an engine screenshot or a new movement test.',font,'#54707b')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);image.save(output)
    if output.stat().st_size<=0:raise ValueError('Empty A103 review image')
    print(output)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'exports/povo_campus/a103_photo4_review.png')
    render(parser.parse_args().output)
