# Povo 2 road / garden fill reference review — 4 November 2026

## Result and scope

The user requested examination of the photos, Google Maps and other sources,
including RoanS77's branch, to determine what belongs in the unfinished area
beside the inclined road and bus. This review produces a concrete treatment
plan. **It does not change source geometry, compile a package or replace the
running sidewalk build.**

The area calls for separate ground, retaining-wall, podium/façade and open
lightwell treatments. A single raised solid across the whole dark area would
conceal real exterior space and interfere with the approved lower route.

[Annotated plan](../exports/povo2_area_reference_20261104/fill_review_plan.png)
and [editable SVG](../exports/povo2_area_reference_20261104/fill_review_plan.svg).
The plan uses the **final assembled** garden/stair metadata from `build_geometry()`;
the earlier `config/povo2_gardens.json` alone contains superseded stair locations.

## Evidence actually examined

| Source | Observation and use | Limits |
| --- | --- | --- |
| Local P009, P010 and P011 | Glazed pavilions beside paved terraces; paving, grass/tree strips, metal guards and a road-edge level change. P011 shows the terrace's vertical edge and glazing below its level. | The viewpoints do not establish surveyed dimensions or every basement face. |
| Local P012 | A flat paved terrace, a tall concrete retaining wall, open grass/paved space below, glazing and an exterior metal stair. The lower space is open to the sky. | Preserve the user's later approved stair/terrace topology over older provisional registrations. |
| User walk photos 44 and 45 | Lower garden grass, perimeter paving, glazed/metal-panel building face, tall concrete boundary and open steel stairs. | Finishing evidence; no new room layout is inferred. |
| Google Maps, Polo Ferrari – Povo 2 | Visually inspected its photo gallery in the browser, including Ammar Eqbal's June 2024 view across the glazed strip and Oussema Kasraoui's May 2023 street-side pavilion/guardrail view. | Context only. No image, texture, traced outline or measured geometry was extracted from Google Maps. These were gallery photos, not a surveyed Street View reconstruction. |
| Comune di Trento 2024 orthophoto | Inspected the existing georeferenced 0.5 m crop and Roan's 0.15 m crop. They distinguish the long terrace/podium, pavilions, open recessed pockets and the road/vegetation strip. | Source flight 28–29 August 2024; CC0 metadata is preserved in the repository. Aerial shadow is not a roof or a wall height measurement. |
| RoanS77 `shaders-mod`, commit `97769b5d9a6dfb9590599698707a4c7a463cfb5b` | Read `remake/PROJECT.md`, `tools/povo2.py`, `tools/build_site.py`, provenance and the corrected campus feedback map. The remake separates the plaza/strip volume from Holes 1–3 and joins flat exterior areas to terrain with retaining walls. | An alternative reconstruction, not the approved layout baseline. Its own guide records approximate strip/lower-floor interiors. |
| BASE, the campus façade contractor | Its project description corroborates architectural aluminium panels around laboratories/courtyards, glazed entrances and stainless-steel railings. | Corroborates material/construction types, not the position of an unobserved opening. |
| Manens project record | Confirms the campus's two blocks, elevated connection and underground accommodation. | General project context, not local fill dimensions. |

Links: [Google Maps place](https://www.google.com/maps/search/?api=1&query=Polo+Ferrari+2+Trento),
[municipal orthophoto viewer](https://gis.comune.trento.it/it/map/cartografia-generale/qdjango/42/),
[RoanS77 commit](https://github.com/AlbertoLupatin/Povo-CS2/commit/97769b5d9a6dfb9590599698707a4c7a463cfb5b),
[BASE project](https://www.baseserramenti.com/it/realizzazioni/poloscientifico-trento),
[Manens project](https://manens.com/en/sectors/university-and-research/fabio-ferrari-science-and-technology-hub-university-of-trento/).

The existing [photo manifest](../data/reference/povo_photos/manifest.json) and
[walk manifest](../data/reference/povo_photos/walk_2026-10-27/manifest.json) retain
photo attribution/source information. Roan's selected files were read through
Git into `build/area-reference-20261104/roan/`, with exact SHA-256 identities in
`read-only-manifest.json`. They were not checked out over local changes or run.
The extra bridge photo was also inspected; most of its view is obstructed by
the bridge louvers, so it is weak evidence for fill boundaries.

## Confirmed source defect to address before adding fill

The assembled exterior still contains `exterior_povo1_street_grade`, an older
Povo 1-to-Povo 2 paving ramp. After successive garden/entrance cuts its surviving
mesh bounds are:

- E **52.0–56.7 m**, N **1.25–6.333 m**, Z **6.2–7.42 m**.
- 96 surviving triangles; a top remains at **7.00 m** at E56/N3 and **6.52 m**
  at E56/N5. These are source-local heights, not absolute surveyed elevations.

The original strip was generated between N0 and N10, independently of the
approved lower garden. Garden/entrance cuts stopping at Z6.2 leave its upper
pieces behind. These are concrete source evidence of surviving raised context
paving, and a plausible contributor to the dark floating-panel appearance.
This does **not** prove that every dark pixel in the native views is this mesh;
removal needs a same-camera native comparison.

The next repair should explicitly remove or trim the obsolete remnant and any
unsupported associated guard pieces, then close the exposed edges. Adding a
solid underneath every remaining triangle would preserve the wrong ramp shape.
See [source diagnostics](../exports/povo2_area_reference_20261104/source-area-diagnostic.json)
and [assembled bounds](../exports/povo2_area_reference_20261104/approved-area-bounds.json).

## Treatment by region

| Plan region | Proposed treatment | Preserve / verify |
| --- | --- | --- |
| **A — road-side backing** | Continuous concrete retaining/cut face under the repaired sidewalk's inner edge. Follow the actual varying sidewalk top; close the sides and underside to adjacent ground/support. | Keep the existing sidewalk top, carriageway and lower walking clearance. Reuse/extend the existing D support pieces where appropriate rather than overlapping them. |
| **B — bank and planting** | Restore coherent ground/upper-bank surfaces, with paving at connections and grass/low shrubs where the reference supports planting. Close visible vertical cuts; remove the old elevated ramp first. | The orange region is a treatment envelope, **not a solid-fill mask**. Subtract the approved lower route, stair and landing clearances from any backing volume. The existing provisional upper level is a fitting constraint, not a new measurement from a photo. |
| **C — terrace / podium edge** | Keep the terrace top flat. Give its exposed edge a coherent vertical façade down to the lower exterior level: concrete retaining faces, aluminium-panel or glazed building faces according to the matching photo. | Do not invent glazed doors or fill existing openings. A podium is building volume, not a sloping pavement sheet. |
| **D — obsolete ramp remnant** | Remove/trim the surviving raised context paving identified above, then stitch its boundary into the chosen ground/retaining treatment. | Exclude the new `road_front_campus_paving_*` sidewalk and every approved terrace/stair component from this removal. |
| **Green — open lower garden** | Keep its open footprint and lower floor. Finish with grass, perimeter paving, concrete boundaries, and the already approved stairs and exits. | No roof or raised blanket fill across it. Keep the blue route in the plan open through/along all proposed backing. |

Small planting details should follow the photos' low vegetation and young street
trees. A specific shrub species, exact planting counts, and detailed unseen
façade modules are not established by this review.

## How RoanS77's branch should inform the implementation

Use its construction method: explicit terrace/podium solids, explicit openings
for lower exterior pockets, and retaining walls where those levels meet terrain.
Its surface classification also keeps road, sidewalk, planting and building
volumes distinct. This is more appropriate than another overlapping sloped slab.

Do not copy its geometry directly. The remake uses **1.25 gameplay scale**, an
origin at E666265/N5103785/Z370 and different building/floor heights (for example,
4.75 m Povo 2 storeys). The current source origin is E666250/N5103800/Z370 and
its approved lower routes use the existing local levels. Its Hammer axes also
differ from this pipeline's world conversion. Re-register any borrowed *method*
to the current model; preserve the approved room, terrace, stair and door bounds.

## Implementation and acceptance order

1. Remove the confirmed obsolete context remnant by name/region and render a
   source comparison. Do not regenerate the approved basement from the remake.
2. Build A/B/C as non-overlapping, closed surface/volume pieces with explicit
   openings for the final assembled lower routes and stairs. Record any metric
   finishing assumptions and retain both render/collision consistency.
3. Check current basement/stair/terrace metadata against the previous accepted
   package; audit lower-route headroom, garden exposure and new face winding.
4. Build using the supported optimized Windows campus pipeline with normal
   lighting. Validate package CRCs and native collision.
5. Repeat the same frontage/uphill/bus cameras from the sidewalk review, plus
   views from the lower landing/garden. Walk the repaired sidewalk and the
   approved lower route in both directions, checking transitions and headroom.

No blanket fill, native validation claim or layout revision is made by this
reference-review artifact. The currently installed package remains the
[verified sidewalk build](POVO2_SLOPED_SIDEWALK_20261104.md), SHA-256 `09396dc0…`.
