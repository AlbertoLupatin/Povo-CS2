# Povo 1 layout audit — 28 October 2026

Verdict: the main classroom arrangement is broadly consistent with the photos, but the building is not yet a faithful room-by-room reconstruction. This is a source/export review while the native build runs; no map geometry, build inputs or running game were changed.

Compared the current campus provenance and generator with photographed plans 10/17/19/22, the existing upper-plan overlay, interior photos 9/23/26/28 from 27 October, and coffee photos 2/4/5 from 28 October. The four Povo 1 configuration hashes match the current export provenance. The older `adjustments_layout_review.png` is stale: it has 33 floor-0 rooms and the old southern toilets, whereas current provenance has 34 rooms including the coffee room.

## Findings

1. **Floor 0, north inner service block: wrong room functions and partitions. High confidence.** Photo 19 shows WC beside A217 and an `AULA STUDIO PC` immediately below it in the photographed orientation. Current `f_north_west` is a generic Locale over the WC, while `f_north_centre_male` occupies the study area. The adjacent female WC also extends beyond the photographed WC region. These are actual configured room footprints, not simply missing labels. Re-trace this whole block, including the small circulation spaces, before furnishing it. Source: `config/povo1_campus.json`, north additions starting at line 259. See the new overlay below.

2. **Floor -1: photographed toilet blocks remain generic offices. High confidence.** Plans 10 and 17 show WC/service blocks flanking A107 and A108. Current entrance-floor metadata contains no restroom rooms: `g_north_west`, `g_north_east`, `g_south_west`, and `g_south_east` are all `Locale`/office placeholders. Their internal toilet partitions and the adjacent lift/vestibule arrangements have not been faithfully traced. Source: `config/povo1_campus.json`, additions starting at line 24.

3. **Lift arrangement does not follow the photographed cores. High confidence for the geometric mismatch; exact replacement needs tracing.** Plan 19 shows paired lift symbols near the two inner end blocks; the current overlay assigns those areas to generic Locale rooms. The implemented shaft beside reception continues vertically through the corner of A214, explicitly acknowledged in the configuration, while the photographed A214 footprint has no such shaft. The ladder is an intentional gameplay substitute, but the shaft location itself is a layout discrepancy. Preserve the user's reception reference when reconciling all floors; do not simply move the shaft from one plan image alone. Sources: `config/povo1_campus.json` elevator entry and `tools/build_povo_campus.py:elevator_shaft`.

4. **Door locations remain approximate, even where room outlines agree. Confirmed implementation limitation.** `derived_config` moves classroom door centres to fraction 0.85 when no window-side override exists, to clear the furniture. This means the existing source-plan overlays are not sufficient proof of the final generated door positions. Audit final openings against visible door swings, especially the larger classrooms with multiple photographed openings. Source: `tools/build_povo_campus.py`, lines 92–94. This is a follow-up fidelity check, not a claim that every shifted doorway is wrong.

## What agrees at the level reviewed

- Floor identities: entrance -1/A1xx, intermediate 0/A2xx, upper +1/offices and bridge.
- Main A2xx classroom order and approximate relative footprints; A201–A203 remain together on the correct floor.
- The four stair-core locations and ring circulation broadly agree with the photographed plans. Exact stair dimensions remain estimated.
- The Acquario is now one long glazed study room with flanking photocopy areas, consistent with photos 9/17, rather than four invented classrooms.
- The latest southern floor-0 layout places the coffee area behind the courtyard emergency stair between service/WC areas. Its six machine/dispenser objects, two tables and window-side bins follow the 28 October photos in broad arrangement. Exact entrance width and pillar registration still need a close geometry comparison.
- The upper office rows broadly follow the plan-22 trace. Upper terraces, door access and fine corridor details are not certified by this review; no photo-derived dimensional accuracy is claimed.

## Review images

[Current floor-0 room footprints over photo 19](../exports/povo1_layout_audit_20261028/floor0_current_rooms.jpg). Blue outlines come from the current exported room metadata, including campus additions. The overlay uses the existing approximate outer-bound registration, not a perspective-rectified survey; it establishes major adjacency/function mismatches, not centimetre errors. It does not draw final wall cuts, lift geometry or door openings.

[Selected original-photo contact sheet](../exports/povo1_layout_audit_20261028/reference_contact.jpg).

Suggested correction order: floor-0 north service/study block, entrance-floor WC blocks, lift/core alignment across floors, then final doorway placement. No compile or gameplay validation was performed or required for this documentation-only review.

## Second pass — wall slices against plans 10, 17, 19 and 22 (28 October, afternoon)

Method: top-down cuts of the generated walls 1.5 m above each floor, taken from the current source build (`build_geometry`) and placed beside the photographed plans, rotated to the same orientation. Room widths are compared as proportions of the photographed span and converted using the generated span. No metric registration is claimed. Sheets: [floor -1 vs plan 17](../exports/povo1_layout_audit_20261028/floor-1_vs_plan17.jpg), [floor 0 vs plan 19](../exports/povo1_layout_audit_20261028/floor0_vs_plan19.jpg), [floor +1 vs plan 22](../exports/povo1_layout_audit_20261028/floor+1_vs_plan22.jpg). Script: `exports/povo1_layout_audit_20261028/wall_slices.py`. The build ran with the uncommitted Povo 2 stair work present, which does not touch Povo 1 geometry. No map geometry was changed.

### New findings

5. **Floor -1 entrance hall is split into three offices that the plans and photos do not show. High confidence.** Between the two entrance-side stair cores, `g_outer_east1..3` ("Studio E5–E7") are closed 8 × 8 m offices against the façade (local x 15.7–24, y -69.7 to -45.7). Plan 17 shows this span as an open hall with a row of columns and two glazed entrance vestibules, one beside each stair core, with double doors and exit signs. The façade is set back between the vestibules. Plan 10's simplified outline shows the same open hall with two rectangles on the façade. Photo 37 of the 23 October walk, taken just inside the main entrance, shows a long open hall with columns, seating along the glazing, and the reception counters on the inner side. The site plan (27 October photo 21) also shows Povo 1's façade toward the library and canteen recessed in its middle. The generator instead has one entrance bank (y -75.5 to -71.9) in a flush façade. Remove the offices and open the hall. Check the second vestibule and the façade recess against exterior photos.

6. **The floor -1 office and infirmary block beside A102 is missing. The space is an empty walled box with no exit. High confidence.** Plan 17 shows nine rooms at the entrance-side end of the A101/A102 column, on both sides of an internal corridor that runs from the main corridor to an exterior exit door. One side has Centro Stella, an unlabelled room, Audio-multimediale and Ufficio. The other has Deposito, Locale pulizie, Locale infermeria (with a first-aid cross), Ufficio responsabile di sede and Ufficio personale di manutenzione. Plan 10 shows the same cluster of small rooms. The generated geometry at local x 8.2–24, y -34 to -20 has only the outer walls and A102's wall: no partitions and no rooms in the metadata. The outer walls at y=-20 and x=24 are continuous, so the plan's exit door is missing. Whether the box can even be reached from the corridor was not checked.

7. **The floor -1 reception row has the wrong partitions. High confidence on the room count; the reception position needs the user.** Plan 17 divides the inner entrance-side row (between the two lift cores, 31.7 m) into three rooms: Segreteria studenti (≈9.5 m), Ufficio (≈6 m) and Informazioni/Controllo (≈11.8 m). The generator has four equal 7.9 m rooms: RECEPTION, ASCENSORE (the ladder shaft), Locale and Locale. Plan 10 marks the Portineria at the main-entrance end, which agrees with the generated reception position, and photo 37 shows counters there. Neither plan has a lift in this row. Both put the paired lifts in the corner cores at each end of it. This is direct evidence for finding 3.

8. **Floor -1 inner top row: plan 17 labels the "Fotocopiatrici" spaces differently. Low severity.** Plan 17 labels the two rooms either side of the Aula studio *Spazi per associazioni* (student association spaces). The config's identity note says "Flanking photocopy space visible in entrance plan17". Widths match: ≈4.2 m each, with the Aula studio at ≈23.3 m. Keep the copier label only if a photo shows copiers there. Plan 17 also draws a door at each end of the Aula studio, while the generator gives it one (`door_fraction` 0.1).

9. **Floor 0 outer classroom rows: A210/A211 and A222/A223 are generated as equal rooms. High confidence.** Plan 19 puts the A211|A210 and A223|A222 partitions off the column grid. As shares of the span between the stair-core walls, it shows A212 24.5 %, A211 18.4 %, A210 32.3 % and A209 24.7 %. The opposite row mirrors this: A221 24 %, A222 32.6 %, A223 18.3 %, A224 25 %. The generator makes all eight rooms 7.83 m. On the generated span, A211 and A223 should be ≈5.8 m and A210 and A222 ≈10.1 m. The inner rows (A213–A220) are equal on both the plan and the build.

### Existing findings, now with more evidence

- **Finding 2 (floor -1 service blocks).** Plan 17 resolves all four inner corners. The two corners away from the courtyard hold a *WC donne* and a cavedio. The two entrance-side corners hold a *WC uomini* with an accessible *WC H*, then the paired lift and a cavedio. The generator makes all four `Locale` offices.
- **Finding 1 (floor 0 north service block).** On plan 19, *Aula studio PC* is followed by two more unlabelled rooms, then the second WC (four basins), then the lift lobby. On floor 0 the lift pairs sit on the corridor side of each lobby, with a small vestibule toward the courtyard.
- **Finding 3 (lifts).** Plans 17, 19 and 22 agree: a paired lift and a cavedio in the two entrance-side inner corners, stacked on all three floors. On floor +1 both corners (local x 8–12.6) are generated as open corridor. The ladder shaft does more than cut into A214. It rises through the middle of the east terrace on floor +1 (x 10.2–12.45, y -69.3 to -67.0), cuts a hole in the terrace floor and opens into the corridor through the terrace glazing. Plan 22 shows unbroken terrace at that point.

### Checked and consistent

- Floor 0 side columns (A204–A208, laboratory, A201–A203) match plan 19's proportions to within about 1 %.
- Floor 0's south-west service block (WC, Locale, coffee area, WC, lift lobby) matches plan 19 to within about 0.2 m per room.
- On floor +1, the office rows (12 strips on the west, two rows of 8 on the long sides), the five laboratories and the courtyard terraces match plan 22.

Some floor +1 labels differ but are not geometry errors; they come from directories rather than this plan. Plan 22 calls the two rooms beside each inner WC *Aula studio*, where the build has `252 laboratory` and `Garda 241`. It also labels the boxes along the corridor spine *Deposito* and *Archivio*, each with a small shaft, where the build has whole-box service shafts. Treat these as label checks.

## Door pass — generated door gaps against emergency-plan door swings (28 October, evening)

Sources with door swings: plan 17 (floor -1), photo 20 of 27 October (the floor 0 emergency plan; plan 19 shows no swings) and plan 22 (floor +1). Each was rotated to the build's orientation and overlaid with the generated walls, using a linear fit to the building outline (perspective error ≈1 m at the edges). Gaps were measured directly from the wall boxes of a source build at 18:28. Evidence: `exports/povo1_layout_audit_20261028/doors_*.png`; overlay helper `door_overlay_scratch.py` (expects the rotated plans and cached geometry from the audit scratchpad). No geometry was changed.

10. **Classrooms on floors -1 and 0 have a second door that the build leaves out. High.** On plans 17 and 20, every classroom checked has two corridor doors, one near each end. On floor 0 they come in pairs, one on each side of every partition column. The generator gives each room a single 1.2 m door at `door_fraction` 0.85. That door matches the plan's door at the same end to within about 0.5–1.5 m. The other one, near the opposite end, is missing.
   - Rooms affected on floor -1: A101–A108 and the Acquario. On plan 17, A101 and A102 have double-leaf doors.
   - Rooms affected on floor 0: A201–A224 and the LAB. A223's second door is unclear on the photo.
   - This answers finding 4: the 0.85 shift did not misplace the door it kept. Nothing needs moving; the near-end door needs adding. In play, this doubles the entries into every classroom.
   - Photo 20 also independently confirms finding 9. Its outer rows measure about 25 / 19 / 32 / 24 %.

11. **On floor +1, plan 22 draws a band of small rooms between the five laboratories (255–259) and the corridor. Medium.** These are shallow rooms or cupboards, about 1.5 m deep, with the lab doors in the gaps between them. The build runs each lab straight to the corridor wall, which makes the corridor about 4 m wide instead of about 2.4 m. The lab door positions themselves match within about 1 m.

12. **Plan 22 draws double doors from the corridor onto both terraces. Resolved.** The user confirms the doors exist; the earlier choice to omit them predated the plan. They are now built from plan 22: on the west terrace at y −75.6 to −74.0 and −47.0 to −45.4, against the terrace ends, and on the east terrace at y −72.1 to −70.5 and −50.8 to −49.2. The overlay check puts all four glazing gaps on the plan's door arcs.

**Doors that match:** the floor +1 offices (243–250, 210–217, 223–236) and labs fall within about 1 m of the plan 22 swings. The `door_fraction` 0.21–0.25 offices sit about 0.5 m to one side of the arcs, and the west offices about 1 m. The courtyard stair's -1 doorway in A107's glazing matches the 28 October user-confirmed layout (landings stacked outside A107), and photo 5 shows a glazed door behind the stair base.
