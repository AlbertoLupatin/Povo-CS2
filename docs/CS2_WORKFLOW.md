# CS2 development workflow

## Why CS2

The user selected CS2 and has access to Windows for editing and compilation. It fits the chosen compact, small-team campus scope and supplies the FPS systems. Valve supports map uploads, offline Workshop testing and community-server hosting through the [Maps Workshop](https://store.steampowered.com/news/posts/?appids=730&enddate=1699055103&feed=steam_community_announcements).

The decision is about the intended match experience, not a claimed hard map-size limit. Full-length roads between districts introduce travel, sightline and production costs even if geometry fits the engine.

Alternatives considered: Black Ops III has official PC mod/map tools, CS:GO has legacy tooling and a current unlisted Steam release, Arma Reforger better accommodates broad terrain, and Xonotic/NetRadiant provides native Linux authoring with a different arena combat style. None is the current project target.

## Workstation checks

Local inspection on 22 October 2026 found Fedora 44, Intel Core Ultra 5 225H (14 logical CPUs), integrated Intel Arrow Lake graphics reported by PCI as `[Arc Pro 130T/140T]`, and approximately 30.6 GiB exposed RAM (32 GB installed). The PCI family label does not establish a precise graphics marketing model or Hammer compatibility.

QGIS, Blender and GDAL command-line tools were not found in this shell. No applications were installed by this setup pass. Steam is present.

The restricted shell's Vulkan probe saw only the software renderer and could not access the desktop display. This is **not a benchmark or a diagnosis of the host graphics driver**. Test hardware acceleration in the actual desktop/Windows session.

Valve states that [Workshop Tools are Windows-only](https://github.com/ValveSoftware/csgo-osx-linux/issues/3266). Its [Hammer announcement](https://store.steampowered.com/news/posts/?appids=730&enddate=1686088105&feed=steam_community_announcements) requires ray-tracing-capable graphics for full lighting/preview functionality. Windows access resolves the OS constraint; successful compilation on the intended GPU remains to be tested.

## 1. Prove the Windows toolchain

1. Install CS2 and its Workshop Tools through Steam on the Windows build machine. Consult [Valve's installation documentation](https://developer.valvesoftware.com/wiki/Counter-Strike_2_Workshop_Tools/Installing_and_Launching_Tools) for the installed release. The documentation endpoint was access-restricted to this research session, so exact current UI labels were not verified here.
2. Create a small test addon using the tools' own sample/templates. Add floor, enclosing geometry, lighting and valid spawn entities for the test mode.
3. Compile it, load it in CS2, and verify movement and lighting. Keep the build log and game/tool version. This establishes actual GPU/tool compatibility.
4. Import a measured cube and doorway from Blender. Confirm dimensions in Hammer and with the player. Record axis mapping and export/import settings; do not apply an assumed metres-to-engine-units conversion twice.
5. Package and host the map in a private test session/community server; connect a second client. A local solo preview does not prove multiplayer distribution.

These checks must succeed before spending heavily on detailed campus assets. A test room is only a toolchain check, not the Trento deliverable.

## 2. Prepare the geography on Fedora

1. Begin with the selected Povo blockout crop and refine its playable boundary through traversal testing. Mesiano is a later candidate.
2. In QGIS, acquire the relevant DTM, building outlines and supporting features; inspect source headers and licences. Clip to the area plus a visual buffer.
3. Reproject horizontal coordinates to the agreed metre-based CRS. Verify vertical references before combining sources. Retain the original authoritative files.
4. Use the Povo blockout's shared local origin `(666250, 5103800, 370)` in source metres. Use `x = easting - E0`, `y = northing - N0`, `z = elevation - Z0` in the Blender master. Keep all campus assets on this same transform. The Z offset retains the source orthometric height reference.
5. Export a clipped ASCII grid for [the terrain utility](TERRAIN_TOOL.md), or construct terrain through a verified GIS/Blender workflow. The utility is a reference mesh exporter; topology, UVs, mesh budgets and collision still need authoring.
6. Build recognizable building volumes, streets and paths. DTM is ground; DSM includes objects; DBM helps roof estimates. Do not turn tree-canopy DSM heights into walking terrain.
7. Check a few known features against current imagery and site references. Mark missing heights, old footprints and interpolated areas explicitly.

Keep original metric geography independent of Hammer-specific assets so source corrections remain traceable.

## 3. Build the actual map in Hammer

Use the metric master as reference and import suitable prepared model assets through the installed Source 2 model pipeline. [ModelDoc](https://developer.valvesoftware.com/wiki/ModelDoc_Editor) is a reference entry point; confirm supported formats/options in the installed tools. An OBJ/FBX by itself is not a playable map.

Author/edit world geometry, materials, collision, walkable stairs and slopes, lighting, visibility boundaries and navigation in the target toolchain. Divide architectural models into manageable pieces; do not import a single opaque city mesh and assume it will perform or collide correctly.

Begin with a simple native mode for movement/scale testing. Choose Wingman, standard bomb defusal or another supported mode after the campus footprint is evaluated. Add the mode's required entities, spawns and objectives from current CS2 examples; do not copy legacy CS:GO entity assumptions unchecked.

For the checked-in Povo blockout, regenerate exports and prepare the VMAP before
deployment:

```sh
python tools/build_povo_blockout.py --force
python tools/cs2_project.py place-blockout
python tools/cs2_project.py compile --target map
```

`place-blockout` deterministically inserts the pitched geographic model, removes
stock-room placeholders, normalizes the Wingman buy zones, relocates starts and
the bomb target, fits the sky/post-processing/lightmap volumes, and adds nav,
probe, soundscape, and minimap support. A repeated run must report `unchanged`.
The map compile now refreshes the ModelDoc model first because Valve's map-only
compiler otherwise consumes stale model physics/material output. Keep route
choices in these reproducible sources or synchronize reviewed Hammer changes
back to Git; never leave the only working copy inside the installed addon.

Bring every major geometry change back into a playable build. Prioritize recognizability, navigability and collision before façade detailing.

## 4. Test and package

Maintain a short playtest record: game/build version, hardware, resolution and settings, player count, frame-time observations, route problems, spawn safety, collision issues and outcome. Measure performance on the Fedora play machine as well as the Windows build machine if they differ.

The [design brief](MAP_DESIGN.md) defines the acceptance gates: two real clients, completed matches, representative team-size balance tests, reproducible packaging, and a clean-install check with every custom dependency included. Workshop availability does not guarantee automatic matchmaking or a trouble-free peer-hosted lobby; verify the actual chosen hosting route.

Release includes the compiled map package, source assets, build instructions, credits/licences and known limitations. Public Workshop publication is a later release action.
