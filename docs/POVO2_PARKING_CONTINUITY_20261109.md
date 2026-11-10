# Povo 2 parking and ramp continuity — 9 November 2026

The user confirmed that the existing ramp placement is correct. It belongs to
the parking, which continues to the far end of this side of Povo 2 and can be
seen through the existing openings in the external −1 terrace.

The final registered assembly now joins the stair-accessed parking to the
larger ramp-served garage, filling their former 1.7 m separation and opening
the common perimeter walls. The ramp retains the installed 5.5 m width,
the flat approach to N1 at Z3, and the descent to the portal at N30/Z−3.2.
The terrace integration already clears the crossing footway from both meshes.

The garage floor, roof and side walls continue from the previous north limit
(N112) to the installed north terrace end (N113.71). Navigation seeds cover
the new connection and far end. Asphalt fills the small strip beneath the
terrace that extended beyond the old inner parking slab.

The shafts of the two guarded lightwells use the bounds from the installed
[terrace revision](POVO2_TERRACE_INTEGRATION_20261108.md). Exterior roofs,
proxy ground, render and collision meshes and the old parking ceiling are
cleared within those bounds. The earlier sketch's southern opening crosses
the current terrace join beside the driveway. The continuous walking deck,
covered sections, −1 rooms, passages, doors, stairs and garden retain their
installed geometry.

The ramp and apron already used `exterior_asphalt`: the same stock asphalt
texture as the road, with the native asphalt collision surface. They retain
that finish. Existing dimensions are fitted source dimensions, not a new survey.

The Windows checkout integrates `a3d82ff` after the local terrace assembly in
`build_registered_geometry()`. `tools/povo2_parking_continuity.py` uses the
same registered bounds as the walking deck and guardrails.
The earlier unregistered exterior study remains a construction-stage view;
use the registered assembly for the final parking.

Validation covers supported standing routes down the ramp, across the former
gap and to the far end; unobstructed views down to asphalt through each terrace
opening; retained cover; ramp placement and asphalt. The registered-frontage
regressions cover existing room and floor registration, stairs and garden access.

The upstream Linux revision was source-verified. See the Windows verification
record below for the integrated package status.

## Windows build verification

The standard campus was rebuilt with the Windows campus pipeline, normal-quality
lighting and a 1024-pixel atlas. All 477 source tests passed. The render audit
found zero coplanar overlaps across 768,126 faces.

The 75,121,285-byte `trento_povo_campus.vpk` passed all 1,557 entry CRCs.
SHA-256 `3341db6e96351b5d9b5f214c05477ca09bff4fe5b3563c9d4671353359a0ded9`.
Compiled collision passed 1,091 terrace, ramp and parking floor samples and
18 unobstructed lightwell shaft samples. The compiled basement regression
passed 18,944 floor samples, 36 column samples and 36 fixed-door samples.

The build and package check logs are in `build/handoff/20261109T182810197835Z/`.
The collision reports and previous standard VPK are in `build/parking-20261109/`.

## CS2 playtest and local package

The exact CRC-verified package loaded in a fresh solo addon. Ten normal-lit
views showed the ramp, joined parking, north end, and both lightwells from the
terrace and the garage. The ramp and portal, parking join, far end, and both
terrace joins passed ordinary standing walks in both directions. The final
result covers 10 routes and 44 waypoints. Three terrace walks were rechecked on
the same VPK using the south strip's centreline and the turn east before the
curved retaining wall. The initial and recheck reports are in
`build/parking-20261109/` and `build/parking-recheck-20261109/`.

The verified standard VPK is available in the local workspace at
`build/package/trento_povo_campus.vpk`. Run `play_campus.cmd` to load it.

## Steam Workshop update

Workshop Manager confirmed the upload to the existing [Povo campus - friends
playtest](https://steamcommunity.com/sharedfiles/filedetails/?id=3827904476)
item on 9 November 2026 at 20:12 Rome time. The submitted visibility was
Friends only and the selected mode tags were Classic and Wingman. The staged
VPK matched the verified build's SHA-256 and passed all 1,557 entry CRCs.
The receipt is in `build/workshop/snapshot.json` and the prior staged package
is backed up in `build/parking-20261109/workshop-before-update/`.
