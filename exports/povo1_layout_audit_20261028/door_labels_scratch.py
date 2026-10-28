import pickle
from PIL import Image,ImageDraw,ImageFont
exec(open('gaps.py').read().split("zs={")[0])
X0,Y0,S0,S=-23.5,-103.5,60,30
try: F=ImageFont.truetype('arialbd.ttf',20); FS=ImageFont.truetype('arial.ttf',17); FT=ImageFont.truetype('arialbd.ttf',26)
except OSError: F=FS=FT=ImageFont.load_default()
P=lambda x,y:((y-Y0)*S,(x-X0)*S)
CLASS=('A1','A2','LAB','Acquario')
def make(src,lid,z,out,title,extra=()):
    im=Image.open(src); im=im.resize((im.width*S//S0,im.height*S//S0)).convert('RGB')
    d=ImageDraw.Draw(im,'RGBA')
    level=[l for l in levels if l['id']==lid][0]
    for r in level['rooms']:
        f=r.get('footprint_local_metres'); side=r.get('door_side')
        if not f: continue
        x0,y0,x1,y1=f
        lines={'x0':(0,x0,y0,y1),'x1':(0,x1,y0,y1),'y0':(1,y0,x0,x1),'y1':(1,y1,x0,x1)}
        for nm,(axis,line,a0,a1) in lines.items():
            for g0,g1 in gaps(axis,line,a0+.15,a1-.15,z):
                if g1-g0>3: continue
                if axis==0: a,b=P(line,g0),P(line,g1)
                else: a,b=P(g0,line),P(g1,line)
                d.rectangle((min(a[0],b[0])-5,min(a[1],b[1])-5,max(a[0],b[0])+5,max(a[1],b[1])+5),fill=(0,170,0,220))
                tgt=[a0+.85*(a1-a0)]
                if lid!='academic_upper' and r['label'].startswith(CLASS) and r.get('door_fraction')==0.85 and min(abs((g0+g1)/2-t) for t in tgt)<1.0 and nm=={'u_min':'y0','u_max':'y1','v_min':'x0','v_max':'x1'}.get(side) and r['label'] not in ('A109','A110'):
                    m0,m1=a0+a1-g1,a0+a1-g0
                    if axis==0: a,b=P(line,m0),P(line,m1)
                    else: a,b=P(m0,line),P(m1,line)
                    cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2
                    d.ellipse((cx-17,cy-17,cx+17,cy+17),outline=(255,120,0,255),width=5)
        cx,cy=P((x0+x1)/2,(y0+y1)/2); t=r['label'][:14]
        w=d.textlength(t,font=F); d.rectangle((cx-w/2-4,cy-13,cx+w/2+4,cy+13),fill=(255,255,255,225)); d.text((cx-w/2,cy-11),t,fill=(0,0,0),font=F)
    for kind,args,label in extra:
        if kind=='ring':
            for (x,y) in args:
                cx,cy=P(x,y); d.ellipse((cx-17,cy-17,cx+17,cy+17),outline=(255,120,0,255),width=5)
            cx,cy=P(*args[0]); d.text((cx+20,cy-30),label,fill=(200,80,0),font=FS)
        if kind=='band':
            (xa,ya,xb,yb)=args; a,b=P(xa,ya),P(xb,yb)
            d.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),outline=(255,120,0,255),width=4,fill=(255,160,0,60))
            d.text((min(a[0],b[0])-330,max(a[1],b[1])+10),label,fill=(200,80,0),font=FS)
    # legend
    d.rectangle((10,im.height-92,1180,im.height-8),fill=(255,255,255,235))
    d.text((20,im.height-88),title,fill=(0,0,0),font=FT)
    d.rectangle((20,im.height-46,48,im.height-26),fill=(0,170,0,220)); d.text((56,im.height-48),'door in the generated map',fill=(0,0,0),font=FS)
    d.ellipse((300,im.height-50,330,im.height-20),outline=(255,120,0,255),width=5); d.text((338,im.height-48),'door on the plan, missing from the map',fill=(0,0,0),font=FS)
    d.text((700,im.height-48),'red = generated walls, grey = photographed plan',fill=(0,0,0),font=FS)
    im.save(out); print(out,im.size)
make('ov_m1_hi.png','academic_ground',5.5,'doors_floor-1_labelled.png','Povo 1 floor -1: generated walls over plan 17 (rotated)',extra=(('ring',[(-12.2,-52.0)],''),))
make('ov_0_hi.png','academic_first',9.1,'doors_floor0_labelled.png','Povo 1 floor 0: generated walls over photo 20 emergency plan (rotated)')
make('ov_p1_hi.png','academic_upper',12.7,'doors_floor+1_labelled.png','Povo 1 floor +1: generated walls over plan 22 (rotated)',
     extra=(('ring',[(12.6,-71.2),(12.6,-50.0)],'terrace double doors on plan 22'),('band',(-20.9,-34.0,15.9,-32.4),'small-room band on plan 22')))
