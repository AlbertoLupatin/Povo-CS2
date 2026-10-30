# Outer scenery — 29 October 2026

The campus generator now includes a first scenery pass of 1,156 render meshes around the map edges.
Eight FBK building volumes follow manually traced roof outlines from the existing
georeferenced municipal aerial. Seven road continuations, the north roundabout,
residential silhouettes, outer green areas and tree belts establish the setting.
The north FBK facade has silver panels, opaque blue window bands and a curved
roof lip. The frontage adds a stone retaining plinth, hedge and blue metal fence.

The user's follow-up extends the road beneath the bridge straight west from
local (-23, -5) to the scenery edge at (-240, -5), maintaining its 6 m carriageway
and 1.4 m footways. One tree was cleared from the new road corridor. The former
bend remains as a parking-access branch. This
outer continuation is scenery and follows the same collision policy as the other
edge roads.

At the user's request, the standard-season editable VMAP was refreshed and the
latest model, materials, radar and map sources were copied to the installed
Workshop addon without compilation or packaging. Repository and installed source
hashes match; existing compiled map/model/package files were unchanged by this
update. Preparation evidence and the previous VMAP are retained under
`build/map_edges/source_update/`.

This is source geometry, with offline review images. **No new native CS2 package
has been compiled or installed for this pass.** Heights, facade subdivisions,
outer terrain grades and vegetation remain estimates. The older simplified campus
masses in these review images provide orientation; they do not show the current
playable interiors.

## Evidence

- [Comune di Trento 2024 orthophoto metadata](https://gis.comune.trento.it/it/map/falda/)
  identifies 28–29 August 2024 imagery, EPSG:25832 and CC0. The existing
  `data/reference/povo_ortho_2024.png` extract is 0.5 m per output pixel.
  Roof outlines are manually traced references, not surveyed ground footprints.
- Today's walk is already in `data/reference/povo_photos/walk_2026_10_29/Images`.
  Of six originals, three are exterior views. Filename suffix `(2)` shows the
  bridge/campus road, `(3)` the low white FBK buildings and blue fence looking
  south, and `(4)` the silver building and hedge over a stone wall looking north.
  The other three are office corridor views. Delivery timestamps do not establish
  camera capture times; the walk date comes from the user's description.
- The configuration and export provenance retain original reference paths,
  SHA-256 hashes, coordinate origin and explicit assumptions. No reference image
  pixels are deployed as textures. The new fence and windows use generated,
  opaque materials.

## Implementation and review

`config/povo_edges.json` contains the editable traces and assumptions;
`tools/povo_edges.py` builds the geometry. `build_povo_campus.build_geometry()`
appends these meshes after the existing campus refinements. The generator uses
the existing exterior material namespace and the existing surface cleanup.

The additions are **render meshes only**: no new collision, navigation seeds,
entrances, gameplay bounds or FBK interiors. The accepted tall campus boundary
fence remains in place and partly obscures FBK from the playable road. The extra
`fbk_frontage` camera sits just beyond that fence to review the new architecture;
the two `junction` cameras show the view from the campus side.

Review files in `exports/povo_edges/`:

- `aerial_traces.png`: north-up footprint and road comparison.
- `overview.png`: campus and surroundings.
- `junction_north.png`, `junction_south.png`: views beside the junction.
- `fbk_frontage.png`: reference-side view beyond the existing boundary fence.
- `povo_edges.obj`, `povo_edges.mtl`: standalone scenery with UVs and normals.
- `provenance.json`, `cameras.json`: evidence and reproducible review cameras.

Reproduce with Python's standard library:

```powershell
python tools/build_povo_edges.py
python tools/build_povo_campus.py
python -m unittest discover -s tests -p test_povo_edges.py -v
python tools/audit_povo_render_surfaces.py exports/povo_edges/povo_edges.obj --report build/map_edges/surface_audit.json
```

Add `--render` to the edge builder when Pillow and numpy are available. Native
compilation uses the usual campus build command after source review.

The full source suite passed **332 tests** during this work. The five edge tests
check concave triangulation, finite nondegenerate geometry, reference hashes,
road endpoint registration and exact preservation of existing collision meshes,
collision boxes, earlier render meshes and gameplay bounds. Native rendering,
lighting, distant visibility and performance still require an in-engine check.

The combined campus source export completed successfully, including both FBK
material remaps. Original reference hashes match and no edge meshes occur in the
collision OBJ. Both the standalone scenery and combined campus exports pass the render surface
audit with **zero coplanar overlaps**.
Reports are in `build/map_edges/surface_audit.json` and
`build/map_edges/campus_surface_audit.json`.

Further passes can refine the road junction outlines, grade the large landscape
patches against the terrain data, add the smaller west-side houses and vineyard
rows, and replace estimated FBK heights and facade proportions with better traces.
