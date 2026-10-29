"""Compile and walk the review terrace in an isolated native CS2 test scene.

The render/collision model imports the committed terrace.obj unchanged. A
separate catch floor at -3.2 is a test fixture, not proposed campus geometry.
The installed campus map/package is never overwritten. Requires CS2 closed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

from tools import cs2_project as project
from tools.cs2_campus import world, box_entity, node_ids
from tools.cs2_console import run
from tools.cs2_explore import SETTINGS
from tools.playtest_povo_survey import Console, Driver, GuardError, run_routes

ROOT = Path(__file__).resolve().parents[1]
MAP = 'povo2_terrace_native_test'
REVIEW = ROOT/'exports/povo2_minus1_terrace_20261029'
OUT = REVIEW/'runtime'


def build_scene(cs2, logs):
    content = cs2/'content/csgo_addons/trento_povo'
    game = cs2/'game/csgo_addons/trento_povo'
    converter = cs2/'game/bin/win64/dmxconvert.exe'
    compiler = cs2/'game/bin/win64/resourcecompiler.exe'
    decoded = logs/'base.vmap.txt'
    subprocess.run([str(converter), '-i', str(content/'maps/trento_povo_campus.vmap'),
                    '-o', str(decoded), '-oe', 'keyvalues2', '-of', 'vmap'], check=True)
    text = decoded.read_text(encoding='utf-8')
    entities = list(project._entity_ranges(text))
    template = next(b for _, _, c, b in entities if c == 'func_buyzone' and '"CMapMesh"' in b)
    keep = {'light_environment', 'env_sky'}
    blocks = [b for _, _, c, b in entities if c in keep]
    start = project._world_children_opening(text)
    end = project._matching_bracket(text, start)
    text = text[:start+1]+'\n'+',\n'.join(blocks)+'\n'+text[end:]
    # Drop the campus asset list as well as its entities: this scene contains
    # only the review model, lighting and the test fixture.
    label = text.index('"map_asset_references" "string_array"')
    a = text.index('[', label); b = project._matching_bracket(text, a)
    text = text[:a+1]+' '+text[b:]
    ids = node_ids(text)
    fixture = box_entity(template, 'terrace-test-catch-floor', 'func_brush',
                         ((-31, -5, -3.45), (47, 113, -3.2)), ids,
                         (('targetname', 'terrace_test_catch_floor'), ('Solidity', '2')),
                         'materials/trento/povo/campus/floor_p2_asphalt.vmat')
    at = project._world_children_opening(text)
    text = text[:at+1]+'\n'+fixture+','+text[at+1:]
    model_path = f'models/povo/{MAP}.vmdl'
    text = project._insert_point_entity(text, 'terrace-test-model', 'prop_static', '0 0 0',
             (('model', model_path), ('solid', '6'), ('lightmapscalebias', '1'),
              ('targetname', 'terrace_review_exact_obj')), angles='-90 0 0')
    for team in ('terrorist', 'counterterrorist'):
        text = project._insert_point_entity(text, 'terrace-test-'+team,
                      'info_player_'+team, world((28, 1.1, .6)))
    text = project._insert_point_entity(text, 'terrace-test-nav', 'point_nav_walkable', world((28, 1.1, .6)))
    text = project._ensure_map_asset_reference(text, model_path)
    decoded = logs/'scene.vmap.txt'; decoded.write_text(text, encoding='utf-8')
    target = content/'maps'/(MAP+'.vmap')
    subprocess.run([str(converter), '-i', str(decoded), '-o', str(target),
                    '-oe', 'binary', '-of', 'vmap'], check=True)
    models = content/'models/povo'; model = models/(MAP+'.vmdl')
    shutil.copyfile(REVIEW/'terrace.obj', models/(MAP+'.obj'))
    definition = (ROOT/'cs2/content/trento_povo/models/povo/povo_blockout.vmdl').read_text(encoding='utf-8')
    definition = definition.replace('povo_blockout_collision.obj', MAP+'.obj').replace('povo_blockout.obj', MAP+'.obj')
    definition = definition.replace('use_global_default = false', 'use_global_default = true')
    definition = definition.replace('global_default_material = ""',
                                    'global_default_material = "materials/trento/povo/campus/floor_terrace.vmat"')
    model.write_text(definition, encoding='utf-8')
    for resource, options in ((model, []), (target, ['-lightmapVRadQuality', '1', '-lightmapMaxResolution', '1024'])):
        print('Compiling', resource, flush=True)
        with (logs/(resource.suffix[1:]+'.log')).open('w', encoding='utf-8') as log:
            subprocess.run([str(compiler), '-nop4', '-fshallow2', *options, '-game',
                            str(cs2/'game/csgo'), '-i', str(resource)], stdout=log, stderr=subprocess.STDOUT, check=True)
    package = game/'maps'/(MAP+'.vpk')
    identity = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (REVIEW/'terrace.obj', models/(MAP+'.obj'),
                             game/'models/povo'/(MAP+'.vmdl_c'), package)}
    (logs/'scene-inputs.json').write_text(json.dumps(identity, indent=2)+'\n', encoding='utf-8')
    return package


class TerraceDriver(Driver):
    def guard(self):
        self.authorized = False
        text = self.console.command('status', .35)
        if (not re.search(r'@ Current\s*:\s*game\b', text)
            or f': {MAP} | main lump | mapload]' not in text
            or not re.search(r'players\s*:\s*1 humans, 0 bots\b', text)):
            raise GuardError('Requires the terrace test scene, one human and zero bots')
        self.authorized = True
        return text


def walking_routes(t):
    routes = []
    def add(name, path):
        for suffix, points in (('', path), ('_return', list(reversed(path)))):
            routes.append(dict(name=name+suffix, kind='walk', category='p2_lower_stair', path=points))
    for st in t['metal_stairs']:
        upper, lower = st['flights']; mid = st['mid_landing']
        y = (upper[1]+upper[3])/2
        run = next(s['bounds'] for s in t['slabs'] if s['id'] == st['run'])
        add(st['id']+'_stair_and_run', [
            [lower[2]+1, y, st['bottom_z']], [lower[2]-.2, y, st['bottom_z']],
            [mid[2], y, (st['top_z']+st['bottom_z'])/2],
            [mid[0], y, (st['top_z']+st['bottom_z'])/2],
            [upper[0]-.5, y, st['top_z']], [run[0]+.65, y, t['z']]])
    for i, strip in enumerate(s for s in t['slabs'] if s['id'].startswith('west_strip')):
        a,b,c,d = strip['bounds']; x = (a+c)/2
        add(f'west_strip_{i}', [[x,b+.65,t['z']], [x,d-.65,t['z']]])
    for i, bay in enumerate(t['recesses']):
        a,b,c,d = bay['bounds']
        add(f'office_bay_{i}', [[c-.65,b+.65,t['z']], [c-.65,d-.65,t['z']]])
    return routes


def require_game_closed():
    if 'cs2.exe' in subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq cs2.exe', '/FO', 'CSV', '/NH'], text=True).lower():
        raise RuntimeError('CS2 is already running; refusing to replace another session')


def guard_probes(terrace):
    """Approach each terrace guard from supported slab, facing the drop."""
    for i, edge in enumerate(terrace['edges']):
        a,b,c,d = edge['bounds']; x,y = (a+c)/2,(b+d)/2
        candidates = ([(x,y+.65,0),(x,y-.65,180)] if c-a >= d-b
                      else [(x+.65,y,-90),(x-.65,y,90)])
        for e,n,yaw in candidates:
            if any(s['bounds'][0] <= e <= s['bounds'][2] and s['bounds'][1] <= n <= s['bounds'][3]
                   for s in terrace['slabs']):
                yield f"{edge['kind']}_{i}", (e,n,terrace['z']), yaw
                break
        else:
            raise RuntimeError('No supported approach to guard '+str(edge))


def launch_scene(cs2):
    require_game_closed()
    exe = cs2/'game/bin/win64/cs2.exe'
    return subprocess.Popen([str(exe), '-steam', '-retail', '-addon', 'trento_povo',
         '-tools', '-insecure', '-condebug', '-vconsole', '-netconport', '27400',
         '-windowed', '-w', '1280', '-h', '800', '+game_type', '0', '+game_mode', '2',
         '+map', 'maps/'+MAP+'.vpk', '+bot_quota', '0', '+mp_warmup_pausetimer', '1'], cwd=exe.parent)


def test_scene(cs2, package):
    OUT.mkdir(parents=True, exist_ok=True)
    t = json.loads((REVIEW/'terrace.json').read_text(encoding='utf-8'))
    report = dict(status='running', map=MAP, isolated_review_scene=True,
                  exact_obj_sha256=hashlib.sha256((REVIEW/'terrace.obj').read_bytes()).hexdigest(),
                  package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(), routes=[], checks=[],
                  started_utc=datetime.now(timezone.utc).isoformat())
    ready = False
    for _ in range(180):
        try:
            status = run(['status'], seconds=.25)
            if re.search(r'@ Current\s*:\s*game\b', status) and f': {MAP} | main lump | mapload]' in status:
                ready = True; break
        except (OSError, socket.timeout):
            pass
        time.sleep(.5)
    if not ready:
        raise RuntimeError('The terrace test scene did not load')
    run(SETTINGS, seconds=3)
    run(['bot_kick', 'jointeam 2', 'mp_warmup_start', 'god 1', 'engine_no_focus_sleep 0', 'fps_max 60'], seconds=2)
    console = Console(27400); driver = TerraceDriver(console, MAP)
    def check(name, passed, **details):
        record = dict(name=name, passed=bool(passed), **details)
        report['checks'].append(record); print(record, flush=True)
    try:
        driver.guard()
        run_routes(driver, walking_routes(t), report, OUT/'walking')
        for i, hole in enumerate(t['holes']):
            driver.guard(); a,b,c,d = hole['bounds']
            console.command(['noclip 0', 'setpos '+world(((a+c)/2,(b+d)/2,t['z']+.1))], 1.5)
            p = driver.position()
            check(f'hole_{i}_has_no_floor', abs(p[2]+3.2)<.15, position=p)
        for name, start, yaw in guard_probes(t):
            driver.guard(); driver.place(start)
            console.pulse([f'setang 0 {yaw} 0', '+forward 42'], 1)
            p = driver.position()
            check(name+'_blocks_fall', abs(p[2]-t['z'])<.15, position=p)
        # Native engine screenshots retain the scene's actual renderer output.
        shots = [('south_stair', (44,1.1,-3.2), (0,-90,0)),
                 ('north_stair', (44,106.2,-3.2), (0,-90,0)),
                 ('south_terrace_handrails', (25,1.15,.4), (0,-90,0)),
                 ('west_middle_hole', (-27,55,4), (40,90,0))]
        screenshot_dir = cs2/'game/csgo_addons/trento_povo/screenshots'
        for name, p, angles in shots:
            driver.guard()
            console.command(['noclip 1', 'setpos '+world(p), 'setang '+' '.join(map(str,angles)),
                             'cl_drawhud 0', 'r_drawviewmodel 0'], .5)
            console.command('png_screenshot terrace_native_'+name, 1.5)
            files = sorted(screenshot_dir.glob('terrace_native_'+name+'*'), key=lambda f:f.stat().st_mtime)
            if files:
                shutil.copyfile(files[-1], OUT/(name+files[-1].suffix))
        report['status'] = 'passed' if all(r['status']=='passed' for r in report['routes']) and all(c['passed'] for c in report['checks']) else 'failed'
    finally:
        driver.cleanup()
        console.command(['cl_drawhud 1','r_drawviewmodel 1','noclip 0'])
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (OUT/'native-test.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        logs = ROOT/'build/terrace-native-test'; logs.mkdir(parents=True, exist_ok=True)
        (logs/'console.log').write_text('\n'.join(console.transcript), encoding='utf-8')
        console.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-only', action='store_true')
    args = parser.parse_args()
    require_game_closed()
    cs2 = project.discover_cs2_root()
    logs = ROOT/'build/terrace-native-test'; logs.mkdir(parents=True, exist_ok=True)
    package = cs2/'game/csgo_addons/trento_povo/maps'/(MAP+'.vpk')
    if not args.run_only:
        package = build_scene(cs2, logs)
    else:
        identity = json.loads((logs/'scene-inputs.json').read_text(encoding='utf-8'))
        if str(REVIEW/'terrace.obj') not in identity or str(package) not in identity:
            raise RuntimeError('Rebuild the native test scene for this checkout/install')
        for name, digest in identity.items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('Native scene inputs changed; rerun without --run-only')
    process = launch_scene(cs2)
    try:
        report = test_scene(cs2, package)
        print('Native terrace test:', report['status'], flush=True)
        return 0 if report['status']=='passed' else 1
    finally:
        # Close only the test session launched by this invocation.
        if process.poll() is None:
            try:
                status = run(['status'], seconds=.25)
                if f': {MAP} | main lump | mapload]' in status:
                    run(['quit'], seconds=.25)
            except OSError:
                pass


if __name__ == '__main__':
    raise SystemExit(main())
