# Povo-CS2

A playable **Counter-Strike 2 map of the University of Trento's Polo Ferrari
campus in Povo**, including Povo 1, Povo 2, their connecting bridge and the
surrounding streets.

This repository contains the source assets, geographic data pipeline and build
tools for the `trento_povo` addon. The campus is reconstructed from open geographic
data, public floor plans and original photography.

## Features

- Multi-floor interiors across Povo 1 and Povo 2, with offices, teaching rooms,
  study spaces, stairs and a connecting bridge.
- Campus roads, parking, gardens and nearby buildings, with terrain derived from
  elevation data.
- Breakable glazing and automatic entrance doors.
- Team starts, buy zones, a bomb target, navigation and a radar with floor views.
- Standard and winter campus variants.

The full map is **`trento_povo_campus`**. **`trento_povo`** is an earlier compact
outdoor arena built from the same source.

## Project status

The campus is playable and under active development. Interiors include estimated
dimensions and blockout-level art; lighting, exterior details, gameplay balance
and multiplayer verification still have open work. See the
[task list](docs/TODO.md) and [worklog](docs/WORKLOG.md) for details.

The Povo 2 -1 layout was approved on 2 November 2026 and is the
[definitive layout baseline](docs/POVO2_MINUS1_DEFINITIVE_LAYOUT.md).
Compiled map packages are generated locally and are not committed to this repo.
Local builds and the Workshop upload may be at different revisions.

## Build and play

Python **3.11 or newer** supports source preparation and tests on Windows,
Linux and macOS. Compiling and playing the map requires Windows, Steam, CS2 and
**Counter-Strike 2 Workshop Tools**. Lighting compilation also requires a GPU
with hardware ray tracing.

For a complete Windows setup, including the required VPKEdit packager, follow the
[build guide](docs/BUILD_HANDOFF.md). From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
# Complete the VPKEdit setup in the build guide before running these commands.
.\build_campus.cmd --check
.\build_campus.cmd
```

Close CS2 and Hammer before building. The build regenerates campus assets and
deploys project-owned files into the installed addon; save Hammer edits first.
Set `CS2_ROOT` or pass `--cs2-root` for a custom Steam library.

After a successful build, with Steam running and CS2 closed:

```powershell
.\play_campus.cmd
```

Use `.\build_campus.cmd --season both` to build the standard and winter variants.
See the [playtest guide](docs/POVO_CAMPUS_PLAYTEST.md) for launch options and
[publishing and hosting](docs/PUBLISH_AND_HOST.md) for Workshop and friends play.

## Development

Install the dependencies in `requirements-build.txt` into your Python environment,
then run these commands from the repository root:

```sh
python tools/cs2_project.py doctor
python -m unittest discover -s tests -q
python tools/build_povo_campus.py
```

The last command generates source geometry without the Windows Workshop Tools.
For deployment, compilation and preserving Hammer edits, see the
[CS2 workflow](docs/CS2_WORKFLOW.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `config/` | Building descriptions, layout decisions and gameplay configuration |
| `data/` | Geographic inputs, terrain samples and credited reference photos |
| `tools/` | Generators, audits, previews and build commands |
| `cs2/` | Versioned addon maps, model definitions and materials |
| `exports/` | Generated plans, reviews, radar artwork and screenshots |
| `tests/` | Source tests |
| `docs/` | Design notes, data sources, build guides and verification reports |
| `AGENTS.md` | Repository instructions and detailed context for coding agents |

Start with the [map design](docs/MAP_DESIGN.md),
[data-source register](docs/DATA_SOURCES.md) and [build guide](docs/BUILD_HANDOFF.md).
Maintainer context and prior build records are preserved in [AGENTS.md](AGENTS.md),
with a detailed handoff in [WINDOWS_RESUME.md](docs/WINDOWS_RESUME.md).

## Contributing

Issues and suggestions are welcome, especially corrections from people familiar
with the campus. Include the building, floor and location, plus photographs or
measurements you have permission to share. Consult [AGENTS.md](AGENTS.md) before
changing source geometry or build tooling.

## Data and licensing

Geometry uses provincial and municipal open data, original photography and
appropriately licensed sources. Google Maps and Street View are not
asset-extraction sources. Source dates, licences, coordinate systems and
uncertainties are recorded in [DATA_SOURCES.md](docs/DATA_SOURCES.md) and the
[photo credits](data/reference/povo_photos/CREDITS.md).

**No blanket licence has been chosen for this repository.** Raw data and
third-party material retain their own licences. Public visibility does not grant
reuse rights; some reference material, including university plans, has no
established redistribution licence.

Counter-Strike 2 and Source 2 belong to Valve. This is an unofficial fan project.
