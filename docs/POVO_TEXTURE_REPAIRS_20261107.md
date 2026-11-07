# Campus texture repairs on 7 November 2026

Continues the texture audit and source repairs from the interrupted Codex chat
`Pull changes and build map`. The original audit and 26 baseline views are in
`C:/Users/Alberto/Documents/Codex/2026-11-06/p/outputs/texture-audit/`.

## Implemented finishes

- Restore the dark sidewalk material on the registered Via Sommarive fence-side
  meshes and upper campus-side segment.
- Give the repaired junction, landings and campus-side Via verge the adjoining
  scored paving finish.
- Match the Povo 1 entrance landing and outdoor library and canteen access joins
  to the plaza. Native review of the first package exposed the canteen omission,
  so this continuation extended the material rule and rebuilt the final package.
- Extend the lobby terrazzo to the stair wall and the upper bridge approach to
  the west room wall. These thin finish strips are excluded from collision.
- Continue terrazzo across the internal Povo 2 bridge extension.
- Match the Povo 2 vestibule floor and ceiling to the hall, removing its older
  separate grout and ceiling-grid geometry.
- Replace the library hedge boxes with the textured leaf geometry already used
  for the opposite planting bed.

The previous agent's applied repairs passed its 39 focused tests. This
continuation ran the full suite twice. The final run passed 462 tests in
228.597 seconds. The final campus OBJ passed the overlap audit over 751,134 faces with
zero overlapping pairs.

## Build and runtime evidence

The standard campus build uses
`build_campus.cmd --optimize-import --lightmap-max-resolution 1024`
with normal-quality lighting. Changed model inputs triggered model compilation.
The final build completed in 19m09.6s, including tests and full CRC verification.
Logs are in `build/handoff/20261107T161908588904Z/`. The first build, which also
forced model compilation, is in `build/handoff/20261107T155635296431Z/`.

The final standard package is 73,536,257 bytes and has 1,536 verified entry CRCs.
Its SHA-256 is
`c9c3ddc0b0adcec6ef82905cb4d58ce6a3252175fd270d0dcd0bbfb5ad485ebc`.
The launcher installed the same package into the native review addon.

Compiled basement collision checks passed 12,707 samples on floor -1 and 6,237
on floor -2, all 36 column samples and 36 fixed-door surface samples. Results
are in `build/texture-repairs-20261107/compiled-basement-final.json`.

The previous standard package is backed up at
`build/texture-repairs-20261107/previous-standard.vpk`.
Verification scripts and overlap results are in the same directory.

Eleven native views were individually reviewed with normal lighting enabled.
The repaired paving, terrazzo strips, vestibule floor and ceiling, bridge
threshold and leaf hedge render with their intended finishes. Screenshots are
in [the review directory](../exports/texture_repairs_20261107/).
Existing dark shading below the raised library approach remains visible.

The final package passed 12 ordinary walking routes over 46 waypoints. These
cover both directions along the library-side bridge sidewalk, the repaired
junction and Povo 2 apron, the automatic Povo 2 entrance, the Povo 1 lobby finish
strip and the Povo 2 bridge threshold. The capture manifest and runtime report
in the review directory record the final package hash. Multiplayer and a
complete campus walkthrough remain outside this verification.

`play_campus.cmd` loads the final standard package. The previous standard package
remains backed up, and the solo review session was closed after verification.
