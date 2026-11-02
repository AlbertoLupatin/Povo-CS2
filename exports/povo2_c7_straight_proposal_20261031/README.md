# Straight C7 and continuous terrace (31 October)

The user approved a proposal in which C7 runs straight at N 15.23-18.0 from its
west end to C5, and the terrace is one strip from E 8.5 to 31.8. They had
reported the C7 jog and narrowing at the main stair as nonexistent ("the
corridor is straight").

`as_built_vs_proposal.png` compares the -1 floor as currently exported (top)
with that approved layout (bottom). `render_proposal.py` regenerates it from
`exports/povo_campus` collision. It also probes both bands for collision
between z 0.5 and 2.3 m and outlines either band in red if it is blocked. The
review drawing of the pre-change geometry was superseded when the 31 October
19:08 build re-exported the campus; its top panel no longer exists.

The implementation is described in `docs/POVO2_WEST_OFFICES_20261029.md` and
`docs/POVO2_DRAWIO_ENTRANCE_20261031.md`.
