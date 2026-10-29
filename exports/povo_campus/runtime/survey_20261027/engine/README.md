# Native engine evidence — photo-survey package

This directory preserves the package before the stair repairs. The
[repaired standard package](../../stair_repair_20261027/README.md) has passing
evidence for all 50 route objectives; the historical results below are unchanged.

Feature and local match checks are complete. The original 50-route walking
sweep finished with 36 passes and 14 failures. Resumed native testing resolves
some harness/path failures; upper Povo 2 stairs and canteen stairs still fail.
Combined latest evidence covers 44 passing route objectives and six failures;
this is not a new complete single sweep.
See the [runtime results](../../../../../docs/POVO_SURVEY_RUNTIME_RESULTS.md).

Recorded on-disk standard package SHA-256:
`2edab45d2625ec635410e0d9af5f353842e6ca51d1cee8b225adb48b05692b61`.
The harness checks the live map name `trento_povo_campus`, not a hash of the
already-loaded map bytes. This identity limit is retained in the source reports.
No runtime geometry changes are represented by these copied results.

## Features: 14 of 14 checks passed

[Report](features/features.json) and [raw log](features/features.log), recorded
18:41–18:42 UTC on 27 October 2026. Checks cover the expected 530 native glass
and 58 door entities; walking-triggered opening at the Povo 1 entrance, Povo 2
outer entrance and library entrance; bullet breakage of A103 teaching-front,
Acquario corridor and library panes; and restoration of all three on the next
round. This is representative feature coverage, not every pane or doorway.

## Local match: 11 of 11 checks passed

[Report](match/survey-match.json) and [raw log](match/survey-match.log), recorded
18:53–18:54 UTC on 27 October 2026. A local 2v2 session with three bots checks
both teams' purchases, rejection of buying at an audited outdoor point, controlled
C4 assignment, rejected planting outside the site, planting at site A, native
defuse, an elimination round win and a normal bot round running. The isolated
defuse check uses controlled placements and a temporary roster team change.
This does not demonstrate a full autonomous bot match or two independent clients.

## Screenshots

Original engine captures, copied unchanged:

- [A103 aisle](screenshots/survey_a103_aisle_0000.png): green chairs, dark rows,
  freestanding board and glazed teaching/corner fronts.
- [Acquario](screenshots/survey_acquario_start_0000.png): shared wood tables,
  corridor/courtyard glazing and steel stair context. Existing debug text is
  retained in the capture.
- [Courtyard overview](screenshots/survey_courtyard_overview_0000.png): glazed
  multi-storey courtyard and steel stairs. This overview is visual evidence,
  not proof of a normal walking route.

## Walking: completed sweep and diagnostic follow-ups

- [Original complete sweep](walking/full-v3/survey-runtime.json) and
  [transcript](walking/full-v3/survey-runtime.log): 36/50 passed, aggregate failed.
  All Povo 1 corner/courtyard stairs, bridge, Acquario, A103 aisles, library stairs
  and canteen entrance passed both ways.
- [Resumed probes](walking/resume-probes/survey-runtime.json) and
  [transcript](walking/resume-probes/survey-runtime.log): 8/14 passed, aggregate
  failed. All four lower Povo 2 stair traversals pass using full floor landings;
  the library partition detour passes both ways; both lift dismounts pass using
  a normal jump after climbing 0.65 m above the upper floor. The four upper
  stair traversals and the first basement detours still fail.
- [Repeated failures and captures](walking/failure-captures/survey-runtime.json)
  and [transcript](walking/failure-captures/survey-runtime.log): repeat the
  Povo 2 lower-module reverse failure and both canteen stair failures. The first
  source-planned basement detour also fails on CIBIO glazing; it is preserved
  rather than counted as a passing route.
- [Canteen standing-hull intersections](walking/canteen-standing-hull-diagnostics.json)
  identify two source wall fragments at the failed stair turn.
- [Final basement portal route](walking/basement-portals/survey-runtime.json)
  and [transcript](walking/basement-portals/survey-runtime.log): 2/2 passed,
  aggregate passed. This path clears both the lift and stair enclosure before
  turning through the CIBIO entrance without breaking its glass.
- [Combined coverage](walking/coverage-summary.json) maps each of the original
  50 route objectives to its latest evidence: 44 passed, six failed. The lift
  entries explicitly require a normal jump off the ladder.
- [Source tests](source-tests.log): all 215 passed during the resumed session.

Failure views: [Povo 2 landing](screenshots/resume_p2_upper_module0_down_return_0000.png),
[canteen ascent](screenshots/resume_amenity_canteen_stair0_up_0000.png),
[canteen descent](screenshots/resume_amenity_canteen_stair0_up_return_0000.png).
The Povo 2 capture has severe dark/colored rendering at the failed position;
it is retained unchanged and does not establish its exact rendering cause.
The [final session state](resume-session.json) leaves solo exploration at the
Povo 1 entrance, noclip disabled and scripted movement inputs released.

Follow-up scripts are saved beside their reports as `replay.py`; run from the
repository root with that root on `PYTHONPATH`. These scripts write diagnostic
reports and do not implement map repairs. Their process exit code is not the
test verdict; inspect the saved aggregate `status`.

The original reports remain unchanged. Separate route paths and jump-assisted
dismounts do not recast that original sweep as passed. Source and staged VPK
hashes match the package above; the in-memory identity limit still applies.
The compile checkpoint's known ladder-top navigation warnings and metric/photo
registration limits remain applicable. Winter was not tested here.
