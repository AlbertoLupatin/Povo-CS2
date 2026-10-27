# Povo campus survey - 27 October 2026

This is the central review index for the 44 supplied walk photographs. Original files are unchanged and hashed in [archive manifest](../data/reference/povo_photos/walk_2026-10-27/manifest.json). The [archive README](../data/reference/povo_photos/walk_2026-10-27/README.md) preserves the complete user photo-to-location guide, including missing03/29, the user-confirmed41/42/43 route.

## Building reviews

- [Povo1 survey](POVO1_SURVEY_20261027.md): entrance, missing intermediate floor, bridge, courtyard, stairs and Acquario.
- [Povo2 survey](POVO2_SURVEY_20261027.md): four floor assignments, full-building room candidates, bridge, lab marks, parking/office route and garden.
- [Library and canteen survey](POVO_AMENITIES_SURVEY_20261027.md): local floor plans, source-space room partitions/openings, terrace and walkable canopy.
- [A103 photo 4 review](../exports/povo_campus/a103_photo4_review.png): current source cutaway and top view, with estimated counts, footprint and transparent glazing edges.
- [Povo 2 annotated photo 46](../exports/povo2_survey/floor_-1.svg): room IDs, observed door segments, exits, corridors and cores over the rectified photograph. Other-floor [0](../exports/povo2_survey/floor_0.svg), [-2](../exports/povo2_survey/floor_-2.svg) and [+1](../exports/povo2_survey/floor_1.svg) diagrams are labelled candidate layouts.
- [Amenities trace data](../config/povo_amenities_survey.json) and annotated photographs: [library0](../exports/povo_amenities_survey/library0.svg), [canteen0](../exports/povo_amenities_survey/canteen0.svg), [canteen1](../exports/povo_amenities_survey/canteen1.svg).

## Canonical floor names and questions

| Building | User floor | Established meaning |
|---|---|---|
| Povo1 | -1 | Entrance and lower courtyard level; A1xx |
| Povo1 | 0 | Intermediate A2xx level now present in source |
| Povo1 | 1 | Offices, bridge and upper courtyard connection |
| Povo2 | -2 | Parking/office vestibule and garden-route assignment; photo37 printed caption differs |
| Povo2 | -1 | Plans1/46 and two marked existing labs |
| Povo2 | 0 | Entrance level |
| Povo2 | 1 | Bridge, joined to Povo1 bridge1 |
| Library/canteen | 0 | Same local floor as Povo1 -1 |
| Library/canteen | 1 | Same local floor as Povo1 0 |
| Library | -1 | Storage shown in directory16; optional implementation |

The user confirms Povo1 entrance-1 and Povo2 entrance0 are roughly the same physical elevation. Bridge1 endpoints align. Povo1 provisional -1/0/1 elevations are4/7.6/11.2; these are gameplay calibration values, not measured storey heights. Amenities local0/1 follow4/7.6. The overhead walkable canopy follows the existing entrance-cover profile with3.4m clearance above the main stair; it is not a new enclosed floor.

The user resolves the route after the second black door: LEFT goes to39/40 offices; RIGHT goes to43, then LEFT into41/42 toward garden44/45. Photo37 still retains the user -2 assignment alongside its printed caption. Photo4 is now confirmed by the user as A103. Its compass placement and exact facade/corridor registration remain approximate; the correction applies only to the A103–A106 family, not other classroom families.

## Integration status

Active source geometry has three Povo 1 floors at 4/7.6/11.2 m, office-style upper rooms, the bridge on +1 and connecting red stair segments. The Acquario is one open study room with glazed corridor frontage and two flanking photocopy spaces, replacing four synthetic cells; shared tables and chairs are provisional. Povo 2 preserves its active compact plan with two successive upper rises to the raised bridge; the full photograph-traced Povo 2 plans remain separate review data, not active geometry or a claim of complete reconstruction. The photo46 registration helper is dormant and is not called by campus assembly. Source previews show all three Povo 1 floors: [layout](../exports/povo_campus/adjustments_layout_review.png), [bridge](../exports/povo_campus/povo2_connection_review.png).

Amenities include observed partition/opening paths, a central library stair and source-axis end stairs, the open street terrace, and thin walkable canopy collision. Their two local floors remain at 4/7.6 m. Perspective registration of independently photographed plans requires provisional stair-clearance cuts and facade aperture extensions; these are access accommodations, not surveyed dimensions. Untraced sanitary cubicles and upper-library directory-only zones remain explicit limits.

Existing XY footprints remain provisional. Photo 4 is identified as A103; only its compass placement and exact registration remain approximate. Photo 37 printed floor caption versus the assigned -2 route remains unresolved. For photo 46's right circled lab, the user confirms exactly one entrance from the corridor; the red star marks a separate exit to the external courtyard. This resolves the connection topology. The exact blue-obscured north door position remains uncertain. The confirmed 43-left-to41/42 garden route is retained. No further room labels or precise wall/door coordinates are inferred from unresolved photographic detail.

This index records source state only. Native build/package evidence belongs in the worklog; earlier successful engine checks do not certify the revised survey geometry. Post-build engine testing is omitted at the user's request.
