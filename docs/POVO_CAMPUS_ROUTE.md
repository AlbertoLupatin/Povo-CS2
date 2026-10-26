# Build the recognizable Povo campus

The [first Povo 2 connection](POVO2_CONNECTION.md) now implements the approved
game adaptation below: A202/A203 are downstairs, and Povo 1 floor 1 connects
through the bridge to the first Povo 2 upper corridor. Older deferred wording
below is retained as the decision history.

Implementation checkpoint: the accepted ground/first-floor footprints now feed
the separate `trento_povo_campus` map, including 56 open furnished rooms and four
mirrored enclosed stairs in front of Studio N1/N2/S1/S2. See
[the implementation and playtest guide](POVO_CAMPUS_PLAYTEST.md) for current
commands and checks. The sections below retain the larger campus route design;
the bridge route and Povo 2 interiors remain future work.

## Approved game adaptation — 23 October 2026

For the later Povo 2 implementation, keep two Povo 1 floors. Start the corridor
to the bridge from the current A202/A203 area and relocate those two rooms to
the corresponding empty corner on the ground floor. This is an intentional
game-layout simplification of the photographed three-floor route below.
A202/A203 stay in their current upper-floor positions until that work starts.
The adaptation is also recorded in `config/povo_campus_route.json` and
`config/povo1_campus.json`; do not add a third Povo 1 floor by default.

The user accepted the outdoor gameplay checks on 23 October 2026 with “All good”.
That checkpoint validates the outdoor prototype for the user's playtest. It does
not establish a two-independent-client match or make the campus interiors built.
The accepted arena remains the working baseline while reconstruction moves into
the buildings. The route design is recorded in `config/povo_campus_route.json`.

## First connected area: Povo 1

Build the entrance, southeast red stair, floor-1 east corridor and identified
A215 first. Use the ground/first-floor plans for room footprints and the user's
walk for floor identities and stair connections. Continue around the existing
north, west and south corridor loop, opening furnished A223/A224 as the next
rooms. The subsequent user revision opens and furnishes every room.

The first acceptance walk is entrance → southeast stairs → A215 → corridor loop
→ southeast stairs → entrance, without noclip or teleportation. This is an
architecture/traversal milestone. Its single confirmed ground-to-first stair
is not being presented as a finished competitive objective layout.

The recognizable features are the red stairs with dark nosings and metal rails,
white corridors with room signs, courtyard glazing, and classrooms with continuous
desk/seat rows, wood-look floors and rear windows opposite the board. A215's
opposite-wing glazing and external metal stair belong in its window view. Exact
dimensions, furniture counts and unseen facade details remain provisional.

## Photographed route reference (before the approved game adaptation)

The full route follows the user's actual sequence:

Povo 2 ground → its stair to floor 1 → bridge → Povo 1 floor 2 → northeast red
stair to floor 1 → A215/east corridor → southeast red stair to ground → entrance
and outside stairs → outdoor link → Povo 2 ground entrance.

That gives the campus an indoor connection and an outdoor alternative. It is
the circulation to reconstruct, not evidence that a balanced match already
exists. Keep the northeast and southeast stair cores separate. The bridge joins
Povo 1 floor 2 and Povo 2 floor 1. Povo 2 stair locations and ground elevation
still need alignment; do not infer them from Povo 1's plan.

The prototype heights are 374.0 m, 377.6 m and the separate bridge estimate
382.49 m. Their rises are inconsistent as a uniform storey stack. Keep them
adjustable and labelled estimates while fitting stair flights and landings to
the photos. Do not silently lower the bridge to the A2xx floor or invent a
complete floor-2 room inventory.

## Integrate architecture into CS2

1. Reconcile the southeast stair opening and the entrance route between the two
   plan registrations. Build landings, flights and railings with separate simple
   movement collision. Record provisional rises, tread count and clear width.
2. Replace the relevant solid Povo 1 massing with a hollow shell. Match its
   windows to the interior openings. Keep the rest of the campus as backdrop.
3. Convert the room/corridor finishes to real Source 2 materials, add ceilings
   and interior lighting, and integrate A215 and the two corridor levels.
4. Test the acceptance walk in CS2; inspect stairs, doorway clearance, desks,
   crouched views, windows, light leakage and navigation on each floor.
5. Extend through the northeast stair, bridge landing and Povo 2 approach; then
   complete the exterior route back between entrances.
6. Place team starts and the objective after measuring movement and sightlines.
   Require two useful approaches to the objective, avoid a compulsory single
   staircase choke, and prevent direct spawn fire across the bridge. Rebuild a
   floor-aware radar and test the new layout with rounds.

The courtyard is a visual anchor. An opening in the floor plan does not prove
that its ground is accessible: do not add a courtyard bombsite, door or window
jump until that connection is supported and built. Likewise, classroom desk
rows do not acquire verified cover/penetration properties just by being visible.

The next playable reconstruction should be a real entrance-to-classroom route,
followed by the campus loop. Mesiano, city streets, every room, and the uncertain
basement are later work.
