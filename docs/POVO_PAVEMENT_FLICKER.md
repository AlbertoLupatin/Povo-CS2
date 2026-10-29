# Floor, wall and model-surface flicker — 29 October 2026

The user's screenshot shows a brighter polygon switching against adjacent tiled
flooring. The source audit found **661 pairs of overlapping horizontal floor
triangles**. Duplicate slabs occur inside Povo 2, on the Povo 1 entrance and
amenities approaches, and on outdoor paving/asphalt. Differently lit triangles
at the same depth can alternate as the camera moves (z-fighting). Native captures
reproduce the broad brightness switches and horizontal striping near the Povo 2
stair hall with camera turns of only 0.04 degrees.

The user then reported vertical surfaces too. The full-model audit found
**65,784 same-facing coplanar triangle pairs**: 40,722 vertical, 25,056 horizontal
(including undersides, ceilings and props), and six sloped. Some are hidden
internal surfaces or intentional detail overlays, rather than visible defects.

`tools/povo_render_surfaces.py` gives every coplanar patch one rendered owner in
any orientation. The OBJ exporter clips duplicate faces, preserving their union,
position, winding and interpolated texture coordinates. Specific interior finishes
take precedence over generic circulation slabs and exterior paving. Small window,
paint and trim faces retain their patches on larger backing surfaces. Different
storeys, offset layers and opposite-facing sheet surfaces remain separate.
The exterior probe-lit finish is extracted from the cleaned mesh, so it also
contains no duplicate coplanar faces. The winter render model uses the same
cleanup. Winter collision explicitly bypasses render cleanup.

All eight standard collision OBJ hashes match the pre-fix exports. Walking
heights, structural collision and the accepted basement layout remain intact.
This correction does not change the lighting shader or add a depth offset.
The earlier exterior finish retains its existing 3 mm offset and normal lighting.

Run the independent exported-face check with:

```powershell
python tools/audit_povo_floor_surfaces.py exports/povo_campus/povo1_campus.obj --report build/floor-overlaps.json
python tools/audit_povo_floor_surfaces.py exports/povo_campus/povo1_campus_paving.obj --report build/finish-overlaps.json
python tools/audit_povo_render_surfaces.py exports/povo_campus/povo1_campus.obj --report build/all-overlaps.json
python tools/audit_povo_render_surfaces.py exports/povo_campus/povo1_campus_paving.obj --report build/finish-all-overlaps.json
python tools/audit_povo_render_surfaces.py exports/povo_campus/winter/povo_winter.obj --report build/winter-all-overlaps.json
```

All three render models report **zero overlapping pairs** after regeneration.
The main model has 382,712 triangles, the pavement finish 4,095, and winter 3,316.
Clipping shared patches increases triangulation while removing overlapping area.
Regression
tests cover crossing slabs, material ownership, union area, unchanged UV scale,
separate storeys, touching boundaries and detection of duplicate triangles.
They also exercise vertical and sloped planes, both normal directions, tiny
floating-point differences, preserved window details and repeated clip vertices.
A separate 0.5 m grid comparison retains all **323,619** original floor samples,
with zero missing or added samples. All 277 source tests pass before the final
numerical-stability regression additions; the final full suite passes **279
tests**. A second grid check preserves all **1,760,041** samples across vertical,
horizontal, upward and downward axis-aligned surfaces at 2 m spacing.

Native build and runtime verification are in progress. Evidence is kept in
`build/pavement-flicker-20261029/` and
`exports/povo_campus/runtime/pavement_flicker_20261029/`.
