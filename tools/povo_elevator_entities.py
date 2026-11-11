"""Native CS2 lift controls using tracktrain arrival and door-state interlocks.

Entity/keyvalue references checked against the CS2 2026-11-05 FGD reference:
https://cs2opendev.github.io/CS2OpenDev-Docs/entities/func_tracktrain/
Door closing is never inferred from a timer. A listener observes every landing
and cabin leaf. Arrival is OnArrivedAtDestinationNode, not a travel-time guess.
"""
from .povo_elevators import PREFIX


def entity_graph(banks):
    """Return a serializable graph, shared by VMAP emission and behavioral tests."""
    entities=[]
    def entity(name,cls,origin,props=None,parts=None,outputs=None,angles='0 0 0'):
        e=dict(name=name,classname=cls,origin=origin,properties=props or {},parts=parts or [],
               outputs=outputs or [],angles=angles)
        entities.append(e);return e
    def edge(e,out,target,inp,param='',delay=0):
        e['outputs'].append(dict(output=out,target=target,input=inp,param=str(param),delay=delay))
    def parts(boxes):return [(b[1],b[2],PREFIX+b[3]+'.vmat') for b in boxes]
    for bank in banks:
        for car in bank['cars']:
            cid=car['id'];origin=car['origin'];stops=car['stops'];n=len(stops)
            train=entity(cid,'func_tracktrain',origin,dict(target=cid+'_path0',startspeed='40',speed='0',
                spawnflags='18',height='0',wheels='0',orientationtype='0',velocitytype='0',dmg='0'),parts(car['parts']))
            edge(train,'OnArrivedAtDestinationNode',cid+'_arrival_value','GetValue')
            lamp=[*origin[:2],origin[2]+2.3]
            entity(cid+'_ceiling_light','light_omni2',lamp,dict(parentname=cid,enabled='1',
                directlight='1',brightness_units='1',brightness_lumens='1200',
                color='240 246 255',colormode='0',range='430',bouncelight='0',
                shape='0',size_params='6 24 0.15'))
            # Separate polled values prevent a drive query from opening doors.
            for kind in ('drive','arrival'):
                counter=entity(cid+'_'+kind+'_value','math_counter',origin,dict(startvalue='0',min='0',max=str(n-1)))
                case=entity(cid+'_'+kind+'_case','logic_case',origin,{f'Case{i+1:02}':str(i) for i in range(n)})
                edge(counter,'OnGetValue',case['name'],'InValue')
                for i in range(n):
                    if kind=='drive':edge(case,f'OnCase{i+1:02}',cid,'MoveToPathNode',cid+f'_path{i}')
                    else:edge(case,f'OnCase{i+1:02}',cid+f'_arrive{i}','Trigger')
            depart=entity(cid+'_depart','logic_relay',origin,dict(StartDisabled='1'))
            edge(depart,'OnTrigger',cid+'_depart','Disable')
            edge(depart,'OnTrigger',cid+'_retry','Disable')
            edge(depart,'OnTrigger',cid+'_drive_value','GetValue',delay=.01)
            listener=entity(cid+'_interlock','logic_branch_listener',origin,dict(Branch01=cid+'_closed_*'))
            edge(listener,'OnAllTrue',cid+'_depart','Trigger')
            retry=entity(cid+'_retry','logic_timer',origin,dict(StartDisabled='1',RefireTime='1.5'))
            for gate in car['gates']:edge(retry,'OnTimer',gate['name'],'Close')
            # Only pressed controls issue requests; touch/shoot cannot open gates.
            for gate_index,gate in enumerate(car['gates']):
                props=dict(speed='45',wait='-1',spawnflags='32',lip='-2',dmg='0',forceclosed='0',
                    movedir='0 0 0' if gate['leaf']==0 else '0 180 0')
                if gate['parent']:props['parentname']=gate['parent']
                g=entity(gate['name'],'func_door',origin,props,parts([gate['box']]))
                state=entity(cid+f'_closed_{gate_index}','logic_branch',origin,dict(InitialValue='1'))
                edge(g,'OnOpen',state['name'],'SetValueTest',0)
                edge(g,'OnFullyClosed',state['name'],'SetValueTest',1)
                # An obstructed leaf reopens its pair and the cabin pair; retry
                # later closes them. No other floor's landing gate is opened.
                for other in car['gates']:
                    if other['parent'] or other['stop']==gate['stop']:
                        edge(g,'OnBlockedClosing',other['name'],'Open')
            init=entity(cid+'_init','logic_auto',origin)
            edge(init,'OnMapSpawn',cid+f'_arrive0','Trigger',delay=.25)
            for i,stop in enumerate(stops):
                pt=list(origin);pt[2]=stop['z']
                props={} if i==n-1 else dict(target=cid+f'_path{i+1}')
                entity(cid+f'_path{i}','path_track',pt,props)
                call=entity(cid+f'_call{i}','logic_relay',origin)
                edge(call,'OnTrigger',cid+f'_at{i}','Test')
                at=entity(cid+f'_at{i}','logic_branch',origin,dict(InitialValue='1' if i==0 else '0'))
                edge(at,'OnTrue',cid+f'_open{i}','Trigger')
                edge(at,'OnFalse',cid+f'_request{i}','Trigger')
                request=entity(cid+f'_request{i}','logic_relay',origin)
                for j in range(n):
                    edge(request,'OnTrigger',cid+f'_call{j}','Disable')
                    edge(request,'OnTrigger',cid+f'_request{j}','Disable')
                for kind in ('drive','arrival'):edge(request,'OnTrigger',cid+'_'+kind+'_value','SetValueNoFire',i)
                edge(request,'OnTrigger',cid+'_depart','Enable')
                for gate in car['gates']:edge(request,'OnTrigger',gate['name'],'Close')
                edge(request,'OnTrigger',cid+'_retry','Enable')
                edge(request,'OnTrigger',cid+'_interlock','Test',delay=.1)
                arrive=entity(cid+f'_arrive{i}','logic_relay',origin)
                for j in range(n):
                    edge(arrive,'OnTrigger',cid+f'_at{j}','SetValue',int(j==i))
                    edge(arrive,'OnTrigger',cid+f'_call{j}','Enable',delay=.6)
                    edge(arrive,'OnTrigger',cid+f'_request{j}','Enable',delay=.6)
                opening=entity(cid+f'_open{i}','logic_relay',origin)
                edge(arrive,'OnTrigger',opening['name'],'Trigger')
                for gate in car['gates']:
                    if gate['parent'] or gate['stop']==i:edge(opening,'OnTrigger',gate['name'],'Open')
                for ind in car['indicators']:edge(arrive,'OnTrigger',ind['name'],'SetMessage',stop['floor'])
            for button in car['buttons']:
                props=dict(spawnflags='1025',wait='.25',speed='5')
                if button['parent']:props['parentname']=button['parent']
                but=entity(button['name'],'func_button',origin,props,parts([button['box']]))
                edge(but,'OnPressed',cid+f'_call{button["stop"]}','Trigger')
                if button['parent']:
                    lo,hi=button['box'][1:3];e=(lo[0]+hi[0])/2
                    # Text sits on the cabin-facing button surface.
                    e=hi[0]+.003 if bank['front']=='west' else lo[0]-.003
                    entity(button['name']+'_label','point_worldtext',[e,(lo[1]+hi[1])/2,hi[2]+.025],
                        dict(parentname=cid,message=str(stops[button['stop']]['floor']),enabled='1',
                             fontname='Arial',fontsize='12',world_units_per_px='.12',color='230 230 220 255',
                             fullbright='1',justifyhorizontal='1',justifyvertical='1'),
                        angles='0 180 90' if bank['front']=='west' else '0 0 90')
            for ind in car['indicators']:
                entity(ind['name'],'point_worldtext',ind['origin'],dict(message=str(stops[0]['floor']),enabled='1',
                    fontname='Arial',fontsize='20',world_units_per_px='.14',color='255 28 12 255',
                    fullbright='1',justifyhorizontal='1',justifyvertical='1'),
                    angles='0 180 90' if bank['front']=='east' else '0 0 90')
    return entities


def insert_entities(source,banks):
    from . import cs2_project as project
    from .povo_interactions import brush_entity, with_outputs
    from .cs2_campus import connection, world
    graph=entity_graph(banks)
    for e in graph:
        props=[('targetname',e['name']),*[(k,str(v)) for k,v in e['properties'].items()]]
        if e['parts']:
            pivot=e['origin'] if e['classname']=='func_tracktrain' else None
            source=brush_entity(source,'native-'+e['name'],e['classname'],e['parts'],props,pivot)
        else:
            source=project._insert_point_entity(source,'native-'+e['name'],e['classname'],world(e['origin']),props,angles=e['angles'])
    for e in graph:
        if not e['outputs']:continue
        rows=[]
        for i,out in enumerate(e['outputs']):
            row=connection(e['name']+'-'+str(i),out['output'],out['target'],out['input'])
            row=row.replace('"overrideParam" "string" ""','"overrideParam" "string" "'+out['param']+'"')
            row=row.replace('"delay" "float" "0"',f'"delay" "float" "{out["delay"]}"')
            rows.append(row)
        source=with_outputs(source,e['name'],rows)
    return source
