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

