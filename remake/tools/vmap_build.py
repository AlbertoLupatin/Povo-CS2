"""Assemble, deploy and compile a generated .vmap in the povo_remake addon.

MapBuilder starts from Valve's Wingman template (sky, sun, fog, post
processing, map parameters), removes the template geometry, and lets
generators add native meshes and entities cloned from Valve examples.
"""

import copy
import json
from pathlib import Path
import subprocess
import time

import kv2
import vmap_mesh as vm

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config/project.json').read_text())
CS2 = Path(CONFIG['cs2_root'])
ADDON = CONFIG['addon']
TEMPLATE = CS2 / 'content/csgo/maps/templates/template_wingman.vmap'
LIGHTING_EXAMPLE = CS2 / 'content/csgo_addons/addon_template/maps/content_examples/lighting_info.vmap'
KEEP = {'env_sky', 'light_environment', 'env_cubemap_fog', 'post_processing_volume', 'info_map_parameters'}
TEMPLATE_ONLY = {'info_player_terrorist', 'info_player_counterterrorist', 'point_worldtext'}
BIN = CS2 / 'game/bin/win64'


def load_text(source, work):
    text = work / (source.stem + '_kv2.vmap')
    if not text.exists() or text.stat().st_mtime < source.stat().st_mtime:
        subprocess.run([str(BIN / 'dmxconvert.exe'), '-i', str(source), '-o', str(text),
                        '-oe', 'keyvalues2', '-of', 'vmap'], check=True, capture_output=True)
    return kv2.parse(text.read_text(encoding='utf8'))


def fresh_ids(element, ids):
    for el in kv2.walk(element):
        if el.get('id') is not None:
            el.set('id', ids.element(), 'elementid')
        if el.get('nodeID') is not None:
            el.set('nodeID', ids.node_id(), 'int')
        if el.get('referenceID') is not None:
            el.set('referenceID', ids.reference(), 'uint64')


class MapBuilder:
    def __init__(self, name):
        self.name = name
        self.work = ROOT / 'build/maps'
        self.work.mkdir(parents=True, exist_ok=True)
        self.header, self.roots = load_text(TEMPLATE, self.work)
        self.root = kv2.root_of(self.roots)
        self.world = self.root.get('world')
        by_id = {r.get('id'): r for r in self.roots}
        raw = self.world.get('children')
        children = [by_id[c[1]] if isinstance(c, tuple) else c for c in raw]
        self.mesh_template = next(c for c in children if c.cls == 'CMapMesh')
        self.kept, self.templates = [], {}
        for item, c in zip(raw, children):
            cls = c.get('entity_properties').get('classname') if c.cls == 'CMapEntity' else None
            if cls in KEEP | TEMPLATE_ONLY and cls not in self.templates:
                self.templates[cls] = c
                if cls in KEEP:
                    self.kept.append(item)   # a ref stays a ref to its top-level definition
        _h, lighting = load_text(LIGHTING_EXAMPLE, self.work)
        for e in (e for r in lighting for e in kv2.walk(r) if e.cls == 'CMapEntity'):
            cls = e.get('entity_properties').get('classname')
            self.templates.setdefault(cls, e)
        first = 1 + max(int(e.get('nodeID')) for r in self.roots for e in kv2.walk(r) if e.get('nodeID'))
        self.ids = vm.Ids(name, first)
        self.new = []

    def mesh(self, solids, tint=(255, 255, 255), lightmap_bias=0, closed=True):
        if solids:
            self.new.append(vm.map_mesh(self.mesh_template, self.ids, solids, tint, lightmap_bias, closed))

    def entity(self, classname, props, origin, angles='0 0 0', template=None):
        """Clone a template entity of this class, overriding the given keyvalues."""
        e = copy.deepcopy(self.templates[template or classname])
        fresh_ids(e, self.ids)
        gp = e.get('entity_properties')
        gp.set('classname', classname)
        for k, v in props.items():
            gp.set(k, str(v))
        e.set('origin', ' '.join(vm.fmt(float(x)) for x in origin), 'vector3')
        e.set('angles', angles, 'qangle')
        self.new.append(e)
        return e

    def set_kept(self, classname, props):
        gp = self.templates[classname].get('entity_properties')
        for k, v in props.items():
            gp.set(k, str(v))

    def write(self):
        self.world.set('children', self.kept + self.new, 'element_array')
        referenced = {c[1] for c in self.kept if isinstance(c, tuple)}
        roots = [r for r in self.roots
                 if r.cls == '$prefix_element$' or r is self.root or r.get('id') in referenced]
        # Editor bookkeeping that points at removed template nodes.
        for el in kv2.walk(self.root):
            if el.cls == 'CMapSelectionSet':
                for a in el.attrs:
                    if a[1] == 'element_array' and a[0] != 'children':
                        a[2] = []
            if el.cls == 'CVisibilityMgr':
                el.set('nodes', [], 'element_array')
                el.set('hiddenFlags', [], 'int_array')
        source = self.work / f'{self.name}_kv2.vmap'
        source.write_text(kv2.emit(self.header, roots), encoding='utf8')
        return source

    def deploy(self, compile_map=True, quality=1, vis=True, bake=True):
        """Convert to binary in the addon's content tree and compile.
        vis=False skips the visibility pass (hours on a large open map), for blockouts;
        bake=False also skips the lightmap bake: an unlit test build in seconds.
        Returns 0 only if the log shows the map built; a GPU hang stops the compile at once."""
        source = self.write()
        content = CS2 / 'content/csgo_addons' / ADDON
        game = CS2 / 'game/csgo_addons' / ADDON
        (content / 'maps').mkdir(parents=True, exist_ok=True)
        game.mkdir(parents=True, exist_ok=True)
        (game / 'addoninfo.txt').write_text('"AddonInfo"\n{\n\t"IsTemplate"\t"0"\n\t"IsPlayable"\t"1"\n}\n')
        target = content / 'maps' / f'{self.name}.vmap'
        subprocess.run([str(BIN / 'dmxconvert.exe'), '-i', str(source), '-o', str(target),
                        '-oe', 'binary', '-of', 'vmap'], check=True, capture_output=True)
        print('deployed', target, flush=True)
        if not compile_map:
            return 0
        log = self.work / f'{self.name}_compile.log'
        # Custom materials first: the map compile bakes lighting before compiling its children.
        custom = sorted((content / 'materials').rglob('*.vmat'))
        if custom:
            subprocess.run([str(BIN / 'resourcecompiler.exe'), '-nop4', '-game', str(CS2 / 'game/csgo'),
                            '-i', *map(str, custom)], capture_output=True)
        # A partial compile (named stages) is refused under -fshallow2.
        # Test builds bake at 2048 max: past ~2 s per GPU block Windows kills vrad3 ("GPU hang").
        if vis:
            stages = ['-fshallow2']
        else:
            stages = ['-fshallow', '-world', '-phys', '-gridnav']
            if bake:
                stages += ['-bakelighting', '-lightmapMaxResolution', '2048']
        hung = False
        with open(log, 'w', encoding='utf8') as fh:
            proc = subprocess.Popen([str(BIN / 'resourcecompiler.exe'), '-nop4', *stages,
                                     '-lightmapVRadQuality', str(quality), '-game', str(CS2 / 'game/csgo'),
                                     '-i', str(target)], stdout=fh, stderr=subprocess.STDOUT)
            # The compiler retries a hung bake five times; stop at the first hang instead.
            while proc.poll() is None:
                time.sleep(2)
                text = log.read_text(encoding='utf8', errors='replace')
                if 'GPU Hang' in text or 'DEVICE_LOST' in text:
                    hung = True
                    for exe in ('vrad3.exe', 'resourcecompiler.exe'):
                        subprocess.run(['taskkill', '/IM', exe, '/F'], capture_output=True)
                    proc.wait()
        # resourcecompiler can exit 0 on a failed map build; trust the log instead.
        text = log.read_text(encoding='utf8', errors='replace')
        failed = hung or proc.returncode or 'Map build FAILED' in text or ' 0 compiled' in text
        reason = 'GPU hang in the lightmap bake' if hung else ''
        print('compile', 'FAILED' if failed else 'ok', reason, 'log', log, flush=True)
        return 1 if failed else 0
