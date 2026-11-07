# Latest campus build and verification — 6 November 2026

The latest frontage alignment and approved garden corridor are built, packaged, installed for `play_campus.cmd`, and tested in CS2. Existing facade work is retained.

## What was fixed

The earlier navigation-stall diagnosis was incorrect. Buffered compiler output left a nonfatal clipping warning as the last visible line. With live output, clearance clipping completed in **0.066 seconds**, and the long later step was identifiable as bomb-damage baking. Native compiler calls now use `-unbufferedio -allthreads`. A fresh normal-quality lighting bake also completed; the driver-level cause of the earlier stalled GPU retries was not established. No map geometry was changed during this build repair, and navigation clearance was not disabled.

The previously failing room-window assertion now checks the approved replacement facade glazing. The focused source patch is in `source-changes.patch`.

## Verified result

- Incoming source `46fe066`, merged revision `ecf711d3c1d2c8bade4013a88512a9bcd424992e`.
- **456 source tests passed** on this geometry; **12 relevant build-tool regression tests rechecked and passed** after the compiler-call change.
- Latest prepared map, source inputs, geometry exports and compiled models were fingerprint-verified before resuming compilation. The successful run reused those verified models and reran the complete native map compile, radar, packaging and CRC stages.
- **1,177 native resources compiled, zero failures.** Full map compile: **653.932 seconds**.
- Normal lighting quality 1, native 1024 atlas. Lighting: **114 seconds**. Visibility: **173.97 seconds**.
- **15,365 navigation areas**, normal clearance checks enabled. Bomb damage bake: **311.2 seconds**, 1,195,480 data points.
- **1,527 package entries; all entry CRCs passed.**
- Compiled collision: **18,944 basement-floor samples**, **36 column samples**, **36 fixed-door samples**, zero missing surfaces.
- **14 ordinary walking routes / 40 target waypoints passed** on a fresh solo load of the exact new VPK: garden exit, bridge arrival, B106/B108/B109 entrances, UP and DOWN exterior stairs, each in both directions.
- Both new garden exit door entities exist. Passage testing used those doors opened.
- **Seven normal-lit native captures inspected**: frontage, garden, lower corridor, exit doorway, B108, bridge and street-side grass. No missing-texture checkerboards or colored lightmap streaks appeared in those views. Existing blockout foliage and dark shadowing beneath the exterior stairs remain.

The initial UP-stair return trial stopped too close to the bottom tread for a full standing hull to settle on the lower floor. Its landing target was moved from N9.24 to N9.70, and both directions passed on recheck. No stair geometry changed. The first trial remains in `runtime-initial.json`; the recheck is recorded separately.

## Package

`trento_povo_campus.vpk` — **71,634,942 bytes**.

SHA-256: `9bb5bb4e8ccbf4daa9081fb71a4c74c288faefd968eb9ab9799b9fa85d5a58ce`.

The same bytes are in the repository's normal `build/package` location and the installed `trento_povo_campus_test` addon. Previous package backup: `build/build-fix-20261106/full-build/previous-standard.vpk`. The original local VMAP edit remains in its named Git stash. Source changes remain uncommitted; nothing was pushed or published to Workshop.

This is targeted runtime and collision verification, not a complete campus walkthrough, bot-play or multiplayer certification. CS2 was closed after testing.

