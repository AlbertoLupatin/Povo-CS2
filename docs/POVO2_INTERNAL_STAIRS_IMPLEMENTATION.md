# Povo 2 internal stair correction — 28 October 2026

**Later corridor correction:** the 29 October user markup supersedes the older
instruction to retain the entire -1 layout. The stair core and its interface
are retained; the longer/narrower lab corridor, lower exit connection and two
fixed shut doors are now built and verified. See
[latest -1 correction](POVO2_MINUS1_CORRECTIONS_20261029.md). The source-only
validation statements below describe this earlier stair implementation stage.

**Route review correction implemented:** parking now continues forward/up in the exit-facing view. Beyond the left vestibule door there is a solid wall ahead and a T-junction: left to other offices; right and then left to the garden door. The earlier straight-corridor diagram is superseded by the [corrected route drawing](../exports/povo2_layout_audit_20261028/minus2_exit_route_corrected.png).

The active campus assembly now replaces the former stair modules after the existing garden and basement placement passes. `tools/povo2_internal_stairs.py` implements the user's confirmed counts and latest vestibule sketch:

- Ground to +1: two flights, thirteen steps each.
- Ground to -1: three flights, ten steps each.
- -1 to -2: three flights, ten steps each.
- The accepted -1 door, open leaves, approach and corridor placement remain in place.
- -2 exits on the same south-facing wall as -1, shifted west into a separate vestibule. Right leads through a double-door threshold toward parking; left passes another threshold to a T-junction facing a wall. The left branch leads to other offices; the right branch requires another left turn to the garden exit through its retaining wall. Office facade doors are closed; unobserved interiors are not reconstructed.

The old stair treads, obsolete doorway and physical railing clips are removed. New turn landings, guards, floor openings, thresholds and open door leaves form the replacement stack. Exterior garden rails are retained. Stair metadata and the existing survey harness now describe the new flights rather than the old two-module upper path.

## Plan-proportion fit update

The accepted route topology is now dimensioned from a manual trace of the stair/vestibule group in photo 37, with photographs 34/35 and 43 used as visual cross-checks. [Annotated evidence and campus fit](../exports/povo2_layout_audit_20261028/dimensional_fit.png), [numeric fit report](../exports/povo2_layout_audit_20261028/dimensional_fit.json), and `config/povo2_internal_dimensions.json` preserve the trace, assumptions and implementation values.

The photo-plan core is approximately 242 x 304 crop pixels. Mapping it to the existing enclosed well (8 x 9.5 m; the accepted -1 approach lies outside that well) gives axis scales differing by about 5.6%, consistent with a rough photographic registration rather than a measured plan. The vestibule is about 110 pixels deep and spans the full 304-pixel core side: conditional on the retained core scale this is about 3.64 x 9.5 m. Its implemented dimensions are now 3.6 x 9.5 m. The cross-corridor band is about 111 pixels / 3.47 m, supporting the retained 3.5 m junction corridor. The narrower 2 m garden branch remains an estimate consistent with the interior photo, not a surveyed width.

The door interval is approximately 54 pixels: the same conditional scale predicts 1.69 m, close to the retained 1.65 m opening. Its centre is about 76% along the wall from the parking end. The -2 door moves from east coordinate 16.5 to 18.2 m, toward the left/office end in the exit-facing drawing. It is about 2.3 m from that end; -1's door and layout remain fixed.

The model's former parking placement was too far east/south relative to the local plan group. The existing 36 x 32 m parking lobe is now rigidly registered at [-25,-12.5,11,19.5], close to the roughly 37 x 28 m lobe inferred from the same plan scale. Rigid placement preserves car, bay and column dimensions. The vacated overlap in the independently generated exterior garage has its floor, roof and perimeter restored, so relocation does not leave holes behind. The stair and vestibule fit within the aerial Povo 2 east-wing envelope. The parking lobe stays 7.5 m clear of the main Povo 1 northern edge and within the larger garage's east-west band, while extending beneath part of the bridge-side area.

These are conditional estimates. The available photographic survey has no independently measured metric scale. Aerial roofs do not establish underground boundaries, and the existing larger exterior garage starts 10.5 m beyond this lobe's north edge; their connection still requires whole-basement registration. This local fit is not a claim that the complete basement, exterior ramp or every building core has been reconstructed. No connecting tunnel is invented to hide that gap.

The existing ground and bridge elevations (4.0 and 11.2 m) are retained. This gives 0.277 m upper risers and 0.3 m treads, considerably steeper than the former placeholder. Basement risers are 0.12 m. Confirmed step counts are implemented, but real riser heights and bridge elevation still need metric calibration. Changing the campus-wide bridge elevation was not part of this local correction.

## Validation and artifacts

The integrated standing-envelope audit passes for all 12 parking-level, 18 basement and 50 ground stations. Every sampled stair tread/landing has support and headroom (272 samples). Separate dense routes check the -2 exit, parking branch, garden branch and office branch (260 samples, no support/headroom failures). A regression check verifies the facing wall blocks straight-on travel. The existing parking wing is reflected about the vestibule centreline, including floor, walls, cars and audit stations, so its actual access follows the corrected direction. Regression tests cover the counts, retained -1 portal, shifted -2 portal, bridge arrival outside the replaced core, lower-floor connectivity and missing-support/low-headroom detection.

Source model/collision assets are regenerated by `python -m tools.build_povo_campus`. [Layout preview](../exports/povo2_layout_audit_20261028/internal_stairs_implemented.png), [clearance report](../exports/povo_campus/povo2_integrated_clearance.json), [test log](../exports/povo2_layout_audit_20261028/stair_tests.log).

No game launch, engine walking, CS2 compilation, VPK packaging or deployment was performed. Source checks do not certify engine movement or measurement accuracy.
