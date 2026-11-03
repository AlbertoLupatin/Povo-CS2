# Fixture and frontage-lamp repairs — 2 November 2026

Source implementation is complete. Native candidate compilation and game review
are in progress; the standard launcher package is still the previously reviewed
entrance/fill version until the candidate passes its remaining checks.

- Suppressed 16 ceiling fittings and their indoor light entities above Povo 1's
  open upper terraces. Roofs remain open.
- Removed the complete original fittings before the Povo 2 stair-well cut can
  leave two ceiling-light fragments on the exterior wall.
- Restored frontage posts 0/1 down to surviving paving at Z4.12 / Z4.00 m.
  Their heads retain their positions. Removed obsolete aula lamp assemblies
  5/6, rather than passing poles through the building.

All **381 source tests pass**. The new mounting regression checks every visible
ceiling diffuser and the complete supported bases of the restored posts.

[Source preservation](source-preservation.json) confirms identical approved
basement metadata, room records, existing exterior meshes and non-lamp collision.
Only audited fitting/lamp boxes changed: 27,843 source visual boxes and 12,554
collision boxes remain before export/entity extraction. The exported model uses
26,831 visual boxes and 11,816 collision boxes.

Both [campus](main-overlaps.json) and [paving](paving-overlaps.json) surface audits
pass with zero coplanar overlaps. All 631 breakable panes, nine automatic door
banks and 64 deathmatch spawns retain their preceding source records.

Native build logs: `build/lighting-fixes-20261102/native-build.log` and
`native-build-errors.log`. Candidate: `build/lighting-fixes-20261102/candidate.vpk`.
Previous standard package/manifest: `build/lighting-fixes-20261102/backup/`.
`build_candidate.py` builds an isolated candidate; `promote.py` requires passing
source, compiled, visual and walking reports before replacing the launcher copy.

The existing asphalt grade defect is outside this lighting repair and remains
unchanged. Winter and Workshop have not been updated.
