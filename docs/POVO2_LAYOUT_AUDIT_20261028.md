# Povo 2 layout audit — 28 October 2026

**Implemented:** the active source geometry now has 2 x 13 upper steps, 3 x 10 steps per basement storey, the retained -1 exit, and the shifted -2 vestibule with parking/office/garden branches. See [implementation and validation](POVO2_INTERNAL_STAIRS_IMPLEMENTATION.md). Earlier stair findings below are the pre-correction audit baseline; metric calibration remains open.


**Latest stair clarification:** the user confirms the existing -1 layout/exit should stay. Correct -2's stair exit into a vestibule with right-hand parking and left-hand office/garden circulation, plus the confirmed flight/step counts. This supersedes the earlier opposite-wall interpretation below. The second sketch supplies connectivity; dimensions must come from planimetry, whose metric registration remains unresolved. See the updated internal-stair reference in data/reference/user_feedback/2026-10-28/povo2_internal_stairs.md. No game launch or geometry change was performed for this clarification.

**Later garden update:** the approved straight -1 corridor and south-facing exit,
UP ahead, and eastward level passage aligned with DOWN are generated. The garden
footprint extends beneath the descending flight; its -2 elevation is unchanged.
See [implementation and validation](POVO2_GARDENS_IMPLEMENTATION.md). Statements
below describing the missing branch and old raised yard are the earlier audit
baseline. Fine photo fidelity and metric calibration remain open.

## Verdict

**Internal stair clarification:** the user's walkthrough confirms two flights of 13 steps from 0 to +1 and three flights of 10 for each basement storey, plus differing basement exit positions. The current two-flight, 20-step stack with aligned portals is therefore a confirmed approximation requiring correction. See [the reference and source comparison](../data/reference/user_feedback/2026-10-28/povo2_internal_stairs.md). The received sketch confirms opposite walls for the 0/+1 and basement exits, with different offsets at -1/-2; flight turns are not drawn. Geometry is unchanged.

**Correction after user clarification:** the earlier office/garden floor-assignment finding below conflated two outdoor places. The accessible -1 route comprises two labs, corridors and the exit below the bridge. The -2 garden is a separate lower exterior area, reached by a left descending stair after a short level stretch outside that -1 door. Current code has only a raised generic yard (z=1.3) reached upward from -1 (z=0.4), then stairs upward to street (z=4.0); it does not implement that descending branch or a separate -2 garden. Do not relocate the entire -1 route on the basis of the original audit. The whole-building photographic plans include more spaces than the accessible gameplay subset described by the user.

[Current -1, -2 and exterior connection diagram](../exports/povo2_layout_audit_20261028/current_minus1_minus2_connections.png). Rectangles are current exported area footprints, not a final wall/door drawing. Source geometry only; no runtime traversal claim.

The subsequent user Gardens sketch and clarification establish successive exterior stair junctions: an approximately 2–3 m wide light-blue passage links the upward stairs near the bridge to the downward stairs farther along at the building corner. The latter branch left into Garden -2. These are not two branches from one landing. This is confirmed reference information for a future correction; map geometry has not been changed.

Povo 2 is a partial route reconstruction, not an accurate full-building layout. The gaps are larger than the local service-room errors identified in Povo 1. Several choices were explicitly approved as temporary gameplay adaptations; their presence is not a regression, but they cannot be counted as matches to reality.

Read-only comparison of the active campus generator/configuration and current export provenance with photos 31/33/34/35/37/38/40/43/44/45/46 and the preserved user-sketch review. All four Povo 2 config hashes in export provenance match the current source files. No geometry, build inputs or running game were changed.

## Confirmed discrepancies and omissions

| Area | Evidence in photographs | Active implementation | Required work |
|---|---|---|---|
| Whole-building ground plan | Photo 33 shows rooms around a long central void, transverse circulation, four stair cores and WC/lift groups. | A compact entrance/table hall, seven classroom room records (B111–B114, B106/B108/B109), a temporary aula and one connected stair stack. | Register and reconstruct the missing wings, central void, cross corridors and service/core groups. The seven records are not the entire physical room count. |
| Floor +1 | Photo 31 shows extensive office wings around the centre. | `compact_arrival=true`; connection `rooms=[]`. Configuration explicitly removes the former W2/E2 onward rooms and retains the bridge arrival/alcoves/stairs. | Add the photo-backed office floor and its circulation; preserve the bridge connection while replacing the compact boundary. |
| Floor -1 research/lab plan | Photo 46 shows dense laboratory wings, service partitions, four cores and two user-marked labs. | Only two generic CIBIO offices are registered as basement rooms, with additional decorative closed office doors backed by solid walls. | Integrate the traced research layout and both identified labs; two generic office boxes are not a substitute. |
| Separate lower garden connection (corrected finding) | User confirms a short exterior stretch beyond the -1 below-bridge exit, then a left descending stair to the -2 garden. | `povo2_interiors.py` instead builds a raised yard reached upward from -1; -2 is principally parking. No separate lower garden/descending branch is generated. | Preserve the -1 labs/exit route. Add the exterior level stretch and left descending garden stair, and reconcile the existing raised yard. Exact geometry remains provisional. |
| Parking/office vestibule | Photos 34/35 and user guide establish a small vestibule: right toward parking, left toward offices. | The active -2 metadata has parking/stair stations and no office branch room records; the office branch is generated one storey above. | Trace the vestibule and both branches as a connected layout on the confirmed level, including double-door thresholds. |
| Sunken garden | Photos 44/45 show curved paving around grass, a research facade, retaining walls and an open steel stair. | Rectangular yard and lawn boxes; five estimated indoor steps and a straight fifteen-step exterior flight with tile-material treads. | Rebuild the photographed path/lawn shape, facade relationship and steel stair, and register the exit against the correct plan/core. The straight flight alone is not an error; its geometry, construction and placement remain a schematic substitute. |

Sources in code: `config/povo2_connection.json` (compact scope), `config/povo2_planimetry.json` (lower levels and base rooms), `config/povo2_additions.json` (temporary aula, offices and yard), `tools/povo2_interiors.py` around lines 313–420 (office/garden level and construction), and `tools/povo2_sketch.py` (rigid rotation).

## Important limits and follow-up checks

- The detailed `povo2_survey.json` is retained and hashed by export, but the active campus generation path does not register its full room layout. Having survey drawings in the repository does not mean those rooms exist in the map.
- Survey candidate totals are not verified room totals. Do not use them to claim a percentage of completeness. Floor-0/-2 candidates and several door/service traces remain provisional.
- The east marked lab has a confirmed north corridor entrance and a separate west courtyard exit. Its narrow stepped entrance recess needs tracing before assigning a precise portal; do not replace it with a centred generic door.
- The user-confirmed route after the second black door is LEFT to offices (39/40), RIGHT toward 43, then LEFT toward 41/42 and garden 44/45. The earlier sketch's rigid rotation is not proof that this later photo-specific door sequence is reproduced. Check it after floor/plan registration; this audit does not claim a proven left/right reversal.
- B106/B108/B109 labels and subdivisions are provisional. B111–B114 use repeated estimated room dimensions. The temporary aula was user-authorized; its exact size/footprint is not established by these photographs. Reconcile these with the full plan rather than deleting approved geometry without a replacement.
- Floor names -2/-1/0/+1 and bridge endpoint identity are recorded, but metric heights and XY calibration remain estimates. The active bridge is at 11.2 m; the old standalone draft's 7.6 m upper level must not be mistaken for the current integrated bridge height.

## Evidence and scope

[Selected source photos](../exports/povo2_layout_audit_20261028/reference_contact.jpg), [rectified ground plan 33](../exports/povo2_survey/rectified_33.png), [annotated lab plan 46](../exports/povo2_survey/rectified_46.png), and [previous sketch review](../exports/povo_campus/sketch_corrections_20261027.png).

The sketch image is historical supporting context; findings above were checked against current configuration and export metadata, not inferred solely from that image. This audit does not certify every exterior wall, classroom doorway or compiled collision. The library/canteen panels in the sketch are separate amenities and are not evidence of reconstructed Povo 2 office wings.

Implementation checklist: [Building layout fixes](BUILDING_LAYOUT_FIXES_TODO.md).

## Second pass — generated walls against plans and photos (28 October, evening)

Method: top-down cuts of the generated walls, 1.5 m above each floor, from a source build taken at 17:31, compared with plans 31, 33, 37 and 46 and with the 23, 26 and 27 October photos. A Codex session was editing the internal stair and the -2 exit route at the same time. The -2 vestibule and route were audited separately, from a rebuild at 18:28, after Codex's last change at 17:10. Slices and photo sheets: `exports/povo2_layout_audit_20261028/second_pass_*`. No geometry was changed.

Most of the rest of the ground storey is a single solid `exterior_povo2_context` mass (z 4–11) with the built rooms carved out of it. The known gaps (missing wings, compact +1, missing -1 lab wings) are not repeated here.

### New findings

1. **B111–B114 have the wrong proportions: they should be narrow and deep, not nearly square. Medium-high.** In the room column beside the hall, the rectified plan 33 draws a partition at every column bay. Each bay is about 0.31 of the room depth, and there are nine bays between the Portineria and the far stair core (one split into two rooms). Photo 16 of 26 October (B11x reference) shows a long, narrow room: two long desk rows run toward a window on the far short wall, chairs line the opposite long wall, and the board is on a long side wall. The generator builds four 9 m × 8 m rooms (B111–B114) with 5.6 m desk rows. It does put the board on a side wall and run the rows toward the window, which matches the photo. The rooms should be about a third as wide as they are deep, so the column holds more rooms than four.

2. **The entrance is not inside the frosted-glass cube. Medium-high.** Photos 22 and 24 of 23 October show the main entrance recessed into the base of a two-storey frosted-glass cube, with the cube overhanging the doors. Photo 18 shows a second, similar cube across the paved courtyard. The generator models the cubes as solid glass blocks (`exterior_povo2_front_annex_0` at x 34.7–51, y 38.7–45; `_1` at x 25–34.4, y 78–92). The entrance banks are in the flat main façade beside the first block (y 29.6–37.4), not under it. The aula magna is a plain-walled box (x 34.5–56.5, y 71.5–93.5) standing next to the second block, in the forecourt. **User-confirmed (28 October):** the aula magna is inside the second frosted-glass cube. The generated aula should therefore occupy the cube's volume, with frosted-glass walls, instead of standing beside a solid glass block.

3. **The lift does not reach -2, but the -2 vestibule has a door to the lifts. High.** In photo 35 of 27 October (the -2 vestibule, left door), the black double door carries an "ASCENSORI" (lifts) sign. Plan 37 also draws lift pairs on this floor. The only generated lift shaft (`p2_lift`, x 20.4–23, y 14.3–16.9) runs from z 0.4 (-1) upward. Its ladder starts at -1, so nothing serves -2. Feed this into the -2 vestibule rework that is under way.

4. **Garden -2 has the building on the wrong side, and its lawn is too narrow. Medium-high.** Photos 44 and 45 of 27 October and photos 19 and 20 of 26 October show the sunken garden as a long strip with the Povo 2 façade along one long side. That façade has two storeys of windows, with full-height glazed doors at garden level. The other long side is a retaining wall carrying the open steel stair. The lawn fills most of the width, with a curved edge and paving strips about 1–3 m wide. The generated garden (x 34.5–55.5, y 12.5–20) lies entirely outside the building footprint (x ≤ 34.5). The building touches only its short west end, where the -2 corridor door is. Its lawn is a 2.5 m strip in a 7.5 m-wide yard, and the floor uses the indoor tile material (`floor_p2_tile`). The photos show garden-level glazed doors along the building side; the implementation note's "no unobserved garden-to-lab door" does not hold for this side.

5. **The two -1 labs are too close together. Medium.** On plan 46 the two blue-circled labs sit on the same façade-side corridor, separated by about three lab widths, each next to its own stair core and emergency exit. The generated "CIBIO office" rooms are 8.5 × 8 m with a 5 m gap between them, so the gap is about 0.6 of a lab width. Corridor proportions differ too. On the plan, the run from the stair core to the lab corridor is about 0.4 of the run along the lab corridor to the second lab. In the build the first corridor (32 m) is longer than the second (25 m). Plan registration is still unresolved, so treat these as ratios to check, not distances.

6. **The lecture room "facing Povo 1" looks much deeper than the generated rooms. Low-medium; needs the user.** Photos 6 and 7 of 26 October show a room about twice as long as it is wide, with about ten rows of continuous desks running to a full-height window wall at the far end. The generated B108 and B109 are 7.5 m deep, which leaves room for about six rows. Plan 33's band at that end draws one room spanning the hall and the room column, with its partition at the edge of the void. It has no partition where the build separates B106 from B108 (x 20).

### -2 vestibule and route (rebuilt at 18:28, after Codex's last change at 17:10)

Evidence: [zoomed -2 slice](../exports/povo2_layout_audit_20261028/second_pass_fm2_zoom.png), [photos 38–43](../exports/povo2_layout_audit_20261028/second_pass_route_38_43.jpg), [photo 39 lift detail](../exports/povo2_layout_audit_20261028/second_pass_photo39_lifts.jpg).

**The vestibule itself matches photos 34 and 35.** The stair door is on its long wall (x 17.4–19). Turning right, the parking double door is on the far end wall (x 11), as in photo 34. The left double door (photo 35, "ASCENSORI") is on the near end wall (x 20.5), with the sign-bearing long wall running beside it. The branch directions also match the user's route: right to parking, left then left to offices, left then right then left to the garden.

7. **The blue corridor and the second black door are missing. High.** The user's route runs: vestibule → left door → the long blue corridor (photo 38: glossy blue walls, side doors on the left, black doors ahead) → second black door → junction. In the build, the left door opens straight into a 3.5 m-wide junction corridor (x 20.5–24). No blue corridor separates them, and the build has only one black door, so the junction comes right after the vestibule.

8. **The office branch is a short dead end, and the lifts belong in it. High.** Photos 39 and 40 show the left branch as a long white office corridor, with doors on both sides. Just past the turn, on its right wall, are two lift doors under a lift sign (photo 39 detail). In the build the office branch is a 7 m stub ending at two closed doors (x 24, y 19.5–22.5), with no lifts. This places finding 3's missing -2 lifts: on the office corridor's right wall just after the second black door, not directly behind the "ASCENSORI" door. That sign marks the route to them.

9. **The garden exit door should be glass. Medium.** Photos 41 and 42 show the garden branch ending at an aluminium-framed glass door with a push bar and an exit sign above, with the steel stair visible through it. The build uses opaque black door leaves (`p2_parking_garden_door_*`, x 34.6–35.4). The approach corridor (≈2 m wide, ≈10 m long, after the right-then-left turns of photos 43 and 42) roughly matches the build's 2.1 × 10.5 m.

### Checked and consistent

- Floor 0 runs in the same order as plan 33: hall along the façade, stair core in line with the room column, then the Portineria.
- The stair door faces the hall. The lifts sit on the opposite side of the short corridor left of the reception, as photo 12 of 26 October shows (two lifts in the photo, one shaft in the build).
- There are two inner automatic entrance banks with a pillar between them, as in photo 13 of 23 October.
- Floor +1 is still the known compact bridge arrival.
- Photo 16 of 23 October (hall with lockers and vending machines) is consistent with the generated hall.
