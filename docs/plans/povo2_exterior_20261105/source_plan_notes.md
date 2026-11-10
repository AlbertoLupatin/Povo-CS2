# Source-based Povo 2 plan — 5 November 2026

This worksheet supersedes the rejected schematic interior. It plots the current assembled source geometry and metadata without relocating rooms or reversing stairs. Green geographic boundaries are OSM footprints, not a floor-level survey. No map geometry was changed.

## Spacing check

At local east 18.25 m, the cached Povo 1 north and Povo 2 south OSM facade intersections give approximately 30.75 m between buildings. The source bridge runs from north -20 to +10, or 30 m. This difference is comparable to the earlier audit's approximately 0.5–1 m reference uncertainty; it is not evidence that either whole building should move. This check applies at the bridge only, not every facade or terrace.

References: `data/reference/osm/povo_osm_overture.geojson`, Overture release 2026-10-21.0, OpenStreetMap contributors / ODbL. The 30 October OSM/LiDAR audit is historical corroboration, not a fresh audit of the current assembled geometry.

The two aerial screenshots embedded in `data/reference/user_feedback/2026-10-28/Povo2 Gardens.drawio` were extracted and visually inspected. They show the roadside grass, bridge, sunken garden, and retaining-wall stair. No visible ruler or scale permits reliable exact lengths from those screenshots alone; oblique imagery should not be treated as a measured floor plan.

## Preserved source layout

Reception opposite entrance; short approach alongside the stair room; perpendicular corridor beyond it serving B106/B108/B109. The source stair core is E11..20.5, N14..26. B106/B108/B109 lie at N0.5..8, and their corridor at N8..11. The OSM main south facade lies around N10.8. Simply translating the row north would overlap the core. The user has now confirmed that the projecting rooms are B106/B108/B109. Their identification is resolved; floor-level registration and dimensions still need checking before proposing a destination. Do not pack the row into an invented internal arrangement.

The exterior panel plots existing UP and DOWN runs directly from source route points. These directions are constraints on any future relocation, not newly designed routes. The -2 garden is E38..55.5, N8.75..20. Its real-world relation to the retained facade requires confirmation.

The entrance target is a simple rectangle retaining both door lines. Its source lobby bounds already form a rectangle; the visually unwanted upper-left extension must be identified among adjacent assembled pieces before trimming. Do not remove part of the main building by treating the entire neighbouring annex as entrance geometry.

## Requested measurements / identification

1. RESOLVED: the user confirms the projecting rooms are B106/B108/B109. Preserve their existing order, connecting corridor and relationship to the stair room; do not substitute a separate study-room area.
2. Google Earth overhead ruler: Povo 1 wall to Povo 2 yellow wall along the bridge centreline, marking both endpoints (walls, not roof overhangs).
3. Pavement building-side edge to Povo 2 yellow wall, perpendicular to the road beside the exit stair. Mark the grate and terrace edge in the same view if visible.
4. Entrance outer-door centre to the yellow facade corner facing Povo 1; mark both endpoints. This constrains the entrance/core/room group along the building.

These resolve global spacing and the room/entrance registration before another after-plan is presented as geometrically feasible.

Files: source_based_plan.png and source_based_plan.pdf; spacing_measurements.json records the numerical check. draw_source_plan.py is the plotting source, run from repository root after caching build_geometry() in build/layout_review/current.pkl. The cached assembly is local generated data, not committed source.

## Revision after Figure 3 correction

Figure 3 of source_based_plan.pdf was a current-source baseline, not the required after-plan, and is superseded for the exterior proposal by revised_garden_plan.pdf. The DOWN stair must START INSIDE the garden footprint. Its descent direction is retained (eastward in source coordinates). The proposed run occupies N8.75..9.75, starts E46.75 (halfway across the current 17.5 m garden length) and ends E54.5; the lower landing occupies the last metre to E55.5. The top landing also lies within the garden. This is a provisional metric fit based on existing garden dimensions, not a surveyed position. The existing terrace-to-stair connection requires reconstruction; the dotted approach is a study line, not a verified route.

floor_registration_review.pdf compares assembled horizontal slices for floors -2, -1, 0 and +1 with identical axes and the shared core datum. It demonstrates the mismatched envelopes without changing interior arrangements. The source elevations (-3.2, 0.4, 4, 11.2 m) are recorded assumptions; +1 is the bridge level in the current campus model, and this does not establish a single-storey interval from 0.

No independent floor translations or uniform scale changes have been applied. The floor-0 projecting room row is identified as B106/B108/B109 by the user. Fixing its registration while preserving its relationship to the core requires checking the facade-to-core distance and entrance-to-core distance against the photographed floor plan. A simple inward translation of the rooms alone is rejected. Whole-building spacing at the bridge remains approximately consistent with the geographic reference.

## AUTHORITATIVE CORRECTION — corridor/stair/garden connection

The user's latest clarification supersedes every earlier statement that the stair starts halfway along the garden:

- The -1 external corridor ends directly at the upper stair landing.
- That upper landing is exactly where the -2 garden footprint starts.
- The stair descends along the garden's road-side retaining wall.
- The LOWER landing at -2 is about halfway along the garden length.
- The corridor and stair are straight and aligned, without any dogleg.
- The stair connects corridor -1 to garden -2, not to the road above.

Earlier revised_garden_plan images and revised_garden_proposal coordinates reversed the start/midpoint relationship and must not be used. The previous provisional tread/run dimensions derived from that wrong relationship are withdrawn. The new connection diagram is schematic and establishes topology only; global registration and metric dimensions must follow this constraint. Interior layout and internal stair directions remain unchanged.
