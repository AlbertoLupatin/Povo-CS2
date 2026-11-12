# Altitude corrections: Povo 1 terrace, parking and campus road

Last updated: 11 November 2026. Status: analysis and implementation plan. Campus floor levels (Povo 1, bridge, Povo 2) adopted in section 5b, together with the streets around Povo 2; other corrections not implemented.

Analysis only. No geometry, interior floor, compiled package or approved Povo 2 layout was changed. This replaces the narrower preliminary interpretation from this chat, not an approved layout record.

## Scope and source checks

The user confirms a Povo 1 −1 exterior terrace facing the west surface parking, approximately 3 m above it, separated by a grass bank similar to the Povo 2 roadside bank. They also identify the dependency on the road descending beneath the bridge.

The full `build_registered_geometry()` assembly was regenerated: 34,977 boxes and 2,610 exterior meshes. Selected road positions were checked against both render and collision meshes. This is a source-model audit; the environment has no `build/package` package and no native CS2 playtest was performed.

Checked evidence:

- PAT 0.5 m DTM `5h666051035_DTM.asc`, SHA-256 `63deffb68da8cf2c48db13e2aed30e1694cd453b3a51fc2edc4d1e7d869f4a63`.
- Matching DBM `5h666051035_DBM.asc`, SHA-256 `950f0ca857e2118b771b968ca3575bb8194615a1784b4811486947f4da6d270c`. Grid dimensions, origins and spacing match the DTM. These are LiDAR-derived rasters, not raw LAS/LAZ scans or surveyed interior floors. No raw LAS/LAZ/E57/PLY files were found under `data/`.
- Municipal August 2024 orthophoto, 0.5 m resampled extract, checksum verified against its JSON provenance.
- Cached OSM routes supplied through Overture. Their projected coordinates agree with the aerial image at the scale relevant to the distinct road branches; they are not survey-grade kerb positions.
- Original October 2026 photographs, particularly `IMG_2367.JPEG` (raised terrace, retaining/guard edges and ramp area) and `IMG_2369.JPEG` (parking, grass bank and elevated terrace).

Use EPSG:25832, source orthometric heights with ITALGEO 2005, and the existing model origin E666250, N5103800, Z370. No vertical datum conversion was made. Source resolution is not positional or vertical accuracy. Licensing and chronology remain as recorded in [source register](docs/DATA_SOURCES.md).

## 1. What the final source currently builds

| Feature | Model local Z / extent |
| --- | --- |
| Povo 1 −1 finished floor | 4.00 m (374.00 in the geographic frame) |
| Povo 1 0 and +1 | 7.60 / 11.20 m |
| Surface parking | Flat at 3.00 m |
| Western grass apron | Flat at 2.84 m |
| Western context concrete | Generally 2.75 m |
| Parking footprint | E−60.8..−35; N−98..−43 |
| Bridge walking slab / underside | 11.20 / 10.98 m |

At E−28/N−65, where the terrace-side upper strip should be, there is low grass at Z2.84 over context concrete. At E−37/N−65, inside the measured bank, the model has parking asphalt at Z3.00. Thus the missing terrace/bank is a geometry issue, not merely an impression produced by the camera.

The active road is not described completely by `config/povo_exterior.json`. `povo2_frontage_registration._road_and_landscape()` replaces its eastern/central segments and moves the straight centreline from N−5 to N−0.81. Final analysis must use that assembly. Its main stations are E50/Z7.6, E32/Z4, E22/Z4, E−23/Z3, E−36/N−12/Z3, followed by the older flat parking approach.

## 2. Terrace / bank / parking sections

For each northing, terrain was sampled in a 2 m north–south strip. Upper-strip medians use E−30..−26; parking medians use E−54..−44. All sampled points are outside the main building footprint. DBM minus DTM is zero at the checked upper-strip centres, consistent with uncovered exterior ground. This does not turn the DTM into a measured paving or indoor-floor survey.

| Local north | Upper-strip median | Parking median | Difference | Approx. bank run | Fitted bank angle |
| --- | ---: | ---: | ---: | ---: | ---: |
| −50 | 373.25 m | 370.33 m | 2.92 m | 8.0 m | 17° |
| −65 | 373.30 m | 369.74 m | 3.56 m | 8.5 m | 21° |
| −80 | 373.29 m | 369.19 m | 4.10 m | 7.0 m | 28° |
| −95 | 373.29 m | 368.61 m | 4.68 m | 7.5 m | 28° |

The user's approximately 3 m description is well supported near the entrance. It should not be enforced as a constant drop along the whole parking lot: the parking falls about 1.72 m over these 45 m, approximately 3.8%, while the upper strip remains almost level.

Bank widths and angles come from a least-squares three-segment fit (parking / bank / upper strip), with fitted slope breaks on a 0.5 m grid. This places the toe around E−40.5..−41.5 and crest around E−32.5..−34. Fit residual RMS is 0.07–0.09 m; this measures model fit, not survey accuracy. The entire plateau-to-parking difference is not the bank face's rise: the shoulder and crossfall contribute too. This corrects the earlier rough angle estimate obtained by dividing the whole drop by an assumed 8 m run.

Moving the sampling windows by ±1 m in X and Y gives drop ranges 2.82–2.96, 3.38–3.63, 4.04–4.17 and 4.52–4.74 m. These are sensitivity checks, not confidence intervals; source vertical error and temporal changes are additional unknowns.

The model's asphalt reaches roughly 5.5–6.5 m into the inferred bank beyond its toe. The terrain plateau and photos support the raised terrace, but do not justify paving the entire crest-to-facade strip. Exact hardscape edge, doors, northern return, guard dimensions and drain details still need tracing. The northern ramp/retaining arrangement must be treated separately from the main straight bank.

## 3. The western road has a horizontal error as well as a height error

The aerial and OSM distinguish:

1. Public Via dei Valóni, `w1499989163`: runs beneath the bridge and continues downhill southwest.
2. Parking access, `w275318481`: branches near local E−52.54/N−16.15 and heads south into the parking.
3. A separate ramp/access system, `w741997306`, `w741997307`, `w741997308`, between that access and Povo 1.

The model bends from E−36/N−12 toward E−47/N−27. This cuts through the separate access/ramp area instead of preserving the public-road/parking-access junction. It explains the deep DTM trough in the preliminary model-centreline profile. That trough is not a required dip in the public road. The first correction must be the route layout; sampling a misregistered route gives misleading grade targets.

OSM route information and the aerial establish the branch separation. Precise ramp deck levels at covered mouths remain uncertain: DTM interpolation at retaining walls and covered transitions cannot be copied blindly.

## 4. Road grade on the correctly identified public route

These DTM values use local 3×3-cell medians, sampled on the mapped public road. The model comparison uses corresponding east stations on its own registered alignment, so the differing XY alignment is explicit.

| Local east | Mapped-road DTM local Z | Current model road Z |
| --- | ---: | ---: |
| +50 | 7.46 m | 7.60 m |
| +32 | 6.02 m | 4.00 m |
| +22 | 5.32 m | 4.00 m |
| −23 | 2.95 m | 3.00 m |
| −36 | 2.01 m | 3.00 m |
| −52.54 (parking-access junction) | 0.80 m | No corresponding correctly placed junction |

The model's E50→32 segment drops 20%; the terrain endpoints imply approximately 8%. The model's E32→22 is flat; terrain endpoints imply approximately 7%. E22→−23 is about 2.2% in the model versus approximately 5.3% between terrain stations. These are segment-average grades, not a final smooth road design.

The DTM sample beneath the bridge is partly interpolated ground: DBM at E18 contains the bridge surface. Adjacent uncovered road samples at E10, E22 and E26 support the broader grade trend, but bridge clearance must use the reconstructed road and actual soffit geometry, not DBM roof minus DTM as a literal clearance measurement.

For scale, the model road at E18/N−0.81 has matching render/collision support at Z3.9136; its slab underside is Z10.98. Raising the road toward the nearby measured Z5.1 would reduce slab clearance from about 7.1 to about 5.8 m. This is indicative, not a full obstruction/beam/vehicle clearance certificate.

## 5. Povo 2 bank comparison

The regenerated Povo 2 grass bank is not uniformly 31°. Its western E8.5..20.5 run drops 3 m over 5 m and is approximately 31°. The eastern run tapers with the later widened pavement; some current mesh sections exceed 50° and the steepest reach approximately 72°. This is directly computed from top-edge coordinates, not inferred from historical prose. Therefore copying its whole current mesh would reproduce unrelated geometry distortions.

The user's comparison is appropriate for the visual form: an upper hard surface, planted sloping earth, lower terrace/parking, edge protection. Povo 1's source-supported width and varying slope should determine its geometry independently. Povo 2's approved floor plan, rooms, terrace connections and stair directions remain the preservation baseline.

## 5b. Povo 2 floor levels from the internal stair, photographs and DTM (11 November)

Added after the analysis above. Povo 2 has three independent anchors that agree, and Povo 1 then turns out to share the same levels. This section therefore adopts new levels for both buildings and the bridge.

**Evidence**

- **Internal stair step counts** (user-counted, recorded 28 October in `data/reference/user_feedback/2026-10-28/povo2_internal_stairs.md`): 1→0 has 13+13 risers; 0→−1 and −1→−2 each have 3 × 10.
- **iPhone LiDAR measurement** on a −1↔−2 step (11 November): riser 16 cm, going 30 cm (31 cm to the nosing). An earlier 23 cm reading, taken from below on the stair side, was discarded. A single step on one flight; the other flights were not measured. Recorded in `config/povo_circulation.json` → `povo2_stair_flights`.
- **−2 gardens (DTM):** both are open, flat ground, with DBM − DTM ≈ 0.
  - South garden (E30..50, N11..18): median −1.56 m, P10–P90 −1.63..−1.35, 168 cells.
  - North garden (E30..50, N103..110): median −1.53 m, P10–P90 −1.64..−1.37.
  - Photos 27 Oct #42/#44 show the garden door level with the −2 corridor, with no steps.
- **East street at the main entrance (DTM):** E55..57, N36..48, uncovered. Median 8.29 m, P10–P90 8.08..8.55.
  - Photo 26 Oct #22 looks out through the outer door. The pavement continues flush with the lobby floor, with no steps.
  - DTM values west of E55 lie under the canopy or building. They are a linear interpolation toward the courtyards, not ground, so the apparent 6.9 m "facade edge" is an artefact.
- **Bridge roof (DBM):** flat at 15.66–15.73 m between N−18 and N8, so the bridge deck is level.

**Result** (implemented in `tools/povo2_levels.py`; see [Povo 2 levels](docs/POVO2_LEVELS_20261111.md))

| Level | Previous model | Adopted | Basis |
| --- | ---: | ---: | --- |
| Povo 2 −2 (parking, vestibule, gardens) | −3.20 | **−1.55** | Garden DTM; flush garden door |
| Povo 2 −1 | 0.40 | **3.25** | −2 plus 30 × 0.16 m (measured flight) |
| Povo 2 0 | 4.00 | **8.05** | −1 plus 30 × 0.16 m; street DTM 8.08–8.29 with a flush entrance |
| Povo 2 +1 / bridge | 11.20 | **12.21** | 0 plus 26 × 0.16 m; bridge DBM roof 15.66–15.73 = deck + 3.35 m bridge walls |
| Povo 1 / library / canteen −1 | 4.00 | **3.25** | Entrance-plaza ground DTM 3.15–3.32 (E27–33, N−80/−65, open cells) |
| Povo 1 / library / canteen 0 | 7.60 | **8.05** | Via Sommarive front DTM 8.00–8.09 at E52–54 for N−100..−15, where floor 0 meets the street |
| Povo 1 +1 | 11.20 | **12.21** | Same deck as the bridge and Povo 2 +1 |

- **Agreement:** the basement storeys, at 16 cm, land Povo 2's floor 0 within 0.05–0.25 m of the independently measured street.
- **Update, 11 November:** the 0↔+1 question is resolved by two independent checks:
  - The bridge's DBM roof matches a 12.21 deck plus the model's 3.35 m bridge walls.
  - Povo 1 lines up on the same three levels. Its entrance ground matches −1 and its Via Sommarive front matches 0, each within 0.1 m.
- **Result:** both buildings share −1 3.25, 0 8.05 and +1 12.21. Povo 1's storeys become 4.8 m and 4.16 m.
- **Povo 1 stairs:** their measured step counts were not available. They keep their modelled counts, with risers scaled uniformly per storey (×1.33, then ×1.16).
- **Exterior consequences, implemented in [Povo 2 levels](docs/POVO2_LEVELS_20261111.md):**
  - Via Sommarive, the roundabout, the north pavement and the south road between Povo 1 and Povo 2 are regraded to the DTM (`tools/povo2_exterior_grade.py`).
  - The Povo 2 UP stair now climbs to the regraded south footway (5.43).
  - The gardens and garage ramp follow −2.
- **Still open for this plan:** the west parking, the Povo 1 terrace bank and the road-branch layout (sections 2–4) are not regraded.

## 6. Why no global vertical shift is established

The model Povo 1 floor is around 0.7 m above the outdoor upper-strip DTM. This is a local comparison between a provisional indoor floor and outdoor ground, not evidence of a global datum mismatch. At E50 the road differs by only +0.14 m, at E32 by −2.02 m, and at the parking N−50 by +2.67 m. A uniform shift cannot reconcile these.

DTM does not determine finished indoor elevations, slab thresholds or all covered stair landings. The previous recommendation to choose between a blanket offset and moving every floor was premature. Keep source elevations, model constraints and unresolved thresholds separate. First reconstruct the exterior profile and identify connection conflicts; then resolve those locally with plan/photo evidence.

## 7. Coordinated correction scope

1. Register the public road, parking access and separate ramp footprints against aerial/OSM evidence; preserve the user-measured bridge cross-section where applicable.
2. Fit a continuous road profile using uncovered DTM samples, rejecting covered-edge and retaining-wall interpolation artefacts.
3. Reconstruct the terrace hardscape at the confirmed −1 relationship, its guard/retaining edges and northern return; avoid inventing exterior door locations.
4. Reserve the grass-bank footprint and trim parking asphalt out of it. Build a graded lot, not one constant-Z slab. Treat the western lot edge/residential interface and the south termination as part of the fit.
5. Remove/reshape the old Z2.75 context slab and Z2.84 grass in the lowered area. Otherwise lowering asphalt alone buries it under the old ground.
6. Re-seat bays, cars, gates, fences, lamp posts, light entities and navigation on the new surfaces. Several fixtures currently have hardcoded Z3 bases.
7. Reconnect Povo 1 paving and Povo 2 road-side stair landings, grass and garage approach. Povo 2 UP currently climbs Z0.4→4 over a 5 m run with 20 risers; a new road level cannot be applied without checking that connection. Keep approved interior topology; record any later explicitly required stair-layout revision.
8. Validate final registered render/collision agreement, joins, road/lot support, bank overlaps, exterior doors and bridge clearance, then compile and walk the affected routes in CS2. Historical tests and pre-registration route audits do not establish correctness of the new profile.

The evidence is sufficient to establish that the existing exterior needs coordinated rebuilding. It is not sufficient to claim surveyed interior floor levels, an exact full terrace perimeter or a ready-to-compile corrected design. The full analysis and reproducible measurement scripts are retained in `work/povo1-full-analysis/` for this session.

## 8. Evidence confidence and unresolved decisions

| Finding / decision | Status | What would strengthen or resolve it |
| --- | --- | --- |
| Raised terrace at Povo 1 −1 facing surface parking | User-confirmed; photographs corroborate | Trace hardscape perimeter and actual threshold connections |
| Parking approximately 3 m below near entrance | Supported by terrain sections | Differential level measurement from terrace paving to nearby asphalt |
| Parking continues falling southward | Strong raster evidence; robust to small sampling shifts | Levels at entrance, middle and south end using one benchmark |
| Bank varies in width and slope | Supported approximate fit | Measure toe, crest, shoulders and any low retaining wall separately |
| Asphalt overlaps bank in model | Confirmed against reconstructed sections | Final aerial trace of asphalt edge, with uncertainty band |
| Public road / parking access / separate ramp are distinct | Aerial and mapped-route agreement | Confirm current gate, branch and ramp-mouth arrangement on site |
| Central model road is too low; lower approach too high | Supported by uncovered-road samples | Road grade survey and verification of exact model-to-real XY registration |
| Povo 1 floor should move down 0.7 m | NOT established | Finished-floor and exterior-threshold survey, tied to a common benchmark |
| Povo 2 bank should be copied exactly | Rejected | Use it as a visual reference; measure each site's actual sections |
| Exact terrace width, access doors, northern return | Unresolved | Floor plan, dated close photographs and local measurements |
| Road sample beneath bridge is observed ground | Not guaranteed | Check classification/interpolation or obtain an independent ground level |
| Compiled game matches these source findings | Not verified here | Build the exact source revision and inspect compiled collision/runtime |

Do not interpret the approximate terrace–parking difference as a required constant everywhere. Do not use fit RMS or ±1 m sampling sensitivity as the total accuracy of the source data. Different survey dates can contain genuine site changes.

## 9. Data verification checklist before implementation

- [ ] Recheck DTM, DBM and image checksums against their provenance; retain the originals.
- [ ] Keep EPSG:25832 and the stated vertical reference explicit. Convert model Z by adding/subtracting the existing 370 m origin exactly once.
- [ ] Separate model local metres from Source 2 engine units. Use the repository's established export conversion; do not infer a new scale from screenshots.
- [ ] Overlay the FINAL registered geometry, not just source config or pre-registration geometry, on the aerial image.
- [ ] Trace asphalt edge, pavement, terrace hardscape, bank toe/crest and retaining walls as separate features. Include the residential edge and southern termination.
- [ ] Preserve the public-road continuation and distinguish it from parking access and the separate ramp. Verify uncertain covered ramp mouths with photographs.
- [ ] Sample multiple parallel road lines and cross-sections; exclude kerbs, walls, buildings and covered edges from a road-surface fit.
- [ ] Flag DBM–DTM building/bridge regions. Agreement between DBM and DTM outdoors is not independent proof of exact elevation: the products may share ground values.
- [ ] Fit a smooth, explicit longitudinal road profile and a graded parking surface. Do not directly triangulate all DTM irregularities into playable asphalt.
- [ ] Retain an evidence record for each anchor: location, surface type, source/date, absolute altitude, local Z, confidence and any game adaptation.
- [ ] Check the actual terrace/indoor threshold relationship before deciding whether to adjust a floor, a short transition or the external grading.
- [ ] Compare later aerial/photos with the 2014/2018 terrain collection for changes, especially the ramp, gates and landscaping.

### Suggested anchor register

Maintain one table in the implementation with these rows at minimum:

- Povo 1 −1 indoor finished floor and each confirmed exterior threshold.
- Terrace paving at north, middle and south; bank crest and toe at the same sections.
- Parking entrance, representative bay/aisle centres and south end.
- Eastern road tie-in, bridge crossing, west bend and parking-access junction.
- Separate ramp mouth, top/bottom landing and retaining edges.
- Povo 2 UP stair bottom/top, adjacent pavement and terrace; garage-ramp tie-in.
- Bridge slab underside and any lower beam, fixture or obstruction.

Use separate columns for **observed source altitude**, **existing model altitude**, and **proposed model altitude**. An adapted model level must not overwrite or be presented as a measured real-world height.

## 10. On-site / real-world checks

These observations would resolve the remaining uncertainties. They are requests for evidence, not measurements already obtained.

- [ ] Establish one repeatable benchmark and record relative levels with suitable levelling equipment. Phone GPS altitude alone is not sufficient for thresholds or floor-storey differences.
- [ ] Measure the step or flush transition between Povo 1 −1 and the terrace. Record which specific doorway connects them; do not infer doors from generic façade bays.
- [ ] Photograph and measure the terrace's paved width at several positions, northern return, south termination, fences and retaining edges.
- [ ] At matching north–south stations, measure terrace paving → upper shoulder → bank crest → bank toe → asphalt. Include wall heights and crossfall, rather than treating every centimetre of the drop as grass slope.
- [ ] Measure parking levels near the entrance, middle and far end, including transverse slope across both rows and aisle.
- [ ] Walk and photograph the public-road/parking-access junction and the separate ramp, including gates, covered entrances and changes of direction.
- [ ] Record road grade breaks, pavement levels, kerb heights and driveway crossings; distinguish public road from service access.
- [ ] Measure bridge underside/lowest obstruction relative to the road below at several transverse positions.
- [ ] Count Povo 2 exterior stair risers and record landing positions, total rise and run. Check whether existing model landings correspond to the same physical points.
- [ ] Confirm drainage channels, drains and runoff direction where terrace/parking/road meet; these help explain small local falls.
- [ ] Record date, viewpoint and measurement endpoints with every photograph or sketch so later changes can be distinguished from registration errors.

## 11. Implementation dependency map

| Area | Relevant source / record | Dependency and required check |
| --- | --- | --- |
| Final assembly | `tools/build_povo_campus.py`, `build_registered_geometry()` | Apply corrections at the correct stage; later passes must not restore old surfaces |
| Exterior input and fixtures | `config/povo_exterior.json`, `tools/build_povo_exterior.py` | Parking Z, road points, markings, cars, gates and lamp bases are coupled; some heights are hardcoded |
| Final road / Povo 2 frontage | `tools/povo2_frontage_registration.py` | Overrides old road XY/Z; controls both pavements, bank, guards, stair landing and bus placement |
| Context ground | `tools/povo_exterior_integration.py` | Cut or rebuild flat concrete/grass beneath lowered exterior; avoid exposed underlay and floating ground |
| Povo 1 apron | `tools/povo_pavement.py` | Existing apron grade is tied to legacy road levels; changing the road alone creates seams |
| Pavement normals / lighting | `tools/povo_pavement.py`, `tools/povo_pavement_lighting.py` | Recalculate geometry-dependent normals/finish surfaces and rebake after regrading |
| Povo 2 terrace / garage | `tools/povo2_terrace_integration.py`, `tools/povo2_parking_continuity.py` | Preserve approved terraces/lightwells; reconcile road/garage ramp mouths and collision |
| Interior floor baseline | `config/povo1_interior_study.json`, `config/povo1_campus.json`, `tools/povo1_survey.py` | DTM cannot alone determine indoor finished-floor Z |
| Povo 1 lift and stairs | `tools/povo1_lift.py`, campus stair generation | If indoor floors move, update lift stops, sills, doors, triggers and all stair endpoints together |
| Bridge / building connections | Final bridge slab and Povo 2 connection metadata | Floor equality, soffit clearance and approaches must remain consistent |
| Props and lighting | Exterior generation and final entity export | Re-seat posts, cars, bus, tree bases and light origins; avoid floating or buried fixtures |
| Navigation / radar | `tools/povo_spawns.py`, campus export, `tools/build_povo_radar.py` | Rebuild derived gameplay data and check floor selection after elevation changes |
| Source audits | `tools/audit_povo_exterior_integrated.py`, `tools/audit_povo2_frontage.py` | Some legacy routes use old N−5 / Z3 assumptions; validate the final registered assembly |

The bridge crossing widths are constrained by the user's measurements recorded in [the library/road span record](docs/POVO_LIBRARY_ROAD_SPANS_20261107.md): approximately 5 m from library wall to rail, then 15 m across the road/pavements to Povo 2 grass. Do not silently discard these constraints while aligning centrelines.

Preserve [the definitive Povo 2 −1 layout](docs/POVO2_MINUS1_DEFINITIVE_LAYOUT.md), including subsequent documented terrace and parking revisions. A required alteration to a stair layout should be an explicit recorded revision, not an accidental consequence of changing road Z. Materials, exterior grading and approved interior topology are separate constraints.

## 12. Source validation and in-game acceptance

### Before compiling

- [ ] Generate final registered geometry successfully and record the source revision/configuration.
- [ ] Sample road, both footways, terrace, parking aisle and driveway connections against final render and collision surfaces.
- [ ] Check surface continuity at joins in both travel directions, including crossfall and kerb ramps. Inspect the actual rise over short distances, not only endpoint equality.
- [ ] Verify no parking asphalt remains over the bank and no old concrete/grass remains above lowered surfaces.
- [ ] Check overlap/flicker audits, mesh winding, closed collision solids, slope transitions and narrow sliver geometry.
- [ ] Check standing-player clearance, stair riser consistency, landings, guards and unintended ways into voids.
- [ ] Recheck bridge clearance across the full carriageway and pavement widths, including beams/fixtures.
- [ ] Preserve the approved Povo 2 interior/terrace connections, garage lightwells and door behaviour.
- [ ] Update affected route assertions to the intended new geometry, while retaining meaningful independent tests for continuity and topology. Do not simply change expected numbers until tests pass.
- [ ] Run relevant exterior, pavement, frontage, parking and stair tests; then the repository's required build checks. The November historical test counts are not evidence for a new build.

### Compiled package and runtime

- [ ] Build through the campus pipeline, not the older compact-arena pipeline. The documented supported compilation path uses Windows CS2 Workshop Tools.
- [ ] Record package identity, timestamp, source revision and validation results. Check compiled collision, not only the Python geometry.
- [ ] Walk downhill and uphill beneath the bridge on both pavements and the road; inspect grade breaks and bridge clearance.
- [ ] Walk from the public road through the actual parking-access branch, across the lot and back, including its southern end.
- [ ] Traverse the terrace and its confirmed entrances/returns. Inspect the bank from both above and below.
- [ ] Check the separate ramp route if playable; otherwise verify its intended boundaries, gates and collision.
- [ ] Retest Povo 2 UP/DOWN stair connections, terrace and garage approach affected by exterior joins.
- [ ] If any interior levels change, retest all affected stairs, the bridge and every Povo 1 lift stop/call/door alignment, including round reset.
- [ ] Use normal movement for acceptance; noclip is useful for inspection but does not prove walkability.
- [ ] Inspect normal-lit views from parking entrance, south end, terrace, bridge road in both directions and Povo 2 bank. Check shadows, textures, seams and floating props.
- [ ] Check nav routes, bots, spawns, radar floor transitions and gameplay clipping after regeneration.
- [ ] Confirm which seasonal package was rebuilt. Do not describe winter or Workshop as updated unless separately built/published and verified.

## 13. Completion criteria and suggested work sequence

A corrected source preview is ready for review when it shows the three distinct road/access paths, a level upper terrace relationship, a longitudinally sloping parking lot, and a continuous grass bank with plausible widths and visible edge details. It must show the affected Povo 1 and Povo 2 junctions, not just an isolated attractive cross-section.

A correction is complete only when the adopted height anchors and adaptations are documented, all connected surfaces and fixtures agree, source checks pass, and the exact compiled package has passed the affected walking and visual checks. Any unresolved real-world dimension must remain labelled approximate.

Suggested work packages:

1. **Evidence and anchors:** finalize traces, source profiles and unresolved threshold measurements.
2. **Coordinated source geometry:** road branches, grades, parking, terrace, bank, retaining edges and joins.
3. **Dependent systems:** props, lighting, doors/lift if affected, navigation, radar and source audits.
4. **Compiled verification:** build, collision checks, normal-lit captures and bidirectional walks.
5. **Handoff:** record final values, deviations from survey, package identity, remaining issues and publication status.

## 14. Supporting records and reproducibility

- [Detailed source audit](docs/POVO1_TERRACE_PARKING_ANALYSIS_20261111.md).
- [Data sources, CRS and licensing](docs/DATA_SOURCES.md).
- [Measured road spans](docs/POVO_LIBRARY_ROAD_SPANS_20261107.md).
- [Povo 1 lift / paving record](docs/POVO1_BUS_PAVING_AND_LIFT_20261109.md).
- [Povo 2 terrace integration](docs/POVO2_TERRACE_INTEGRATION_20261108.md).
- [Povo 2 parking continuity](docs/POVO2_PARKING_CONTINUITY_20261109.md).
- [Build handoff](docs/BUILD_HANDOFF.md).

Session working evidence is under `work/povo1-full-analysis/`: `analyze.py`, `measure.py`, `figures.py`, regenerated `geometry.json`, `measurements.json`, `route_samples.json`, `support_checks.json`, `plan-review.png` and `elevation-review.png`. This working directory is untracked; preserve selected evidence in a maintained location before relying on it in another checkout. Run scripts from the repository root with `PYTHONPATH=.` and the existing Python/numpy/matplotlib dependencies. The source hashes and numeric findings above are retained in this document even if working artifacts are absent.

The older `work/povo1-grade-review/` is preliminary. In particular, its model-centreline road trough and uniform Povo 2 slope interpretation must not be used as implementation targets. Use the corrections and limitations in this file.
