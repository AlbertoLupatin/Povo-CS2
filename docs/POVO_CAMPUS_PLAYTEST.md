# Povo 1 campus implementation

Current seasonal builds, moving doors, breakable panes, physical surfaces and
local match evidence are documented in
[POVO_SEASONS_AND_INTERACTIONS.md](POVO_SEASONS_AND_INTERACTIONS.md).
Use `play_campus_winter.cmd` for winter or `play_campus.cmd` for standard;
both retain the saved fullscreen setting. Build both with
`python tools/cs2_campus.py --season both`.
The older counts and implementation descriptions below are historical.

The [Povo 2 connection and sign revision](POVO2_CONNECTION.md) supersedes the
room count and deferred-bridge notes below: 61 furnished rooms total, A202/A203
downstairs, a connected floor-1 bridge, and the first Povo 2 arrival section.
There are now 99 source tests and 161 clearance stations. Continue the upper
northeast corridor toward the former A202/A203 area to reach the bridge.

The latest room and stair revision is recorded in
[the room/stair review](POVO_ROOMS_STAIRS_REVIEW.md). Earlier appearance comparisons
are in [the visual review](POVO_VISUAL_REVIEW.md). The original package identity
at the end of this document is historical.

The new map is `trento_povo_campus`; `trento_povo` retains the previously
accepted outdoor arena. Both are built from the same addon source.

User feedback is implemented as follows:

- Ground A103–A106 repeat the A103 classroom family.
- Ground A107–A110 use the A101 classroom family, within their accepted footprints.
- All 56 rooms are open and furnished, including A101/A102 and the computer/lab
  spaces. Repeated desk/seat rows, boards, wood floors and ceiling fixtures fill
  the previously empty bays. Internal study rooms do not gain exterior windows.
- Added rooms give the broad north area a normal corridor with rooms on both sides.
  Circulation floors use a lighter off-white finish.
- Four identical mirrored red switchback stairs join ground and first floors in
  front of Studio N1/N2/S1/S2. The central Aula studio rooms are unchanged. Each
  stair has twenty 18 cm risers, 28 cm treads and 1.5 m wide flights, opaque walls
  and open black double doors with red panic bars on both floors. Floor heights
  and stair dimensions remain estimates.
- The solid Povo 1 exterior mass has been replaced by the interior shell.
  Courtyard glazing, ceilings, lighting, room labels and a short entrance landing
  are included. Povo 2 and the bridge remain backdrop.
- T starts in the Povo 2 entrance hall, CT starts on Povo 1's top floor, buy zones, one upper east-corridor bomb
  target and a radar with separate floor images provide a playable prototype.
  Competitive balance remains open.

## Build and launch

```powershell
python tools/cs2_campus.py
python -m unittest discover -s tests -q
python tools/audit_povo_campus.py
```

With Steam running and CS2 closed, double-click `play_campus.cmd`.
It checks and installs `build/package/trento_povo_campus.vpk` into a separate
test addon with no loose custom assets, then opens the map in Workshop Tools mode.
The installed CS2 Workshop Tools are required. For a different Steam location,
run `tools/play_povo_campus.ps1 -CS2Root 'your installation directory'`.

The launcher starts solo exploration by default: one human, no bots, paused
warmup, no round limit, respawns and invulnerability. `play_campus.cmd -Fly`
starts with noclip; `play_campus.cmd -Match` retains normal match defaults.

## Walking and gameplay checks

1. Start as T at the ground entrance. Walk into A103–A106 and A107–A110;
   reach both ends of the desk rows. A101/A102 should also be accessible.
2. At each corner Studio, walk through the open black doors, up both red stair
   flights, turn at the landing and return down without jumping or noclip.
3. Walk the upper corridor loop and enter A215, A223/A224 and the other rooms.
   Check door clearance, furniture collision, overhead clearance and window views.
4. Confirm the radar changes floor at the stair. Buy in each spawn zone,
   plant at the upper east-corridor A marker, and complete a round.
5. Check bots can move between floors. A separate two-client match and
   performance/balance review remain release checks.

The generated clearance audit checks a standing envelope 0.82 m wide and
1.85 m tall against the simplified game collision on each floor. It checks
65 ground stations, 120 upper stations and four lower-vestibule stations,
including classroom side aisles, all four stair endpoints and both sides
of each stair portal. Low overhead slabs and raised floor surfaces count
as obstacles. The separate integrated Povo 2 audit checks 8/8/17 stations
and 72 stair samples; the exterior audit checks 1,234 samples on nine routes.
It does not establish vertical traversal or replace the CS2 checks above.

The [latest user corrections](POVO_USER_CORRECTIONS.md) pass 41 engine walking
waypoints on 13 routes and three wall/fence blocking checks. Run `python tools/playtest_povo_exterior.py`
after the solo launcher finishes. It requires this map with one human and
zero bots; it writes timestamped package-identifying evidence to
`build/gameplay/`. Use `--output` to preserve a separate run.

The editable definitions are `config/povo1_campus.json`,
`tools/build_povo_campus.py` and `tools/cs2_campus.py`. Generated model/radar
assets and their provenance live in `exports/povo_campus/`. Physics keeps
structural surfaces and desk/chair profiles, combines narrow seat gaps, and
omits small supports beneath the furniture. The original interior study remains
separate. Exact furniture counts, unseen finishes and facade details are provisional.

Live floor-drop calibration establishes Source coordinates as
`(-north, east, up) * 39.37007874`, after the existing ModelDoc import and
`-90 0 0` placed-prop rotation. Entity, lighting and radar placement all use this
same transform. The north sign corrects an earlier untested documentation assumption.

## Historical initial Windows checkpoint — 23 October 2026

All 90 Python tests pass. The final model, map and four radar textures compile
with zero resource failures. The map retains 2,150 nav areas. Model import has
the same nonfatal duplicate-bone naming warning as the baseline static model.
The indexed OBJ exporter shares vertices, puts attributes before faces, supplies
flat normals and gives vertical surfaces valid UVs; the model now compiles in
about 14 seconds on this machine.

The package is 25,247,460 bytes with 107 entries. All entry CRCs
and staged asset SHA256 checks pass. Its SHA256 is
`9000e3617b5ae6ffcd997827f65a4e229db35a22b4fbd3bd90da805518e2017e`.
The game test addon contains only this VPK, addon metadata and diagnostic
screenshots. It loads server/client physics, both radar sections, one human
and three bots. Glazing uses the installed game's `materials/glass/glass01.vmat`.

Normal forward movement, with turns at the landing and no jumping/crouching/
noclip, traversed both flights up and down in the final package. Recorded foot
heights are approximately 157.5 → 228.4 → 299.7 Source units, then back to 158.0.
Separate room probes entered A103 and A109 and stopped at the sealed A101/A102
walls. A T-side `autobuy` created an AK47 with unrestricted buying disabled.

Logs and package reports are in `build/gameplay/` and `build/package/` locally:
`campus-release-build.log`, `campus-final-runtime.log`,
`campus-final-stair-traversal.log`, `campus-room-traversal.log`,
`campus-objective.log`, and `trento_povo_campus.json`.

Plant/defuse, CT buying, a complete round, bot traversal between floors, visual
quality, performance and an independent second client remain manual checks.
Background engine screenshots did not provide a reliable visual review. The
runtime also reports missing optional map artwork/camera-node files and an
unbaked reflection cubemap array; reflection baking remains a lighting task.
These checks are not claimed as passed. The game is returned to cheats off,
moving bots, normal round timing and a fresh round for the user's playtest.
