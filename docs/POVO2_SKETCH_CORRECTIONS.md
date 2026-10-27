# Povo 2 — 27 October sketch and pavement repairs

Reference: `data/reference/user_feedback/2026-10-27/povo2_corrected_layout.drawio`.
The original is preserved unchanged. The user confirmed a south-facing basement
stair door after the requested clockwise rotation.

## Layout

- Aula moved east of its lobby; stage, desk and screen on the west wall, seats
  facing west. B111–B114 and their opposite table hall retain their arrangement.
- Reception extends south to N=26; stair east face moves to E=20.5 to align with
  its front. All stair flights and floor elevations remain consistent as a stack.
- Ladder shaft moves into the wall gap south of the stairs. Dedicated access at
  each floor and a new upper stair-pocket opening keep the ladder reachable.
- Basement corridors, offices, lockers, yard and exit stairs receive one rigid
  90-degree clockwise rotation. Rectangles retain their dimensions, and relative
  distances are preserved. Only interfaces to the fixed stair/lift are rebuilt.
- Ground canteen counter moves east and tables sit on its right. Bar counter
  extends east; six drawn orange tables replace the previous pair, around a white
  partition. The entrance porch remains glazed around its perimeter.

## Pavement

Continuous lower Povo 1 plaza replaces disconnected narrow paths; south and
north pavement end caps close exposed edges. A graded bridge-side apron joins
the Povo 1 ground level to the sloping road. The relocated sunken yard stays open;
its former excavation is paved over. Guards do not intrude into Povo 1 rooms.
Road-junction disks now have closed collision matching their render geometry.
Flat footway bend wedges also receive paving and collision; sloping road breaks
retain their original grade.

## Verification

- 191 source tests pass (`build/sketch-verified-tests.log`).
- 8,408 pavement support samples pass at a 0.5 m grid, for both visible and
  physical surfaces (`build/pavement-clearance.json`). Removing a repaired slab
  makes the regression fail.
- Povo 2 parking, basement and ground: 8/18/50 connected stations; 72 stair
  samples pass. Yard stairs/landings: 22 samples pass.
- Exterior routes, wings, Povo 1 room aisles, floor ledges and both ladders pass.
- Compiled ModelDoc contact surfaces pass for asphalt, concrete, glass, grass,
  metal, tile and wood (`build/sketch-compiled-surfaces.json`).
- Native standard map compile/package succeeded with zero compile failures
  (`build/sketch-verified-compile.log`). Package: 61,562,729 bytes / 944 entries.
  Post-build tests and CS2 launch are explicitly skipped at the user's request.
  Earlier runtime results do not validate this new package.

Review image: `exports/povo_campus/sketch_corrections_20261027.png`.
Editable diagram: `exports/povo_campus/povo2_layout_editable_20261027.drawio`
(4 pages / 179 shapes); a copy is also in Downloads. Rebuild with
`python tools/export_povo2_drawio.py`.
No native walking test is scheduled; the user requested stopping after the build.

Backup of pre-task sources, including pre-existing uncommitted edits:
`build/sketch-corrections-backup-20261027/`. This work does not publish to Workshop.
