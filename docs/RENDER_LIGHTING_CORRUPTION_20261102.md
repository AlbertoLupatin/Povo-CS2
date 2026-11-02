# Normal-lighting corruption — 2 November 2026

The 31 October package `e221ccbecc828c0e6a46900a57e2f6abdcf15a0a8b3a087d01a9ffbff555db5f`
passed source, collision and CRC checks but rendered black/turquoise streaks in
CS2. It was incorrectly described as ready without a native visual review.

## Diagnosis and repair

The defect was reproduced in a fresh solo game. Temporarily disabling baked
lighting removed the streaks while leaving correct geometry and base textures.
The saved `irradiance.exr` and chart atlas also contain the streaks. That bake
had used the script-only 1024-to-256 block recovery from
`build/lighting-recovery/20261031T223219Z/`.

Script-only retiling is now rejected: retaining atlas dimensions and sampling
counts does not establish that the generated binary packing inputs remain
consistent. `recover_povo_lighting.py` fails before touching any process.
Regression tests cover both guards. An unrelated stale survey assertion now
compares the straight-C7 route after its existing collinear-point simplification.

An untouched 2048-atlas retry completed its first block but then stopped
advancing. The successful repair recompiles the existing map through Valve's
resourcecompiler with `-lightmapVRadQuality 1 -lightmapMaxResolution 1024`.
The script, packing data and atlas are generated together. There are no manual
block edits, unlit materials or fullbright settings in the repaired package.
The smaller atlas reduces baked-lighting detail relative to 2048; normal
lighting, shadows and denoising remain enabled. Both shared campus model hashes
are identical to the previous package, preserving the accepted layout/collision.

## Completed verification

- All **363 source tests pass**.
- Native compile: **914 compiled, zero failures**, exit code 0.
- Package: **61,958,853 bytes**, **1,237 entries**, all CRCs and staged bytes checked.
- SHA-256: `6a52dc98ddf5050f430894597337ec86361557d95adf9f1798771a8e1f74c9ee`.
- Nine native camera captures were individually inspected with
  **`mat_fullbright = 0`**: entrance, C7, C5, WI1, terrace, UP stair, DOWN stair,
  lower approach and campus overview. The reported streaks are absent.
- The promoted package also passes 80 compiled entrance checks, 22,997 basement
  floor samples, 72 column samples and 36 fixed-door surface samples.

The exact visually reviewed candidate was copied to
`build/package/trento_povo_campus.vpk`; its copied hash was verified. The game
review used a separate `trento_povo_render_review` addon. These camera captures
use noclip placement and do not certify a new ordinary-movement walkthrough.
Other unfinished exterior modelling remains separate from this rendering repair.

Evidence: [normal-lit entrance](../exports/render_corruption_20261102/normal-lighting/entrance.png),
[capture manifest](../exports/render_corruption_20261102/normal-lighting/captures.json),
[validation summary](../exports/render_corruption_20261102/validation-summary.json),
`build/render-corruption-20261102/native-rebake-1024.log` and
`build/render-corruption-20261102/source-tests-final.log`.
The corrupt input package is preserved as
`build/render-corruption-20261102/corrupt-input.vpk`.

Close CS2 and rerun `play_campus.cmd` to load the repaired standard package.
Winter and Workshop packages have not been updated.
