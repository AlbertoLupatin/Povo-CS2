# Povo 2 internal stairs — user clarification, 28 October 2026

**Implementation update:** source geometry has now been corrected; see [implementation, dimensional limits and validation](../../../../docs/POVO2_INTERNAL_STAIRS_IMPLEMENTATION.md). The status/comparison paragraphs below preserve the earlier reference audit, not the current generated geometry.

Source: the user's first-hand stair walkthrough in chat and [subsequently attached door-position sketch](povo2_internal_stair_doors.jpg). The original JPEG is preserved unchanged; source/copy SHA-256 equality was checked. This concerns the internal reception-side stair, separately from the outdoor garden stairs.

## Confirmed reference

### Latest clarification supersedes the earlier wall interpretation

The user subsequently confirms that the existing -1 exit/layout is to be kept; apart from stair flight/step counts, the layout correction is at -2. See the [second basement/vestibule sketch](povo2_basement_stair_vestibule.jpg), preserved unchanged with SHA-256 equality checked. The earlier interpretation below that both basement exits must move to a wall opposite 0/+1 must not drive geometry changes.

The second sketch shows -2 exiting into a small vestibule. Relative to leaving the stair, the right-hand branch leads through doors toward parking; the left-hand branch leads through doors toward the cross corridor, with other offices on the left and Garden -2 toward the right end. Preserve these distinct thresholds and the intermediate vestibule rather than opening the stair directly into parking. The -1 drawing is contextual evidence for the retained corridor/exit arrangement, not a request to rebuild it.

The sketch establishes connectivity, not scale. Use photographed planimetry for proportions and registration. `exports/povo2_survey/plan_minus2.jpg` shows parking, internal cores and office/corridor bands; it has no readable metric dimensions at the available review resolution. `config/povo2_survey.json` explicitly has `metric_scale=null` and uses 0..100 photo coordinates, not metres. Do not present the sketch's proportions or the survey coordinates as measured dimensions.

Source audit of the assembled campus (no game launch): `povo2_connection.py` creates two stacked 20-step modules from ground z=4 to bridge z=11.2, i.e. four flights of 10; `povo2_integration.py` copies one 20-step/two-flight module to each basement storey. `povo2_sketch.py` then relocates -1's door to [19.2,18,0.4], while -2 remains [20.5,22,-3.2]. Thus the standalone draft comparison below is not the final assembled door arrangement. Keep the accepted -1 door and correct -2 to the user's vestibule relationship.

The +1 vertical span also needs reconciliation when implementing the confirmed 26 steps: the current estimated 7.2 m span would give approximately 0.277 m per step if kept unchanged. Do not merely replace loop counts and claim the resulting dimensions are plan-verified. This is an implementation constraint, not a change to the user's confirmed step count.

All directions use floor 0 as reference, looking toward reception: PC room left, aula magna right. Preserve this reference when comparing drawings; do not reinterpret left/right from each flight's changing heading.

| Journey | Flights | Steps per flight | Exit relationship described by user |
| --- | --- | --- | --- |
| 0 to +1 | 2 | 13 each (26 total) | Door ahead, on the same wall as the floor-0 door. |
| 0 to -1 | 3 | 10 each (30 total) | Door on the left compared with entry. |
| -1 to -2 | 3 more | 10 each (30 total) | Door on the right; same wall as the -1 exit, shifted toward the entrance. |

The sketch shows four separate schematic floor footprints labelled +1, 0, -1 and -2. Read with the labels upright, +1 and 0 have their door marks along the top wall, toward the left; -1 has its door toward the left of the bottom wall; -2 has its door toward the right of that same bottom wall. Thus the basement exit wall is opposite the wall used at 0/+1. The -2 shift toward the entrance comes from the accompanying written account. These are page-relative descriptions, not compass directions or measured offsets.

The sketch contains no flights or intermediate landings. Their turn sequence and exact sizes remain unverified; do not claim the sketch establishes them. Step counts do not establish measured storey heights.

## Comparison with current source

`config/povo2_planimetry.json` currently sets `risers_per_storey=20`. `tools/povo2_planimetry.py` builds two flights of ten steps for each of the three storey connections. All portals use the west shell at `x=25`, `door_y=39.5`, with a common north landing.

Thus none of the three connections has the confirmed step count. The uniform portal arrangement does not encode the basement door relationships. Existing traversal/headroom checks verify the placeholder's usability, not fidelity to this walkthrough.

## Correction status

Reference and discrepancy recorded; generated geometry and playable build have not been changed. Reconstruct flights and landings together with level-specific portals using the confirmed opposite-wall relationship and the differing basement door offsets. Flight turns and landing dimensions still require reconstruction against the plans and available footprint; they are not drawn in this sketch. Update route metadata and assertions that currently require 20 steps and 75 audit samples, then verify support, headroom, doorway clearance and traversal in both directions. Keep existing estimated floor elevations provisional unless measured evidence supersedes them.
