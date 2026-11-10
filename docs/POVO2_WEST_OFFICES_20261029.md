# Povo 2 −1 West Offices

**FINAL / USER-APPROVED:** the current West Offices, straight C7 and entrance
arrangement form the [definitive Povo 2 −1 map layout](POVO2_MINUS1_DEFINITIVE_LAYOUT.md),
explicitly approved in-game on 2 November 2026. Historical drawings below are
reference history and do not override that approved implementation.

The local eastern entrance and exterior stair arrangement now follow the
[31 October user Draw.io correction](POVO2_DRAWIO_ENTRANCE_20261031.md).
The historical plan images below are not a current as-built entrance drawing.

The West Offices are built inside the approved full-plan −1 layout, south of
C7 (the west main corridor), from the uncropped photo-46 office strip. The
photo corridor is the offices' **internal** spine, not a main corridor.

## Geometry

- 22 rooms, W01–W23 without W03 (drawing references, not official numbers).
  W01–W06 sit on C7's south side, W07–W18 form the outer south row, W19–W22
  the west end row, and W23 the south-west corner. W06 is a service room.
- Four internal passages: WI1, the east/west spine; WI2, the return
  vestibule to C7; WI3, the end return to W23; and WI4, the user-confirmed
  corridor (29 Oct) on the former W03 strip. WI4 runs from WI1 straight to
  C7, open full-width at both ends, with about 1.86 m clear.
- WI1's east end opens full-width onto C5 (about 2.18 m clear), as the user
  confirmed; photo 46 shows an opening at that end of the spine. The 0.22 m
  gap between the office shell and C5 is floored and has no walls.
- Five public portals from C7: WI2's entrance, WI4's open end, and the traced
  public-side doors of W02, W04 and W05; plus WI1's open end onto C5. W01's public leaf is hidden by the blue
  annotation, so no door is guessed.
- Each room has one internal door. These are amber **estimated** review
  openings, because the plan swings are unreadable. Office fronts on the
  passages are glazed; party and outer walls are solid.

Registration is the accepted core-relative fit from the full plan. The local
trace, in `config/povo2_west_offices.json`, maps the strip's 335 × 1090 pixels
to source-plan bounds 89.06–105 × 49–99.69. Wall thickness, perspective and
absolute dimensions are estimates.

## Corrections to the baseline

- **C8 ends at C7's south edge.** Its source band reached the photo edge
  (v 0–100), not a traced end, and photo 46 shows the office strip there. The
  10.8 m stub put two walls across WI1 and sealed W06. The other eight
  corridors are unchanged.
- **C7 runs straight past the main stair core to C5** (user correction,
  31 October). Photo 46 shows C7 running straight past the core to C5, about
  2.7 m wide. The registered core (east 11–20.5, north 18–26) is shared with
  floors 0 and −2 and with the installed stair door at (19.2, 18.0), and it
  overlaps the full-plan C7 band (north 17.69–20.46) by 2.46 m. The core
  can't move, so the whole C7 band moves south at its own width: north
  15.23–18.0, from its west end (east −14.79) to C5. Its north wall lines up
  with the core's south wall. The 29 October version kept the full-plan band
  and jogged south under the core (`c7_core_bypass`), which left an L and a
  1.4 m diagonal; the user confirmed that does not exist, and it is retired.
  The offices on C7 (W01, W02, W04–W06 and WI4) now end at its south wall,
  north 15.23, as W01 does in the user's Draw.io. WI2's top merges into C7's
  west end. The traced public doors keep their east positions on the new
  wall. W19–W23 and the south row are unchanged. The review proposal is in
  `exports/povo2_c7_straight_proposal_20261031/`.

## Outputs and checks

Run `py -3 -m tools.build_povo2_west_offices` to write
`exports/povo2_west_offices_20261029/`: `layout.json`,
`minus1_with_west_offices.{png,svg}`, `west_offices_detail.{png,svg}`,
`west_offices_shell.obj`, `west_offices_plan_trace.png` and
`registration.json`.

`py -3 -m unittest tests.test_povo2_west_offices` runs nine checks: the
room/passage set, WI4's straight connection from the spine to C7, WI1's open
east end onto C5, the C8
trim, passages free of crossing walls, the stair door reaching C5, straight
C7 (one clear band, reaches C5 and the stair door, offices closed along it
except at their openings), and floors −2/0 unchanged. A 0.1 m flood fill, with
walls inflated by 0.3 m, reaches every passage and all 22 rooms from C7.
Against Codex's original builder, the checks fail: W06 was unreachable and the
stair threshold was blocked.

## Playable campus integration

`tools/povo2_west_offices.py` now consumes this same trace in the main campus
generator, after the basement rebuild. It adds all 22 rooms, the four internal
passages, straight C7 and the southern C5 connection. The remaining full-plan
research wings are not imported. The retained stair/lift cores and both fixed
research-door pairs keep their existing positions.

The older first lab now extends south to straight C7's north wall (north
18.08 rather than 18.5); its northern boundary, east entrance and the 30 m gap
to the second lab stay in place, and its desks keep their positions. The
restricted research corridor and the CIBIO terrace beside it also reach C7.
The strip east of them (east −0.59 to 11, north 18–20.46) belonged to the
full-plan band and stays closed; its full-plan rooms are not built. The
basement routes follow straight C7 rather than running through the offices.
Tests: `tests.test_povo2_west_offices_integrated` checks C7 against the final
collision, end to end in both directions, and the lab reaching it.

The actual map receives wood floors, solid party walls, permanent glazed
fronts with horizontal privacy bands and metal frames, suspended ceilings,
diffusers, room signs, navigation seeds and radar room shapes. W01–W23 remain
drawing references, and the unreadable internal door offsets remain estimates.
No furniture is assigned to unidentified West Office rooms.

`tests/test_povo2_west_offices_integrated.py` checks every room against the
complete campus collision geometry: a standing 0.82 × 1.85 m player must reach
all 22 from the existing stair landing, and every entry, internal passage and
stair connection must pass in both directions. Existing basement tests also
check the retained labs, parking routes and restricted doors.

The final source run passes **333 tests**. The exported standard campus model
also passes the floor and general surface audits: **3,632 floor faces** and
**646,088 total faces**, with **zero overlapping pairs**. The reports
`integrated_floor_audit.json` and `integrated_surface_audit.json` in this
area's export folder include the audited OBJ's SHA-256. The deployed VMAP's
22 West room signs are checked in `integrated_map_entities.json`.
