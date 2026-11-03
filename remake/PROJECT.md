# Povo campus for CS2: project guide

From-scratch rebuild of the University of Trento Povo campus (Polo Ferrari) as a CS2 map.
The buildings are generated from data: real terrain, official plans and reference photos.
The output is native Hammer geometry in the addon `povo_remake`.
This file is the single overview: what exists, how it is made, how to work on it, and what comes next.

Last updated: 2 November 2026.

---

## 1. Where things stand

Everything below has been built and checked in game with unlit test builds.

| Part | State |
| --- | --- |
| Site | LiDAR terrain (2 m), OSM roads/paths/parking, grass from the orthophoto, ~520 trees (smaller young street trees), other buildings as blocks, overcast sky, light haze |
| Povo 1 | All three floors room by room, stone + glass facades, courtyard with emergency stair, planters, terraces, square-spiral stairwells, -1 outside doors from the annotated map, bridge doorway |
| Povo 2 | Main block on four levels (-2 to 1) round the courtyard, four stair cores, lifts, garage with columns, street strip under the plaza, Holes 1-3 (Hole 2 with its steel stair), the two frosted glass boxes |
| Bridge | Louvred, glass inside, diagonal braces, Povo 2 floor 1 to Povo 1 floor +1 |
| East block | Mensa (bar/kitchen -1, dining hall 0), library (reading rooms, study booths), glass roof over the passage, red entrance stair from Via Sommarive, red -1 lane |

Not done yet:
- interior furniture
- door leaves (doorways are open)
- breakable glass, wallbang rules
- spawns and bombsites, nav mesh
- sounds and ambience
- mountain skybox
- final lit build

**Lit builds need a longer GPU timeout (solved 2 November 2026).**
With Povo 2 included, lightmap block 3 takes ~4.2 s on the RTX 2060; Windows' default 2 s limit reset the GPU ("GPU hang", TDR).
With TdrDelay at 10 s the full bake succeeds (`povo_site_lit`, 3 min 36 s). Splitting the bake into smaller blocks is not a fix: the legacy project tried it and got a streaked lightmap.
The setting (admin PowerShell, then reboot), already applied on this PC:

```powershell
New-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\GraphicsDrivers" -Name TdrDelay -PropertyType DWord -Value 10 -Force
```

To undo it, delete the `TdrDelay` value from that key and reboot.

---

## 2. Agreed order of work

1. **Your layout and look changes**, building by building and floor by floor (section 8 explains how to send them).
2. **Manual fixes in Hammer** for the parts easier to do by hand (section 7).
3. **Gameplay**: spawns and bombsites, opening doors, breakable glass panes, wallbangable or solid walls, bot nav mesh.
4. **Atmosphere**: furniture, sounds and ambience, the real mountains in a 3D skybox.
5. **Final build**: TdrDelay reminder, lit bake at full resolution, visibility pass.

---

## 3. Sources

| Source | Where | Used for |
| --- | --- | --- |
| PAT LiDAR 2014, DTM/DBM/DSM first, 0.5 m (CC BY 4.0) | `data/lidar/` | Terrain, building and roof heights, floor levels, trees |
| Comune di Trento orthophoto 2024 (CC0) | `data/ortho/` | Grass/paving classification, checking |
| OpenStreetMap (ODbL) | `data/osm/`, `data/derived/site_layers.json` | Outlines, roads, paths, trees, Povo 1 -1 rooms |
| Povo 1 fire plans, floors -1/0/+1 (photos, rectified) | `data/plans/povo1_floor*.png` | Povo 1 rooms |
| Povo 2 official evacuation plans, ground and semi-basement (rectified) | `data/plans/povo2_floor*.png` | Povo 2 rooms |
| Povo 2 -2 plan, floor +1 department directory | `../Povo-CS2/data/reference/povo_photos/walk_2026-10-27` images 37, 31 | Povo 2 -2 and +1 |
| Canteen and library plans | same folder, images 12, 13, 15 | Mensa, library |
| Annotated maps (doors, stairs) and stair sections | `../Povo-CS2/data/reference/povo_plans/mappe-povo/` | Povo 1 doors and spiral stairs |
| Labelled aerials (reference only) | `../Povo-CS2/data/reference/povo_earth_aeral/` | Levels, holes, boxes, facades |
| ~150 photos | `../Povo-CS2/data/reference/povo_photos/` | Materials and details |

Google Earth imagery is used only as visual reference, never for textures or geometry.

---

## 4. Frames, scale, levels

- **Gameplay scale:** 1.25 uniform (1 m = 49.21 Hammer units), chosen after walking the scale test.
- **Site origin:** E 666265, N 5103785, Z 370 m (EPSG:25832). Hammer +X = east, +Y = north.
- Each building has its own plan frame: x east, y north from its south-west corner, z up from its lowest floor.

| Building | Origin (E, N, Z) | Size (m) | Levels (absolute m) |
| --- | --- | --- | --- |
| Povo 1 | 666227.3, 5103698.65, 373.4 | 47.5 x 81.4 | -1 373.4, 0 377.85, +1 382.3, roof 386.75 |
| Povo 2 main | 666226.9, 5103810.85, 368.5 | 49.7 x 101.5 | -2 368.5, -1 373.25, 0 378.0, 1 382.3, roof 387.3 |
| Povo 2 strip | 666276.3, 5103820.1, 368.5 | 28.3 x 82.9 | -2, -1; roof = plaza at 378.0 (floor 0) |
| Mensa | 666285.3, 5103689.5, 373.4 | 16.0 x 33.2 | -1 373.4, 0 377.9, roof 382.5 |
| Library | 666287.5, 5103732.6, 373.4 | 13.9 x 54.5 | -1 373.4, 0 377.9, roof 382.5 |
| Bridge | Povo 2 frame, x 40.1-43.6, y -30.8-0 | 3.5 x 30.8 | deck 382.3 |

- **Povo 1 stairs:** a square spiral, four flights of 6 risers per storey, round an open well. On -1 and 0 the floor corner has two doors; floor +1 has one.
- **Povo 2 stairs:** two flights from 0 to 1, three flights per storey below.

---

## 5. Pipeline and tools (`tools/`)

| Tool | Role |
| --- | --- |
| `fetch_site.py`, `site_master.py` | Download and derive the site data (section 3) |
| `rectify_plan.py` | Warp a plan photo onto a building's real outline (4 control points) |
| `materials.py` | Custom textures and materials (red stair floor, red paving, terrazzo, beige stone, cream tile, frosted glass, anthracite, aluminium) |
| `building.py` | Shared engine: room table to walls, door gaps and frames, per-room floor slabs, facades (curtain / stone bays / ribbon / solid), stair cores (U or spiral), lifts, lights |
| `povo1.py`, `povo2.py`, `east_block.py` | One spec per building: rooms per floor, cores, facade styles, doors, extras (courtyard stair, glass boxes, bridge, glass roof, entrance stair, Hole 2 stair) |
| `build_site.py` | Whole map: terrain, OSM blocks, trees, spawns, sky, fog, then every detailed building |
| `vmap_mesh.py`, `kv2.py`, `vmap_build.py` | Write native Hammer meshes and entities; convert, deploy and compile |
| `test_build.py` | One test cycle (see below) |
| `contact_sheet.py` | Screenshots side by side in one labelled image |
| `cs2_launch.py`, `cs2_shots.py` | Start CS2 and load a map; take named screenshots |

Data and outputs live on `D:\CS2_Povo` behind junctions (`data`, `out`, `build`); the C: footprint is ~12 MB.

**Hand-made inputs** (versioned):
- `views/*.json`: the camera positions for the test screenshots.
- `data/plans/corners/*.json`: the control points that fit each plan photo onto its building.
- `cs2/cfg/povo_marks.cfg`: the F6 marker; the launcher installs it into the addon.
- `docs/`: before/after sheets of the lighting and of the first 11 fixes.

**Generated, not versioned:** `build/` (map sources, logs, run status) and `out/` (screenshots, grids). Every build rewrites them.

**On GitHub** (branch `shaders-mod`, folder `remake/`):
- **Included:** the code, specs, config, views and docs; the derived site data; the rectified plans and their control points; the orthophoto crop; the OSM extract; `labeled_pictures`.
- **Left out:**
  - the raw LiDAR tiles (`python tools/fetch_site.py` downloads them again);
  - `build/` and `out/` (generated).
- **Setup on another machine:** set `cs2_root` in `config/project.json`.

### Build and test

```bash
python tools/test_build.py views/povo1_views.json              # unlit: build + load + screenshots
python tools/test_build.py --bake --quality 1 views/povo1_views.json # lit, ~15 min (needs TdrDelay, closes CS2)
python tools/build_site.py --no-compile                       # write the map only
```

- **Two maps from one generator:** unlit builds write `maps/povo_site` (layout work, seconds); `--bake` builds write `maps/povo_site_lit` (baked lighting, to see it properly). A lit build never overwrites the quick map, and both can stay installed.

- **Unlit builds** compile in seconds. A full cycle with 24 screenshots takes about 3-4 minutes, and the build reuses a running CS2.
- **Failures** stop the cycle with a reason. The result is written to `build/maps/last_run.json`.
- **Screenshots** land in `out/shots/`, with grids in `out/*_grid.jpg`.

### Ground (build_site.py)

- **Terrain:** LiDAR every 2 m, written as open sheets (`closed=False`).
- **Cut at the walls:** it is cut exactly at the detailed buildings' walls, so there is no ditch round them.
- **Flat terraces** at the ground floor's level, ending in straight concrete retaining walls (`ZONES`):
  - round Povo 1 (6 m);
  - the -1 lane and the passage;
  - the floors of Holes 1 and 3.
- **Surfaces:** areas with exact edges, top first:
  - red paving (the passage and its opening to the street);
  - asphalt (roads, parking);
  - the dark grey Via Sommarive sidewalk (2.5 m), then the grass strip (3 m);
  - footpaths;
  - lawns traced from the orthophoto.
- **Everything else:** light grey concrete on the campus, slabs in town.
- **One arrangement per tile:** each terrain tile is one snap-rounded arrangement (grid, diagonals, cuts, area edges), so pieces always share edges.
- **Trees:** near the buildings, only OSM trees, as small young trees.

### How a building is described

Each floor is a list of rooms. A room has:
- a name and a kind (classroom, office, wc, lab, hall, study, terrace…);
- a rectangle in the building frame;
- doors, as side, position and width;
- optionally, glazed or open sides.

The engine merges room edges into walls, cuts the doors, and gives every room its own floor finish by kind.
Facades are chosen per side and floor; door openings in facades are listed per facade.
Changing a room is a one-line edit.
A facade can also be split into segments, each with its own style. Povo 1 uses this for its fine stone fins over the stair cores and the wide glazed bays between them on every side, plus the east -1 portico.

---

## 6. Materials

| Surface | Material |
| --- | --- |
| Povo 1 and Povo 2 stone | custom `beige_stone` (cream slabs with joints) |
| Corridors (Povo 1) | custom `terrazzo` |
| Floors (Povo 2) | custom `cream_tile` (40 cm) |
| Povo 1 stairs | custom `red_floor`; railings `aluminium` |
| Povo 2 stairs | grey concrete |
| Classrooms | stock light oak boards |
| Walls | stock smooth white plaster |
| Ceilings | stock 60 cm ceiling tiles |
| Window frames, mullions | custom `aluminium`; door frames `anthracite` |
| Courtyard white panels, mensa/library | stock white metal panels |
| Glass | stock clear glass; Povo 2 boxes custom `frosted_glass` |
| Outdoor | red paving (entrance, -1 lane), concrete slabs (courtyards, plaza, terraces), grating (steel stairs) |

---

## 7. Editing the map yourself in Hammer

**Open it.**
1. In Steam, Library, right-click Counter-Strike 2, then Launch CS2 Workshop Tools.
2. Pick the addon `povo_remake`.
3. In the Asset Browser, open `maps/povo_site.vmap`.

Everything I generate is ordinary Hammer meshes and entities. You can select, move, retexture and add props, lights, brushes and entities.
CS2 Hammer has no heightmap sculpting tool; terrain is edited by moving mesh vertices or with mesh tools.

**Keeping your edits.** Every build rewrites `povo_site.vmap`, so edits made directly in it are lost.
The plan, to set up before you start editing:
- The generator writes its output to a separate file, e.g. `maps/prefabs/povo_generated.vmap`.
- You work in a master map, e.g. `maps/povo_site_master.vmap`. It contains the generated file as a prefab, plus everything you add.
- We compile the master. Rebuilds only replace the prefab; your edits stay.

How CS2 stores prefab references is not verified yet. I will set it up and test it with you once, in Hammer, before you start.
Changes to generated parts (e.g. moving a generated wall) are better sent to me as a change (section 8), so they are not overwritten. Hand edits are for things the generator doesn't do: props, decals, details, special cases.

---

## 8. How to send changes

**Order:** building by building, floor by floor, with Povo 1 floor numbering -1/0/+1 and Povo 2 -2/-1/0/1 (section 4).

**What works best:**
- an annotated plan (the official plans or the rectified ones in `data/plans/`): arrows for doors, crosses for walls to remove, lines for walls to add, labels for room names;
- a photo with a note of where it was taken and which way it faces, for looks and materials;
- any measurement, even rough (counted tiles or steps, paces, "door about 1.6 m wide");
- for facades: a photo of the side and the floor it applies to.

**Where:** `data/labeled_pictures/` (on D:), one folder per building plus `EXTERNAL` and `PROBLEMS_TO_SOLVE`; its README has the conventions.
- **Labelled maps:** `tools/label_maps.py` writes them per building and floor into `<BUILDING>/MAPS/`, with `rooms.md`, and writes `build/maps/room_index.json` to map IDs back to the specs. Rerun it after each round of changes.
- **In-game marks:** `play.cmd [lit|unlit]` starts CS2 with F6 bound to "getpos; screenshot" (addon `cfg/povo_marks.cfg`). `tools/marks.py [--views]` collects the marks into `PROBLEMS_TO_SOLVE/marks/` and can write views to re-shoot them; the launcher collects them before each start.

**What I do with each change:**
1. Update the room table or facade rules for that building and floor.
2. Before building, draw the result back over the plan for you to confirm.
3. Build and screenshot the spot in game.

Unclear points come back to you as questions, not guesses.

---

## 9. Open points and known approximations

- **Room detail:** Povo 2 -2, +1 and the strip interiors are approximate. They come from the -2 plan photo, the directory sketch and the general plan, not a measured layout.
- **East block:** the mensa and library interiors are simplified from their evacuation plans. The plan photos' orientation is assumed (stairs at the north end).
- **Openings:** doorways are open, and room door positions are typical where plans don't show them.
- **Glass:** facade glass is grouped per facade and floor. It will be split per pane when breakable glass is done.
- **Lighting in unlit builds:** interiors look bluish with dark ceilings; that is the engine's preview mode, not the materials.
- **Scale of furniture and props:** not yet placed.
- **Lit builds:** working since TdrDelay (section 1). Use `--quality 1`: quality 0 bakes 16 samples and leaves colour blotches on the facades. Interior lights cast shadows: without that, baked light leaked through walls and floors and burnt corridors white.
