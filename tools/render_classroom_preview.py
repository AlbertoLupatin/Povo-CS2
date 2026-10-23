#!/usr/bin/env python3
"""Render A224 from the exported study OBJ, hiding walls for a labelled cutaway."""
import argparse
import io
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'trento-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

try:
    from .audit_povo_interior import read_box_mesh
    from .build_povo_interior import COLORS
    from .build_povo_blockout import write_box
    from .render_architecture_preview import rasterize
except ImportError:
    from audit_povo_interior import read_box_mesh
    from build_povo_interior import COLORS
    from build_povo_blockout import write_box
    from render_architecture_preview import rasterize


def triangles_for(boxes):
    triangles=[];colors=[]
    for name,lo,hi,material in boxes:
        stream=io.StringIO();write_box(stream,name,lo,hi,0,material)
        vertices=[]
        for line in stream.getvalue().splitlines():
            if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:])))
            if line.startswith('f '):
                triangles.append([vertices[int(i)-1] for i in line.split()[1:]])
                colors.append(np.array(COLORS[material])/255)
    return np.array(triangles),np.array(colors)


def panel(ax,boxes,view,title):
    triangles,colors=triangles_for(boxes)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    shade=.7+.3*np.abs(normals@np.array([.35,-.3,.887]))
    ax.imshow(rasterize(triangles,colors*shade[:,None],view,width=1500,height=1100))
    ax.set_axis_off();ax.set_title(title,loc='left',fontsize=15,color='#193441')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset-dir',type=Path,default=Path('exports/povo1_interior_study'))
    parser.add_argument('--room',default='a224',choices=('a224','a223'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    provenance=json.loads((args.asset_dir/'provenance.json').read_text())
    level=next(l for l in provenance['levels'] if l['id']=='academic_first')
    room=next(r for r in level['rooms'] if r['id']==args.room)
    if args.output is None:args.output=args.asset_dir/f'classroom_{room["label"]}.png'
    x0,y0,x1,y1=room['footprint_local_metres'];z=level['floor_elevation_metres']-provenance['origin'][2]
    room_boxes=[];ceiling=[];plan_boxes=[]
    for name,lo,hi,material in read_box_mesh(args.asset_dir/'povo1_interior_study.obj'):
        if not name.startswith(level['id']+'_'):continue
        if name.startswith(level['id']+'_room_'+args.room+'_') and '_ceiling_' in name:
            ceiling.append((name,lo,hi,material));continue
        if '_ceiling_' in name:continue
        if material not in ('wall','courtyard_wall','floor_room','floor_circulation') and not name.startswith(level['id']+'_room_'+args.room+'_'):
            continue
        if material=='window_glass':continue # transparent in OBJ/MTL; omitted by opaque review renderer
        if any(hi[i]<=bound for i,bound in enumerate((x0-.1,y0-.1,z-.23))) or lo[0]>=x1+.1 or lo[1]>=y1+.1:continue
        a=(max(lo[0],x0-.1),max(lo[1],y0-.1),lo[2]);b=(min(hi[0],x1+.1),min(hi[1],y1+.1),hi[2])
        plan_boxes.append((name,a,b,material))
        # Retain the opposite teaching/window walls; remove both side walls.
        if material in ('wall','courtyard_wall') and (b[1]<y0+.15 or a[1]>y1-.15):continue
        room_boxes.append((name,a,b,material))
    fig=plt.figure(figsize=(16,10),facecolor='#edf1f2')
    fig.text(.04,.95,room['label']+' / CORRECTED CLASSROOM LAYOUT',fontsize=25,weight='bold',color='#193441')
    subtitle='User-confirmed A224 arrangement; counts and other dimensions estimated' if args.room=='a224' else 'P022-style room assigned to A223; photographed room location remains unknown'
    fig.text(.04,.91,subtitle,fontsize=12,color='#54707b')
    panel(fig.add_axes([.025,.3,.62,.54]),room_boxes,(43,130),'Continuous rows / ceiling and side walls hidden')
    ax=fig.add_axes([.69,.34,.275,.45])
    ax.set_facecolor('#edf1f2')
    order={'floor_room':0,'floor_wood':1,'wall':2,'courtyard_wall':2}
    for name,lo,hi,material in sorted(plan_boxes,key=lambda b:order.get(b[3],3)):
        if material not in ('floor_room','floor_wood','wall','courtyard_wall','desk_dark','seat_wood','teaching_board','projection_screen','window_frame'):continue
        color=np.array(COLORS[material])/255
        ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor=color,edgecolor='none'))
    # The clear metre is measured between finished wall face and row end.
    half=.09;aisle=room['fitout']['side_aisle_metres']
    for low,high in ((y0+half,y0+half+aisle),(y1-half-aisle,y1-half)):
        ax.add_patch(Rectangle((x0+half,low),x1-x0-2*half,high-low,facecolor='#65aebc',alpha=.25))
        xx=(x0+x1)/2
        ax.annotate('',xy=(xx,low),xytext=(xx,high),arrowprops=dict(arrowstyle='<->',color='#193441',lw=1.3))
        ax.text(xx+.2,(low+high)/2,'1 m',ha='left',va='center',fontsize=11,color='#193441')
    ax.text(x0+.20,(y0+y1)/2,'REAR WINDOWS',rotation=90,ha='left',va='center',fontsize=10,color='#193441')
    ax.text(x1-.22,(y0+y1)/2,'BOARD / FRONT',rotation=90,ha='right',va='center',fontsize=10,color='#193441')
    ax.set_xlim(x0-.2,x1+.2);ax.set_ylim(y0-.2,y1+.2);ax.set_aspect('equal');ax.set_axis_off()
    ax.set_title('Top view / clear side passages',loc='left',fontsize=14,color='#193441')
    for i,(name,label) in enumerate((('floor_wood','Wood-look floor'),('ceiling_panel','Perforated ceiling'))):
        ax=fig.add_axes([.12+i*.36,.12,.19,.15]);im=plt.imread(args.asset_dir/(name+'.png'))
        ax.imshow(np.tile(im,(3,3,1)));ax.set_axis_off();ax.set_title(label,fontsize=11,color='#193441')
    fig.text(.04,.06,f"{room['fitout']['seats']} estimated seats; continuous desk rows, 1 m clear at both sides, rear windows opposite the blackboard.",fontsize=12,color='#193441')
    fig.text(.04,.025,'Glass has no break interaction. Fixtures are geometry, without game lighting. This is an offline preview, not a CS2 screenshot.',fontsize=11,color='#54707b')
    args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=145,facecolor=fig.get_facecolor());plt.close(fig)
    print(f'Saved {args.output}')


if __name__=='__main__':main()
