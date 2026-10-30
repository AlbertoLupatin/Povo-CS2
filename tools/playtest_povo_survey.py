"""Guarded native survey walkthrough; no game launch or map reload.

Use --list-routes for source-only inspection. Runtime requires the operator to
load a fresh standard map, one human and zero bots. Each route uses one initial
placement; every subsequent point is reached by ordinary movement.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import socket
import time

try:
    from .cs2_campus import UNITS, world
    from .cs2_explore import campus_loaded
except ImportError:
    from cs2_campus import UNITS, world
    from cs2_explore import campus_loaded

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_TIMINGS=dict(position_read=.10,guard_read=.35,stop_read=.04,placement_settle=.5,
                     broad_pulse_max=.45,narrow_pulse_max=.25,broad_pulse_min=.04,narrow_pulse_min=.035)
PACKAGE_SHA256='e08a52bbf22d4b9e668d88cd5becbb8375f34831393fb1996dc59073332af3c4'


def simplify_path(points):
    """Remove only collinear interior points; keep every landing and turn.

    Three-dimensional direction changes also preserve starts/ends of a flight,
    so targets keep their true tread/landing elevations.
    """
    result=[]
    for p in points:
        p=list(map(float,p))
        if result and math.dist(result[-1],p)<1e-6:continue
        while len(result)>1:
            a,b=result[-2:];u=[b[i]-a[i] for i in range(3)];v=[p[i]-b[i] for i in range(3)]
            cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            if math.sqrt(sum(x*x for x in cross))>1e-6*max(1,math.dist(a,b)*math.dist(b,p)) or sum(u[i]*v[i] for i in range(3))<=0:break
            result.pop()
        result.append(p)
    return result


def door_point(room):
    a,b,c,d=room['footprint_local_metres'];f=room['door_fraction']
    return {'u_min':([a+(c-a)*f,b],[0,-1]),'u_max':([a+(c-a)*f,d],[0,1]),
            'v_min':([a,b+(d-b)*f],[-1,0]),'v_max':([c,b+(d-b)*f],[1,0])}[room['door_side']]


def build_routes(metadata):
    routes=[]
    def add(name,points,category,*,reverse=True):
        points=simplify_path(points)
        if category in ('p2_upper_stair','p2_lower_stair'):
            # Check the full landings, rather than stopping a standing hull
            # over the final tread and incorrectly calling it a floor-height failure.
            floor=points[-1][2];landing_x=points[0][0]
            body=[p for p in points[2:-1] if abs(p[2]-floor)>1e-6]
            exits=[p for p in points[1:] if abs(p[2]-floor)<1e-6 and abs(p[0]-landing_x)<1e-6]
            points=[points[0],[landing_x,points[1][1],points[0][2]],
                    *body,[landing_x,body[-1][1],floor],*exits]
        if len(points)<2:raise ValueError('Route needs two distinct points: '+name)
        tolerance=.025 if category=='p2_basement_route' else .06 if category=='p1_courtyard_stair' else .15
        options=dict(xy_tolerance=tolerance)
        if category=='p2_basement_route':options['timings']=dict(broad_pulse_min=.012,broad_pulse_max=.25)
        routes.append(dict(name=name,kind='walk',category=category,path=points,**options))
        if reverse:routes.append(dict(name=name+'_return',kind='walk',category=category,path=list(reversed(points)),**options))
    levels=metadata['levels'];origin=metadata['origin'][2]
    for n,segment in enumerate(metadata['stair']['segments']):
        for core in segment['cores']:
            lower,upper=core['enclosure']['portals'][:2]
            sign=-1 if not core['mirror_east'] else 1
            def portal_points(portal):
                x,y,z=portal['centre']
                return [[x+sign*.65,y,z],[x-sign*.65,y,z]]
            low=portal_points(lower);high=portal_points(upper)
            add(f'p1_{core["id"]}_segment{n}_up',[*low,*core['path'],*reversed(high)],'p1_corner_stair')
    for n,segment in enumerate(metadata['stair']['courtyard']['segments']):
        add(f'p1_courtyard_segment{n}_up',segment['path'],'p1_courtyard_stair')
    link=metadata['connection'];stair=link['stair']
    # The combined path contains both upper modules and their actual connecting
    # floor landing. Split at the consecutive module-boundary points, not at
    # a guessed 3.6m overall rise or obsolete x coordinates.
    combined=[stair['top'],*stair['path'],stair['bottom']]
    lower=stair['bottom'][2];height=stair['module_height']
    for module in range(stair['modules']):
        top=lower+(module+1)*height;bottom=lower+module*height
        start=max(i for i,p in enumerate(combined) if abs(p[2]-top)<1e-6)
        end=max(i for i,p in enumerate(combined) if abs(p[2]-bottom)<1e-6)
        points=combined[start:end+1]
        add(f'p2_upper_module{module}_down',points,'p2_upper_stair')
    for path in metadata['povo2']['stairs']['path']:
        add(f'p2_to_floor{path["lower_floor"]}_down',path['points'],'p2_lower_stair')
    z=max(l['floor_elevation_metres'] for l in levels)-origin
    bridge_points=[[s['point'][0],s['point'][1],z] for s in link['audit_stations'] if re.fullmatch(r'link_[0-7]',s['id'])]
    add('p1_p2_bridge',bridge_points,'bridge')
    ground=next(l for l in levels if l['user_floor']==-1);zg=ground['floor_elevation_metres']-origin
    room=next(r for r in ground['rooms'] if r['id']=='acquario');a,b,c,d=room['footprint_local_metres'];p,normal=door_point(room)
    outside=[p[i]+normal[i]*.75 for i in range(2)];inside=[p[i]-normal[i]*.65 for i in range(2)]
    add('acquario_door_and_long_aisle',[[*outside,zg],[*inside,zg],[(a+c)/2,inside[1],zg],[(a+c)/2,b+1,zg],[(a+c)/2,d-1,zg]],'study')
    room=next(r for r in ground['rooms'] if r['id']=='a103');a,b,c,d=room['footprint_local_metres'];p,normal=door_point(room)
    for n,aisle in enumerate(room['fitout']['audit_points_local_metres']):
        # Metadata owns aisle X. Photo4's teaching front is south; target stops
        # behind its low platform and clear of the first desk.
        add(f'a103_side_aisle{n}',[[p[0]+normal[0]*.75,p[1]+normal[1]*.75,zg],
            [p[0]-normal[0]*.75,p[1]-normal[1]*.75,zg],[aisle[0],d-.75,zg],
            [aisle[0],b+1.9,zg]],'classroom')
    for n,st in enumerate(metadata.get('wings',{}).get('stairs',[])):
        add(f'amenity_{st["building"]}_stair{n}_up',[st['bottom'],*st['path'],st['top']],'amenity_stair')
    for level in metadata.get('wings',{}).get('levels',[]):
        if level['floor']!=0:continue
        stations={s['id']:s['point'] for s in level['audit_stations']}
        names=(['porch_outer','porch_turn','porch_inner','entrance','stair_approach'] if level['building']=='canteen'
               else ['povo1_side_approach','entrance','west_corridor_middle','west_corridor_north','stairs_bottom'])
        points=[[*stations[n],level['z']] for n in names if n in stations]
        if level['building']=='library':
            # Native-verified route around the provisionally registered recess
            # and office partitions; the old west-side straight line crossed them.
            points=[[ *stations['povo1_side_approach'],level['z']],
                    [*stations['entrance'],level['z']],
                    *[[x,y,level['z']] for x,y in ((37.5,-55),(40.3,-55),(40.3,-52.3),
                       (42.3,-52.3),(42.3,-34.5),(43,-34.5),(43,-22),(38,-22),(38,-19))],
                    [*stations['stairs_bottom'],level['z']]]
        add('amenity_'+level['building']+'_entry',points,'amenity_entry')
    basement=metadata['povo2']['basement']
    corridor=basement['corridor'];branch=basement['cross_corridor']
    zbase=next(l['z'] for l in metadata['povo2']['levels'] if l['floor']==-1) 
    # Follow the actual registered horizontal corridor then its right-angle
    # return. Its source transform is already baked into these rectangles.
    y=(corridor[1]+corridor[3])/2
    x=metadata['povo2'].get('minus1_corrections',{}).get('spine_route_x',(branch[0]+branch[2])/2)
    start_x=corridor[2]-1
    # The moved lift and stair enclosure occupy the middle of the straight
    # route. Turn south again before crossing the CIBIO corridor's north wall.
    core=metadata['povo2']['stairs']['bounds'];lift=metadata['povo2']['lift']['shaft']
    west=metadata['povo2'].get('west_offices')
    if west:
        detour=west['connection_route']
        link=metadata['povo2'].get('walkthrough_repairs',{}).get('c7_exit_link')
        if link:
            # Through C7's east door, which sits midway along the link.
            door_y=next(d['pivot'][1] for d in metadata['povo2']['repair_doors'] if d['id']=='p2_c7_exit_0')
            link_y=door_y+(next(d['pivot'][1] for d in metadata['povo2']['repair_doors'] if d['id']=='p2_c7_exit_1')-door_y)/2
            approach=[[start_x,y,zbase],[start_x,link_y,zbase],[19.2,link_y,zbase]]
        else:approach=[[start_x,y,zbase],[lift[2]+.8,y,zbase],[lift[2]+.8,17.15,zbase]]
        add('p2_basement_rotated_corridor',[*approach,*detour,[x,branch[3]-1,zbase]],'p2_basement_route')
    else:
        add('p2_basement_rotated_corridor',[[start_x,y,zbase],[lift[2]+.8,y,zbase],
            [lift[2]+.8,17.15,zbase],[core[0]+.7,17.15,zbase],
            [core[0]+.7,16.85,zbase],[x,16.85,zbase],[x,branch[3]-1,zbase]],'p2_basement_route')
    for route in metadata['povo2'].get('basement_rebuild',{}).get('routes',[]):
        add('p2_rebuilt_'+route['id'],route['points'],'p2_basement_route')
    for i,route in enumerate(metadata['povo2']['parking'].get('routes',[])):
        add('p2_rebuilt_vestibule_'+str(i),route['points'],'p2_basement_route')
    for name,spec in [('p1',metadata['elevator']),('p2',metadata['povo2']['lift'])]:
        if not spec.get('enabled',True):continue
        lo,hi=spec['ladder'];axis=min(range(2),key=lambda i:hi[i]-lo[i]);start=[(a+b)/2 for a,b in zip(lo,hi)]
        start[axis]=hi[axis]+.4072;start[2]=lo[2]
        dismount=list(start);dismount[2]=z
        if name=='p1':dismount[:2]=spec['stations']['first']
        else:dismount[axis]=metadata['povo2']['lift']['shaft'][axis]+1.55
        routes.append(dict(name=name+'_lift_climb_and_dismount',kind='ladder',category='lift',start=start,
                           ladder=spec['ladder'],axis=axis,target_floor=z,dismount=dismount))
    names=[r['name'] for r in routes]
    if len(names)!=len(set(names)):raise ValueError('Duplicate route names')
    return routes


class Console:
    """Persistent netconsole permits short, stopped walking pulses.

    cs2_console.run has a 200ms minimum read. That is too long to aim a standing
    hull through a 0.96m stair flight. This transport sends -forward immediately
    after the requested ordinary-walking pulse, then gathers its response.
    """
    def __init__(self,port):
        self.socket=socket.create_connection(('127.0.0.1',port),timeout=5)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.stop_read=DEFAULT_TIMINGS['stop_read']
        self.transcript=[]
    def _read(self,seconds):
        end=time.monotonic()+seconds;chunks=[]
        while time.monotonic()<end:
            self.socket.settimeout(max(.001,min(.025,end-time.monotonic())))
            try:data=self.socket.recv(65536)
            except socket.timeout:continue
            if not data:raise OSError('CS2 netconsole closed')
            chunks.append(data)
        text=b''.join(chunks).decode('utf-8',errors='replace');self.transcript.append(text);return text
    def send(self,commands):
        if isinstance(commands,str):commands=[commands]
        self.transcript.append('> '+'\n> '.join(commands));self.socket.sendall(('\n'.join(commands)+'\n').encode())
    def command(self,commands,seconds=.25):self.send(commands);return self._read(seconds)
    def pulse(self,commands,seconds):
        self.send(commands)
        try:return self._read(seconds)
        finally:self.send('-forward 42');self._read(self.stop_read)
    def close(self):self.socket.close()


def waypoint_height_tolerance(route,index):
    """Standing hull may contact either of the next two 18cm stair risers.

    Only intermediate stair elevations receive that envelope. Both terminal
    floor elevations, all door/hall points on them and every non-stair route
    remain strict; the native standing hull is not a point at a tread centre.
    """
    path=route['path'];target=path[index]
    floors=(path[0][2],path[-1][2])
    stair=route.get('category') in ('p1_corner_stair','p1_courtyard_stair','p2_upper_stair','p2_lower_stair','amenity_stair')
    if stair and index not in (0,len(path)-1) and not any(abs(target[2]-z)<1e-6 for z in floors):return .42
    return .25


class GuardError(RuntimeError):
    pass


class Driver:
    def __init__(self,console,map_name,*,timings=None):
        self.console=console;self.map_name=map_name;self.checks=[];self.authorized=False
        self.base_timings={**DEFAULT_TIMINGS,**(timings or {})};self.timings=dict(self.base_timings)
    def guard(self):
        self.authorized=False
        text=self.console.command('status',self.timings['guard_read'])
        if not campus_loaded(text,self.map_name) or not re.search(r'players\s*:\s*1 humans, 0 bots\b',text):
            raise GuardError('Requires expected campus map, exactly one human and zero bots')
        self.authorized=True
        return text
    def position(self):
        response=self.console.command('getpos_exact',self.timings['position_read'])
        matches=re.findall(r'setpos_exact ([-\d.]+) ([-\d.]+) ([-\d.]+)',response)
        if not matches:raise RuntimeError('Player position unavailable')
        x,y,z=map(float,matches[-1]);return [y/UNITS,-x/UNITS,z/UNITS]
    def place(self,p):
        p=list(p);p[2]+=.10
        self.console.command(['-forward 42','-sprint 42','sv_cheats 1','god 1','noclip 0','slot3','gameui_hide','setpos '+world(p)],self.timings['placement_settle'])
        actual=self.position()
        if math.dist(actual[:2],p[:2])>.3 or abs(actual[2]-(p[2]-.1))>.25:raise RuntimeError('Starting placement did not settle on intended floor: '+str(actual))
    def walk(self,target,*,height_tolerance=.25,xy_tolerance=.15):
        p=self.position();distance=math.dist(p[:2],target[:2]);deadline=time.monotonic()+distance/1.5+10
        previous=distance;stalled=0
        while time.monotonic()<deadline:
            dx=target[0]-p[0];dy=target[1]-p[1];distance=math.hypot(dx,dy)
            if distance<xy_tolerance:
                ok=abs(p[2]-target[2])<height_tolerance
                self.checks.append(dict(target=target,position=p,passed=ok,height_tolerance=height_tolerance))
                if not ok:raise RuntimeError('Unexpected floor height: '+str(p)+' target '+str(target))
                return p
            yaw=math.degrees(math.atan2(dx,-dy))
            narrow=xy_tolerance<.1
            maximum=self.timings['narrow_pulse_max' if narrow else 'broad_pulse_max']
            minimum=self.timings['narrow_pulse_min' if narrow else 'broad_pulse_min']
            # Broad straight approaches use longer pulses. Narrow courtyard
            # turns retain the shorter cap and their unchanged6cm tolerance.
            duration=min(maximum,max(minimum,(distance-.03)/3.3))
            self.console.pulse([f'setang 0 {yaw:.3f} 0','+sprint 42','+forward 42'],duration)
            stalled=stalled+1 if abs(previous-distance)<.015 else 0;previous=distance
            p=self.position()
            if stalled>=10:break
        raise RuntimeError('Ordinary movement stalled: '+str(self.position())+' target '+str(target))
    def execute(self,route):
        self.timings={**self.base_timings,**route.get('timings',{})}
        self.console.stop_read=self.timings['stop_read']
        self.checks=[];self.guard()
        if route['kind']=='walk':
            self.place(route['path'][0])
            for index,point in enumerate(route['path'][1:],1):
                self.walk(point,xy_tolerance=route.get('xy_tolerance',.15),height_tolerance=waypoint_height_tolerance(route,index))
        else:
            self.place(route['start']);axis=route['axis'];yaw=-90 if axis==0 else 0
            top=route['target_floor'];reached=False
            self.console.command('-sprint 42')
            for _ in range(80):
                self.console.pulse([f'setang -55 {yaw} 0','+forward 42'],.2)
                p=self.position()
                if p[2]>top+.65:reached=True;break
                if p[2]<route['start'][2]-.4:raise RuntimeError('Fell from lift ladder')
            self.checks.append(dict(kind='ladder_climb',target_floor=top,position=p,passed=reached))
            if not reached:raise RuntimeError('Ladder did not reach above current upper floor')
            # Native jump detaches from the ladder before moving onto the ledge.
            self.console.pulse([f'setang 0 {yaw} 0','+jump 42'],.12)
            self.console.command('-jump 42',.05)
            self.walk(route['dismount'],height_tolerance=.25)
        return list(self.checks)
    def cleanup(self):
        if self.authorized:return self.console.command(['-forward 42','-sprint 42','-jump 42','-jump','-attack','noclip 0'])


def run_routes(driver,routes,report,output):
    """Persist every route independently; a physical failure does not abort others."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for route_index,route in enumerate(routes):
        guard_failed=False
        result=dict(name=route['name'],kind=route['kind'],status='failed',checks=[])
        try:
            result['checks']=driver.execute(route);result['status']='passed'
        except GuardError as error:
            guard_failed=True;result['error']=str(error);result['status']='blocked'
        except Exception as error:
            result['error']=str(error);result['checks']=list(driver.checks)
        finally:
            try:driver.cleanup()
            except Exception as error:result['cleanup_error']=str(error);result['status']='failed'
        report['routes'].append(result)
        (output/(route['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        (output/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        print(route['name'],result['status'],result.get('error',''),flush=True)
        if guard_failed:
            report['routes'].extend(dict(name=r['name'],kind=r['kind'],status='not_run',checks=[],error='Session guard rejected before this route') for r in routes[route_index+1:])
            break
    report['status']='passed' if len(report['routes'])==len(routes) and all(r['status']=='passed' for r in report['routes']) else 'failed'
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata',type=Path,default=ROOT/'exports/povo_campus/provenance.json')
    parser.add_argument('--package',type=Path,default=ROOT/'build/package/trento_povo_campus.vpk')
    parser.add_argument('--output',type=Path,default=ROOT/'build/gameplay/survey-20261027')
    parser.add_argument('--expected-package-sha256',default=PACKAGE_SHA256)
    parser.add_argument('--map',dest='map_name',default='trento_povo_campus')
    parser.add_argument('--port',type=int,default=27400)
    parser.add_argument('--routes',help='Regular expression selecting route names')
    parser.add_argument('--position-read',type=float,default=DEFAULT_TIMINGS['position_read'])
    parser.add_argument('--pulse-max',type=float,default=DEFAULT_TIMINGS['broad_pulse_max'])
    parser.add_argument('--narrow-pulse-max',type=float,default=DEFAULT_TIMINGS['narrow_pulse_max'])
    parser.add_argument('--pulse-min',type=float,default=DEFAULT_TIMINGS['broad_pulse_min'])
    parser.add_argument('--narrow-pulse-min',type=float,default=DEFAULT_TIMINGS['narrow_pulse_min'])
    parser.add_argument('--stop-read',type=float,default=DEFAULT_TIMINGS['stop_read'])
    parser.add_argument('--list-routes',action='store_true',help='Source-only route listing; never connects to CS2')
    args=parser.parse_args(argv)
    timings=dict(position_read=args.position_read,broad_pulse_max=args.pulse_max,narrow_pulse_max=args.narrow_pulse_max,
                 broad_pulse_min=args.pulse_min,narrow_pulse_min=args.narrow_pulse_min,stop_read=args.stop_read)
    if any(not math.isfinite(v) or v<=0 for v in timings.values()):parser.error('Timings must be finite and positive')
    if args.pulse_min>args.pulse_max or args.narrow_pulse_min>args.narrow_pulse_max:parser.error('Pulse minimum must not exceed maximum')
    metadata=json.loads(args.metadata.read_text());routes=build_routes(metadata)
    if args.routes:routes=[r for r in routes if re.search(args.routes,r['name'])]
    if not routes:parser.error('No routes selected')
    if args.list_routes:
        print(json.dumps(routes,indent=2));return 0
    package_hash=hashlib.sha256(args.package.read_bytes()).hexdigest()
    if package_hash!=args.expected_package_sha256:raise RuntimeError('On-disk package SHA256 does not match expected tested package')
    report=dict(status='failed',started_at_utc=datetime.now(timezone.utc).isoformat(),routes=[],planned_routes=len(routes),
        package_on_disk=str(args.package.resolve()),package_sha256=package_hash,package_bytes=args.package.stat().st_size,
        metadata_sha256=hashlib.sha256(args.metadata.read_bytes()).hexdigest(),map_name=args.map_name,
        package_identity_scope='On-disk bytes verified; native status confirms loaded map name, not loaded VPK bytes',
        fresh_map_scope='Operator must load a fresh map before running; status checks map name and one human/zero bots',
        movement='One initial placement per route; ordinary walking/climbing with jump-assisted ladder dismounts; noclip0 enforced at placement/cleanup',
        route_plan=routes,controller_timings={**DEFAULT_TIMINGS,**timings})
    args.output.mkdir(parents=True,exist_ok=True);console=None;driver=None
    try:
        console=Console(args.port);driver=Driver(console,args.map_name,timings=timings)
        report['initial_status']=driver.guard();report['loaded_map_name']=args.map_name;run_routes(driver,routes,report,args.output)
    except BaseException as error:
        report['error']=str(error);report['status']='failed'
    finally:
        if driver:
            try:driver.cleanup()
            except Exception as error:report['cleanup_error']=str(error);report['status']='failed'
        recorded={r['name'] for r in report['routes']}
        report['routes'].extend(dict(name=r['name'],kind=r['kind'],status='not_run',checks=[],error='Run interrupted before route completed') for r in routes if r['name'] not in recorded)
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        (args.output/'survey-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
        if console:
            (args.output/'survey-runtime.log').write_text('\n'.join(console.transcript))
            console.close()
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
