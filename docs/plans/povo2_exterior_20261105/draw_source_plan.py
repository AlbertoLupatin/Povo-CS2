import json,pickle,os
os.environ['MPLCONFIGDIR']='/tmp/povo-layout-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from pathlib import Path
out=Path('docs/plans/povo2_exterior_20261105');out.mkdir(exist_ok=True)
s,c,boxes,levels,stair=pickle.load(open('build/layout_review/current.pkl','rb'))
p=next(x['connection']['povo2'] for x in levels if 'connection' in x)
data=json.load(open('data/reference/osm/povo_osm_overture.geojson'))
features={f['properties'].get('osm'):f for f in data['features']}
def ring(id):return [(x-666250,y-5103800) for x,y in features[id]['geometry']['coordinates'][0]]
def cross(poly,x):
 ys=[]
 for (a,b),(c,d) in zip(poly,poly[1:]):
  if min(a,c)<=x<max(a,c):ys.append(b+(d-b)*(x-a)/(c-a))
 return sorted(ys)
x=18.25;p1=cross(ring('r3663359'),x)[-1];p2=cross(ring('w1193371312'),x)[0]
fig,axs=plt.subplots(1,3,figsize=(21,10));a,b,d=axs
for id,col,label in [('r3663359','#bac8d7','Povo 1'),('w1193371312','#c9d9cb','Povo 2'),('w1192921194','#dddddd','Bridge')]:
 a.add_patch(Polygon(ring(id),fc=col,ec='#34495e',alpha=.8));
 if id!='w1192921194':a.text(0,-45 if id=='r3663359' else 48,label,ha='center',fontsize=13)
a.plot([x,x],[p1,p2],color='black');a.text(x+2,-5,f'{p2-p1:.2f} m\nOSM facade gap',fontsize=10)
a.plot([-23,25],[10,10],'--',color='#dc8025');a.plot([-23,24],[-20,-20],'--',color='#dc8025')
a.text(-23,-27,'Dashed orange: source facade planes\n30.0 m source bridge span',fontsize=9)
a.set(xlim=(-30,60),ylim=(-55,80),title='1. Building spacing / reference check')
# Source horizontal slice: no synthetic rearrangement.
for n,lo,hi,m in boxes:
 if lo[2]<5.2<hi[2] and ('p2_' in n or 'povo2' in n) and m in ('wall','window_frame','window_glass','entry_glass','exterior_white','exterior_concrete'):
  b.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],fc='#999999',alpha=.45,linewidth=0))
def rect(ax,r,col,label,alpha=.45):
 x,y,u,v=r;ax.add_patch(Rectangle((x,y),u-x,v-y,fc=col,ec='#444',alpha=alpha));ax.text((x+u)/2,(y+v)/2,label,ha='center',va='center',fontsize=8)
for lv in p['levels']:
 if lv['floor']==0:
  for r in lv['rooms']:rect(b,r['bounds'],'#e68883' if r['id'] in ('b106','b108','b109') else '#a6c6e8',r['id'].upper())
cfg=json.load(open('config/povo2_additions.json'))
rect(b,cfg['reception'],'#dac8e1','Reception');rect(b,cfg['ground_approach'],'#f4dda4','');rect(b,cfg['ground_corridor'],'#f4dda4','Room corridor')
rect(b,p['stairs']['bounds'],'#a3a5a8','Existing stair room\nDIRECTIONS FIXED')
entry=json.load(open('config/povo_exterior.json'))['povo2_double_entrance'];rect(b,entry['lobby_bounds'],'#c4e9dd','Entrance lobby\nrectangular target')
for k in ('outer_x','inner_x'):b.plot([entry[k]]*2,[29.5,37.5],color='#228b60',lw=2)
b.plot(*zip(*ring('w1193371312')),color='#158447',lw=2)
b.text(-20,2,'RED: projecting room row\nDestination unresolved:\nstraight shift overlaps core',fontsize=9,color='#9e3025')
b.annotate('',xy=(18,14),xytext=(18,8),arrowprops={'arrowstyle':'->','color':'#c43a32','lw':2})
b.set(xlim=(-25,56),ylim=(-4,76),title='2. Actual floor 0 / correction constraints')
g=p['gardens'];rect(d,g['garden'],'#b6d697','Garden -2');rect(d,g['passage'],'#edcf9e','Terrace -1');rect(d,g['down_stair'],'#c0c6cb','DOWN');rect(d,g['up_stair'],'#c0c6cb','UP')
for key,col in [('up','#174c9b'),('down','#bd4b26')]:
 pts=g['routes'][key];d.plot([q[0] for q in pts],[q[1] for q in pts],color=col,lw=2)
 i=len(pts)//2;d.annotate('',xy=pts[i+1][:2],xytext=pts[i-1][:2],arrowprops={'arrowstyle':'->','color':col,'lw':2})
road=json.load(open('config/povo_exterior.json'))['road'];d.plot([q[0] for q in road['points']],[q[1] for q in road['points']],color='#888',lw=6,alpha=.5)
d.axhline(10.82,color='#158447',lw=1,ls='--');d.text(8,23,'Actual stair runs shown — do not rotate.\nExterior relocation must retain run directions.\nGrass / fence / bush: approved topology,\nmetric placement pending ruler checks.',fontsize=9)
d.set(xlim=(5,61),ylim=(-12,32),title='3. Existing exterior routes / direction baseline')
for ax in axs:ax.set_aspect('equal');ax.set_xlabel('East / local metres');ax.set_ylabel('North / local metres');ax.grid(alpha=.2)
fig.suptitle('POVO 2 — SOURCE-BASED REDESIGN WORKSHEET\nExisting geometry + geographic reference + explicit unresolved corrections',fontsize=17)
fig.text(.02,.035,'Green outline: cached OSM building footprint, not a floor-plan survey. Approx. 0.5–1 m reference uncertainty.\nInterior relationships and stair directions preserved. No proposed room destination has been invented. No geometry changed.',fontsize=11)
fig.subplots_adjust(top=.88,bottom=.13,wspace=.24)
fig.savefig(out/'source_based_plan.png',dpi=160);fig.savefig(out/'source_based_plan.pdf')
(out/'spacing_measurements.json').write_text(json.dumps({'reference':'cached OSM / Overture 2026-10-21; EPSG:25832','at_local_east':x,'povo1_north_facade':p1,'povo2_south_facade':p2,'reference_gap':p2-p1,'source_bridge_span':30,'not_surveyed':True},indent=2))
print('Reference gap',p2-p1)
