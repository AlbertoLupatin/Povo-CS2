import os,json,pickle
os.environ['MPLCONFIGDIR']='/tmp/povo-layout-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
P=Path('docs/plans/povo2_exterior_20261105')
_,_,boxes,levels,_=pickle.load(open('build/layout_review/registered.pkl','rb'));link=next(q['connection'] for q in levels if 'connection'in q);p=link['povo2'];cfg=json.load(open('config/povo2_additions.json'));entry=json.load(open('config/povo_exterior.json'))['povo2_double_entrance']
def xy(x,y):return y,-x
colors={'room':'#c3d9ec','corr':'#f3dfb0','core':'#d6bee4','entry':'#bae3dd','office':'#cddfc7'}
def rect(ax,r,col,label='',size=9):
 a,b,c,d=r;ax.add_patch(Rectangle((b,-c),d-b,c-a,facecolor=col,edgecolor='#82909b',lw=.7));
 if label:ax.text((b+d)/2,-(a+c)/2,label,ha='center',va='center',fontsize=size,clip_on=True)
def note(ax,point,text,place):ax.annotate(text,xy=xy(*point),xytext=place,fontsize=10,bbox={'boxstyle':'round,pad=.3','fc':'white','ec':'#516170'},arrowprops={'arrowstyle':'-','color':'#516170'},ha='center')
def draw(fl,z,limits,title):
 fig,ax=plt.subplots(figsize=(16,11))
 if fl==0:
  rect(ax,cfg['ground_approach'],colors['corr']);rect(ax,cfg['ground_corridor'],colors['corr'])
  for lv in p['levels']:
   if lv['floor']==0:
    for r in lv['rooms']:rect(ax,r['bounds'],colors['room'],r['id'].upper(),10)
  rect(ax,cfg['reception'],colors['entry'],'RECEPTION')
  rect(ax,entry['lobby_bounds'],colors['entry'],'ENTRANCE LOBBY',10)
  for k in ('outer_x','inner_x'):
   x=entry[k];ax.plot([29.55,37.45],[-x,-x],color='#168b79',lw=3)
  if limits[1]>80:
   rect(ax,cfg['aula_lobby'],colors['corr'],'Aula lobby');rect(ax,cfg['aula_magna'],colors['room'],'AULA MAGNA')
 elif fl in (-1,-2):
  lv=next(q for q in p['basement_rebuild']['levels'] if q['floor']==fl)
  for r in lv['areas']:rect(ax,r,'#f4f1e8')
  if fl==-1:
   for r in p['west_offices']['rooms']:rect(ax,r['bounds'],colors['office'],r.get('label',r['id']),7)
   for key in ('c5','e1','e2'):
    rect(ax,p['drawio_entrance']['areas'][key],colors['corr'] if key=='c5' else colors['room'],key.upper(),8)
   rect(ax,p['gardens']['passage'],'#edce94','EXTERNAL CORRIDOR −1',8)
  else:
   for r in p['basement_rebuild']['routes']:
    if r['id']=='minus2_parking_aisle':
     pts=r['points'];ax.plot([q[1] for q in pts],[-q[0] for q in pts],color='#b79d6d',ls='--')
 elif fl==1:
  for r in link['povo2_floor_parts']:rect(ax,r,colors['corr'])
  rect(ax,link['bridge'],'#c4d7ed','BRIDGE FROM POVO 1',9)
 # Shade only the actual well, before walls so partitions remain visible.
 rect(ax,p['stairs']['well_bounds'],colors['core'],'',8)
 # Wall slice from actual assembled geometry, no invented partitions.
 for n,lo,hi,m in boxes:
  if lo[2]<z+1.3<hi[2] and hi[1]>-21 and lo[1]<115 and hi[0]>-27 and lo[0]<57 and (n.startswith(('p2_','academic_first_link_p2_','exterior_p2_entry')) or 'west_' in n):
   if m in ('wall','window_frame','window_glass','exterior_white','exterior_entry_glass'):
    ax.add_patch(Rectangle((lo[1],-hi[0]),hi[1]-lo[1],hi[0]-lo[0],fc='#444f59' if 'glass' not in m else '#48a3c4',lw=0,alpha=.8))
 # Core overlay & source tread footprints
 a,b,c,d=p['stairs']['well_bounds']
 for n,lo,hi,m in boxes:
  if 'step_' in n and z<hi[2]<=z+3.6 and lo[0]>=a-.2 and hi[0]<=c+.2 and lo[1]>=b-.2 and hi[1]<=d+.2:
   ax.add_patch(Rectangle((lo[1],-hi[0]),hi[1]-lo[1],hi[0]-lo[0],fill=False,ec='#635078',lw=.5))
 note(ax,(15.75,22),'INTERNAL STAIRWELL',(21,0))
 # Actual lift position is shown as separate object, not an invented central core.
 if p.get('lift',{}).get('enabled',False):rect(ax,link['lift']['shaft'],'#b5a2ce','Lift',7)
 if fl==0:
  note(ax,(24,18),'SHORT CORRIDOR\nalongside stair room',(16,-33))
  note(ax,(7,16.7),'PERPENDICULAR CORRIDOR\nparallel to B106 / B108 / B109',(1,4))
  note(ax,(49.4,33.5),'ENTER HERE\nReception directly ahead',(34,-61))
  ax.plot([33.5,33.5,16.7,16.7],[-34.5,-24,-24,-3],color='#c08b28',lw=1.5,ls='--')
 if fl==-1:
  note(ax,(21.85,2),'EXIT TO EXTERNAL CORRIDOR',(1,-37))
  note(ax,(22,16.6),'C5 / C7 JUNCTION',(35,-29))
 if fl==-2:
  note(ax,(36,13.5),'LOWER INTERIOR EXIT\nto exterior garden connection',(26,-50))
 ax.set(xlim=(limits[0],limits[1]),ylim=(-65,10) if fl==0 else (-65,28),aspect='equal',xlabel='North / local metres →',ylabel='West / local metres ↑')
 ax.grid(alpha=.12);fig.suptitle(title,fontsize=17)
 fig.text(.07,.92,'Orientation: street entrance at bottom; looking inward. Povo 1 / bridge side is LEFT.',fontsize=11)
 fig.text(.07,.035,'IMPLEMENTED — B106/B108/B109 fit behind the yellow facade; 4.6 m room depth + 2.6 m corridor. Core and basement interiors retained.\nRoadside grass registration awaits the basement facade alignment check. The accepted exterior connection is on the final page.',fontsize=10)
 fig.subplots_adjust(top=.87,bottom=.12);return fig
with PdfPages(P/'internal_building_layout.pdf') as pdf:
 for fl,z,lim,title,name in [(0,4,(-5,48),'POVO 2 — ENTRANCE, RECEPTION, STAIR AND CLASSROOM CORRIDORS','internal_ground_detail'),(0,4,(-5,100),'POVO 2 — FLOOR 0 / FULL MODELLED INTERIOR','internal_ground_full'),(-1,.4,(-5,110),'POVO 2 — FLOOR −1 / EXISTING INTERIOR AND EXTERNAL EXIT','internal_minus1'),(-2,-3.2,(-5,75),'POVO 2 — FLOOR −2 / EXISTING INTERIOR ACCESS','internal_minus2'),(1,11.2,(-21,48),'POVO 2 — FLOOR +1 / MODELLED BRIDGE ARRIVAL','internal_bridge')]:
  fig=draw(fl,z,lim,title);pdf.savefig(fig);fig.savefig(P/(name+'.png'),dpi=140);plt.close(fig)
 fig,ax=plt.subplots(figsize=(16,11))
 ax.imshow(plt.imread(P/'corridor_garden_connection.png'));ax.axis('off')
 fig.suptitle('ACCEPTED EXTERIOR CONNECTION — schematic, not a registered floor plan',fontsize=15)
 pdf.savefig(fig);plt.close(fig)
print('Saved six-page internal layout PDF and floor previews')
