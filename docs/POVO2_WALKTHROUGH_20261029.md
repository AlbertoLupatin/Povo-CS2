# Povo 2 walkthrough repairs — 29 October 2026

## East entrance, retraced from photo 46

The user rejected the second eastern plan as well ("so off"). That plan had a
5 m C5 running past the core to N=26, a terrace door 4.9 m north of the office
facade, a glazed C7 stub and an east "stair-exit arm" from `corridor_4`. None
of these is on photo 46. The entrance is now retraced from the original photo,
rotated north up, and registered on the fixed core, the W office rooms, WI1
and the C7 core bypass:

- **C5** is a 2.6 m corridor on the offices' east facade, east 20.5–23.1, from
  the facade line (N=2.0) to C7 (N=18).
- The **terrace door** (the plan's exit star) is at C5's south end, on the
  facade line. It opens onto the south run of the approved terrace plan.
- **WI1** is the first opening on the left, through its glass pair. The leaves
  park inside WI1 so the narrow C5 stays clear.
- **C7** opens full width onto C5 under the core's south face, with no door.
  Its bypass under the core now has corridor tile instead of office wood.
- A **sealed door** ends C5 at N=18, straight ahead. It is permanent solid
  geometry, like the two 29 October junction doors, and is recorded as
  `minus1_corrections.c5_north_junction_door`.
- C7 continues east past C5 through a **door pair** (photo 46's door at the
  C7 bay) to the exit corridor. This keeps the 29 October markup's link from
  the stair corridor to the exit corridor. The original lower junction door at
  (34.5, 18) and its closed area are restored.
- East of C5, **E1 and E2** are closed rooms.
- A **terrace link** east of E2 joins the south run to the existing landing
  of the UP stair to the street. Photo 46 doesn't show it; its position is
  provisional. Earth retaining walls replace the old west garden slope there.

The trace and its pixel evidence are in `config/povo2_east_entrance.json`, which
`tools/povo2_playtest_repairs.py` builds from. Its own drawing,
`exports/povo2_walkthrough_20261029/east_entrance_photo46.png`
(`python -m tools.render_povo2_east_entrance`), shows it next to the photo,
with Codex's previous plan dashed. C7's offset under the core is unchanged:
the core is shared with floors 0 and −2.

The earlier evidence crops, `plan46_east_end_evidence.png` and
`plan46_core_original.png`, are in the same directory.

The user's five screenshots identify missing exit leaves, exposed outdoor
undersides, the temporary lift/ladder at floor 0, missing stair guards and an
incorrect eastern W approach. The user subsequently confirmed the intended
arrival order: terrace entrance, WI1/wooden office corridor on the left,
C7/main W corridor on the left, then a closed door ahead. They also confirmed
that screenshot 2 is taken from Povo 2's outdoor metal UP stairs.

## Changes

- Remove the substitute Povo 2 ladder and its shaft walls, portals and ledges.
  Fill its floor and ceiling openings at −1, 0 and the bridge arrival. Its
  metadata remains marked `enabled: false` for earlier layout references;
  neither the climbable brush nor its runtime climb route is generated.
- Restore the paired outdoor exit doors after the basement shell is rebuilt.
- Rebuild the eastern entrance from photo 46, as described above.
- Supply glass door pairs at the 22 W office openings. They use the estimated
  trace positions; the leaves are 0.10 m wider than the earlier 0.95 m review
  opening to accommodate a standing hull and frames on the 0.1 m audit grid.
- Replace the six solid decorative placeholders beside the CIBIO corridor
  with usable glass terrace exits at their existing positions. Glaze this
  corridor side and supply a guarded terrace. The terrace stops at N=55.9,
  before the restricted upper return beginning at N=56.5.
- Include the W office glass in the native `func_breakable` export. Opaque
  privacy bands belong to their pane entity and disappear with it; they have
  no separate permanent collision. Door leaves use native rotating entities.
- Complete the exposed landing and turn guards. Move the lower middle-flight
  railing to its inner edge and add wall handrails. Keep the flight clear.
- Add closed soil embankments beside the outdoor UP stairs. The street edges
  follow the existing road grade. Preserve the paved walking route and fill
  the earth down to −3.42 m so the garden is not a floating sheet. This does
  not add an unsurveyed first-floor interior plan.
- Include the new terraces in the basement radar.

The final-coordinate changes are in `tools/povo2_playtest_repairs.py`, after
the W offices are assembled. The five original screenshots are preserved in
`data/reference/user_feedback/2026-10-29/walkthrough/`.

## Checks and artifacts

- The 336-test run in `build/handoff/20261029T201649295208Z/tests.log` and
  `source-clearance.json` predate the photo-46 entrance and describe Codex's
  layout. After the rebuild, 19 Povo 2 and campus test modules (154 tests)
  pass, including West Offices reachability, basement routes and floor
  surfaces.
- The native build (`build/handoff/20261029T211903359215Z`) passed: 337
  tests, compile with fast lighting, and the package check (1,245 entries,
  all CRCs). The exported surface-overlap audit has not been rerun.
- `tools/playtest_povo2_walkthrough.py --reload` passed in a solo session on
  30 October: **133/133 checks, 37/37 routes**. These include the terrace, WI1
  and C7-east door pairs (closed blocks, open passes) and both bullet-break
  checks. The glass check now waits 1.5 s for the rifle and fires for 0.8 s;
  the earlier 0.18 s tap registered no hit. Two earlier runs stopped when CS2
  answered position queries late; these were not map failures. Screenshots
  are in `exports/povo2_walkthrough_20261029/runtime/`.
- `tests/test_povo2_walkthrough_repairs.py` checks the entrance itself: the
  C5 width and facade-line door, WI1 then C7 open on the left, the sealed
  door at N=18, no arm, the restored lower door, and all four entrance routes
  walked both ways with a standing hull.
- `exports/povo2_walkthrough_20261029/eastern_approach.png` shows the assembled
  eastern approach. Reproduce with `python -m tools.render_povo2_walkthrough`.
- The native build runs through `tools/build_on_windows.py --fast-lighting`.
  Native results are recorded separately after compilation and packaging.
- `tools/playtest_povo2_walkthrough.py` checks a guarded solo session: door
  existence, closed/open collision, W and terrace routes, pane breakage from
  bullets, and normal-lighting screenshots. It never terminates the user's
  game. With `--reload`, it first verifies the existing solo map, unloads it,
  replaces the dedicated test package and reloads it.

Existing local changes present before this task are retained. Standard-map
compilation is in scope; Winter and Workshop publication are separate.
