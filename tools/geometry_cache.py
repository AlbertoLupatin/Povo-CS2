"""Reuse campus geometry within one process while its inputs are unchanged.

The test suite builds the same campus dozens of times and each build takes
seconds. A result is reused only when the call arguments, the size and mtime
of every file under config/ and data/ and of every tools/*.py, and the
identity of every global in the loaded tools modules all match. A
mock.patch of a module constant therefore still forces a fresh build.
Callers always receive deep copies. POVO_GEOMETRY_CACHE=0 disables reuse.
"""

import copy
import functools
import inspect
import os
import sys
from pathlib import Path

TOOLS = os.path.normcase(str(Path(__file__).resolve().parent))
ENTRIES = 4


def _file_stamps(root):
    stamps = []
    for folder in ('config', 'data', 'tools'):
        for directory, folders, names in os.walk(root / folder):
            folders[:] = [f for f in folders if f != '__pycache__']
            for name in names:
                if folder == 'tools' and not name.endswith('.py'):
                    continue
                stat = os.stat(os.path.join(directory, name))
                stamps.append((directory, name, stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(stamps))


def _module_state():
    state = []
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and os.path.normcase(os.path.dirname(os.path.abspath(path))) == TOOLS:
            state.append((name, tuple((key, id(value)) for key, value in list(vars(module).items()))))
    return tuple(sorted(state))


def memoize_geometry(build):
    signature = inspect.signature(build)
    cache = {}

    @functools.wraps(build)
    def cached(*args, **kwargs):
        if os.environ.get('POVO_GEOMETRY_CACHE', '1') == '0':
            return build(*args, **kwargs)
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = tuple((name, repr(value)) for name, value in bound.arguments.items())
        root = Path(bound.arguments['root']).resolve()
        key = (arguments, _file_stamps(root), _module_state())
        if key not in cache:
            result = build(*args, **kwargs)
            # The first build imports helpers lazily; key the entry on the
            # state after those imports so the next identical call matches.
            key = (arguments, _file_stamps(root), _module_state())
            cache[key] = result
            while len(cache) > ENTRIES:
                del cache[next(iter(cache))]
        return copy.deepcopy(cache[key])

    cached.cache_clear = cache.clear
    return cached
