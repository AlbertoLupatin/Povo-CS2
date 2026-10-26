# To do

Open actions, most urgent first. Tick them off here and record evidence in
[WORKLOG.md](WORKLOG.md).

## Windows: verify the breakable glass, automatic doors and stairs

All three are source-only: tested on Linux, never compiled or played.

- [ ] Pull `main`, then build: `python tools/cs2_campus.py`. Expect zero compile
      failures, then a package that passes `python tools/verify_cs2_package.py`.
- [ ] Hammer opens `trento_povo_campus.vmap` without errors and shows 316
      `func_breakable`, 54 `func_door` and 9 `trigger_multiple` entities.
- [ ] Glass: shoot one pane of each kind (room window, courtyard, stair, bridge,
      Povo 2 entrance sidelight, canopy, library/canteen wing). Each breaks with
      one bullet and plays glass gibs and sound.
- [ ] Glass: check the `glass01` texture scale on the panes, and lighting where
      glass used to be part of the baked model.
- [ ] Glass: the library/canteen wings reveal their playable interiors after panes break; no dark placeholder core remains.
- [ ] Doors: the Povo 1 entrance bank and all four Povo 2 banks (two outer, two inner) start closed,
      slide open about 2 m before you reach them, and close once nobody is near.
- [ ] Doors: the leaves slide over the sidelights without clipping the frames,
      and a player standing in the doorway is not trapped.
- [ ] Re-run the exterior walking checks (`python tools/playtest_povo_exterior.py`
      in a loaded solo session); both door banks must still pass.
- [ ] Bots: they don't path through intact windows, and they get through the
      entrance doors (touching a door also opens it).
- [ ] Stairs: walk up and down all four Povo 1 cores (three flights: left,
      straight, right) and the Povo 2 stair (upper floor to -2). Nothing snags
      at the landings, the floors are red, and the well railings hold.
- [ ] Lift: in the shaft right of the reception, climb the ladder from the
      ground floor and step off onto the upper ledge, then climb back down.
      Check the ladder surface lines up with the visible rungs.
- [ ] Lift: bots and the nav mesh handle the ladder (or ignore it safely).
- [ ] Povo 2 lift (beside the stair door): climb from -1 to ground and on to
      +1, stepping off at each opening; check the ladder lines up with the rungs.
- [ ] Stairs: railings show as continuous sloped handrails with bars (no
      floating rectangles) and stop you falling into the well.
- [ ] Performance: frame rate with about 320 extra entities stays acceptable.
- [ ] Update the README build figures (package size, test count) after a good build.

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
