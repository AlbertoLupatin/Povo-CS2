# Povo exterior detail and interior references

The source model now has a first photo-guided exterior pass: eight facade
sections with glazing/frame grids or stone/window patterns, plus a bridge deck,
roof, posts and horizontal louvers. These replace the plain appearance of selected
building faces and the old solid bridge placeholder.

This is intermediate architecture, not a finished or newly verified CS2 build.
The glazing is an **opaque coloured placeholder**. There are no breakable panes,
openable doors, accessible building interiors, or new gameplay routes in this
pass. Exact window counts, positions, dimensions and floor levels are estimates.

## Sources and reproducibility

- `config/povo_blockout.json` retains the approximate geographic building modules
  and adds an `architecture` section. Each facade names a module, face, elevations,
  bay/row counts, photographic IDs and a note about placement uncertainty.
- `data/reference/povo_photos/manifest.json` records the user-reviewed photographs,
  sources, licences, file paths, and hashes. The two user-supplied plans are P016
  and P017; their original filenames and file locations are retained.
- `tools/povo_architecture.py` generates closed visual components in local metres.
  `build_povo_blockout.py` adds them to the existing visual OBJ and records their
  assumptions and photographic credits in the export provenance. It verifies
  each referenced photograph's hash before publishing generated files.
- Four new material sources and ModelDoc remaps distinguish glazing, frames,
  stone and dark trim. The materials extend the existing opaque shader setup;
  they do not implement transparency or breakage.

Regenerate with the existing commands:

```sh
python tools/build_povo_blockout.py --force
python tools/build_povo_radar.py --force
python -m unittest discover -s tests -v
```

Optional offline reviews use the same numpy/matplotlib dependencies as the
original geographic preview:

```sh
python tools/render_blockout_preview.py
python tools/render_architecture_preview.py
```

`exports/povo_blockout/architecture_preview.png` renders the exported geometry,
including 20 m facade sections and the bridge. Its depth-buffer renderer resolves
the thin facade layers correctly. It is not a CS2 screenshot.

The current visual mesh has 41,724 triangles and 926 detail components. The
arena collision OBJ remains byte-identical to the previous Windows baseline:
2,304 triangles, with no new building or bridge collision. The bridge roof stays
at the previous 385.69 m DBM estimate; its 382.49 m deck elevation is an explicit
3.2 m-below-roof assumption. It is scenery, not a validated walkable connection.

On Windows, prepare/deploy/compile through the existing workflow and inspect
the material import, facade visibility, frame-rate cost, and collision separation.
`compile --target all` builds the model, map, then radar. The added details have
not yet passed that Windows compiler or runtime check.

## New plan references

The user supplied two plan images and identified
[`agusmeroli/mappe-povo`](https://github.com/agusmeroli/mappe-povo). Its README
describes the plans as unofficial and links its classroom-map source to a 2017
conference map. We downloaded both PDFs, both available floor PNGs, and the
README under `data/reference/povo_plans/mappe-povo/`, with URL/hash provenance.
No licence file was listed in the inspected repository tree. These downloaded
reference files are not automatically packaged into the game.

The room plans show classroom groups, a courtyard, study areas, reception,
entrance connections, and four stair cores. Their compass puts **north to the
right and east downward**. `config/povo1_plan_alignment.json` records a provisional
registration to the existing 47 x 83 m core footprint. It includes manually
selected stair regions and an entrance point; the annotated images are in
`exports/povo_plan_review/`.

The registration is an alignment study, not a surveyed model. It uses the
existing approximate footprint as its metric anchor; it does not independently
prove building dimensions. The fitted entrance lands near E666274, N5103726,
within the northing range of the existing east connector module (5103723-5103732).

Keep the numbering conventions separate:

| Room group | Room-plan label | Lift label on room plan | Stair-diagram label | User image name |
| --- | --- | --- | --- | --- |
| A1xx | piano terra | -1 | 0 | P016, floor1 |
| A2xx | primo piano | 0 | 1 | P017, floor2 |

These labels describe references to the same room groups; none gives an absolute
floor elevation. The user images are preserved as supplied. The small P016 image
is useful for context but should not be used to estimate detailed dimensions.

## What would help next

A separate [interior circulation study](POVO_INTERIOR_STUDY.md) now prepares two
adjustable levels, courtyard voids, reserved upper stair openings, and schematic
entrance/corridor geometry. It uses provisional heights and floor finishes and
is excluded from CS2 deployment. This exterior pass still retains solid building
massing; opening a playable interior requires a later integration step.

Nothing additional is required to continue exterior refinement. The next useful
field evidence is one entrance-to-corridor scan or photo sequence, one known
doorway/corridor dimension, and a view identifying a bridge landing and floor
label. Those would help establish floor elevations, clearances and connections
before opening an interior route in the actual map. A Windows compile and local
playtest remain the next way to validate the current source changes.
