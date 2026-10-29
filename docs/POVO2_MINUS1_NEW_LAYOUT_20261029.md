# Restored full-plan corridor layout

The user's latest clarification supersedes the western rearrangement below:
the corridor in today's photos is **internal to West Offices**. It is not the
main west corridor. When offered the original two-lab layout or the full plan,
the user explicitly selected **the full-plan layout before the west-office
rearrangement** and requested the complete 2D map.

The active exporter now uses `create_layout` followed by the annotation-only
`restore_full_plan`. It does not call `focus_west_corridor`, does not move the
western public passage to north 8–11 m, and does not apply the 6.7 m −2 shift.
The former full-plan room outlines, eight source corridors, four cores and
central void are restored. No main-corridor dimensions or positions come from
today's internal-office photos. The previous full-plan registration and its
0.75 m adjustment of the −2 branch are retained.

The full 2D map includes the western office area at the cropped plan edge as
a dashed context outline. The photograph is attributed to internal office
circulation; no exact internal corridor line or glass partitions are invented.
Restricted lab access stays closed as a requirement. The exact transfer of
the two installed fixed doors into this new full-plan registration is still
unresolved, so the map does not invent replacement door positions.

Current outputs: `exports/povo2_minus1_layout_20261029/layout.json`,
`minus1_full_plan_restored.png` and `minus1_full_plan_restored.svg`.
The PNG and SVG come from the same geometry via
`tools/render_povo2_full_plan_2d.py`. These are layout review artifacts;
the installed game map has not been changed.

## Historical western rearrangement — rejected

The user corrected the first review: the intended office route is the WEST
east/west corridor at the bottom of the figures, above B106/PC. The large
research wings are labs, and access to them must stay closed through both
permanently locked doors. The first review below is historical and its
north/south corridor reference is superseded.

The current export shows the western office corridor and its room band,
the retained main core, a short south approach, and two solid closed lab-access
doors. Today's glass/wood office finish study is applied to this western
route. The complete 80-room lab trace is retained only in the JSON's
`restricted_lab_context`; it is not shown as accessible offices.

The actual ground reference is now the transverse corridor at north 8–11 m,
east 2–31 m: all three westward passages share the **north 9.5 m centreline**.
The −2 vestibule moves 6.7 m south, retaining its 3.6 m width, with a short
stair approach to the unchanged core. This replaces the first review's
0.75 m eastward branch adjustment. The −1 western route is fitted locally
to the same north 8–11 m band while the core remains at its original bounds.

The western band contains six office outlines, the observed service room and
WC block. The existing side-room outlines come from photo 46. Four additional
outer-room outlines use the visible partitions along that photo's right edge;
their cropped outer boundary and exact glazing subdivisions remain provisional.
Three outer-room leaf intervals are approximately traced; the opening partly
hidden by the blue core annotation is labelled unresolved rather than guessed.
Exact photo-to-room IDs and official room numbers remain unconfirmed.

Two closed boundaries terminate the public route toward the lab wing: one at
the eastern end and one at the northern return. They are solid review-model
geometry with no opening action. Their new local positions are a schematic
refit of the user's access restriction, not a fresh surveyed door registration.
The existing −1 core's east face remains closed, preventing a third accidental
public connection into the laboratories. Only the south portal feeds the
western office approach.

Nine source tests pass, including the westward axis on all three floors,
continuous floor support from the existing stair door along the office route,
exactly two permanently closed lab boundaries, and isolation of the displayed
office layout from the restricted laboratory context.

The generator, settings and output paths are unchanged. This is a review
layout; no campus package has been compiled or deployed.

## Historical first review — superseded corridor interpretation

The interactive stack revealed that the short corridor beside the main stair
core was not aligned across floors. The user requested a new −1 layout using
floor 0 as the reference, the full floor plan and the 29 October walk photos.

This deliverable is a new, reproducible layout model and interactive review.
It does not replace or compile the installed campus package. The former
two-room basement and its fixed closed doors remain in that installed build.
The new full-plan layout supersedes that simplified shape in this review.

## Registration and alignment

The floor-0 reference is the north/south passage beside the stair core, at
campus east **20.5–25.5 m**, north **11–29.5 m**. Its centreline is east **23 m**.

The blue-marked core in photo 46 (`annotated_corridor_exit_core`) maps exactly
to the retained core, east 11–20.5 m and north 18–26 m. Photo horizontal maps
to campus south; photo vertical maps to campus west. Core-relative scale is
approximately 0.985 m and 0.869 m per normalized plan unit respectively.
The adjacent cross corridor's width is normalized locally to the floor-0
5 m width. All rooms, door endpoints and corridors use this same continuous
piecewise registration. This is a layout fit to existing estimated geometry,
not an independently measured metric survey.

The new −1 main corridor therefore has the **same 23 m centreline** as floor 0.
It extends across the complete traced floor, from north 6.92 to 105.38 m.
The short approach from the existing −1 south stair door joins this corridor;
the core footprint and door location stay in place.

The −2 office branch centreline moves from east 22.25 to **23 m**, a **0.75 m
eastward shift**. Its width stays 3.5 m. The vestibule extends to meet it, and
the garden approach meets its shifted eastern edge. Parking, garden and core
footprints remain at their existing coordinates. This is included in the
review model; it is not a claim of a deployed −2 change.

## Complete −1 content

The previous two generic labs are replaced by all **80 room outlines** in the
existing observed photo-46 trace, including both research wings, services,
toilets, lift lobbies, inner cross-wing labs, the two user-marked labs and
the office band. All eight traced circulation bounds, the central open void,
four core enclosures and fourteen photographed exit positions are retained.
Only the existing core contains the retained stair-tread study; the other
three cores are enclosures without invented flights.

All **79 image-traced door intervals** are carried through the registration
and cut from the adjacent walls. The single corridor entrance of
`annotated_lab_e` is confirmed by the user, but its position is obscured by
the blue annotation. It is labelled unresolved, with no guessed doorway.
Exit positions are reference markers in the JSON, not verified exterior routes.
Descriptive room IDs are trace identifiers, not invented official room numbers.

Photo 46 includes wings that are absent from the current partial floor-0
model. Their wider footprint in the stack is expected; fitting a complete
floor into the currently modelled ground-floor subset would erase the
missing research wings again.

## Today's photos

The three indoor images in `data/reference/povo_photos/walk_2026_10_29/Images`
show wood flooring, glazed office partitions with frosted horizontal bands,
white service walls, suspended ceiling panels, and a copier/recycling/
noticeboard recess. The new office band uses a wood/glazing finish study.
The exact photographed room locations are unconfirmed; furnishings and
room identities are not assigned to guessed locations. The three outdoor
photos do not establish additional −1 partitions.

## Files and validation

- Settings and evidence: `config/povo2_minus1_layout_review.json`.
- Generator: `tools/create_povo2_minus1_layout.py`.
- Viewer template: `tools/templates/povo2_layout_review.html`.
- Outputs: `exports/povo2_minus1_layout_20261029/layout.json`,
  `minus1_new_layout.svg`, and `review-3d.html`.
- The updated interactive view retains floor show/hide buttons, rotation,
  pan, zoom, plan overlay, adjustable spacing and a shared alignment selector.
  It opens with −1 alone; toggle floor 0 and −2 to compare.

Reproduce with `py -3 -m tools.create_povo2_minus1_layout`.
Run `py -3 -m unittest tests.test_povo2_minus1_layout_review -q`.

Six source checks pass: shared corridor axes, unchanged core registration,
continuous mapping at corridor boundaries, complete room/core/exit sets,
79 unobstructed traced door midpoints with the obscured door unresolved,
open courtyard, room-floor coverage, and source-backed finish annotations.
Browser checks confirm floor toggles, overlay, selected-point comparison,
responsive layout and no runtime JavaScript errors. These checks establish
the layout review, not native game traversal or photo-complete reconstruction.
