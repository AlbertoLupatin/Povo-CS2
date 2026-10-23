# Povo CS2: Windows import and first-playable handoff

## Verified state on 23 October 2026

The Workshop Tools are installed and the repository deploys a `trento_povo`
addon through `tools/cs2_project.py`. ModelDoc compiles the full Povo visual OBJ
at 39.37007874 Hammer units per metre and a separate arena-only collision OBJ.
The deterministic VMAP preparation removes the stock room, fits the sky and
post-processing shell, adds lightmap/probe/nav/minimap support, and relocates the
Wingman entities into the compact east forecourt. GPU lighting and a 503-area nav
mesh compile successfully on the Intel Arc 130T.

The packaged map loads as `trento_povo`; a human reached the configured CT start
and three bots joined its listen server. The latest local VPK is 9,312,611 bytes
with SHA-256
`52e7292dd29db1cb17d918aa5d1d799dc6c3505f6b56a98645f808c01aea7b1f`.
See [the worklog](WORKLOG.md) for exact build evidence and limitations.

The steps below remain acceptance criteria where they have not been superseded.
Direct calibration-cube measurement, a completed bot round, buy/bomb behavior,
visual/performance inspection, clean installation, and independent-client
multiplayer testing are still open.

Linux continuation now supplies schematic radar sources in `exports/povo_radar/`
and a `compile --target radar` path. The full `--target all` build orders model,
map, then radar and restores the matching overview. These radar resources have
not been compiled in Windows or added to a verified VPK. Follow
[the radar workflow](POVO_RADAR.md) before claiming that gate complete.

Target: Polo Ferrari, Povo; a compact campus map for small-team play. The OBJ assets
are geographic working material. They are **not a playable map**, and importing a
render mesh does not establish working collision or multiplayer.

## 1. Establish the build machine

Install CS2 and its Workshop Tools on the Windows machine, then create an addon
named `trento_povo`. Open Hammer, ModelDoc and the Material Editor from that addon.
Use the installed release's examples and UI to create and compile a tiny test map
with a floor, lighting and the required spawn/game entities. Load the result in
CS2 and walk around it before importing the campus.

Record the Windows version, GPU/driver, CS2/tool version, build preset and build log.
Windows access is confirmed; a successful build on the intended hardware is still
unverified. Valve's [Windows-only tools statement](https://github.com/ValveSoftware/csgo-osx-linux/issues/3266)
and [ray-tracing requirement announcement](https://store.steampowered.com/news/posts/?appids=730&enddate=1686088105&feed=steam_community_announcements)
explain why this is the first gate. The laptop's integrated-GPU family name alone
does not demonstrate compatibility.

## 2. Inspect the metric master in Blender

Copy the complete exported asset directory, including OBJ, matching MTL, referenced
images and metadata. Keep relative paths intact. Import the OBJ in Blender using
**File → Import → Wavefront (.obj)**. Matching MTL files carry basic material
assignments; object splitting and axis/scale controls are documented in the
[Blender OBJ manual](https://docs.blender.org/manual/en/4.1/files/import_export/obj.html).
The installed Blender version may present these controls differently.

Use these checks for this project's master:

- Coordinates are local metres: X east, Y north, Z up. Read the export metadata
  for the actual origin and vertical offset. Preserve them for all imports.
- Disable automatic bounding-box clamping; ensure a one-unit edge remains one
  metre in the master. Do not separately centre each building or terrain tile.
- Check that north is in +Y, slopes rise in +Z, and terrain normals face upward.
- Inspect material preview and the image orientation. Aerial imagery is a
  reconstruction aid; façades, ground materials and missing interiors still need
  authoring. Existing trees/shadows in an orthophoto are not 3D geometry.
- Save a `.blend` master. Export individual terrain/architecture pieces for the
  engine so they can be corrected, hidden and optimized independently.

## 3. Calibrate one object before the campus

Make a calibration object with a **1 m × 1 m × 1 m** cube and an asymmetric marker
on its east side. Export only this object first. FBX is a practical interchange
candidate for ModelDoc; retain the OBJ master as a separate source.

Create a model in ModelDoc using the imported render mesh, assign a Source 2
material, configure collision and compile the model. Then place it in the tiny
Hammer test map. Keep all mesh/texture sources in the addon's **content** tree,
and preserve the `.vmdl` and `.vmat` sources along with the generated resources.
Do not expect an OBJ MTL or Blender shader graph to become a ready-to-use CS2
material without checking its conversion.

Measure the imported cube in Hammer; check the marker direction and up axis.
Record Blender's unit settings, export scale/axes, ModelDoc import settings and
the resulting Hammer dimensions. Select the project metres-to-game-units mapping
once and apply it in one place. Verify a doorway and step with the CS2 player
before freezing that mapping. A metre-scale GIS model does not itself define a
playable doorway or staircase.

The [cs2asset author's repository](https://github.com/gronnmann/cs2asset) documents
a third-party automated model/material import route using Blender and Valve's
compiler. It is a possible future convenience, **not installed or validated here**.
The initial handoff uses the installed tools directly to expose scale, material
and collision problems clearly.

## 4. Assemble the first campus map in Hammer

Use the calibrated settings for the campus pieces, with the same origin and
placement transform. Begin with terrain, two recognizable building volumes and
one continuous route. The imported masses are references for reconstructing
entrances and circulation, not verified interiors.

Build walkable collision deliberately. Test slopes, stairs, wall contacts and
model seams in CS2; visual geometry alone is insufficient. Add lighting, map
boundaries, navigation, valid spawns and the chosen mode's objectives using the
current CS2 examples. Save the source `.vmap` from Hammer and compile it. Add
more campus area only after this small portion works in game.

No `.vmap` schema or compiler command line has been invented for this workspace.
The Valve wiki was access-restricted during research, and no usable CS2 editor
installation was found in the inspected standard local Steam library paths.
Exact ModelDoc node options and build commands must be recorded from the Windows
installation after the calibration succeeds.

## 5. Accept the first playable build

| Check | Required evidence |
| --- | --- |
| Toolchain | Tiny map builds and runs; retain successful log and versions |
| Geographic import | Cube dimensions/orientation and shared campus origin verified |
| Traversal | Continuous route; no falling through terrain, stuck stairs or invisible barriers |
| Gameplay | Correct team spawns, working chosen-mode objectives and a completed match |
| Multiplayer | Two independent CS2 clients connect to the same packaged map and complete a match |
| Packaging | Second client can load every custom asset without the source workspace |
| Performance | Record frame-time observations on the Fedora laptop, settings and player count |

Package and use a private test server/session appropriate to the installed CS2
release. A solo editor launch or bot match does not satisfy the two-client gate.
Public Workshop publication remains a later release step. Representative team-size
tests come after this functional check and establish whether the layout is balanced.
