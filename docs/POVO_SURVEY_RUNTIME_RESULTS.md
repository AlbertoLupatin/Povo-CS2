# Standard map repairs and native verification — 27 October 2026

The Povo 2 and canteen stair collisions are fixed. The rebuilt standard package
has passing evidence for all **50 route objectives**, **14 feature checks**,
**11 controlled local-match checks** and **219 source tests**.

The complete walking sweep passed 49/50. Its remaining failure checked the
last tread of the Povo 2 intermediate landing while the standing hull still
spanned adjacent risers. The harness now checks the full floor landing; both
directions passed on retest with the same 25 cm floor-height tolerance. The
[combined coverage](../exports/povo_campus/runtime/stair_repair_20261027/coverage-summary.json)
records the source run for every objective. The original failed aggregate is
preserved unchanged; this is combined coverage, not a passing single sweep.

## Repairs

Povo 2 inherited solid geometry from the Hammer template sky room. Its original
768/640-unit brush edges and solid floor at Z6.9088–10.16 m intersected the upper
stairs. Mesh transform scales had not resized the compiled brush. The campus
generator now resizes its actual vertices, placing the floor below the garage
and the walls outside the campus. Compiled world-physics inspection confirms
that the old obstructions are absent. All four upper-stair directions pass.

The canteen's independently fitted photo-plan walls left upper WC and lower
atrium fragments inside the stair turn. The generator now clears the full
standing hull between tread centres, across the landing and while stepping
onto adjacent risers. A regression reproduces the original overlap and passes
after the fix. Both canteen stair directions pass in the focused check and the
complete sweep.

The walkthrough also retains full Povo 2 floor-landing checkpoints, the library
route around its traced partitions, and the basement route around the lift,
stair enclosure and CIBIO glazing. Both lift ladders reach the 11.2 m upper
floor and dismount with a normal jump after climbing 0.65 m above the floor.
These are jump-assisted dismount checks, not automatic walk-offs.

## Build and evidence

Native model compilation: one compiled, zero failed. Native map compilation:
673 compiled, zero failed. Five radar sections and 12,480 navigation areas were
generated. The standard VPK contains 942 entries / 61,507,512 bytes, with all
942 CRCs verified. SHA-256:
`e08a52bbf22d4b9e668d88cd5becbb8375f34831393fb1996dc59073332af3c4`.

The [evidence index](../exports/povo_campus/runtime/stair_repair_20261027/README.md)
links the complete reports, raw console/compiler logs, source tests, compiled
collision inspections and repaired-stair screenshots. CS2 was freshly launched
on this package in the isolated test addon. The staged and source package
hashes match; native status itself checks the map name rather than hashing
already-loaded map bytes. The final session is solo exploration at the Povo 1
entrance, with noclip disabled and scripted inputs released.

The Duplicate Bone model-import warning persists. The compiler also retains
one unconnected Povo 2 ladder-top navigation link at `(-571.653, 860.236, 444)`;
passing player ladder movement does not prove autonomous bot traversal. The
local match checks cover purchases, planting restrictions, planting, native
defusing and round completion. Independent-client multiplayer, competitive
balance, and winter remain untested. Photo registration remains provisional.

## Earlier package

The previous package (`2edab45d…`) passed 36/50 in its original sweep and 44/50
objectives across follow-ups. Its [original engine evidence](../exports/povo_campus/runtime/survey_20261027/engine/README.md)
remains unchanged. The old VPK is preserved locally in
`build/survey-repair/pre-repair/trento_povo_campus.vpk`; compiled VPKs are ignored
by Git. No Workshop upload was performed.
