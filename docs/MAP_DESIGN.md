# Real-World Trento FPS — map design brief

## Product and current decisions

Create a recognizable Trento environment that runs as a multiplayer map in an existing FPS.
The host game supplies movement, weapons, combat rules, networking, and match management.
The deliverable is an installable, playable map package plus editable map sources.

The user selected a detailed campus area for small-team matches as the first experience.
The user selected CS2 as the host game and can use Windows for editing and compilation.
The user selected Povo's Polo Ferrari as the first campus. The game mode and final playable boundary remain undecided.
Use QGIS and Blender on Fedora 44 for geographic preparation and modeling, then Hammer on Windows.
Prove this source-to-game workflow before committing to detailed production assets.

## Provisional location and boundary

Start with a compact exterior slice of Povo's Polo Ferrari; Mesiano is a future map candidate.
The initial geographic blockout covers E666150–666350, N5103650–5103950 in EPSG:25832:
200 × 300 m around the two main buildings. This is a modelling crop, not a frozen playable boundary.
Its source terrain and approximate building volumes still require in-game route testing.

Start with a roughly 200–350 m design envelope in the main horizontal dimensions.
This is a scope budget for exploration, not a measured campus extent or an engine limit.
Draw the actual boundary only after checking geography and testing traversal in the chosen game.
Keep the playable area compact; use simplified surrounding scenery to retain its setting.
Include nearby streets only where they improve orientation or provide useful match routes.

Treat central Trento, Mesiano, and Povo as potential separate maps initially.
Connecting streets are a later scope decision requiring measured travel times and performance tests.
Do not promise a combined city-and-campus map before the first campus map is proven playable.

## Reference and reconstruction standard

Maintain a real-world master that preserves the source geography and records its coordinate system,
origin, units, source dates, attribution, and known gaps or uncertainty.
Keep this master separate from the game map so gameplay edits do not silently replace measured data.
Record every source and its permitted reuse before including derived assets in a distributable map.
Reference viewing does not establish permission to extract imagery, geometry, or textures.

Prioritize the features that make the chosen place recognizable:

- Street and path alignment, relative building positions, and major building silhouettes.
- Terrain contours, level changes, ramps, stairways, and retaining features.
- Distinctive public spaces, visible architectural features, vegetation, and landmarks.
- Facade proportions and material character before small decorative objects.

Separate measured, reference-derived, and assumed geometry in the working records.
Do not infer complete building interiors from exterior imagery or label invented rooms accurate.
Add only selected interiors supported by suitable reference and useful to the match layout.
Mark unavailable interiors as closed; omit them from the first blockout unless essential to circulation.

## Translation into a playable map

Keep real-world scale as the starting point and document the conversion to the host game's units.
Test door widths, clearance, steps, ramps, jump heights, and traversal against the actual player controller.
Preserve recognizable spatial relationships while allowing documented, limited gameplay adjustments.
Log each adjustment with its location, original condition, change, and gameplay reason.
Examples include removing a snag point, simplifying collision, or adding a readable map boundary.

Design a connected route network with alternate approaches and opportunities to disengage.
Use the site's real geometry to establish orientation and varied encounters.
Avoid creating long mandatory walks, a single unavoidable choke point, or direct spawn-to-spawn fire.
Set spawn locations, objectives, and any pickups according to the chosen game's native rules.
Evaluate balance through played rounds; an overhead layout alone does not validate it.

Provide continuous, predictable collision on roads, terrain, paths, ramps, and stairs.
Where appropriate, separate visual stair geometry from simpler walkable collision.
Test boundaries, ledges, vegetation, corners, and elevation transitions for trapping or unintended access.
Keep gameplay-relevant sightlines and collision consistent with the visible environment.

## Development phases and acceptance gates

### 1. Select the site and prove the toolchain

Choose a CS2 game mode and verify the Windows Hammer editing, compilation, and installation workflow.
Confirm data availability and reuse terms; select a campus boundary and record unresolved reference gaps.
Prove that a minimal map can be packaged, loaded, and joined in the existing game before detailed modeling.
That technical check is a toolchain milestone, not the finished Trento map.

### 2. Build and play the campus blockout

Build the selected site's main terrain, building volumes, streets, paths, and level changes.
Add the chosen mode's required entities, functional collision, spawns, and deliberate playable boundaries.
Run it inside the host game and adjust layout from traversal and encounter observations.

The first multiplayer blockout passes only when:

- Two independent game clients can join the same session and complete a match using native game rules.
- Players can traverse all intended routes without falling out, becoming trapped, or reaching unfinished space.
- Spawning and match start, end, and restart work; required objectives are reachable where applicable.
- A tester can install the packaged artifact in a clean supported game installation using the included instructions.
- All map dependencies, required host-game content, and distribution conditions are listed explicitly.
- Source files, build steps, known issues, and the tested game version accompany the artifact.

Two clients establish multiplayer function; representative small-team sessions are still needed to assess balance.

### 3. Add recognizable detail

Replace validated blockout volumes with reference-based architecture, terrain materials, and landmarks.
Add selective interiors, vegetation, props, lighting, ambient sound, and navigation aids as supported by the game.
Recheck collision and match flow after geometry changes; retain the geographic change log.

### 4. Optimize and release

Measure performance in the actual game on the user's machine and record settings and test conditions.
Optimize geometry, materials, visibility, collision, and surrounding scenery using the chosen engine's tools.
Set a performance target from measured results; do not assume a frame rate from hardware specifications alone.
Repeat representative multiplayer rounds and clean-install verification for the release package.
Deliver the playable package, editable sources, installation/build guide, source/license register, and known limitations.
