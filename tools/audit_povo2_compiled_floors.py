"""Read real Source 2 PHYS triangles and check the approved basement footprints."""
import hashlib,json,math,re,struct,sys
from pathlib import Path


def on_triangle(point,face):
    a,b,c=face;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    length=math.sqrt(sum(x*x for x in n))
    if length<1e-9 or abs(sum(n[i]*(point[i]-a[i]) for i in range(3)))>length*.001:return False
    axis=max(range(3),key=lambda i:abs(n[i]));i,j=[k for k in range(3) if k!=axis]
    den=(b[j]-c[j])*(a[i]-c[i])+(c[i]-b[i])*(a[j]-c[j])
    s=((b[j]-c[j])*(point[i]-c[i])+(c[i]-b[i])*(point[j]-c[j]))/den
    t=((c[j]-a[j])*(point[i]-c[i])+(a[i]-c[i])*(point[j]-c[j]))/den
    return min(s,t,1-s-t)>=-1e-4


def main():
    if len(sys.argv)!=3:
        print('Usage: audit_povo2_compiled_floors.py PHYS_DUMP.txt REPORT.json')
        return 2
    spec=json.loads(Path('exports/povo_campus/provenance.json').read_text())['povo2']
    text=Path(sys.argv[1]).read_text()
    vertex_blocks=re.findall(r'm_Vertices\s*=\s*#\[([^\]]*)\]',text,re.S)
    triangle_blocks=re.findall(r'm_Triangles\s*=\s*#\[([^\]]*)\]',text,re.S)
    assert vertex_blocks and len(vertex_blocks)==len(triangle_blocks)
    triangles=[];units=39.37007874
    for vv,tt in zip(vertex_blocks,triangle_blocks):
        vertices=[(y/units,z/units,x/units) for x,y,z in struct.iter_unpack('<fff',bytes.fromhex(vv))]
        for face in struct.iter_unpack('<III',bytes.fromhex(tt)):
            triangles.append([vertices[i] for i in face])
    report=[]
    for level in spec['basement_rebuild']['levels']:
        floor=level['floor'];z=.4 if floor==-1 else -3.2;selected=[]
        for face in triangles:
            if not all(abs(v[2]-z)<.015 for v in face):continue
            a,b,c=face
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-8:continue
            selected.append((face,den,(min(v[0] for v in face),min(v[1] for v in face),max(v[0] for v in face),max(v[1] for v in face))))
        missing=[];samples=0;shaft=spec['lift']['shaft']
        for x0,y0,x1,y1 in level['areas']:
            for i in range(math.ceil((x1-x0)/.35)):
                for j in range(math.ceil((y1-y0)/.35)):
                    x=min(x1-.02,x0+.02+i*.35);y=min(y1-.02,y0+.02+j*.35)
                    if floor==-1 and shaft[0]<=x<=shaft[2] and shaft[1]<=y<=shaft[3]:continue
                    samples+=1;hit=False
                    for face,den,(a0,b0,a1,b1) in selected:
                        if not(a0-.001<=x<=a1+.001 and b0-.001<=y<=b1+.001):continue
                        a,b,c=face
                        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
                        if min(u,v,1-u-v)>=-1e-5:hit=True;break
                    if not hit:missing.append([x,y,z])
        report.append(dict(floor=floor,samples=samples,missing_samples=len(missing),missing_points=missing))
        print('Compiled floor',floor,':',samples,'samples,',len(missing),'missing')
    column_samples=0;column_missing=[]
    bounds=[(face,[min(v[k] for v in face) for k in range(3)],
                  [max(v[k] for v in face) for k in range(3)]) for face in triangles]
    for x,y in spec['parking'].get('columns',[]):
        faces=[face for face,lo,hi in bounds if lo[0]<x+.32 and hi[0]>x-.32 and lo[1]<y+.32 and hi[1]>y-.32]
        for z in (-3.,-1.6,-.4):
            for p in ((x-.3,y,z),(x+.3,y,z),(x,y-.3,z),(x,y+.3,z)):
                column_samples+=1
                if not any(on_triangle(p,face) for face in faces):column_missing.append(p)
    print('Compiled columns:',column_samples,'surface samples,',len(column_missing),'missing')
    locked=[]
    correction=spec.get('minus1_corrections',{})
    for key in ('upper_junction_door','lower_junction_door','c5_north_junction_door'):
        portal=correction.get(key)
        if not portal:continue
        centre=portal['centre'];axis=portal['axis'];across=1-axis;missing=[];samples=0
        selected=[face for face,lo,hi in bounds if all(lo[k]<centre[k]+1.1 and hi[k]>centre[k]-1.1 for k in range(2))]
        for side in (-.04,.04):
            for offset in (-portal['width']*.3,portal['width']*.3):
                for height in (.3,1.2,2.):
                    p=list(centre);p[axis]+=side;p[across]+=offset;p[2]+=height;samples+=1
                    if not any(on_triangle(p,face) for face in selected):missing.append(p)
        locked.append(dict(id=key,samples=samples,missing_points=missing))
        print('Compiled locked door',key,':',samples,'samples,',len(missing),'missing')
    passed=not any(r['missing_samples'] for r in report) and not column_missing and not any(r['missing_points'] for r in locked)
    Path(sys.argv[2]).write_text(json.dumps(dict(status='passed' if passed else 'failed',physics_dump_sha256=hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),metadata_sha256=hashlib.sha256(Path('exports/povo_campus/provenance.json').read_bytes()).hexdigest(),scope='Compiled PHYS floors, columns and fixed shut door surfaces; engine movement checked separately',levels=report,columns=dict(samples=column_samples,missing_points=column_missing),locked_doors=locked),indent=2)+'\n')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
