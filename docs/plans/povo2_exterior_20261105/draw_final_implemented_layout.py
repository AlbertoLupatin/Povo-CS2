"""Draw the final exported registration, never the historical local assembly.
Run from repository root; optional --cache build/layout_review/final_frontage.pkl.
"""
import argparse, os, pickle, sys
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/povo-final-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path);args=parser.parse_args()
if args.cache:
    with args.cache.open('rb') as f:settings,config,boxes,levels,stair=pickle.load(f)
else:
    from tools.build_povo_campus import build_registered_geometry
    settings,config,boxes,levels,stair=build_registered_geometry()
link=next(l['connection'] for l in levels if 'connection' in l);p=link['povo2'];ext=levels[0]['exterior']
assert p.get('frontage_registration'), 'Use the final registered geometry, not build_geometry()'
cfg=p['additions']['config'];g=p['gardens'];reg=p['frontage_registration'];land=p['landscape_registration']
OUT=Path(__file__).resolve().parent
C={'room':'#c7ddec','corr':'#f4dfad','core':'#dac6e6','entry':'#bfe3dd','garden':'#d7e9c7'}
def rect(ax,r,color,label='',size=9):
    a,b,c,d=r;ax.add_patch(Rectangle((b,-c),d-b,c-a,fc=color,ec='#7b8891',lw=.6))
    if label:ax.text((b+d)/2,-(a+c)/2,label,ha='center',va='center',fontsize=size)
def arrow(ax,points,color='#a66913'):
    ax.plot([v[1] for v in points],[-v[0] for v in points],color=color,lw=1.7)
    ax.annotate('',xy=(points[-1][1],-points[-1][0]),xytext=(points[-2][1],-points[-2][0]),arrowprops={'arrowstyle':'->','color':color,'lw':1.7})
def walls(ax,z):
    for name,lo,hi,m in boxes:
        if name.startswith(('p2_','academic_first_link_p2_','exterior_p2_entry_')) and lo[2]<z+1.3<hi[2] and (m in ('wall','window_frame','window_glass','exterior_white','exterior_entry_glass')):
            ax.add_patch(Rectangle((lo[1],-hi[0]),hi[1]-lo[1],hi[0]-lo[0],fc='#3d4c59' if 'glass' not in m else '#3296b2',lw=0,alpha=.85))
    a,b,c,d=p['stairs']['well_bounds']
    for name,lo,hi,m in boxes:
        if 'step_' in name and z<hi[2]<=z+3.6 and a-.2<=lo[0]<=hi[0]<=c+.2 and b-.2<=lo[1]<=hi[1]<=d+.2:
            ax.add_patch(Rectangle((lo[1],-hi[0]),hi[1]-lo[1],hi[0]-lo[0],fill=False,ec='#785989',lw=.45))
def base(ax):
    ax.set(xlim=(-9,105),ylim=(-59,27),aspect='equal',xlabel='North / m →',ylabel='West / m ↑');ax.grid(alpha=.13)
    ax.plot([10.8,10.8],[-31,25],color='#d9aa00',lw=2.7,zorder=5)
    ax.text(9.4,22,'Shared yellow facade N10.8',rotation=90,ha='right',va='top',fontsize=8,color='#8a6900')
def foot(fig,text):fig.text(.045,.025,text,fontsize=10)
with PdfPages(OUT/'final_implemented_layout.pdf') as pdf:
    fig,axs=plt.subplots(2,2,figsize=(20,16))
    for ax,(floor,z) in zip(axs.flat,[(0,4),(-1,.4),(-2,-3.2),(1,11.2)]):
        if floor==0:
            for key in ('ground_corridor','ground_approach','aula_lobby'):rect(ax,cfg[key],C['corr'])
            for room in next(l for l in p['levels'] if l['floor']==0)['rooms']:rect(ax,room['bounds'],C['room'],room['id'].upper(),9)
            rect(ax,cfg['aula_magna'],C['room'],'AULA MAGNA',9)
            rect(ax,cfg['reception'],C['entry'],'Reception',9);rect(ax,ext['entrance']['lobby_bounds'],C['entry'],'Entrance lobby',9)
            for bank in ext['entrance']['door_banks']:
                e,n,_=bank['centre'];ax.plot([n-.9,n+.9],[-e,-e],color='#147d6d',lw=2)
            arrow(ax,[(49.4,42.3),(24,42.3),(24,25.5),(3,25.5)])
            ax.text(28.3,-26,'Short\ncorridor',fontsize=8);ax.text(25.5,-2,'Room corridor',rotation=90,fontsize=8,ha='center',va='top')
        elif floor in (-1,-2):
            for r in next(l for l in p['basement_rebuild']['levels'] if l['floor']==floor)['areas']:rect(ax,r,'#f4f1e8')
            if floor==-1:
                for r in p['west_offices']['rooms']:rect(ax,r['bounds'],'#d5e5cd')
                rect(ax,g['passage'],C['corr']);arrow(ax,g['routes']['passage'])
                ax.text(15,-37,'−1 terrace → DOWN stair',fontsize=9)
            else:
                rect(ax,g['garden'],C['garden'],'Garden −2',9);arrow(ax,g['routes']['office_exit'])
                e,n,_=g['office_exit']['door_centre']
                ax.plot([n-.85,n+.85],[-e,-e],color='#147d6d',lw=2)
                ax.annotate('Garden exit W−31.8 / N15',xy=(n,-e),xytext=(34,-43),fontsize=9,arrowprops={'arrowstyle':'->'})
                ax.text(18,-10,'Parking / retained aisle',fontsize=9)
        else:
            for r in link['povo2_floor_parts']:rect(ax,r,C['corr'])
            rect(ax,link['bridge'],C['room']);ax.text(-7,-23,'Bridge from Povo 1',fontsize=9)
            ax.text(20,-23,'Internal bridge connector',fontsize=9)
        rect(ax,p['stairs']['well_bounds'],C['core']);walls(ax,z)
        ax.text(31,-15,'Stairs',ha='center',fontsize=9,bbox={'fc':'white','ec':'none','alpha':.8})
        base(ax);ax.set_title(f'Floor {floor:+d}  |  walking level z={z:g} m',fontsize=13)
    fig.suptitle('POVO 2 — FINAL IMPLEMENTED FLOOR REGISTRATION',fontsize=20,y=.98)
    foot(fig,'All panels: identical orientation and scale. Enter from bottom; stairwell is left of reception. No lift. Walls and treads are actual geometry.\nRoom colours identify existing model areas; blank space is not a claim about the real building. Fitted estimates, not a metric survey. Native CS2 validation pending.')
    fig.subplots_adjust(left=.055,right=.98,bottom=.085,top=.94,hspace=.23,wspace=.12)
    pdf.savefig(fig);fig.savefig(OUT/'final_implemented_floors.png',dpi=140);plt.close(fig)
    fig=plt.figure(figsize=(13,15));ax=fig.add_axes([.07,.31,.65,.6]);sec=fig.add_axes([.09,.09,.56,.15])
    # Plan uses the same orientation as the floor plans.
    rect(ax,[-1,-3.31,50,2.69],'#b7b9bc','ROAD — 6 m',10)
    rect(ax,[8.5,2.69,49.3,4.09],'#e7e5df')
    for a,b in land['grass_runs']:rect(ax,[a,4.09,b,9.09],C['garden'])
    rect(ax,land['bush'],'#719d58','BUSH 5 × 5 m',10)
    rect(ax,g['garden'],C['garden'],'GARDEN −2',11)
    for part in g['office_exit']['corridor_parts']:rect(ax,part,'#f4f1e8')
    e,n,_=g['office_exit']['door_centre']
    ax.plot([n-.85,n+.85],[-e,-e],color='#147d6d',lw=2)
    arrow(ax,g['routes']['office_exit'])
    ax.annotate('−2 exit W−31.8 / N15',xy=(n,-e),xytext=(16,-24),fontsize=10,arrowprops={'arrowstyle':'->'})
    rect(ax,g['passage'],C['corr']);rect(ax,g['up_stair'],'#b5cde2');rect(ax,g['down_stair'],'#b5cde2');rect(ax,g['down_landing'],'#e9cd91')
    for name,lo,hi,m in boxes:
        if name.startswith(('p2_registered_up_step_','p2_aligned_garden_down_step_')):
            rect(ax,[lo[0],lo[1],hi[0],hi[1]],'#b5cde2')
    for a,b in land['grass_runs']:ax.plot([land['grate_north']]*2,[-a,-b],color='#495662',lw=2)
    ax.plot([10.8]*2,[-8.5,-31.8],color='#d9aa00',lw=3)
    arrow(ax,g['routes']['up']);arrow(ax,g['routes']['passage']);arrow(ax,g['routes']['down'])
    ax.text(6.7,-21.75,'UP',fontsize=10,ha='center');ax.text(10,-36,'DOWN',fontsize=10,ha='center')
    ax.text(11.6,-18,'Yellow facade / building limit',fontsize=11)
    ax.text(9.9,-15,'−1 external corridor',rotation=90,fontsize=10,ha='center',va='center')
    ax.annotate('Stair START = garden start',xy=(9.95,-31.8),xytext=(16,-30),fontsize=11,arrowprops={'arrowstyle':'->'})
    ax.annotate('Lower landing ≈\ngarden midpoint',xy=(9.95,-41.15),xytext=(19,-43),fontsize=11,arrowprops={'arrowstyle':'->'})
    ax.annotate('Grass outside grate\nslopes to terrace',xy=(6.6,-43),xytext=(16,-47),fontsize=10,arrowprops={'arrowstyle':'-'})
    ax.text(6.6,-25.4,'5 m gap',fontsize=9,ha='center')
    ax.set(xlim=(-4,30),ylim=(-52,-6),aspect='equal',xlabel='North / m →',ylabel='West / m ↑');ax.grid(alpha=.14)
    sec.plot([2.69,4.09,9.09,10.8],[4.12,4.12,.4,.4],color='#477b38',lw=3)
    sec.fill_between([4.09,9.09],[4.12,.4],[-.3,-.3],color=C['garden'])
    sec.plot([9.03,9.03],[.4,1.5],color='#495662',lw=2)
    sec.plot([10.8,10.8],[.4,4.7],color='#d9aa00',lw=3)
    sec.text(6.5,2.8,'Grass slope: 5 m',fontsize=10,ha='center');sec.text(9.5,1.9,'Grate',fontsize=9)
    sec.set(xlim=(2.4,11.5),ylim=(-.4,5),xlabel='North / m →',ylabel='Elevation / m',title='Road-to-facade section away from UP stair');sec.grid(alpha=.15)
    fig.text(.72,.55,'Implemented fitted dimensions\nRoom depth: 13.4 m\nRoom corridor: 2.6 m\nTerrace width: 1.71 m\nGrass width: 5 m\nPavement: 1.4 m\nRoad: 6 m\nGarden: 17.5 × 11.25 m\n\nBush starts 5 m beyond\nUP stair right edge.\n\nDOWN remains eastward,\nalong wall below road.\n\nExternal bridge retained',fontsize=10,linespacing=1.6)
    fig.suptitle('POVO 2 — IMPLEMENTED EXTERIOR CONNECTION AND LANDSCAPE',fontsize=15,y=.975)
    foot(fig,'Same orientation as page 1. Plan footprints derive from registered assembly; section uses local road/pavement height at the UP stair.\nTopology confirmed by user; dimensions fitted, not surveyed. Final export stage implemented; no native CS2 compilation or in-game validation claimed.')
    pdf.savefig(fig);fig.savefig(OUT/'final_implemented_exterior.png',dpi=150);plt.close(fig)
print(OUT/'final_implemented_layout.pdf')
