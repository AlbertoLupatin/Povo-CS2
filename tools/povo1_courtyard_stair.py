"""Photo 5-8/23-25 courtyard steel stair spanning P1 -1, 0 and 1.

Topology and exposed metal structure are observed; footprint/riser dimensions
are a provisional fit to the registered courtyard, not photogrammetry.
"""
try:
    from .povo_room_fitout import subtract_box
    from .povo_stairs import railing
except ImportError:
    from povo_room_fitout import subtract_box
    from povo_stairs import railing


def extend(boxes, levels, origin):
    result=list(boxes);rails=[]
    def add(name,lo,hi,mat='metal_dark'):
        result.append(('p1_courtyard_stair_'+name,tuple(lo),tuple(hi),mat))
    zs=[l['floor_elevation_metres']-origin[2] for l in levels]
    for i,(level,z) in enumerate(zip(levels,zs)):
        edge=level['voids_local_metres'][0][1]
        # Clear the whole standing landing approach, including source room
        # partition returns at the provisional upper courtyard registration.
        hole=((-1.9,edge-(.95 if i==len(levels)-1 else .3),z-.01),(1.9,edge+.4,z+2.3))
        result=[part for b in result for part in (subtract_box(b,hole) if b[3] in ('wall','courtyard_wall','window_glass','window_frame') else [b])]
        add('floor_'+str(i)+'_landing',(-1.8,min(edge-.8,-76.8),z-.15),(1.8,max(-75.8,edge+.12),z),'floor_circulation')
    segments=[]
    for floor,(lo,hi) in enumerate(zip(zs,zs[1:])):
        # Three flights around a central well, visible in photos 5-8/25.
        # Twenty-four risers and all dimensions remain a gameplay fit.
        side_count=9;cross_count=6;tread=.28;count=2*side_count+cross_count
        rise=(hi-lo)/count;start=-75.8;band=start+side_count*tread
        width=(3.6-cross_count*tread)/2;left=-1.8+width;right=1.8-width
        z1=lo+side_count*rise;z2=lo+(side_count+cross_count)*rise
        add(f'{floor}_corner_west',(-1.8,band,z1-.12),(left,band+width,z1))
        add(f'{floor}_corner_east',(right,band,z2-.12),(1.8,band+width,z2))
        for i in range(side_count):
            top=lo+(i+1)*rise
            add(f'{floor}_up_{i}',(-1.8,start+i*tread,top-.12),(left,start+(i+1)*tread,top))
            top=lo+(side_count+cross_count+i+1)*rise
            add(f'{floor}_return_{i}',(right,band-(i+1)*tread,top-.12),(1.8,band-i*tread,top))
        for i in range(cross_count):
            add(f'{floor}_cross_{i}',(left+i*tread,band,z1+(i+1)*rise-.12),
                (left+(i+1)*tread,band+width,z1+(i+1)*rise))
        railing(add,rails,str(floor)+'_west',(-1.8,start,lo),(-1.8,band,z1))
        railing(add,rails,str(floor)+'_east',(1.8,band,z2),(1.8,start,hi))
        railing(add,rails,str(floor)+'_well_west',(left,start,lo),(left,band,z1))
        railing(add,rails,str(floor)+'_well_cross',(left,band,z1),(right,band,z2))
        railing(add,rails,str(floor)+'_well_east',(right,band,z2),(right,start,hi))
        railing(add,rails,str(floor)+'_far',(-1.8,band+width,z1),(1.8,band+width,z2))
        path=[[(-1.8+left)/2,start-.4,lo],
              *[[(-1.8+left)/2,start+(i+.5)*tread,lo+(i+1)*rise] for i in range(side_count)],
              [(-1.8+left)/2,band+width/2,z1],
              *[[left+(i+.5)*tread,band+width/2,z1+(i+1)*rise] for i in range(cross_count)],
              [(right+1.8)/2,band+width/2,z2],
              *[[(right+1.8)/2,band-(i+.5)*tread,z2+(i+1)*rise] for i in range(side_count)],
              [(right+1.8)/2,start-.4,hi]]
        segments.append(dict(path=path,from_floor=floor-1,to_floor=floor,flights=3,risers=count,rise_metres=rise,
                             flight_width_metres=width,
                             bottom=[(-1.8+left)/2,start-.4,lo],top=[(right+1.8)/2,start-.4,hi],
                             mid=[0,band+width/2,(z1+z2)/2]))
    for x in (-1.85,1.85):
        for y in (-75.8,-72.32):add('column_'+str(x)+'_'+str(y),(x-.07,y-.07,zs[0]),(x+.07,y+.07,zs[-1]+1.05))
    metadata=dict(source_photos=[5,6,7,8,23,24,25,30],floors=[-1,0,1],segments=segments,
                  rails=rails,bounds=[-1.9,-78.2,1.9,-72.2],
                  status='Observed steel stair with three flights per storey; metric fit and exact landing registration provisional')
    levels[0]['courtyard_stair']=metadata
    return result,metadata
