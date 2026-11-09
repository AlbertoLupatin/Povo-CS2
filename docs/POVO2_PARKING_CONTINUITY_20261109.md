# Povo 2 parking and ramp continuity — 9 November 2026

The user confirmed that the existing ramp placement is correct. It belongs to
the parking, which continues to the far end of this side of Povo 2 and can be
seen through the existing openings in the external −1 terrace.

The final registered assembly now joins the stair-accessed parking to the
larger ramp-served garage, filling their former 1.7 m separation and opening
the common perimeter walls. The original ramp mouth, heading, width and grade
are retained. A frontage sidewalk that crossed the ramp mouth is cut away in
both the render and collision meshes.

The garage floor, roof and side walls continue from the previous north limit
(N112) to the registered north terrace end (N115.895). Navigation seeds cover
the new connection and far end. Asphalt fills the small strip beneath the
terrace that extended beyond the old inner parking slab.

The terrace's existing user-marked opening intervals come from
`config/povo2_minus1_terrace.json`, translated by the same N8.8 registration as
the building. Their shafts are cleared through exterior roofs, proxy ground,
visual meshes, collision meshes and the old parking ceiling. The alternating
covered sections retain their roofs. Existing −1 rooms, passages, doors,
stairs, garden and terrace solids are preserved.

The ramp and apron already used `exterior_asphalt`: the same stock asphalt
texture as the road, with the native asphalt collision surface. They retain
that finish. Existing dimensions are fitted source dimensions, not a new survey.

Implementation: `tools/povo2_parking_continuity.py`, called after frontage
registration by `build_registered_geometry()` in `tools/build_povo_campus.py`.
The earlier unregistered exterior study remains a construction-stage view;
use the registered assembly for the final parking.

Validation covers supported standing routes down the ramp, across the former
gap and to the far end; unobstructed views down to asphalt through each terrace
opening; retained cover; ramp placement and asphalt. The registered-frontage
regressions cover existing room/floor registration, stairs and garden access.
A comparison against the pre-change registered geometry also preserves all
4,256 basement, ground, internal-stair and garden boxes exactly.

This is a Linux source revision. The Windows Workshop Tools package has not
been compiled or playtested in CS2 in this environment.
