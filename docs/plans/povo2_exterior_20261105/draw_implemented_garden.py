"""Render implemented source geometry; run from repository root."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/povo-layout-mpl')
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from tools.build_povo_campus import build_geometry
# An explicit cache is useful during review; the default regenerates the source.
if len(sys.argv)>1:
    import pickle
    _,_,boxes,levels,_=pickle.load(open(sys.argv[1],'rb'))
else:
    _,_,boxes,levels,_=build_geometry()
p=next(l['connection']['povo2'] for l in levels if l.get('connection'))
g=p['gardens']
fig,axs=plt.subplots(2,1,figsize=(13,10),height_ratios=[2,1])
ax=axs[0]
colors={'floor_terrace':'#dfddd2','floor_grating':'#aaa5b3','floor_yard_grass':'#a1bf8b'}
for n,lo,hi,m in sorted(boxes,key=lambda b:b[2][2]):
    if (n.startswith('p2_aligned_garden_') or n=='p2_basement_drawio_terrace') and m in colors:
        ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],fc=colors[m],ec='#6e7970',lw=.5))
a,b,c,d=g['garden'];mid=(a+c)/2;y=(g['passage'][1]+g['passage'][3])/2
ax.text((a+c)/2,(b+d)/2,'GARDEN −2\nOriginal 17.5 × 11.25 m dimensions retained',ha='center',va='center')
ax.text(24,y+1.5,'EXISTING −1 CORRIDOR',ha='center')
ax.annotate('DOWN',xy=(mid-.4,y),xytext=(a+1.2,y),arrowprops={'arrowstyle':'->','color':'#652f7f'},color='#652f7f',va='center')
ax.annotate('Garden starts / upper landing',xy=(a,y),xytext=(a-5,-3),arrowprops={'arrowstyle':'-'},ha='center')
ax.annotate('Lower landing at midpoint',xy=(mid,y),xytext=(mid+4,-3),arrowprops={'arrowstyle':'-'},ha='center')
ax.plot(*zip(*[q[:2] for q in g['routes']['office_exit']]),color='#326d89',lw=2)
ax.annotate('Retained interior exit −2',xy=g['routes']['office_exit'][0][:2],xytext=(25,14),arrowprops={'arrowstyle':'-'})
ax.text(44,-1,'Road-side retaining wall',ha='center',fontsize=9)
ax.set(xlim=(19,51),ylim=(-5,16),aspect='equal',xlabel='East / metres →',ylabel='North / metres ↑')
ax.grid(alpha=.15)
ax=axs[1]
ax.plot([22,a+.6],[.4,.4],color='#666',lw=3)
for n,lo,hi,m in boxes:
    if n.startswith('p2_aligned_garden_down_step_') or n=='p2_aligned_garden_midlanding':
        ax.plot([lo[0],hi[0]],[hi[2],hi[2]],color='#625071',lw=2)
ax.plot([a,c],[-3.2,-3.2],color='#74935f',lw=3)
ax.text(24,.7,'−1 corridor',ha='center')
ax.text(46,-2.8,'−2 garden',ha='center')
ax.axvline(a,ls=':',color='#aaa');ax.axvline(mid,ls=':',color='#aaa')
ax.set(xlim=(19,51),ylim=(-4,2),xlabel='East / metres →',ylabel='Height / metres',title='Side elevation — stair descends into garden, not toward road')
ax.grid(alpha=.15)
fig.suptitle('IMPLEMENTED EXTERIOR CONNECTION — interior layout retained',fontsize=15)
fig.text(.06,.02,'Corridor-anchored source geometry, not surveyed registration. Room/facade and 5 m grass-strip alignment remain pending.',fontsize=10)
fig.tight_layout(rect=(0,.04,1,.95))
out=Path(__file__).resolve().parent
fig.savefig(out/'implemented_garden.png',dpi=140)
fig.savefig(out/'implemented_garden.pdf')
