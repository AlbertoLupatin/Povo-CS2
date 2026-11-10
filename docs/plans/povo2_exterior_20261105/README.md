# CURRENT STATUS — implemented final registration, 6 November 2026

The final exported Povo 2 assembly now aligns the floors at the common yellow facade **N10.8**. The latest review is [final_implemented_layout.pdf](final_implemented_layout.pdf), with [floor previews](final_implemented_floors.png) and [exterior preview](final_implemented_exterior.png). It supersedes every pending registration question, the earlier 4.6 m room-depth fit, and all older drawings in this directory. Historical notes and artifacts below remain as a record of earlier checkpoints; they are not current implementation instructions.

B106/B108/B109 fill the space behind the yellow facade, N10.8–24.2: **13.4 m fitted depth**, followed by the 2.6 m perpendicular room corridor N24.2–26.8. The internal assembly is registered +8.8 m north, including reception, the rectangular entrance lobby, basement interiors, doors, furnishings, routes and the stairwell. The actual stairwell is E11–20.5 / N26.8–34.8. Entrance remains opposite reception; the stairwell is on its left when entering, with the short corridor beside it leading to the perpendicular room corridor. Stair directions are retained; no Povo 2 lift is enabled. The exterior bridge span is retained; an internal connector reaches the translated arrival. The three speculative −2 parking bays outside the common frontage are removed, retaining the aisle and vestibule.

The −2 garden approach meets the garden at **W−31.8 / N15** (approximately W−30 / N15 as requested). The user-approved [single L drawing](single_l_garden_corridor.png) defines the route: continue the existing W−21 corridor straight to N15, then turn once toward the door. Its exit opens eastward directly through the garden’s west boundary. The former exit farther east is closed; the garden footprint and exterior DOWN stair are retained.

The −1 external corridor continues straight into DOWN at the **start** of the rectangular −2 garden. The lower landing lies approximately halfway along the garden, against its road-side retaining wall. The 5 m grass strip lies outside the grate and slopes from pavement toward the terrace; UP interrupts it. The bush spans 5 × 5 m, starting 5 m beyond UP's right edge when viewed from the road. The road is registered 4.69 m north relative to the earlier local layout, retaining 6 m carriageway and 1.4 m pavement widths. Terrace width is 1.71 m; garden footprint remains 17.5 × 11.25 m. These are fitted model dimensions guided by confirmed relationships, **not surveyed measurements**.

The drawing reads `build_registered_geometry()` from `tools/build_povo_campus.py`, the same final registration stage used by export. Historical `build_geometry()` returns the local construction frame and must not be used to depict this final layout. Reproduce from repository root:

```sh
python docs/plans/povo2_exterior_20261105/draw_final_implemented_layout.py
# Optional explicit assembly snapshot:
python docs/plans/povo2_exterior_20261105/draw_final_implemented_layout.py --cache build/layout_review/final_frontage.pkl
```

The two-page review shows all four modelled floor levels with identical axes/orientation/scale, then the exterior connection and a road-to-facade section. Walls and stair treads use actual assembled geometry; coloured areas identify model metadata, not inferred real-world rooms. Native CS2 compilation and in-game traversal have not been performed. Before the garden-exit correction, the full unittest suite passed **424 tests (1 skipped)**. The approved single-L implementation passed **13 focused frontage tests** and a fresh registered-geometry audit with **3,555 route samples (including parking routes) and no failures**, including mesh-aware garden clearance. Native door extraction also confirms both new leaves are exported and the old exit is absent. Reproduce those checks with `python -m unittest discover -s tests -p test_povo2_frontage_registration.py` and `python -m tools.audit_povo2_frontage`. These checks use source geometry; native CS2 compilation and in-game traversal remain pending. Validation results from historical checkpoints below apply only to their named assemblies.

---

## HISTORICAL CHECKPOINTS — superseded by CURRENT STATUS above

# Approved Povo 2 exterior arrangement — 5 November 2026

The user approved `approved_plan.png` and requested implementation. This revises the exterior portions of the earlier definitive -1 layout; interiors, partitions, doors and the main core must be preserved. The diagram is schematic, not a metric survey. Its narrow road is a drawing convention: retain the current 6 m carriageway and 1.4 m pavement widths.

## Approved relationships

From road toward Povo 2: pavement, grass sloping down toward the building, metal grate/fence, -1 outdoor terrace/corridor, yellow windowed facade. The facade is the building limit; remove the incorrectly protruding enclosure beneath the bridge without changing interior rooms. Keep the bridge overhead.

The exit stair interrupts the roadside grass. Looking from the road toward Povo 2, a bush starts approximately 5 m to its right and runs approximately 5 m. It fills the approximately 5 m grass-strip width.

Keep the -2 garden rectangular. Move the exterior descending stair closer to the yellow facade, attaching it to the retaining wall immediately below the road. Its start is approximately halfway along the garden; its footprint lies in the final approximately 1 m wall-side strip. Landings, guards and route metadata must move consistently. Do not change interior circulation to accommodate exterior geometry.

## Registration investigation — previous gap calculation is not a blocker

The current bridge road has centreline N=-5, carriageway width 6 m and footway width 1.4 m (`config/povo_exterior.json`). Its building-side pavement edge is therefore N=-0.6. The existing -1 terrace is N=0.29..2.0 (`tools/povo2_drawio_entrance.py`), leaving only 0.89 m between them. Inserting a 5 m grass strip on this alignment needs approximately 4.11 m more separation. This measurement uses the existing protruding layout and does not establish that the road must move. The user correctly requested removal/repositioning of the protruding rooms before calculating the available exterior space. Do not use the 0.89 m gap to authorize a road displacement.

The current DOWN stair is E31.8..42.3, N0.29..2.0, whereas the retained -2 garden is E38..55.5, N8.75..20. These are not registered to the same wall. Its relocation requires reconstructing its exterior approach rather than translating stair treads alone.

The old roadside closure fills flat lawns, caps roofs and adds the fence at the pavement edge. That implementation is superseded in design, but has not yet been replaced: changing only fence position would leave the terrace and lower garden incorrectly connected.

No map geometry has been changed in this revision. Resolve the global registration before implementation. `registration_comparison.png` shows current source coordinates and a hypothetical grass footprint; it is not a proposed road relocation.

## Evidence

- User confirmations in this task, including final approval and request to implement.
- `docs/POVO2_ROADSIDE_CLOSURE_20261105.md` and its source renders (not native CS2 screenshots).
- `docs/POVO2_MINUS1_TERRACE_20261029.md`: earlier unresolved garden/stair registration.
- `data/reference/povo_photos/walk_2026-10-27/.../image00044.jpeg`: lower garden and road-side retaining wall stair.
- `data/reference/povo_photos/walk_2026-10-23/originals/IMG_2365.JPEG`: road, pavements and bridge.

Native compilation and in-game checks require Windows CS2 Workshop Tools. No build or tests are claimed for this documentation-only checkpoint.

## Follow-up: protruding ground-floor rooms

`config/povo2_additions.json` places B106, B108 and B109 at N0.5..8, across E2..31, with their connecting corridor at N8..11. The bridge arrival in `config/povo2_connection.json` starts at N10. These are concrete candidates for the unwanted under-bridge extension. Relative to that N10 arrival plane, the room fronts project 9.5 m south. Confirm the yellow facade plane from assembled geometry and photos before relocating rooms; their destination must not overlap the retained stair/lift or existing rooms. The previous scaled comparison shows existing coordinates only, not the corrected exterior envelope. No road relocation is justified by it.

## Reset after rejected combined redesign

The user rejected the combined interior/exterior redesign. Its image and notes have been deleted. It must not be used as a layout reference. No map geometry was changed by that proposal.

The current source interior is the baseline, with these mandatory relationships:

- Entrance directly in front of reception.
- Stair room to the left of reception when entering.
- Short corridor to the left, extending the length of the stair room.
- Perpendicular corridor begins after the stair room and runs parallel to B106/B108/B109; the stair room forms its corner.
- Preserve all existing stair orientations, including the external stair descending to Garden -2. Do not reverse, rotate or replace their runs from a schematic.
- Correct the external projection/registration while preserving these connected interior relationships. Moving an isolated room row is not an accepted solution.
- The confirmed entrance-only upper-left projection should be removed; preserve the entrance/reception relationship and both door lines.

Restart from assembled source geometry. Any next drawing must show the existing walls, doors, corridors and stair runs directly, with proposed changes overlaid in the same coordinate frame. Do not use an invented schematic interior as a substitute. The earlier approved exterior drawing records broad exterior relationships only; it must not override the source stair orientations or these later corrections.

## AUTHORITATIVE CORRECTION — corridor/stair/garden connection

The user's latest clarification supersedes every earlier statement that the stair starts halfway along the garden:

- The -1 external corridor ends directly at the upper stair landing.
- That upper landing is exactly where the -2 garden footprint starts.
- The stair descends along the garden's road-side retaining wall.
- The LOWER landing at -2 is about halfway along the garden length.
- The corridor and stair are straight and aligned, without any dogleg.
- The stair connects corridor -1 to garden -2, not to the road above.

Earlier revised_garden_plan images and revised_garden_proposal coordinates reversed the start/midpoint relationship and must not be used. The previous provisional tread/run dimensions derived from that wrong relationship are withdrawn. The new connection diagram is schematic and establishes topology only; global registration and metric dimensions must follow this constraint. Interior layout and internal stair directions remain unchanged.

## Internal layout companion

`internal_building_layout.pdf` adds six pages to the accepted exterior connection:

1. Entrance/reception/stair/classroom corridor detail.
2. Full modelled floor 0, including B111–B114 and Aula Magna.
3. Existing floor −1 interior and external corridor exit.
4. Existing floor −2 interior access and lower exterior exit.
5. Modelled +1 bridge arrival.
6. The accepted straight corridor/stair/garden connection schematic.

The first five pages derive from assembled source geometry and configuration, with north to the right and west upwards (entering from the bottom). Room fills and the highlighted stair-room envelope aid identification; this is not a construction drawing. These pages document the interior baseline to preserve, not relocated B106/B108/B109 or a verified final alignment with the yellow facade. The accepted exterior diagram establishes the connection topology but not surveyed coordinates. Blank areas do not establish that a floor is empty in real life.

The outer and inner entrance door lines are labelled by their position along the lobby. The existing lobby bounds are rectangular; removal of any adjacent entrance-only projection still requires identifying its generating geometry. No building geometry has been edited.

Reproduction: `draw_internal_plan.py`, run from repository root, uses the existing assembled diagnostic cache `build/layout_review/current.pkl` (the five-value return of `build_geometry()`). Preview PNGs accompany the PDF. No build or game validation is claimed for this drawing-only update.

### Stairwell shading correction

The internal companion now shades `stairs.well_bounds` (E11–20.5, N18–26), not the broader `stairs.bounds` (E11–20.5, N14–26). The latter includes a 4 m corridor/vestibule strip outside the actual well. The previous purple overlay obscured this distinction on −1 and −2. Walls render above the shading. This corrects the drawing only; no circulation or stair geometry moves.

## Implementation checkpoint — 5 November 2026

Implemented in the assembled map source:

- Removed stale Povo 2 lift metadata from active drawings and export views. The geometry already removed the substitute ladder/lift; both metadata representations now record it disabled. Povo 1's lift is unaffected.
- The entrance-only glass envelope follows the rectangular lobby's north/south edges. Both door lines, reception and main interior stay in place.
- The garden now starts at the retained −1 external corridor end. The upper landing is inside its footprint; DOWN continues straight east to the garden midpoint, retaining a middle landing and 20 risers. Garden dimensions remain the previous provisional 17.5 × 11.25 m.
- Rebuilt exterior retaining walls, lower interior exit connection, garden ground, guards and collision. Filled the obsolete excavation and removed old stair/landing/approach geometry. Updated garden navigation and spawn support to follow the moved ground.
- Internal rooms, corridors, stairs, floor footprints and the UP stair to the street are unchanged. `implementation_checks.json` records the baseline comparison.

`implemented_garden.pdf` / `.png` show the implemented connection. `draw_implemented_garden.py` regenerates it directly from `build_geometry()` (or an explicitly provided review-cache path). The internal PDF now omits the disabled lift and uses the implementation cache, `build/layout_review/implemented.pkl`.

**Still pending — not implemented:** B106/B108/B109 relocation to the yellow facade and the dependent ~5 m roadside grass strip, building-side grate and bush. The accepted interior PDF explicitly left this registration unresolved. At the geographic yellow-facade line, the current core leaves about 7 m, while room depth plus corridor uses 10.5 m. Translating the row alone overlaps the preserved core. Requested the yellow-facade-to-stairwell distance before changing the interior or road spacing. No road relocation/narrowing or invented interior redesign is included.

The garden connection is anchored to the existing corridor, not claimed as a surveyed final building registration. Native CS2 compilation and in-game validation have not been performed.

Validation: 40 focused tests and 32 regression tests pass. Final basement route sampling: 5,232 points in both directions, zero failures. Exterior support/headroom audit: 1,098 samples, zero failures. The initial full-suite run exposed stale exterior route/spawn metadata and an obsolete infill expectation; these were corrected and all failing cases passed in the rechecks. The full suite was not rerun after those corrections. Native compilation and in-game traversal remain untested.

## Ground-floor room registration implemented

Following the user's clarification that the facade-to-stairwell space must contain the room row and its corridor, B106/B108/B109 now occupy N10.8–15.4, with the perpendicular corridor N15.4–18. The short approach joins it at N18. Room order and east/west spans are retained. The 4.6 m room depth and 2.6 m corridor are fitted model dimensions, not a measured survey. Furniture is regenerated to fit; obsolete side-bay walls no longer cross the new corridor. Reception, stairwell, stair directions, basement interiors and the accepted garden connection are preserved. `ground_registration_checks.json` records comparisons against the previous assembly.

The internal PDF and previews now show this implementation (`registered.pkl` review cache). The old measurement diagram records the earlier question and is not the current room plan.

**Remaining cross-floor conflict:** the −1 office frontage is at N2 in the current model, while the yellow ground-floor facade is at N10.8. With the road-side pavement edge N−0.6, a 5 m grass strip would occupy N−0.6–4.4 and enter the existing −1 offices; the adjoining terrace would also overlap them. `floor_alignment_conflict.png` illustrates this. Asked whether the real −1 fronts align below the yellow facade or project toward the road. Do not move the road, resize basement interiors, or place landscaping through rooms without resolving that identification.

Ground-registration validation: 46 relevant tests passed, covering room-door traversal in both directions, core integration, basement access, garden routes and spawns. No native CS2 compilation or in-game check was performed.
