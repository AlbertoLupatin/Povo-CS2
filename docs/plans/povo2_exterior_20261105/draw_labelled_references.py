import os,pickle,json
os.environ['MPLCONFIGDIR']='/tmp/povo-layout-mpl'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
P=Path('docs/plans/povo2_exterior_20261105')
_,_,boxes,levels,_=pickle.load(open('build/layout_review/current.pkl','rb'));link=next(q['connection'] for q in levels if 'connection'in q);p=link['povo2'];g=p['gardens']
fig,axs=plt.subplots(2,2,figsize=(17,14));cols={'core':'#9e65b5','entry':'#2a9c91','terrace':'#d9a43b','garden':'#70a94b'}
def area(ax,r,col):
 a,b,c,d=r;ax.add_patch(Rectangle((a,b),c-a,d-b,fc=col,ec=col,alpha=.24,lw=2))
def tag(ax,xy,text,pos,col):
 ax.annotate(text,xy=xy,xytext=pos,fontsize=9,color=col,bbox={'boxstyle':'round,pad=.3','fc':'white','ec':col},arrowprops={'arrowstyle':'-','color':col},ha='left',va='center')
for ax,(fl,z,title) in zip(axs.flat,[(0,4,'0 — Entrance and classrooms'),(1,11.2,'+1 — Bridge arrival'),(-1,.4,'−1 — Interior exits and terrace'),(-2,-3.2,'−2 — Garden and lower access')]):
 for n,lo,hi,m in boxes:
  if lo[2]<z+1.3<hi[2] and hi[1]>-10 and lo[1]<46 and hi[0]>-26 and lo[0]<58 and ('wall' in m or m in ('window_frame','window_glass','exterior_concrete')):
   ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],fc='#75808a',lw=0,alpha=.35))
 area(ax,p['stairs']['bounds'],cols['core']);tag(ax,(15.75,20),'S — INTERNAL STAIR CORE\nSame location on all panels',(-23,28),cols['core'])
 if fl==0:
  cfg=json.load(open('config/povo2_additions.json'));e=json.load(open('config/povo_exterior.json'))['povo2_double_entrance'];area(ax,e['lobby_bounds'],cols['entry']);area(ax,cfg['reception'],'#76bfc4')
  tag(ax,(49.4,33.5),'E — STREET ENTRANCE\nOuter → inner doors',(33,43),cols['entry']);tag(ax,(16.5,31),'R — RECEPTION',(-23,40),cols['entry'])
  for r in cfg['ground_rooms']:
   area(ax,r['bounds'],'#d56363');a,b,c,d=r['bounds'];ax.text((a+c)/2,(b+d)/2,r['id'].upper(),ha='center',fontsize=9)
  area(ax,cfg['ground_approach'],'#ddb554');area(ax,cfg['ground_corridor'],'#ddb554');tag(ax,(24,16),'C — SHORT CORRIDOR\nthen perpendicular room corridor',(33,23),'#8a6723')
 elif fl==1:
  area(ax,link['bridge'],'#5a8ac6');tag(ax,(18.25,0),'B — BRIDGE FROM POVO 1',(-23,-5),'#315c91')
  # Actual upper core route, no rearrangement.
  pts=link['stair'].get('path',[])
  if pts:ax.plot([q[0] for q in pts],[q[1] for q in pts],color=cols['core'],lw=1.5)
 elif fl==-1:
  area(ax,g['passage'],cols['terrace']);area(ax,g['up_stair'],'#5a8ac6');tag(ax,(21.75,-2),'U — EXIT STAIR TO STREET',(-23,-6),'#315c91')
  tag(ax,(21.85,2),'T — TERRACE / EXIT DOOR',(-23,6),'#926815');tag(ax,(22,12),'C5 — INTERIOR APPROACH',(32,28),'#926815')
  pts=g['routes']['indoor'];ax.plot([q[0] for q in pts],[q[1] for q in pts],color='#b08226',lw=2)
 else:
  pts=g['routes']['office_exit'];ax.plot([q[0] for q in pts],[q[1] for q in pts],color='#b08226',lw=2);tag(ax,pts[-1][:2],'I — EXISTING LOWER\nINTERIOR EXIT',(31,29),'#926815')
 if fl in (-1,-2):
  area(ax,g['garden'],cols['garden']);tag(ax,(49,17),'G — CURRENT GARDEN\nPosition being corrected',(32,40),'#467523')
  r=g['down_stair'];a,b,c,d=r;ax.add_patch(Rectangle((a,b),c-a,d-b,fill=False,ec='#b64646',ls='--',lw=2));tag(ax,(37,1),'D — OLD GARDEN STAIR\nDashed: NOT the proposed position',(33,-6),'#b64646')
 ax.set(xlim=(-27,61),ylim=(-11,47),aspect='equal',xlabel='East / metres',ylabel='North / metres',title=title);ax.grid(alpha=.15)
fig.suptitle('POVO 2 — NAMED LANDMARKS IN THE CURRENT SOURCE\nSame orientation and scale • baseline for correction, not a new interior arrangement',fontsize=16)
fig.text(.06,.025,'E entrance · R reception · S internal core · C corridor · B bridge · U street exit stair · T terrace · D garden stair · G garden\nThe old garden/stair positions are explicitly marked. Existing interior geometry is preserved; no road-facing stair ascent is proposed.',fontsize=11)
fig.subplots_adjust(top=.91,bottom=.1,wspace=.15,hspace=.2);fig.savefig(P/'labelled_floor_references.png',dpi=150);fig.savefig(P/'labelled_floor_references.pdf')
