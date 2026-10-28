import pickle
from PIL import Image,ImageDraw
boxes,levels=pickle.load(open('geom.pkl','rb'))
X0,X1,Y0,Y1=-23.5,24.5,-103.5,-19.5; S=24
FURN=('seat','desk','office','canteen','sanitary','teaching','projection','metal','light','ceiling','sign','floor','window_frame')
def overlay(n,bbox,z,name):
    plan=Image.open(f'rot{n}.jpg'); k=plan.width/1600
    l,t,r,b=[v*k for v in bbox]
    W=int((Y1-Y0)*S); H=int((X1-X0)*S)
    # map outline (-23,-103)-(24,-20) to bbox
    sx=(r-l)/(83*S); sy=(b-t)/(47*S)
    ox=l-(-103-Y0)*S*sx; oy=t-(-23-X0)*S*sy
    crop=plan.crop((ox,oy,ox+W*sx,oy+H*sy)).resize((W,H)).convert('RGB')
    im=Image.blend(Image.new('RGB',(W,H),'white'),crop,0.75); d=ImageDraw.Draw(im,'RGBA')
    for nm,lo,hi,m in boxes:
        if not(lo[2]<=z<=hi[2]) or m.startswith(FURN) or hi[0]<X0 or lo[0]>X1 or hi[1]<Y0 or lo[1]>Y1: continue
        a=((lo[1]-Y0)*S,(lo[0]-X0)*S); c=((hi[1]-Y0)*S,(hi[0]-X0)*S)
        col=(0,120,255,150) if 'glass' in m else (230,0,0,170)
        d.rectangle((min(a[0],c[0]),min(a[1],c[1]),max(a[0],c[0]),max(a[1],c[1])),fill=col)
    im.save(name)
overlay(17,(15,40,1585,930),5.5,'ov_m1.png')
overlay(20,(12,15,1575,930),9.1,'ov_0.png')
overlay(22,(10,15,1590,935),12.7,'ov_p1.png')
print('ok')
