# Povo 1 service blocks and entrance hall recheck — 29 October 2026

Rechecked before implementation, using the original 27 October photographs
10, 17, 19 and 20, the separately preserved `Povo 1 mappa piano1.png`, current
`config/povo1_campus.json`, and fresh in-memory output from
`tools.build_povo_campus.build_geometry`. No geometry/configuration, model
exports, compiled maps or game session were changed.

## Confirmed discrepancies

- **Floor 0, north inner block:** photo 19 explicitly labels a WC beside
  A217 and Aula Studio PC immediately below it in that photo's orientation.
  The separate classroom map agrees. Current generated `f_north_west` is an
  office/Locale in the WC position; `f_north_centre_male` is a furnished
  restroom spanning the study-room area. The next generated restroom is too
  extensive to preserve the intermediate rooms shown on the plan. The block
  needs a partition trace, not a label exchange.
- **Floor -1, four inner service corners:** photos 10 and 17 place WC/service
  cores on either side of A107 and A108. Plan 17 resolves the two corners away
  from the entrance as WC donne plus cavedio; the two hall-side corners contain
  WC uomini, an accessible WC H, paired lifts and service shafts. Current
  `g_north_west`, `g_north_east`, `g_south_west` and `g_south_east` are generated
  as office/Locale cells. Preserve the whole service-core arrangement when
  replacing them; these are not four uniform toilet rooms.
- **Floor -1, entrance hall:** plan 17 shows an open columned hall and two
  entrance vestibules near its end stair cores, with the facade recessed
  between them. Photo 10 independently shows the open hall. Current generated
  walls still enclose `g_outer_east1..3` as three offices in that hall span.
  Their removal is supported; the exact vestibule and facade dimensions
  still need tracing and exterior-photo registration before rebuilding them.

## Limits and implementation scope

The unnamed intermediate rooms on photo 19 must retain their visible boundaries
without invented functions. Photo 19 labels WCs generically; use the detailed
emergency plan 20 for sanitary partitions, door swings and any gender labels.
The retained photographs and unofficial map establish adjacency and shape,
not independently measured metre dimensions. Align the service blocks and
paired lift cores together before cutting floors or relocating the gameplay
ladder shaft. This recheck does not resolve that ladder's replacement location.

## Evidence

- [Fresh floor-0 walls versus photo 19](floor0_current_vs_plan19.jpg)
- [Fresh floor--1 walls versus photo 17](floor-1_current_vs_plan17.jpg)
- [Photo 19 north service-block detail](plan19_north_service.png)
- [Photo 17 entrance-hall detail](plan17_entrance_hall.png)
- [Current generated room records, including actual fit-out types](current_room_records.json)

The fresh wall drawings reuse the slice-rendering helpers from
`exports/povo1_layout_audit_20261028/wall_slices.py`, evaluated against the current
in-memory geometry. They compare proportional layouts side by side; they are
not perspective-corrected overlays or game screenshots. Original photos are
preserved unchanged under `data/reference/povo_photos/walk_2026-10-27/`.
