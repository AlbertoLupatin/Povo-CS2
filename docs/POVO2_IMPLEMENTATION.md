# Integrated Povo 2 — 23 October 2026

**24 October update:** the [map adjustments](POVO_MAP_ADJUSTMENTS.md) rename the
classrooms B111–B114, move the boards to the south wall in world coordinates,
extend the tables to the hall midpoint and shorten the ground corridor by two
metres to end at the final classroom. The original checkpoint below is historical.

The approved entrance, reception, table corridor, B110–B113, basement and
parking are now assembled against the completed compact W1 staircase.
`compact_arrival` stays enabled: its bridge, alcoves, upper walls, guards,
doorway and tread tops retain their positions. The temporary closed lower
vestibule is opened into the new entrance hall. The staircase continues down
two more storeys to the basement and covered parking.

The standalone review in [POVO2_PLANIMETRY.md](POVO2_PLANIMETRY.md) retains the
user-approved drawing orientation. Placement rotates the lower plan by 180
degrees and shifts it to meet the existing east-facing stair exit. This
preserves all entrance-relative directions: reception ahead, corridor and
stair left, table-lined corridor right, classroom doors opposite those tables.
The classroom wall remains flush with reception. B110–B113 contain grey tiles
and a board on the player's right when entering, with no desks or seats.
The sealed reception uses opaque frosted glazing; office decoration is deferred.

The basement stair block remains at the start of its long corridor. Turning
right out of its door leads to the far end and the short branch. The parking
has grey rubberized asphalt, columns, bay markings, five simple car meshes
and a clear drive aisle. The entrance ends at a small exterior landing; the
outdoor third phase is still separate.

## Geometry and placement

All coordinates below are local metres, with east E and north N. Levels are
bridge 7.6, ground 4.0, basement 0.4 and parking -3.2. The three switchbacks
have twenty 18 cm risers and 30 cm treads each, with 2 m flights. These remain
gameplay estimates rather than survey measurements.

- The existing stair enclosure is E7–16.5, N14–26.
- Upper doorway: E16.5, N20. Lower doorways: E16.5, N22.
- Ground entrance is near E34.5, N33.5, facing west.
- Reception front and B-room corridor wall share E20.5.
- B110–B113 doors are at N39, 48, 57 and 66, entering westwards; boards are north.
- Basement long corridor: E16.5–20, N-6.5–26; short branch extends east at N-5.
- Parking footprint: E-1.5–34.5, N19.5–51.5.

Original solid stair undersides are hollowed while preserving their tread tops,
allowing a vertically stacked staircase with standing headroom. Floor openings
are cut only from landing plates. Threshold slabs bridge the stair enclosure
to the new lower floors. Old solid Povo 2 scenery is clipped only around the
occupied lower spaces; the completed upper arrival remains intact.

Lights, fixed labels, navigation seeds and four radar altitude sections are
included. The light-probe and lightmap-density volumes cover the northern
ground rooms and both basement floors. Overview bounds include all new areas.

## Source validation

All 113 Python tests pass. The existing Povo 1/upper/vestibule audit still passes
its 159 stations. The integrated Povo 2 audit passes 32 stations across the
three lower levels and 72 tread/landing samples across all three connections.
A regression compares the upper arrival geometry with the completed compact
source. Separate tests check the shared core, classroom/reception alignment,
board side, empty rooms and lower-floor connectivity.

```powershell
python -m unittest discover -s tests -q
python tools/audit_povo_campus.py
python tools/audit_povo2_integrated.py
python tools/cs2_campus.py
```

Implementation: `tools/povo2_integration.py`, fed by
`config/povo2_planimetry.json` and `tools/povo2_planimetry.py`. Integration is
selected automatically when the compact connection and lower plan are enabled.
The draft renderer remains independent, without a +1 panel.

## Build and runtime checkpoint

Build in progress: `build/gameplay/p2-integration-build.log`. The previous baked
package, source map, provenance and installed addon trees are preserved under
`build/p2-integration-backup-20261023-224751/`. Engine walking, visuals, reflection
bake and final package identity will be recorded after completion.
