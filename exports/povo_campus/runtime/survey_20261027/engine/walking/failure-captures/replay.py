import json
from pathlib import Path
from tools import playtest_povo_survey as s
out=Path('build/gameplay/survey-20261027/failure-captures');out.mkdir(parents=True,exist_ok=True)
m=json.loads(Path('exports/povo_campus/provenance.json').read_text());by={r['name']:r for r in s.build_routes(m)}
routes=[by[n] for n in ['p2_upper_module0_down_return','amenity_canteen_stair0_up','amenity_canteen_stair0_up_return']]
path=json.loads((Path(__file__).resolve().parent.parent/'planned-detours.json').read_text())['basement']
for suffix,points in [('',path),('_return',list(reversed(path)))]:
 routes.append(dict(name='basement_source_planned_detour'+suffix,kind='walk',category='p2_basement_route',path=points,xy_tolerance=.025,timings=dict(broad_pulse_min=.012,broad_pulse_max=.25)))
class Driver(s.Driver):
 def execute(self,r):
  try:return super().execute(r)
  except s.GuardError:raise
  except Exception:
   self.console.command(['-forward 42','-sprint 42'],.3)
   self.console.command('png_screenshot resume_'+r['name'],.8)
   raise
report=dict(status='failed',routes=[],planned_routes=len(routes),route_plan=routes,package_sha256=s.hashlib.sha256(Path('build/package/trento_povo_campus.vpk').read_bytes()).hexdigest(),started_at_utc=s.datetime.now(s.timezone.utc).isoformat())
c=s.Console(27400);d=Driver(c,'trento_povo_campus')
try:s.run_routes(d,routes,report,out)
finally:
 d.cleanup();report['finished_at_utc']=s.datetime.now(s.timezone.utc).isoformat();(out/'survey-runtime.json').write_text(json.dumps(report,indent=2));(out/'survey-runtime.log').write_text('\n'.join(c.transcript));c.close()
