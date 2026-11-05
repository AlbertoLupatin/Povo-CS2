# Approved Povo 1 / bridge-facing facade correction

The user approved implementation on 5 November after reviewing and correcting
the concept images. The accepted south-end preview, not the rejected earlier
bridge images or initial Roan-pattern schematic, is the visual baseline.

- Povo 1 north and south: six broad glazed bays on both upper levels, with
  substantial stone piers, continuous floor bands, aluminium window divisions
  and horizontal metal window guards.
- Povo 2's facing south elevation uses that same six-bay pattern.
- Povo 1 east/west share the approved broad central bays and narrow fin/window
  divisions at the ends. Lower glazing is independent of room furniture.
- The guards and shallow sill recesses are not deep projecting balconies or
  new outdoor corridors. Photographs establish the appearance; the metric
  finishing dimensions are fitted estimates.
- The existing bridge stays at E16.5–20 / N−20–10 / deck Z11.2 in local metres.
  Povo 1's east edge is E24. Looking south from Povo 2, east is screen-left,
  so this is the outer-left bay in the user's north-end Earth screenshot.
  No mirrored relocation across the building is required.

`config/povo_facades.json` records the schedule. `tools/povo_facades.py` applies
it after the existing room, stair, entrance, pavement and furniture integrations,
and exports its schedule/source hashes in campus provenance. The pass removes
the obsolete perimeter walls, glazing and trim, then supplies the complete
facade independently of the classroom kits. Interior cross-partitions terminate
at the glazing. Stone fins project outward while glass stays at the existing
wall line to preserve the classroom aisles. Slabs and ceilings stay in place.

The working Povo 1 automatic bank and Povo 2's approved ground-floor left
extension passage remain explicit openings. Both bridge portals stay clear.
The unmodelled Povo 2 backdrop receives genuine shallow window recesses and
sealed panes using the same glass material as playable windows; its unseen
interior is not invented as new playable rooms. Basement and campus-model geometry below
local Z4 are unchanged. The bridge's old coarse louver strips are replaced by
a finer aluminium screen while its deck, enclosure and walking route stay put.

Evidence uses the user's original IMG_2365/IMG_2367, P024/P057 and the existing
P013 reference, with the final user-approved pattern. Earth screenshots and
generated images are visual review context, not game textures or traced meshes.
RoanS77's material choices remain in `config/povo_textures.json`.

## Verification record

The first regression run caught glass inset narrowing three classroom aisles
and a new panel sealing the Povo 2 left extension. Both were corrected. The
27 focused regression tests then passed. Legacy assertions identifying removed
individual room/stair glass pieces were updated to check the replacement
facade glazing and the existing general breakable-glass export path.

Final build and verification are recorded below. Historic build records are not
evidence for this revision.


## North courtyard obstruction (user revision)

The user requested removal of the elevated grey pavement seen at the north
end. Inspection found no corresponding elevated slab in either campus OBJ.
The only developer-grey material in the prepared VMAP belonged to the inherited
sample arena enclosure. `campus_sky_shell` replaces its opaque lower faces with
sky and writes the distant enclosure bounds explicitly into its vertices,
with an identity transform. This removes the sample floor/walls from the
courtyard while retaining a closed outer sky shell. Real ground paving, bridge
deck and the approved Povo 2 basement remain unchanged.

The prior complete source suite passed 436 tests. After the upper window-return
junction and aluminium diffuse-material correction, the focused final map,
facade and texture suite passed 29 tests. The new enclosure regression checks
that no developer-grey face survives and that enclosure vertices lie outside
the campus rather than crossing the courtyard. Native verification follows.


## Final native result and handoff

The standard native build completed successfully (normal lighting, 1024 atlas).
Final VPK: 72,920,216 bytes, 1,529 entries; every entry CRC verified.
SHA-256: `35e06fd4d63f97dde06595e6098c4cdba7f8f461fbccebf4a78be6629769a104`.
The package was loaded in the isolated `trento_povo_facade_review` addon.
Six unedited normal-lit engine screenshots confirm the new facades, silver
frames, correct bridge corner and complete removal of the raised grey courtyard
obstruction. The user accepted the result and asked to exit and push to GitHub.
Five ordinary-walking waypoints passed from Povo 1 into the bridge, through
local N0. Further walking and bullet-break checks were stopped at that request;
the reverse crossing, entrance traversal and bullet behaviour were not claimed
as verified. CS2 was closed normally.

The unchanged compiled campus model passed 1,086 facade/portal collision samples,
22,997 basement-floor samples, 72 column and 36 locked-door checks; 250 compiled
sidewalk samples also passed. These model checks exclude VMAP world brushes;
the north enclosure correction was separately checked in source and in game.
The rebuilt package is installed in the usual `trento_povo_campus_test` addon.
The previous standard package backup is in
`build/facade-fix-20261105/previous-standard.vpk`. Build logs are in that same
folder. Native screenshots and machine-readable reports are in the chat's
`outputs/povo1-facade-implementation` folder. No Workshop publication was made.
