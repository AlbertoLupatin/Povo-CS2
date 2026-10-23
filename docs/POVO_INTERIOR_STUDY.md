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
  wood-look and perforated-ceiling textures for the A224/A223/A215 prototypes. Repeating metric
  UVs use the provisional 0.6 m repeat. Reference photos establish the appearance
  family; texture patterns and exact colours are approximate.

The study currently has 1,080 closed component boxes and 12,960 triangles, including
three furnished rooms with ceilings, fixtures and west-facing rear window openings.
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
- `classroom_A224.png`, `classroom_A223.png`, `classroom_A215.png`: cutaways, top views with side-clearance
  dimensions and finish swatches.
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
python tools/render_classroom_preview.py --room a223
python tools/render_classroom_preview.py --room a215
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
points, ten rooms) and all 33 floor-1 stations (assumed landing approach, four
circulation points, 22 empty-room centres and both side aisles in each furnished
room). These are independent horizontal checks; they do
not establish a route between floors. Outputs in `exports/povo1_interior_audit/`
include a JSON report and north-up reachability maps. Exported classroom furniture
and ceiling fixtures participate in this check; jumps, real engine collision,
navigation and game traversal remain outside it. All three furnished rooms remain reachable
through their doors and 1 m side passages. Named side-aisle stations replace
centre points occupied by continuous rows. Only named stations are checked, not
access to every seat or every point on the floor. Crouched cover, bullet
penetration and engine collision remain Windows gameplay checks.

## Room photos and reusable fit-out

Use different approximate room footprints from the plans, then reuse a shared
set of furniture, lights, floor/wall/ceiling materials and window components.
Adapt desk rows and spacing to each room. A conventional classroom, computer
room and lecture hall may need different arrangements. A photo of one ordinary
classroom is enough to start the common kit; it cannot establish every room's
exact layout. A224, A223 and A215 now reuse the kit; other rooms remain
unfurnished.

The seven new photos are P018–P024. P020 shows A224's tall framed west-facing
windows, dark desktops, wooden seats, light wood-look floor, suspended perforated
panels, recessed light grids and ventilation cassettes. P021 (A208) supports the
common floor/furniture/ceiling style and shows a projector and teaching board.
P022 shows a board and pull-down screen. The user does not know its room;
its style is assigned to the existing A223 footprint by design choice. This is
not an identification of P022 as A223. P019 supplies westward exterior context;
P018/P023/P024 show outdoor passages, paving and facades. A filename's “courtyard”
does not establish the central plan courtyard; exterior placement remains to be
aligned.

The user corrected the A224 layout: continuous desk/seat rows across the room,
leaving 1 m clear at both side walls, with windows behind the seated students
opposite the blackboard. The template is rotated accordingly: windows west,
blackboard east. There is no central break in the desktop rows. A223 repeats
this layout as the requested additional room in the shared style.

A224/A223 have 45 estimated seats in five rows. A215 has 27 estimated seats in three rows. The seat
count, row pitch, desktop/seat heights, fixture positions, window dimensions and
bay count remain modelling estimates. The 1 m side passages are measured from
the inside wall faces to each row's end, including the current wall thickness.
The rows are intended as crouched cover; actual CS2 crouch visibility, collision and
bullet behaviour remain untested. Photos and user feedback establish the style
and layout; they do not establish ballistic properties.

`classroom_fitouts` selects the rooms, teaching/window sides, side clearance and
row pitch. The template requires opposite teaching/window walls, an exterior
window wall, a room at least 6 m wide × 4.5 m deep and at least 2.8 m wall height. The source-plan
doors of A224 and A223 are placed approximately near their north ends. A teaching
board across the doorway is rejected. Other room types will need their own
arrangements. Courtyard material spans remain local so aligned classroom walls
retain their own finish.

The furnished rooms have a teaching desk, board/screen, suspended ceiling, grid fixtures,
vents, projector, wood-look floor and framed glazing. Actual rectangular window
openings preserve sill/head wall sections. Glass has only an OBJ/MTL opacity
hint; the opaque offline renderer omits panes for cutaway views. No CS2 break
interaction or transparent material has been built. Fixtures are geometry,
without game lighting. No people or source-image pixels are included.

Photo originals are retained unchanged, with hashes and supplied filenames in
`data/reference/povo_photos/manifest.json`. The builder validates all used
photos and records their hashes and the manifest hash. The audit rejects a stale
photo or catalogue. No people, screens or photograph pixels are used in generated
textures. Original authorship/licences were not supplied for these new images;
they remain working references.

## Existing red stair reference

P007 already establishes red treads and landings, dark nosing strips, metal
horizontal-bar railings, and white walls/columns. No replacement photo is needed
for that appearance. It does not identify which of the four registered stair
cores it shows, the full step count between A1xx and A2xx, or measured landing
heights. The view is oblique and lower steps are obscured, so those values are
not inferred as measurements. Stair flights have not been built yet.

A nearest room number is enough to identify the relevant core approximately:

| Core in the registered upper plan | Nearby rooms |
| --- | --- |
| Southwest | A208 / A221 |
| Northwest | A224 / LAB |
| Southeast | A204 / A212 |
| Northeast | A203 / A209 |

The later walk locates the two used red stairwells: photos 51–47 are near
A209/A216 (northeast core), from Povo 1 floor 2 to floor 1; photos 39–38 are near
A212/A213 (southeast core), from floor 1 to ground. The user confirmed they are
different stairwells. The new photos provide clearer appearance and flight views.
Complete riser counts and metric landing heights remain unmeasured; flights are
not built in the source yet. See [the circulation review](POVO_CIRCULATION.md).

## Next refinement

Entrance-to-corridor and stair photographs can establish the actual connections
and finishes. A known doorway dimension, step height/depth and flight counts
can replace the provisional clearances and floor spacing. Then refine the chosen
small interior route, build its stairs and collision, remove overlapping solid
massing in that section, and validate it in Windows before exposing it to players.

## Identified A215 and window context

Walk photos 44–43 identify A215. It uses its smaller courtyard-side plan footprint,
with a real window cut through the courtyard wall. Continuous desk fronts now
have dark modesty panels, shared pedestal supports, floor feet and a seat beam,
instead of independent table/chair legs at every place. A215 shows three rows;
seat count, depth and furniture dimensions are estimates. The desk-panel
perforation texture is generated, not extracted from a photograph.

The outside view shows opposite glazing and a metal external stair. These are
recorded in A215's `window_context`, with the high-resolution references retained;
that detailed exterior stair is not yet modelled. Photos 42–41 are A211 or A212,
so they remain an ambiguous scene rather than being assigned to one room. Their
window/background evidence is retained for later alignment.

The existing study still contains only Povo 1 ground / floor 1. The bridge is
on the currently unbuilt floor 2; Povo 2 interiors and physical vertical stair
connections are not present in this OBJ. The new circulation graph records the
correct floor relation independently of these incomplete geometry assets.
