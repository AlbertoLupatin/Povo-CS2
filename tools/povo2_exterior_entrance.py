"""Photo-guided outer doors, entrance lobby and inner reception doors.

Edits only the supplied exterior-study boxes. Sliding doors are parked open;
the paired openings must remain physically clear, including old facade frames.
"""
try:
    from .povo_room_fitout import subtract_box
except ImportError:
    from povo_room_fitout import subtract_box


def door_bank(box,prefix,x,y,z,bank_width,clear_width,door_height):
    """One sliding bank in the plane x, outside towards +x, leaves parked open.

    The leaf parts (`_parked_leaf_`, `_parked_leaf_band_`, `_leaf_bottom_`)
    become automatic doors in the CS2 map; see split_auto_doors().
    """
    half=bank_width/2;clear=clear_width/2;head=z+door_height
    # A pair of sliding leaves rests over the fixed sidelights.
    for sign in (-1,1):
        lo,hi=(y-half,y-clear) if sign<0 else (y+clear,y+half)
        for depth,label in ((-.07,'fixed'),(.035,'parked_leaf')):
            box(f'{prefix}_{label}_{sign}',(x+depth,lo,z+.08),(x+depth+.025,hi,head-.06),'entry_glass')
            box(f'{prefix}_{label}_band_{sign}',(x+depth-.004,lo,z+1.12),(x+depth+.03,hi,z+1.17),'white')
        # Stops short of the sliding-leaf track (x+.03 to x+.07).
        for yy in (lo,hi):
            box(f'{prefix}_sash_{sign}_{yy}',(x-.08,yy-.023,z),(x+.025,yy+.023,head),'fence')
        box(f'{prefix}_leaf_bottom_{sign}',(x+.03,lo,z+.035),(x+.07,hi,z+.085),'fence')
    box(prefix+'_head',(x-.10,y-half-.05,head),(x+.12,y+half+.05,head+.13),'fence')
    box(prefix+'_sensor',(x+.12,y-.13,head+.14),(x+.17,y+.13,head+.23),'dark')
    box(prefix+'_mat',(x-.7,y-half,z+.005),(x+.7,y+half,z+.015),'dark')
    return dict(centre=[x,y,z],clear_width=clear_width,height=door_height)


def extend(boxes,spec,live_entrance):
    result=[];a,b,c,d=spec['lobby_bounds'];z=spec['floor_z'];height=spec['ceiling_height']
    hole=((a-.15,b,z-.015),(c,d,z+height))
    # Hollow the former solid glass block. Cut all its facade grids as well,
    # otherwise horizontal transoms would still cross the walking routes.
    for item in boxes:
        name=item[0]
        if name.startswith(('povo2_entrance_doors','povo2_entrance_glazing','povo2_entrance_handle','povo2_entrance_canopy')):continue
        if name.startswith('povo2_front_annex_0_'):
            result.extend(subtract_box(item,hole))
        else:result.append(item)
    def box(name,lo,hi,mat):
        if any(x>=y for x,y in zip(lo,hi)):raise ValueError(name)
        result.append(('p2_entry_'+name,tuple(lo),tuple(hi),mat))
    def slab(name,r,top,mat,thickness=.10):box(name,(r[0],r[1],top-thickness),(r[2],r[3],top),mat)
    slab('floor',(a,b,c,d),z,'tile',.20)
    slab('ceiling',(a,b,c,d),z+height,'white',.08)
    # Finish faces sit inside the cut shell, avoiding coplanar glass/plaster.
    box('wall_south',(a,b-.075,z),(c,b+.025,z+height),'white')
    box('wall_north',(a,d-.025,z),(c,d+.075,z+height),'white')
    # Floor/ceiling grids and recessed lamps follow the photographed lobby.
    for i in range(int((c-a)/.6)+1):
        x=a+i*.6;box(f'floor_joint_x_{i}',(x,b,z+.002),(x+.012,d,z+.006),'grout')
    for i in range(int((d-b)/.6)+1):
        y=b+i*.6;box(f'floor_joint_y_{i}',(a,y,z+.002),(c,y+.012,z+.006),'grout')
    for i in range(int((c-a)/1.2)+1):
        x=a+i*1.2;box(f'ceiling_joint_x_{i}',(x,b,z+height-.09),(x+.015,d,z+height-.08),'fence')
    for y in (b+1.5,d-1.5):
        for i,x in enumerate(range(28,49,4)):
            slab(f'light_{y}_{i}',(x-.3,y-.3,x+.3,y+.3),z+height-.09,'light',.015)
    centre=spec['centre_y'];banks=[]
    for side,x in (('outer',spec['outer_x']),('inner',spec['inner_x'])):
        for index,offset in enumerate(spec['bank_offsets_y']):
            bank=door_bank(box,f'{side}_bank_{index}',x,centre+offset,z,
                           spec['bank_width'],spec['clear_width'],spec['door_height'])
            banks.append(dict(bank,line=side,index=index))
        # Seal the rest of each door plane around the two real openings.
        low=centre+min(spec['bank_offsets_y'])-spec['bank_width']/2
        high=centre+max(spec['bank_offsets_y'])+spec['bank_width']/2
        for label,y0,y1 in (('south',b,low),('north',high,d)):
            box(side+'_side_'+label,(x-.1,y0,z),(x+.1,y1,z+height),'white')
        half=(spec['inner_column_width']/2 if side=='inner' else .12)
        box(side+'_central_column',(x-.18,centre-half,z),(x+.18,centre+half,z+height),'white' if side=='inner' else 'fence')
        box(side+'_header',(x-.12,low,z+spec['door_height']+.13),(x+.14,high,z+height),'white')
    # Recessed outer reveal replaces the previous projecting canopy placeholder.
    x=spec['outer_x'];facade=51.2
    for label,y0,y1 in (('south',centre-4.5,centre-4.3),('north',centre+4.3,centre+4.5)):
        box('outer_reveal_'+label,(x,y0,z),(facade,y1,z+height),'concrete')
    box('outer_reveal_header',(x,centre-4.5,z+height),(facade,centre+4.5,z+height+.15),'fence')
    # Neutral fixture proxies: no copied posters, faces, logos or screen text.
    for i,x in enumerate((38,39.3,40.6,41.9)):
        box(f'vending_{i}',(x,d-.95,z),(x+1.0,d-.08,z+2.0),'dark')
        box(f'vending_screen_{i}',(x+.15,d-.97,z+.8),(x+.85,d-.94,z+1.8),'glass')
    box('locker',(35.5,d-.6,z),(37.3,d-.06,z+1.9),'orange')
    for x in (40,45):box(f'notice_screen_{x}',(x-.6,b+.015,z+1.2),(x+.6,b+.07,z+2),'glass')
    box('inner_column_noticeboard',(spec['inner_x']+.19,centre-.25,z+.8),(spec['inner_x']+.24,centre+.25,z+2.1),'concrete')
    for i,mat in enumerate(('car_blue','grass','marking','concrete')):
        yy=centre+3.0+i*.43
        box(f'outside_bin_{i}',(50.0,yy,z),(50.65,yy+.39,z+.9),'white')
        slab(f'outside_bin_lid_{i}',(50.0,yy,50.65,yy+.39),z+.96,mat,.10)
    return result,dict(door_banks=banks,outer_x=spec['outer_x'],inner_x=spec['inner_x'],
                       lobby_bounds=spec['lobby_bounds'],floor_z=z,
                       source_entrance_xy=live_entrance,source_floor_z=4.0,
                       integration_note='Inner doorway XY and floor match current interior source. Static leaves parked open; glass 20% transparent.')
