# Surface textures adopted from the remake

RoanS77's branch `shaders-mod` (commit `97769b5`, folder `remake/`) rebuilds the
campus from scratch in a separate addon. Its look comes from a few photo-matched
procedural textures, well-chosen stock CS2 materials and stock tree models. This
change brings those choices into the `trento_povo_campus` pipeline. It doesn't
touch the room layout, collision or playable geometry. The only geometry removed
is the render-only placeholder trees in the outer scenery.

## What changed

| Campus material | Now uses | From |
| --- | --- | --- |
| `stair_red` | custom `red_floor` (red rubber, P007, P040–P045) | `remake/tools/materials.py` |
| `floor_circulation` | custom `terrazzo` (P036–P039) | same |
| `floor_p2_tile` | custom `cream_tile`, 40 cm tiles (P074–P114) | same |
| `exterior_stone` | custom `beige_stone`, 1.3 × 0.65 m slabs (P013, P024, P057) | same |
| `door_black` | custom `anthracite` (P040, P041, P045) | same |
| `exterior_asphalt`, `floor_p2_asphalt` | stock `asphalt/hr_c/hr_asphalt_001` | `remake/tools/build_site.py` |
| `exterior_grass`, `floor_yard_grass` | stock `de_overpass/nature/wild_grass_1` | same |
| `exterior_concrete` | stock `concrete/hr_c/hr_concrete_floor_001` | same |
| `exterior_paving` | stock `cs_italy/ground/sidewalk_concrete_slabs_1` | same |
| `wall` | stock `ar_baggage/baggage_plaster_wall_smooth_01` | `remake/tools/building.py` |
| `ceiling_panel` | stock `ceiling/hr_c/hr_ceiling_tile_001_color` (60 cm tiles) | same |
| `floor_wood` | stock `de_train/.../hrts2_wood_floor_boards_01` | same |

| Povo 1 perimeter walls, outside faces | custom `beige_stone` (new `stone_facade`) | `remake/tools/building.py` facades |
| Via Sommarive sidewalks | custom `dark_paving` (new `exterior_dark_sidewalk`) | `remake/tools/build_site.py` |
| Povo 1 east entrance stair | custom `red_paving` (new `exterior_red_paving`) | same |
| Outer scenery tree belts | stock maple tree props | `remake/tools/build_site.py` `TREES` |

Every other material keeps its flat-colour finish. The mapping lives in
[`config/povo_textures.json`](../config/povo_textures.json): delete a line to
revert one surface, or add one to adopt another. The remake's `frosted_glass`
and `aluminium` generators are ported but unused.

### Render-only splits of shared materials

Some surfaces share a material with unrelated parts. The last three surface rows
above are split off at render time only. The geometry, collision, physics
surfaces and every box-level tool still see the original materials.

- **`facades`**: the outside face of each Povo 1 perimeter wall
  (`academic_*_outer_*`, material `wall`) becomes `stone_facade`. A face counts
  as outside when it spans the wall's thickness and faces the nearest edge of
  the building outline. Interior faces, window reveals, tops and ends keep
  plaster. On the current source, 280 faces qualify, all exactly on the outline.
- **`renames`**: `exterior_road_front_footway_*` and
  `exterior_edges_south_sommarive_walk_*` paving become `exterior_dark_sidewalk`.
  The campus-side `road_front_campus_paving` stays light, as in the remake.
  `exterior_entry_stair_*` (orange) becomes `exterior_red_paving`; the lockers
  and facade recesses keep orange.

The new names keep the wall's or the `campus_exterior_` prefix's priority in
the coplanar-overlap resolver. The dark sidewalk also stays in the probe-lit
pavement finish and the floor-surface audit.

### Edge trees

`edge_trees` replaces the octagonal placeholder crowns of the outer scenery
belts (`tree_rows` in `config/povo_edges.json`, 8–11 m) with stock CS2 tree
props. `cs2_campus.add_edge_trees` places one non-solid `prop_static` per tree.
The model comes from the remake's height bands: urban small up to 6 m, maples up
to 12 m, poplars above. Model and yaw are chosen from the position.
The placeholders had no collision, so the props are not solid either. The
roadside ginkgos (an approved, species-specific asset) and the courtyard
planters keep their own art. Set `"enabled": false` to bring the placeholders
back.

## Texture scale

The campus OBJ maps every surface at one texture repeat per 0.6 m. The remake's
textures and the stock materials are drawn for one repeat per 1024 texels at
4 texels per Hammer unit. At the remake's 1.25 gameplay scale, that is about
5.2 real metres (2.6 m for the 512-texel ceiling tile).
`render_obj` in `tools/build_povo_campus.py` now asks `povo_textures.repeat_metres`
for each material, so these surfaces repeat at that real size and slabs, tiles
and boards keep their real dimensions. Untextured surfaces keep 0.6 m, so
their UVs are unchanged.

## Files

- `tools/povo_textures.py`: the ported generators (same recipes and colours; the
  noise is now exactly periodic and each texture has its own seed), the
  material mapping and the per-material repeat. `python tools/povo_textures.py`
  rewrites the textures on their own.
- `cs2/content/trento_povo/materials/trento/povo/campus/textures/`: the seven
  textures in use, written by every campus build (under 1 MB in total).
- `tools/povo_pavement_lighting.py`: the probe-lit pavement finish model uses
  the same material sources as the structural model.
- `tools/povo_edges.py`, `tools/cs2_campus.py`: edge trees as props.
- `tests/test_povo_textures.py`.

## Still to verify on Windows

These checks need the CS2 Workshop Tools and have not been run:

1. Rebuild with `build_campus.cmd` (or `python tools/cs2_campus.py`). The committed
   `exports/povo_campus/*.obj` and `models/povo/*.vmdl` are regenerated by that
   build. They were not regenerated in this change, because the Windows
   pipeline post-processes them and writes CRLF line endings.
2. Check in game that the stock materials compile into the model and appear:
   Roan's builds load them from native Hammer meshes, while here a ModelDoc model
   references them.
3. Compare against the photos: facade stone, terrazzo corridors, Povo 2 tiles,
   the red stairs, grass, asphalt, ceilings, the Via Sommarive sidewalk.
4. Check that the edge tree props appear upright at ground level and at a
   plausible size. The remake uses them unscaled at its 1.25 scale, so here they
   may read about 25% larger relative to the buildings. Also check they cast
   acceptable baked shadows. In winter they stay green, like the ginkgos.
5. Check the package size and that `verify_cs2_package.py` passes. Stock
   materials and tree models ship with CS2, so only the seven custom textures
   are added.

Footstep sounds are unchanged: they come from the collision meshes' physics
groups, not from the render materials.
