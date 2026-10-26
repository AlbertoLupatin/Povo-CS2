# Independent review — 24 October 2026

Reviewed Claude's integrated-campus commit `f5a5f6`, including the exterior,
entrance, lower-floor assembly, collision audits, packaging and launch tools.

## Corrections

- The horizontal clearance audit excluded every `floor_*` material from
  obstacles. It could therefore approve a route through a raised slab or below
  a ceiling too low to stand under. Vertical bounds now determine obstruction,
  including floor slabs and stair treads. Regression cases cover low ceilings,
  raised slabs and a sufficiently high ceiling. The actual campus still passes.
- The launcher verified radar assets and CRCs without requiring the map,
  campus model or gameplay configuration. Its verification now explicitly
  requires those three nonempty runtime resources. Packaging uses the same
  check. Radar-only verification remains available for existing callers.
- The exterior walking script covered six routes. It now checks ten, adding
  the complete front connection, bridge road to ramp, north road and surface
  parking. It refuses other maps or sessions with other humans/bots before
  changing player state. Reports identify the on-disk package hash and UTC
  times. Connection loss during cleanup no longer masks the original failure
  or prevents writing diagnostic evidence. Output paths resolve from the repo,
  and `--output`, `--package` and `--port` allow separate review runs.
- README and Windows handoff now describe the integrated, compiled state.
  Previous statements that the lower floors were undeployed are identified
  as historical checkpoints.

## Verification

- All **140 tests pass** on Windows, including the added failure regressions.
- Regenerating the campus exactly reproduces the tracked OBJ, collision OBJ,
  material sources, ModelDoc and provenance before the audit correction.
  No geometry or material correction was required by this review.
- The stricter campus audit passes **65 / 120 / 4 stations**. The integrated
  Povo 2 audit passes **8 / 8 / 17 stations** and **72 stair samples**. Its
  parking walkable-cell counts decrease because raised floor geometry is now
  correctly included as an obstacle; all required stations remain reachable.
- Exterior source clearance passes **1,210 samples on eight routes**.
- The compiled package passes **344 entry CRCs**, radar alignment against the
  generated overview, and the new map/model/configuration presence checks.
- A fresh solo CS2 launch passes **35 normal-walking waypoints on ten routes**.
  Each route uses one initial placement; no teleporting or noclip is used
  between its waypoints. Expected floor heights are checked at each waypoint.

The compiled package remains **44,979,765 bytes**, SHA-256
`13973fad877f8070b5941295908b6865c70c3b7029bfe2b9fa80ed4ceabb52ba`.
The installed dedicated test-addon package has the same hash. No recompile is
needed for these audit, verification, test and documentation changes.

The portable walking evidence is
[`codex_review_walk.json`](../exports/povo_campus/runtime/codex_review_walk.json).
Full local evidence is in `build/gameplay/codex-review/` (walking JSON/log and
package report), `codex-review-tests.log` and `review-launch.log`.
The session is returned to Povo 1's entrance, stationary, normal walking,
one human, no bots and paused warmup.

## Reproduce

```powershell
python -m unittest discover -s tests -v
python tools/audit_povo_campus.py
python tools/audit_povo2_integrated.py
python tools/audit_povo_exterior_integrated.py
python tools/verify_cs2_package.py build/package/trento_povo_campus.vpk --map trento_povo_campus --model povo1_campus --overview exports/povo_campus/radar/trento_povo_campus.txt --full-crc
```

With CS2 closed, run `play_campus.cmd`. Once solo exploration is ready:

```powershell
python tools/playtest_povo_exterior.py --output build/gameplay/codex-review
```

These are prototype checks. They do not establish a complete objective round,
bot traversal/balance, clean installation without loose development assets, performance
under a full match, or play between independent clients. Navigation is generated,
but the exterior build still skips tactical approach/hiding analysis. Exterior
art and the dim/hazy garage remain provisional, as documented in the exterior
guide. The review did not change estimated architectural dimensions or claim
those remaining release gates as passed.
