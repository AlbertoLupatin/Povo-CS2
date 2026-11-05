"""Opt-in, exact-input optimizations for a complete campus build."""
from contextlib import contextmanager
import functools
import json
from pathlib import Path
import sys
import time

try:
    from . import fast_point_entities, vmap_delimiters
    from .obj_compile_batches import rebatch_render_model, split_model_collision
except ImportError:
    import fast_point_entities, vmap_delimiters
    from obj_compile_batches import rebatch_render_model, split_model_collision


def _project_modules():
    directory = Path(__file__).resolve().parent
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).resolve().parent == directory:
            yield module


def _replace_aliases(replacements):
    for module in _project_modules():
        for name, value in list(vars(module).items()):
            for old, new in replacements:
                if value is old:
                    setattr(module, name, new)
                    break


@contextmanager
def optimized_inputs(campus):
    """Retain serializers and geometry, restoring process hooks on exit.

    Only deployed collision inputs are partitioned. Render shared indices and
    layout are untouched. The normal build still exports and compiles all models;
    this context does not enable a cache or alter lighting options.
    """
    project = campus.project
    original_deploy = campus.deploy_assets
    replacements = [
        (project._matching_brace, functools.partial(vmap_delimiters.matching_brace, error_type=project.ProjectError)),
        (project._matching_bracket, functools.partial(vmap_delimiters.matching_bracket, error_type=project.ProjectError)),
    ]
    _replace_aliases(replacements)
    stats, undo = fast_point_entities.enable(project)

    @functools.wraps(original_deploy)
    def deploy(cs2_root, *args, **kwargs):
        result = original_deploy(cs2_root, *args, **kwargs)
        content = Path(cs2_root) / 'content/csgo_addons/trento_povo'
        model = content / 'models/povo' / (campus.MODEL + '.vmdl')
        started = time.monotonic()
        report = {'render': rebatch_render_model(content, model),
                  'collision': split_model_collision(content, model),
                  'point_insertion': dict(stats)}
        report['seconds'] = time.monotonic() - started
        output = campus.ROOT / 'build/compile_partitions' / (campus.MODEL + '.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print('Verified exact compiler input partitions: ' + str(output), flush=True)
        return result

    campus.deploy_assets = deploy
    try:
        yield stats
    finally:
        campus.deploy_assets = original_deploy
        undo()
        _replace_aliases([(new, old) for old, new in replacements])
