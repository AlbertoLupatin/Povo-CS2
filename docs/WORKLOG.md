# Development worklog

This is the durable record of material project actions. Git history remains the
authoritative record of file-level changes; this log records decisions, local
tool results, limitations, and work that affects the installed CS2 addon.

## 23 October 2026 — Windows resume documentation and approved full-data push

- The reconstruction checkpoint is `34ac930`, with the 66-photo archive,
  camera/GPS metadata, confirmed walk, bridge binding and A215 refinement.
  Its initial push was blocked by automatic approval review pending explicit
  authorization for the photo/location payload. The user then explicitly
  instructed: "Push everything, I'll continue from the Windows side" after the
  request identifying all full-resolution photos and GPS/camera metadata.
- Added `docs/WINDOWS_RESUME.md` as the current detailed operational handoff.
  It covers preserving Git/installed-addon edits, pulling all source photos,
  known compiled baseline versus source-only changes, exact photo/floor/core
  facts, unresolved metric heights, source ownership, standard-library checks,
  optional previews, deterministic placement, real deployment/compile commands,
  a staged interior integration plan, package/radar/gameplay gates and source
  sync. It does not claim the offline interior is already deployed or walkable.
- Replaced stale Windows handoff text that still described the toolchain and
  VMAP/compiler workflow as unverified. Linked the resume guide prominently
  from README and the general CS2 workflow. Historical build evidence remains
  in earlier log entries rather than being overwritten as current results.
- Documentation commands were checked against the current parser/deployment/
  sync implementation. No new application code or geometry changed in this
  documentation pass; the prior 73 passing tests remain the source baseline.

## 23 October 2026 — Confirmed 66-photo walk, bridge floors and identified A215

- Imported all 66 user-supplied WeTransfer JPEGs, 307.9 MB total, byte-for-byte
  into `data/reference/povo_photos/walk_2026-10-23/originals/`. Preserved exported
  filenames; catalogue IDs P025–P090 map photo 66 through photo 01. All 90 photo
  and plan hashes pass. These JPEGs are not claimed to be original HEIC files.
- Saved native camera/EXIF/Apple/GPS metadata, excluding transient download
  filesystem fields. All 66 report iPhone 17 Pro, 5712 × 4284 source pixels,
  capture time, lens, GPS and magnetic heading; 26 main-lens and 40 ultrawide
  images. Accuracy fields remain attached. GPS/headings are clues, not an indoor
  survey. Prepared and inspected six chronological review sheets with stable
  source numbers and individual-photo links; route notes now reflect the user.
- Recorded the full narrated sequence in `config/povo_circulation.json`.
  The bridge connects Povo 2 floor 1 to Povo 1 floor 2. The user clarified this
  floor equivalence; no other cross-building height equality is inferred.
  Added the named-level binding to exterior bridge metadata without moving it.
- User confirmed that photos 39–38 use a different stairwell near A212/A213
  (southeast) than photos 51–47 near A209/A216 (northeast). Recorded separate
  1→ground and 2→1 connections. Povo 2 stair cores remain spatially unregistered.
  A215 is identified in 44–43; 42–41 remain A211 or A212. Photo 40/14 contextual
  inferences and overlapping entrance/outward wording for 16 remain explicit.
- Added `tools/povo_circulation.py` and a labelled connection diagram. It checks
  complete photo coverage, named-level connectivity, bridge floor identity,
  distinct red stair cores and source hashes. It propagates only the confirmed
  bridge equality. Povo 2 ground and −1 elevations remain null. Existing Povo 1
  prototype/scenery estimates imply unequal 3.6 / 4.89 m rises; the report flags
  this for calibration rather than claiming measured heights or hiding it.
- Corrected current floor labels: A2xx is Povo 1 floor 1; earlier P016/P017
  floor-number filenames remain historical source names. The interior study
  still contains Povo 1 ground/floor 1 only; bridge floor 2, Povo 2 interiors,
  physical flights and vertical traversal are not built in that OBJ.
- Added an A215 fit-out in its smaller registered courtyard-side footprint,
  with three estimated rows / 27 seats and an actual courtyard-wall window cut.
  Improved the shared desk kit with dark modesty panels, shared pedestals, floor
  feet and seat beams from the high-resolution images. Panel perforation is an
  original generated texture. A215's opposite glazing/external metal stair view
  is recorded as background evidence; the detailed external stair is unbuilt.
- The clearance check caught a tight rear passage in the small A215 template.
  Adjusted estimated first-row position, pitch and chair depth while retaining
  three rows and side access. All 16 ground and 33 floor-1 stations now pass.
  The study is 1,080 boxes / 12,960 triangles; fewer repeated legs offset the
  additional furnished room. Game crouch/ballistic/engine behaviour is untested.
- All 73 unit tests pass. Added regression coverage for A215 courtyard openings,
  rows/panels, bridge identity/elevation propagation, unknown Povo 2 heights,
  photo coverage, ambiguous room identity, distinct stair cores and stale photos.
  Regenerated and visually inspected A215 and existing classroom previews,
  the floor review, clearance heatmaps and the connection diagram. Exterior
  visual OBJ and arena collision remain byte-identical; Windows work is pending.

## 23 October 2026 — User-corrected classroom layout and P022-style second room

- Applied the user's A224 correction: continuous rows spanning the room with
  1 m clear at both finished side-wall faces. Removed the old split row layout.
  Rotated the teaching/seating arrangement so west windows are behind students,
  opposite the east blackboard. Kept seat heights, row pitch, counts and fixture
  dimensions explicitly estimated. Each current room has five rows / 45 seats.
- Reused the kit in A223 as the additional P022-style room requested by the user.
  The user does not know P022's room; A223 is a design assignment, not a photo
  identification. Recorded that distinction in configuration and photo metadata.
  Refined A223's approximate source-plan door toward the north end and rejected
  a front-wall teaching board that overlaps a doorway.
- Generalized the kit to cardinal teaching directions with opposite rear glazing
  and multiple registered targets. Added regression checks for continuous tops,
  exact 1 m side gaps, rear windows/front board, chair direction, inconsistent
  orientation, blocked front doors and duplicate targets. All 68 tests pass.
- The clearance audit now checks both side aisles in furnished rooms instead of
  centres occupied by the continuous rows. All 16 ground and 32 upper stations
  pass. Actual crouched cover, shooting/penetration and CS2 collision remain
  Windows validation work; this is an offline source model only.
- Added a dimensional top view and refreshed actual-mesh cutaways for both
  A224 and A223. Regenerated the whole-interior preview, room plan, audit maps
  and source provenance. The interior is 1,338 boxes / 16,056 triangles.
- Reinspected P007, the existing red stair photo. It establishes red steps and
  landings, dark nosing, horizontal metal rails and white walls/columns. No new
  photograph is required for appearance. The stair core identity, full step
  count between A1xx/A2xx and landing heights remain unknown. Asked for a nearby
  room number and rough step count, and documented the four core/room pairings.
  Stair flights and their vertical game route are not yet built.

## 23 October 2026 — New photos and first furnished A224 pilot

- Inspected and registered seven user-supplied photos, P018–P024. Preserved their
  original bytes/names, recorded hashes, descriptions and source uncertainty,
  and refreshed the reference contact sheet. Reconciled the user's relocation
  of P017 into `images/` as a byte-identical move. All 24 catalogue hashes pass.
- P020 (A224) establishes tall framed glazing, a transom, dark desk tops, wooden
  seating, a light wood-look floor, perforated suspended ceiling, recessed light
  grids and ventilation cassettes. P021 (A208) adds a projector/board reference;
  P022 shows a teaching board and projection screen but lacks a room number.
  P019 supplies a westward exterior view. Outdoor P018/P023/P024 are reference
  for later alignment; “courtyard” filenames are not assumed to locate the
  central plan courtyard. No game season was selected from seasonal photos.
- Added `tools/povo_room_fitout.py` and integrated a parameterized A224 pilot in
  the existing interior mesh. It includes 24 estimated seats/desks, a teaching
  desk, board/screen, ceiling panels, grid lights, vents, projector and window
  framing. A real opening is subtracted from the west wall, preserving the sill
  and head. OBJ/MTL glass has an opacity hint; there are no CS2 glass materials,
  break interactions, game lights, people or copied photo pixels in this model.
- Furniture count/placement, bay count, material colours, all fixture dimensions
  and teaching-wall orientation remain estimates. The room's door fraction was
  refined approximately toward its north end from the source plan. A central
  aisle and transverse passage are reserved. Only A224 is furnished so far;
  other ordinary rooms can reuse an adjusted kit after validation. Computer
  rooms and the auditorium still need their own arrangements.
- Added original generated wood-look/perforation textures with metric UVs.
  Fixed wall material propagation so a collinear courtyard wall does not tint
  unrelated classroom spans. The study is now 563 boxes / 6,756 triangles.
  Recorded the three used photo hashes and catalogue hash; the builder/audit
  reject stale photos. Refreshed exterior provenance for the catalogue update;
  the exterior OBJ and arena collision remain byte-identical.
- Added and visually inspected `classroom_A224.png`, rendered from the actual
  exported mesh with clearly labelled cutaway and ceiling views. Regenerated
  the whole-interior preview, room plan and clearance heatmaps. The clearance
  audit includes furniture/fixtures and still reaches all 16 ground and 30 upper
  stations independently. It does not validate in-game traversal or stairs.
- All 66 unit tests pass, including new checks for opening volume, actual window
  cuts/furniture bounds, changed-photo rejection and invalid pilot locations.
  `git diff --check` passes. Windows integration/testing remains pending.
- Asked the user for P022's room number and the teaching-wall side in A224.
  Pending that optional answer, the south teaching side is explicitly provisional.
  The next useful photo shows A224's entrance and teaching wall together; stair
  views with both landings would help establish the floor connection.

## 23 October 2026 — Individual Povo 1 rooms and offline checks

- Clarified the interior/exterior split after the user found the circulation
  overview confusing. The outdoor addon still uses solid building masses; the
  separate interior study is preparation for replacing a chosen part of that
  massing and connecting entrances. It is not a deployed indoor game route.
- Traced approximate individual room rectangles from each registered plan:
  A101–A110 on the ground level, A201–A224 plus LAB upstairs. Each level now has
  its own courtyard/circulation/room layout. Source pixel footprints, room names,
  simplified door sides and approximate local dimensions/areas are retained in
  configuration/provenance. These are unofficial-plan estimates, not a survey.
- Built classroom walls and real door gaps/lintels. Merged shared collinear wall
  spans to avoid duplicate walls between adjoining rooms. Removed the cloned
  upper external entry because that position crosses A212 in the upper plan;
  access through stairs remains to be established. The study has 164 component
  boxes and 1,968 triangles. Rooms are unfurnished; a common photo-guided kit
  will be adapted to individual footprints rather than copying one room's shape.
- Replaced the ambiguous review with two clearly labelled north-up room plans,
  building outline, corridors, courtyard, stair reservations and entrance.
  Regenerated and visually inspected the plan, actual mesh preview and clearance
  heatmaps. Grey service/study areas still need subdivision; ceilings, window
  openings, stairs, props and gameplay interactions remain unfinished.
- Added an actual-exported-OBJ horizontal clearance audit with source/mesh hash
  checks. At the provisional 0.85 m width / 1.9 m height / 0.1 m grid, all ground
  stations (16) and upper stations (30) are reachable from their separate starts,
  including every named room centre. This does not validate real CS2 physics,
  vertical traversal, engine collision/nav or furnished rooms.
- Added a read-only VPK v1/v2 reader and final-radar package checker while Windows
  is unavailable. It checks required entries, overview fields and streamed CRCs;
  full entry CRC verification is optional. Synthetic tests cover malformed data,
  split/preload payloads, missing radar and overview mismatches. Three temporary
  upstream preload/single/split fixtures passed every payload CRC. A CS2 signature
  fixture parsed but its absent numbered chunk prevented payload verification.
  No current project VPK was available for this check; no signatures or full
  custom dependency closure are claimed. See `docs/CS2_PACKAGE_CHECK.md`.
- All 62 unit tests pass; `git diff --check` passes. The outdoor source,
  collision, VMAP, deployment list and Windows build remain unchanged.

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

## 23 October 2026 — GitHub checkpoint and independent interior study

- At the user's request, committed all exterior/radar work, reviewed photographs,
  original reference sources and plan alignments as `e2e9a5c` and pushed `main`
  to GitHub. The source README's original trailing whitespace is preserved using
  a narrowly scoped Git attribute rather than changing its recorded source bytes.
- Continued with a separate Povo 1 circulation study in
  `config/povo1_interior_study.json` and `tools/build_povo_interior.py`. It exports
  two floor levels, an open courtyard on both, four reserved upper stair openings,
  simplified corridor/lobby finishes and wall/door-gap geometry. It contains 100
  boxes and 1,200 triangles, using the same local-metre origin as the campus.
- Ground reference 374.0 m, upper offset +3.6 m, wall/door clearances, tile size,
  partition positions and stair landing margins are explicitly provisional.
  Both levels share a coarse circulation layout rather than claiming a complete
  reconstruction of their different room arrangements. No stair flights,
  ceilings, room inventory, gameplay entities, or vertical navigation are built.
- Added original generated tile PNGs and repeating metric OBJ UVs. The warm/pale
  grey finishes are placeholders for refinement from the user's upcoming photos.
  Added a north-up aspect-correct review and rendered the exported mesh and finish
  swatches with `tools/render_interior_preview.py`; visually inspected both.
- The interior study remains outside the deployment source list and does not
  alter the current campus mesh, arena collision, navigation, or package. Source
  plan hashes, per-level labels, assumptions, statistics and artifact hashes are
  recorded in its provenance. A failed regeneration preserves existing output.
- All 47 unit tests pass. Eight added checks cover subtraction of overlapping
  voids, coordinate orientation, actual courtyard/stair slab holes, entrance gap
  and lintel geometry, adjustable floor spacing, OBJ UV/material/hash consistency,
  invalid route/dimension rejection, and failed-generation preservation.
- Windows compilation and in-game validation remain pending. The next interior
  refinements depend on entrance/stair views and measured reference dimensions;
  those will replace estimates before gameplay integration.


## 23 October 2026 — Windows pull and updated exterior/radar build

- Fast-forwarded the clean Windows `main` from `26ee052` to GitHub `2acf729`
  (eight commits), including the full photo archive and reconstruction sources.
- Preserved both installed addon trees under the ignored local directory
  `build/windows-resume-backup-20261023-162008/`. All existing editable files in
  the sync list matched `26ee052`; the new facade materials were not installed.
  No unsynchronized edits in those files needed merging before deployment.
- All 73 tests pass on Windows 11 / Python 3.15.1. `doctor` reports ready sources
  and finds the installed compiler. Circulation validation verifies all 66 walk
  photos and the confirmed bridge floor relation. Its platform-specific report
  is saved locally as `build/windows-circulation-report.json`; the tracked Linux
  report was retained to avoid incidental path/checkout-line-ending hash churn.
- Deterministic VMAP preparation reported `unchanged`. Deployed the new source
  and ran `compile --target all` with CS2 Workshop Tools build `26144732`.
  Model compilation completed with the existing duplicate imported bone warning;
  the map compiled 29 resources with zero failures in 1 minute 46 seconds.
  The generated navigation still contains 503 areas. Both custom radar textures
  then compiled successfully as 1024 x 1024 BGRA8888 resources, with zero failures.
- Full compiler output is in the ignored `build/windows-resume-compile.log`.
  The new installed map VPK is 9,521,788 bytes, SHA256
  `12bdcc031525fdbbc4529fe2a5e64830a35ecc1a18f32ce2b98c5fbbf36c3e1d`.
- Ran `verify_cs2_package.py --full-crc`: all 31 existing entries pass CRC checks,
  but the overall radar check fails because both custom radar textures and the
  generated overview are missing from the package. They are present as loose
  addon files only. The report is `build/windows-package-check.json`.
- Next validation work is to include custom radar/overview in the distributable
  package, verify radar alignment and the updated facade materials in game, then
  complete gameplay/clean-install/independent-client gates. No game was launched
  during this continuation. Interior geometry is still an offline study and was
  not installed or made playable by this build.

## 23 October 2026 — portable map packaging and runtime load

- Added `tools/package_cs2.py` to package the existing successful Windows compile
  into a separate map VPK using the standalone VPKEdit 4.4.2 CLI. The packager
  preserves original map entries and adds the custom model, all nine materials,
  generated terrain/default textures, map config, radar and overview. Full photo
  archives and offline interiors remain excluded. Third-party tools/dependencies
  are local under ignored `build/tools/`; no global install was required.
- The first VPKEdit output passed per-entry CRCs, staged byte hashes and its own
  checksums, but CS2 rejected its Source 1 MD5 chunk table (`Chunk hash not found`,
  expected type 1). Compared the compiler's 1 MiB chunk layout and the upstream
  ValvePak BLAKE3 enum/verification implementation. Added the CS2 BLAKE3-128 table,
  rebuilt the three footer MD5 checksums and retained the unsigned descriptor.
  A recomputed BLAKE3 fraction matches the original Valve compiler's hash.
- A subsequent engine launch reached server/client physics, but logged a missing
  `trento_povo_radar_psd.vtex_c` lookup. The installed stock Dust II radar uses the
  same PSD suffix. Added normal/spectator PSD aliases from the compiled TGA bytes,
  and extended the package checker to require both lookup variants.
- Final artifact: `build/package/trento_povo.vpk`, 10,623,229 bytes, 51 entries,
  SHA256 `549edf5423049e52b05a2667e21df5683b40cf6752f5e894d2ad750fa8618187`.
  All entries match their staged SHA256s and pass CRC checks; the overview matches
  the generated source. Package/asset/packer provenance is recorded locally in
  `build/package/trento_povo.json`; the independent radar check is `radar-check.json`.
- Installed the packaged artifact in the existing addon, preserving the original
  compiler-only package as `build/package/compiler-trento_povo.vpk`. The final
  16:47 local launch logs `Spawn Server: trento_povo`, a loopback connection,
  server/client physics and `OnSwitchLoopModeFinished( game : success )`.
  No missing overhead-map texture or fatal chunk-hash error appears in this run.
  Log snapshot: `build/package/windows-load-test.log`. The tools/game process
  was left open for local inspection.
- All 79 tests pass on Windows. Six packaging tests cover unsigned CS2 trailers,
  missing assets/stale overview, corrupt input, preservation on packer failure or
  dropped entries, installed-package protection, and BLAKE3/checksum rebuilding.
  The optional BLAKE3 test is skipped when that packaging dependency is absent.
- This is a successful packaged-map load, not a visual/performance or gameplay
  acceptance result. Existing optional detail-resource, missing cubemap-array,
  and missing loading-screen/icon warnings remain. The next checks are visual
  radar alignment, traversal/objectives/a full round, clean installation without
  loose addon assets, and two independent clients. No new interior geometry or
  playable staircase route was added.

## 23 October 2026 — accepted outdoor playtest and campus reconstruction design

- Corrected the relocated buy volumes: the inherited CT box was narrow and the
  T box was small/off-centre. Trigger meshes now use centred local half-extents
  (256, 420, 180) Hammer units. The bomb trigger uses (196, 300, 140) to span
  uneven terrain. Preserved vertex topology and verified repeated preparation
  is unchanged. Tests cover all starts plus player clearance and skewed-box fitting.
- Rebuilt the map with zero resource failures, packaged the changes and launched
  an isolated addon containing only addon metadata and the VPK. A live Terrorist
  purchase was recorded; no custom Povo asset or radar lookup failures were seen.
  Diagnostics and normal-round reset commands are in `build/gameplay/`.
- After receiving the manual buy/movement/radar/plant/defuse/round checklist, the
  user reported “All good”. Record this as user acceptance of that outdoor
  playtest, not automated completion of each objective or a second-client test.
- Added `config/povo_campus_route.json` and `docs/POVO_CAMPUS_ROUTE.md`. The first
  reconstruction is the real Povo 1 entrance → southeast stair → A215/east hall,
  then the floor-1 corridor loop and A223/A224. Replace overlapping solid massing,
  reconcile glazing and add real materials/interior lighting before integration.
- The full campus route follows the narrated walk through the separate northeast
  stair, Povo 1 floor 2, bridge, Povo 2 floor 1 and its ground entrance, returning
  outside. Bridge equality and unknown Povo 2 heights/core locations are retained.
  The 374.0 / 377.6 / 382.49 m estimates are not a measured storey stack.
- Objectives/spawns for the campus layout remain undecided until the vertical
  route and two useful approaches work. The courtyard is a visual anchor; access
  through a new door/window is not implied. No new stair or interior geometry
  was created by this design checkpoint. All 81 source tests pass on Windows.

## 23 October 2026 — playable two-floor Povo 1 campus

- Implemented the accepted footprints in the separate `trento_povo_campus`
  map, preserving the user-tested outdoor `trento_povo` map. Ground A101/A102
  along the outer north wing are sealed per the user's clarification. Ground
  A103–A106 repeat the A103 room family; A107–A110 repeat the A101 family.
  All 25 existing upper room footprints are open: 33 playable rooms overall.
- Added classroom rows/boards/windows/wood floors/ceiling fixtures, courtyard
  glazing, real ceilings, interior lights, room labels, a bounded entrance
  landing and a 20-riser southeast switchback stair. Povo 2 and the bridge
  remain scenery; floor 2 and the larger campus route are not implemented.
- Added campus model/VMAP/radar generators, simplified collision, a per-floor
  clearance audit, packaging support for named maps and lower radar sections,
  and `play_campus.cmd` with a dedicated isolated test addon.
- Native import initially became excessively slow with per-face duplicated
  terrain vertices. Shared indexed attributes before faces and explicit normals
  reduced the final model compile to about 14 seconds. Physics uses 1,253 boxes
  and visual geometry has 8,210 boxes plus the campus backdrop.
- Live drops exposed an earlier documentation sign error: after the established
  model import/prop rotation, Source coordinates are (-north, east, up), scaled
  once by 39.37007874. Fixed all campus entities, lights and radar. The corrected
  compile retains 2,150 navigation areas, instead of pruning every area.
- Final model/map/four radar textures compile with zero resource failures;
  90 Python tests and the 18-ground/49-upper-station clearance audits pass.
  Package identity: 25,247,460 bytes, 107 entries; all CRCs and staged hashes pass.
  SHA256: 9000e3617b5ae6ffcd997827f65a4e229db35a22b4fbd3bd90da805518e2017e.
- The isolated addon loads the final VPK with one human and three bots. Normal
  walking ascended and descended both stair flights, turning at the landing,
  without jumping, crouching or noclip. Separate probes entered A103/A109 and
  were blocked by A101/A102. A T purchase via autobuy produced an AK47 with
  buy-anywhere disabled. Returned the game to cheats off, moving bots and
  normal round timing, and left it running for the user's playtest.
- Plant/defuse, CT purchasing, a complete round, bot travel between floors,
  reliable visual/performance review and independent-client testing remain
  open. Background screenshots were stale/unreliable. The runtime reports
  optional missing map artwork/camera-node files and a reflection cubemap array
  needing a bake; those results are not claimed as verified.
- See `docs/POVO_CAMPUS_PLAYTEST.md` for the current reproducible build, package,
  runtime logs and manual checklist. Local build logs are ignored by Git.

## 23 October 2026 — user-rejected appearance and first visual correction

- The user rejected the campus appearance. Foreground CS2 inspection confirmed
  severe overexposure, mottled baked lighting, bare door openings and oversized
  red stair blocks. The earlier functional checks did not establish visual quality.
- Added explicit original material color/normal/roughness maps, grey aggregate
  floors, acoustic ceiling grids, doorway trim, skirtings and corridor fixtures.
  Reduced exposure and fitted the lighting-density guide around the two floors;
  enabled explicit model lightmaps and the higher-quality bake/denoising setting.
- Replaced full-height stair columns with thin treads/landing in both rendering
  and collision, and sloped the outer handrails. All 90 source tests and the two
  clearance audits pass. A new runtime walk traverses both flights up and down
  normally, without jumping, crouching or noclip (157.5/228.4/299.7/228.4/158.0).
- Final map/model/radar build has zero resource failures and 2,168 nav areas.
  Baked reflections in the isolated addon, verified all old entry hashes were
  unchanged, and adopted the baked package: 32,390,610 bytes, 138 entries, all
  CRCs pass; SHA256 941ae271dff76063407438475400e2d68f2582a6d3ec80030826e9ec49bcf8aa.
- Saved actual before/after engine screenshots and inspected the corridor,
  A215 and A103 directly. Lighting is substantially cleaner, but A103 remains
  too dim, public spaces sparse, furniture simplified and exterior work rough.
  No finished-art or whole-map visual acceptance is claimed. See
  `docs/POVO_VISUAL_REVIEW.md` for screenshots, camera positions and evidence.

## 23 October 2026 — complete rooms, solo exploration and four enclosed stairs

- User requested normal-width corridors with rooms on both sides, all rooms
  open/furnished, off-white circulation floors and enclosed stairs with open
  black doors. Added repeated room bays, opened A101/A102 and furnished all
  room types: 25 ground rooms and 31 first-floor rooms. The original offline
  interior study is preserved separately. Added subdivisions and repeated
  furniture remain approximate, not a claim about official room inventories.
- User accepted the complete room layout and requested an identical mirrored
  red stair opposite each Studio N1/N2/S1/S2, excluding central Aula studio.
  Mirrored the southeast flights, landings, rails, opaque enclosure, glazing
  and open black double doors with red panic bars into all four corners.
  Regenerated slab/ceiling openings and radar shafts for all four cores.
- All 97 tests pass; the standing-envelope audit passes 63 ground and 75 first
  stations, including both sides of every stair portal. Final tests/audit logs
  are `build/gameplay/campus-four-stairs-tests.log` and
  `build/gameplay/campus-four-stairs-audit.log`. The reviewed source plan is
  `exports/povo_campus/layout_review.png`.
- `play_campus.cmd` defaults to one-human/no-bot exploration, paused offline
  warmup, respawns and invulnerability; `-Fly` adds noclip, `-Match` retains
  match defaults. Setup waits for this exact campus map before applying settings.
- Recorded the user's later Povo 2 adaptation in both campus configs: retain
  two Povo 1 floors, start the bridge corridor at current A202/A203 and move
  those rooms into the corresponding empty ground corner. This room move is
  deferred until Povo 2 development; current A202/A203 remain upstairs.
- The full-quality four-stair compile is logged at
  `build/gameplay/campus-four-stairs-build.log`. Runtime/build completion
  evidence is maintained in `docs/POVO_ROOMS_STAIRS_REVIEW.md`.
- Final model/map/four-radar compilation has zero resource failures and 3,938
  nav areas. All 40 runtime walking stages passed across the four stairs and
  eight doorways with noclip off and no jumping. A half-second exit probe was
  too short; a full-second crossing passes without geometry changes.
- Baked the reflection array, verified every source entry unchanged, and
  adopted the package: 39,431,526 bytes, 147 entries, all CRCs pass, SHA256
  516c4c11b2914f388f73bffee3ef3a109f56122598be2771d40f081b17c1e029.
  Installed/build hashes match. Inspected foreground corridor, mirrored stairs,
  Studio N1, A101 and LAB, and saved six unretouched engine images under
  `exports/povo_rooms_stairs_review/`. Large-room lighting remains uneven;
  repeated furnishings and exterior detail remain provisional.
- Final live state verifies one human, zero bots, paused warmup (no countdown),
  normal walking, and the player at the ground entrance facing into the hall.
  The exploration helper now sets that initial view direction; its three tests
  also pass after this final adjustment. CS2 is left running for exploration.

## 23 October 2026 — Povo 2 bridge, floor-1 arrival and fixed door signs

- User accepted the four-stair revision, requested a fix for room numbering
  above doors, and authorized starting Povo 2 with the floor-1 corridor and
  bridge. A Computer Use Escape interrupted the first inspection; the user
  clarified they were moving the game window and explicitly resumed work.
  Keep the chat visible while observing CS2. The live engine setting
  `r_always_render_all_windows true` allows captures without repeated focus
  changes; the solo launcher now defaults to a smaller 960 × 600 window with
  optional `-Width`/`-Height` parameters.
- Implemented the earlier approved two-floor adaptation. A202/A203 move to
  the empty ground northeast corner, keeping labels and repeated furnishings.
  Their old upper area contains a 3.5 m corridor, a furnished bridge study
  room, cabinets and a bench. A 30 m level bridge leads into an initial
  approximately 18 × 32 m Povo 2 floor-1 area with a lobby/print station,
  corridor, rear cross corridor and four furnished study bays. Povo 2 labels
  are provisional descriptive names, not asserted official room numbers.
- Photos 61–56 guide glazed bridge sides, alternating dark steel braces,
  horizontal louvers, pale flooring, ceiling panels/lights and open glazed
  doors. Photos 63–62 guide the Povo 2 corridor/arrival. The old high bridge
  scenery is removed and the overlapping Povo 2 east mass/facade is clipped
  away from the opened section. Other Povo 2 floors and the rest of its
  layout remain a later phase; original photo floor identities stay intact.
- Room labels now have wall-specific upright angles, no camera rotation,
  outside-wall text origins, centered white text sized to fit physical blue
  plaques, and IDs including both floor and room. Updated navigation seeds,
  illumination/probe/density coverage, overview bounds and radar include the
  new route. Geometry has 17,071 visual and 2,443 collision boxes.
- All 99 source tests pass, plus the three solo-helper tests after the final
  rendering-setting adjustment. The clearance audit passes 67 ground and
  94 upper stations. The new route also has sampled continuous support and
  standing clearance tests. Source plan:
  `exports/povo_campus/povo2_connection_review.png`.
- Preserved the previous verified package/report in
  `build/povo2-backup-20261023-202208/`. Build log:
  `build/gameplay/povo2-bridge-build.log`. Current build/runtime evidence and
  limitations are recorded in `docs/POVO2_CONNECTION.md`.
- Final build completed with zero resource failures and 4,352 nav areas.
  Reflection baking added only the cubemap array, preserving every previous
  entry hash. Final package: 41,136,321 bytes, 161 entries, all CRCs pass,
  SHA256 71ebcb9717f1e2aac5b12ecdde499e74562a8f1dd023846cf777d2c48eeda821.
  Build and installed hashes match.
- Sixteen normal walking samples cover the complete corridor/bridge/Povo 2
  route and the return, with no jumping/noclip during walking. Preserve
  `build/gameplay/povo2-bridge-walk.json` as that route-only evidence.
  The broader optional doorway harness had unreliable held/stop input and
  failed its extra room assertions; do not claim all 24 stages pass. A
  separate normal forward probe entered the west room. Source audit reaches
  all new room aisles. Restarted CS2 after testing to clear injected movement;
  successive getpos samples in the new session confirm no residual movement.
- Inspected the bridge, Povo 2 corridor/study bay, bridge approach and fixed
  A201/Studio N2/A202/A203 signs. Saved unretouched engine conversions in
  `exports/povo2_review/`. Photos guide the route; Povo 2 study labels/layout
  remain provisional and repeated board/desk fit-outs need further art work.
- Final fresh live state: one human, zero bots, paused warmup, noclip off,
  default multi-input-bind restrictions and player facing the bridge from
  Povo 1 floor 1. The 960 × 600 game window remains open for exploration.
  See `povo2-final-explore.log` and `povo2-final-state.log` locally.

## 23 October 2026 — Povo 2 planimetry source

Implemented the user-requested entrance-relative arrangement: sealed opaque
frosted-glass reception ahead, tables/chairs to the right, left corridor and
stair portal to the left of reception. B110-B113 are empty shells with grey
tile floors and west-wall blackboards (right when entering southwards).
Added a grey 3.6 m/storey switchback from the existing bridge arrival at local
7.6 m to ground 4.0 m, basement 0.4 m and parking -3.2 m. These dimensions are
explicit estimates. The basement uses photos 3-1 for its corridor, green wall,
display case and black doors. Generic covered parking has rubberized grey
asphalt, columns, bay markings and five simple cars. Exterior approach stops
at the entrance landing; reception office decoration remains deferred.

Integrated geometry/materials with the campus builder and included new lights,
fixed signs, navigation seeds and four radar sections in the map pipeline.
Packaging/verification derives radar requirements from all overview sections,
including the two new basement levels. No Valve compilation, deployment or
runtime automation was performed; the installed route build was preserved.
Standalone source review, OBJ and provenance: exports/povo2_planimetry/.
Details and reproduction: docs/POVO2_PLANIMETRY.md.

Validation: 105 source tests pass; the existing Povo 1/bridge 161-station audit
passes. The independent Povo 2 audit passes 30 horizontal stations across four
levels and 75 supported stair/landing samples with standing headroom. Fixed
a blocking half-wall at the basement cross-corridor junction during this audit.
These are source-geometry checks, not CS2 collision, navigation or visual proof.

## 23 October 2026 - Corrected Povo 2 lower-floor planimetry

Re-read photos 12/9/3/1 and applied the user's corrections. The ground right
corridor is now longer, with 12 tables along its west/right wall and B110-B113
doorways opposite on the east/left wall. The boards move to south walls, still
the player's right when entering. The reception front wall continues left/north
with a screened stair-access opening. User confirmed the basement topology:
the stair door opens directly in the long corridor's right/east wall about a
third from its north end; turn right from the door for the short branch at
that end. Updated draft geometry, independent audit, tests and review.

The top-right first-floor panel is preserved pixel-for-pixel (SHA256 of pixels:
ce2e3f75134de4582ce1f7ad8527b3b170d7073fa0f56db7d5690109d725debd).
The independent renderer/audit no longer assume the live campus enables the
full lower-floor draft. Preserved the compact-arrival gate and the separately
owned first-floor source/build. No deployment, compile or runtime action ran.
The full suite passes 109 tests. Standalone clearance passes 29 lower-floor
stations, one local upper landing, and 75 draft stair/headroom samples; linking
that draft core to the compact W1 stair remains a separate integration step.
See docs/POVO2_PLANIMETRY.md for the shared-file coordination checkpoint.

## 23 October 2026 - Align classroom wall and remove +1 review

Moved the B110-B113 corridor wall from E15 to E21, flush with the reception
front and its leftward wall extension. Doors and boards follow the corrected
room bounds. Removed the +1 drawing and obsolete cached reference image from
the standalone review; it now contains only ground, -1 and -2 in three panels.
The separately implemented first-floor source is untouched. All eight Povo 2
tests and the independent clearance audit pass after the adjustment.

## 23 October 2026 - Basement stair block at corridor start

Aligned the -1 stair block's lower edge with the long corridor start, bringing
the door towards that start. In shared local coordinates the basement corridor
and its far-end short branch shift north by 14 m, preserving the physical draft
stair core and every other floor. Updated basement fixtures, route stations,
layout description and drawing. All eight focused tests and the standalone
clearance/headroom audit pass. No compile or deployment was performed.

## 23 October 2026 — Compact Povo 2 bridge arrival

Kept the two bridge-exit alcoves, their bench and printer. Replaced provisional
W1 with an enclosed gray switchback down from local z7.6 to z4: twenty 18 cm
risers, 30 cm treads, 2 m flights, a mid landing, guarded upper shaft and open
black double doors with red panic bars at both levels. Removed E1 and all
W2/E2/rear-corridor geometry and furniture. Solid corridor east wall and end
wall at N26 close this phase; the lower door opens to a closed vestibule.
Povo 1 retains 57 furnished rooms, relocated A202/A203, and all four red stairs.
Updated fixed SCALE signs, nav seeds, both radar floors, and focused plan.

Alberto authorized messaging the concurrent Add povo 2 game planimetry chat.
Coordinated the new upper/lower door positions and shared build ownership.
The compact_arrival gate preserves that standalone ground/basement source
without superimposing its conflicting shell/core. Its audit/tests now run
independently; later integration must align the stairs first.

109 source tests pass. Horizontal clearance passes 67/88/4 stations and the
compact stair tests cover tread support, headroom and both portals. Full Valve
compile/lighting/nav/radar/package succeeded; final nav has 4,282 polygons.
Reflection bake preserved existing VPK entries and added one cubemap. Final
package is 40,402,867 bytes / 162 entries, full CRC passed, installed/local SHA
cbffd1a07529e495a56e66f82aa1b85473314891779826c7ddb0914ef31bbd40 match.
Previous package backed up in build/p2-compact-backup-20261023-211637/.

CS2 normal walking passed six consecutive stair/door stages down and back up,
using one starting placement and no intermediate teleports. See
build/gameplay/p2-compact-walk.log and .json. Inspection teleport placements
produced some stuck warnings; the interrupted drop probe is not a passing
traversal check. Actual screenshots are under exports/povo_campus/runtime/.
Railings and dimensions remain simplified prototype geometry. Final game
position is stationary at the bridge exit, normal walking, one human, no bots,
paused warmup. Small game window placement and visible chat were preserved.
Details: docs/POVO2_CONNECTION.md; build log: build/gameplay/p2-compact-build.log.


## 24 October 2026 — requested map adjustments

Ground Studio E1 in Povo 1 becomes a sealed frosted reception, using the same
shared glazing generator as Povo 2. Circulation floors are slightly darker.
Povo 2 ground tables reach the hall midpoint; its boards move to the opposite
wall, the hall ends at the last room, and labels read B111–B114 from the entrance.
Each upper north/south study room becomes separate UOMINI/DONNE restrooms,
with grey floors, two toilet cubicles per room, washbasins and fixed door signs.

126 tests pass. Campus clearance passes 65/92/4 stations; integrated lower
floors pass 32 stations and 72 stair samples. All eight cubicles and four
washbasins are reachable in the source audit. CS2 normal walking passes all
four restroom entrances and the shortened corridor wall. Native screenshots
verify reception, fixtures, tables, board position and visible B111–B114 text.
The final label correction uses -fshallow -entities -vpkincr; hashes confirm
only default_ents.vents_c and the parent vmap_c changed, preserving world,
collision, baked lighting and navigation. Full compile has zero failures;
the existing duplicate-bone warning remains.

Final reflection-baked package: 42,212,394 bytes / 217 entries, SHA-256
289ffd586414bdb425be2bb5390b60e40870a8bd08eb19ccceb63b4db45555fa.
All CRCs and asset hashes pass; local and installed test-addon VPKs match.
Previous addon/source/game/package state is backed up under
build/map-adjustments-backup-20261024-103106/. The final solo session is
stationary at Povo 1's entrance, facing reception, normal walking, no bots,
paused warmup. Details and screenshots: docs/POVO_MAP_ADJUSTMENTS.md.

## 24 October 2026 — integrated exterior, compiled and walked

The user approved integrating the exterior study into the campus map, with
entrance glass at 20% transparency. The roads, the road beneath the bridge,
the surface lot and residential backdrop, both east fronts, the Povo 2 double
entrance and terrace, and the straight ramp into the covered Povo 2 parking now
build with the campus by default (`config/povo_exterior.json`,
`tools/povo_exterior_integration.py`). Interior furniture is preserved.

The first combined compile stalled for over 80 minutes in CS2's bot
"Compute Approach areas" pass (9,210 open nav areas against 4,282 before).
Exterior builds now add a `trigger_survival_playarea` box, which CS2 reads only
to skip that bot-analysis step; the nav mesh is still generated. The rebuild
took 14.5 minutes with zero failures. The reflection bake added only the cubemap.
Final package: 44,979,765 bytes / 344 entries, all CRCs pass, SHA-256
13973fad877f8070b5941295908b6865c70c3b7029bfe2b9fa80ed4ceabb52ba; local and
installed copies match.

135 source tests pass. Normal walking in CS2 passes all 21 waypoints on six
exterior routes: both door banks, the ramp down and up, garage to original
parking, and the Povo 1 external stairs. Eight engine screenshots are under
exports/povo_campus/runtime/exterior_*. The exterior remains blockout art; the
garage is dim and the road beneath the bridge is heavily shadowed.
Details: docs/POVO_EXTERIOR.md.

## 24 October 2026 — independent review of Claude's integrated campus

Reviewed f5a5f6 and reproduced the geometry/material/provenance exports exactly.
Corrected the horizontal audit's floor-material exemption: low overhead slabs
and raised floor surfaces now obstruct standing clearance. All campus routes
still pass, with corrected parking walkable/reachable-cell counts. Added
regressions for those false-positive cases.

The launcher and packager now require the compiled map, model and map cfg in
addition to the radar checks. Expanded the native exterior walking tool to ten
routes / 35 waypoints, added a solo/correct-map precondition and timestamped
package hash evidence, and preserved error reports when cleanup disconnects.
All 140 tests pass, as do 65/120/4 campus stations, 8/8/17 Povo 2 stations,
72 stair samples, 1,210 exterior samples and all 344 package entry CRCs.
A fresh CS2 solo session passes all 35 waypoints on the existing package.

Package and installed dedicated-test copy retain SHA-256
13973fad877f8070b5941295908b6865c70c3b7029bfe2b9fa80ed4ceabb52ba.
No geometry/material recompile was necessary. Game returned to the Povo 1
entrance, stationary, normal walking, no bots and paused warmup. Current-state
documentation replaces stale undeployed-lower-floor claims at the entry points;
older checkpoints remain explicitly historical. Details and evidence:
docs/CODEX_REVIEW.md and exports/povo_campus/runtime/codex_review_walk.json.
Objective rounds, bot match behavior, clean-install and independent-client
validation, performance and final art/lighting remain release gates.

## 24 October 2026 — user screenshot corrections, rebuilt and verified

Restored 51 opaque shared room partitions after office/window conversions,
including the reception-to-classroom wall shown by the user. Rebuilt Povo 1's
red entrance stair straight outward after a 3 m landing, ending on continuous
upper paving. A 35%-opaque glass cover starts at the exterior threshold and
ends before the street pavement. Added Povo 2's left entrance terrace, confirmed
as left while facing the entrance from the street. Added a 4 m fixed fence on
the far side of the street opposite both entrances, following its grade; the
street between the buildings remains open. Three simple volumes supply fence
collision. Reversed the basement's far branch west/right, removed obsolete
draft fire-door leaves and an orphaned door fragment, updated lights/radar,
and filled exterior/underside voids with concrete. Distant context is unlit and
excluded from physics/navigation.

All 146 tests pass. Source audits pass 65/120/4 campus stations, 8/8/17 Povo 2
stations, 72 stair samples and 1,234 exterior samples. Model compile: 949.756 s;
map compile: 705.313 s, zero resource failures, 9,633 nav areas. The preexisting
duplicate-bone warning remains. The shader decoder confirms glass opacity 0.35.
The reflection bake adds only its cubemap; all 341 previous entries are unchanged.

Final package: 44,632,576 bytes / 342 entries, SHA-256
a05d5d3adf6080d8797f343a8a29271e20a4fce0ef4a8be7f4b5afa0e35de860.
All 342 CRCs/source asset hashes pass and the installed test-addon copy matches.
Native normal walking passes 41 waypoints on 13 routes. Three separate movement
checks stop at the restored classroom wall and the fence opposite each building.
Eight engine captures were inspected, including the concrete outskirts (noclip
inspection only). The game is foreground/full screen at Povo 1's exterior
entrance facing the corrected stairs, no bots, normal walking, paused warmup.

Prior installed addon, source and package backup:
build/user-corrections-backup-20261024-175726/. Source screenshots are preserved
under data/reference/user_feedback/2026-10-24/. Native logs and package evidence
are in build/gameplay/user-corrections*, with portable JSON/screenshots under
exports/povo_campus/runtime/user_corrections/. Details:
docs/POVO_USER_CORRECTIONS.md. The launcher now respects saved display settings;
use -Windowed to explicitly request the old small review window.

## Standard/winter atmosphere and interactions — 25 October 2026

Implemented separately selectable standard and winter maps sharing the same
campus architecture, collision, radar geometry and objective. Added revised
lighting/exposure, cooler overcast winter lighting, light exterior snowfall,
thin snow on exposed roofs/vegetation/edges and wet paving. Shelters and interior
floors are excluded from dressing. Added local ventilation, garage, wind and
traffic soundevents with room-specific reverb. Stock ambient loop markers were
verified; listening-level calibration is not claimed. Additional furnishing is
deferred as requested.

Replaced fixed-open proxies with 38 native door leaves across fire stairs,
entrances and four classrooms. Two small east stair panes are breakable and
return on round reset. Restored correct physics surface assignments by splitting
collision imports into seven explicit ModelDoc groups; checked compiled PHYS
surface tables and per-triangle contacts. Winter adds snow/concrete contact
groups. Both packages contain the identical compiled campus model.

Both native builds and reflection bakes completed. Standard package:
45,173,047 bytes / 391 entries, SHA-256
5de0dc71af0cc6e2aaac4570e5445611d72768f66a3ed6069ea66507bd7d461f.
Winter package: 43,453,973 bytes / 396 entries, SHA-256
5f54c53436c22570695a66b58532282ece794cc63f97309187eb193f9975d2f7.
Cubemap adoption checks every prior source entry and permits only the reflection
addition. All entry CRCs pass, and installed test-addon copies match.

All 156 source tests pass. Native interactions: standard 14/14, winter 15/15.
Normal walking: each version 41/41 waypoints on 13 routes. Local 2v2 mechanics:
each version 11/11, including both buy zones, outside-zone rejection, C4 plant,
defuse and elimination. The defuse uses controlled placement and a temporary
team change; this does not establish autonomous bot objective completion,
competitive balance or independent-client synchronization. The user explicitly
selected local bot tests. Six native camera views per season are recorded.

The winter map is left in solo exploration at the Povo 1 entrance, one human,
zero bots, paused warmup, normal walking. Launch standard with play_campus.cmd
or winter with play_campus_winter.cmd; saved fullscreen settings are preserved.
Backup: build/atmosphere-backup-20261024-205704/. Final portable evidence:
exports/povo_campus/runtime/atmosphere/. Implementation and scope:
docs/POVO_SEASONS_AND_INTERACTIONS.md. No commit or publication was made.


## 26 October 2026 — breakable glass (source only, not yet compiled)

Playable building glass now breaks: 295 panes (287 after the automatic doors below) are generated as separate
`func_breakable` entities (material Glass, health 1) instead of static model
geometry. They are cloned from the buy-zone mesh, the same proven path as the
exterior play-area trigger; `func_shatterglass` is excluded by CS2's csgo.fgd.
Covered: room, courtyard, stair, bridge and bridge-door windows, the Povo 2
entrance door banks, the basement display, both front canopies, and the
library/canteen wings in front of Povo 1. Those wings are now 184 panes (two per
frame bay) over an opaque core, ready for their interiors to be modelled.
Kept sealed: both receptions (unplayable offices), car cabins, screens, the
residential backdrop and the solid Povo 2 backdrop/annex facades.

`is_breakable_glass` (tools/build_povo_campus.py) selects the panes; export()
removes them from the static OBJ and collision, while build_geometry() keeps
them solid so the clearance audits are unchanged. 138 tests and the campus,
exterior and Povo 2 audits pass on Linux.

Still to verify on Windows: compile and package, that panes render and break
in game, glass01 UV scale on the cloned meshes, lighting through former glass,
nav mesh behaviour at windows (bots must not path through intact panes), and
frame rate with ~300 extra entities.


## 26 October 2026 — automatic Povo 2 entrance doors (source only)

The four Povo 2 entrance banks (two outer, two inner) now slide. Each sliding
leaf (glass, band and bottom rail) is a `func_door` named after its bank,
spawned closed and moving by its own width over the sidelight it used to park
on. A players-only `trigger_multiple` 2 m deep on each side fires `Open` on
OnStartTouch and `Close` on OnEndTouchAll; doors use wait -1, and Touch Opens
stays on as a fallback. The connection rows copy the field types read from
Valve's `cs_script_demo.vmap` (targetType 7 = by name). The sashes now stop
short of the leaf track so closed leaves do not cut through them. These leaves
leave the breakable-glass set (287 panes); the fixed sidelights still break.
Povo 1's entrance is an open doorway with no doors, so it is unchanged.

The audits still use the parked-open leaves, so walking clearance is unchanged.
140 tests and all audits pass on Linux. Windows checks: docs/TODO.md.


## 26 October 2026 — Povo 1 sliding entrance, photo-matched stairs (source only)

Povo 1's 2.2 m entrance is now one Povo 2 style automatic sliding bank
(3.6 m wide, 1.8 m clear, two leaves over fixed sidelights) at the east wall.
The bank builder is shared (`door_bank` in tools/povo2_exterior_entrance.py),
so the library and canteen can reuse it once their interiors exist. Map step:
285 breakable panes, 30 `func_door` parts, 5 sensors, 10 I/O rows.

Stairs, after photos 38/39/47-49 (Povo 1) and 64-66/4-8 (Povo 2): both were
small islands in oversized stairwells. Each now has two flights side by side,
each half the well width (Povo 1 about 3.9 m in its 8 m well; Povo 2 3.0 m),
a 0.3 m well between them and full-width floor and mid landings. Povo 1 flights
and its mid landing are solid to the floor. Povo 2 keeps its enclosure; two new
partitions cut the well to 6.3 m and close the unused ends, and its
lower-floor copies cut their shafts from the shared `shaft` instead of fixed
coordinates.

Railings follow the photos: a sloped top handrail over six horizontal bars,
posts about every 1.2 m, and wall handrails on the outer sides. The rails and
bars are sheared faces (`tools/povo_stairs.py`) instead of per-tread boxes,
which is why the old handrails showed as a few separate rectangles. Collision is
a stepped `_clip_` panel that render_obj() leaves out of the visible model.

140 tests and all three audits pass on Linux. Windows checks: docs/TODO.md.


## 26 October 2026 — three-flight Povo 1 stairs, red stairwells, lift shaft (source only)

User review of the previous stairs: better, but Povo 1's cores have three
flights. From the floor landing one flight goes left, one runs straight across
the far end and one comes back on the right, around a central well (photos 48,
P007). Each core now has 7 + 6 + 7 risers (0.18 m) on 0.28 m treads, three
3.17 m wide flights, two square corner landings and a 1.68 x 1.96 m well with
railings on all three inner sides. The floor landing is now 3.6 m deep. Floors
inside the stairwells, on both levels, are the same red as the stairs.

Studio E2, right of the reception, is now the lift ("ASCENSORE"). A working
CS2 lift would need a moving platform that carries players, which is untested
here, so the shaft (2 x 2 m, both floors) holds a straight ladder on its back
wall. CS2 makes the ladder climbable through a world mesh with
`materials/tools/toolsinvisibleladder.vmat` (cloned from the lightmap density
volume); the visible rails and rungs have no collision. An upper ledge on the
corridor side lets players step off. Upstairs the shaft takes the south-east
corner of A214. The rest of E2 is sealed. Config: `elevator` in
config/povo1_campus.json.

141 tests and all three audits pass on Linux (new lift stations on both floors).


## 26 October 2026 — new photos filed, Povo 2 lift (source only)

27 user photos filed as P091–P117 under
data/reference/povo_photos/walk_2026-10-26/ (photo 13 withdrawn by the user),
with manifest, credits and locations. They cover Povo 2 -1 and ground floor
spaces not yet built, the sunken yard by the -1 exit, and the canteen entrance
and ground floor. The user's layout description is in
docs/POVO2_INTERIOR_BRIEF.md; canteen notes went into
docs/LIBRARY_CANTEEN_BRIEF.md.

Povo 2 now has a lift beside the stair door (photo 12): a ladder shaft at
E20.1–22.4, N17.2–19.4 opening into the ground hall, the -1 long corridor and
the +1 bridge corridor (`lift` in config/povo2_connection.json, `lift()` in
tools/povo2_integration.py). Two hall lockers were removed and the -1 display
case moved north to clear the openings. Audit stations on the ground ledge,
the -1 floor and the +1 ledge are all reachable. 141 tests and all three
audits pass on Linux; not yet compiled or tested in CS2.

## 26 October 2026 — implement photo-guided interior additions (source, not compiled)

The new photos now drive geometry rather than serving only as briefs:

- B111–B114 have tile, dark continuous desk rows, beech seats, screens and
  end glazing. Side aisles and the teaching area are clearance-tested.
- The Povo 2 left corridor connects a provisional B106 computer room (blank
  monitors) and B108/B109 classrooms with bamboo finishes, raked seating and
  full-height glazing. Labels, subdivision and dimensions are estimates.
- The table corridor now reaches a glazed aula lobby with lockers and a
  user-authorized temporary aula magna, raked seats and a continuous centre aisle.
- The CIBIO branch has two accessible furnished offices on its left, a glazed
  entrance and decorative closed black office doors along the corridor.
- The short south wing is now the canteen; the long north wing is the library.
  Solid cores are removed. Both have two floors, Povo 1-facing sliding entrances,
  breakable facade panes and switchback stairs with continuous rail bars.
- The canteen has a projecting L-route porch with two sliding banks, a ground
  bar, orange serving counters, orange tables/blue chairs and an upstairs
  sliding exit onto the raised pavement. The library has ground reception and
  three estimated reading rooms per floor with tables/chairs.

User-confirmed relationship: Povo 1, canteen and library ground floors are
level; their first floors meet the street. Their source levels are 4.0/7.6 m.
The Povo 1-side pavement and external stairs/canopies are corrected accordingly.

The user confirmed that the existing game bridge and building floors are correct
and must remain unchanged. Povo 1 stays at two playable floors; Povo 2 retains
its -2/-1/ground/+1 arrangement and the established bridge connection. No floor
or bridge relocation is required. The earlier request to reconcile the real
building's level names is superseded by this instruction.

The basement locker corridor, indoor push-door/stair route, sunken yard and
outdoor steel stair are now implemented. The new route joins the retained
outer pavement without blocking the existing Povo 1 -> Povo 2 walk. Internal
five-riser and outdoor fifteen-riser stairs are gameplay estimates, not surveyed
counts. Yard elevation and dimensions are configurable in povo2_additions.json.
Photo 19's GPS places the yard observation on the front-street side, approximately
local (55,18) m with ~4.7 m reported horizontal error; this is supporting location
evidence, not a metric survey or a level measurement.

Editable sources: config/povo2_additions.json, config/povo_wings.json,
tools/povo2_interiors.py and tools/povo_wings.py. Source checks:
`python -m unittest discover -s tests -q` (150 passed, no skips), plus
`python tools/audit_povo_wings.py` (four level routes and 44 stair samples pass).
`python tools/render_photo_additions.py` creates a labelled Povo 2 review plan.
`python tools/audit_povo_yard.py` checks yard access and 22 stair/landing samples.
Real VMAP conversion, compilation, door/glass behaviour and walking still need
Windows CS2 Workshop Tools. A source test's mocked compiler output is not a VPK.

## Layout corrections after user review

- The Povo 2 classroom corridor now runs straight south from reception alongside
  the whole room sequence. The large PC room is first, on a short side opening,
  and no longer projects far sideways. The stair entrance is a black double
  doorway beside reception; a screened vestibule connects it to the retained
  stair core. Core flights, bridge and floor elevations remain unchanged.
- From the basement stair exit facing east, right/south then right/west reaches
  CIBIO. Both playable offices are on the left/south of that westbound passage.
  The separate exit route is left/north a few metres, then right/east. The
  review image now draws arrows for both narrated routes.
- The canteen entrance/porch moves south to about the former white counter's
  location. Entering eastward places the bar on the right/south, a smaller
  ground dining area on the left/north, and the stair/fire doors straight ahead.
  The upstairs furniture leaves the relocated stair and exit approach clear.
- The temporary aula magna is on the right/east of its lobby, entered through
  the lobby's short edge, rather than continuing ahead through the far wall.

These are photo/narrative-guided gameplay dimensions, not a measured survey.
CIBIO ceilings fit beneath the unchanged sloped road. Actual sloped mesh/box
intersection is checked before excavation; broad bounding boxes alone would
incorrectly report road overlap at this location.

Validation after these corrections: all 154 tests pass, including explicit
layout checks for the two basement turns, straight classroom corridor, stair
entry beside reception, canteen left/right/ahead arrangement, and the aula on
the lobby short edge. Geometry and radar were regenerated. Windows checks
remain unrun.

## 26 October 2026 — Windows merge and source validation

Fetched `origin/main` at `0015b88` and preserved the existing Windows work in
commit `f43a8a2` on `codex/windows-before-photo-additions-20261026`. Merge commit
`cd9336b` combines the photo additions with the geometry corrections, seasonal
maps, ambience, physical surfaces and native fire/classroom doors. The active
branch is `codex/photo-additions-windows`. `Gameplay.mp4` remains untouched and
untracked. Nothing has been pushed or published.

The merge retains the straight covered Povo 1 approach and raises its twenty
0.18 m risers to the new 7.6 m street/wing floor. Automatic entrance banks
replace the older interactive entrance leaves, avoiding two overlapping door
systems. The sunken yard replaces part of the old direct terrace route; the
exterior audit follows the remaining outer pavement, while the yard audit checks
the new exit/stair connection. A yard station was moved beside the lawn rather
than onto its raised edge; standing-clearance exemptions were not relaxed.

All 176 source tests pass. Campus clearance passes 64 / 122 / 4 stations; Povo 2
passes 8 / 18 / 49 stations and 72 stair samples; wings pass 15 / 11 / 12 / 10
stations and their stair checks; the yard passes 22 stair/landing samples.
The exterior audit passes 1,215 route samples. The regenerated binary VMAP,
decoded independently with dmxconvert, contains 349 breakable panes, 54 sliding
parts, 28 rotating doors, nine entrance sensors and 159 navigation markers.

Installed addon source/game trees and existing packages were copied to
`build/photo-additions-backup-20261026-183237/` before deployment. Native model
compilation succeeds with zero failures; the shared model takes 12m21s and
reports the existing OBJ duplicate-bone warning. Compiled PHYS inspection confirms
all seven shared contact surfaces and both winter contact surfaces. Evidence:
`build/gameplay/photo-additions/shared-surfaces.json` and `winter-surfaces.json`.
Full compilation is recorded in `build/photo-additions-compile.log`.

Map lighting, packaging and engine validation are in progress. Source checks
and successful model compilation do not establish those later gates.
