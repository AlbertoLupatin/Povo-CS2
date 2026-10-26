# Real-World Trento FPS Map

**Continuing on Windows:** read [the current resume guide](docs/WINDOWS_RESUME.md)
first. It covers the full photo archive, confirmed floor/stair connections,
installed-addon backups, build commands and the next reconstruction steps.

A recognizable Trento environment, delivered as a **playable multiplayer map in Counter-Strike 2**. CS2 supplies movement, weapons, combat, and multiplayer.

## Decisions confirmed on 22 October 2026

- **Game:** CS2. Windows is available for Hammer editing and compilation.
- **First release:** one detailed campus area for small-team matches.
- **Preparation workstation:** Fedora 44, Intel Core Ultra 5 225H, integrated Intel graphics, 32 GB RAM.
- **Selected campus:** Polo Ferrari in Povo. A 200 × 300 m geographic blockout surrounds a compact 25 × 130 m east-forecourt Wingman arena.
- **Later scope:** separate Mesiano, Povo, and central-Trento maps before considering connecting streets.

## Current status

The current playable map is **`trento_povo_campus`**: two Povo 1 floors,
62 open rooms across the campus, four enclosed red stairs, the bridge and
compact Povo 2 arrival, plus connected ground, basement and covered parking.
The integrated exterior adds both east fronts, the double entrance, roads,
surface parking, terrace and a straight garage ramp. Entrance glass has
20% transparency. The lower floors are integrated and compiled; the separate
planimetry export remains a reference study.

Double-click `play_campus.cmd` with CS2 closed for solo exploration without
bots or round limits. Use `play_campus.cmd -Fly` for noclip or
`play_campus.cmd -Match` for match defaults. Build and launch instructions are
in [the campus playtest guide](docs/POVO_CAMPUS_PLAYTEST.md).

`play_campus_winter.cmd` selects the separate winter version, with light snow,
wet paving and an overcast sky. Both versions share the campus layout and now
include revised lighting, local ambience, physical footstep surfaces, 38 moving
door leaves and two small breakable stair panes. Launchers retain the saved
fullscreen setting. Details and validation evidence are in
[the seasonal implementation notes](docs/POVO_SEASONS_AND_INTERACTIONS.md).

The latest [user geometry corrections](docs/POVO_USER_CORRECTIONS.md) restore
opaque room partitions, straighten and glaze the Povo 1 entrance stair, add
Povo 2's left terrace and the fence across the street, correct the basement
turn/duplicate door and fill the concrete outskirts. That guide records the
geometry checkpoint; the seasonal notes record the current packages. The earlier
[independent review](docs/CODEX_REVIEW.md) is retained as a historical checkpoint.

This remains a playable prototype. Local tests cover 2v2 setup, purchases,
planting, defusing and elimination. Broader bot behavior, competitive balance,
clean-machine validation and replication between independent clients still need
evaluation. The exterior build generates navigation but skips the expensive bot
tactical-analysis pass. Additional furnishing remains deferred.

The earlier `trento_povo` outdoor Wingman arena is a separate map. Source terrain,
photo references and plan studies are preserved. Read [the map design brief](docs/MAP_DESIGN.md),
[the data-source register](docs/DATA_SOURCES.md) and [the circulation facts](docs/POVO_CIRCULATION.md)
for accepted decisions, provenance, estimated dimensions and the two-floor gameplay adaptation.
Historical checkpoints are retained in [the worklog](docs/WORKLOG.md).

## Workspace

| Path | Purpose |
| --- | --- |
| `config/project.json` | Accepted decisions, candidate areas, unresolved choices |
| `docs/MAP_DESIGN.md` | Fidelity, scope, gameplay, and release acceptance criteria |
| `docs/DATA_SOURCES.md` | Source links, licences, dates, and outstanding checks |
| `docs/CS2_WORKFLOW.md` | Fedora preparation and Windows build/playtest sequence |
| `data/reference/` | Small georeferenced campus imagery extracts and provenance |
| `data/raw/` | Original terrain/vector downloads, added selectively |
| `tools/fetch_reference.py` | Reproduce the campus imagery extracts from the municipal WMS |
| `tools/asc_to_obj.py` | Convert a clipped elevation grid to a local-coordinate mesh |
| `config/povo_blockout.json` | Povo extent, local origin and approximate building modules |
| `tools/build_povo_blockout.py` | Assemble the Povo terrain, reference texture and rough building volumes |
| `tools/build_povo_radar.py` | Generate radar artwork, overview coordinates and an annotated review |
| `docs/POVO_RADAR.md` | Radar generation, Windows compilation and packaging checks |
| `docs/POVO_ARCHITECTURE.md` | Exterior detail, plan alignment and remaining measurement needs |
| `docs/POVO_INTERIOR_STUDY.md` | Separate two-level interior study, assumptions and rebuild commands |
| `docs/TERRAIN_TOOL.md` | Terrain converter usage and limitations |
| `docs/WINDOWS_RESUME.md` | Current detailed Windows continuation, backups, photos, geometry priorities and commands |
| `docs/WINDOWS_HANDOFF.md` | Entry point linking to the current resume guide and verified state |
| `cs2/` | Versioned `trento_povo` addon source, model definition and materials |
| `tools/cs2_project.py` | Cross-platform checks plus Windows deploy/compile/sync commands |
| `docs/WORKLOG.md` | Durable decisions, build evidence, warnings and remaining gates |

## First milestone

Load a rough reconstruction of the chosen campus in CS2 and have **two independent clients join and complete a match**. Validate scale, slopes, stairs, collision, spawning, objectives, packaging, and installation before detailed architecture. Two-player validation proves multiplayer function; later sessions at the intended team size establish balance.

## Data policy

Use provincial/municipal open data and original or appropriately licensed photography. Google Maps/Street View is not an asset-extraction pipeline for this project. Preserve source dates, licences, coordinate systems, and uncertainty. Exterior imagery does not establish accurate interiors.

Raw data retains its own licence. No blanket licence for this repository is chosen yet; preserve the source-specific credits in the register and per-file metadata.
