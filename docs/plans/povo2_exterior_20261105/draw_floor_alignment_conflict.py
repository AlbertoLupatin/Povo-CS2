"""Section explaining the remaining road/grass/basement registration conflict."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/povo-layout-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from pathlib import Path
fig,ax=plt.subplots(figsize=(12,6))
ax.add_patch(Rectangle((2,.4),13.2,3.1,fc='#ddd9e3',ec='#786c8b'))
ax.text(9,1.8,'Existing −1 offices\n(interiors to preserve)',ha='center',fontsize=12)
ax.add_patch(Rectangle((10.8,4),4.6,3.35,fc='#c2d8e9',ec='#49697e'))
ax.text(13.1,5.65,'Relocated\nfloor-0 rooms',ha='center',fontsize=11)
ax.plot([10.8,10.8],[-.4,7.4],ls='--',lw=2,color='#bc9426')
ax.annotate('Yellow façade line',xy=(10.8,7.2),xytext=(7,8.3),ha='center',arrowprops={'arrowstyle':'-'},color='#8b6912')
ax.plot([2,2],[.4,3.5],lw=3,color='#8c4141')
ax.annotate('Current −1 office front',xy=(2,1.8),xytext=(-4,.1),ha='center',arrowprops={'arrowstyle':'-'},color='#8c4141')
ax.plot([-8,-.6],[4.12,4.12],lw=8,color='#8c9397')
ax.text(-5.5,4.6,'Road + pavement',ha='center',fontsize=11)
ax.plot([-.6,4.4],[4.12,.4],lw=3,color='#4a893e')
ax.text(-.1,6.3,'5 m grass strip\nfalls toward terrace',color='#427334',ha='center',fontsize=11)
ax.annotate('',xy=(-.6,5.6),xytext=(4.4,5.6),arrowprops={'arrowstyle':'<->','color':'#427334'})
ax.plot([4.4,6.11],[.4,.4],lw=6,color='#c99427')
ax.annotate('−1 terrace',xy=(5.3,.4),xytext=(5,-1),ha='center',arrowprops={'arrowstyle':'-'},color='#966614')
ax.add_patch(Polygon([(2,.4),(4.4,.4),(2,2.1856)],fc='#d4525233',ec='#ad3434',hatch='///'))
ax.text(-6.5,-2,'Does the real −1 office front align with the yellow façade above?\nThe current model puts it 8.8 m closer to the road.',fontsize=12)
ax.set(xlim=(-8.5,16),ylim=(-2.8,9),xlabel='North / local metres →',ylabel='Height / local metres');ax.grid(alpha=.12)
fig.suptitle('REMAINING ALIGNMENT CHECK — section through the office frontage',fontsize=15)
fig.text(.08,.015,'Green line illustrates the clash if the road stays fixed; it is not an implemented grass placement. Road grade shown at the exit stair.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.94))
out=Path(__file__).resolve().parent
fig.savefig(out/'floor_alignment_conflict.png',dpi=140)
fig.savefig(out/'floor_alignment_conflict.pdf')
