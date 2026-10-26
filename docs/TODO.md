# To do

Open actions, most urgent first. Tick them off here and record evidence in
[WORKLOG.md](WORKLOG.md).

## Windows: verify the breakable glass, automatic doors and stairs

All three are source-only: tested on Linux, never compiled or played.

- [ ] Pull `main`, then build: `python tools/cs2_campus.py`. Expect zero compile
      failures, then a package that passes `python tools/verify_cs2_package.py`.
- [ ] Hammer opens `trento_povo_campus.vmap` without errors and shows 285
      `func_breakable`, 30 `func_door` and 5 `trigger_multiple` entities.
- [ ] Glass: shoot one pane of each kind (room window, courtyard, stair, bridge,
      Povo 2 entrance sidelight, canopy, library/canteen wing). Each breaks with
      one bullet and plays glass gibs and sound.
- [ ] Glass: check the `glass01` texture scale on the panes, and lighting where
      glass used to be part of the baked model.
- [ ] Glass: the library/canteen wings show their dark core through broken panes.
- [ ] Doors: the Povo 1 entrance bank and all four Povo 2 banks (two outer, two inner) start closed,
      slide open about 2 m before you reach them, and close once nobody is near.
- [ ] Doors: the leaves slide over the sidelights without clipping the frames,
      and a player standing in the doorway is not trapped.
- [ ] Re-run the exterior walking checks (`python tools/playtest_povo_exterior.py`
      in a loaded solo session); both door banks must still pass.
- [ ] Bots: they don't path through intact windows, and they get through the
      entrance doors (touching a door also opens it).
- [ ] Stairs: walk up and down all four Povo 1 cores and the Povo 2 stair
      (upper floor to -2). Flights fill the well, the mid landing spans it, and
      nothing snags at the top, bottom or turn.
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

- [ ] Model the library and canteen interiors in front of Povo 1 from
      [LIBRARY_CANTEEN_BRIEF.md](LIBRARY_CANTEEN_BRIEF.md) once photos arrive,
      add their sliding entrances with `door_bank`, then remove the
      placeholder cores (`_core` boxes in `tools/build_povo_exterior.py`).
