# Resume the Povo project on Windows

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
Its resulting map axes are world X=north and world Y=east. Apply the conversion
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
