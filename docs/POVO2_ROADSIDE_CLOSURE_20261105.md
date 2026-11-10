# Povo 2 roadside closure — 5 November 2026

The user reported, from an in-game screenshot on the sloped front-road sidewalk
looking west toward the bridge:

1. many missing parts around the Povo 2 south corner;
2. Povo 2 −1/−2 structure visible from the road where it should not be,
   while Garden −2 itself should stay visible;
3. the metal fence separating the road from Povo 2's outdoor terrace missing
   and buggy.

Only the standard (non-winter) map is in scope for this pass.

## Cause

- `tools/povo2_drawio_entrance.py` (31 October) deletes the street-garden earth
  embankments `exterior_p2_garden_slope_*` that the playtest repair had built,
  and never replaced them. The street-level garden between the −1 terrace/DOWN
  stair and Garden −2 became open voids down to the context underlay
  (about 317 m² of unintended holes in the area).
- Garden −2's south retaining wall still stopped at the old −1 passage level
  (z 0.4); its west side was open between N8.75 and N11.25; the −2 office garden
  approach and the −1 roofs west of the garden had no cover.
- Nothing separated the bridge-road footway (north edge N−0.6, z 4–7.7) from the
  −1 terrace and DOWN stair (z 0.4 to −3.2). A 2 m piece of footway at E50–52 was
  missing. The terrace guard-rail clips were the only thing a falling player hit.
- Remnants of an obsolete Povo 1 street ramp (`exterior_povo1_street_grade`)
  and its 5 cm guard bars floated above the street garden and Garden −2.

## References used

- Street photos walk 2026-10-23 photos 24–26 (fence on concrete kerb with a
  handrail, along the front road and the bridge-road corner).
- WhatsApp photo 2026-10-29 2.16.20 PM (2): bridge road, grass verge, grey
  grating fence on a concrete wall in front of Povo 2.
- Walk 2026-10-26 photos 19–20: Garden −2 from above, retaining wall with the
  fence on top, stainless guard rail on the terrace edge.
- The aerial images embedded in `data/reference/user_feedback/2026-10-28/Povo2 Gardens.drawio`:
  road → street-level grass → fence/drop → Garden −2.

## Change

New pass `tools/povo2_roadside_closure.py`, run after the A–D exterior fills:

- **Street garden restored:** solid earth with a lawn at street level (z 4.0)
  across the void strips (E31.88–56.7, N0.13–8.75 around the approach). The
  retained paved strip at E55.5–56.7 gets a solid body.
- **Garden −2 walls:** south retaining wall raised to z 4.0; the open west
  end (N8.75–11.25) closed. Guard rails added on the new south/west edges and
  where the lawn meets the DOWN stair and lower landing.
- **Cover:** a ground-level concrete cap (z 3.5–4.0) over the open −1 roofs
  between E20.4 and E37.8, only where no ground-floor slab or wall already
  exists. The −2 office garden approach becomes a closed passage (walls and
  ceiling at z −0.1) behind its existing portal and doors.
- **Road-edge wall:** a concrete retaining wall flush with the footway grade from
  E8.34 to E56.7 (leaving the UP-stair channel E20.34–23.16 open), with a 0.35 m
  kerb. The missing E50–52 footway piece is filled.
- **Fence:** grey grating fence 1.7 m high on the kerb along the bridge road and
  around the corner along the front-road sidewalk to N28.3 (end of the entrance
  courtyard). It has posts every 2 m, four rails and flat bars every 0.1 m.
  The bars are visual only; one continuous invisible barrier per run carries
  collision, so there are no hundreds of tiny physics hulls.
- **Remnants removed:** the floating ramp piece and guard bars.

The approved Povo 2 −1 layout is unchanged: rooms, terrace, UP/DOWN stairs,
lower approach, Garden −2 and their routes. Fence/kerb heights and bar spacing
are photo estimates. Metric registration of the street garden is unchanged.

## Evidence

Source renders (three.js of the exported OBJ, not CS2 captures) in
[exports/povo2_roadside_closure_20261105](../exports/povo2_roadside_closure_20261105):
the user's view, overview and road corner before/after, and the top-down
hole maps (red = unintended pit below z 3.6) before and after.

- 389 source tests pass (8 new in `tests/test_povo2_roadside_closure.py`).
- The render-surface audit finds 0 coplanar overlaps in `povo1_campus.obj`
  (672,261 faces) and `povo1_campus_paving.obj`.
- The remaining flagged area west of E11 (N12–20) is outside this pass.

Not done: no native CS2 compile, lighting bake, walking test or screenshot.
The committed `exports/povo_campus` OBJs predate this change. Rebuild the
standard package on Windows with `build_campus.cmd` (default season
`standard`). The winter variant was intentionally not rebuilt.
