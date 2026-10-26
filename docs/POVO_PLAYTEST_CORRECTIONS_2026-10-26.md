# Playtest corrections — 26 October 2026

Status: layout approved with the three amendments below. Source geometry and
materials implemented; standard map compiled (681 resources, 0 failed) and
packaged. In-game verification is being done by the user by hand.

## Proposed floor 0 arrangement

Entrance-relative schematic: enter from the left, reception ahead. Turn left
and pass the stair/lift area before reaching a transverse corridor at 90 degrees
to that approach. The PC branch is to the left; B108/B109 are to the right.
Room numbers and dimensions remain provisional. Preserve the bridge and current
floor elevations. Replace the redundant stair door and empty vestibule with a
direct route through the remaining stair door.

Approval amendments: the ladder has a dedicated entry in the narrow space
between the stair block and the transverse corridor. B106 grows to adjoin B108.
The aula moves to the opposite (west) side of the intermediate lobby, with its
interior turned 180 degrees from the reviewed drawing to face the new entrance.

The right hall retains tables opposite B111–B114. Remove the table-area handrail.
End the classroom/corridor wall at the last room, without a tail beyond it.
Use framed glass after the last tables, enclosing the intermediate lobby.
Use a solid wall between that lobby and the aula magna, with its entrance.
Seats face east toward the entrance side of the relocated aula. Room sizing
remains an estimated gameplay adaptation.

The basement left exit should reach the ascending stair immediately after the
exit door, with no detour across the sunken yard. Keep the yard alongside it.

Review visual:
`C:/Users/Alberto/.codex/visualizations/2026/10/26/01a179cd-c7d1-7a92-969e-3cc501461662/povo2-layout-approval.html`

## Source changes

- Repair ladder dismounts at the served upper floors in both buildings.
- Match library/canteen exterior glazing to Povo 1's metal frame pattern.
- Restore Povo exterior glass visibility from indoors as well as outdoors.
- Increase glass opacity slightly so broken panels are more apparent.
- Keep black doors permanently open; preserve intentionally inaccessible rooms.
- Repair Povo 2 stair geometry, landings, openings, and headroom; remove the
  redundant first black stair door and the empty space it leads to.
- Apply the approved transverse floor 0 classroom corridor.
- Remove the floor 0 table-area handrail shown in screenshot 3.
- End walls with the rooms; inspect the B112 facade/corridor overrun shown in
  screenshot 4, including any opaque scenery behind its glazing.
- Replace the wall after the tables with framed glass and place the solid
  partition between the intermediate area and the aula magna.
- Relocate the aula to the lobby's opposite side and turn its interior toward
  the new entrance (180 degrees from the initial reviewed proposal).
- Put the basement left exit stair directly after the exit doorway.
- Close the missing street paving between Povo 1's frontage end at N=-13 and
  the bridge road, and align the cross-road connector to the 7.6 m street.
  Its old 5.8 m height produced a 1.8 m drop. Continue the paving along the
  adjoining footway's grade, retaining the separate open basement yard.

User evidence: five screenshots attached in the 26 October playtest request.
Screenshot 1 shows the broken Povo 2 stair; screenshot 2 the wrong corridor;
screenshot 3 the unwanted table-area rail; screenshot 4 the B112 wall/glazing;
screenshot 5 the basement exit stair offset from its doorway.

## Verification needed after implementation

Regenerate and audit geometry; run relevant source tests, then build/package
checks. In CS2, walk both ladder dismounts, every Povo 2 stair transition and the
basement exit without noclip; verify glass from both sides and its break state,
fixed-open doors, room-wall endings and the approved floor 0 arrangement.

Existing unrelated local multiplayer launcher/hosting edits are outside scope.

## Build isolation

An older winter compile was already running when these corrections began.
Its installed source and game files are preserved. The corrected standard map
is built under the separate `trento_povo_playtest_corrections` addon, with output
at `build/package/pc/trento_povo_campus.vpk` (60,893,188 bytes, full CRC check
passed). The longer `playtest_corrections` output folder pushed one staged glass
entity path past Windows' 260-character limit. The unchanged shared blockout
materials are copied from the main `trento_povo` addon's compiled output. The
package replaced `build/package/trento_povo_campus.vpk` for `play_campus.cmd`;
the previous one is in `build/playtest-corrections-backup-20261026-2157/`.
The temporary build driver is `build/compile_playtest_corrections.py`.
