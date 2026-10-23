# Povo radar source and Windows validation

The blockout has a reproducible, schematic radar showing the configured
forecourt, the same segmented perimeter used by the collision generator, six
cover footprints, and an A at the objective origin. Ground is schematic, without
terrain shading or a claim of verified walkability. The runtime image omits the
review's spawn dots, cover-height labels, and legend.

## Generate and review on Linux or Windows

From the repository root, using Python 3.12 or newer with no extra packages:

```sh
python tools/build_povo_radar.py --force
python -m unittest discover -s tests -v
```

Outputs in `exports/povo_radar/`:

| File | Purpose |
| --- | --- |
| `trento_povo_radar.png` | Transparent 1024 × 1024 runtime artwork |
| `trento_povo_radar_tga.vtex` | Explicitly named Source 2 radar texture source |
| `trento_povo_radar_spectate_tga.vtex` | Spectator texture source using the same image |
| `trento_povo.txt` | Overview origin, scale, and normalized loading-screen markers |
| `review.svg` | Annotated review with twelve starts, cover heights, north/east arrows, and metric scale |
| `radar.json` | Source/output hashes, transform, settings, and limitations |
| `CREDITS.txt` | Geographic source attribution inherited from the blockout configuration |

`review.png` is an optional raster rendering of `review.svg`, included for quick
viewing. To refresh it with ImageMagick installed:

```sh
magick -background none exports/povo_radar/review.svg exports/povo_radar/review.png
```

The generator accepts `--config`, `--output`, and `--padding` (default 7 metres).
An existing directory requires `--force`. Validation happens before replacing
generated files, and unrelated files in that directory are retained.

## Coordinate alignment

The verified ModelDoc import and map prop pitch give this transform:

```text
world_x = (northing - 5103800) × 39.37007874
world_y = (easting  - 666250) × 39.37007874
pixel_x = (world_x - pos_x) / scale
pixel_y = (pos_y - world_y) / scale
```

Geographic north points right and east points up in this image. Do not rotate
the artwork independently of its overview coordinates. The square image preserves
aspect ratio: the current 130 m long arena plus 7 m padding at each end produces
a 144 m square at 5.536417323 Hammer units per pixel. The narrow arena occupies
the middle of that square; empty space remains transparent.

The generator reads cover/perimeter dimensions from `povo_blockout.json` and the
verified starts/objective from `cs2_project.py`. It rejects starts or an objective
outside the configured playable rectangle. A marks the objective origin, not
the bomb trigger's plantable extent. Team markers are the means of their six
configured starts, normalized to the 1024-pixel image. These are loading-screen
positions, not buy-zone bounds.

## Compile and install on Windows

Regenerate the geographic exports too if their configuration changed. For a full
build, after the usual `place-blockout` preparation:

```powershell
python tools/build_povo_radar.py --force
python tools/cs2_project.py compile --target all
```

`deploy` copies the image and VTEX sources into the addon's content tree at
`panorama/images/overheadmaps/`, and the overview into its game tree at
`resource/overviews/trento_povo.txt`. `compile --target all` builds the model,
then the map, then both radar textures, and restores the generated overview last.
This order matters because a map build can generate its own radar/overview from
the VMAP minimap boundary entities.

To update only the custom radar after an existing map build:

```powershell
python tools/cs2_project.py compile --target radar
```

`compile --target map` retains its existing model-before-map behavior. Run the
radar command afterward to restore the custom artwork and overview. The generated
radar is managed separately from editor-saved source and is not imported by
`sync-from-cs2`.

**Current verification stops at generated source and simulated deployment/build
ordering.** There is no Windows compiler or CS2 runtime in this Linux session.
The explicit VTEX sources use Source 2's typed texture format; their compilation
and runtime lookup in the installed CS2 build remain to be verified. The schema
was cross-checked against a [texture-tool author's implementation](https://github.com/Predi-i/Deadlock-Mod-Compiler/blob/main/tools/vtex_tool.ps1).

## Windows acceptance checklist

1. Compile both VTEX sources with zero resource failures. Confirm these files in
   `game/csgo_addons/trento_povo/panorama/images/overheadmaps/`:
   `trento_povo_radar_tga.vtex_c` and
   `trento_povo_radar_spectate_tga.vtex_c`.
2. Confirm `resource/overviews/trento_povo.txt` matches the generated file after
   the complete build. A 144 m square overview must accompany this artwork;
   retaining the map compiler's independently generated overview can misalign it.
3. Launch the known working local VPK. Check CT/T spawns, movement beside each
   cover, the A marker, radar rotation, full-map overview, and spectator display.
   Player dots must stay aligned with ground and cover throughout.
4. Ensure the packaged addon includes both compiled radar textures and the
   overview text above. **Compiling loose radar resources after the map does not
   update the already-built map VPK.** Inspect final packaged contents and perform
   the existing clean-install test without the loose development addon. A local
   loose-file test does not establish package validation.
   The read-only [package checker](CS2_PACKAGE_CHECK.md) now checks radar entries,
   overview alignment and entry CRCs in the actual VPK. Run it after packaging;
   its result supplements the clean-install and in-game checks.
5. Record compiler output, screenshots, CS2 build, package hash, and results in
   `WORKLOG.md`. The existing bot-round, buy/plant/defuse, performance, calibration,
   and two-independent-client gates still apply.

For future detailed Hammer layouts, the [RadGen authors' workflow](https://radargenerator.github.io/)
can generate overviews from authored geometry. This small generator remains tied
to the reproducible rectangular blockout rather than attempting to decode the
binary VMAP or replace geometry-aware radar authoring.
