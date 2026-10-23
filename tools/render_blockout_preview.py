#!/usr/bin/env python3
"""Render the exported Povo OBJ as a geospatial review figure (requires numpy/matplotlib)."""

import argparse
import json
import os
from pathlib import Path
import tempfile

# Keep plotting caches out of the user's configuration directory.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "trento-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colormaps
from matplotlib.colors import LightSource, Normalize
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def read_obj(path, *, with_materials=False):
    vertices, groups, current, materials = [], {}, "default", {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append([float(v) for v in parts[1:4]])
        elif parts[0] == "o":
            current = parts[1]
        elif parts[0] == "usemtl":
            materials[current] = parts[1]
        elif parts[0] == "f":
            face = [int(v.split("/")[0]) - 1 for v in parts[1:]]
            if len(face) != 3:
                raise ValueError("Expected triangulated OBJ")
            groups.setdefault(current, []).append(face)
    result = (np.array(vertices), groups)
    return (*result, materials) if with_materials else result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/povo_blockout.json"))
    parser.add_argument("--asset-dir", type=Path, default=Path("exports/povo_blockout"))
    parser.add_argument("--output", type=Path, default=Path("exports/povo_blockout/preview.png"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    vertices, groups, materials = read_obj(args.asset_dir / "povo_blockout.obj", with_materials=True)
    origin = np.array(config["origin"])
    bounds = config["terrain_bounds"]
    ortho_bounds = config["orthophoto_bounds"]
    root = args.config.resolve().parent.parent
    fig = plt.figure(figsize=(16, 10), facecolor="#f2f4f5")
    fig.suptitle("POVO  /  POLO FERRARI", x=.055, y=.96, ha="left", fontsize=24, weight="bold", color="#192d3b")
    fig.text(.055, .915, "Geographic blockout v0.1  ·  200 × 300 m study area  ·  Local metres, north = +Y", color="#4b5962", fontsize=12)
    left = fig.add_axes([.05, .16, .34, .70])
    left.imshow(plt.imread(root / config["orthophoto"]), extent=[ortho_bounds[0], ortho_bounds[2], ortho_bounds[1], ortho_bounds[3]])
    for block in config["buildings"]:
        west, south, east, north = block["bounds"]
        left.add_patch(Rectangle((west, south), east-west, north-south,
                                fill=False, edgecolor="#fff3ad", linewidth=1.1))
    left.set_xlim(bounds[0], bounds[2])
    left.set_ylim(bounds[1], bounds[3])
    left.set_xticks([])
    left.set_yticks([])
    left.set_title("2024 aerial reference + approximate roof envelopes", fontsize=10, loc="left", pad=10)
    for text, east, north in [("POVO 2",666205,5103860),("POVO 1",666205,5103738)]:
        left.text(east,north,text,fontsize=9,color="white",weight="bold",rotation=90,
                  ha="center",va="center",bbox={"facecolor":"#192d3b","alpha":.8,"edgecolor":"none","pad":4})
    left.annotate("N",xy=(666165,5103937),xytext=(666165,5103916),
                  arrowprops={"color":"white","lw":1.8},color="white",ha="center",weight="bold")
    left.plot([666165,666215],[5103663,5103663],color="white",lw=3)
    left.text(666190,5103668,"50 m",color="white",ha="center",fontsize=9)
    right = fig.add_axes([.405, .16, .57, .70], projection="3d", facecolor="#f2f4f5")
    terrain_faces = []
    architecture_faces, architecture_colors = [], []
    palette = {"building_mass": (.65,.63,.59), "facade_glazing": (.16,.32,.35),
               "facade_frame": (.70,.74,.73), "facade_stone": (.78,.75,.65),
               "facade_dark": (.15,.18,.20), "gameplay_cover": (.32,.48,.62),
               "gameplay_boundary": (.16,.19,.22)}
    for name, faces in groups.items():
        if "calibration" in name:
            continue
        if "terrain" in name:
            terrain_faces.extend(faces)
        else:
            architecture_faces.extend(faces)
            architecture_colors.extend([palette.get(materials.get(name), (.65,.63,.59))] * len(faces))
    if not terrain_faces:
        raise ValueError("No terrain object found in exported OBJ")
    triangles = vertices[np.array(terrain_faces)]
    normals = np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normals /= np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    shade = LightSource(azdeg=315, altdeg=50).shade_normals(normals)
    colors = colormaps["terrain"](Normalize(vmin=320-origin[2],vmax=420-origin[2])(triangles[:,:,2].mean(axis=1)))
    colors[:,:3] *= (.45 + .55*shade[:,None])
    combined = triangles
    edges = np.zeros((len(triangles),4))
    widths = np.zeros(len(triangles))
    if architecture_faces:
        architecture = vertices[np.array(architecture_faces)]
        normals = np.cross(architecture[:,1]-architecture[:,0],architecture[:,2]-architecture[:,0])
        normals /= np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        intensity = .65 + .35*np.clip(normals @ np.array([-.4,-.4,.8246]),0,1)
        building_colors = np.ones((len(architecture),4))
        building_colors[:,:3] = np.array(architecture_colors)*intensity[:,None]
        combined = np.concatenate([triangles,architecture])
        colors = np.concatenate([colors,building_colors])
        edges = np.concatenate([edges,np.tile([.33,.39,.42,1],(len(architecture),1))])
        widths = np.concatenate([widths,np.full(len(architecture),.05)])
    # One collection lets mplot3d sort building and terrain triangles together.
    right.add_collection3d(Poly3DCollection(combined,facecolors=colors,edgecolors=edges,linewidths=widths))
    right.set_xlim(bounds[0]-origin[0],bounds[2]-origin[0])
    right.set_ylim(bounds[1]-origin[1],bounds[3]-origin[1])
    right.set_zlim(-30,45)
    right.set_box_aspect((200,300,75))
    right.view_init(elev=38, azim=-60)
    right.set_xlabel("East (m)",labelpad=8,fontsize=9)
    right.set_ylabel("North (m)",labelpad=8,fontsize=9)
    right.set_zlabel("Height above 370 m (m)",labelpad=8,fontsize=8)
    right.tick_params(labelsize=8)
    right.set_title("Exported terrain and photo-guided exterior detail",fontsize=11,pad=10)
    fig.text(.055,.105,"Measured terrain; estimated architectural detail. Offline source preview; CS2 validation pending.",fontsize=12,weight="bold",color="#192d3b")
    fig.text(.055,.065,"Sources: PAT LiDAR DTM/DBM 2014–2018 (CC BY 4.0); Comune di Trento orthophoto 2024 (CC0).\nTerrain sampled at 2 m for this blockout. Source elevation cells: 0.5 m. Vertical exaggeration: none.",fontsize=10,color="#4b5962",linespacing=1.5)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.output,dpi=140,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
