# Campus gameplay proposal — 24 October 2026

Draft for discussion, targeting flexible teams with 2v2 as the main case.
These are proposed placements and timing goals, not a compiled gameplay change
or measured match balance. The existing exploration package remains the current
runtime checkpoint.

## First playable layout

Start with one bombsite in the northern part of Povo 1. Four players should
share a small set of encounters instead of defending sites in separate buildings.
Use the existing architecture as the basis and preserve full-campus exploration.

| Element | Proposed location | Purpose |
| --- | --- | --- |
| Site A | First-floor Aula studio ponte, beside the Povo 1 end of the bridge | A recognizable room with space to shape planting and cover; replaces the narrow upper east-corridor trigger |
| T spawn | Ground east corridor, south of the northeast red stair | Bring attackers close to their first route decision without starting inside the site approach |
| CT spawn | First-floor north corridor toward the northwest stair | Give defenders time to reach A or contest the alternate approach |
| Direct attack | Ground east corridor → northeast red stair → upper east/north junction → A | Short, readable main approach |
| Alternate attack | Ground north corridor → northwest red stair → upper north corridor → A | A slower flank that does not require circling the south end of the building |
| Bridge | Povo 1 end retained as a short, visibly bounded approach/pocket | Retain the landmark without making a trip through Povo 2 mandatory |

The room's current access is not sufficient to assume a good bombsite. Inspect
its furniture and door before choosing the final plant rectangle. Prototype a
second doorway from the adjacent bridge corridor into the room so its entrances
can be covered from different angles. This is a deliberate gameplay adaptation,
not a claim about the real building. Both approaches must reach their entrances
before merging; two routes ending at the same doorway do not count as two site
approaches.

Begin with one clear plant area, a limited number of readable cover positions,
and space to move around the planted bomb. Prevent a single position from seeing
both entrances and every plant spot. Keep CT spawns out of direct attacker view,
give both teams local buy zones, and verify all spawn slots for collision,
overlap and fair route access. Reserve enough starts for later larger-team tests;
2v2 determines the initial route and site balance.

## Shorter travel

The source has a 30 m bridge, an 83 m-long Povo 1 footprint, and a front walkway
test route extending from northing -71 to +31.35 before its entrance turn.
Those distances precede room approaches and stair travel. They explain why
using the entire campus for every round risks long, empty rotations.

For the first match version, concentrate play around the two northern red stairs,
the connecting corridors and A. Give the south building wings, most classrooms,
Povo 2 and underground parking visible match boundaries. Boundaries must block
players and bots consistently and preserve readable radar; full exploration
keeps those areas accessible. This needs a separate match layout/variant rather
than a launcher change alone.

Keep normal combat movement as the initial baseline. First shorten route
distance, remove unnecessary detours and place spawns near meaningful decisions.
Only add another cross-connection if timed walking shows that the northwest
flank is too slow. Label A, Bridge, East Stairs and West Stairs on signs/radar.

For exploring the current package immediately, `play_campus.cmd -Fly` already
provides noclip. A faster exploration-only walking option could be added
separately; it should not supply the movement settings used for balance tests.

## Timing and round checks

Initial design goals, timed from the end of freeze time at normal movement:

- CT reaches a defensive choice before the fastest T can enter A.
- First contested contact around 8–12 seconds on the direct route.
- Alternative route costs only a few additional seconds and gains another angle.
- A useful defender reposition or retake route takes about 10–15 seconds.

These targets may change after walking and played rounds. Record weapon held,
spawn slot, path, floor changes and elapsed time; use actual collision routes
rather than straight-line distance. Test fastest and slowest spawn slots.

Then verify buying, bomb assignment, planting at the edges of the intended
area, defusing, elimination, explosion, round restart and both team assignments.
Run real 2v2 rounds to check how often each route is useful, whether one defender
can lock both entrances, and how long players spend searching after a plant.
Navigation exists but tactical bot analysis is currently skipped for the large
exterior; bots can help find path failures but cannot establish balance.

## Later expansion

Test the same single-site layout with larger teams first. If it becomes crowded,
consider an extended layout with Site B around Povo 2's ground entrance/table
hall. Time the complete A–B rotation through real stairs before enabling it;
adding a site across the campus alone does not solve travel time. Do not put the
second site in underground parking for the first iteration.

## Source evidence

- `tools/cs2_campus.py`: six starts per team, T in the Povo 2 entrance hall (moved from the Povo 1
  ground entrance on 28 October),
  CT upstairs, and a single upper east-corridor objective.
- `exports/povo_campus/provenance.json`: room bounds, four stair cores, bridge
  bounds and integrated Povo 2 floor/stair layout.
- `tools/playtest_povo_exterior.py`: existing ground routes and walking checks.
- `tools/play_povo_campus.ps1` and `tools/cs2_explore.py`: current Wingman launch
  and solo exploration setup, including the existing Fly option.
