"""Concrete closures from the reviewed 2 November exterior drawing."""
from .povo_street_footways import prism

BASE=-3.42
REGIONS=dict(A=[31.96,2.75,35.75,8.75],B=[35.75,2.,42.02,2.75],
             C=[45.58,2.,55.5,2.75],D=[56.7,-1.,58.,15.])


def intersect_rect(polygon,r):
    polygon=list(polygon)
    for axis,value,sign in ((0,r[0],1),(0,r[2],-1),(1,r[1],1),(1,r[3],-1)):
        result=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            da=(a[axis]-value)*sign;db=(b[axis]-value)*sign
            if da>=0:result.append(a)
            if (da>=0)!=(db>=0):
                t=da/(da-db);result.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
        polygon=result
        if len(polygon)<3:return []
    return polygon


def extend(boxes,levels):
    result=list(boxes);ext=levels[0]['exterior']
    def box(name,lo,hi):result.append(('exterior_user_fill_'+name,tuple(lo),tuple(hi),'exterior_concrete'))
    a,b,c,d=REGIONS['A'];t=.08
    for name,lo,hi in (
        ('a_west',(a-t,b,BASE),(a,d,4.)),('a_east',(c,b,BASE),(c+t,d,4.)),
        ('a_south',(a-t,b-t,BASE),(c+t,b,4.)),('a_north',(a-t,d,BASE),(c+t,d+t,4.))):
        box(name,lo,hi)
    for name in ('B','C'):
        a,b,c,d=REGIONS[name];box(name.lower(),(a,b,BASE),(c,d,4.))
    # D follows the actual surviving paving, including its sloped triangles.
    # Add support below those surfaces, rather than a new slab across the garden.
    tops=[];r=REGIONS['D']
    for name,lo,hi,material in boxes:
        if material!='exterior_paving':continue
        tops.append([(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),
                     (hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])])
    for mesh in ext['meshes']:
        if mesh['material']!='exterior_paving':continue
        for f in mesh['faces']:
            p=[mesh['vertices'][i] for i in f];a,b,c=p[:3]
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>1e-8:tops.append(p)
    supports=[]
    for top in tops:
        if max(p[0] for p in top)<=r[0] or min(p[0] for p in top)>=r[2] or max(p[1] for p in top)<=r[1] or min(p[1] for p in top)>=r[3]:continue
        clipped=intersect_rect(top,r)
        if len(clipped)<3:continue
        mesh=prism(f'exterior_user_fill_d_{len(supports)}',[(x,y,z-.03) for x,y,z in clipped],'exterior_concrete')
        if mesh is None:continue
        n=len(mesh['vertices'])//2
        mesh['vertices']=[(x,y,BASE if i<n else z) for i,(x,y,z) in enumerate(mesh['vertices'])]
        supports.append(mesh)
    ext['meshes'].extend(supports);ext['collision_meshes'].extend(supports)
    ext['concrete_fill_review']=dict(regions=REGIONS,base_z=BASE,support_meshes=len(supports),
        plan='exports/exterior_entrance_review_20261102/exterior_fill_proposal.png',
        preserve='Existing walking grades, terrace, both stairs, lower approach and garden remain open')
    return result
