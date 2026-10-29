import json
from pathlib import Path
from tools import playtest_povo_survey as s
out=Path('build/gameplay/survey-20261027/basement-portals');out.mkdir(parents=True,exist_ok=True)
path=[[26.2,16.25,.4],[23.8,16.25,.4],[23.8,17.15,.4],[11.7,17.15,.4],[11.7,16.85,.4],[-3.8,16.85,.4],[-3.8,38.5,.4]]
routes=[dict(name='basement_portal_detour'+suffix,kind='walk',category='p2_basement_route',path=points,xy_tolerance=.025,timings=dict(broad_pulse_min=.012,broad_pulse_max=.25)) for suffix,points in [('',path),('_return',list(reversed(path)))]]
r=dict(status='failed',routes=[],planned_routes=len(routes),route_plan=routes,started_at_utc=s.datetime.now(s.timezone.utc).isoformat(),package_sha256=s.hashlib.sha256(Path('build/package/trento_povo_campus.vpk').read_bytes()).hexdigest())
c=s.Console(27400);d=s.Driver(c,'trento_povo_campus')
try:s.run_routes(d,routes,r,out)
finally:
 d.cleanup();r['finished_at_utc']=s.datetime.now(s.timezone.utc).isoformat();(out/'survey-runtime.json').write_text(json.dumps(r,indent=2));(out/'survey-runtime.log').write_text('\n'.join(c.transcript));c.close()
