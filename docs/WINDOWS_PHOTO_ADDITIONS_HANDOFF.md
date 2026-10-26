# Windows handoff: 26 October photo additions

All photo-guided implementation, tests, generated OBJ/collision/provenance,
materials, radar sources and the corrected review image are committed together.
The bridge, existing Povo 2 floor elevations and two-floor Povo 1 adaptation
are retained. No Windows compile or engine playtest was possible in the cloud.

## Resume

From the existing Windows checkout, preserve local work and pull `main` using
`git pull --ff-only`. Use its existing Windows Python environment; do not copy
or try to activate the cloud Linux `.venv`. Python dependencies used here:

```powershell
python -m pip install Pillow==12.3.0 blake3==1.0.8
python tools/cs2_project.py doctor
python -m unittest discover -s tests -q
python tools/audit_povo2_integrated.py
python tools/audit_povo_wings.py
python tools/audit_povo_yard.py
python tools/audit_povo_exterior_integrated.py
```

Cloud validation: **154 tests passed, no skips**, campus/interior/exterior
clearance passed, both wing stairs and the basement exit/yard routes passed.
Dimensions, inferred room numbers, furniture counts and the aula magna remain
blockout estimates. The corrected review is
[photo_additions_review.png](../exports/povo_campus/photo_additions_review.png).

Before deploying, back up the installed addon source/game trees and previous
working package using the existing backup guidance in WINDOWS_RESUME.md. Keep
local Hammer edits separate; do not sync old installed source over this update.
Set `CS2_ROOT` if doctor cannot find the existing Windows CS2 Workshop Tools.

## Build and verify the campus

The pipeline needs the installed Workshop Tools `dmxconvert.exe` and
`resourcecompiler.exe`. The committed campus VMAP is the older binary; the
following command regenerates it from the new geometry/metadata before compiling.
The VPKEdit 4.4.2 Windows CLI must already exist at
`build/tools/vpkedit-4.4.2/vpkeditcli.exe`; installation reference:
[CS2_PACKAGE_CHECK.md](CS2_PACKAGE_CHECK.md). That ignored executable and the
previous VPK are not included in Git.

```powershell
python tools/cs2_campus.py
python tools/verify_cs2_package.py build/package/trento_povo_campus.vpk --map trento_povo_campus --overview exports/povo_campus/radar/trento_povo_campus.txt --full-crc --report build/package/photo-additions-check.json
```

Do not use `play_campus.cmd` to judge this update before the rebuild succeeds:
it can otherwise load the previous working package. After compilation/package
verification, use that existing launcher and the playtest workflow.

## Required in-game review

- Confirm 316 breakable panes, 54 sliding-door parts and 9 sensor triggers in
  the newly generated campus map; test all 9 banks, glass and player openings.
- Povo 2 reception: stair entry beside reception, straight corridor, PC room
  first on its short branch, then the provisional B108/B109 classrooms. Verify
  walking, furniture, room labels, lighting and the preserved stair/lift routes.
- Basement: from the stair exit, right then right reaches CIBIO (offices on
  the left); left a few metres then right reaches the locker/exit route. Walk
  through both push-door openings, the indoor steps, yard and outdoor steel
  stairs to the existing pavement. Check the low CIBIO ceiling below the road.
- Aula: reach its lobby from the table corridor, turn right through the short
  edge into the temporary hall; check stage, seating and centre aisle.
- Canteen: enter from Povo 1 farther south. Bar is right, smaller ground dining
  area left, stairs straight ahead. Walk the projecting L-shaped porch, both
  sliding banks, stair/fire-door approach and upstairs pavement exit.
- Library: Povo 1-side entrance, ground reception, both floors' reading rooms
  and stairs; confirm placeholder cores are absent and facade panes break.
- Recheck the unchanged bridge, both lift ladders, existing outside routes,
  radar floor alignment, lighting/reflections, navigation, bots and frame rate.

Keep source-audit success distinct from engine movement, visibility, bot
navigation, package integrity and multiplayer readiness. Update the worklog
with Windows compile/package logs and actual playtest results.
