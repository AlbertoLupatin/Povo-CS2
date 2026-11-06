"""Identify the real-world facade-to-stairwell distance needed for registration."""
import os,json
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/povo-layout-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
root=Path(__file__).resolve().parents[3]
cfg=json.loads((root/'config/povo2_additions.json').read_text())
entry=json.loads((root/'config/povo_exterior.json').read_text())['povo2_double_entrance']
fig,ax=plt.subplots(figsize=(11,9))
def rect(r,col,label='',size=11):
 a,b,c,d=r
 ax.add_patch(Rectangle((b,-c),d-b,c-a,fc=col,ec='#54616a',lw=1))
 if label:ax.text((b+d)/2,-(a+c)/2,label,ha='center',va='center',fontsize=size)
rect(cfg['ground_approach'],'#f1dfb8','Short corridor',9)
rect(cfg['ground_corridor'],'#f1dfb8')
for r in cfg['ground_rooms']:rect(r['bounds'],'#e9c9c6',r['id'].upper(),10)
rect([11,18,20.5,26],'#d2c4e3','Internal\nstairwell')
rect(cfg['reception'],'#c9e2da','Reception',10)
rect(entry['lobby_bounds'],'#d8ece6','Entrance\nlobby',11)
for k in ('outer_x','inner_x'):
 ax.plot([29.55,37.45],[-entry[k],-entry[k]],color='#237969',lw=3)
ax.annotate('Enter here',xy=(33.5,-49.4),xytext=(33.5,-57),ha='center',fontsize=11,arrowprops={'arrowstyle':'->'})
# Same orientation as the internal plan: north right, west up.
# A is only the reference facade line; its registration is what is being checked.
a,b,y=10.8,18.,-15.75
ax.plot([a,a],[-32,1],ls=(0,(6,3)),color='#bb9021',lw=3)
ax.annotate('',xy=(b,y),xytext=(a,y),arrowprops={'arrowstyle':'<->','lw':2.5,'color':'#bc302f','shrinkA':0,'shrinkB':0})
for x,label in ((a,'A'),(b,'B')):
 ax.scatter([x],[y],s=45,color='#bc302f',zorder=5)
 ax.text(x,y-2.4,label,ha='center',va='center',fontsize=12,color='#bc302f',weight='bold')
ax.text((a+b)/2,y+2,'D = ?',ha='center',color='#bc302f',fontsize=15,weight='bold')
ax.annotate('A — yellow windowed façade\n(the side facing Povo 1)',xy=(a,-5),xytext=(0,10),ha='left',fontsize=11,arrowprops={'arrowstyle':'-','color':'#bb9021'},color='#836112')
ax.annotate('B — nearest face of the\ninternal stairwell enclosure',xy=(b,-12),xytext=(22,3),ha='left',fontsize=11,arrowprops={'arrowstyle':'-','color':'#65517b'},color='#65517b')
ax.text(1,-37,'B106 / B108 / B109\nshown in their current\nmodel positions',fontsize=10,color='#88524e')
ax.text(0,-51,'← Povo 1 / bridge side',fontsize=11,color='#52616b')
ax.set(xlim=(-2,45),ylim=(-61,17),aspect='equal');ax.axis('off')
fig.suptitle('Measure D: yellow façade → nearest stairwell wall',fontsize=17,y=.97)
fig.text(.5,.91,'A straight distance perpendicular to the façade, on floor 0.',ha='center',fontsize=12)
fig.text(.08,.045,'Orientation follows the internal plan: enter from the bottom, reception ahead, stairwell to its left.\nDashed yellow line = provisional façade reference. Please measure the real walls, not this drawing.',fontsize=10)
fig.subplots_adjust(top=.88,bottom=.1,left=.06,right=.94)
out=Path(__file__).resolve().parent
fig.savefig(out/'requested_measurement.png',dpi=150)
fig.savefig(out/'requested_measurement.pdf')
