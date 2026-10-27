"""Three-level Povo 1 survey source, independent of the campus vertical datum.

The photograph trace retains independent source coordinates; the campus
integrator anchors the confirmed -1/0/1 correspondence to physical elevations.
No offices are assigned a repeated classroom furniture kit.
"""
import copy
import hashlib
import json
from pathlib import Path

try:
    from . import build_povo_interior as interior
except ImportError:
    import build_povo_interior as interior

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = Path('data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300')


def source_config(root=ROOT, *, floor_elevations=None):
    """Return ordinary interior config/alignment with explicit floor identities.

    ``floor_elevations`` maps -1, 0 and 1 to absolute metres. Omission keeps
    provisional legacy 3.6 m spacing solely for offline inspection.
    """
    survey = json.loads((root/'config/povo1_survey.json').read_text())
    config = json.loads((root/'config/povo1_interior_study.json').read_text())
    alignment = json.loads((root/config['alignment']).read_text())
    config = copy.deepcopy(config)
    config['classroom_fitouts'] = []
    config['status'] = survey['status']
    config['wall_height_metres'] = 2.9
    for level, identity in zip(config['levels'], survey['canonical_floors']):
        level['user_floor'] = identity['user_floor']
        level['source_photos'] = identity['source_photos']
        # These are the source-plan A202/A203 positions, never their temporary
        # campus relocation to the reception floor.
        profile = next(p for p in alignment['profiles'] if p['id'] == level['id'])
        profile['labels'].pop('user_confirmed_floor', None)
        profile['labels']['source_plan_floor'] = identity['user_floor']
        level['trace_status'] = 'Legacy manual footprint; checked against new source photo, not newly rectified'
        profile['labels']['source_walk_20261027'] = identity['source_photos']
    upper = copy.deepcopy(survey['upper_level'])
    config['levels'].append(upper)
    alignment['profiles'].append(dict(
        id=upper['id'], outer=survey['preview']['outer'],
        entry=[136,675], features=[],
        source_file=str(PHOTO_DIR/survey['source_photo']),
        labels=dict(source_plan_floor=1, room_group='206-259 offices/laboratories',
                    source_walk_20261027=[22,31,32])))
    if floor_elevations is not None:
        if set(floor_elevations) != {-1,0,1}:
            raise ValueError('Supply physical elevations for exactly floors -1, 0 and 1')
        config['reference_elevation_metres'] = floor_elevations[-1]
        for level in config['levels']:
            level['height_offset_metres'] = floor_elevations[level['user_floor']]-floor_elevations[-1]
    config['survey_20261027'] = survey
    return config, alignment


def build_survey_geometry(root=ROOT, *, floor_elevations=None):
    """Build every traced level, without linking to an unconfirmed bridge datum.

    This returns walls, individual room door gaps, ring corridors and open
    courtyard/terraces. The campus integrator adds stairs and bridge geometry.
    """
    config, alignment = source_config(root, floor_elevations=floor_elevations)
    campus = json.loads((root/config['campus_config']).read_text())
    boxes, levels = interior.build_boxes(config, alignment, campus['origin'])
    for level, source in zip(levels, config['levels']):
        level['user_floor'] = source['user_floor']
        level['source_photos'] = source.get('source_photos', [22,31,32])
        level['survey_status'] = source.get('trace_status', 'New photo trace; dimensions and door widths provisional')
    return config, alignment, boxes, levels


def source_hashes(root=ROOT):
    return {f'image{n:05}.jpeg':hashlib.sha256((root/PHOTO_DIR/f'image{n:05}.jpeg').read_bytes()).hexdigest()
            for n in (4,5,6,7,8,9,10,17,18,19,20,22,23,24,25,26,27,28,30,31,32)}
