import os,json,pickle
os.environ['MPLCONFIGDIR']='/tmp/povo-layout-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
P=Path('docs/plans/povo2_exterior_20261105')
s,c,boxes,levels,t=pickle.load(open('build/layout_review/current.pkl','rb'));p=next(q['connection']['povo2'] for q in levels if 'connection'in q)
f=next(f for f in json.load(open('data/reference/osm/povo_osm_overture.geojson'))['features'] if f['properties'].get('osm')=='w1193371312');ring=[(x-666250,y-5103800) for x,y in f['geometry']['coordinates'][0]]
fig,axes=plt.subplots(2,2,figsize=(14,18))
for ax,(floor,z) in zip(axes.flat,[(-2,-3.2),(-1,.4),(0,4),(1,11.2)]):
 for n,lo,hi,m in boxes:
  if lo[2]<z+1.3<hi[2] and hi[1]>-12 and lo[1]<115 and hi[0]>-27 and lo[0]<58 and ('wall' in m or m in ('window_frame','window_glass','metal_dark','exterior_concrete','exterior_entry_glass')):
   ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],fc='#67717e',alpha=.3,lw=0))
 ax.plot(*zip(*ring),color='#16834c',lw=1.8,label='OSM main footprint (reference)')
 a,b,c,d=p['stairs']['bounds'];ax.add_patch(Rectangle((a,b),c-a,d-b,fill=False,ec='#a7329d',lw=2,label='Shared core datum'))
 ax.axhline(10.82,color='#16834c',ls=':',lw=1)
 ax.set(xlim=(-29,61),ylim=(-14,116),aspect='equal',xlabel='East / m',ylabel='North / m',title=f'Floor {floor:+d} — current source slice, z={z:g} m')
 ax.grid(alpha=.2)
 if floor==0:
  for r in next(q for q in p['levels'] if q['floor']==0)['rooms']:
   a,b,c,d=r['bounds'];ax.text((a+c)/2,(b+d)/2,r['id'].upper(),ha='center',fontsize=7)
  ax.annotate('Projecting room row:\nregistration unresolved',xy=(15,4),xytext=(-27,-10),fontsize=8,arrowprops={'arrowstyle':'->','color':'#b33'})
 if floor in (-1,-2):
  a,b,c,d=p['gardens']['garden'];ax.add_patch(Rectangle((a,b),c-a,d-b,fill=False,ec='#4c9c26',lw=2));ax.text(40,23,'Garden footprint',fontsize=7)
 ax.legend(loc='upper left',fontsize=7)
fig.suptitle('POVO 2 — FLOOR REGISTRATION REVIEW\nAll panels use the same axes and scale; existing geometry, not relocated rooms',fontsize=15)
fig.text(.06,.025,'Green = geographic reference; magenta = common core datum. Exterior objects are included in the slices.\nUpper arrival is near the reference facade; floor-0 rooms project south of it. No floor has been scaled or moved.\nExisting floor elevations are source assumptions, not a measured vertical survey.',fontsize=10)
fig.subplots_adjust(top=.94,bottom=.07,hspace=.2);fig.savefig(P/'floor_registration_review.png',dpi=150);fig.savefig(P/'floor_registration_review.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(14,9));g=p['gardens'];a,b,c,d=g['garden']
ax.add_patch(Rectangle((a,b),c-a,d-b,fc='#d6e8c6',ec='#487c28',lw=2));ax.text(46,17,'GARDEN -2\nExisting rectangular footprint retained',ha='center',fontsize=12)
# Current stair ghost, explicitly obsolete.
u,v,w,h=g['down_stair'];ax.add_patch(Rectangle((u,v),w-u,h-v,fill=False,ec='#b95454',ls='--',lw=2));ax.text(u, v-1.1,'OLD POSITION — to relocate',color='#a33',fontsize=10)
u,v,w,h=g['passage'];ax.add_patch(Rectangle((u,v),w-u,h-v,fc='#eddfbd',ec='#a88d59'));ax.text(15,1.1,'Existing -1 terrace',fontsize=9)
# Proposed external stair: direction unchanged, entirely inside garden.
start=(a+c)/2;end=c-1.;y=b;wide=1.;mid=1.1;count=20;step=(end-start-mid)/count
ax.add_patch(Rectangle((start-1,y),1,wide,fc='#e4c07c',ec='black'))
for i in range(count):
 xx=start+i*step+(mid if i>=10 else 0)
 ax.add_patch(Rectangle((xx,y),step,wide,fc='#aec8de',ec='#354c66',lw=.6))
xx=start+10*step;ax.add_patch(Rectangle((xx,y),mid,wide,fc='#d2dfec',ec='#354c66'))
ax.add_patch(Rectangle((end,y),1,wide,fc='#e4c07c',ec='black'))
ax.annotate('',xy=(end,y+.5),xytext=(start,y+.5),arrowprops={'arrowstyle':'->','color':'#173a7a','lw':2})
ax.plot([a,c],[b-.1,b-.1],color='#555',lw=4);ax.text(39,7.7,'Retaining wall below road — confirmed side',fontsize=9)
ax.annotate('NEW START inside garden\n~halfway along its length',xy=(start,y+.5),xytext=(31,24),fontsize=11,arrowprops={'arrowstyle':'->'})
ax.annotate('DOWN direction retained\n1 m wall-side strip\n1 m lower landing',xy=(54.6,9.2),xytext=(55.8,12),fontsize=10,arrowprops={'arrowstyle':'->'})
# Route is deliberately not a newly validated walkway.
ax.plot([31.8,36.8,36.8,start-1],[1.145,1.145,9.25,9.25],ls=':',color='#d08b24',lw=2)
ax.text(24,4.5,'Terrace connection needs redesign\nDotted line = connection study only;\nNOT a validated walking route',fontsize=9,color='#9a6517')
ax.set(xlim=(7,65),ylim=(-3,27),aspect='equal',xlabel='East / campus m',ylabel='North / campus m',title='REVISED EXTERIOR PLAN — DOWN stair starts INSIDE Garden -2\nProvisional metric fit to the current garden; interior layout and stair direction preserved');ax.grid(alpha=.2)
fig.text(.09,.035,'Current garden: 17.5 x 11.25 m (source dimensions, not surveyed). New stair run: 7.75 m including 1.1 m mid-landing.\n20 risers across the existing 3.6 m drop: 0.18 m rise / ~0.333 m tread. Check landings, guards and approach before implementation.\nThis resolves the stair/garden relationship only; overall floor registration remains open.',fontsize=10)
fig.subplots_adjust(bottom=.15,top=.88);fig.savefig(P/'revised_garden_plan.png',dpi=160);fig.savefig(P/'revised_garden_plan.pdf')
(P/'revised_garden_proposal.json').write_text(json.dumps(dict(status='review proposal only; not implemented or surveyed',garden=g['garden'],old_stair=g['down_stair'],new_stair=[start,y,end,y+wide],top_landing=[start-1,y,start,y+wide],bottom_landing=[end,y,c,y+wide],direction='eastward descent retained',risers=count,rise=.18,tread=step,mid_landing=mid,approach_status='unresolved; do not implement dotted route as-is'),indent=2))
