# Building layout fixes

**Implemented:** the active source geometry now has 2 x 13 upper steps, 3 x 10 steps per basement storey, the retained -1 exit, and the shifted -2 vestibule with parking/office/garden branches. See [implementation and validation](POVO2_INTERNAL_STAIRS_IMPLEMENTATION.md). Earlier stair findings below are the pre-correction audit baseline; metric calibration remains open.


Photo audit: 28 October 2026. These items record outstanding work; they are not implemented fixes. Keep source/photo fidelity separate from gameplay clearance checks.

## Povo 1

- [ ] **Rebuild floor 0's north inner service block from photo 19.** Restore the WC beside A217, currently `f_north_west`/Locale. Restore Aula Studio PC where `f_north_centre_male` currently places toilets. Correct the neighbouring female WC extent and intervening circulation. Trace partitions and openings together, rather than changing labels alone.
- [ ] **Replace entrance-floor placeholder offices with the photographed WC/service blocks.** Use plans 10/17 around A107/A108 to correct `g_north_west`, `g_north_east`, `g_south_west` and `g_south_east`. Include toilet partitions, vestibules and adjoining core spaces.
- [ ] **Reconcile lift/core positions across all three floors.** Trace the paired lift symbols near the inner end blocks; remove the unsupported shaft intrusion into A214. Reconcile the user's reception-side lift reference before moving geometry. Keep the intentional ladder gameplay substitute separate from the physical placement decision.
- [ ] **Add the second classroom door on floors -1 and 0.** Plans 17 and 20 (the floor 0 emergency plan) show two corridor doors per classroom, one near each end. The build's single 0.85 door matches one of them; add the near-end door to A101–A108, the Acquario, A201–A224 and the LAB. A101/A102 use double-leaf doors. Evidence: second-pass door section of the Povo 1 audit.
- [ ] **Add the floor +1 small-room band between the labs and the corridor** (plan 22, ≈1.5 m deep; corridor ≈2.4 m, not 4 m).
- [x] **Floor +1 terrace doors.** The user confirms the plan 22 double doors exist. They are now built: two per terrace, west at both terrace ends and east further in (`tools/povo1_courtyard_stair.py`, `TERRACE_DOORS`). Exports are not yet regenerated.
- [ ] **Audit final classroom openings against photographed door swings.** Done for plan swings on all three floors (see the door pass); photo checks remain. Review the generator's automatic `door_fraction = 0.85` adjustment; preserve real doorway positions and move furnishings where necessary. Check multiple entrances in larger rooms, not only one generated door per room.
- [ ] **Verify coffee-room entrance and pillar geometry.** Broad placement and furniture agree with 28 October photos 2–5, but entrance width, open passage shape and pillar position remain approximate.
- [ ] **Verify upper terrace access and fine corridor geometry.** Compare photos 22–30 and current geometry; resolve access details before treating the terraces as fully verified. Do not infer absent doors from a single photograph.
- [ ] **Open the floor -1 entrance hall.** Remove `g_outer_east1..3` (Studio E5–E7). Plans 17/10 and 23 October photo 37 show an open hall with columns and seating along the glazing, and two entrance vestibules beside the stair cores. Check the second vestibule and the façade recess against exterior photos before building them.
- [ ] **Build the floor -1 office/infirmary block beside A102.** Plan 17: nine rooms on an internal corridor ending in an exterior exit door (Centro Stella, Audio-multimediale, Ufficio, Deposito, Locale pulizie, Locale infermeria, Ufficio responsabile di sede, Ufficio personale di manutenzione, plus one unlabelled room). It is currently an empty walled box with no exit.
- [ ] **Re-partition the floor -1 reception row.** Plan 17 shows three rooms (Segreteria studenti ≈9.5 m, Ufficio ≈6 m, Informazioni/Controllo ≈11.8 m), not four equal rooms with a lift shaft. Settle the lift question (see the lift/core item above) before choosing which end holds the reception.
- [ ] **Move the floor 0 A210/A211 and A222/A223 partitions.** Plan 19: A211 and A223 are ≈5.8 m and A210 and A222 ≈10.1 m. The build makes all eight outer rooms 7.83 m.
- [ ] **Check the floor -1 "Fotocopiatrici" labels.** Plan 17 calls these rooms *Spazi per associazioni*. Also add the Aula studio's second door.
- [ ] **Regenerate review drawings after corrections.** Replace the stale `adjustments_layout_review.png`; show final room partitions, lift shafts and door cuts, not only source rectangles.
- [ ] **Validate corrected geometry.** Check route continuity, stairs, doorway clearance and collisions, then inspect a newly compiled build. Passing traversal checks alone does not demonstrate photo fidelity.

Second-pass detail for the existing service-block and lift items: plan 17 puts WC donne + cavedio in the two inner corners away from the entrance, and WC uomini + WC H + paired lift + cavedio in the two entrance-side corners. The same lift corners stack on floors 0 and +1. On +1 the ladder shaft also stands in the middle of the east terrace.

Evidence: [Povo 1 audit](POVO1_LAYOUT_AUDIT_20261028.md) (including the second pass and its generated-versus-plan sheets) and [current floor-0 overlay](../exports/povo1_layout_audit_20261028/floor0_current_rooms.jpg). Metric dimensions and elevations remain provisional; no centimetre-level match has been established.

## Library and canteen

- [ ] **Replace the street-side glazing on both ground floors with solid walls.** Plan 13 (*piano primo sottostrada*) and plan 15 draw that long side as a solid wall below street level, with a row of cells on the library side. The build glazes it from z 4.0 to 7.35 directly under the street-level sidewalk. Check in game what shows through the glass.
- [ ] **Close off the canteen's kitchen half.** Plan 13 encloses the kitchen, changing rooms, bar store and WCs along the street side. The build leaves most of it as open dining floor.
- [ ] **Re-trace canteen local 1 the right way round.** Plan 12's exits, lifts and stair belong on the street side. Today the three exits open onto a 3.6 m drop on the Povo 1 side, and the only street door is an automatic bank the plan doesn't show. Anchor the refit on the real stair (the traced core is ≈4 m off along the building and doesn't enclose it) and on the lifts.
- [ ] **Add the lifts.** Plan 13 has two lift shafts by the canteen stair, and both buildings' lifts should reach local 1.
- [ ] **Enclose the library end stair on both floors.** Plan 15 draws an enclosed stair core with doors. The flights currently stand open in the reading room.
- [ ] **Give library local 1 its directory-16 rooms.** It has the group-study rooms and stair/lift enclosures; today the floor has no walls at all.
- [ ] **Locate the photo 11 terrace and the library's main entrance with the user.** The terrace overlaps the sidewalk on the street side, and plan 15 shows no door where the entrance bank stands.

Evidence: [library and canteen audit](AMENITIES_LAYOUT_AUDIT_20261028.md).

## Povo 2

**29 October -1 correction supersedes the earlier “retain -1 layout” scope:**
the user's markup is implemented and verified in the standard native package.
The inter-lab gap is provisionally 30 m; only its right/east corridor half is
retained. The lower corridor joins the outdoor exit, and two permanently closed
static doors isolate the upper/right L. The stair core and -2 stay in place.
All 12 selected -1 walking routes and eight fixed-door walk/Use attempts pass.
See [latest geometry and native results](POVO2_MINUS1_CORRECTIONS_20261029.md).

- [x] **Rebuild -1 from the 29 October corrections and seal the L.** Includes the
  longer/narrower lab corridor, lower connection, two unopenable doors, corrected
  radar, readable outdoor-stair review, and native validation.

**Latest stair clarification:** the user confirms the existing -1 layout/exit should stay. Correct -2's stair exit into a vestibule with right-hand parking and left-hand office/garden circulation, plus the confirmed flight/step counts. This supersedes the earlier opposite-wall interpretation below. The second sketch supplies connectivity; dimensions must come from planimetry, whose metric registration remains unresolved. See the updated internal-stair reference in data/reference/user_feedback/2026-10-28/povo2_internal_stairs.md. No game launch or geometry change was performed for this clarification.


**Garden implementation update (28 October):** the approved straight indoor
corridor, UP directly ahead of the exit, and a level passage aligned with DOWN
are generated. Garden -2 extends beneath the fixed descending stairs, at its
unchanged elevation. The garden-related checklist
items below retain the remaining metric/photo fidelity work; their descriptions
of the old raised yard are the audit baseline, not the latest source. See
[implementation and validation](POVO2_GARDENS_IMPLEMENTATION.md).

- [x] **Correct the reception-side internal stair and -2 vestibule.** Implemented confirmed flight counts, retained -1 exit, shifted -2 door, parking branch and office/garden corridor. See [implementation and source checks](POVO2_INTERNAL_STAIRS_IMPLEMENTATION.md). Dimensions/elevations still require metric calibration.

The active model is a partial route reconstruction. Several compact/temporary choices were previously user-approved; the tasks below record remaining fidelity work rather than claiming those choices are new regressions.

- [ ] **Register the full photographed building before extending it.** Align plans 33/46/37 and directory 31 to a common footprint, the bridge and all visible stair/lift cores. Establish a reliable scale reference; keep provisional measurements explicit. Survey JSON being hashed in provenance does not mean its geometry is integrated.
- [ ] **Restore the missing floor-0 wings and circulation.** Build the central void, surrounding room bands, transverse corridors and WC/lift groups shown in photo 33. The current seven classroom records plus hall/aula do not represent the full floor.
- [ ] **Build the missing +1 office floor.** Replace the compact arrival-only scope with the office wings and corridors visible in directory 31. Preserve the bridge route and resolve doors from additional plan evidence where the directory has none.
- [ ] **Build floor -1's laboratory/research layout.** Integrate the individually traced room boundaries and doors from photo 46. Replace generic CIBIO offices and decorative closed doors where the plan establishes actual rooms; finish unresolved sanitary/service partitions rather than assuming candidate rectangles are complete.
- [ ] **Register both blue-circled labs.** Preserve their identified room identities. Refine the east lab's stepped north entrance recess and separate west courtyard exit; do not invent a second corridor entrance or use a centred default portal.
- [ ] **Separate the below-bridge exit (-1) from the lower garden (-2).** User clarification: the accessible -1 portion is two labs, connecting corridors and the below-bridge exit. Preserve that route on -1. The earlier audit conflated the model's generic yard with the photographed lower garden; do NOT move the whole -1 route to -2.
- [ ] **Add the missing exterior branch to the -2 garden.** After the -1 exit door below the bridge, provide a short level outdoor stretch (user estimates a couple of metres) before the existing upward stairs. On the left when walking out, add stairs descending to the exterior garden at -2. Exact run, width, turn shape and lower landing are not yet measured; the connection is user-confirmed even if absent from photos.
- [ ] **Use the user's Gardens sketch to separate all three outdoor spaces.** Reference: `data/reference/user_feedback/2026-10-28/Povo2 Gardens.drawio`. From the road toward the building, the sketch distinguishes street-level garden, Garden -2, and the ground-floor left-entrance courtyard. Preserve their distinct elevations and boundaries. User confirms successive stair junctions linked by the light-blue passage, approximately 2–3 m wide: upward stairs nearer the bridge, then continue toward the corner to the left-hand stairs down into Garden -2. Do not combine both stairs onto one landing. Passage length and stair dimensions remain provisional.
- [ ] **Replace the current yard interpretation with distinct exterior levels.** Current generated geometry rises five steps from -1 z=0.4 to a yard at z=1.3, then fifteen steps to street z=4.0. It has no lower garden or descending branch. Reconcile this five-step threshold with the confirmed level exit stretch; register the lower garden independently rather than relabelling the existing raised yard.
- [ ] **Rebuild the -2 vestibule and both branches.** Match photos 34/35: right toward parking, left toward offices. Connect the office branch on the confirmed floor rather than leaving it one storey above.
- [ ] **Verify the complete black-door/junction sequence.** After the second black door: left to photos 39/40; right toward 43, then left toward 41/42 and garden 44/45. Check final doorway positions and route turns after registration; rotation of the earlier sketch is not sufficient evidence.
- [ ] **Reconstruct the sunken garden and external stair.** Match curved paving, lawn outline, retaining walls, glazed research facade and open steel stair from photos 44/45. Replace the schematic rectangular yard/lawn and tiled stair representation; verify the exit/core and exterior heights.
- [ ] **Reconcile provisional classroom and aula geometry.** Verify B106/B108/B109 identities/subdivisions and repeated B111–B114 dimensions against the full plan. Replace the temporary aula only with an evidence-backed layout, preserving approved access during integration.
- [ ] **Make B111–B114 narrow and deep.** Plan 33 has a partition every column bay (each bay ≈0.31 of room depth). The 26 October photo 16 shows a long room with desk rows running to the end window. The build has four near-square 9 × 8 m rooms.
- [ ] **Put the entrance inside the frosted-glass cube.** The 23 October photos 22/24 show the entrance recessed into the cube's base. In the build it sits in the flat façade beside a solid glass block. The user confirms the aula magna is inside the second cube: rebuild the aula in that cube's volume, replacing both the plain-walled box in the forecourt and the solid glass block.
- [ ] **Extend the lift to -2.** The -2 vestibule's left door is signed ASCENSORI (27 October photo 35), and plan 37 draws lifts there. Photo 39 places two lift doors on the right wall of the office corridor, just past the second black door. The shaft currently starts at -1.
- [ ] **Add the -2 blue corridor and second black door.** Photo 38 shows the long blue corridor between the vestibule's left door and the junction. The build goes straight from the vestibule into the junction with one door.
- [ ] **Extend the -2 office branch into a corridor.** Photos 39/40 show a long office corridor with doors on both sides and the lifts on its right. The build has a 7 m stub ending at two closed doors.
- [ ] **Make the -2 garden exit a glass door.** Photos 41/42 show an aluminium-framed glass door with a push bar; the build uses black leaves.
- [ ] **Turn Garden -2 to run along the building.** In the photos the Povo 2 façade, with garden-level glazed doors, runs along the garden's long side. The lawn fills most of the width and the floor is outdoor paving. The build puts the building only at the garden's short end, with a 2.5 m lawn strip and indoor tile.
- [ ] **Space the -1 labs as on plan 46.** On the plan they are about three lab widths apart, each by its own stair core and exit. In the build the gap is 5 m.
- [ ] **Resolve remaining doors and metric calibration.** Do not deploy unresolved survey door defaults as faithful geometry. Keep user floor names and current bridge identity consistent; distinguish the standalone draft's old upper height from the active 11.2 m bridge.
- [ ] **Produce final four-floor comparison drawings and validate.** Show actual generated walls, doors, cores and routes against the corresponding photos. Run geometry/clearance checks after changes, then inspect the newly compiled map. Do not report route-test success as proof of a faithful full building.

Evidence: [Povo 2 audit](POVO2_LAYOUT_AUDIT_20261028.md) and [photo contact sheet](../exports/povo2_layout_audit_20261028/reference_contact.jpg).

### Restricted wings: proposed fidelity scope

The user cannot access most Povo 2 laboratory/office wings. Prioritize the accessible two labs, public routes, stair cores, exits and garden. Use existing plans for the inaccessible wings' footprints and visible corridor-facing walls/doors; keep unverified interiors closed and unfurnished rather than inventing them. Full playable lab/office interiors above remain optional expansion work, not a requirement for completing the accessible-area reconstruction. This is a proposed scope, not a claim that inaccessible interiors have been verified.
