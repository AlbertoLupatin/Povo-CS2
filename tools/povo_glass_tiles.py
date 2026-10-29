"""One breakable per visible glazing tile, following existing fixed frames."""
import re


def split_tiles(glass,boxes):
    frames=[b for b in boxes if b[3] in ('window_frame','metal_dark')
            and re.search(r'mullion|transom|_frame(?:_|$)|_post_',b[0])
            and '_louver_' not in b[0]]
    result=[]
    for name,lo,hi,material in glass:
        normal=min(range(3),key=lambda i:hi[i]-lo[i])
        axes=[i for i in range(3) if i!=normal]
        cuts={axis:[lo[axis],hi[axis]] for axis in axes}
        for _,a,b,_ in frames:
            if a[normal]>hi[normal]+.001 or b[normal]<lo[normal]-.001:continue
            for axis in axes:
                other=next(i for i in axes if i!=axis)
                # Only a continuous bar across this pane defines a tile edge.
                if b[axis]-a[axis]>.25 or a[other]>lo[other]+.12 or b[other]<hi[other]-.12:continue
                centre=(a[axis]+b[axis])/2
                if lo[axis]+.015<centre<hi[axis]-.015:cuts[axis].append(centre)
        for axis in axes:
            merged=[]
            for x in sorted(cuts[axis]):
                if not merged or x-merged[-1]>.015:merged.append(x)
            cuts[axis]=merged
        nx,ny=(len(cuts[i])-1 for i in axes)
        for x in range(nx):
            for y in range(ny):
                a,b=list(lo),list(hi)
                for axis,index in zip(axes,(x,y)):a[axis],b[axis]=cuts[axis][index:index+2]
                token=name if nx*ny==1 else f'{name}_tile_{x:02d}_{y:02d}'
                result.append(dict(name=token,source_facet=name,lo=a,hi=b,material=material,
                                   tile=[x,y],tile_grid=[nx,ny]))
    return result
