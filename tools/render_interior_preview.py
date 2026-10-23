#!/usr/bin/env python3
"""Preview the actual offline interior mesh and generated finish swatches."""

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
    from .render_architecture_preview import rasterize
    from .build_povo_interior import COLORS
except ImportError:
    from render_blockout_preview import read_obj
    from render_architecture_preview import rasterize
    from build_povo_interior import COLORS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir",type=Path,default=Path("exports/povo1_interior_study"))
    parser.add_argument("--output",type=Path,default=Path("exports/povo1_interior_study/preview.png"))
    args=parser.parse_args()
    vertices,groups,materials=read_obj(args.asset_dir/"povo1_interior_study.obj",with_materials=True)
    fig=plt.figure(figsize=(16,11),facecolor="#edf1f2")
    fig.text(.045,.95,"POVO 1 / INTERIOR STUDY",fontsize=28,color="#193441",weight="bold")
    fig.text(.045,.91,"Actual exported mesh · approximate plan layout · provisional floor heights and finishes",fontsize=14,color="#54707b")
    for index,(level,title) in enumerate((("academic_ground","Ground level / assumed reference height"),
                                         ("academic_first","Upper level / assumed +3.6 m"))):
        faces,colors=[],[]
        for name,triangles in groups.items():
            if name.startswith(level+"_"):
                faces.extend(triangles)
                colors.extend([np.array(COLORS[materials[name]])/255]*len(triangles))
        triangles=vertices[np.array(faces)]
        normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        shade=.65+.35*np.clip(normals@np.array([.4,-.3,.866]),0,1)
        ax=fig.add_axes([.035+index*.50,.38,.43,.45])
        ax.imshow(rasterize(triangles,np.array(colors)*shade[:,None],(62,-40),width=1300,height=1100))
        ax.set_axis_off();ax.set_title(title,fontsize=14,loc="left",color="#193441")
    for index,(name,label) in enumerate((("floor_room","General floor / provisional warm grey"),
                                        ("floor_circulation","Circulation / provisional pale grey"))):
        ax=fig.add_axes([.08+index*.5,.14,.22,.17])
        image=plt.imread(args.asset_dir/(name+".png"))
        ax.imshow(np.tile(image,(4,4,1)));ax.set_axis_off()
        ax.set_title(label,fontsize=12,color="#193441")
    fig.text(.045,.08,"Courtyard void on both levels; four reserved stair openings upstairs. No flights or ceilings yet.",fontsize=13,color="#193441")
    fig.text(.045,.045,"Swatches show the generated 0.6 m tile materials. Geometry preview uses flat colors. This study is not deployed to CS2.",fontsize=11,color="#54707b")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output,dpi=140,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__=="__main__":main()
