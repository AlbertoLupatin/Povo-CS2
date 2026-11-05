# Full build of the latest povo-updates bundle — 4 November 2026

The user requested another complete build using `claude/povo-updates.bundle`.
The selected bundle is 108,640 bytes, modified at 17:54:35 CET on 4 November.
`git bundle verify` passes; its prerequisite is the current HEAD,
`c22a11a6c56c19e99475484b2ba1b1880fc53aaa`.
Bundle SHA-256:
`99bd28f6d0b95791f3bacf3b313928a0d706642031ffe1db9ee5b1a79494d906`.

Bundle head: `3225d4049bb0b125218e5bfccb98ad8c74c3ad87`
(`claude/magical-planck-7tbolq`). It contains two additional commits:

- `0cd77f5`: adopt the remake's aluminium and frosted-glass textures.
- `3225d40`: regrade the Via Sommarive crest-road joint and update the lamp checklist.

The bundle changes 20 files, including the new textures, material mapping,
exterior road-joint clipping/closure logic, source tests and documentation.
It does not request a change to the approved Povo 2 −1 room layout.

## Source and isolation

The run snapshots the complete current working source, including the verified
build/import optimizations, background-tree probe lighting and the two
clean-packaging fixes from the [previous complete run](HPC3_BUILD_20261104.md).
It then applies only the bundle's prerequisite-to-tip diff inside that snapshot.
`git apply --check` succeeds; all 20 changed paths are applied to the private
source directory. The ordinary working-tree files and its pre-existing README
merge conflict are not changed by importing the bundle. The fetch creates a
separate remote-style Git ref for provenance; it does not switch/merge branches.

`bundle-provenance.json` records the bundle SHA-256, exact base/tip commits and
hashes of its applied files. `HANDOFF_MANIFEST.json` is updated after applying
the bundle. The working optimization changes overlapping bundle tests are kept;
the complete resulting suite runs before compilation.

The user authorized closing CS2 for comparable GPU timing; it was closed before
the run. The laptop is on AC power. Both private custom-addon directories start
empty; no compiled project model or lighting data is seeded from the installed
addon or a previous candidate. The installed base game/tools are shared through
directory junctions. Original installed map/model hashes are recorded before
compilation for comparison after completion.

## Build execution

Run directory: `build/local-benchmark/20261104T165933Z/`.
Started **17:59:33 CET**, launcher PID **720**.

The timer includes source staging, bundle application, runtime/tool staging,
all source tests, generation, complete native model/map compilation, normal
quality-1 lighting with a 1024 atlas, navigation and bomb-damage baking, radar,
packaging/full CRC checks and compiled collision audits. No stage is omitted
from the whole-build comparison. The runner is
`build/hpc3/20261104/local_full_benchmark.py`, passed the bundle as its second
argument after the CS2 installation path.

Live files:

- `build/local-benchmark/benchmark-live.log`: stage and native compiler output.
- `build/local-benchmark/benchmark-errors.log`: errors, if any.
- Run directory `source-tests.log`: complete source-test output.
- Run directory `timings.json`: stage states and final total duration.
- Run directory `bundle-provenance.json`: exact bundle and applied-file identities.

On completion the runner saves per-run copies as `full-build-live.log` and
`full-build-errors.log`. Successful package output stays in the run's
`source/build/package/`; normal-lit visual and movement review are separate,
and there is no automatic promotion or Workshop publication.

Initial stages: source staging **19.138s**, bundle application **0.672s** and
isolated runtime staging **0.344s** passed. **All 421 source tests pass**
(160.067s in the test runner; 162.025s including process startup). Geometry
generation and native compilation followed.

The timing-file writer then hit a Windows `WinError 5` rename lock immediately
before geometry export started. This was an operational logger failure, not a
failed source test or native compile. The runner now retries transient rename
denials. The same run resumed after validating the passed staging/tests and
confirming that its compiled-output directories were still empty. Its original
17:59:33 start is retained, so the final wall time includes the logger failure
and recovery delay. Launcher PID after recovery is **27124**; original failure
logs and timings are preserved in `logger-failure-*.log` and
`timings-before-logger-recovery.json`. Geometry export and every native build/bake
step still execute in full.

## Completed result

The full cold standard-season build completed at **18:18:20 CET**:
**1,127.308 seconds / 18m47.3s**, measured from the original 17:59:33 start.
This includes source and bundle staging, all 421 tests, geometry/map generation,
all model/material compilation, normal native lighting, navigation and bomb-damage
baking, radar, packaging, full CRC verification and compiled collision audits,
**including the timing-logger failure/recovery pause**. Native/model outputs were
empty before compilation resumed; no compiled project output was borrowed from
another build. This is the full-run total, not a model-only measurement or an
estimate with the recovery delay subtracted.

| Stage | Seconds |
| --- | ---: |
| Geometry generation / map preparation | 41.011 / 87.411 |
| Cold main model / paving model | 46.467 / 1.624 |
| Complete native map compile | 461.196 |
| GPU lightmapping (inside map compile) | 87.080 |
| Bomb-damage bake (inside map compile) | 278.600 |
| Packaging and full CRC verification | 8.821 |
| Compiled collision audits | 2.542 |

Do not add nested lightmapping/bomb times to the parent map-compile time.
The normal 1024 atlas packed **228,686 charts**. Native navigation generated
14,873 areas. The earlier unconnected-ladder warning at `(2683.07, 410.236, 444)`
is still present; this is the same warning in previous successful native builds.

The resulting package is
`build/local-benchmark/20261104T165933Z/source/build/package/trento_povo_campus.vpk`:

- **63,112,930 bytes**, **1,204 entries**, **all 1,204 entry CRCs verified**.
- SHA-256: `98a21c01cb4fa5f6cb51f388a48a53985dba4b4bd9046002cf0e0de98fe267ea`.
- Compiled checks: **22,997 floor samples**, **72 column samples**, **36 sealed-door
  samples**, zero missing, plus all seven expected physical surface types.
- `layout-comparison.json` confirms the basement rebuild, −1 corrections, West
  Offices, stairs and lift metadata match the previous verified build.
- The three original installed map/model hashes are unchanged.
- The `povo-updates.bundle` file still matches the selected SHA-256 at completion.

The compact checked result is `benchmark-result.json`; complete stages are in
`timings.json`. The final post-bundle source-manifest SHA-256 is
`a902728c925d0c91ba04c748e4e2381583c8d37054d45214cfb2abf064cf0a35`.
The main source tree has not been merged with the bundle; its changes exist in
this candidate's isolated source copy. The candidate has not been promoted to
the approved package or published. **Normal-lit visual review and ordinary
movement testing of the updated road/materials remain pending.** Passing the
build/source/collision/CRC checks does not certify those separate runtime checks.

The user's subsequent screenshot request found the running `trento_povo_campus_test`
addon still contained the 2 November VPK (`18d154a0…`). The new candidate was then
loaded in `trento_povo_bundle_review` and five normal-lit native screenshots were
captured and inspected. See [the screenshot record](../exports/bundle_review_20261104/README.md).
This targeted review does not certify a complete visual/movement pass; unresolved
dark skyline shapes and ramp underside patches are documented there. The ordinary
launcher remains on the older approved package; a separate review launcher is
provided alongside the screenshots.
