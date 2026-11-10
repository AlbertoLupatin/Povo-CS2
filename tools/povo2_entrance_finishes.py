"""Close the unused side bay beside the Povo 2 floor-0 stair entrance."""
from .povo_room_fitout import subtract_box

def extend(boxes,levels):
    # The live stair portal is at E20.5 / N22. The unused opening immediately
    # south of the core is closed on that same plane, leaving the approach,
    # classroom corridor and actual stair opening in their existing locations.
    result=list(boxes)
    spec=levels[1]['connection']['povo2']
    registered=spec['additions']['config'].get('ground_registration')
    south=18. if registered else 11.1
    if not registered:
        result.append(('p2_ground_entrance_side_bay_closure',
                       (20.4,11.1,4.),(20.6,18.,7.35),'wall'))
    # The obsolete wall tops also hid missing ceiling finish over the widened
    # approach. Complete its flat tiled ceiling, preserving the stairwell cut.
    panels=[('p2_ground_entrance_ceiling_infill',(20.6,south,7.28),(25.5,29.5,7.35),'ceiling_panel')]
    for _,lo,hi,material in boxes:
        if material=='ceiling_panel':panels=[p for panel in panels for p in subtract_box(panel,(lo,hi))]
    result.extend(panels)
    levels[1]['connection']['povo2']['entrance_finishes']=dict(
        closed_side_bay=None if registered else [20.4,11.1,20.6,18.],floor_z=4.,ceiling_z=7.35,
        source='User entrance screenshots, 2 November 2026',
        preserve='Existing stair portal E20.5/N22 and all -1 layout geometry')
    return result
