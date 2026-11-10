# Library stair and bridge road measurements — 7 November 2026

The user measured two consecutive spans across the street. The library wall to the roadside handrail is about 5 m. From that rail across both pavements and the road to the Povo 2 grass is a further 15 m. The [27 October bridge photo](../data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300/image00002.jpeg) shows the library stair, hedge and planted slope. The user supplied the overhead screenshot as a visual reference and supplied the distances. The model uses those dimensions.

## Mid-stair cross-section

At E44, distances increase from the library toward Povo 2.

| Feature | North coordinate | Distance from library wall |
| --- | ---: | ---: |
| Library wall | −13.00 m | 0.00 m |
| Roadside handrail at planted retaining edge | −8.00 m | 5.00 m |
| Library-side curb at asphalt | −4.31 m | 8.69 m |
| Povo 2 curb at asphalt | +2.69 m | 15.69 m |
| End of pavement at Povo 2 grass | +7.00 m | 20.00 m |

The measured endpoints determine the two outer edges. The existing curb lines determine the division within the 15 m span, giving 3.69 m from rail centre to asphalt, a 7 m carriageway and 4.31 m across the opposite pavement. Those individual widths have no new independent survey measurement.

Library planting now extends from the stair-side edge at N−11.45 to the retaining wall at N−8.1. The street handrail sits on that wall. The concrete strip formerly separating the planting and street handrail has been removed. The planted bank across the road narrows near the measured section. The library stair, Povo 2 basement stairs and terrace, and adjacent buildings retain their positions.

The measured section extends from E32 to E46. Both walks taper toward the lower approach at E22. At the upper end, the Povo 2 pavement rejoins the existing corner apron at E49.3. The library pavement follows the planting to E52 and rejoins the existing sidewalk at E54. Sidewalk faces share cross-sections through the bend, with vertices at each change in curb direction.

## Verification

The frontage audit passed 3,267 route samples and 272 bridge samples. A separate check sampled 10,850 interior points on each sidewalk from E22 to E57. All 21,700 points had exactly one supporting pavement mesh. A regression test also checks the area of intersection between the sidewalks and the carriageway. The corner apron retains its existing 0.12 m continuity limit between samples taken 5 cm apart.

The final source passed all 465 tests. The render overlap audit examined 750,610 faces and found zero overlapping pairs. The standard build used normal lighting with a 1024-pixel atlas. All 1,536 package entries passed CRC verification. The 73,483,250-byte package has SHA-256 `d6a2812e1afab85dc27f67ef37bd558bb252847c05433db7c8f9873e8e44bdb8`. Build logs are in `build/handoff/20261107T170734902408Z/`. The prior standard package is backed up in `build/library-measurement-20261107/previous-standard.vpk`.

Compiled physics supported all 699 sampled pavement points, including the upper bend. The separate basement audit passed 12,707 floor −1 samples, 6,237 floor −2 samples, 36 column samples and 36 fixed-door surface samples. The native review addon loaded the verified package. Four ordinary walks traversed the widened pavement uphill and downhill on both sides, reaching all 12 waypoint checks. The solo review session was closed. See the [walking report](../exports/library_road_spans_20261107/runtime-report.json), [view toward the upper junction](../exports/library_road_spans_20261107/library_bridge_approach.png) and [view toward the bridge](../exports/library_road_spans_20261107/library_street_section.png).
