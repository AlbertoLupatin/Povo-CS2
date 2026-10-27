"""Editable, simplified floor-plan diagrams derived from the corrected source."""
import xml.etree.ElementTree as ET
from pathlib import Path
try:
    from .build_povo_campus import build_geometry
except ImportError:
    from build_povo_campus import build_geometry

ROOT=Path(__file__).resolve().parents[1]


def export():
    _,_,boxes,levels,_=build_geometry();p2=levels[1]['connection']['povo2']
    doc=ET.Element('mxfile',host='app.diagrams.net');count=0
    def page(name,bounds):
        nonlocal count
        diagram=ET.SubElement(doc,'diagram',name=name,id='p'+str(len(doc)))
        model=ET.SubElement(diagram,'mxGraphModel',grid='1',gridSize='10',page='1',
                            pageWidth='1100',pageHeight='1400',pageScale='1',math='0',shadow='0')
        root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
        a,_,_,d=bounds;scale=10
        def rectangle(r,label='',fill='#eeeeee',stroke='#566573'):
            nonlocal count
            count+=1
            cell=ET.SubElement(root,'mxCell',id=str(count+1),parent='1',vertex='1',value=label,
                style=f'rounded=0;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};fontSize=12;')
            ET.SubElement(cell,'mxGeometry',x=str(50+(r[0]-a)*scale),y=str(90+(d-r[3])*scale),
                          width=str((r[2]-r[0])*scale),height=str((r[3]-r[1])*scale),**{'as':'geometry'})
        def note(label,x,y):
            rectangle((x,y-2,x+35,y),label,'none','none')
        note(name+' | North up | schematic metres',a,d+5)
        note('Rooms, corridors and furniture remain editable. Dimensions are estimates.',a,d+2.5)
        return rectangle,note

    ground=next(l for l in p2['levels'] if l['floor']==0);cfg=p2['additions']['config']
    rect,note=page('Povo 2 — ground',(0,0,62,98))
    # Use surviving floor pieces, so the removed classroom-side strip is absent.
    for n,lo,hi,m in boxes:
        if n.startswith(('p2_ground_slab','p2_ground_left_approach_floor','p2_ground_left_extension_floor','p2_ground_stair_hall_floor')) and abs(hi[2]-4)<.02:
            rect([*lo[:2],*hi[:2]],fill='#f3f4f4',stroke='none')
    for r in ground['rooms']:rect(r['bounds'],r['label'],'#fff2cc')
    rect(cfg['aula_lobby'],'Aula lobby','#dae8fc');rect(cfg['aula_magna'],'AULA MAGNA\nSeats face WEST','#fff2cc')
    a,b,c,d=cfg['aula_magna'];rect((a+.2,b+8,a+.5,d-3),'Desk / board','#82b366')
    for r in ground['table_bounds']:rect(r,fill='#d5b88b')
    rect(p2['ground']['reception'],'RECEPTION','#d5e8d4')
    rect(p2['stairs']['bounds'],'STAIRS','#d0d0d0');rect(p2['lift']['shaft'],'Ladder','#b1ddf0')
    rect((20.4,21.175,20.6,22.825),fill='#00a86b',stroke='#00a86b')

    rect,note=page('Povo 2 — basement rotated clockwise',(-16,-28,34,42))
    seen=set()
    for name,r in p2['basement'].items():
        if tuple(r) in seen:continue
        seen.add(tuple(r))
        label=name.replace('_',' ').upper()
        rect(r,label,'#e2efd9' if name=='yard' else '#fff2cc' if 'office' in name else '#dae8fc')
    rect(p2['stairs']['bounds'],'STAIR STACK','#d0d0d0');rect(p2['lift']['shaft'],'Ladder','#b1ddf0')
    x,y,_=p2['basement_placement']['portal']
    rect((x-.825,y-.1,x+.825,y+.1),'SOUTH door','#00a86b','#00a86b')
    # The yard and its exit stair rotate with the rest of this floor.
    path=p2['additions']['yard']['outdoor_path']
    for x,y,_ in path:rect((x-.8,y-.15,x+.8,y+.15),fill='#c0c0c0')

    wings=levels[0]['wings'];wc=wings['config']
    for floor in (0,1):
        rect,note=page('Library and canteen — '+('ground' if floor==0 else 'first'),(28,-114,55,-10))
        for level in wings['levels']:
            if level['floor']!=floor:continue
            rect(level['bounds'],level['building'].upper(),'#f3f4f4')
            for room in level['rooms']:rect(room['bounds'],room['id'].replace('_',' '),'#fff2cc')
        for kind in ('library','canteen'):rect(wc[kind]['stair'],'STAIRS','#d0d0d0')
        z=(4,7.6)[floor]
        for n,lo,hi,m in boxes:
            if n.startswith(('canteen_'+str(floor)+'_','library_'+str(floor)+'_')) and n.endswith('_top') and z<lo[2]<z+1.1:
                rect([*lo[:2],*hi[:2]],fill='#f8ad57' if m=='canteen_orange' else '#d5b88b')
        if floor==0:
            for key,label,fill in [('bar_counter','BAR COUNTER','#f8ad57'),('bar_white_wall','White wall','#ffffff'),
                                   ('serving_counter','Serving counter','#f8ad57'),('porch','Glazed porch','#d9f0f5')]:
                rect(wc['canteen'][key],label,fill)
    output=ROOT/'exports/povo_campus/povo2_layout_editable_20261027.drawio'
    ET.indent(doc);ET.ElementTree(doc).write(output,encoding='utf-8',xml_declaration=True)
    print(output);print(len(doc),'pages;',count,'editable shapes')
    return output


if __name__=='__main__':export()
