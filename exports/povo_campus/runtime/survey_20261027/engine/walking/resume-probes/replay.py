import json
from pathlib import Path
from tools import playtest_povo_survey as s
m=json.loads(Path('exports/povo_campus/provenance.json').read_text());by={r['name']:r for r in s.build_routes(m)}
routes=[]
def add(name,path,category):
 for suffix,points in [('',path),('_return',list(reversed(path)))]:routes.append(dict(name=name+suffix,kind='walk',path=points,category=category,xy_tolerance=.08))
for module in range(2):
 z=7.6+3.6*module;mid=z-1.8;lo=z-3.6
 add(f'p2_module{module}_continuous',[[19.2,20,z],[19.2,19.35,z],[14.5,19.35,mid],[13.15,19.35,mid],[13.15,22.65,mid],[14.5,22.65,mid],[19.2,22.65,lo],[19.2,22,lo]],'p2_upper_stair')
for floor in (-1,-2):
 r=by[f'p2_to_floor{floor}_down'];p=r['path'];add(f'p2_lower{floor}_floor_landings',[p[0],[p[0][0],p[1][1],p[0][2]],*p[2:-2],[p[-1][0],p[-2][1],p[-1][2]],p[-1]],'p2_lower_stair')
add('library_partition_detour',[[32,-61,4],[37.5,-61,4],[37.5,-55,4],[40.3,-55,4],[40.3,-52.3,4],[42.3,-52.3,4],[42.3,-34.5,4],[43,-34.5,4],[43,-22,4],[38,-22,4],[38,-19,4],[37.4,-17.55,4]],'amenity_entry')
add('basement_lift_detour',[[26.2,16.25,.4],[23.8,16.25,.4],[23.8,17.3,.4],[-3.8,17.3,.4],[-3.8,38.5,.4]],'p2_basement_route')
for name in ('p1','p2'):routes.append(by[name+'_lift_climb_and_dismount'])
class Driver(s.Driver):
 def execute(self,route):
  if route['kind']!='ladder':return super().execute(route)
  self.checks=[];self.guard();self.place(route['start']);yaw=-90 if route['axis']==0 else 0;top=route['target_floor']
  self.console.command('-sprint 42')
  for _ in range(100):
   self.console.pulse([f'setang -55 {yaw} 0','+forward 42'],.2);p=self.position()
   if p[2]>top+.65:break
  self.checks.append(dict(kind='ladder_climb',position=p,target_floor=top,passed=p[2]>top+.65))
  if p[2]<=top+.65:raise RuntimeError('Did not reach jump-off height')
  self.console.pulse([f'setang 0 {yaw} 0','+jump 42'],.12);self.console.command('-jump 42',.05)
  self.walk(route['dismount']);return self.checks
out=Path('build/gameplay/survey-20261027/resume-probes');out.mkdir(parents=True,exist_ok=True)
report=dict(status='failed',routes=[],planned_routes=len(routes),route_plan=routes,started_at_utc=s.datetime.now(s.timezone.utc).isoformat(),package_sha256=s.hashlib.sha256(Path('build/package/trento_povo_campus.vpk').read_bytes()).hexdigest(),notes='Diagnostic routes; original sweep retained. Ladder dismount uses ordinary jump to detach, with a 0.65m clearance threshold. No geometry changes.')
c=s.Console(27400);d=Driver(c,'trento_povo_campus')
try:s.run_routes(d,routes,report,out)
finally:
 d.cleanup();report['finished_at_utc']=s.datetime.now(s.timezone.utc).isoformat();(out/'survey-runtime.json').write_text(json.dumps(report,indent=2));(out/'survey-runtime.log').write_text('\n'.join(c.transcript));c.close()
