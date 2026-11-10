# Povo 2 −1 exterior terrace integration

## Joined west terrace and office frontage

The follow-up screenshots showed separate plates beside the west offices and
concrete remnants across the CIBIO glazing. The west garage deck now meets the
facade-side terrace at Z0.4. A strip from the south corner crosses the former
break at the office side of the ramp. The deck links both recessed bays and
the north run. Guards follow the two remaining garage lightwells and the open
ramp edge. The descending driveway and the 5.5 m portal retain their clearance.
The CIBIO windows retain their registration and receive flush aprons after
the old garage roof lip and floating site concrete are trimmed back.

On floor 0, the west corridor keeps a single level ceiling at Z7.28. The old
shaft cap is removed and the lower face of the overlying context clears the
ceiling panels. B106 receives seven rows of computer desks. B108 and B109 each
receive seven raked rows of classroom seating using the existing furniture kit.
The three rooms use one line of separately breakable window panes at N10.8,
with the original B106 window material. Room and door positions are retained.
The terrace connection widths and furniture counts are fitted to the model.

The standard VPK is 75,077,268 bytes. All 1,557 entry CRCs passed.
SHA-256 `e94a799f3470c0f231e477204dc03b8f8ebeda82ad512e91fef2ccb55dc0c606`.
The render audit found zero overlapping coplanar faces among 767,899 faces.
The packaged physics mesh passed 669 targeted samples and the basement floor,
column and fixed-door regression checks. The packaged entity lump contains
eight separate breakables for B106, seven for B108 and six for B109.
All 474 source tests passed across the main run and the native-permission
rerun of the terrain export tests.
Build evidence and the previous standard VPK are in
`build/povo2-followup-20261108/`. Use `play_campus.cmd` to load the updated
standard package.

On 9 November, a fresh solo addon loaded the verified VPK. All 21 classroom
panes and both CIBIO exterior panes broke when shot. A review of 14 views with
normal lighting confirmed the flat corridor ceiling, room furnishings, shared
glazing finish, joined deck and cleared CIBIO window faces. The north view
was retaken from the terrace after the first camera intersected the podium.

All 16 standing walks and 60 waypoints passed across the initial run and
two rechecks. The walks cover both directions through the classroom doors and
side aisles, the garage portal, both recessed bays, and the south and north
terrace joins. At the south turn the gutter narrows the usable line beside
the guard. The recheck walked through the centre of the strip. At the north
join, the route turns east before the curved retaining wall. The recheck
reports are in `build/povo2-followup-recheck-20261109/` and
`build/povo2-followup-walk-20261109/`. The package was identical across the
three runs, and CS2 was closed after verification.

## Deck elevation correction

The user's follow-up screenshots showed two concrete caps that the first pass
had brought up to street grade. The south deck between the sidewalk and the
office glazing and the west deck over the garage portal now both finish at
Z0.4, the Povo 2 −1 office threshold. The south deck meets the narrow terrace
strip at that level. The west deck starts above the existing 5.5 m portal,
with its underside at Z0.2 and the same −2 ramp endpoint.

Narrow retaining walls and guards take the grade change at the higher
sidewalks. The outside edge of the west deck follows the north road bend.
The three marked openings, both garden stairs and the interior registration
retain their previous layout.

The corrected standard package was built with normal-quality lighting and a
1024-pixel atlas. All 470 source tests passed. The render audit checked
759,276 faces with zero overlaps, and the compiled model passed all 588
terrace and ramp surface samples and the basement regression audit.
All 1,537 entry CRCs passed for the 74,205,056-byte package.
SHA-256 `a578feaaba1c23e33ab1a958104d154cfb0363c423f40602b92748cd14bad7d1`.
The build records and the previous standard package are in
`build/terrace-level-20261108/`.

The local CS2 test addon loaded the corrected package. All 10 ordinary walks
and 48 waypoints passed. Both directions were tested across the south deck
join, over the garage deck, along the west sidewalk, through the garage
portal and down the north stair to the garden. The game was closed after the
review. See the [south deck from the sidewalk](../exports/povo2_terrace_20261108/south_from_sidewalk.png)
and [west deck from the garage approach](../exports/povo2_terrace_20261108/garage_from_office_side.png).
Run `play_campus.cmd` to load the corrected standard package.

## First-pass implementation

The two 8 November in-game views show an exposed cut below the south roadside
footway and unsupported slabs around the garage portal. The [corrected
Draw.io terrace](../data/reference/user_feedback/2026-10-29/Povo2_Minus1_Terrace_Corrected.drawio)
and [plan 46 review](POVO2_MINUS1_TERRACE_20261029.md) establish where terrace
plates, the two wider bays and the three openings belong. The garage approach
[walk photo](../data/reference/povo_photos/walk_2026-10-23/originals/IMG_2366.JPEG)
shows the curb, concrete base and metal guards. Dimensions are fitted to
the live assembly.

## Revision to the approved exterior boundary

- The existing entrance terrace still runs from E8.5 to E31.8. The extension
  continues west to E−25.45 at the same Z0.4 between N9.09 and N10.8. The
  former west end closure is removed. A backed concrete verge meets the
  graded sidewalk above it, and a concrete soffit closes the floor 0 edge
  above the office glazing.
- The two marked west strips and wider office bays use the drawn east bounds
  and the current West Offices registration. Farther north, the sketch is
  fitted to the existing N112 floor 0 and garage edge. Three guarded openings
  expose the garage-side cut. The first looks toward the ramp beside the
  retained parking wall. The other two expose the garage floor through
  openings in the old podium roof.
- The driveway stays flush across the road junction, then descends straight
  from N1/Z3 to the existing 5.5 m portal at N30/Z−3.2. Concrete abutments,
  supported paving and guardrails close the exposed sides and the space above
  the portal. The garage floor and its main driving lane retain their bounds.
- The user confirmed that the north metal stair reaches a second garden
  identical to the one on the Povo 1 side. The north garden mirrors the
  existing 17.5 × 11.25 m footprint, paving, lawn and two stair flights
  at the same levels. The retaining rim meets the local north grade. The
  adjacent north interiors and any door from the garden into them remain
  untraced.

The approved south UP/DOWN stairs, interior room and door bounds, and the
lower garden route retain their registered positions. The terrace is fitted
after frontage registration so the new geometry and collision use the same
coordinate frame as the live roads and rooms.

## First-pass package verification

The Windows campus pipeline completed with normal-quality lighting and a
1024-pixel atlas. All 469 source tests passed with native Windows temporary
file permissions. The render audit checked 757,992 faces and found zero
overlapping pairs.

The 74,041,515-byte standard package passed all 1,537 entry CRC checks.
SHA-256 `dc8e5397d5477122b430406a62befffeac35c7c7950bc011e0ced03ffea10ab9`.
The previous standard package is saved under `build/terrace-20261108/`.

The packaged model passed 553 compiled terrace, garden and ramp surface
samples. The basement regression audit passed 12,707 floor −1 samples,
6,237 floor −2 samples, 36 column samples and 36 locked-door surface
samples. The compiler, test and collision logs are in
`build/terrace-20261108/`.

The local CS2 review addon loaded the verified standard package. All 14
ordinary walks and 48 waypoint checks passed. They cover the south terrace
join, garage ramp and portal, both west strips, both wider bays and the north
stair with its garden path, each in both directions. Each route started on
its local floor. Eight normal-lit views were inspected, including the
[south terrace](../exports/povo2_terrace_20261108/south_terrace.png),
[garage ramp](../exports/povo2_terrace_20261108/garage_ramp.png) and
[north garden](../exports/povo2_terrace_20261108/north_garden.png).
The package hash in this section identifies the build before the deck
elevation correction.
