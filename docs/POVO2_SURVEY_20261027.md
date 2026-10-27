# Povo 2 survey — 27 October 2026

## Scope and accuracy

The new photographs establish the full block layout, not just the previously implemented walking route. They do not establish measured dimensions. The existing campus geometry remains a route approximation; this work must not be described as a complete or exact reconstruction.

`config/povo2_survey.json` retains a reviewable manual trace in normalized image coordinates. `tools/povo2_survey.py` validates it, produces four SVG reviews, and exposes `register()` to create metric partitions only after an explicit scale/origin/rotation is supplied. No metric calibration has been silently chosen. Faithful registration refuses unresolved door traces. Centred review portals require explicit `allow_provisional=True`; 79 semibasement portals now use individually traced photo46 segments. The trace has 49 ground-floor, 80 detailed semibasement, 42 lower-floor and 67 directory-numbered first-floor room candidates. These are candidates, not verified room totals: photographed symbols conceal some boundaries; several service areas need subdivision; the current trace does not claim complete doors or partition topology.

## Canonical floor names

Use user floors -2, -1, 0 (entrance), 1 (bridge); Povo1 and Povo2 bridge endpoints share floor 1. Current local elevations -3.2, 0.4, 4.0 and 11.2 metres are provisional. The entrance-to-bridge rise uses two 3.6 m modules (40 risers/four flights), twice either basement storey; intermediate 7.6 m is a turn landing, not an additional Povo2 user floor. They are not measurements.

Photo 1 is assigned -1 by the user and its caption is PIANO SEMINTERRATO. Photo 37 is assigned -2 by the user but its printed caption says PIANO 1° INTERRATO. Retain both assertions as an evidence conflict; do not silently move the user route to -1.

## Image evidence

Source directory: `data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300`.

| Photo | Assignment and directly visible evidence | Remaining uncertainty |
|---|---|---|
| 1 | User -1. Landscape full plan: long central enclosed void, rooms on both long sides, four stair cores, toilet/lift groups, dense research wings on the opposite side of a transverse corridor, several exterior exits. | Printed plan is photographed obliquely. Door swings and several fine service partitions are unreadable. |
| 31 | User floor1, directory includes both buildings. Povo2 is lower diagram. Readable numbers on long wings and lower transverse wing. | Directory omits door symbols and some service-room numbers. Occupant names are not copied into geometry. |
| 33 | User floor0. Caption BLOCCO2 / PIANO TERRA. Portrait orientation with north pointing down. Long central void, western entrance by PORTINERIA, four stair cores, multiple WC groups, long perimeter office/classroom wings and cross wings. | West edge includes a cropped adjacent area. Room IDs mostly absent. |
| 34 | User -2: short tiled white corridor terminating in black double doors; suspended ceiling, dark skirting, illuminated ceiling panel. Right from small vestibule leads toward parking. | Camera position and precise distance need registration. Door plaque text is not reliable enough to label geometry. |
| 35 | User -2: opposite black double door; label ASCENSORE visible. Left from vestibule leads toward other offices. | Do not infer that the entire door is a lift shaft; sign may indicate a route. |
| 36 | Overall ground plan, via Sommarive orientation and block arrangement. | Context only, no trustworthy scale. |
| 37 | User -2, caption conflict retained. AUTORIMESSA to upper left; white corridor structure and lower courtyard/external stair recesses; three principal cores visible. | Several upper large spaces have faint/incomplete boundaries and nonrectangular outlines. Trace candidates do not resolve all of them. |
| 38 | User blue corridor; glossy blue walls, light square tile, suspended ceiling with continuous light panels, side doors on left, black door sequence ahead. | Exact count of black doors/side doors requires viewpoint registration. |
| 39–40 | User after second black door, turn left toward offices. White painted corridor with dark grey door frames, tiled floor, ceiling lights and signs; photo39 left edge contains blue colour at junction. | Longitudinal location of every door is not measured. |
| 41 | Not explicitly mapped by user. White short corridor, glazed exit at end, exterior metal stair visible beyond. | Confirmed by user as garden exit approach, after right branch43 and left turn. |
| 42 | White corridor toward glazed external door; left foreground opening/junction, emergency arrow, damaged plaster low on right, portable equipment. | User resolved route: after second black door right sees43, then left to41/42 and44/45. |
| 43 | White corridor end/left return; same portable unit, extinguisher/sign and wall damage as42. | Confirmed right branch at second-door junction; next left reaches41/42. |
| 44–45 | User garden exit. Sunken landscaped courtyard, curved paved walk, grass island, glazed research facade, tall retaining wall and external steel stairs. | Route ties to particular exit/core not yet registered. Existing model's rectangular yard/straight stair is only an approximation. |
| 46 | User -1 annotated plan. Blue circles identify two existing labs; blue square identifies corridor exit/core. Plan shows many research bays and service partitions absent from the old route layout. | Rotate photo1 by180 degrees to align the central void and four cores with46. Detailed room trace now follows46; blue circles have stable IDs annotated_lab_w and annotated_lab_e; right middle core is recorded explicitly. |

## First-floor transcription

Photo31 Povo2 long outer west wing reads 127–145; inner west reads 110,111,112,113,114,115,116,118,120,121,122,124,125. Inner east reads178,177,176,175,174,173,172,171. Outer east reads184–196. Bottom reads147,148,149,150,151,152,153,154,155,156,157,158,159,170. The trace records those numbers individually; their metric extents and door locations remain unmeasured. No person-name directory content is needed to reconstruct room access.

## Integration boundary

The old implementation has four B11x rooms, two invented generic CIBIO offices and decorative closed doors. Those elements cannot be treated as a full-building plan. `extend_layout()` also contains an authorized temporary aula magna; its shape is not established by these new photographs.

The active source model integrates the entrance, bridge and basement routes through the aligned stair core. It preserves the user sketch’s rigid 90-degree clockwise basement placement and south-facing basement exit. The upper entrance-to-bridge route has four flights/40 risers; each basement connection has two flights/20 risers. Tread support and standing clearance are checked in source geometry, including intermediate turn landings. These route adaptations are not a complete surveyed building.

The photo-plan survey generator is deliberately review-only until a measured registration and the remaining door positions are available. It must not automatically remove the existing connected staircase or insert guessed full-building geometry into the running map. The `register()` API returns ordinary `(name, lower, upper, material)` boxes and a spec with per-room portal uncertainty for a subsequent controlled integration. It does not deploy, compile or modify a game installation.

Outstanding work: obtain a measured span and register all four cores and bridge; trace remaining doors and service partitions; register the two photo46 labs; tie the real courtyard and steel stair to its photographed exit. Photos41–43 route order is resolved below. Floor37 remains assigned user floor-2, with its conflicting printed caption preserved as evidence. No claim of 100% accuracy is justified before those steps.


## Follow-up examination and confirmed route

Rectified originals are saved for photos1,33,46 with full-resolution quadrants and door crops. Rotation180 of photo1 aligns the central void and four stair cores with photo46. Photo46 provides readable door swings:80 individually traced room candidates with79 explicit off-centre opening segments, plus14 emergency-exit stars, four core rectangles, service/WC groups and two user-marked labs. The user confirms exactly one north corridor entrance for the marked east lab and a distinct west exterior courtyard exit (red star `research_exit_11`). The corridor door’s exact along-wall segment is obscured by blue annotation; topology is resolved, metric opening placement remains pending. Some small outer/perimeter rooms and compound sanitary subpartitions remain outstanding;80 is a working trace count, not a claim of completeness.

Photo33 at full resolution is a simplified emergency schematic: many room perimeter lines have no identifiable door swing or gap. It supports room adjacency and shape but cannot establish every door. Earlier regular room candidates on floors0/-2 are explicitly broad layout hypotheses and must not enter a faithful geometry build without individual correction.

User follow-up confirms the -2 route: small vestibule right to parking(photo34), left to other offices(photo35); after the second black door, LEFT goes to39/40, RIGHT sees43 then LEFT goes to41/42 and garden44/45. Photo41 is now confirmed. Povo1 entrance floor-1 and Povo2 entrance floor0 are roughly the same physical elevation, with bridge at user floor1 in both buildings. The campus registration now uses two upper stair modules to satisfy both facts. Absolute metric dimensions remain provisional.

Validation: all four trace levels load with positive bounded room rectangles and unique room IDs. Registered review boxes were checked for positive volumes/unique names under all four quarter-turn rotations. Default registration rejects unresolved doors; traced segments are used directly, with explicit review-only opt-in required for remaining provisional openings. This survey review does not compile or deploy game assets.
