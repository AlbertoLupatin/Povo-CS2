# Standard stair repair evidence — 27 October 2026

The repaired standard package has passing evidence for all 50 route objectives,
14 feature checks, 11 controlled local-match checks and 219 source tests.
The [acceptance summary](acceptance-summary.json) records scope and input hashes;
the [runtime write-up](../../../../docs/POVO_SURVEY_RUNTIME_RESULTS.md) explains
the two collision repairs and the remaining limitations.

| Check | Result | Evidence |
| --- | --- | --- |
| Native build | Model 1 compiled / 0 failed; map 673 compiled / 0 failed | [Compiler log](compile.log) |
| Package | 942 entries / 61,507,512 bytes; all 942 CRCs verified | [Package check](package-check.json) |
| Six repaired stair directions | 6/6 passed | [Report](critical/survey-runtime.json), [transcript](critical/survey-runtime.log) |
| Full walking/climbing sweep | 49/50 passed; original aggregate **failed** | [Report](full/survey-runtime.json), [transcript](full/survey-runtime.log) |
| Corrected intermediate landing | Both directions passed; same floor-height tolerance | [Report](landing-retest/survey-runtime.json), [transcript](landing-retest/survey-runtime.log) |
| Combined route coverage | **50/50 objectives passed** on the same package | [Per-route evidence mapping](coverage-summary.json) |
| Automatic entrances / bullet breakage / round restoration | 14/14 passed | [Report](features/features.json), [transcript](features/features.log) |
| Controlled local match | 11/11 passed | [Report](match/survey-match.json), [transcript](match/survey-match.log) |
| Source suite | 219 passed | [Source test output](source-tests.log) |

The complete sweep stopped one intermediate check on the final stair tread,
where the standing hull still overlapped neighbouring risers. The test now
continues onto the full floor landing before measuring its floor height.
Both directions then pass. The failed sweep is preserved unchanged; the
combined result is not presented as a passing single sweep.

Compiled collision evidence: [previous template obstruction](previous-world-obstructions.json),
[repaired Povo 2 clearance](compiled-p2-clearance.json) and
[repaired canteen clearance](compiled-canteen-clearance.json).

Native captures, unchanged:

- [Povo 2 upper stairs](screenshots/repaired_p2_upper_stairs_0000.png).
- [Canteen stairs](screenshots/repaired_canteen_stairs_0000.png).

Package SHA-256:
`e08a52bbf22d4b9e668d88cd5becbb8375f34831393fb1996dc59073332af3c4`.
The [fresh-launch log](launch.log) and [final session](final-session.json)
record the staged package and final solo exploration state. Status checks the
loaded map name; it does not independently hash loaded memory.

The Duplicate Bone import warning and one unconnected Povo 2 ladder-top
navigation link remain. Player lift checks use a normal jump to detach and do
not establish autonomous bot ladder traversal. Local match checks use controlled
placements and a temporary team change for defusing. Winter, independent-client
multiplayer, balance and performance remain outside this verification.
