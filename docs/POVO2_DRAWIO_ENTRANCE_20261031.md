# Povo 2 -1 entrance from the user's corrected Draw.io

**FINAL / USER-APPROVED:** on 2 November the user confirmed the current in-game
layout as the [definitive Povo 2 −1 map layout](POVO2_MINUS1_DEFINITIVE_LAYOUT.md).
This implementation is accepted; older alternatives must not replace it.

**Current package:** the 31 October lighting bake was visibly corrupt despite
passing collision/CRC checks. It is superseded by the
[2 November repair and native visual verification](RENDER_LIGHTING_CORRUPTION_20261102.md).
The layout and shared collision model are unchanged. The current compiled
plan/check reports use repaired package SHA-256
`6a52dc98ddf5050f430894597337ec86361557d95adf9f1798771a8e1f74c9ee`.

The user confirmed `east_entrance_edited.drawio` as the correct local arrangement
and requested its implementation on 31 October. The original is preserved under
`data/reference/user_feedback/2026-10-31/`. Its SHA-256 is
`7d97dccaa2254e7f1e0fa2378ff2eadb3391ec9d9e787d2ceba9e5a95d1c9bf4`.

## Implemented arrangement

`tools/povo2_drawio_entrance.py` reads the actual Draw.io shapes and replaces the
local entrance region after the legacy basement passes. The earlier
`config/povo2_east_entrance.json` remains a historical reconstruction input; it
does not describe the final entrance.

- C5 retains its shared office facade and 2.6 m corridor width and extends north
  to the drawing's sealed end at N 21.0767, instead of N 18.
- E1 and E2 extend east to E 31.8, instead of E 29.7. Their west wall shares C5's
  east wall. Both room volumes remain closed.
- C7 joins C5 from the west under the main stair. The added eastward arm and its
  opening entities are removed. The existing restricted northern research
  corridor stays isolated.
- The terrace entrance remains on the south facade. The UP stair is directly
  south of it, across the terrace: E 20.5-23.0, N -5.71-0.29. A new excavation
  removes the old road/ground surfaces from its standing clearance.
- The metal stair to Garden -2 follows the south terrace run, E 31.8-42.3,
  N 0.29-2.0, with two ten-riser flights and a middle landing. A lower paved
  approach joins the retained garden. Paving covers the full excavation width
  and retaining edges close its sides; its old footprint is not relabelled as a
  new survey. The obsolete stair runs, terrace detour and their railing bodies
  are removed; the former UP-stair excavation is filled.

- The terrace is one strip, E 8.5-31.8, as drawn (user correction, 31 October).
  The old entrance's end wall at E 20.2-20.36 split it in two and is removed.
  The ground slab over the west half is excavated like the east half, and the
  west half is closed by a retaining wall along its south edge (to the UP
  stair) and at its west end. `tests.test_povo2_drawio_entrance` walks the
  whole strip in both directions and checks both edges are closed.

Small drag offsets at shared edges in the Draw.io file (approximately 4-14 cm)
are snapped to the established office facade and terrace datum, preventing
cracks and double walls. The edited north/east and stair positions are retained.
Both raw and normalized bounds are recorded in the campus provenance under
`povo2.drawio_entrance`. Dimensions remain the drawing's fitted coordinates,
not independently surveyed measurements.

The source route metadata and native replay now follow the terrace entrance,
WI1, C7 and the farther sealed end. Previous test routes through the deleted arm
are removed. The main stair, West Office rooms, two accessible labs, fixed
research doors and interior floor stack retain their accepted registration.

## Validation and package

All **359 source tests pass**. They include the original basement/office
connectivity and restricted-area guards, the Draw.io bounds and removed-arm
checks, both directions on the stair/landing routes, full-width lower-approach
support and closed matching road-junction colliders. The source log is saved
under `exports/povo2_drawio_entrance_20261031/source-tests.log`.

The build `build/handoff/20261031T150439148864Z/` passed its package check. It
was superseded the same day by `build/handoff/20261031T180852703141Z/`, which
adds the continuous terrace and straight C7 (362 source tests and the package
check passed; see `docs/WORKLOG.md`). The user's running game is not reloaded or
moved by the source/build work.

### Earlier packaged geometry verification — 2 November

The latest standard build finished on **31 October at 23:45 Europe/Rome**.
Its 362 source tests and full package check passed. The current VPK is
64,450,766 bytes with 1,237 entries, all CRCs verified again on 2 November.
SHA-256: `e221ccbecc828c0e6a46900a57e2f6abdcf15a0a8b3a087d01a9ffbff555db5f`.

The package's extracted static PHYS passed all 80 entrance checks:
relocated stair/landing support, the sealed C5 end, widened east facade,
full-width lower approach and absence of the obsolete arm and UP stair.
The basement regression check also finds no missing support across 22,997
floor samples, 72 column samples and 36 fixed-door samples. These are compiled
geometry checks; a new native player traversal was not performed.

Evidence: `exports/povo2_drawio_entrance_20261031/compiled-layout-check.json`,
`compiled-floors.json`, `current-package-check.json` and
[the actual compiled collision plan](../exports/povo2_drawio_entrance_20261031/compiled_plan.png).
The older `source_plan.png` predates the later straight-C7 correction.
Close CS2 and run `play_campus.cmd` to copy and load this package; the launcher
loads the latest compiled package and does not rebuild source changes.
