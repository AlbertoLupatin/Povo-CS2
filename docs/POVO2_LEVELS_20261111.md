# Povo 2 levels and reception stair — 11 November 2026

## Levels

Evidence and reasoning are in [Altitude_Corrections.md](../Altitude_Corrections.md), section 5b.

| Level | Before | Now |
| --- | ---: | ---: |
| −2 (parking, vestibule, both gardens) | −3.20 | −1.55 |
| −1 | 0.40 | 3.25 |
| 0 | 4.00 | 8.05 |
| +1 / bridge | 11.20 | 11.20 |

- −2 matches the flat garden DTM, at a median of about −1.55 in both gardens.
- −1 and 0 follow from 30 × 16 cm per basement storey. The 16 cm riser was iPhone-LiDAR measured on a −1↔−2 step.
- Floor 0 closes on the street DTM at the flush entrance, 8.08–8.29.
- Povo 1 and the bridge are unchanged. The 26 upper risers are therefore 12.1 cm. That storey is unmeasured; a 16 cm measurement would mean the bridge is about 1 m too low.

### How the levels are applied

`tools/povo2_levels.py` runs in `build_registered_geometry()` after the terrace and parking joins and before the lifts. The older Povo 2 passes still build at the old heights. This pass maps them through one monotonic height profile, so all modules move together.

- **Height profile:** each storey translates up to its door heads.
  - Basement storeys stretch from 3.6 to 4.8 m, so their ceilings are about 4.25 m high.
  - The 0→+1 storey compresses from 7.2 to 3.15 m, so floor 0 ceilings are about 2.7 m high.
- **What moves:** boxes, the Povo 2 exterior meshes, spec metadata, rails, lights and nav seeds.
- **Garage ramp:** keeps its road junction and now descends only to −1.55.
- **Garden DOWN stairs (south and north):** rebuilt with 27 risers of 17.8 cm on the same 0.3525 m treads (13 + 1.1 m landing + 14). Each now ends at E43.02 instead of E40.55. Keeping 20 steps would have meant 24 cm risers, which the walk audit rejects. The real count is unknown.
- **South UP stair:** keeps its 20 steps and plan, with the rise spread evenly. It tops out at the legacy south footway (4.0), so it only climbs 0.75 m. See "Open" below.
- **Exterior scenery:** unmapped scenery is carved out of the raised walking volumes. For example, the north pavement slab used to cover the north terrace run and now sits only 0.75 m above it.
- **Lift:** stops for the Povo 2 bank are now 3.25 and 8.05 (`config/povo_elevators.json`).
- **CS2 export (`tools/cs2_campus.py`):**
  - T starts stand on floor 0 at 8.05.
  - Garage nav points and lights use the profile.
  - Radar sections: basement2 below 0.85, basement1 from 0.85 to 3.60, and "lower" above that. Povo 2 −1 (3.25) and Povo 1 −1 (4.0) are only 0.75 m apart.

## Streets around Povo 2 regraded to the LiDAR

`tools/povo2_exterior_grade.py` runs right after the re-levelling.

- **Zones:**
  - Via Sommarive and the area east of it, north of N−10 and E49.5–110. The east zone fades in between N−10 and N0, south of where the legacy via used to drop into its 4.0 hollow. South of the garden edge (N9.1), the fade runs E40–51 instead.
  - North of Povo 2 from N101.5: the north garden rim, the north pavement, the roundabout and the village edges.
- **What moves:** every exterior object not owned by the Povo 2 storeys, by dz = smoothed DTM ground − legacy model ground.
  - The DTM uses ground cells only. The sunken gardens and terrace runs are masked out, and the DTM under the entrance canopy is anchored at floor 0 (8.05), because there it is interpolated.
  - Large ground slabs inside the zones become 2 m terrain sheets, 12 cm below the paving.
  - Walkable boxes are cut into 1 m tiles, other boxes into 4 m tiles.
  - Road strips at the junction are subdivided so their seams match.
- **Povo 2 street-level frontage:** the front walk, green strip, trees and lamps, the left terrace, the north pavement and the north garden rim/bend now follow the street (`STREET` in `tools/povo2_levels.py`) instead of the storey profile.
- **Result:**
  - The via and its footways are within about 0.5 m of the DTM, at 7.7–9.8 along Povo 2. They were 4 m too low.
  - The front walk runs from 8.05 at the entrance to 8.5 further north.
  - The north pavement climbs from about 3.1 to 6.8.
  - The FBK and village backdrop rise with the hill; FBK roofs now land within about 1 m of the LiDAR building surface.
- **South road east end (E40–51):** fades in gently, so it rises to the regraded junction at about 6 % more than before. The rest of that road is left for the altitude plan.

## Reception stair

The user's counts are 1→0 13+13, 0→−1 3×10 and −1→−2 3×10. The layout is the one approved in chat on 11 November.

- **Well:** inner E13.69–20.39 × N26.9–34.7. The former west strip, E11.11–13.69, is closed off.
- **Lanes:**
  - Two lanes, 3.8 m each, with a 0.2 m gap at N30.8.
  - 30 cm treads.
  - 2 m end landings; the far landing of 0↔+1 is 1.1 m.
- **Doors 0 and +1:** stacked on the east wall at N30.8.
- **−1 door:** south wall at the west landing, E14.69. Its leaves open onto the landing.
- **−2 door:** south wall at the east landing, E19.2, into the existing vestibule.
- **Descending from 0:**
  - Flight 1 on the left (south lane, west), then flight 2 east, then flight 3 west to −1.
  - Then three more flights, east, west and east, to −2. Door −2 is on the right.

## Verification (source only)

- Registered-geometry standing audit:
  - All 13 −2 stations, 20 −1 stations and 50 floor 0 stations are reachable.
  - 3,115 stair, parking and −1 route samples have support and headroom.
  - All garden routes pass.
- No CS2 compile or in-game walk has been done.

## Open

- **South footway near the UP stair:** about 1.3 m below the DTM. When it is regraded, retarget the UP stair top in `STAIR_GROUPS`.
- **South −1 deck strip (E−12..12, N8–9):** the DTM is about −1.3 there, open ground. That suggests a lightwell down to garden level rather than a deck at −1. It is not changed; it needs a photo or site check.
- **North terrace run (N112–113.7):** at 3.25. The regraded north pavement now runs from about 3.1 at its west end to 6.8 east, so the step between them grows eastward.
- **Measurements still wanted:** a 0↔+1 riser height, and the real step counts of the outdoor stairs.
