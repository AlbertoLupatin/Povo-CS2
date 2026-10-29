# Povo-CS2

A playable **Counter-Strike 2 map of the Polo Ferrari buildings at Povo
(University of Trento)**: **Povo 1 and Povo 2**, the bridge between them, and their
immediate surroundings. CS2 supplies movement, weapons, combat and multiplayer;
this repository holds the reproducible source, data pipeline and build tooling for
the `trento_povo` addon, built from open geographic data and original photography.

## What's in the map

`trento_povo_campus` is the full campus map (`trento_povo` is the earlier compact
outdoor arena, built from the same source).

- **Povo 1:** three floors: -1 entrance/A1xx at provisional 4 m, 0 A2xx at 7.6 m, +1 offices and bridge at 11.2 m. Four red stair cores connect the floors; one Acquario study room replaces four synthetic cells, with reception, courtyard, sanitary spaces and source-plan room labels retained.
- **Bridge** joins Povo 1 +1 and Povo 2 +1 at 11.2 m. The active compact Povo 2 plan retains entrance/table halls, B110–B114 rooms, two successive upper stair rises and basement parking. Its full photographed floor plans remain a separate survey, not a complete active reconstruction.
- **Exterior:** roads, surface lot, residential backdrop, straight ramp into the covered garage, terrain from real 0.5 m elevation data.
- **Gameplay:** team starts, buy zones, bomb target, generated navigation and a radar with separate floors.
- **Breakable glass:** playable windows, doors, bridge, stair and courtyard glazing, plus the library and canteen wings in front of Povo 1. Receptions stay sealed.
- **Automatic doors:** the Povo 1 and Povo 2 entrances slide open as players approach.

Latest local standard-season build: **29 October 2026**, with Povo 2 floors
**-1 and -2 rebuilt from the approved layout**. Continuous floors/ceilings,
clean corridor walls, restored stair doors and full-height parking columns are
verified in CS2. All 256 source tests pass; 26 native walking routes pass in both
directions, and all 1,075 VPK entry CRCs are verified. The local package uses
normal-quality lighting with a 2048-pixel atlas; reproduce with
`build_campus.cmd --fast-lighting`. Winter and the Workshop upload remain at
their previous versions. See the [rebuild details and in-game screenshots](docs/POVO2_BASEMENTS_REBUILD.md).

The later 29 October [exterior visibility investigation](docs/POVO_EXTERIOR_VISIBILITY.md)
updated the local package's lighting and fixed a frontage seam. Large black
courtyard patches remain under investigation. CS2 is closed between test batches
to avoid idling on battery.

The [floor and wall flicker correction](docs/POVO_PAVEMENT_FLICKER.md) removes
coplanar render overlaps throughout the campus, paving finish and winter model
while preserving collision and texture alignment. All three model audits report
zero remaining overlaps, including vertical and sloped faces.

Interiors are reconstructed from public floor plans and photographs, so room
dimensions and seat counts are estimates, and surfaces are blockout-level art
rather than final textures. Balance and large-match testing are still open.

The 27 October Povo 2 corrections are based on the user's draw.io sketch.
See [the corrected layout and pavement checks](docs/POVO2_SKETCH_CORRECTIONS.md),
the [latest plan image](exports/povo_campus/sketch_corrections_20261027.png), or
the [editable four-page drawing](exports/povo_campus/povo2_layout_editable_20261027.drawio).

The [27 October photo-survey index](docs/POVO_SURVEY_20261027.md) records the
44 original images, confirmed floor names and remaining ambiguities. Amenities
local 0/1 align with Povo 1 -1/0; the photographed canopy is a thin walkable cover
with open air beneath. [Three-floor layout review](exports/povo_campus/adjustments_layout_review.png)
and [bridge review](exports/povo_campus/povo2_connection_review.png) show the current
source geometry. Photo 4 is confirmed as A103; its compass placement and exact
registration remain approximate. This clarification applies to the A103–A106
family only; see the [A103 cutaway and top view](exports/povo_campus/a103_photo4_review.png).
The user confirms photo 46's right circled lab has one entrance
from the corridor and a separate red-star exit to the external courtyard. Its
north-door leaf/swing is visible below the blue stroke near the wall's west end;
its narrow entrance recess needs stepped-footprint refinement before an exact
opening segment is registered. No generic room plan is substituted for
unobserved details.

## Build it

**Building on another person's PC:** follow the [Windows build handoff](docs/BUILD_HANDOFF.md)
for source transfer, dependencies and the checked `build_campus.cmd` command.

The compiled VPK is not committed (`build/` is git-ignored); build it from source.

- **Any platform** (Python 3): data preparation, map generation, audits, tests.
- **Windows only:** deploy, compile and sync, because Valve's CS2 Workshop Tools are Windows-only.

```sh
python tools/cs2_project.py doctor            # check the toolchain
python -m unittest discover -s tests -q       # run the tests
python tools/cs2_campus.py                    # Windows: generate, deploy, compile and package the campus
python tools/cs2_project.py sync-from-cs2 --dry-run  # review installed edits after Hammer sessions
```

Use `python tools/build_povo_campus.py` for source geometry generation without
Windows Workshop Tools. `python tools/cs2_campus.py --season both` builds the
standard and winter variants. The `cs2_project.py compile --target all` command
builds the earlier outdoor arena; use the campus pipeline above for this map.

Set `CS2_ROOT` (or pass `--cs2-root`) if Steam is not in a default library.
To explore solo on Windows with Steam running and CS2 closed, run `play_campus.cmd` (`-Fly` for noclip,
`-Match` for match defaults). Details: [CS2 workflow](docs/CS2_WORKFLOW.md),
[playtest guide](docs/POVO_CAMPUS_PLAYTEST.md), [package check](docs/CS2_PACKAGE_CHECK.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `config/` | Project decisions and per-building JSON descriptions (blockout, interior, exterior, route) |
| `data/` | Georeferenced imagery extracts, terrain samples, photo archive with credits and locations |
| `tools/` | Generators, audits, previews, packaging and CS2 build commands |
| `cs2/` | Versioned `trento_povo` addon source: maps, model definition, materials |
| `exports/` | Generated reviews, plans, radar artwork and in-engine screenshots |
| `tests/` | Source tests |
| `docs/` | Design, data sources, per-area write-ups and the [worklog](docs/WORKLOG.md) |

Start with the [map design brief](docs/MAP_DESIGN.md), the
[data-source register](docs/DATA_SOURCES.md) and the [worklog](docs/WORKLOG.md).
Area write-ups: [architecture](docs/POVO_ARCHITECTURE.md),
[interior study](docs/POVO_INTERIOR_STUDY.md), [circulation](docs/POVO_CIRCULATION.md),
[Povo 2](docs/POVO2_CONNECTION.md), [exterior](docs/POVO_EXTERIOR.md),
[radar](docs/POVO_RADAR.md), [terrain tool](docs/TERRAIN_TOOL.md).
Open work is tracked in [TODO.md](docs/TODO.md).
[Publishing and hosting](docs/PUBLISH_AND_HOST.md) explains Workshop upload and playing with friends.
For two players through Steam, `host_campus.cmd` installs the match profile and
opens normal CS2; after loading the published Workshop map with Open Party,
enter `exec povo_duel` in the developer console.
[WINDOWS_RESUME.md](docs/WINDOWS_RESUME.md) is the detailed maintainer handoff log.

## Data policy and licensing

Geometry uses provincial/municipal open data and original or appropriately licensed
photography. Google Maps/Street View is **not** an asset-extraction source. Source
dates, licences, coordinate systems and uncertainty are recorded in
[DATA_SOURCES.md](docs/DATA_SOURCES.md) and the photo
[credits](data/reference/povo_photos/CREDITS.md).

**No blanket licence has been chosen for this repository.** Raw data and third-party
material keep their own licences; public visibility is not a reuse licence, and some
reference material (e.g. university plans) has no redistribution licence established.
Counter-Strike 2 and Source 2 belong to Valve; this is an unofficial fan project.

## Contributing

Issues and suggestions are welcome — corrections to room layout or dimensions from
people who know the buildings are especially useful.
