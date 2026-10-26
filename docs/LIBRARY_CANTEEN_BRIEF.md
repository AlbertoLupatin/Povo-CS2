# Library and canteen brief

Design notes for the two buildings in front of Povo 1, given by the user on
26 October 2026 before reference photos. Use this together with the photos
when they arrive. Where photos disagree with this text, ask the user.

## Current state in the map

Both are the two glazed wings between Povo 1 and the front road
(`frontages.povo1_library_wings` in `config/povo_exterior.json`):

| Wing | Local bounds (x0, y0, x1, y1) m | Ground z | Roof z |
| --- | --- | --- | --- |
| `povo1_library_0` (south) | 36, -110, 52, -77 | 4.0 | 10.9 |
| `povo1_library_1` (north) | 36, -69, 52, -13 | 4.0 | 10.9 |

The `_core` placeholders are now replaced in the campus assembly by playable
interiors (`tools/povo_wings.py`); the standalone exterior study retains its
original placeholders. The covered
passage between them (y -77 to -69) leads from the street to Povo 1's external
stairs. The street-side walk is now at z 7.6, level with the wings' first floor;
their ground floors remain at z 4.0.

## Both buildings

- Two floors: ground and first.
- Entrance doors: the same automatic sliding doors as Povo 1 and Povo 2.

## Library

- Entrance as Povo 1 and Povo 2.
- Ground floor: reception desk on the right when entering; the rest is tables,
  divided into a few rooms.
- First floor: only tables, divided into rooms.

## Canteen

- Entrance: an extra piece outside the building, with the same sliding door,
  then an L-shaped entrance before entering the building itself.
- Ground floor, seen from the entrance:
  - a bar on the right;
  - the canteen itself on the left;
  - food (serving) desks along the right side, reaching about half the length;
  - tables on the left, and in the other half of the length;
  - at the front, a couple of tables and the stairs (similar to Povo 2's stairs,
    but not identical).
- First floor: only a serving desk and tables.
- First floor exit: straight out onto the pavement towards the street.

"Right" and "left" are as seen when walking in through the entrance.

## Photos (26 October 2026)

P110–P117 (photos 21–28 of that set, see
`data/reference/povo_photos/LOCATIONS.md`):

- 21–23: the canteen's entrance porch, the glazed piece projecting from the
  building, with an automatic sliding door at each end.
- 24, 27: ground floor, left part, the bar: orange counter, high tables and
  orange stools.
- 25, 28: ground floor, right part, the canteen: orange and blue tables, long
  orange serving counter on the right, glazed outer wall on the left.
- 26: ground floor, front part: a black double fire door leading to the
  stair.

## Remaining approximations

Library room counts, partitions, furniture capacities and exact stair positions
remain estimates. The canteen's automatic first-floor exit is a consistent
entrance-family choice, not a confirmed observation. The existing Povo 2 entrance/bridge
floor arrangement is retained, as the user requested.

## When building

- Remove each wing's `_core` box and replace it with the interior.
- Keep the facade panes breakable; add the sliding entrance banks with the
  shared automatic-door code (`split_auto_doors` in
  `tools/build_povo_campus.py` and `add_auto_doors` in `tools/cs2_campus.py`).
- Furnish with the existing furniture kits where they fit (tables and chairs
  from the Povo 2 table hall, the reception desk kit from the receptions).

## Implemented source and confirmed placement

User clarification: short south wing = canteen, long north wing = library.
Both entrances face Povo 1. Povo 1/canteen/library ground floors are level;
their first floors meet the street pavement (prototype elevations 4.0/7.6 m).
The canteen has its projecting L-route porch, bar/dining/serving furniture,
internal stairs and a sliding first-floor pavement exit. The library has
ground reception, three estimated reading rooms per floor, tables and stairs.
Room counts, furniture and stair positions are inferred blockout choices.
See `config/povo_wings.json` and the latest worklog for limitations, including
the game adaptation retaining the established bridge and Povo 2 floor levels.
