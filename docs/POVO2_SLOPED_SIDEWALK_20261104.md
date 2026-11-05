# Povo 2 sloped sidewalk repair — 4 November 2026

The user requested continuation of the sidewalk repairs on the inclined road
beside Povo 2, near the bus. This revision uses the latest `povo-updates.bundle`
changes plus the local native-build optimizations. The bundle diff was applied
to the main working source before the sidewalk revision; the earlier bundle
build report's isolated-only statement describes that earlier build.

## Geometry change

The campus-side widening used endpoints at a constant northing, while the
original narrow sidewalk used perpendicular offsets from the diagonal road.
These two overlapping surfaces consequently had different slopes: the wider
walking line was roughly 15–25 cm below the curb-aligned surface.

`campus_frontage()` now replaces the narrow campus-side strips north of the
crest with one widening following the actual curb endpoints and the road's
perpendicular end planes. Successive sections are clipped against previous
sections and uncovered corner gaps are filled at the shared endpoint elevation.
The existing carriageway trimming remains in force. Rendering and collision
use the same closed prisms.

The street alignment, asphalt, opposite sidewalk, bus, and approved Povo 2 −1
rooms, corridors, doors, terraces, stairs and garden excavation are retained.
This is a walking-surface repair, not a revision of the approved basement layout.

## Source and native model verification

- Six focused sidewalk tests pass, including cross-width grade consistency and
  a continuous 20 m walking line sampled every 5 cm through both slope ends.
- The new native-collision audit samples 250 points over the widened slope,
  its transitions, and both sidewalks of the bridge/bus approach. Against the
  earlier bundle package it detects 43 points off the required grade on the
  wider walking line; that comparison is retained in
  `build/sidewalk-fix-20261104/previous-collision.json`.
- A complete cold standard-season native build was launched in
  `build/local-benchmark/20261104T212308Z/` with normal lighting, a 1024 atlas,
  fresh addon outputs, all source tests, packaging/CRC and compiled basement
  audits. Final status and runtime evidence are recorded below.

The first full test pass stopped before compilation because the historical
route waypoints still expected the wider sidewalk's old grade. Its clearance
thresholds were retained; source and default native walking waypoints now
follow the corrected perpendicular slope-end planes. The focused route audit
passes after that correction, and a fresh complete build was launched.
The corrected run is `build/local-benchmark/20261104T212734Z/`; the earlier
failed run is retained and its time is not part of the corrected run's timer.

The corrected run passes all **423 source tests**. The main native model
compiles in **47.913 seconds**, and the new compiled-sidewalk audit passes
**all 250 samples**, with zero missing points (`compiled-sidewalks.json`).
`layout-comparison.json` confirms the basement rebuild, −1 corrections, West
Offices, stairs and lift metadata match the previous bundle build.

## Complete cold build

The corrected run completed at **22:44:00 CET**, taking **985.892 seconds /
16m25.9s** from source staging through all 423 tests, generation, model/material
compilation, normal lighting, navigation, bomb-damage bake, radar, packaging,
full CRC verification and compiled collision audits. The earlier failed
source-test attempt is separate, as recorded above. The native map compile
took 536.673 seconds, including 113.09 seconds of lightmapping and 304.1 seconds
of bomb-damage baking. The existing unconnected-ladder warning is retained.

Candidate: `build/local-benchmark/20261104T212734Z/source/build/package/trento_povo_campus.vpk`.

- Size: **62,991,896 bytes**.
- SHA-256: `09396dc0e1bb6709c528335a44d3c66911f63dee549f33472acbc06634a87bac`.
- **1,205 entries**, all **1,205 CRCs verified**.
- Compiled basement: **22,997 floor**, **72 column** and **36 sealed-door**
  samples pass; all seven required physical surface types are present.
- The original installed development map/model outputs remained unchanged.

The new package was copied into the isolated `trento_povo_bundle_review`
addon while CS2 was closed; its installed SHA-256 was checked before launch.
Native walking/visual review is recorded below separately.

## Native review and local deployment

**10 ordinary walking routes / 50 waypoints pass** on this package, with one
initial placement per route and no jumping or noclip between waypoints. They
cover downhill/uphill along the wider inner sidewalk, downhill/uphill near
the curb, crossing the slope in both directions, and downhill/uphill on each
side of the bridge/bus approach. The transcript and exact target/observed
positions are in
`exports/sidewalk_fix_20261104/exterior-runtime-walk.{json,log}`.

Four normal-lit native views were individually inspected and retained:

- [Same position as the earlier frontage view](../exports/sidewalk_fix_20261104/frontage_same_view.png).
- [Continuous downhill sidewalk](../exports/sidewalk_fix_20261104/frontage_downhill.png).
- [Lower transition looking uphill](../exports/sidewalk_fix_20261104/frontage_uphill.png).
- [Sidewalk toward the bus](../exports/sidewalk_fix_20261104/bus_approach.png).

The overlapping gray strip has been replaced by continuous paved surfacing.
Existing dark sloped surfaces farther inside the garden/approach remain visible
and are not certified repaired by this sidewalk pass. The open approved garden
and stairs remain; this is a targeted exterior review, not a full-campus or
multiplayer certification.

After that review, the checked package was copied to
`build/package/trento_povo_campus.vpk` and the normal `trento_povo_campus_test`
addon. Both copies match the candidate SHA-256 above. The normal package was
reverified against the root radar overview with all 1,205 CRCs checked. Previous
copies (SHA-256 `18d154a01b9cdbe554db740657cd700899dab4ebc4ac8a5541ed4eaacafcd753`)
are backed up as `build/sidewalk-fix-20261104/previous-{0,1}.vpk`.

The running game uses the same new bytes through `trento_povo_bundle_review`.
After closing it, the ordinary `play_campus.cmd` now loads this repair. The
winter package and Workshop publication remain at their prior versions.
See `exports/sidewalk_fix_20261104/promotion.json` for exact copy/backup paths
and `captures.json` for image hashes, poses and lighting settings.

The prior normal-lit view is
`exports/bundle_review_20261104/povo2_current_view.png`. New native screenshots
and normal walking results belong in `exports/sidewalk_fix_20261104/`.
