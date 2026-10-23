# Povo geographic blockout

`tools/build_povo_blockout.py` generates an intermediate reference mesh from the
downloaded Povo DTM, configured DBM roof elevations, and the municipal orthophoto.
It uses only the Python standard library and reuses the terrain converter's grid
reader, decimation, triangle winding, and NoData handling.

From the project root:

```sh
python3 tools/build_povo_blockout.py
python3 -m unittest discover -s tests -v
```

The default configuration is `config/povo_blockout.json`; outputs go to
`exports/povo_blockout/`. Use `--config`, `--output`, and optionally `--root` to
change locations. Input paths are relative to the configuration directory's
parent unless `--root` is provided. An existing output directory is rejected;
`--force` replaces the six generated files after validation and preserves other
files in that directory.

The generated folder contains:

- `povo_blockout.obj`: full terrain, building modules, terrain-fitted gameplay
  cover/perimeter, and a 1 m scale cube.
- `povo_blockout_collision.obj`: arena-only terrain and gameplay volumes for
  physics/nav; it deliberately excludes the distant building modules.
- `povo_blockout.mtl`: neutral building colors and the terrain reference material.
- `orthophoto_reference.png`: an unchanged copy of the full orthophoto extract.
- `provenance.json`: input/config/output hashes, coordinate declarations, sampled extents, resolution, module assumptions, and limitations.
- `CREDITS.txt`: source attribution and a description of changes.

Keep these files together when importing the OBJ into a modelling application.
The mesh uses metres with east X, north Y, and up Z. Source coordinates are
translated by the configured origin; the builder performs no reprojection or
datum conversion. CRS declarations and supporting evidence remain the
responsibility of the source register and project configuration.

The default terrain crop is 200 × 300 m. Source cells are 0.5 m; a sampling step
of four gives nominal 2 m mesh spacing. Vertices remain at original cell centres
inside the crop, so the mesh stops half a source cell inside integer crop edges.
The last sample row/column is retained even if the last interval is shorter.
NoData triangles and coarse cells spanning discarded NoData are omitted.

Terrain UVs use the **full orthophoto bounds**, not the cropped terrain bounds:
west is U=0, east U=1, south V=0, and north V=1. The aerial imagery is an alignment
reference: photographed roofs remain visible on the terrain beneath the volume
models. It is unsuitable as a finished ground material.

Each configured building or gameplay module becomes a closed rectangular box with eight vertices and
twelve outward-facing triangles. These are approximate roof-envelope volumes,
not surveyed building outlines. Their explicit roof elevations are recorded;
the builder checks DBM alignment but does not infer buildings from the raster.
Bases, bridge depth, and gaps remain modelling assumptions. A `calibration_1m`
cube at local `(-120, -170, 0)` is solely for import-scale checks and should be
removed from the finished game scene.

The checked-in export currently contains 41,724 visual triangles and 38 gameplay
volumes (six cover boxes plus a segmented perimeter). Its 2,304-triangle cropped
collision export feeds ModelDoc physics and CS2 nav generation. CS2 entities,
lighting, navigation seeding, and packaging remain in the VMAP workflow rather
than this geographic export. The blockout still has no detailed entrances,
stairs, interiors, final materials, or release radar artwork. Continue with
[the Windows handoff](WINDOWS_HANDOFF.md) and [the CS2 workflow](CS2_WORKFLOW.md).

The optional `architecture` configuration now adds 926 visual detail components:
photo-guided facade grids/window patterns and a bridge structure. It checks the
referenced photo hashes and adds source credits to provenance. Facade dimensions
and deck height remain estimates; the original arena collision is unchanged.
See [the architecture/plan review](POVO_ARCHITECTURE.md) for source limitations,
material behaviour, previews, and the newly registered Povo 1 interior plans.
