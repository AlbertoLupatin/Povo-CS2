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

The [24 October map adjustments](docs/POVO_MAP_ADJUSTMENTS.md) replace ground
Studio E1 with a reception, add separate male/female restrooms in both upstairs
Povo 1 study wings, darken the circulation floors, enlarge the Povo 2 tables,
move its boards, shorten its ground hall and label its rooms B111–B114 from
the entrance. All 126 source tests pass. The rebuilt package passes its asset
and CRC checks, and CS2 walking checks pass all four new restroom entrances
and the shortened corridor end. B111–B114 signs are visually verified in-game.

The latest [compact Povo 2 arrival](docs/POVO2_CONNECTION.md) retains the bridge
exit's two alcoves, replaces W1 with enclosed gray stairs down, removes E1,
and closes the corridor before W2/E2. Povo 1 retains its 57 furnished rooms.
The compact source passes all 109 tests and 159 horizontal clearance stations
across Povo 1's two floors and the separate lower stair vestibule. The larger
Povo 2 draft below stays separate until its stairs align with this arrival.

The next [Povo 2 planimetry source](docs/POVO2_PLANIMETRY.md) adds the entrance,
sealed glass reception, table hall, empty B110–B113 rooms, stairs linking +1 to
ground/-1/-2, the photo-guided basement corridor and covered parking. A
three-floor review is in `exports/povo2_planimetry/review.png`. The corrected
ground/basement draft stays separate while its stairs are aligned with the
independently edited first floor. It has not been compiled or deployed.

The two-floor Povo 1 implementation is now generated as the separate
`trento_povo_campus` map: 61 open furnished rooms across Povo 1 and the first
Povo 2 section, a connected floor-1 corridor and bridge, four mirrored enclosed red
stairs beside Studio N1/N2/S1/S2, courtyard glazing, interior lighting,
team starts, a bomb target and a radar with separate floors. Build/launch commands
and the walking checklist are in [the campus playtest guide](docs/POVO_CAMPUS_PLAYTEST.md).
The per-floor collision-clearance audit (161 stations) and all 99 source tests
pass. Double-click `play_campus.cmd` with CS2 closed to start a solo exploration
session without bots or round limits. Use `play_campus.cmd -Fly` for noclip or
`play_campus.cmd -Match` for the match defaults. A first
[in-game visual correction and review](docs/POVO_VISUAL_REVIEW.md)
addresses the severe overexposure, coarse finishes and block-like stairs.
This remains a prototype; a full visual pass and objective round remain open.

The user accepted the outdoor gameplay checks on 23 October 2026. The larger
[campus route design](docs/POVO_CAMPUS_ROUTE.md) records the approved Povo 2
adaptation: retain two Povo 1 floors, connect the bridge from the former upper
A202/A203 area, and relocate those rooms to the matching empty ground corner.
The [first Povo 2 connection](docs/POVO2_CONNECTION.md) implements that route
and fixes the room signs above the doors.

As of 23 October 2026, this repository contains a reproducible geographic and
gameplay blockout for a first CS2 addon. The generated east-forecourt arena has
terrain-fitted perimeter collision, six cover volumes, twelve relocated starts,
buy zones, a bomb target, lighting/probe support, minimap bounds, and generated
navigation. The stock Wingman room has been removed while its proven mode
entities are retained. Visual geography and arena-only collision are separate,
so the full campus remains visible without making bots navigate the entire crop.

The current Windows build completes with zero resource failures and retains
503 nav areas. The packaged map is 10,623,229 bytes with 51 entries, including
custom model/material/texture dependencies and radar. All entry CRCs and staged
asset hashes pass; CS2 loads `trento_povo` and creates server/client physics.
The earlier arena baseline also verified a human CT spawn and three live bots.
**This is a functional first-playable blockout, not a finished release:** a full
bot round, objective/buy-zone checks, visual/performance review, clean-install
test, and two-independent-client match remain to be completed. Detailed campus
architecture, materials, final radar artwork, sound, and balance are also open.

Linux continuation adds generated schematic radar artwork, a coordinate-aligned
overview, and an annotated layout review in `exports/povo_radar/`. Deployment now
installs those assets and supports `compile --target radar`; `--target all`
builds radar textures after the map and restores the matching overview.
Both radar textures now compile and are included in the VPK with the matching
overview and current CS2 lookup aliases. Visual radar alignment remains untested.
See [the package workflow](docs/CS2_PACKAGE_CHECK.md) and [radar workflow](docs/POVO_RADAR.md).

The latest source also adds a first photo-guided exterior pass: glazed facade
grids, stone/window patterns, and bridge structure. Reviewed photos and the newly
provided Povo 1 plans are catalogued with their assumptions. This 41,724-triangle
visual source now compiles and loads in Windows; the arena collision remains
unchanged. See [the architecture and plan review](docs/POVO_ARCHITECTURE.md).

A separate [Povo 1 interior study](docs/POVO_INTERIOR_STUDY.md) now provides two
provisional floor levels, 35 named room footprints with walls and doorways,
courtyard/stair openings, corridors, and furnished A224/A223/A215 prototypes with
continuous rows, 1 m side passages and rear windows opposite the board. Seat
counts and remaining dimensions are estimated. This study is excluded from the CS2 deployment and playable arena.

The [confirmed 66-photo walk](docs/POVO_CIRCULATION.md) records the bridge as
Povo 2 floor 1 ↔ Povo 1 floor 2 and locates the two distinct red stairwells.
Full-resolution photo references and camera metadata are preserved in the repo.

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
