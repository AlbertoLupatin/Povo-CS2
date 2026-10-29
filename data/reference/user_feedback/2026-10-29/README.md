# Povo 2 level -1 corrections

`povo2_minus1_corrections.png` is the user's markup of the generated basement
review, supplied on 29 October 2026. The user explicitly requested rebuilding it.

- Extend the lower stair corridor east to meet the exit corridor.
- Lengthen the clear section between Room 1 and Room 2. The user counted roughly
  35–40 long steps and stated a height of 1.75 m. The implementation uses a
  provisional 30 m gap, based on an explicitly stated assumption of 0.8 m per
  step (28–32 m). This is not a measured dimension.
- Remove the left/west half only of that inter-lab section, leaving a nominal
  1.5 m plan width on the right/east. The user confirmed this scope; retain the lab rooms
  and their entrance approaches.
- Put a door across the upper return at the marked lab-corridor junction.
- Put another door across the northward left turn at the new lower-right
  junction, toward the EXIT CORRIDOR label.
- Both new doors must always remain closed and be impossible to open. They
  isolate the upper L-shaped corridor. Build them as static solid geometry,
  without door entities, sensors, interaction handlers or breakability.

The questioned black piece at the south exit is a projection of the existing
outdoor UP stair and its railing collision. Preserve those stairs and label
them clearly in the regenerated review. Street, garden, stair-core and level -2
positions are retained.

## Pavement flicker

`pavement_flicker.png` is the user's in-game screenshot supplied later on
29 October. The user reports that many pavements flicker and identifies the
brighter central region as an example. See
[the source correction and verification](../../../../docs/POVO_PAVEMENT_FLICKER.md).
