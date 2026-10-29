# Povo 2 −1 West Offices

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
- **C7 reaches C5 south of the main stair core.** Photo 46 shows C7 running
  straight past the core to C5, about 2.7 m wide. The registered core (east
  11–20.5, north 18–26) is shared with floors 0 and −2 and with the installed
  stair door at (19.2, 18.0), and it overlaps C7 (north 17.69–20.46) by
  2.46 m. That left C7 only 0.31 m deep under the core, a dead end. The core
  can't move, so C7 now jogs south under it at its own width: a
  `c7_core_bypass` band at east 9.5–20.5, north 15.23–18. It starts 1.5 m west
  of the core (`turn_metres` in the config), which leaves about 1.4 m
  diagonal clearance at the turn. It also covers the retained stair-door
  threshold. W01 loses its north 2.46 m (now north 10.43–15.23) and W02 a
  2.2 × 2.46 m corner (`excluded_for_c7_bypass`). A solid wall closes the
  offices along the band. The real offices' north wall is straight; this jog
  stands in for the core registration error.

## Outputs and checks

Run `py -3 -m tools.build_povo2_west_offices` to write
`exports/povo2_west_offices_20261029/`: `layout.json`,
`minus1_with_west_offices.{png,svg}`, `west_offices_detail.{png,svg}`,
`west_offices_shell.obj`, `west_offices_plan_trace.png` and
`registration.json`.

`py -3 -m unittest tests.test_povo2_west_offices` runs nine checks: the
room/passage set, WI4's straight connection from the spine to C7, WI1's open
east end onto C5, the C8
trim, passages free of crossing walls, the stair door reaching C5, the C7
bypass (clear, C7 reaches C5 and the stair door, offices closed along it), and
floors −2/0 unchanged. A 0.1 m flood fill, with walls inflated by 0.3 m, reaches every
passage and all 22 rooms from C7. Against Codex's original builder, the checks fail: W06 was unreachable and
the stair threshold was blocked. Without the bypass, the C7 → C5 check
fails.

This is review geometry only. The installed CS2 map has not been changed,
compiled or deployed.
