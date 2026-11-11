# Paired moving lifts — 10 November 2026 revision

This revision implements the user-reviewed placement and supersedes the old ladder and the overlapping Povo 2 basement door/stub. Dimensions are model estimates, not a measured survey.

| Building | Repository floor labels | Bank bounds (east, north metres) | Frontage |
| --- | --- | --- | --- |
| Povo 1 | −1, 0, +1 | E 8–12.6; N −85.2–−79.2 | 6 m |
| Povo 2 | −1, 0 | E 25.7–35.2; N 26.8–34.8 | 8 m |

Povo 1 replaces the reception-side ladder with two stacked shafts in the reviewed corner opposite the entrance stairs. The 6 m bank uses approximately two-thirds of the corner frontage in the plan; confirm this dimension on site before treating it as surveyed. The former ladder opening and terrace closers are removed.

Povo 2's combined bank matches the stair core's 8 × 9.5 m footprint. The ground entrances face the stairs; the basement entrances face the expanded C5 side corridor. D1 remains locked and moves north to N 36 (about 6.12 m beyond its former position). The unverified doorway previously labelled D2 and its overlapping stub are removed; the remaining restricted corridor is capped at N 35.1. The obsolete concrete apron is cut out of the lobby and shaft. No additional Povo 2 stops are inferred.

## Geometry, appearance and operation

`config/povo_elevators.json` owns the registered positions and stops. `tools/povo_elevators.py` carves the shafts after campus registration, builds the portals, parked preview cabins and door geometry, and records entity metadata. Dynamic pieces are excluded from the static render/collision export and spawn placement.

The appearance follows photograph `image00012.jpeg`: brushed stainless doors and recessed frames, pale walls and a shared call panel with red floor indicators. Generated materials use `csgo_complex.vfx`, explicit metalness, roughness textures and metal physical surfaces. These are original CS2 materials, not guessed stock material paths.

`tools/povo_elevator_entities.py` emits four independent `func_tracktrain` cars, parented cabin doors/buttons, paired landing doors and connected floor paths. Use a landing button to call its car; use the labelled buttons inside to choose a floor. Busy cars ignore further calls until arrival; there is no call queue. All landing and cabin leaves must report closed before departure. A blocked closing door reopens its pair, and closing retries until clear. Actual destination arrival opens only that landing and the cabin doors. No travel-time timer or teleport substitutes for arrival.

## Validation and remaining native check

`python -m unittest tests.test_povo_elevators -v` checks registered geometry, full-height cabin clearance, landing gates, restricted boundaries, entity identities, interlock routing and reproducible CS2 materials. The normal campus export includes the lift metadata and assets.

This Linux environment has no CS2 Workshop Tools. Regenerating the binary VMAP itself requires `dmxconvert.exe` and has not run here; the existing binary map remains unchanged. The normal Windows prepare/build must regenerate the lift controls before opening or riding the new shaft layout. Source export and tests do not prove native compilation or player transport. Before release, compile through the normal Windows campus build and ride both cars through every stop in both directions; check repeated calls, doorway obstruction/retry, passenger collision, parented controls, red indicators and material appearance. Check both D1 and the remaining restricted corridor remain sealed. Confirm the Povo 1 frontage in person if possible.
