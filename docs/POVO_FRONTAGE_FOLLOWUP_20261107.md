# Povo campus frontage follow-up

The bridge-facing approach is from east to west. The left side is Povo 1, and the right side is Povo 2. The bus moved 1.8 m north, toward the right in that view. Its shell, trim, wheels and collision share that translation.

- The Povo 1 and Povo 2 entrance banks use the room-wall glass tint and 0.32 pane opacity. The sidelights, sliding leaves and entrance triggers remain in place.
- The Povo 2 corner apron follows the descending Via Sommarive sidewalk through to the lower forecourt. The sidewalk and paving also join across the narrow gap on the east edge of the forecourt. The −2 garden remains open, with a guard along its east edge.
- The widened strip on the Povo 1 side is paved. The library-side street rail continues along the retaining edge, with a break for access to the bridge apron. The narrower planting beside the library stair and the Povo 2 street guard are retained. Paving was restored along the former cut in the Povo 1 lower plaza. A separate recess remains west of that plaza at the Povo 1 facade.
- The leftover ground slab was cut back to the edge of the −2 garden. The former 3.77 m-high concrete return by the −1 West exit was cut back to terrace level.
- The −1 outdoor corridor remains at Z0.4 m. Between the street and the corridor grate, the planted bank drops 3.0 m over 5.0 m (31°). A low retaining toe takes up the remaining difference, up to 0.72 m. This is a fitted game grade from the existing road and terrace levels. The main interior floors and the UP and DOWN stair connections retain their prior elevations.

## Verification on 7 November 2026

The standard package was built with `build_campus.cmd --optimize-import --lightmap-max-resolution 1024`. All 459 source tests passed. The Povo 2 frontage audit passed with 3,267 route samples and 272 bridge samples. All 1,539 VPK entries passed CRC verification. The package is 73,166,943 bytes. Its SHA-256 is `a6054b969f33d68e19b3dfa158b2e1c2e9ac14a001eb6b17e4dc45d4737648f5`.

The fresh solo CS2 session passed 16 bidirectional walking routes with 68 waypoints across the Povo 2 ramp and sidewalk, Povo 1 widened sidewalk and lower plaza, bus aisle, automatic entrances and −1 outdoor stair. Three collision checks stopped the player at the bus shell and the two roadside rails. Eight normal-lit captures were inspected, including closed glass at both entrances and the two cleared exits.

Build logs and package verification are in `build/handoff/20261107T104630573165Z/`. The preceding package is backed up at `build/frontage-followup-20261107/previous-standard.vpk`. The native runtime report is in the same checkpoint directory.
