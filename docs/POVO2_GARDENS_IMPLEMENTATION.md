# Povo 2 approved exit and garden layout

28 October 2026. Supersedes the earlier side-branch layouts and their preview
images. Reference: the user's blue markup, approved proposal v2, and subsequent
confirmation to extend the garden footprint underneath the fixed stairs without
raising its floor elevation.

- A straight indoor corridor reaches a south-facing -1 exit. Its distant left
  turn is outside the local diagram and connects to the existing laboratory
  corridor. The two playable laboratories and their doors remain in place.
- UP lies directly ahead of the exit. The short level passage runs east (right
  in the approved drawing), continuing directly into DOWN on the same axis.
- DOWN starts at the beginning of Garden -2 and ends halfway along its length.
- The garden footprint extends south under the descending flight. Its floor
  remains at local z=-3.2 m, the existing -2 level. The passage remains at z=0.4 m.
- The street garden now extends west to meet the fixed UP stairs, with its lawn
  brought to the stair edge. Two garden regression checks pass after this change.
- Street garden and ground-floor entrance courtyard remain separate exterior
  spaces. The existing sloped sidewalk is preserved.

The route topology is user-approved. Metric registration, distant indoor turn
position, landscaping, flight dimensions and step counts remain provisional.
The long indoor connector is a connected source reconstruction, not a newly
measured survey of restricted interiors. Annotation colours are not materials.

[Generated implementation preview](../exports/povo_campus/povo2_gardens_implemented.png).
[Preserved user markup](../data/reference/user_feedback/2026-10-28/povo2_gardens_user_markup.png).

## Validation and build status

Current source routes pass 2,121 support and standing-clearance samples, including
exterior collision meshes. Eleven garden/basement tests and the integrated lower-floor follow-up pass. The
full suite ran 239 tests with seven failures. One was the old station-count
expectation, corrected and rerun successfully; six broader stair, door and
garage-route checks remain failing. This is not a passing full-suite claim.
See [validation summary](../exports/povo_campus/gardens_approved_validation_20261028/summary.json)
and adjacent raw logs.

The earlier 236-test/1,388-sample reports in `gardens_validation_20261028` describe
the superseded layout. Current evidence is kept separately under
`exports/povo_campus/gardens_approved_validation_20261028/`.

Native compilation was stopped at the user's request. It has not been restarted;
no VPK of this approved layout has been produced and native traversal is untested.
The separately implemented reception-side stair/vestibule reconstruction is preserved; the garden pass now runs after it so garage infills cannot seal the approved corridors.

## Reproduce source checks and exports

`python -m unittest discover -s tests -q`

`python tools/audit_povo_yard.py`

`python tools/build_povo_campus.py` (source/model export only)

`python tools/render_povo2_gardens.py` (requires Pillow)
