# Development worklog

This is the durable record of material project actions. Git history remains the
authoritative record of file-level changes; this log records decisions, local
tool results, limitations, and work that affects the installed CS2 addon.

## 22 October 2026 — Windows continuation and first compiled Povo addon

### Repository and baseline

- Located the private GitHub repository `AlbertoLupatin/trento_fps` and cloned
  `main` to `C:\Users\Alberto\Desktop\trento_fps`.
- Confirmed the clone was initially clean at commit `75d1886` with only `main`.
- Reviewed the design, data-source, terrain, blockout, CS2 workflow, and Windows
  handoff documents; inspected the generated preview and project configuration.
- Ran the original 17 unit tests successfully.
- Invoking `python` caused the Windows Python install manager to update and
  install Python 3.15.1. No additional Python packages were installed.

### Installed toolchain findings

- Found CS2 in the default Steam library with Workshop Tools depot `2347779`
  (optional DLC app `2279721`) installed.
- Recorded installed CS2 build `26087496` from `appmanifest_730.acf`.
- Confirmed `resourcecompiler.exe`, `dmxconvert.exe`, stock addon templates, and
  the Wingman map template are present.
- The compiler identified the graphics adapter as Intel Arc 130T GPU (16 GB
  reported shared/dedicated budget), driver `32.0.101.8626`, and successfully
  used Vulkan GPU ray tracing for lighting.
- Steam currently presents its sign-in window. Authentication was not automated,
  so Hammer inspection and an in-game launch remain pending.

### Cross-platform project workflow

- Added `tools/cs2_project.py` with the following commands:
  - `doctor`: validates repository sources and reports optional geographic tools.
  - `deploy`: additively copies repository-owned addon source and generated
    blockout assets into an installed CS2 Workshop Tools tree.
  - `place-blockout`: uses Valve's DMX converter to insert the geographic model
    into the binary Wingman VMAP deterministically.
  - `compile`: builds the ModelDoc model and/or map through Valve's resource
    compiler.
  - `sync-from-cs2`: copies Hammer/ModelDoc-edited source back into the repository.
- Added four initial deployment/discovery tests and one VMAP-insertion test.
  The full suite now contains 22 passing tests.
- Added GitHub Actions coverage for Windows, Ubuntu, and macOS. Valve compilation
  remains Windows-only, while geographic generation, validation, and deployment
  logic remain ordinary Python with no third-party dependencies.
- The first GitHub Actions run passed on all three operating systems. The workflow
  was then moved to the current major versions of the official checkout and
  Python setup actions after GitHub reported Node.js 20 deprecation annotations.

### CS2 addon source and compilation

- Selected Wingman as the provisional first-playable mode because it matches the
  compact campus/small-team brief. This is a blockout assumption, not a balance
  conclusion.
- Seeded `cs2/content/trento_povo/maps/trento_povo.vmap` from the Wingman template
  shipped with build `26087496`. Original template SHA-256:
  `9cff6309a167baaf93343a76d2239bc197caf6f70d25d4f982b045dffeb41695`.
- Added a ModelDoc source that imports the metre-based Povo OBJ at
  `39.37007874` Source/Hammer units per metre and uses the same mesh for initial
  collision. Added provisional terrain, building, and calibration materials.
- Deployed an installed addon at `content/csgo_addons/trento_povo` and
  `game/csgo_addons/trento_povo` without deleting unrelated files.
- Compiled the Povo model successfully. The compiler emitted one non-fatal
  duplicate-bone warning because each OBJ object uses the same object/bone base
  name; the resulting static model and materials were produced.
- Inserted the model as a solid `prop_static` at map origin and rebuilt the map.
  Compiler evidence confirms the geographic content was included:
  - 30,000 terrain triangles using `terrain_reference.vmat`.
  - 156 building triangles using `building_blockout.vmat`.
  - 36 calibration-cube indices using `calibration.vmat`.
- Produced the installed local VPK
  `game/csgo_addons/trento_povo/maps/trento_povo.vpk`:
  - Size: 2,765,079 bytes.
  - SHA-256: `7de8d9a9f59e8045854ee0294150977202759355c144ef528fc611eb2c3f9afa`.
  - Result: 26 resources compiled, zero failures, in approximately 50 seconds.

### Known issues from this build

- The local VPK is unsigned, which is expected without Valve signing keys.
- The stock template references one unavailable sky material and the compiler
  also reports a missing optional detail-prop data resource.
- No lightmap-resolution volume encloses the campus; the terrain consumed about
  65% of a 4096×4096 lightmap in this test build.
- Roughly 30,000 terrain triangles lie outside the stock template's visibility
  region. The playable boundary and visibility setup must be rebuilt around Povo.
- Navigation generation was skipped because the current map has no walkable nav
  seed. Spawns and the bomb target still belong to the stock Wingman template and
  have not been relocated onto verified campus routes.
- Collision compiled, but scale, orientation, walkability, spawn safety, and match
  completion have not yet been verified in CS2.

### Next verified milestone

After Steam sign-in, open `trento_povo` in Hammer, confirm the calibration cube is
39.3701 units per side, frame the campus, and replace the stock template floor,
spawns, bombsite, nav seed, visibility bounds, and lightmap-resolution volume with
a compact route network fitted to the Povo terrain. Then compile and complete a
local bot round before the two-client multiplayer gate.

## 22 October 2026 — first Hammer inspection and axis correction

- Confirmed the Steam client was signed in as the user's existing account and
  launched the already-installed Counter-Strike 2 Workshop Tools. No software was
  installed and no authentication was automated.
- Selected the `trento_povo` addon and opened `maps/trento_povo.vmap` in Hammer.
- Selected the `povo_geographic_blockout` `prop_static` through Hammer's Outliner.
  At its original `0 0 0` angles, Hammer reported bounds of approximately
  1,643 × 8,652 × 12,589 units: the geographic north extent was vertical, so the
  campus stood on edge.
- Set the placed prop to pitch `-90` degrees. Hammer then reported approximately
  12,589 × 8,652 × 1,643 units, equivalent to the intended 320 × 220 × 42 m
  geographic extent after the 39.37007874 units-per-metre conversion. The aerial
  terrain rendered face-up and the campus footprint became horizontal in both
  perspective and top views.
- Framed the corrected model in all views and visually confirmed that the stock
  Wingman template occupies only a small central portion of the full campus. This
  reinforces the existing requirement to rebuild the gameplay boundary, spawns,
  objective, visibility, lighting, and navigation around a deliberately selected
  campus route rather than treating the whole reference mesh as playable space.
- Saved in Hammer and synchronized the installed VMAP back to the repository.
  Decoding the saved binary with Valve's `dmxconvert.exe` confirmed origin
  `0 0 0`, angles `-90 0 0`, and scale `1 1 1` for the Povo prop.
- Updated the deterministic VMAP insertion helper and its unit test so a newly
  seeded map receives the verified `-90 0 0` axis correction automatically.
- Redeployed and rebuilt the corrected map successfully: 26 resources compiled,
  zero failures, in 2 minutes 32 seconds. The output VPK is 14,577,648 bytes with
  SHA-256 `2e43aae92fcfbe3d56a4f0d7eba14c8a5f6db8851c1b7e4339471b791276ce08`.
  The build again included 30,000 terrain triangles, 156 building triangles, and
  the calibration cube; the known missing sky/detail resource, lightmap-volume,
  visibility-boundary, and nav-seed warnings remain.
- Launched the compiled VPK through Hammer's `Run (Skip Build)` path. The map
  reached team selection, accepted a Counter-Terrorist join, spawned the player
  with the normal HUD and weapon, and accepted weapon input without crashing.
  The spawn view was dark and heavily obstructed because the stock Wingman floor,
  buildings, spawn, and the geographic model still intersect at the shared map
  origin. This validates the launch path but does not yet validate walking on the
  geographic terrain. The local playtest and Hammer build dialog were then closed.

### Remaining validation

- The full model bounds and upward terrain are verified, but the isolated 1 m
  calibration cube still needs a direct 39.3701-unit measurement in Hammer.
- Choose the compact campus routes, remove or relocate the overlapping stock
  Wingman floor and entities, then move the spawns onto verified Povo surfaces and
  confirm collision and movement on the geographic terrain.

## 22 October 2026 — campus spawn correction and live traversal check

### Diagnosis and deterministic layout

- Confirmed that all six Counter-Terrorist starts, all six Terrorist starts, the
  bomb target, and the buy zones still occupied the stock Wingman layout around
  the map origin. The geographic model also occupies that origin, which explains
  the dark, obstructed first spawn rather than a model-orientation regression.
- Selected a provisional north/south route along the open east side of the Povo
  terrain. Its local eastings are 70–74 m, beyond the current rough building
  volumes, while its terrain heights come from vertices in the exported mesh.
- Added the layout to `tools/cs2_project.py`: twelve starts now have sampled
  origins and inward-facing angles, and the bomb target and three template buy
  zones move with them. `place-blockout` applies the model insertion and entity
  placement in one deterministic VMAP round trip.
- Added an idempotence/unit test for the entity placement. A second preparation
  run made no changes, and the full suite passed all 23 tests.

### Build and live evidence

- The first rebuild could not replace `trento_povo.vpk` because the previous CS2
  tools process still held it open. After preserving the source and closing that
  process, the same build completed normally: 26 resources compiled, zero
  failures, in 53 seconds.
- Rebuilt installed VPK:
  - Size: 14,577,771 bytes.
  - Compiler MD5: `4780097beaccb6246e483ff156414a74`.
  - SHA-256: `e05ab774da45c59ff5e207ee399cdcacfdba26bd051d6781356308b9fe5a31f2`.
- Confirmed the required local launch form in the tested build:
  `-addon trento_povo -tools -asset maps/trento_povo.vmap` followed by
  `map maps/trento_povo.vpk`. The shorter `map trento_povo` form fell back to an
  empty map. The successful run reported `Spawn Server: trento_povo`, loaded the
  main and Wingman prefab spawn groups, and created client/server physics.
- A live Terrorist join landed at
  `-3927.165 2765.748 431.546`, directly below the configured first-playable
  start at `-3927.165 2765.748 462.315`. A live Counter-Terrorist join landed at
  `3789.370 2844.488 397.762`, directly below its configured start at
  `3789.370 2844.488 428.850`. The roughly 31-unit offset is the intentional
  spawn clearance above the sampled ground.
- From the Counter-Terrorist position, two seconds of forward movement changed
  the live player position to `3311.298 2844.525 393.184`: approximately 478
  units of unobstructed horizontal travel with a 4.6-unit terrain-height change.
  This directly verifies that the player is no longer trapped in the original
  overlapping geometry and that collision supports movement on this corridor.
- Engine screenshot commands worked, but the background Workshop Tools renderer
  captured its loading artwork rather than the active hidden game view. Spawn and
  traversal verification therefore rests on the live client/server console
  positions above, not on that screenshot.

### Still open

- This is a reliable diagnostic route, not a final balanced layout. Remove or
  rebuild the remaining stock template geometry, define deliberate paths and
  boundaries, add a nav seed and navigation mesh, repair lighting/visibility,
  and complete a local bot round.
- The two-independent-client match gate, clean-install package check, and direct
  39.3701-unit calibration-cube measurement are still outstanding.

## 23 October 2026 — compact Wingman arena, navigation, and production rebuild

### Reproducible arena source

- Replaced the diagnostic corridor with an explicit 25 × 130 m Wingman envelope
  on the east forecourt: E666305–666330, N5103735–5103865.
- Extended `config/povo_blockout.json` and `tools/build_povo_blockout.py` with six
  terrain-fitted cover boxes and a 3.2 m high, 0.6 m thick segmented perimeter.
  Generated output now contains 30,624 visual triangles and 38 gameplay volumes.
- Added `povo_blockout_collision.obj`, cropped one metre outside the arena. It
  contains 1,309 vertices and 2,304 triangles and excludes the distant building
  modules. ModelDoc now uses it for physics while retaining the complete campus
  model for presentation. This reduced nav input from 30,178 to 2,314 triangles.
- Added distinct cover and boundary materials. The first map-only retry exposed
  that Valve reused the previous compiled model; `compile --target map` now
  compiles ModelDoc first so collision/material changes cannot silently go stale.

### Deterministic VMAP preparation

- Removed the remaining stock Wingman room and placeholder helper entities while
  preserving its proven mode entities and sky shell.
- Normalized the conditional template buy zones, moved all twelve starts and the
  bomb target into the compact arena, and moved the intro/end cameras with them.
- Added a deterministic nav seed, combined light-probe volume, outdoor
  soundscape, two minimap boundary points, a fitted lightmap-resolution volume,
  and a larger sky/visibility shell using the valid 65-degree sky resource.
- `place-blockout` successfully round-tripped the binary VMAP and two subsequent
  runs reported `unchanged`, establishing idempotence.
- Added generator/config validation, collision-export coverage, lightmap-volume
  insertion coverage, and model-before-map compilation coverage. The complete
  suite contains 26 passing tests.

### Compile and runtime evidence

- The final rebuild completed 25 map resources with zero failures in 57 seconds;
  the explicit ModelDoc prerequisite compiled separately in one second.
- Nav generation consumed 2,314 collision triangles, removed disconnected
  islands, produced 503 nav areas, and completed tactical metadata in roughly
  1.2 seconds after recast. The nav resource is 114,568 bytes.
- Lighting baked a 4096 × 4096 atlas and the probe atlas successfully. The new
  lightmap-resolution volume removed the earlier missing-volume warning.
- Packaged VPK:
  - Size: 9,312,611 bytes.
  - Compiler MD5: `bc240457e022f88a741e7dfc2cb4463b`.
  - SHA-256: `52e7292dd29db1cb17d918aa5d1d799dc6c3505f6b56a98645f808c01aea7b1f`.
- Launched through Workshop Tools with `-addon trento_povo -tools -asset
  maps/trento_povo.vmap` and `+map maps/trento_povo.vpk`. CS2 loaded spawngroup
  `trento_povo`, placed the human at the configured CT forecourt start
  (`2253.937 2568.898 328.200` after ground settlement), and reported three live
  bots. This proves package loading, spawn placement, and bot population against
  the generated nav mesh; it does not yet prove a completed round.

### Known warnings and next gates

- ModelDoc still reports duplicate imported OBJ bone names. The map compiler also
  reports the stock optional `scripts/detail_prop_types.vdata_c` as missing and
  emits the expected unsigned-VPK warning without Valve signing keys.
- The full 200 × 300 m reference terrain is intentionally outside much of the
  compact combat PVS and lightmap-density volume; it is aggregated as backdrop.
  Runtime visual/performance inspection must decide how much of that backdrop to
  retain or further simplify.
- The 1 m calibration cube is still present for direct Hammer measurement and
  must be removed from a release asset afterward.
- Resume with an active-window visual review, a complete bot round, CT/T buy
  checks, bomb plant/defuse and restart checks, radar artwork, frame-time capture,
  clean-install packaging, and a two-independent-client match. Detailed
  architecture/materials and representative balance sessions remain release
  work; this checkpoint is not the claimed finished map.

## 23 October 2026 — Linux continuation and schematic radar source

### Recovered baseline

- Confirmed local `main` was clean at the start and matches GitHub's only branch
  at `26ee052e450b2c0d6258444bdd6cea23ff93a1ad`, the compact arena commit from
  Windows. No remote changes needed to be imported.
- Read the Windows build/runtime evidence and ran all 26 baseline tests.
  `doctor` finds the geographic/addon sources ready on Fedora; the Windows
  Workshop Tools are unavailable in this session.

### Radar source and build workflow

- Added `tools/build_povo_radar.py`, using only the Python standard library. It
  generates a transparent 1024-pixel schematic radar, two explicitly named VTEX
  sources, overview coordinates/markers, an annotated SVG review, source/output
  hashes, and credits under `exports/povo_radar/`.
- Reused the geographic generator's perimeter segments and configured cover
  footprints. Starts/objective come from the existing verified placement code.
  The transform preserves world X=north and world Y=east, so geographic north
  points right and east points up. A 7 m margin yields a 144 m square and
  5.536417323 Hammer units per pixel without stretching the narrow arena.
- The runtime image includes an A at the objective origin. The separate review
  adds twelve start dots, cover heights, compass labels, and a 10 m scale bar;
  its PNG was rendered with ImageMagick and visually inspected. The schematic
  does not infer nav connectivity, buy-zone bounds, or plantable trigger extents.
- Extended additive deployment to install the image/VTEX sources in addon content
  and the generated overview in addon game resources. `doctor` now checks all
  deployment inputs, including the cropped collision and radar files.
- Added `compile --target radar`. The full `--target all` sequence builds model,
  map, then radar textures and restores the generated overview last, because map
  compilation can regenerate its own radar assets. Input preflight happens before
  launching the first compiler. `--target map` retains its previous behavior.
- Documented generation, compile order, coordinate alignment, and Windows checks
  in `docs/POVO_RADAR.md` and linked it from the main workflows.

### Verification and remaining gates

- All 34 unit tests pass on Python 3.14.8: the 26 baseline tests plus eight tests
  covering radar coordinate handedness/known CT coordinates, square scaling,
  perimeter coverage, PNG CRC/dimensions/transparency/cover colors, deterministic
  exports, failed-input preservation, deployment, and compiler ordering/failure.
- Deployed the real repository source into a temporary simulated CS2 tree:
  18 file hashes verified, dry-run wrote nothing, and a second deployment reported
  every file unchanged. All seven generator-owned radar files match a clean
  rebuild byte for byte. `git diff --check` passed.
- No Valve compiler or game runtime was executed. The VTEX schema and generated
  lookup names need confirmation in the installed CS2 build. Compiling loose
  textures after a map **does not insert them into its existing VPK**; final
  packaged inclusion and a clean-install radar check remain required.
- The completed bot round, buy/plant/defuse, restart, performance, direct cube
  measurement, and two-independent-client match gates remain open. This change
  supplies reviewable radar source, not a newly verified playable Windows build.

## 23 October 2026 — photographic references and user identification

- Collected 15 architectural reference JPEGs in `data/reference/povo_photos/`,
  with source credits, licence records, original image hashes, and a contact
  sheet. Sources comprise two Wikimedia photographs and thirteen image extracts
  from the university's 2023 campus publication. These are research references;
  they have not been incorporated into game textures or new map geometry.
- The user reviewed the set and corrected six filenames: P001, P002, P003, P004,
  P006, and P010. Synchronized the manifest, credit links, location worksheet,
  and contact sheet with the actual filenames. All 15 JPEG hashes still match.
- P001/P002 are confirmed as Povo 1 and P010 as Povo 2. P003 faces the internal
  building; P004/P006 depict winter conditions. These notes do not establish
  cardinal viewing directions, floor levels, dimensions, or a game-map season.
- LiDAR capture is deferred until the user can try it. The photographic set now
  includes stairwell, library, corridor, and connecting-bridge references, but
  does not establish a complete measured internal floor plan.

## 23 October 2026 — first exterior detail pass and Povo 1 plan registration

- Added optional architectural configuration and `tools/povo_architecture.py`.
  Eight facade sections now use photo-guided glazing grids or stone/window
  patterns. The bridge placeholder is replaced visually by a deck, roof, posts
  and louvers. The export contains 926 architectural components and 41,724 total
  visual triangles. Bay counts, floor/window dimensions and facade assignment are
  estimates recorded per section, not measurements inferred as fact.
- Added four opaque material sources and their ModelDoc remaps; all nine OBJ
  materials resolve to repository-owned material sources. Glazing is a teal
  placeholder, without transparency or breakage. New details remain outside the
  gameplay collision export; its bytes match the previous Windows baseline and
  still describe 2,304 triangles. No new interior routes are deployed.
- The bridge roof retains the earlier 385.69 m DBM estimate. Its 382.49 m deck is
  estimated 3.2 m below the roof, rather than treating the old roof-height slab
  as an accessible floor. The bridge is still scenery pending measured landing
  and floor relationships.
- Added photograph hash verification and reference/assumption records to the
  geographic export. Regenerated the visual OBJ, material library, provenance,
  credits and radar metadata. Updated the full-campus preview and added an
  architectural close-up renderer with a depth buffer for thin facade layers.
  The resulting source-mesh preview was visually inspected.
- Registered the user's P016/P017 plan images without moving or changing their
  original files. Downloaded the two PDFs, two floor-plan PNGs and README from
  `agusmeroli/mappe-povo`; retained URL/hash provenance and the inspected tree SHA.
  The repository describes these as unofficial maps; no licence file was listed.
  Downloaded plans remain reference material outside the deployment pipeline.
- Inspected/rendered the staircase PDF and both room plans. Their north-right,
  east-down orientation is recorded in `config/povo1_plan_alignment.json`.
  Provisional alignment to the existing 47 x 83 m core identifies four stair
  regions and an entrance near E666274/N5103726, matching the northing range of
  the existing east connector. This fit uses the approximate footprint and does
  not independently establish surveyed dimensions.
- Preserved distinct numbering conventions: A1xx/A2xx academic ground/first,
  lift labels -1/0 in the room plans, stair labels 0/1, and user filenames
  floor1/floor2. Absolute floor elevations and riser/tread sizes remain unknown.
  Annotated reviews are in `exports/povo_plan_review/`; workflow and limitations
  are documented in `docs/POVO_ARCHITECTURE.md`.
- All 39 unit tests pass, including five new geometry/provenance checks. A real
  source deployment into a temporary tree verified 22 file hashes and reported
  every file unchanged on a second deployment. All 17 image hashes match their
  registered originals; `doctor` and `git diff --check` pass.
- No Windows compilation, in-game material inspection, performance test, or new
  multiplayer evidence was produced. An entrance/corridor scan, one known
  dimension, and a bridge landing/floor identification are the next useful field
  evidence; they do not block further exterior modelling.

