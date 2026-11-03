# Povo 2 −1 office and wall finishes — 2 November 2026

The user's finishing request preserves the [definitive floor layout](POVO2_MINUS1_DEFINITIVE_LAYOUT.md).
Room names, bounds, door positions, corridor extents, stairs, terrace plates and
the Draw.io entrance remain registered to the approved baseline.

- W07–W23 exterior faces use the same glass, metal frames and horizontal bands
  as the internal office fronts. Party walls and walls facing C5/C7 remain solid.
  W01/W02/W04/W05/W06 have no face on the exterior perimeter of this office block.
- W01 and W02 each have seven computer workstations in two rows; W04 has five.
  Every other W room, including W06, has exactly one desk, computer and chair.
  Room labels and existing room kinds are retained.
- CIBIO / OFFICE 1 and 2 each have six computer workstations in two rows.
  The user clarified that their glass goes on the **opposite exterior wall**,
  away from the corridor entrance. Their entrance-side walls remain opaque.
- Photo 1's missing white wall is restored on the C7 west-end boundary.
  Its left side has a 0.95 m empty doorway into WI2, with no door entity or leaf.
  The WI2 audit path uses the centre of the remaining passage.
- Photo 2's long terrace/corridor facade is opaque white wall. Its six original
  door locations have black pairs fixed shut. Their former glass door entities
  and through-door test routes are removed. The terrace floor and railing stay.

Implementation: [final finishing pass](../tools/povo2_minus1_finishes.py), applied
after the legacy basement and Draw.io entrance passes. Glazing bands belong to
their breakable panes, so they do not leave floating strips or solid barriers
after a pane breaks. Furniture is checked against standing routes and room bounds.

User reference screenshots are preserved in
`data/reference/user_feedback/2026-11-02/minus1-finishes/`.

Source verification:

- All **369 source tests pass** in the project virtual environment.
- **5,236 standing-route samples pass**, including both directions.
- **662,050 render faces**, with **zero overlapping coplanar faces**.
- Baseline comparison confirms identical room names/bounds/door records,
  corridor extents, stairs, Draw.io entrance/terrace, exterior meshes and
  exterior collision meshes, and every non-basement box.
- [Source comparison](../exports/povo2_minus1_finishes_20261102/source-validation.json)
  and [surface audit](../exports/povo2_minus1_finishes_20261102/render-surfaces.json).

Native verification completed on 2 November 2026:

- Valve's native model compilation and the retried 1024-atlas map lighting bake
  completed successfully. The first stalled bake was preserved; no atlas retiling
  or lighting workaround was applied.
- The actual packaged model passes **239 finishing checks**, **22,997 basement
  floor samples**, **72 column samples** and **36 fixed-door surface samples**.
- All **12 native screenshots** were individually inspected with
  **`mat_fullbright = 0`**. The glazing, furniture, opaque terrace wall and empty
  left doorway are visible; the previous black/turquoise lighting corruption is
  absent in these views. See the [contact sheet](../exports/povo2_minus1_finishes_20261102/native/contact-sheet.jpg)
  and [capture manifest](../exports/povo2_minus1_finishes_20261102/native/captures.json).
- **16 ordinary standing walks / 48 waypoints pass**: both directions through
  W01, W02, W04, W10, W19, CIBIO / OFFICE 1 and 2, and the empty WI2 doorway.
  Each route uses one initial placement, then ordinary movement with noclip off.
  **21 new breakable panes** exist and all **12 former moving terrace door
  entities** are absent.
- The initial walking harness allowed 15 cm of sideways error and failed the
  W01 return. The existing 2.5 cm doorway tolerance passes both directions.
  WI2's tight return turn also needed a 200 ms stopping pause to avoid residual
  sideways motion. Both failed attempts are retained in the walking evidence;
  no geometry was changed to satisfy the controller.

Walking evidence: [main run](../exports/povo2_minus1_finishes_20261102/native-walking.json)
and [WI2 repeat](../exports/povo2_minus1_finishes_20261102/native-walking-wi2.json).
The main run records its WI2 return failure; the separate repeat supersedes
that route and passes in both directions.

All six fixed black terrace door pairs also block ordinary movement from
both sides (**12 collision checks**). Sample exterior panes in W10 and
CIBIO / OFFICE 1 are present and break when shot (**4 entity/bullet checks**).
See the [native interaction report](../exports/povo2_minus1_finishes_20261102/native-interactions.json).

The exact visually reviewed and walked standard candidate was promoted to
`build/package/trento_povo_campus.vpk`, which `play_campus.cmd` copies into its
test addon on the next launch. The promoted bytes pass all **1,232 entry CRCs**.

- Package size: **62,778,837 bytes**.
- SHA-256: `96cfccfdd484f325ea239deae5dc9cd797ca7dbc7c3896ab40fced7b2a8e3f93`.
- Structural model SHA-256: `38218680740a32c587f0bfad2b54eed8caa9449158cff49773a173026c156ce2`.
- Approved pre-finishing package and manifest are preserved under
  `build/minus1-finishes-20261102/backup/approved-baseline.*`.
- [Validation summary](../exports/povo2_minus1_finishes_20261102/validation-summary.json)
  and [promoted-package verification](../exports/povo2_minus1_finishes_20261102/promoted-package-check.json).

This verification covers the finishing update in a solo native addon. Winter,
Workshop, multiplayer and a complete campus walkthrough were not tested or
updated. No layout or geometry changes were made while continuing testing.
