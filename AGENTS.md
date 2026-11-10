# Repository instructions for coding agents

These instructions apply throughout this repository. Read the preserved project
context below before making changes, then consult the linked area documentation
for the part of the map you are changing.

- Preserve the approved Povo 2 -1 layout described in
  [the definitive layout record](docs/POVO2_MINUS1_DEFINITIVE_LAYOUT.md).
  Document any later user-requested layout change as a revision of that baseline.
- Use the campus build pipeline for `trento_povo_campus`; the earlier compact
  outdoor arena has a separate build command.
- Treat the dated build results below as historical checkpoints, not proof that
  the current checkout or a newly compiled package has passed validation.
- Keep operational handoff notes and detailed verification records in this file
  or the linked documentation. Keep `README.md` focused on repository visitors.
- Follow the data-source and licensing constraints recorded below.

The previous README is preserved in full below so its project decisions,
verification history, known issues and documentation links remain available to
agents that automatically load the root `AGENTS.md`.

---

# Povo-CS2

A playable **Counter-Strike 2 map of the Polo Ferrari buildings at Povo
(University of Trento)**: **Povo 1 and Povo 2**, the bridge between them, and their
immediate surroundings. CS2 supplies movement, weapons, combat and multiplayer;
this repository holds the reproducible source, data pipeline and build tooling for
the `trento_povo` addon, built from open geographic data and original photography.

## What's in the map

**Povo 2 −1 is FINAL: the current in-game layout was explicitly approved by the
user on 2 November 2026 as the definitive map layout.**
The [definitive layout record](docs/POVO2_MINUS1_DEFINITIVE_LAYOUT.md) is the
source of truth and supersedes conflicting older sketches, proposals and audit
items. Preserve this layout during further finishing and work on other areas.

`trento_povo_campus` is the full campus map (`trento_povo` is the earlier compact
outdoor arena, built from the same source).

- **Povo 1:** three floors: -1 entrance/A1xx at provisional 4 m, 0 A2xx at 7.6 m, +1 offices and bridge at 11.2 m. Four red stair cores connect the floors; one Acquario study room replaces four synthetic cells, with reception, courtyard, sanitary spaces and source-plan room labels retained.
- **Bridge** joins Povo 1 +1 and Povo 2 +1 at 11.2 m. The active Povo 2 plan retains entrance/table halls, B110–B114 rooms, two successive upper stair rises and basement parking. The −1 West Offices now add 22 plan-traced rooms and four internal passages with photo-guided finishes; see the [integration details](docs/POVO2_WEST_OFFICES_20261029.md). The remaining full photographed floor plans are a separate survey.
- **Exterior:** roads, surface lot, residential backdrop, straight ramp into the covered garage, terrain from real 0.5 m elevation data.
- **Map edges:** OSM-registered FBK buildings with open courtyards and LiDAR heights, photo-guided frontage, corrected northern Via Sommarive and roundabout, outer roads and greenery; [31 October corrections](docs/BUILDING_REGISTRATION_IMPLEMENTATION_20261031.md).
- **Gameplay:** team starts, buy zones, bomb target, generated navigation and a radar with separate floors.
- **Breakable glass:** playable windows, doors, bridge, stair and courtyard glazing, plus the library and canteen wings in front of Povo 1. Receptions stay sealed.
- **Automatic doors:** the Povo 1 and Povo 2 entrances slide open as players approach.

Latest local standard-season package: **2 November 2026**, completing the Povo 2
entrance ceiling, overlapping stair sign, side-wall closure and A–D exterior
concrete fills. All **378 source tests pass**; the **62,707,301-byte** package has
**1,234 verified entry CRCs**. **77 compiled entrance/fill checks**, **12 ordinary
walking routes / 110 waypoints** and **10 normal-lit views** verify this revision.
The approved basement layout and earlier street-concrete repairs are preserved.
See the [entrance and exterior report](exports/exterior_entrance_review_20261102/README.md).
The existing uphill asphalt ledge remains unresolved; the full uphill street
was not retested. After closing CS2, `play_campus.cmd` loads this standard package.

The earlier **2 November 2026** finishing package added the requested
Povo 2 −1 office furniture, exterior glazing and wall finishes while preserving
the approved room bounds, names, corridors, stairs and terrace. All **369 source
tests pass**. The 62,778,837-byte package has **1,232 verified entry CRCs**;
12 native views were individually inspected with normal lighting enabled.
**16 ordinary standing walks / 48 waypoints** verify the selected furnished
office entrances and empty WI2 doorway in both directions. All six fixed terrace
door pairs block from both sides, and sampled new exterior panes break when shot.
See the [finishing report and screenshots](docs/POVO2_MINUS1_FINISHES_20261102.md).
It uses normal-quality lighting with a 1024-pixel atlas, retaining the
[lighting repair](docs/RENDER_LIGHTING_CORRUPTION_20261102.md),
[entrance layout](docs/POVO2_DRAWIO_ENTRANCE_20261031.md), straight C7, continuous
terrace and OSM/LiDAR corrections. These targeted walks do not certify a complete
campus walkthrough or multiplayer. Full source builds use `build_campus.cmd`;
the repair report records the smaller native bake settings. Script-only VRAD
retiling is disabled. Close CS2 and rerun `play_campus.cmd` to load the new
package. Winter and the Workshop upload remain at their previous versions.

The 30 October [OSM and LiDAR registration audit](docs/BUILDING_REGISTRATION_AUDIT_20261030.md)
confirms the Povo 1 and Povo 2 footprints. Its FBK, residential and northern road
corrections are now [implemented and measured](docs/BUILDING_REGISTRATION_IMPLEMENTATION_20261031.md).
Povo 2's unresolved roofs, podium and campus bridge width remain pending review,
as confirmed by the user.

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

## Experimental HPC build handoff — 4 November 2026

The user-approved 5 November Povo facade implementation is documented in
[the facade correction record](docs/POVO_FACADES_20261105.md). Use its final
six-bay short-end pattern and bridge-corner explanation; earlier generated
bridge previews and the initial remake-pattern schematic were rejected.
Consult that record for current build/runtime verification and installation
status rather than assuming source implementation is a tested package.

The user requested an hpc3 build attempt under PBS job name `tmp_cs_build`.
See [the HPC execution record](docs/HPC3_BUILD_20261104.md) for SSH access,
isolated source/runtime staging, job IDs, resources, logs and limitations.
This Wine/Apptainer experiment does not replace the supported Windows campus
pipeline and is not evidence of a successful or visually verified new package.

The subsequent **full local cold benchmark** completed in **25m05s**, including
tests, every build/bake step, packaging repairs/retries, full CRC checks and
compiled collision audits. The opt-in command is
`build_campus.cmd --optimize-import --force-model --lightmap-max-resolution 1024`.
The candidate remains unpromoted, with normal-lit visual review pending; see the
same [execution record](docs/HPC3_BUILD_20261104.md) for the complete timings,
artifact hashes, lighting changes for background trees and verification limits.

The requested build of the latest `claude/povo-updates.bundle` completed in
**18m47s**, including all steps and logger-recovery delay, with 421 passing tests,
1,204 verified entry CRCs and passing compiled collision audits. It is recorded in
[the bundle build handoff](docs/POVO_UPDATES_BUNDLE_BUILD_20261104.md). It applies
the bundle in a private source snapshot while retaining the build fixes; consult
that record for its exact commit, full-run status and candidate verification.

The subsequent user-requested Povo 2 sloped sidewalk repair is recorded in
[the sidewalk handoff](docs/POVO2_SLOPED_SIDEWALK_20261104.md). That task applies
the bundle diff to the main working source, replaces the overlapping campus-side
footway grades and updates the route waypoints. Consult its observed final
build/runtime status before treating the revision as validated.

That sidewalk build completed in **16m26s**, with **423 source tests**, **250
compiled sidewalk samples**, **1,205 verified entry CRCs** and the compiled
basement checks passing. **10 ordinary walking routes / 50 waypoints** and four
normal-lit native views verify the targeted repair. The new standard package
(`09396dc0…`) is now installed for `play_campus.cmd`, with the previous package
backed up; the running review addon has the same bytes. Existing dark surfaces
inside the adjacent garden/approach remain. See the linked handoff and
[screenshots/results](exports/sidewalk_fix_20261104/README.md) for exact scope.

The following [road/garden fill reference review](docs/POVO2_AREA_FILL_REFERENCE_20261104.md)
examines photos, Google Maps as visual context, municipal orthophotography and
RoanS77's `shaders-mod` remake at `97769b5`. Its [annotated proposal](exports/povo2_area_reference_20261104/README.md)
distinguishes retaining/podium faces and ground/planting from the protected open
garden and lower route. It confirms a surviving old raised paving remnant at
E52–56.7/N1.25–6.333/Z6.2–7.42. This is research and a repair plan, **not an
implemented fill or a newly tested package**. Use final assembled stair/terrace
bounds; the early garden JSON has superseded stair positions. Do not port the
remake's 1.25 scale or different floor heights into the approved layout.


## Latest campus build verification - 6 November 2026

The latest frontage/garden source has now compiled and passed targeted native
verification. See [the build repair record](docs/LATEST_BUILD_20261106.md) for
package identity, live compiler output/threading changes, test evidence and
limits. The earlier navigation-stall diagnosis was incorrect; the native
clipping warning is nonfatal and clearance checks remain enabled.


## Exterior repairs verified on 7 November 2026

The current standard build closes the Povo 2 corner road void, restores the bus,
replaces the shrub proxy, extends the roadside guard and relocates the red
Povo 1 stair. See [the exterior repair record](docs/EXTERIOR_REPAIR_20261107.md)
for package identity and native verification.

## Povo 1 and Povo 2 frontage follow-up

The latest standard build matches entrance glazing to the room windows, joins
the Povo 2 sidewalk to the forecourt, and extends the Povo 1 library-side guard.
See [the frontage follow-up record](docs/POVO_FRONTAGE_FOLLOWUP_20261107.md) for
the bus shift, exterior grade and verification results.

## Campus descents and Povo 2 vestibule

See [the curb and entrance record](docs/POVO_CURBS_AND_ENTRANCE_20261107.md) for
the latest standard build, measured road and sidewalk widths, corrected light
positions and native verification.

## Campus texture repairs verified on 7 November 2026

See [the texture repair record](docs/POVO_TEXTURE_REPAIRS_20261107.md) for the
latest standard package, corrected sidewalk and entrance paving, continuous
terrazzo finishes, Povo 2 vestibule materials and textured library hedge. The
final revision passed 462 source tests, all 1,536 entry CRCs, the render overlap
and compiled basement audits, 11 normal-lit views and 12 walks over 46 waypoints.

## Library stair and bridge road measurements

The [library stair and road record](docs/POVO_LIBRARY_ROAD_SPANS_20261107.md)
supersedes the uniform sidewalk widths along the measured part of the bridge
approach. It records the two separate spans, local pavement tapers and checks.

## Povo 2 −1 exterior terrace revision

The [terrace integration record](docs/POVO2_TERRACE_INTEGRATION_20261108.md)
documents the integration of the corrected terrace drawing, the garage ramp
and floor 0 edge repairs, and the status of the standard campus build.

## Povo 2 parking continuity verified on 9 November 2026

The [parking record](docs/POVO2_PARKING_CONTINUITY_20261109.md) documents the
integration of `a3d82ff` with the installed terrace, the compiled lightwell and
parking checks, and the solo playtest. The verified standard package is ready
in the local workspace for `play_campus.cmd` and was uploaded to the existing
friends-only Workshop item 3827904476.

## Povo 1 bus-side paving and reception lift

See [the Povo 1 repair record](docs/POVO1_BUS_PAVING_AND_LIFT_20261109.md) for the
paved recess and the three-stop lift in the existing reception shaft. The
standard local package passed four paving walks, seven lift rides and calls
from all three landings in a fresh solo CS2 session.
