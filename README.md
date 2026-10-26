# Povo-CS2

A playable **Counter-Strike 2 map of the Polo Ferrari buildings at Povo
(University of Trento)**: **Povo 1 and Povo 2**, the bridge between them, and their
immediate surroundings. CS2 supplies movement, weapons, combat and multiplayer;
this repository holds the reproducible source, data pipeline and build tooling for
the `trento_povo` addon, built from open geographic data and original photography.

## What's in the map

`trento_povo_campus` is the full campus map (`trento_povo` is the earlier compact
outdoor arena, built from the same source).

- **Povo 1:** two floors, ~60 furnished rooms (classrooms, labs, studios), four enclosed red stairs, courtyard glazing, reception, restrooms.
- **Bridge** between Povo 2 floor 1 and Povo 1 floor 2, plus the Povo 2 entrance hall, table hall, B110–B114 rooms, stairs and basement parking.
- **Exterior:** roads, surface lot, residential backdrop, straight ramp into the covered garage, terrain from real 0.5 m elevation data.
- **Gameplay:** team starts, buy zones, bomb target, generated navigation and a radar with separate floors.
- **Breakable glass:** playable windows, doors, bridge, stair and courtyard glazing, plus the library and canteen wings in front of Povo 1. Receptions stay sealed.
- **Automatic doors:** the Povo 2 entrance banks slide open as players approach.

Latest verified build (24 October 2026): zero compile failures, 44,979,765-byte VPK
(344 entries, all CRCs pass), 135 source tests passing, and normal-walking route
checks passing in the CS2 engine. Interiors are reconstructed from public floor plans
and photographs, so room dimensions and seat counts are estimates, and surfaces are
blockout-level art rather than final textures. Balance and large-match testing are
still open; see [the worklog](docs/WORKLOG.md) for evidence and remaining gates.

## Build it

The compiled VPK is not committed (`build/` is git-ignored); build it from source.

- **Any platform** (Python 3): data preparation, map generation, audits, tests.
- **Windows only:** deploy, compile and sync, because Valve's CS2 Workshop Tools are Windows-only.

```sh
python tools/cs2_project.py doctor            # check the toolchain
python tools/cs2_campus.py                    # generate the campus map source
python -m unittest discover -s tests -q       # run the tests
python tools/cs2_project.py deploy            # Windows: install into the CS2 addon tree
python tools/cs2_project.py compile --target all
python tools/cs2_project.py sync-from-cs2     # after Hammer sessions; review the diff
```

Set `CS2_ROOT` (or pass `--cs2-root`) if Steam is not in a default library.
To explore solo on Windows with CS2 closed, run `play_campus.cmd` (`-Fly` for noclip,
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
