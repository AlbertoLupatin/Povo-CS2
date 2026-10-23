#!/usr/bin/env python3
"""Render the actual exported facade/bridge meshes (numpy/matplotlib optional)."""

import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "trento-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    from .render_blockout_preview import read_obj
    from .povo_architecture import MATERIALS
except ImportError:
    from render_blockout_preview import read_obj
    from povo_architecture import MATERIALS


def rasterize(triangles, colors, view, width=1400, height=600):
    """Orthographic depth-buffer render; thin facade layers need real occlusion."""
    elevation, azimuth = np.radians(view)
    camera=np.array([np.cos(elevation)*np.cos(azimuth),
                     np.cos(elevation)*np.sin(azimuth),np.sin(elevation)])
    right=np.cross([0.,0.,1.],camera);right/=np.linalg.norm(right)
    up=np.cross(camera,right)
    projected=np.stack((triangles@right,-triangles@up,triangles@camera),axis=-1)
    low=projected[:,:,:2].reshape(-1,2).min(axis=0)
    high=projected[:,:,:2].reshape(-1,2).max(axis=0)
    scale=min((width-60)/(high[0]-low[0]),(height-50)/(high[1]-low[1]))
    projected[:,:,:2]=(projected[:,:,:2]-(low+high)/2)*scale+[width/2,height/2]
    result=np.full((height,width,3),[237,241,242],dtype=np.uint8)
    depth=np.full((height,width),-np.inf)
    for points,color in zip(projected,colors):
        x0,y0=np.maximum(np.floor(points[:,:2].min(axis=0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(points[:,:2].max(axis=0)).astype(int),[width-1,height-1])
        if x1<x0 or y1<y0:continue
        a,b,c=points
        denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(denominator)<1e-8:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
        xx=xx+.5;yy=yy+.5
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
        wc=1-wa-wb
        z=wa*a[2]+wb*b[2]+wc*c[2]
        region=depth[y0:y1+1,x0:x1+1]
        mask=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(z>region)
        region[mask]=z[mask]
        result[y0:y1+1,x0:x1+1][mask]=np.clip(np.array(color)*255,0,255).astype(np.uint8)
    return result


def mesh_panel(fig, rectangle, vertices, groups, materials, prefix, title, view):
    axes = fig.add_axes(rectangle, facecolor="#edf1f2")
    faces, colors = [], []
    for name, triangles in groups.items():
        if name.startswith(prefix):
            faces.extend(triangles)
            colors.extend([MATERIALS.get(materials[name], (.65,.63,.59))] * len(triangles))
    if not faces:
        raise ValueError(f"No exported objects matching {prefix}")
    triangles = vertices[np.array(faces)]
    normals = np.cross(triangles[:,1]-triangles[:,0], triangles[:,2]-triangles[:,0])
    normals /= np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    intensity = .65 + .35 * np.clip(normals @ np.array([.5,-.3,.8124]),0,1)
    minimum, maximum = triangles.reshape(-1,3).min(axis=0), triangles.reshape(-1,3).max(axis=0)
    span = maximum-minimum
    # Facades have very little depth; show a short real-mesh section at its
    # actual height rather than stretching a 97 m facade into a square.
    if prefix != "arch_bridge":
        centre = (minimum[1]+maximum[1])/2
        minimum[1],maximum[1] = centre-min(10,span[1]/2), centre+min(10,span[1]/2)
        # Long curtain panels and transoms cross the section. Clip those boxes'
        # triangle coordinates for this review only; the exported model is intact.
        triangles=triangles.copy()
        triangles[:,:,1]=np.clip(triangles[:,:,1],minimum[1],maximum[1])
    axes.imshow(rasterize(triangles,np.array(colors)*intensity[:,None],view))
    axes.set_axis_off()
    axes.set_title(title,loc="left",fontsize=14,pad=5,color="#193441",weight="bold")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir",type=Path,default=Path("exports/povo_blockout"))
    parser.add_argument("--output",type=Path,default=Path("exports/povo_blockout/architecture_preview.png"))
    args=parser.parse_args()
    vertices,groups,materials=read_obj(args.asset_dir/"povo_blockout.obj",with_materials=True)
    fig=plt.figure(figsize=(16,11),facecolor="#edf1f2")
    fig.text(.045,.95,"POVO / EXTERIOR DETAIL PASS",fontsize=27,weight="bold",color="#193441")
    fig.text(.045,.91,"Actual exported geometry · photo-guided appearance · estimated dimensions",fontsize=14,color="#54707b")
    mesh_panel(fig,[.04,.51,.43,.32],vertices,groups,materials,"arch_povo1_low_east_",
               "Povo 1: glazed facade / 20 m section",(12,10))
    mesh_panel(fig,[.53,.51,.43,.32],vertices,groups,materials,"arch_povo2_core_east_",
               "Povo 2: stone and windows / 20 m section",(12,10))
    mesh_panel(fig,[.1,.12,.8,.33],vertices,groups,materials,"arch_bridge",
               "Connecting bridge: deck, roof, posts and louvers",(20,35))
    fig.text(.045,.075,"Static exterior scenery. Glazing is opaque placeholder material; windows do not break.",fontsize=13,color="#193441")
    fig.text(.045,.043,"Reference IDs and assumptions are recorded in provenance.json. This is an offline model preview, not a CS2 screenshot.",fontsize=11,color="#54707b")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output,dpi=140,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
