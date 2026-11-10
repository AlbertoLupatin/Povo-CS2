# Exterior repairs verified in CS2

The standard campus package was rebuilt and installed for `play_campus.cmd` on 7 November 2026.

- The Povo 2 road bend now has joined road and sidewalk sections. A paved apron closes the corner and meets the restored descending sidewalk at its grade.
- The bus is back at its original broadside position (E25, N−5, Z4). Its shell, trim and four wheels are intact. The aisle was walked in both directions, and the side collision stopped the player at the visible body.
- The shrub uses clustered leaf geometry with three shades and vein textures.
- The upper roadside handrail runs to the garden end and wraps the corner along the descending sidewalk. The UP stair opening remains accessible. A collision test stopped the player before the drop.
- The red Povo 1 stair descends from the street-facing wing edges at E52 to their Povo 1 ends at E36. It fills the passage between the canteen and library under the glass canopy. The former stair footprint is now part of the lower landing.

The full suite passed 458 tests before the final verge-grade correction. All 15 frontage tests passed after that correction. The native build used normal lighting with a 1024 atlas, and all 1,539 VPK entries passed CRC verification. Eight in-game routes and 36 waypoints passed, including the road junction, sidewalk, bus aisle and red stair in both directions. Two collision checks passed. Six normal-lighting captures were reviewed. The nearby lower recess behind the bus is visible in the bus capture and is separate from the repaired road junction.

Package SHA-256 is `35fd0ebaf899a4fb9da88f3bea0c762fffe0f85b8664d66ea193edfb18a73eaf`. The previous package is backed up at `build/exterior-repair-20261107/previous-standard.vpk`. Build and package logs are in `build/exterior-repair-20261107`.
