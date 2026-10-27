# To do

Open actions, most urgent first. Tick them off here and record evidence in
[WORKLOG.md](WORKLOG.md).

## 27 October photo-survey source revision

- [x] Restore Povo 1 -1 A1xx / 0 A2xx / +1 offices-and-bridge convention at provisional 4/7.6/11.2 m, with connecting stair segments.
- [x] Retain the active compact Povo 2 plan and two upper stair rises to the bridge; keep the full photographed plans separately reviewable.
- [x] Integrate observed amenities partitions/openings, source-axis stairs, open terrace and thin walkable canopy with standing clearance.
- [x] Update three-floor source previews and derive stair/bridge sound zones from current elevations.
- [x] Record photo 46 right lab: one corridor entrance, plus the red-star exit to the external courtyard.
- [x] Identify photo 4 as A103 from user clarification; scope the correction to the A103–A106 family.
- [ ] Refine photo 4 compass/metric registration, photo 46's blue-obscured north door position, and photo 37 floor-caption mismatch against user evidence.
- [ ] Improve metric/perspective registration and faint sanitary-core tracing; upper-library directory colours remain semantic zones.
- [ ] Record the survey revision's native build/package result in the worklog. Earlier evidence below describes earlier geometry; no post-build engine testing is requested.

## Windows: verify the breakable glass, automatic doors and stairs

Both initial Windows variants compile with zero failures and pass full CRC
verification. All 177 source tests pass after correcting both lift shafts.
Normal walking, room access and representative breakage checks pass on the first
standard build; the corrected lift rebuild is in progress. Evidence and exact
package scope are recorded in [WORKLOG.md](WORKLOG.md).

- [x] Pull `main`, then build: `python tools/cs2_campus.py`. Expect zero compile
      failures, then a package that passes `python tools/verify_cs2_package.py`.
- [x] Native runtime entity counts match 349 breakables, 54 sliding parts, 28
      rotating doors and nine sensors.
- [ ] Hammer opens `trento_povo_campus.vmap` without errors and shows 349
      `func_breakable`, 54 `func_door` and 9 `trigger_multiple` entities. The
      merged Windows source has 349 breakables instead of the cloud-only 316.
- [ ] Glass: shoot one pane of each kind (room window, courtyard, stair, bridge,
      Povo 2 entrance sidelight, canopy, library/canteen wing). Each breaks with
      one bullet and plays glass gibs and sound.
- [ ] Glass: check the `glass01` texture scale on the panes, and lighting where
      glass used to be part of the baked model.
- [ ] Glass: the library/canteen wings reveal their playable interiors after panes break; no dark placeholder core remains.
- [x] Normal walking through all nine automatic entrance banks.
- [ ] Doors: the Povo 1 entrance bank and all four Povo 2 banks (two outer, two inner) start closed,
      slide open about 2 m before you reach them, and close once nobody is near.
- [ ] Doors: the leaves slide over the sidelights without clipping the frames,
      and a player standing in the doorway is not trapped.
- [x] Re-run the exterior walking checks (`python tools/playtest_povo_exterior.py`
      in a loaded solo session); both door banks must still pass.
- [ ] Bots: they don't path through intact windows, and they get through the
      entrance doors (touching a door also opens it).
- [x] Stairs: normal walking up and down all four Povo 1 three-flight cores,
      Povo 2 from +1 to -2, and both library/canteen stairs.
- [ ] Stairs: visually check red floors and all well railings.
- [x] Normal walking through the PC/classroom corridor, aula lobby/aisle,
      basement locker/yard exit, bar and library reading rooms; continuous
      ascent and descent of the outdoor steel stair.
- [x] Representative room, bridge, stair, Povo 2 sidelight and library/canteen
      panes break after one AWP shot; restarting the round restores all 349.
- [ ] Lift: in the shaft right of the reception, climb the ladder from the
      ground floor and step off onto the upper ledge, then climb back down.
      Check the ladder surface lines up with the visible rungs.
- [ ] Lift: bots and the nav mesh handle the ladder (or ignore it safely).
- [ ] Povo 2 lift (beside the stair door): climb from -1 to ground and on to
      +1, stepping off at each opening; check the ladder lines up with the rungs.
- [ ] Stairs: railings show as continuous sloped handrails with bars (no
      floating rectangles) and stop you falling into the well.
- [ ] Performance: frame rate with about 320 extra entities stays acceptable.
- [x] Update the README build figures (package size, test count) after a good build.

## Release gates still open

- [ ] Two independent clients join and finish a match (first milestone).
- [ ] Full bot round with objectives and buy zones checked.
- [ ] Clean-install test from the published Workshop item; see
      [PUBLISH_AND_HOST.md](PUBLISH_AND_HOST.md).
- [ ] Resolve redistribution rights for reference material before a public
      Workshop listing ([DATA_SOURCES.md](DATA_SOURCES.md)).
- [ ] Balance, final textures, sound and a performance review.

## Next content

- [ ] Optional: replace the lift ladder with a moving platform (`func_door`
      moving up) once a quick CS2 test shows players ride it smoothly.

- [x] Implement the Povo 2 additions in source; Windows validation pending. See
      [Windows handoff](WINDOWS_PHOTO_ADDITIONS_HANDOFF.md). Original brief in [POVO2_INTERIOR_BRIEF.md](POVO2_INTERIOR_BRIEF.md):
      -1 exit stair, sunken yard and CIBIO offices, ground left corridor with
      classrooms and computer room, aula magna, B11x furniture.

- [x] Implement library/canteen interiors, sliding entrances and replacement
      of placeholder cores in the campus assembly. Windows validation pending;
      see [Windows handoff](WINDOWS_PHOTO_ADDITIONS_HANDOFF.md).
