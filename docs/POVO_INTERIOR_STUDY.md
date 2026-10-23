# Povo 1 room and circulation study

This is a separate OBJ study of two Povo 1 levels. It prepares editable floor,
courtyard, entrance, classroom and corridor geometry while the user collects photographs.
It is **not installed by `cs2_project.py deploy`**, does not replace the current
solid campus massing, and does not add a playable route to the Wingman arena.

## What is built

- A ground level and an upper level in the campus's existing local-metre frame.
- Floor slabs that leave the courtyard open on both levels.
- Four reserved stair openings in the upper slab, with an assumed landing margin.
  The ground slab remains under these regions. Stair flights are not built yet.
- Different room/corridor layouts on the two levels, traced approximately from
  their respective plan images: A101–A110 downstairs, A201–A224 and LAB upstairs.
  Study areas, toilets, reception and other service spaces still need subdivision.
- Outer/courtyard walls and individual classroom walls. Collinear shared walls
  are merged before door gaps are cut, avoiding duplicate walls between rooms.
  Doorways are gaps below lintels, without door leaves or gameplay interaction.
- Ground entrance opening only. Upper-floor access is provisional and checked
  from an assumed stair-landing approach; no upper exterior entry is invented.
- Two generated tile placeholders for general floor/circulation, plus original
  wood-look and perforated-ceiling textures for the A224 pilot. Repeating metric
  UVs use the provisional 0.6 m repeat. Reference photos establish the appearance
  family; texture patterns and exact colours are approximate.

The study currently has 563 closed component boxes and 6,756 triangles, including
a furnished A224 pilot with a ceiling, fixtures and west-facing window opening.
It has no functional breakable glass, navigation, lighting bake or CS2 entities.
The source mesh has not been compiled or traversed in the game.

## Assumptions and source limits

`config/povo1_interior_study.json` keeps all adjustable assumptions together:

| Parameter | Current provisional value |
| --- | --- |
| Ground reference elevation | 374.0 m above the source vertical datum |
| Upper level relative height | +3.6 m |
| Slab thickness | 0.22 m |
| Wall height / thickness | 2.9 m / 0.18 m |
| Door opening height | 2.15 m |
| Floor tile repeat | 0.6 m |
| Stair-opening inset inside registered stair region | 1.5 m |

These are modelling assumptions. The ground elevation is not established by a
site measurement; the upper offset is not a measured storey height. Each room
keeps its approximate source-pixel footprint and its door side. Room shapes are
rectangular approximations, not a survey. Door widths and centres are provisional. The available plans do not establish stair-flight
dimensions or landing elevations.

The builder uses `config/povo1_plan_alignment.json` and verifies the referenced
plan image hashes. That alignment fits an approximate 47 x 83 m core footprint.
It maps source image right to north and down to east, then converts to local
east +X / north +Y coordinates. The source numbering conventions remain attached
to each level in provenance. See [the plan review](POVO_ARCHITECTURE.md).

The source repository describes its maps as unofficial, and no redistribution
licence was established in the inspected tree. Keep the downloaded maps and
this study's assumptions/provenance with the working references. No plan image
pixels, logos, or map annotations are used in the generated floor textures.

## Rebuild and inspect

The generator and its unit tests use the Python standard library:

```sh
python tools/build_povo_interior.py --force
python -m unittest discover -s tests -v
```

Outputs go to `exports/povo1_interior_study/`:

- `povo1_interior_study.obj` and `.mtl`: geometry and material assignments.
- `floor_room.png`, `floor_circulation.png`: original generated tile patterns.
- `floor_wood.png`, `ceiling_panel.png`: original generated pilot finish patterns.
- `classroom_A224.png`: optional room/ceiling cutaway and finish swatches.
- `review.svg`: labelled north-up room/corridor/courtyard diagram at the footprint's aspect ratio.
- `provenance.json`, `CREDITS.txt`: inputs, source image hashes, parameters, levels,
  statistics and output hashes.

Keep the OBJ, MTL and texture PNGs together when reviewing in a modelling tool.
The origin is `(666250, 5103800, 370)` and the geometry remains in metres.

Optional previews use the existing numpy/matplotlib renderer dependencies and
ImageMagick for the SVG raster:

```sh
python tools/render_interior_preview.py
python tools/render_classroom_preview.py
magick -background none exports/povo1_interior_study/review.svg exports/povo1_interior_study/review.png
```

`preview.png` renders the exported mesh with flat material colours and shows the
actual generated texture swatches separately. Neither review is a game screenshot.

The generator rejects disconnected corridor rectangles, circulation/rooms crossing a
reserved void, overlapping room footprints, out-of-wall door gaps, insufficient floor spacing,
invalid values, and changed source plan images. Floor slabs are partitioned
around voids, and corridor finish intersections are partitioned to avoid doubled
coplanar floor faces. Rebuilding is deterministic; failed generation preserves
the previous export and unrelated files.

## Horizontal clearance check

```sh
python tools/audit_povo_interior.py
```

The audit reads the exported OBJ, verifies its recorded hash and input hashes,
and checks floor support, wall obstacles and lintels. The default configurable
standing envelope is 0.85 m wide and 1.9 m tall on a 0.1 m grid. These are audit
assumptions, not a claim about CS2 player physics. It expands obstacles and voids
by half the envelope width and searches the remaining connected floor cells.

The current mesh reaches all 16 ground stations (entrance, five circulation
points, ten rooms) and all 30 upper stations (assumed landing approach, four
circulation points, 25 rooms). These are independent horizontal checks; they do
not establish a route between floors. Outputs in `exports/povo1_interior_audit/`
include a JSON report and north-up reachability maps. Exported A224 furniture
and ceiling fixtures participate in this check; jumps, real engine collision,
navigation and game traversal remain outside it. The pilot remains reachable
through its door and central aisle. Only named stations are checked, not access
to every seat or every point on the floor.

## Room photos and reusable fit-out

Use different approximate room footprints from the plans, then reuse a shared
set of furniture, lights, floor/wall/ceiling materials and window components.
Adapt desk rows and spacing to each room. A conventional classroom, computer
room and lecture hall may need different arrangements. A photo of one ordinary
classroom is enough to start the common kit; it cannot establish every room's
exact layout. A224 now contains the first reusable kit; other rooms remain
unfurnished.

The seven new photos are P018–P024. P020 shows A224's tall framed west-facing
windows, dark desktops, wooden seats, light wood-look floor, suspended perforated
panels, recessed light grids and ventilation cassettes. P021 (A208) supports the
common floor/furniture/ceiling style and shows a projector and teaching board.
P022 shows a board and pull-down screen, but its room number is unknown. Its
teaching-wall style is a provisional common-kit reference, not verified for A224.
P019 supplies westward exterior context; P018/P023/P024 show outdoor passages,
paving and facades. A filename's “courtyard” does not establish the central plan
courtyard; exact exterior placement remains to be aligned.

The pilot has 24 placeholder seats, a teaching desk, board/screen, ceiling grid
fixtures, ventilation units, projector, floor and ceiling finishes, and framed
glazing. The outside wall is cut around an actual rectangular window opening,
leaving a sill and head. Glass has an OBJ/MTL opacity hint; the offline opaque
renderer omits it for the cutaway. No CS2 transparent/breakable material or
interaction has been built. Furniture dimensions, layout, count, lighting
positions, sill/head heights, bay count and teaching-wall orientation remain
estimates. Light fixtures are geometry only, not game lights.

`classroom_fitout` in the study configuration selects the pilot and its editable
north/south teaching side, central aisle and row pitch. A224's door fraction was
refined toward the north end from its source plan, still approximately. The kit
leaves a transverse passage to that side door. Its current pilot range requires
a west exterior classroom at least 6 × 6 m, with at least 2.8 m wall height. Other
room types will need their own arrangements before expansion. The wall builder
also keeps courtyard material spans local, so aligned classroom walls retain
their own finish.

Photo originals are retained unchanged, with hashes and supplied filenames in
`data/reference/povo_photos/manifest.json`. The builder validates the three used
photos and records their hashes and the manifest hash. The audit rejects a stale
photo or catalogue. No people, screens or photograph pixels are used in generated
textures. Original authorship/licences were not supplied for these new images;
they remain working references.

The most useful next reference is a photo showing A224's entrance and teaching
wall together. Also identify P022's room, and confirm whether the teaching wall
is left or right when facing A224's windows. A known door width or floor-tile
size would help scale. Prefer 1× for details; 0.5× can show a whole small room.
No scan is needed for this step.

## Next refinement

Entrance-to-corridor and stair photographs can establish the actual connections
and finishes. A known doorway dimension, step height/depth and flight counts
can replace the provisional clearances and floor spacing. Then refine the chosen
small interior route, build its stairs and collision, remove overlapping solid
massing in that section, and validate it in Windows before exposing it to players.
