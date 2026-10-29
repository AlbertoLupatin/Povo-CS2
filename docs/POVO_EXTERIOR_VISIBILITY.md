# Exterior pavement correction — 29 October 2026

**Later -1 update:** the corrected Povo 2 layout now has a newer local package.
Its courtyard and street pavement controls still pass; see
[current layout and package](POVO2_MINUS1_CORRECTIONS_20261029.md).
The full nine-view record and package identity below describe the pavement repair
before the later -1 geometry correction.

Status: **verified in the standard native package**. The courtyard surface and
street curb no longer appear as black holes under normal lighting. All nine
matched pavement pixel checks, 12 exterior walking routes and 24 Povo 2
basement/stair routes pass on this package. CS2 is closed after the test batch.

## Correction

`tools/povo_pavement_lighting.py` copies the existing exterior paving/asphalt
tops and exposed curb faces into `povo1_campus_paving.vmdl`. UVs, normals and
triangle winding are retained. A 3 mm offset along the surface normal prevents
coplanar flicker. Building surfaces and pavement undersides are excluded.
This finishing model is lightprobed and non-solid; it does not cast duplicate
shadows. Materials remain normally lit. This is not a fullbright/unlit-material
workaround.

The structural campus model retains every original position, UV and face;
all eight collision OBJ hashes remain identical. Compiled Povo 2 checks find
zero missing samples among 4,181 floor points on -1, 10,290 on -2, and 72 column
surface points. All seven contact materials pass. Basement screenshots show
continuous floors/ceilings and columns reaching the ceiling. These checks
preserve the accepted accessible layout; they do not certify full survey fidelity.

The exporter, map generator, asset deployment, native model compilation and
packaging all include the finishing model. Regression checks verify the
offset geometry, preserved UVs and exclusion of buildings and undersides.

## Native package and evidence

`build/package/trento_povo_campus.vpk`: **45,393,237 bytes**,
**1,082 entries**, all CRCs verified. SHA-256:
`c916c179db8a9ea84adef59c428af6b801f1beca6ea89c98291ef77c3b64aa7f`.

The package's structural and finishing models match the compiled native files
byte for byte. The latest map bake compiled 777 resources with zero failures
in 461.587 seconds. The final curb update recompiles the external, render-only
probe-lit model and repackages it with that completed map; collision and the
placed prop are unchanged. Fresh engine captures and walks test the repackaged
bytes. Final quality is 0 with a 2048-pixel atlas. Default quality remains 1.

Reproduce with `build_campus.cmd --fast-lighting --lighting-quality 0`.
The explicit quality reaches Valve's compiler and is recorded by the checked
build wrapper. The 265-test source suite passes, followed by ten targeted
build/pavement checks after the final changes.

Evidence directory: `exports/povo_campus/runtime/exterior_visibility_20261029/`:

- [Normal-lighting screenshots](../exports/povo_campus/runtime/exterior_visibility_20261029/gallery.md).
- `final-visibility-audit.json`: nine matching views pass. The reported courtyard
  and curb samples have zero nearly black pixels; other sampled ground regions
  remain below 0.023%.
- `final-walking/`: 12 ordinary exterior walking routes, both directions.
- `final-basement-walking/`: 24 ordinary Povo 2 routes, both directions.
- `final-compiled-floors.json`, `final-compiled-surfaces.json`: native geometry/material checks.
- `source-geometry-unchanged.json`: structural geometry and collision comparison.
- `final-package-check.json`, `completion.json`: package identity and consolidated results.

The runner uses an isolated addon, one human, zero bots, normal lighting and
ordinary movement with noclip disabled. It closes CS2 in `finally`, including
a process-specific fallback. Winter and Workshop were not updated.

## Investigation history

Fullbright diagnosis confirmed that the initially invisible surface was rendered
geometry with black baked lighting. A stronger quality-1 / 2048 bake fixed a
frontage seam but retained the courtyard patch. Disabling SSAO, directional
lightmaps and live sun shadows did not repair it.

Joining the hard-normal apron strips into a continuous lighting surface fixed
the small control scene, but failed in the campus map. A quality-1 / 2048 bake
stalled on GPU tile 3/4; a 4096 atlas had stalled earlier. Both were stopped.
The faster full-map bake confirmed that smoothing alone was insufficient.
The documented double-sided lightmap option also failed in the full map.

The probe-lit tops removed the courtyard patch; adding exposed vertical curb
faces removed the last black street band. Rejected captures are retained in
`smooth-preview-failed/`, `double-sided-failed/` and `probe-tops-curb-failed/`.
The successful captures are in `final/`. Earlier packages and logs remain
diagnostic history, not the current result.
