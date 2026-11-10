# Povo 1 bus-side paving and reception lift

The user screenshot matches the lower-plaza view recorded on 7 November,
with Povo 1 glazing on the left and the bus under the bridge to the right.
The old Povo 2 yard excavation had also cut the adjacent Povo 1 paving.
The remaining rectangle runs from E11.08 to E24 and N−20 to N−15.88.
A solid slab uses the existing exterior paving material and meets the
building and lower plaza at Z4. The adjacent apron crossfall varies by
up to 4.2 cm along the seam.

The first playable lift uses the existing Povo 1 shaft beside reception.
Its three landings are −1, 0 and +1 at Z4, Z7.6 and Z11.2. The native
`func_tracktrain` car follows three `path_track` stops and the small bundled
`povo1_lift.js` controller operates the two sliding leaves at each landing.
Press Use on the hall button marked CHIAMA to call the car, then press Use
on the desired floor inside. The car departs after both leaves close. An
obstruction reopens both leaves and the player can request the trip again.
The controller checks the car's alignment with the destination sill before
opening the doors. It accepts a new trip after both arrival leaves open.

The shaft's original position and openings are retained. The export replaces
the ladder and its projecting ledges with the car and level sills. The earlier
Povo 2 shaft was filled after the 29 October walkthrough. Povo 2's approved
−1 layout and the guarded parking lightwells retain their existing geometry.

The entity properties and I/O come from Valve's installed `game/core/base.fgd`
and the scripting API from the Workshop Tools demo. The car, doors and
controls are packaged with the campus.

## Standard package

The first normal-quality Windows build used a 1024-pixel lightmap atlas
and passed 477 source tests. Both new regressions passed in targeted runs.
The render audit found zero overlaps in 767,812 faces. The first solo run
found that CS2 kept the controller alive while recreating the train and
doors during a round reset. It also found that the lower call button was
partly inside the corridor wall and the train stopped about 5 Source units
short of the middle sill.

The final entity recompile reused the verified structural and paving
models. It resets the controller with the round, places the call buttons
on each corridor's exposed wall face, and aligns the car to the exact
path node on arrival. The 66,706,871-byte standard VPK passed all 1,570
entry CRCs. SHA-256
`727ffc5ded575110769a29e68dae47f8e847dd5d2d390b025d217ee1e245705e`.

The packaged collision passed 297 samples across the infill, 1,091
terrace/ramp/parking floor samples, and 18 clear lightwell shaft samples.
The basement regression also passed 18,944 floor samples, 36 column
samples and 36 fixed-door samples. The build logs are in
`build/handoff/20261109T210251397184Z/`. The collision reports and previous
standard VPK are in `build/povo1-lift-20261109/`.

## Solo CS2 verification

The final package passed four ordinary walks over ten waypoints across the
bus-side infill. Seven rides covered all six directed trips between the
three floors. Calls from each landing used the hall buttons, with the
empty landing doors blocking walking access until the car arrived. The
player selected each destination with Use and walked off at the destination
floor. This run used the usual warmup startup and a fresh local test addon.

The normal-lit views `bus_side_paving.png` and `lift_lower.png`, the final
entity compile log, and `runtime-report.json` are in
`build/povo1-lift-20261109/`. The verified standard package is in
`build/package/trento_povo_campus.vpk` for `play_campus.cmd`.
