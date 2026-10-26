# Resume the Povo project on Windows

## Current source handoff: 26 October photo additions

Start with [WINDOWS_PHOTO_ADDITIONS_HANDOFF.md](WINDOWS_PHOTO_ADDITIONS_HANDOFF.md).
It includes the corrected layout, 154 passing tests, dependencies, campus
rebuild/package commands and remaining in-game checks. Older verified builds
below are historical and do not contain these new interiors.

## Latest: map adjustments — 24 October 2026

See [POVO_MAP_ADJUSTMENTS.md](POVO_MAP_ADJUSTMENTS.md) for the reception replacing
ground Studio E1, four upstairs restrooms with UOMINI/DONNE door signs, darker
corridor floors and Povo 2's enlarged tables, reversed boards, shortened ground
hall and B111–B114 labels. Source clearance passes 65/92/4 campus stations,
32 integrated lower-floor stations and 72 stair samples. A new test also checks
access to all toilet cubicles and washbasins. The previous source/game/test
addon trees and package are backed up at
`build/map-adjustments-backup-20261024-103106/`.

The final rebuilt and reflection-baked package passes all 217 entry CRCs and
asset hashes. It is 42,212,394 bytes, SHA-256
`289ffd586414bdb425be2bb5390b60e40870a8bd08eb19ccceb63b4db45555fa`.
All 126 tests pass. Engine walking passes each new restroom door and the
shortened Povo 2 end wall; native screenshots verify all four B111–B114 labels.
The launcher uses this package. See the adjustments guide for screenshots,
compile logs, package evidence and the entity-only sign correction.

## Latest arrival: compact Povo 2 — 23 October 2026

See [POVO2_CONNECTION.md](POVO2_CONNECTION.md). The arrival alcoves remain;
W1 is an enclosed gray stair down to a closed lower vestibule, E1 is removed,
and the corridor ends at N26 before W2/E2. `compact_arrival: true` in
`config/povo2_connection.json` defers the overlapping full Povo 2 draft while
its ground/basement source is aligned. Preserve both sources. The two chats
are coordinating this boundary with the user's authorization.

109 source tests pass. Horizontal clearance passes 67/88/4 stations. The
compact build log is `build/gameplay/p2-compact-build.log`; the previous baked
package is backed up under `build/p2-compact-backup-20261023-211637/`.
The compact compile, navigation and reflection bake succeeded. The local and
installed packages match: 40,402,867 bytes / 162 entries, SHA-256
`cbffd1a07529e495a56e66f82aa1b85473314891779826c7ddb0914ef31bbd40`.
Normal walking down and back up both flights and through both doorways passes
six recorded stages (`build/gameplay/p2-compact-walk.json`). The game is left
stationary at the bridge exit, one human / zero bots / paused warmup. Keep
the chat visible beside its small window. Full details and screenshots are
in the connection guide; earlier checkpoints below are historical.

## Latest source: Povo 2 planimetry — 23 October 2026

[POVO2_PLANIMETRY.md](POVO2_PLANIMETRY.md) records the new entrance/reception,
table hall, empty B110–B113 rooms, four-level grey stair, basement corridor and
covered parking. The corrected lower-floor draft remains standalone while its
stair is aligned with the compact first-floor work; it was not compiled or
deployed. The ground/-1/-2 review and 30-station / 75-stair-sample standalone
audit are in `exports/povo2_planimetry/`. The first-floor panel was removed;
the single audited upper landing belongs to the draft, not the compact build.
Use the separate build/runtime checkpoints below for the installed package.

## Latest: Povo 2 connection and fixed door signs — 23 October 2026

See [POVO2_CONNECTION.md](POVO2_CONNECTION.md) for the current route, package and
runtime evidence. The source has 61 furnished rooms, A202/A203 relocated into
the ground corner, a level floor-1 corridor/bridge and the initial Povo 2 arrival
section. Room text uses fixed upright transforms and blue plaques. All 99 tests
and the 161-station audit pass. The earlier checkpoints below are historical.
Keep the user's chat window visible during game checks; CS2's
`r_always_render_all_windows true` lets the game update without repeated focus
changes. Do not activate or automate the Codex UI.

## Latest: playable Povo 1 campus — 23 October 2026

The user's visual review rejected the initial campus appearance. The subsequent
[visual correction/review](POVO_VISUAL_REVIEW.md) records actual foreground CS2
inspection, material/exposure fixes, the revised stair and current package.
The historical compile/traversal checkpoint below does not establish visual quality.

The latest source has 56 open furnished rooms, normal-width north corridors and
four mirrored enclosed stairs beside Studio N1/N2/S1/S2. A101/A102 are open;
all room types repeat the furniture kit. The lighter circulation floor is
off-white. All 97 tests and the 138-station clearance audit pass. See
[the current room/stair review](POVO_ROOMS_STAIRS_REVIEW.md) for build/runtime
evidence and [the playtest guide](POVO_CAMPUS_PLAYTEST.md) for launch commands.
`play_campus.cmd` defaults to solo exploration; `-Fly` enables noclip, `-Match`
uses match defaults. Future Povo 2 work keeps Povo 1 at two floors, starts the
bridge corridor from current A202/A203 and moves those rooms to the empty
ground corner. The room move is recorded but deferred.
The outdoor `trento_povo` map remains separate. Older checkpoints below describe
earlier states, including the original offline interior study.

## Windows continuation checkpoint — 23 October 2026

The Windows checkout has now pulled `main` through `2acf729`. All 79 tests pass
on Windows 11 with Python 3.15.1. CS2 Workshop Tools build `26144732` successfully
compiled the updated exterior model, map and both custom radar textures with
zero resource failures. Deterministic map preparation reported `unchanged`.

Installed editable files matched the previous `26ee052` baseline before
deployment. Both installed addon trees were preserved under
`build/windows-resume-backup-20261023-162008/`. The new compile log is
`build/windows-resume-compile.log`; these local backup/log files are ignored by Git.

The compiler-only VPK is 9,521,788 bytes; its missing custom assets are now added
by `tools/package_cs2.py`. The final `build/package/trento_povo.vpk` is
10,623,229 bytes, SHA256
`549edf5423049e52b05a2667e21df5683b40cf6752f5e894d2ad750fa8618187`.
All 51 entries pass CRC and staged-source hash checks. It includes custom
model/material/texture dependencies, the generated overview and both TGA/PSD
radar lookup names. The package uses CS2's BLAKE3 chunk hashes; a default
Source 1 MD5 table was rejected during the first load test and corrected.

The final package is installed in the existing addon. A local launch confirms
`Spawn Server: trento_povo`, server/client physics and a successful game-loop
transition. The log is `build/package/windows-load-test.log`; the package report
is `build/package/trento_povo.json`. See [CS2_PACKAGE_CHECK.md](CS2_PACKAGE_CHECK.md)
for repeatable packaging commands. Visual radar alignment, a completed round,
clean installation and independent-client validation remain open. The interior
remains an offline study outside deployment.

The handoff below describes the source received from Linux and retains the older
baseline evidence; use this checkpoint for the latest Windows compile results.

Updated 23 October 2026. This is the current operational handoff. Read this before
older setup sections in the worklog or workflow. The reconstruction checkpoint
is commit `34ac930`; this documentation follows it. Pull the latest `main` to
obtain both, including all 66 full-resolution walk photos and camera metadata.

## 1. Current state: what runs and what is source-only

| Component | Current state | Evidence / limitation |
| --- | --- | --- |
| Compact outdoor Wingman arena | Previously compiled and loaded on Windows | 25 × 130 m playable envelope; human CT spawn and three bots verified |
| Campus reference terrain/buildings | Approximate 200 × 300 m backdrop | Local-metre geography; not the whole city centre |
| Latest exterior facade/bridge detail | Generated source, not yet recompiled on Windows | 41,724 visual triangles; collision remains the prior compact arena |
| Radar | Generated source and compile workflow | Real VTEX compile, runtime lookup, final VPK inclusion and alignment still need Windows validation |
| Povo 1 interior study | Offline OBJ/MTL, not installed by deployment | Ground and floor 1 only; 35 room footprints; A224/A223/A215 furnished |
| Interior details | 1,080 boxes / 12,960 triangles | A224/A223: 45 estimated seats each; A215: 27; counts/dimensions are estimates |
| Stairs / bridge route | Confirmed connection graph and reference photos | No traversable interior stair flights, Povo 1 floor-2 geometry, or Povo 2 interior geometry built yet |
| Windows after Linux changes | Not tested | Last actual runtime evidence is the earlier arena baseline |

The last verified Windows checkpoint was `26ee052`, CS2 build `26087496`.
The old VPK was 9,312,611 bytes, SHA256
`52e7292dd29db1cb17d918aa5d1d799dc6c3505f6b56a98645f808c01aea7b1f`.
It loaded with a human and three bots. A completed round, buy/plant/defuse,
restart, performance, clean installation and two independent clients remain open.
This hash identifies the old package, not the newer source awaiting compilation.

The current source has **73 passing Python tests on Linux**. Windows results for
this exact source must be recorded separately. Core generators/checkers need
Python 3.12+ and its standard library. Optional preview rendering needs
numpy/matplotlib; existing PNG reviews are committed, so rendering is optional.
ExifTool is not needed to read the saved JSON metadata or rebuild geometry.

## 2. Recover the Windows working tree and preserve installed edits

The previously used checkout is `C:\Users\Alberto\Desktop\trento_fps`.
Adjust it if the checkout moved. Start in PowerShell:

```powershell
Set-Location 'C:\Users\Alberto\Desktop\trento_fps'
git status --short
git branch --show-current
git fetch origin
git log --oneline HEAD..origin/main
```

Inspect and preserve any local changes before pulling. Do not discard Windows
work with `reset --hard`, `clean`, or an overwrite. Use a separate branch/commit
and reconcile differences if needed. Once the working tree is clean and the
branch can fast-forward:

```powershell
git pull --ff-only origin main
git status --short
git log -3 --oneline
```

The complete photo archive is about 308 MB; the pull can take longer than earlier
updates. Photos are normal repository files, with no dependency on Linux's
Downloads folder, a mounted iPhone, WeTransfer, or a Git LFS download step.

**Before deploying, back up the installed addon.** Hammer/ModelDoc may have
unsynchronized edits inside Steam even when the Git checkout is clean. The
following copies preserve both addon trees, including editable content, game
configuration and the previous map package:

```powershell
$cs2Install = 'C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive'
$backupRoot = Join-Path (Get-Location) ('build\windows-resume-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backupRoot | Out-Null
$installedContent = Join-Path $cs2Install 'content\csgo_addons\trento_povo'
$installedGame = Join-Path $cs2Install 'game\csgo_addons\trento_povo'
if (Test-Path -LiteralPath $installedContent) {
    Copy-Item -LiteralPath $installedContent -Destination (Join-Path $backupRoot 'content-trento_povo') -Recurse
}
if (Test-Path -LiteralPath $installedGame) {
    Copy-Item -LiteralPath $installedGame -Destination (Join-Path $backupRoot 'game-trento_povo') -Recurse
}
$backupPackage = Join-Path $backupRoot 'game-trento_povo\maps\trento_povo.vpk'
if (Test-Path -LiteralPath $backupPackage) {
    Get-FileHash -LiteralPath $backupPackage -Algorithm SHA256
}
```

Set `$cs2Install` to the actual Steam-library installation if different. Keep the
backup until the new source is built and inspected. `build/` is ignored by Git.
Compare installed editable files against the repository before choosing which
changes to retain. `sync-from-cs2 --dry-run` can report differences, but it is a
one-way copy tool, not a merge tool; blindly running the real sync can restore
older installed VMAP/ModelDoc/material files over the new repository versions.

## 3. Read the reconstruction facts before changing geometry

The authoritative route is `config/povo_circulation.json`, reviewed in
[POVO_CIRCULATION.md](POVO_CIRCULATION.md). Follow the user's named floors:

- **Bridge: Povo 2 floor 1 ↔ Povo 1 floor 2.** This does not establish the height
  of Povo 2 ground, nor that a Povo 2 storey equals two Povo 1 storeys.
- Povo 1 photos **51–47**: red stairwell near **A209/A216**, floor 2 → floor 1,
  the northeast core in the registered plan.
- Povo 1 photos **39–38**: a **different** red stairwell near **A212/A213**,
  floor 1 → ground, the southeast core. The user explicitly confirmed this.
- A2xx rooms are Povo 1 **floor 1**. Povo 1 ground uses the A1xx room plan.
  Earlier reference filenames called floor1/floor2 are historical names; do not
  use them to move the A2xx rooms onto the bridge floor.
- Photos **44–43** identify **A215**. Photos **42–41** are **A211 or A212**;
  the user does not remember which. Keep that uncertainty.
- Photos 40 and 14 have contextual interpretations rather than explicit user
  identifications. Photo 16 appears in overlapping entrance/outward batches.
  These details need not block the confirmed connections.

The two existing Povo 1 prototype elevations are 374.0 m and 377.6 m. The scenery
bridge deck was separately estimated at 382.49 m. That gives inconsistent
placeholder rises of 3.6 and 4.89 m. **These are not measured storey heights.**
`exports/povo_circulation/report.json` flags this; Povo 2 ground and basement
heights remain null. Establish a coherent vertical model from photo/plan evidence
and calibration before authoring final stair collision. Do not silently shift
one building or equate unknown ground floors to hide the discrepancy.

### Source files to edit

| File | Purpose |
| --- | --- |
| `config/povo_circulation.json` | User-confirmed walk, bridge equality, separate stair cores, ambiguous photo groups |
| `config/povo1_plan_alignment.json` | Plan-image rectangles, orientation, approximate geographic bounds and current floor labels |
| `config/povo1_interior_study.json` | Two Povo 1 floor layouts, room footprints/doors, heights and furnished-room settings |
| `tools/build_povo_interior.py` | Slabs, walls, voids, door/window geometry, generated textures and provenance |
| `tools/povo_room_fitout.py` | Reusable desk/seat/ceiling/window kit, room sizing and side-aisle stations |
| `config/povo_blockout.json` | Exterior modules, facade details, bridge scenery estimate and arena layout |
| `tools/povo_circulation.py` | Route validation, photo verification, named-floor diagram and elevation consistency report |
| `tools/cs2_project.py` | Addon deployment, deterministic VMAP preparation, resource compilation and source sync |

## 4. Find the photos and reviews

Original exported filenames are preserved under
`data/reference/povo_photos/walk_2026-10-23/originals/`.
The walk is reverse numbered: `image00066.jpeg` was first, `image00001.jpeg` last.
Catalogue IDs P025–P090 are separate stable reference IDs; do not confuse them
with walk numbers. `manifest.json` maps IDs, filenames, descriptions and SHA256s.
`walk_2026-10-23/capture_metadata.json` stores native camera/EXIF/Apple/GPS tags.
All 66 images have 5712 × 4284 source pixels; honor EXIF orientation for display.
26 use the main lens and 40 the ultrawide. Recorded headings are magnetic, and
indoor GPS has accuracy limits; user room/floor identifications take precedence.

Useful committed reviews, viewable without installing rendering packages:

- `exports/povo_photo_walk_2026-10-23/REVIEW.md`: six numbered contact sheets and
  individual originals. `ROUTE_NOTES.md` contains the confirmed narrated route.
- `exports/povo_circulation/review.png`: named floors and both red stair cores.
- `exports/povo1_interior_study/review.png`: ground/floor-1 rooms and corridors.
- `exports/povo1_interior_study/classroom_A215.png`: identified small classroom.
- `exports/povo1_interior_study/classroom_A224.png` and `classroom_A223.png`:
  earlier kit prototypes; A223 was a deliberate P022-style assignment, not a
  confirmed identification of the room in P022.
- `exports/povo1_interior_audit/review.png`: conservative horizontal clearance.
- `exports/povo_blockout/architecture_preview.png`: exterior detail source.
- `exports/povo_radar/review.png`: schematic arena radar and transform.

A215's window background includes opposite courtyard glazing and an external
metal stair. Those details are recorded in `window_context`; that exterior
stair is **not** reconstructed yet. Preserve these backgrounds while refining
window positions and sightlines; do not treat the room photos only as furniture
references. Photos 42–41 also preserve useful backgrounds despite room ambiguity.

The shared classroom kit now has continuous rows, 1 m side passages, dark desk
fronts with generated perforation, shared metal pedestals/feet and wooden seats.
A215 uses three estimated rows; A224/A223 have five. Dimensions and counts remain
estimates. Crouch visibility, bullet penetration, breakable windows and moving
doors have not been implemented/validated in CS2.

## 5. Run source checks and regenerate when inputs change

Run each command from the repository root and stop on a nonzero exit or error.
The generators/checkers below use the standard library:

```powershell
python -m unittest discover -s tests -v
python tools/cs2_project.py --cs2-root "$cs2Install" doctor
python tools/povo_circulation.py
```

`doctor` can report source readiness even when optional tools are absent. Inspect
its CS2/compiler lines as well as the exit code; a green Python test suite is not
a Valve compile. A missing Windows CS2 installation is not fixed by regenerating
OBJ files.

If geographic/interior/configuration inputs changed, regenerate in this order:

```powershell
python tools/build_povo_blockout.py --force
python tools/build_povo_radar.py --force
python tools/build_povo_interior.py --force
python tools/audit_povo_interior.py
python tools/povo_circulation.py
```

The interior audit verifies recorded source/mesh/photo hashes. Its default
0.85 m wide × 1.9 m high standing envelope on a 0.1 m grid is an audit assumption,
not asserted CS2 player physics. It independently reaches 16 ground and 33 floor-1
stations, including both side passages in each furnished room. It does not check
stairs, jumps, every seat, real navigation or bullet collisions. It supports the
current axis-aligned box OBJ components; curved/non-box geometry needs an
extended audit or a separate collision representation.

Optional render commands, if numpy/matplotlib are available:

```powershell
python tools/render_interior_preview.py
python tools/render_classroom_preview.py --room a215
python tools/render_classroom_preview.py --room a224
python tools/render_classroom_preview.py --room a223
```

SVG-to-PNG rendering additionally uses ImageMagick. Existing tracked PNGs are
sufficient for review without these optional tools. Regenerating geometry does
not automatically refresh the optional PNG reviews.

## 6. Rebuild the existing outdoor addon first

After preserving/reconciling installed edits, preview deployment:

```powershell
python tools/cs2_project.py --cs2-root "$cs2Install" deploy --dry-run
python tools/cs2_project.py --cs2-root "$cs2Install" sync-from-cs2 --dry-run
```

The real `deploy` copies repository-owned source and generated exterior/radar
assets into the installed addon; it can replace changed destination files.
`compile` deploys by default too. The offline interior OBJ/MTL, photos and
circulation diagram are excluded from deployment. Compiling now will update the
exterior/radar baseline; it will not make A215 or the stair route playable.

Use deterministic placement only after deciding the repository VMAP is the
correct source. It modifies the repository's binary VMAP, including starts,
objective, stock placeholders and supporting volumes. A repeated run should be
unchanged:

```powershell
python tools/cs2_project.py --cs2-root "$cs2Install" place-blockout
python tools/cs2_project.py --cs2-root "$cs2Install" place-blockout
New-Item -ItemType Directory -Force -Path build | Out-Null
python tools/cs2_project.py --cs2-root "$cs2Install" compile --target all 2>&1 | Tee-Object -FilePath build/windows-resume-compile.log
$compileResult = $LASTEXITCODE
if ($compileResult -ne 0) { throw "CS2 compile failed with exit code $compileResult" }
```

`--target all` builds ModelDoc, map, then radar and restores the generated
overview. `--target map` also refreshes the model first; a radar-only follow-up
can restore custom radar source after another map build. `--no-deploy` is for a
reviewed installed working copy and skips the initial deploy, not every generated
radar/overview write.

Open the existing `trento_povo` addon in Workshop Tools and inspect the compiled
map/materials. The known successful console map form was:

```text
map maps/trento_povo.vpk
```

Record the new CS2 build, compiler log, package hash, screenshots and runtime
results. The historical warnings include duplicate OBJ bone names, an optional
stock detail resource and unsigned VPK output; judge current warnings against
actual failures rather than assuming every warning is harmless. Keep the old
backup until new visual, collision and runtime behavior is verified.

## 7. Continue the interior as a small integrated route

Recommended implementation order after the baseline compiles:

1. Calibrate the vertical model. Keep the bridge equality and two red cores fixed
   as facts; resolve metric heights and riser/landing arrangement from the new
   high-resolution photos and available plans. Do not duplicate a floor-1 plan
   into floor 2 and label the new room inventory as observed.
2. Build the two distinct Povo 1 stair connections and the bridge-level landing/
   corridor as a limited test route. Establish Povo 2 landing locations and rises
   separately. Ground Povo 2 and ground Povo 1 are not equated by the evidence.
3. Refine the identified A215 and its courtyard background. Keep A211/A212 as an
   ambiguous reference until the room is identified. Add needed door/window
   leaves and actual Source 2 materials/entities deliberately.
4. Replace the relevant solid exterior massing with a hollow section, reconcile
   facade/window positions, and author collision. Putting the offline room inside
   the existing opaque solid building does not create a usable entrance.
5. Test a doorway, stair, desk row and window with a real player before expanding
   the interior. Verify crouched sightlines, cover/penetration, step traversal,
   door clearance and navigation. The OBJ opacity hint is not breakable glass.
6. Keep the rest of the campus as reference/backdrop until this route works.
   More detailed geometry does not by itself improve the compact mode's balance.

Coordinate contract: source models are local metres, east +X / north +Y / up +Z,
origin `(666250, 5103800, 370)` in the existing geographic frame. The established
ModelDoc import uses 39.37007874 units/metre and the placed prop pitch `-90 0 0`.
Live campus floor drops corrected the earlier sign assumption: world X is
**negative north**, world Y is east, and world Z is up. The symmetric outdoor
arena did not expose that sign error. Apply the conversion
once; new Blender/ModelDoc pieces must be calibrated against the same origin and
orientation. Imported OBJ/MTL materials require actual Source 2 material work.

## 8. Package, test and save Windows work

Compiling radar as loose resources after the map does **not** insert those
resources into the existing VPK. Follow [POVO_RADAR.md](POVO_RADAR.md) and
[CS2_PACKAGE_CHECK.md](CS2_PACKAGE_CHECK.md), then inspect the actual package:

```powershell
$mapPackage = Join-Path $cs2Install 'game\csgo_addons\trento_povo\maps\trento_povo.vpk'
python tools/verify_cs2_package.py "$mapPackage" --full-crc --report build/windows-package-check.json
Get-FileHash -LiteralPath $mapPackage -Algorithm SHA256
```

The checker verifies expected radar entries, overview fields and entry CRCs; it
is not a complete dependency/signature/gameplay test. Missing radar means the
packaging step is incomplete, even if loose development files make it work.
Do a clean-install test without those loose files, finish a round with buy/plant/
defuse/restart checks, and connect two independent clients before claiming the
multiplayer/distribution gates complete. Public Workshop publication is a later
step and is not requested by this handoff.

Before leaving Windows, inspect/synchronize the intended Hammer/ModelDoc/material
source changes back into the repository:

```powershell
python tools/cs2_project.py --cs2-root "$cs2Install" sync-from-cs2 --dry-run
# After reviewing the listed changes:
python tools/cs2_project.py --cs2-root "$cs2Install" sync-from-cs2
git status --short
git diff --stat
```

The sync list covers known VMAP, ModelDoc, material, addon-info and map-config
files. New custom models/materials/entities may need additional source files and
deployment/sync entries; inspect them explicitly. Generated custom radar remains
managed separately. Keep build logs/artifacts locally under `build/`, and record
material findings, tool versions, successful/failed gates, assumptions and next
steps in `docs/WORKLOG.md`. Commit/push reviewed source so Linux and Windows
continue from the same state.
