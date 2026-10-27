# Standard native build evidence — 27 October 2026

Completed at 19:17 Europe/Rome from source checkpoint `14a8ef5`, pushed on
`codex/photo-additions-windows`. This directory preserves the full
[compile log](compile.log) and [package verification report](package-check.json).

- Pipeline exited 0. Map: 707 compiled, 0 failed. Model: 1 compiled, 0 failed.
- Five radar sections compiled. Generated navigation contains 12,566 areas.
- Standard VPK: 61,351,046 bytes, 976 entries; all 976 entry CRCs verified.
- Package report status: `passed`; `all_entry_crc_requested` is true.
- SHA-256: `2edab45d2625ec635410e0d9af5f353842e6ca51d1cee8b225adb48b05692b61`.

The model compiler retains the known DuplicateBone warning. Navigation reports
two unconnected ladder tops at `(2683.07, 410.236, 444)` and
`(-571.653, 860.236, 444)`. The earlier sketch build had the same two warnings
at Z302. These are known bot-navigation limits; source physical stair/ladder
clearance checks do not establish in-game bot traversal.

No post-build engine/session tests were run, as requested by the user. This
build covers STANDARD only; the winter VPK was not rebuilt. Package signature
verification is not performed by this report. The local previous package is
preserved at `build/package/trento_povo_campus-pre-survey.vpk`; neither VPK is
included in this evidence directory.

Metric/photo registration remains provisional. Full Povo 2 photographed plans
are saved review data; they are not activated by this successful compact-route
build. The separately saved east-lab door evidence still needs a stepped
footprint refinement before assigning an exact registered opening segment.
