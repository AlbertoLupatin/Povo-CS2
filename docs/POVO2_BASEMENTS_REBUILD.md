# Povo 2 basement rebuild — 28 October 2026

**29 October correction:** the user rejected the former -1 layout. Its updated
30 m / 1.5 m lab corridor, lower exit connection and two permanently closed
doors isolating the L are documented in [the latest correction](POVO2_MINUS1_CORRECTIONS_20261029.md).
The older -1 layout and verification below are historical; level -2 is retained.

The package identities below describe the completed basement rebuild. A later
29 October lighting investigation produced a newer local standard package;
see [exterior visibility notes](POVO_EXTERIOR_VISIBILITY.md). The exterior pavement repair is now verified; the structural geometry and
collision are preserved while a separate probe-lit finish corrects rendering.
See that note for the current package identity and fresh basement regression results.

The user reported that levels -1 and -2 in the playable map differed from the
accepted paper layout, with incorrect placement, blocked routes, overlaps and
missing surfaces. The final basement shells are now built together by
`tools/povo2_basements.py`, in campus coordinates, after the earlier reference
placement passes. The generator consumes the accepted footprint and room records;
it does not reinterpret the sketches or introduce another registration.

The relocated parking previously retained rectangular floor and ceiling holes
from its old staircase. Sparse station checks missed them. A before/after
25 cm grid check of the parking rectangle finds 988 missing floor samples and
988 missing ceiling samples out of 18,432 before the rebuild, and zero after.
The recorded points are in `runtime/basements_rebuilt_20261028/parking_before_after.json`
under the campus exports. The replacement uses
a union of complete rectangles for each floor, with disjoint floor/ceiling
pieces and a merged perimeter. Internal room partitions and vestibule doors are
explicit. Shared stair-wall and floor overlaps are removed before opening the
portals. Both rendering and collision export consume these same boxes.

- **-1:** retained stair exit, corridor past the lift recess, two furnished
  CIBIO rooms, far left turn, straight exit corridor and approved garden passage.
- **-2:** complete parking slab and ceiling, separate vestibule, right-hand
  parking threshold and forward turn, left-hand office junction with a facing
  wall, and the right-then-left route to Garden -2.
- All six parking columns are rebuilt from floor to ceiling. Old clipped bodies,
  floating painted bands and orphan skirting fragments are removed.
- Existing stair positions, elevations and confirmed step counts are retained.
  Lower-floor lamps and ceiling fixtures are rebuilt inside the new shells.
- The -2 radar now includes the vestibule and office/garden corridors, in
  addition to parking and the garden.

The earlier independent exterior garage and its ramp retain their separate
registration. This change does not invent a connection across the unsurveyed
gap to that garage. Room labels, dimensions and absolute floor heights retain
their existing uncertainty; this is a repair of the accepted gameplay layout,
not a new measured survey of the entire underground building.

## Verification

`tests/test_povo2_basements.py` checks support and ceiling coverage throughout
the complete approved footprints on a 35 cm grid, including the former parking
shaft holes. It also checks the stair-to-lab route, both room thresholds, far
exit turn, parking aisle, vestibule branches and garden exit in both directions.
The integrated audit now includes these routes instead of only stair treads and
sparse stations. Its 1,519 sampled route points pass support/headroom checks;
all 12 parking, 20 basement and 50 ground-floor stations remain connected.

The older campus audit aliased only the former staircase's object names to the
upper floor. It now includes the replacement core plates and omits the obsolete
standalone compact-ground audit when the complete ground plan is integrated.
The stair's upper audit station moves from the removed flight onto its actual
landing; the old 40-step test now checks the confirmed 26-step upper stair.

[Geometry-derived review](../exports/povo_campus/povo2_basements_rebuilt.png).
Regenerate with `py -3 -m tools.render_povo2_basements`.

All 256 source tests pass (`build/basement-final-columns-tests.log`). The deployed
render/collision/map files match the rebuilt sources byte for byte; see
`exports/povo_campus/runtime/basements_rebuilt_20261028/source-deploy.json`.
The exterior garage route audit ends inside that garage, without claiming the
unsurveyed connection. The library wall test excludes the deliberately placed
bus, whose collision remains covered by the bus tests.

## Native model and map verification

The final native campus model compiled successfully. The existing Duplicate
Bone warning remains. Its SHA-256 is `2260dd191fd3f2e7adabfb03ad81ef43b4c04af4f096a2887563f94b3477326d`.

The compiled PHYS triangle checks pass: 4,181 floor samples on -1, 10,290 on -2,
and 72 column-surface samples at three heights around all six parking columns.
There are no missing floor or column samples. The previous column geometry
missed 48 of those 72 column checks. All seven physical surfaces pass as well
(asphalt, concrete, glass, grass, metal, tile, wood).

`tools/audit_povo2_compiled_floors.py` reads a Source2Viewer PHYS text dump and
checks the accepted floor footprints and registered columns. Reports are in
`exports/povo_campus/runtime/basements_rebuilt_20261028/`.

The final map uses **fast lighting with a 2048-pixel atlas**. Earlier 4096-pixel
atlas attempts stopped advancing and were stopped before packaging. The final
smaller-atlas run completed lighting in 7.46 seconds and map compilation in
387.974 seconds: 777 resources compiled, zero failures. Navigation contains
14,305 areas. Geometry and collision are unchanged by the lighting setting.

Reproduce with `build_campus.cmd --fast-lighting` or
`py -3 tools/cs2_campus.py --fast-lighting`. The checked wrapper preserves source
tests, package verification and build evidence. Its five tests pass, including
forwarding and recording the new option. Default lighting settings are retained
when the option is omitted.

## Final playable package and engine checks

`build/package/trento_povo_campus.vpk`: **45,193,069 bytes**,
**1,075 entries**, all **1,075 CRCs verified**. SHA-256:
`d0caba55484840059666c257662b7d4b6df9b4adfbc34e57154c10913178dc52`.
The packaged model hash matches the compiled model checked above. The copied
VPK in the fresh `trento_povo_basement_rebuild_test` addon matches these bytes.

A fresh solo CS2 session passed all **26 walking routes / 96 waypoints**:
24 routes covering both basement stair connections, rooms, the full -1 exit
route, -2 parking, vestibule branches and garden link, plus two ordinary walks
directly across the former parking-floor hole. Every route has one initial
placement; movement between its waypoints uses ordinary walking with collision
and `noclip 0`. Both directions pass. The guard requires exactly one human and
zero bots. This verifies traversal, not multiplayer balance or bot tactics.

Ten native PNG screenshots were captured and visually reviewed. They show the
continuous floors/ceilings, restored doors, both vestibule branches and all
parking columns reaching the ceiling without floating remnants.

- [Level -1 stair exit](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus1_stair_exit.png)
- [Level -1 corridor](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus1_corridor.png)
- [Level -1 exit corridor](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus1_exit_corridor.png)
- [Parking](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus2_parking.png)
- [Former floor hole](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus2_former_hole.png)
- [Vestibule toward parking](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus2_vestibule_parking.png)
- [Vestibule toward offices](../exports/povo_campus/runtime/basements_rebuilt_20261028/screenshots/minus2_vestibule_offices.png)

[Build summary](../exports/povo_campus/runtime/basements_rebuilt_20261028/build-summary.json),
[walking results](../exports/povo_campus/runtime/basements_rebuilt_20261028/walking/survey-runtime.json),
[hole-crossing results](../exports/povo_campus/runtime/basements_rebuilt_20261028/former_hole_walk/survey-runtime.json).

The standard seasonal variant is ready locally. Winter was not compiled and
Workshop was not updated.
