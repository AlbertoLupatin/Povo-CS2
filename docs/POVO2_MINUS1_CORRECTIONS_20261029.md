# Povo 2 level -1 — user corrections, 29 October 2026

Status: **native rebuild and engine checks passed**. The corrected layout is in
the local standard package. All 12 selected -1 walking routes pass;
both new fixed doors block movement from both sides before and after Use.
The isolated test game was closed after the batch.

The user rejected the former -1 layout and supplied
`data/reference/user_feedback/2026-10-29/povo2_minus1_corrections.png`, followed
by a distance estimate, a width clarification and a request to close the L.
These instructions supersede the previous retained -1 route and exit-turn scope.

## Corrected geometry

- The lower stair corridor continues east to the existing outdoor exit corridor.
- Room 1 and both laboratory room sizes remain fixed. Room 2 and the upper
  return move 25 m north, increasing the clear gap between the rooms from 5 m
  to a provisional 30 m. The user counted about 35–40 long steps; an explicitly
  stated 0.8 m/step assumption yields 28–32 m. This is an estimate, not a survey.
- Only the section between the labs is narrowed: remove its west/left half and
  keep a nominal 1.5 m corridor on the east/right (about 1.3 m between the
  centred wall faces). Room entrances retain their
  original wider approaches. Furniture, Room 2's doorway and audit stations
  follow the moved room.
- A permanently closed door spans the upper return where marked “Put door here”.
- A second permanently closed door spans the northward left turn at the new
  lower-right junction, toward the EXIT CORRIDOR label.
- Both pairs of leaves are static solid geometry in the structural render and
  collision model. They have no door entities, opening sensors, Use handlers
  or breakability. The upper/right L is deliberately inaccessible.
- The labs connect back down the narrow spine to the lower corridor, which
  leads to the outdoor exit south of the second door. The exterior UP and DOWN
  stairs, garden elevations, stair core and level -2 stay in place.

The questioned black piece was the outdoor UP stair and its railing collision
projected by the old plan slice. The revised review shows the actual stair
treads in gold and labels UP TO STREET / DOWN TO -2.

[Corrected geometry review](../exports/povo_campus/povo2_minus1_corrected_20261029.png).

## Implementation and source checks

`config/povo2_minus1_corrections.json` records the latest user intent and metric
assumption. `tools/povo2_minus1_corrections.py` applies it in campus coordinates
before `tools/povo2_basements.py` builds the final shells. Radar and floor audits
use the actual disjoint floor pieces, including the narrowed section. Radar
shades the inaccessible L separately.

The 269-test suite passes. Targeted tests confirm the 30 m gap, removal of the
west half, solid door leaves without opening entities, and isolation of all
four closed-L stations while every active station stays connected. The source
standing-envelope audit passes 1,901 route samples and all 12 parking, 20 active
basement and 50 ground stations. All 298 retained Povo 2 boxes entirely below
the -1 floor band match the saved pre-correction geometry exactly.

The build initially stopped before native compilation because the radar assumed
every basement dictionary entry was a single rectangle. It now consumes the
rebuilt floor pieces, and the radar regression test includes actual Povo 2
metadata and both basement overviews. That test passes. The successful export
and prepared VMAP are hash-checked and reused for the resumed native build.

## Native verification

Build evidence: `build/minus1-correction-20261029/` and
`build/handoff/20261029T113001717601Z/`.

The verifier checks compiled basement floors, parking columns and both
surfaces of both fixed doors. Its isolated solo game batch attempts to walk
through each door from each side, presses Use and repeats the attempt. It then
captures the narrow corridor, moved room, both doors, lower connection, outdoor
stair and pavement control views, and walks the accessible -1 routes in both
directions. It closes CS2 in `finally`, with a process-specific fallback.

Results are saved in
`exports/povo_campus/runtime/minus1_corrections_20261029/`. Source checks alone
do not establish engine movement. Winter and Workshop are outside this build.


## Completed native results

The package contains 1,082 entries; all CRCs pass.
SHA-256: `d6891711d74524fe0c5cfb62087d6e5fd8809e915f8ded32d83094d1e8c17f48` (45,089,434 bytes).

Compiled PHYS checks pass 15,601 basement floor points,
72 parking-column points and 24
surface points on the two fixed doors. The eight native walk/Use attempts
cannot cross either door. All 12 accessible -1 walking routes pass.
Normal-lighting courtyard and street pavement controls pass as well.

[Native screenshots](../exports/povo_campus/runtime/minus1_corrections_20261029/gallery.md).
`completion.json` consolidates the package and check identities. The 30 m
distance remains an estimate from the user's step count. Winter and Workshop
were not updated.
