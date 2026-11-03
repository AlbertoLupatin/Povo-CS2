# Feedback for the Povo map

One place at a time: a building floor, or an outside area. Put everything for it together, then tell me it's ready.

## The maps (`<BUILDING>/MAPS/`)

Generated from the map as it is now, over the official plans:

- **Rooms:** numbered in reading order (north to south, west to east). Write them as `P1 -1 #07`, `P2 0 #12`, the Povo 2 strip as `P2 -1 #S03`, the mensa as `ME 0 #02`, the library as `LI -1 #05`.
- **Lines:** red for room and stair doors, green for entrances in the facade, blue for glazed sides.
- **Spots:** the 5 m grid gives `C7` (letter = column west to east, number = row south to north).
- **Outside:** use `EXTERNAL/MAPS/SITE_map.png` (25 m grid, "site F9") or `CAMPUS_map.png` (10 m grid, "campus D12").
- **Room list:** `rooms.md` in each MAPS folder lists every ID with its name and size.

The numbers can change after a round of edits. I regenerate the maps each time, so always use the latest ones.

## What to put in a place's folder

e.g. `POVO 1/floor -1/`:

| File | What |
|---|---|
| `notes.md` | Numbered items, one per change (see below) |
| `plan.png` | A copy of the floor map with your markings: arrows for doors, crosses for walls to remove, lines for new walls, renamed rooms, item numbers |
| `07.jpg`, `07_2.jpg`… | Photos of a room, named by its ID. In the notes, say what to take from it (floor, walls, ceiling, furniture, windows) |
| `C7_corridor.jpg`… | Photos of a spot, named by grid cell |

Example `notes.md`:

```
1. #07 (A108) is a lab, not a classroom: grey floor, benches along the walls (07.jpg).
2. Wall between #09 and #11: remove, it is one office.
3. Door of #14 is at the north end, not the middle.
4. C3-D3: the corridor has a glass wall to the courtyard (C3_corridor.jpg).
5. mark 4: the stair clips the ceiling.
```

Rough measurements help ("door ~1.6 m", "12 steps").

## Problems in game: the F6 marker

1. Start the map with `remake\play.cmd` (lit map), or `play.cmd unlit` (the quick map).
2. Walk or noclip to the problem and press **F6**. It saves your exact position, view and a screenshot as the next mark.
3. Write `mark N: what's wrong` in the notes. The marks are numbered in order; I can show you the list.

Marks are collected into `PROBLEMS_TO_SOLVE/marks/` (`mark_001.png`… plus `marks.json` with the positions) the next time the map starts, or when I collect them. I can fly the camera back to each mark, fix it, and shoot the same view after.

Once a problem is fixed and checked in game, its screenshot moves to `PROBLEMS_TO_SOLVE/solved/`.

Screenshots you take yourself (like the ones already in `PROBLEMS_TO_SOLVE`) are fine too: a descriptive file name is enough, plus a note if it's not obvious where it is.
