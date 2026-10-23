# Real-World Trento FPS Map

A recognizable Trento environment, delivered as a **playable multiplayer map in Counter-Strike 2**. CS2 supplies movement, weapons, combat, and multiplayer.

## Decisions confirmed on 22 October 2026

- **Game:** CS2. Windows is available for Hammer editing and compilation.
- **First release:** one detailed campus area for small-team matches.
- **Preparation workstation:** Fedora 44, Intel Core Ultra 5 225H, integrated Intel graphics, 32 GB RAM.
- **Selected campus:** Polo Ferrari in Povo. A 200 × 300 m geographic blockout surrounds a compact 25 × 130 m east-forecourt Wingman arena.
- **Later scope:** separate Mesiano, Povo, and central-Trento maps before considering connecting streets.

## Current status

As of 23 October 2026, this repository contains a reproducible geographic and
gameplay blockout for a first CS2 addon. The generated east-forecourt arena has
terrain-fitted perimeter collision, six cover volumes, twelve relocated starts,
buy zones, a bomb target, lighting/probe support, minimap bounds, and generated
navigation. The stock Wingman room has been removed while its proven mode
entities are retained. Visual geography and arena-only collision are separate,
so the full campus remains visible without making bots navigate the entire crop.

The current Windows build completes with zero resource failures, produces a
9,312,611-byte VPK, and loads in CS2 as `trento_povo` with 503 nav areas. A human
spawned at the intended CT start and three bots joined the live listen server.
**This is a functional first-playable blockout, not a finished release:** a full
bot round, objective/buy-zone checks, visual/performance review, clean-install
test, and two-independent-client match remain to be completed. Detailed campus
architecture, materials, radar artwork, sound, and final balance are also open.

The workspace contains real 0.5 m terrain samples for Povo and Mesiano, a Povo building-surface raster, municipal aerial references, and a Fedora → Windows workflow. The terrain conversion utility prepares a local-metre OBJ from an ASCII elevation grid; it does not create a Hammer map, collision, or game entities. Povo is the first map; Mesiano is retained as a later candidate. Its current sample covers the western approach and only part of the campus, so it must be expanded before modelling that campus.

Start with [the map design brief](docs/MAP_DESIGN.md), [the data-source register](docs/DATA_SOURCES.md), and [the CS2 workflow](docs/CS2_WORKFLOW.md).

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
| `docs/TERRAIN_TOOL.md` | Terrain converter usage and limitations |
| `docs/WINDOWS_HANDOFF.md` | Import calibration, Hammer compilation and multiplayer checks |
| `cs2/` | Versioned `trento_povo` addon source, model definition and materials |
| `tools/cs2_project.py` | Cross-platform checks plus Windows deploy/compile/sync commands |
| `docs/WORKLOG.md` | Durable decisions, build evidence, warnings and remaining gates |

## First milestone

Load a rough reconstruction of the chosen campus in CS2 and have **two independent clients join and complete a match**. Validate scale, slopes, stairs, collision, spawning, objectives, packaging, and installation before detailed architecture. Two-player validation proves multiplayer function; later sessions at the intended team size establish balance.

## Data policy

Use provincial/municipal open data and original or appropriately licensed photography. Google Maps/Street View is not an asset-extraction pipeline for this project. Preserve source dates, licences, coordinate systems, and uncertainty. Exterior imagery does not establish accurate interiors.

Raw data retains its own licence. No blanket licence for this repository is chosen yet; preserve the source-specific credits in the register and per-file metadata.
