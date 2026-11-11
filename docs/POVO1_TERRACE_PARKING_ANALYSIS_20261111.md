# Povo 1 terrace, surface parking and descending road — 11 November 2026

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

Use EPSG:25832, source orthometric heights with ITALGEO 2005, and the existing model origin E666250, N5103800, Z370. No vertical datum conversion was made. Source resolution is not positional or vertical accuracy. Licensing and chronology remain as recorded in `DATA_SOURCES.md`.

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
