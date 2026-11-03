# DEFINITIVE POVO 2 −1 MAP LAYOUT

**Status: FINAL — explicitly approved by the user in-game on 2 November 2026.**

The user confirmed: **“map layout is perfect”** and instructed that this be
published as the **definitive Povo 2 −1 map layout**. The current implemented
layout is the source of truth. Earlier sketches, proposed layouts, photo-based
reconstructions and unresolved-layout checklist entries are superseded wherever
they disagree with this approved implementation.

## Approved layout

The approval covers the complete current Povo 2 −1 floor layout, including:

- The West Offices room partitions and WI1–WI4 passages/openings.
- Straight C7 past the main stair core, without the former jog or narrowing.
- C5, its connection to WI1/C7 and its permanently sealed northern end.
- The closed E1/E2 room footprints and their shared corridor/facade boundaries.
- The retained main stair/lift-core registration, lab connections and permanently
  closed boundaries isolating restricted research circulation.
- The continuous south terrace and its entrance/opening arrangement.
- The UP stair directly opposite C5 and the two-flight DOWN stair along the
  eastern terrace run, with their landings and connection to the lower garden.

Preserve these room, corridor, door/opening, stair and terrace relationships
when improving materials, lighting, props, other floors or exterior scenery.
Do not replace them with an older proposal or infer a different layout from an
earlier plan. A later user-requested layout change must be documented as a
revision of this approved baseline. Approval here applies to Povo 2 −1;
remaining work on other floors/buildings and exterior finishing stays separate.

## Implementation and exact approved build

The [2 November finishing pass](POVO2_MINUS1_FINISHES_20261102.md) adds the
user-requested glazing, office furniture and missing wall/closed-door finishes.
It retains all room bounds, labels, corridor extents, stairs and terrace coordinates.
The package identity below records the original approved layout checkpoint.

The definitive layout is the **assembled final geometry**, including the
West Offices and straight-C7 pass followed by the user's Draw.io entrance pass.
`config/povo2_east_entrance.json` is a legacy intermediate input, not a standalone
description of the final floor.

- Assembly: [campus generator](../tools/build_povo_campus.py),
  [West Offices](../tools/povo2_west_offices.py),
  [Draw.io entrance replacement](../tools/povo2_drawio_entrance.py).
- Current source model/collision and registration:
  `exports/povo_campus/povo1_campus*.obj` and
  [provenance](../exports/povo_campus/provenance.json).
- User's preserved drawing:
  [east_entrance_edited.drawio](../data/reference/user_feedback/2026-10-31/east_entrance_edited.drawio).
- [Compiled entrance-region collision plan](../exports/povo2_drawio_entrance_20261031/compiled_plan.png)
  (local review, not a complete floor drawing).
- Native normal-lit views: [C7](../exports/render_corruption_20261102/normal-lighting/c7.png),
  [C5](../exports/render_corruption_20261102/normal-lighting/c5.png),
  [WI1](../exports/render_corruption_20261102/normal-lighting/wi1.png),
  [UP stair](../exports/render_corruption_20261102/normal-lighting/up_stair.png),
  [DOWN stair](../exports/render_corruption_20261102/normal-lighting/down_stair.png).

Approved standard package: `build/package/trento_povo_campus.vpk`.
SHA-256: `6a52dc98ddf5050f430894597337ec86361557d95adf9f1798771a8e1f74c9ee`.
Shared structural model SHA-256:
`efec420634ce87e2bd42a29538b2890b2c1ce551cb27ca7c2917b02fb7f75d96`.
The VPK is a local build artifact and is not stored in Git.

Validation: 363 source tests, 1,237 verified package entry CRCs, 80 compiled
entrance checks and the full basement floor/column/fixed-door surface checks
pass. Nine actual game views were inspected with normal lighting enabled;
the user then explicitly approved the layout. See the
[lighting repair record](RENDER_LIGHTING_CORRUPTION_20261102.md) for package and
visual evidence. Existing coordinates retain their recorded source provenance;
this approval establishes the final map layout rather than a new metric survey.
