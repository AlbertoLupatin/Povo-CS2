#!/usr/bin/env python3
"""Deploy, compile, and recover the repository-owned CS2 addon source.

The geographic preparation pipeline is platform-independent. Only commands that
touch Valve's installed Workshop Tools require Windows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable
import uuid


ADDON_NAME = "trento_povo"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STEAM_INSTALL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive"
)

GENERATED_CONTENT = (
    (Path("exports/povo_blockout/povo_blockout.obj"), Path(
        "models/povo/povo_blockout.obj"
    )),
    (Path("exports/povo_blockout/povo_blockout.mtl"), Path(
        "models/povo/povo_blockout.mtl"
    )),
    (Path("exports/povo_blockout/povo_blockout_collision.obj"), Path(
        "models/povo/povo_blockout_collision.obj"
    )),
    (Path("exports/povo_blockout/orthophoto_reference.png"), Path(
        "models/povo/orthophoto_reference.png"
    )),
    (Path("exports/povo_blockout/orthophoto_reference.png"), Path(
        "materials/trento/povo/orthophoto_reference.png"
    )),
)

# Files that Hammer/ModelDoc may update and that belong back in the repository.
SYNC_CONTENT = (
    Path("maps/trento_povo.vmap"),
    Path("models/povo/povo_blockout.vmdl"),
    Path("materials/trento/povo/terrain_reference.vmat"),
    Path("materials/trento/povo/building_blockout.vmat"),
    Path("materials/trento/povo/gameplay_cover.vmat"),
    Path("materials/trento/povo/gameplay_boundary.vmat"),
    Path("materials/trento/povo/calibration.vmat"),
)
SYNC_GAME = (
    Path("addoninfo.txt"),
    Path("cfg/maps/trento_povo.cfg"),
)
BLOCKOUT_MODEL = "models/povo/povo_blockout.vmdl"
# Source 2's OBJ importer exposes the export's Z-up axes as (Z, X, Y).
# Pitching the placed prop by -90 degrees restores geographic Z as world up.
BLOCKOUT_ANGLES = "-90 0 0"

# Compact Wingman layout in the Povo east forecourt. These coordinates are
# sampled from the exported terrain after applying the model's -90 degree pitch
# and 39.37007874 units-per-metre scale. The paired north/south starts feed two
# cover-separated approaches inside the generated boundary.
PLAYTEST_SPAWNS = {
    "info_player_counterterrorist": (
        ("2253.937 2332.677 369.008", "0 180 0"),
        ("2253.937 2568.898 356.409", "0 180 0"),
        ("2253.937 2844.488 417.827", "0 180 0"),
        ("2096.457 2332.677 371.764", "0 180 0"),
        ("2096.457 2568.898 360.740", "0 180 0"),
        ("2096.457 2844.488 421.370", "0 180 0"),
    ),
    "info_player_terrorist": (
        ("-2096.457 2332.677 392.630", "0 0 0"),
        ("-2096.457 2568.898 380.819", "0 0 0"),
        ("-2096.457 2844.488 441.843", "0 0 0"),
        ("-2253.937 2332.677 401.685", "0 0 0"),
        ("-2253.937 2568.898 389.087", "0 0 0"),
        ("-2253.937 2844.488 446.961", "0 0 0"),
    ),
}
PLAYTEST_OBJECTIVE_ORIGIN = "-9.843 2608.268 358.772"
PLAYTEST_BUYZONE_ORIGINS = {
    "3": "2175.197 2568.898 360.740",  # Counter-Terrorist
    "2": "-2175.197 2568.898 384.756",  # Terrorist
    "0": PLAYTEST_OBJECTIVE_ORIGIN,  # Template 2v2 zone; harmless when disabled.
}
PLAYTEST_NAV_ORIGIN = "-9.843 2608.268 342.772"
PLAYTEST_CENTER = "0 2608.268 600"
PLAYTEST_SKYBOX_ORIGIN = "0 0 400"
PLAYTEST_SKYBOX_SCALES = "10 8 16"
PLAYTEST_POSTPROCESS_SCALES = "170 40 30"
PLAYTEST_MINIMAP_CORNERS = (
    "-2559.055 2165.354 250",
    "2559.055 3149.606 900",
)
VALID_SKY_MATERIAL = (
    "materials/skybox/skymodel_hosekwilkie_ref/"
    "skymodel_hosekwilkie_albedo_0_30_turbidity_02_0_elevation_65_0.vmat"
)
LIGHTMAP_RESOLUTION_MATERIAL = "materials/tools/toolslightmapres.vmat"
POSTPROCESS_VOLUME_MESH_MATERIAL = (
    "materials/models/props_junk/trashclusters01.vmat"
)
TEMPLATE_ENTITY_CLASSES_TO_REMOVE = {
    "func_brush",
    "func_clip_vphysics",
    "func_nav_blocker",
    "logic_auto",
    "logic_script",
    "point_worldtext",
}


class ProjectError(RuntimeError):
    """An actionable project configuration error."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_steam_library_paths(text: str) -> list[Path]:
    """Extract Steam library roots from libraryfolders.vdf text."""
    paths: list[Path] = []
    for raw in re.findall(r'"path"\s+"([^"]+)"', text, flags=re.IGNORECASE):
        path = Path(raw.replace(r"\\", "\\"))
        if path not in paths:
            paths.append(path)
    return paths


def _steam_roots() -> list[Path]:
    roots: list[Path] = []
    steam_path = None
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_path = Path(winreg.QueryValueEx(key, "SteamPath")[0])
        except (ImportError, FileNotFoundError, OSError):
            pass
    if steam_path:
        roots.append(steam_path)
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        roots.append(Path(program_files_x86) / "Steam")

    libraries: list[Path] = []
    for root in roots:
        if root not in libraries:
            libraries.append(root)
        library_file = root / "steamapps" / "libraryfolders.vdf"
        if library_file.is_file():
            try:
                for path in parse_steam_library_paths(
                    library_file.read_text(encoding="utf-8", errors="replace")
                ):
                    if path not in libraries:
                        libraries.append(path)
            except OSError:
                pass
    return libraries


def is_cs2_root(path: Path) -> bool:
    return (
        (path / "content" / "csgo").is_dir()
        and (path / "game" / "csgo" / "gameinfo.gi").is_file()
        and (
            path / "game" / "bin" / "win64" / "resourcecompiler.exe"
        ).is_file()
    )


def discover_cs2_root(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("CS2_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    candidates.append(DEFAULT_STEAM_INSTALL)
    for library in _steam_roots():
        candidates.append(
            library / "steamapps" / "common" / "Counter-Strike Global Offensive"
        )

    checked: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in checked:
            continue
        checked.append(resolved)
        if is_cs2_root(resolved):
            return resolved
    rendered = "\n  - ".join(str(path) for path in checked)
    raise ProjectError(
        "CS2 Workshop Tools were not found. Set CS2_ROOT or pass --cs2-root. "
        f"Checked:\n  - {rendered}"
    )


def _repo_sources(repo_root: Path) -> tuple[Path, Path]:
    return (
        repo_root / "cs2" / "content" / ADDON_NAME,
        repo_root / "cs2" / "game" / ADDON_NAME,
    )


def _installed_targets(cs2_root: Path) -> tuple[Path, Path]:
    return (
        cs2_root / "content" / "csgo_addons" / ADDON_NAME,
        cs2_root / "game" / "csgo_addons" / ADDON_NAME,
    )


def _copy_file(
    source: Path,
    destination: Path,
    *,
    dry_run: bool,
    records: list[dict[str, str]],
) -> None:
    if not source.is_file():
        raise ProjectError(f"Required source file is missing: {source}")
    source_hash = sha256(source)
    changed = not destination.is_file() or sha256(destination) != source_hash
    records.append(
        {
            "source": str(source),
            "destination": str(destination),
            "sha256": source_hash,
            "status": "update" if changed else "unchanged",
        }
    )
    if changed and not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _tree_files(root: Path) -> Iterable[tuple[Path, Path]]:
    if not root.is_dir():
        raise ProjectError(f"Required source directory is missing: {root}")
    for source in sorted(path for path in root.rglob("*") if path.is_file()):
        yield source, source.relative_to(root)


def deploy(
    cs2_root: Path,
    *,
    repo_root: Path = REPO_ROOT,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    content_source, game_source = _repo_sources(repo_root)
    content_target, game_target = _installed_targets(cs2_root)
    records: list[dict[str, str]] = []

    for source, relative in _tree_files(content_source):
        _copy_file(
            source, content_target / relative, dry_run=dry_run, records=records
        )
    for source, relative in _tree_files(game_source):
        _copy_file(source, game_target / relative, dry_run=dry_run, records=records)
    for relative_source, relative_target in GENERATED_CONTENT:
        _copy_file(
            repo_root / relative_source,
            content_target / relative_target,
            dry_run=dry_run,
            records=records,
        )

    if not dry_run:
        manifest_path = content_target / "trento_deploy_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "addon": ADDON_NAME,
                    "repository": str(repo_root.resolve()),
                    "files": records,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(manifest_path)
    return records


def sync_from_cs2(
    cs2_root: Path,
    *,
    repo_root: Path = REPO_ROOT,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    content_source, game_source = _repo_sources(repo_root)
    content_target, game_target = _installed_targets(cs2_root)
    records: list[dict[str, str]] = []
    pairs = [
        *((content_target / path, content_source / path) for path in SYNC_CONTENT),
        *((game_target / path, game_source / path) for path in SYNC_GAME),
    ]
    for installed, repository in pairs:
        if not installed.is_file():
            continue
        _copy_file(installed, repository, dry_run=dry_run, records=records)
    return records


def _print_records(records: list[dict[str, str]]) -> None:
    for record in records:
        print(f"{record['status']:>9}  {record['destination']}")


def _matching_bracket(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    for position in range(opening, len(text)):
        character = text[position]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return position
    raise ProjectError("Unbalanced element array in VMAP text")


def _matching_brace(text: str, opening: int) -> int:
    """Return the closing brace while ignoring braces inside quoted values."""
    depth = 0
    quoted = False
    escaped = False
    for position in range(opening, len(text)):
        character = text[position]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return position
    raise ProjectError("Unbalanced entity block in VMAP text")


def _replace_entity_transform(
    block: str,
    origin: str,
    angles: str | None = None,
    scales: str | None = None,
) -> str:
    """Move an entity and any brush children sharing its local origin."""

    def replace_vector(match: re.Match[str], desired: str) -> str:
        current_values = tuple(float(value) for value in match.group(2).split())
        desired_values = tuple(float(value) for value in desired.split())
        if len(current_values) == len(desired_values) and all(
            abs(current - target) <= 0.001
            for current, target in zip(current_values, desired_values)
        ):
            return match.group(0)
        return f"{match.group(1)}{desired}{match.group(3)}"

    updated, origin_count = re.subn(
        r'("origin"\s+"vector3"\s+")([^"]+)(")',
        lambda match: replace_vector(match, origin),
        block,
    )
    if not origin_count:
        raise ProjectError("VMAP entity has no origin transform")
    if angles is not None:
        updated, angle_count = re.subn(
            r'("angles"\s+"qangle"\s+")([^"]+)(")',
            lambda match: replace_vector(match, angles),
            updated,
        )
        if not angle_count:
            raise ProjectError("VMAP entity has no angle transform")
    if scales is not None:
        updated, scale_count = re.subn(
            r'("scales"\s+"vector3"\s+")([^"]+)(")',
            lambda match: replace_vector(match, scales),
            updated,
        )
        if not scale_count:
            raise ProjectError("VMAP entity has no scale transform")
    return updated


def _element_span(text: str, start: int, closing: int) -> tuple[int, int]:
    """Include a VMAP array element's optional comma and following newline."""
    end = closing + 1
    while end < len(text) and text[end] in " \t":
        end += 1
    if end < len(text) and text[end] == ",":
        end += 1
    if text.startswith("\r\n", end):
        end += 2
    elif end < len(text) and text[end] == "\n":
        end += 1
    return start, end


def _entity_ranges(text: str) -> list[tuple[int, int, str, str]]:
    """Return entity block ranges, class names, and source blocks."""
    ranges = []
    pattern = re.compile(r'(?m)^[ \t]*"CMapEntity"[ \t]*$')
    class_pattern = re.compile(r'"classname"\s+"string"\s+"([^"]+)"')
    for match in pattern.finditer(text):
        opening = text.find("{", match.end())
        if opening < 0:
            raise ProjectError("VMAP entity has no opening brace")
        closing = _matching_brace(text, opening)
        block = text[match.start() : closing + 1]
        class_match = class_pattern.search(block)
        ranges.append(
            (match.start(), closing + 1, class_match.group(1) if class_match else "", block)
        )
    return ranges


def normalize_template_buyzones(text: str) -> str:
    """Turn the template's conditional 2v2 volume into the real T buy zone."""
    replacements = []
    for start, end, classname, block in _entity_ranges(text):
        if classname != "func_buyzone":
            continue
        team_match = re.search(r'("TeamNum"\s+"string"\s+")([^"]+)(")', block)
        if not team_match:
            continue
        team = team_match.group(2)
        has_mesh = '"CMapMesh"' in block
        desired = "2" if team == "0" and has_mesh else "0" if team == "2" and not has_mesh else team
        updated = block
        if desired != team:
            updated = (
                updated[: team_match.start(2)]
                + desired
                + updated[team_match.end(2) :]
            )
        if desired == "2":
            updated = re.sub(
                r'("targetname"\s+"string"\s+")([^"]*)(")',
                r'\1\3',
                updated,
                count=1,
            )
        if updated != block:
            replacements.append((start, end, updated))
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text


def remove_template_placeholders(text: str) -> str:
    """Remove sample-room geometry and editor helpers, preserving its sky shell."""
    entities = _entity_ranges(text)
    removals = []
    for start, end, classname, _ in entities:
        if classname in TEMPLATE_ENTITY_CLASSES_TO_REMOVE:
            opening = text.find("{", start, end)
            closing = _matching_brace(text, opening)
            removals.append(_element_span(text, start, closing))

    entity_spans = [(start, end) for start, end, _, _ in entities]
    mesh_pattern = re.compile(r'(?m)^[ \t]*"CMapMesh"[ \t]*$')
    for match in mesh_pattern.finditer(text):
        if any(start <= match.start() < end for start, end in entity_spans):
            continue
        opening = text.find("{", match.end())
        if opening < 0:
            raise ProjectError("VMAP mesh has no opening brace")
        closing = _matching_brace(text, opening)
        block = text[match.start() : closing + 1]
        retained_materials = (
            "materials/tools/toolsskybox.vmat",
            LIGHTMAP_RESOLUTION_MATERIAL,
        )
        if not any(material in block for material in retained_materials):
            removals.append(_element_span(text, match.start(), closing))

    for start, end in sorted(removals, reverse=True):
        text = text[:start] + text[end:]
    children_open = _world_children_opening(text)
    children_close = _matching_bracket(text, children_open)
    children = text[children_open + 1 : children_close]
    children = re.sub(r",(\s*)$", r"\1", children)
    text = text[: children_open + 1] + children + text[children_close:]
    return text


def configure_playtest_environment(text: str) -> str:
    """Fit the retained sky shell and exposure volume to the Povo arena."""
    text = re.sub(
        r'materials/skybox/skymodel_hosekwilkie_ref/'
        r'skymodel_hosekwilkie_albedo_0_30_turbidity_02_0_elevation_\d+_0\.vmat',
        VALID_SKY_MATERIAL,
        text,
    )
    replacements = []
    postprocess_count = 0
    for start, end, classname, block in _entity_ranges(text):
        if classname == "post_processing_volume":
            updated = _replace_entity_transform(
                block,
                PLAYTEST_CENTER,
                scales=PLAYTEST_POSTPROCESS_SCALES,
            )
            replacements.append((start, end, updated))
            postprocess_count += 1
    if postprocess_count != 1:
        raise ProjectError(
            f"VMAP has {postprocess_count} post-processing volumes; expected 1"
        )
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]

    sky_matches = []
    for match in re.finditer(r'(?m)^[ \t]*"CMapMesh"[ \t]*$', text):
        opening = text.find("{", match.end())
        closing = _matching_brace(text, opening)
        block = text[match.start() : closing + 1]
        if "materials/tools/toolsskybox.vmat" in block:
            sky_matches.append((match.start(), closing + 1, block))
    if len(sky_matches) != 1:
        raise ProjectError(f"VMAP has {len(sky_matches)} sky shells; expected 1")
    start, end, block = sky_matches[0]
    updated = _replace_entity_transform(
        block,
        PLAYTEST_SKYBOX_ORIGIN,
        scales=PLAYTEST_SKYBOX_SCALES,
    )
    return text[:start] + updated + text[end:]


def _ensure_map_asset_reference(text: str, asset: str) -> str:
    """Add one source asset to the VMAP header without duplicating it."""
    references_at = text.find('"map_asset_references" "string_array"')
    if references_at < 0:
        raise ProjectError("VMAP has no map_asset_references array")
    opening = text.find("[", references_at)
    closing = _matching_bracket(text, opening)
    body = text[opening + 1 : closing]
    if re.search(rf'"{re.escape(asset)}"', body):
        return text
    has_entries = bool(re.search(r'"[^"]+"', body))
    addition = f'\n\t\t"{asset}"' + ("," if has_entries else "")
    return text[: opening + 1] + addition + text[opening + 1 :]


def insert_lightmap_resolution_volume(text: str) -> str:
    """Clone the proven volume mesh as the arena's lightmap density control."""
    token = "lightmap-resolution"
    stable_id = uuid.uuid5(uuid.NAMESPACE_URL, f"trento-povo:{token}:0")
    if str(stable_id) in text:
        return text

    postprocess_blocks = [
        block
        for _, _, classname, block in _entity_ranges(text)
        if classname == "post_processing_volume"
    ]
    if len(postprocess_blocks) != 1:
        raise ProjectError(
            f"VMAP has {len(postprocess_blocks)} post-processing volumes; expected 1"
        )
    postprocess = postprocess_blocks[0]
    mesh_match = re.search(r'(?m)^[ \t]*"CMapMesh"[ \t]*$', postprocess)
    if not mesh_match:
        raise ProjectError("Post-processing volume has no CMapMesh child")
    mesh_opening = postprocess.find("{", mesh_match.end())
    mesh_closing = _matching_brace(postprocess, mesh_opening)
    mesh = postprocess[mesh_match.start() : mesh_closing + 1]
    if POSTPROCESS_VOLUME_MESH_MATERIAL not in mesh:
        raise ProjectError("Post-processing mesh does not use the expected material")

    id_index = 0

    def replace_id(_match: re.Match[str]) -> str:
        nonlocal id_index
        replacement = uuid.uuid5(
            uuid.NAMESPACE_URL, f"trento-povo:{token}:{id_index}"
        )
        id_index += 1
        return f'"id" "elementid" "{replacement}"'

    mesh = re.sub(r'"id"\s+"elementid"\s+"[^"]+"', replace_id, mesh)
    if id_index == 0:
        raise ProjectError("Post-processing mesh has no element IDs")
    node_ids = [int(value) for value in re.findall(r'"nodeID"\s+"int"\s+"(\d+)"', text)]
    mesh, node_count = re.subn(
        r'("nodeID"\s+"int"\s+")\d+("\s*)',
        rf'\g<1>{max(node_ids, default=1) + 1}\2',
        mesh,
        count=1,
    )
    if node_count != 1:
        raise ProjectError("Post-processing mesh has no nodeID")
    reference_id = stable_id.int & ((1 << 64) - 1)
    mesh, reference_count = re.subn(
        r'("referenceID"\s+"uint64"\s+")0x[0-9a-fA-F]+(")',
        rf'\g<1>0x{reference_id:x}\2',
        mesh,
        count=1,
    )
    if reference_count != 1:
        raise ProjectError("Post-processing mesh has no referenceID")
    mesh = mesh.replace(
        POSTPROCESS_VOLUME_MESH_MATERIAL, LIGHTMAP_RESOLUTION_MATERIAL
    )
    mesh = _replace_entity_transform(
        mesh,
        PLAYTEST_CENTER,
        angles="0 0 0",
        scales=PLAYTEST_POSTPROCESS_SCALES,
    )

    text = _ensure_map_asset_reference(text, LIGHTMAP_RESOLUTION_MATERIAL)
    children_open = _world_children_opening(text)
    insertion = "\n" + mesh + ","
    return text[: children_open + 1] + insertion + text[children_open + 1 :]


def _world_children_opening(text: str) -> int:
    world_at = text.find('"world" "CMapWorld"')
    if world_at < 0:
        raise ProjectError("VMAP has no CMapWorld")
    children_at = text.find('"children" "element_array"', world_at)
    if children_at < 0:
        raise ProjectError("CMapWorld has no children array")
    opening = text.find("[", children_at)
    _matching_bracket(text, opening)
    return opening


def _insert_point_entity(
    text: str,
    token: str,
    classname: str,
    origin: str,
    properties: tuple[tuple[str, str], ...] = (),
) -> str:
    """Insert one deterministic point entity unless its stable ID already exists."""
    entity_id = uuid.uuid5(uuid.NAMESPACE_URL, f"trento-povo:{token}")
    if str(entity_id) in text:
        return text
    relay_id = uuid.uuid5(uuid.NAMESPACE_URL, f"trento-povo:{token}:relay")
    properties_id = uuid.uuid5(uuid.NAMESPACE_URL, f"trento-povo:{token}:properties")
    reference_id = entity_id.int & ((1 << 64) - 1)
    node_ids = [int(value) for value in re.findall(r'"nodeID"\s+"int"\s+"(\d+)"', text)]
    node_id = max(node_ids, default=1) + 1
    rendered_properties = "".join(
        f'\n\t\t\t\t\t"{key}" "string" "{value}"' for key, value in properties
    )
    entity = f'''
\t\t\t"CMapEntity"
\t\t\t{{
\t\t\t\t"id" "elementid" "{entity_id}"
\t\t\t\t"nodeID" "int" "{node_id}"
\t\t\t\t"referenceID" "uint64" "0x{reference_id:x}"
\t\t\t\t"children" "element_array" [ ]
\t\t\t\t"variableTargetKeys" "string_array" [ ]
\t\t\t\t"variableNames" "string_array" [ ]
\t\t\t\t"relayPlugData" "DmePlugList"
\t\t\t\t{{
\t\t\t\t\t"id" "elementid" "{relay_id}"
\t\t\t\t\t"names" "string_array" [ ]
\t\t\t\t\t"dataTypes" "int_array" [ ]
\t\t\t\t\t"plugTypes" "int_array" [ ]
\t\t\t\t\t"descriptions" "string_array" [ ]
\t\t\t\t}}
\t\t\t\t"connectionsData" "element_array" [ ]
\t\t\t\t"entity_properties" "EditGameClassProps"
\t\t\t\t{{
\t\t\t\t\t"id" "elementid" "{properties_id}"
\t\t\t\t\t"classname" "string" "{classname}"{rendered_properties}
\t\t\t\t}}
\t\t\t\t"hitNormal" "vector3" "0 0 1"
\t\t\t\t"isProceduralEntity" "bool" "0"
\t\t\t\t"origin" "vector3" "{origin}"
\t\t\t\t"angles" "qangle" "0 0 0"
\t\t\t\t"scales" "vector3" "1 1 1"
\t\t\t\t"transformLocked" "bool" "0"
\t\t\t\t"force_hidden" "bool" "0"
\t\t\t\t"editorOnly" "bool" "0"
\t\t\t}},'''
    opening = _world_children_opening(text)
    return text[: opening + 1] + entity + text[opening + 1 :]


def insert_gameplay_support_entities(text: str) -> str:
    """Add navigation, light probes, sound, and radar bounds for the arena."""
    specs = (
        (
            "nav-seed",
            "point_nav_walkable",
            PLAYTEST_NAV_ORIGIN,
            (("vscripts", ""), ("targetname", "trento_nav_seed")),
        ),
        (
            "light-probe",
            "env_combined_light_probe_volume",
            PLAYTEST_CENTER,
            (
                ("targetname", "trento_light_probe"),
                ("vscripts", ""),
                ("StartDisabled", "0"),
                ("cubemaptexture", ""),
                ("bakenearz", "2.0"),
                ("bakefarz", "4096.0"),
                ("lightgroup", ""),
                ("moveable", "0"),
                ("lightprobetexture", ""),
                ("box_mins", "-2700 -650 -400"),
                ("box_maxs", "2700 650 700"),
                ("voxel_size", "64.0"),
                ("flood_fill", "1"),
                ("voxelize", "1"),
                ("light_probe_volume_from_cubemap", "0"),
                ("storage", "-1"),
                ("indoor_outdoor_level", "0"),
                ("edge_fade_dists", "0 32 0"),
                ("clientSideEntity", "1"),
            ),
        ),
        (
            "soundscape",
            "env_soundscape",
            PLAYTEST_CENTER,
            (
                ("vscripts", ""),
                ("targetname", "trento_outdoors"),
                ("StartDisabled", "0"),
                ("radius", "6000"),
                ("soundscape", "Nothing"),
                ("enablesoundevent", "1"),
                ("soundevent", "ambient_example.outdoors"),
            ),
        ),
        (
            "minimap-min",
            "cs_minimap_boundary",
            PLAYTEST_MINIMAP_CORNERS[0],
            (),
        ),
        (
            "minimap-max",
            "cs_minimap_boundary",
            PLAYTEST_MINIMAP_CORNERS[1],
            (),
        ),
    )
    for token, classname, origin, properties in specs:
        text = _insert_point_entity(text, token, classname, origin, properties)
    return text


def relocate_playtest_entities(text: str) -> str:
    """Move Wingman spawns, cameras, and volumes into the compact Povo arena."""
    entity_pattern = re.compile(r'(?m)^[ \t]*"CMapEntity"[ \t]*$')
    class_pattern = re.compile(r'"classname"\s+"string"\s+"([^"]+)"')
    team_pattern = re.compile(r'"TeamNum"\s+"string"\s+"([^"]+)"')
    spawn_indices = {classname: 0 for classname in PLAYTEST_SPAWNS}
    replacements: list[tuple[int, int, str]] = []
    objective_count = 0
    buyzone_teams: set[str] = set()

    for match in entity_pattern.finditer(text):
        opening = text.find("{", match.end())
        if opening < 0:
            raise ProjectError("VMAP entity has no opening brace")
        closing = _matching_brace(text, opening)
        block = text[match.start() : closing + 1]
        class_match = class_pattern.search(block)
        if not class_match:
            continue
        classname = class_match.group(1)
        updated = block

        if classname in PLAYTEST_SPAWNS:
            index = spawn_indices[classname]
            layout = PLAYTEST_SPAWNS[classname]
            if index >= len(layout):
                raise ProjectError(f"VMAP has too many {classname} entities")
            origin, angles = layout[index]
            updated = _replace_entity_transform(block, origin, angles)
            updated = re.sub(
                r'("targetname"\s+"string"\s+")spawnpoints\.2v2(")',
                r'\1\2',
                updated,
                count=1,
            )
            spawn_indices[classname] += 1
        elif classname == "func_bomb_target":
            updated = _replace_entity_transform(block, PLAYTEST_OBJECTIVE_ORIGIN)
            objective_count += 1
        elif classname == "func_buyzone":
            team_match = team_pattern.search(block)
            if team_match and team_match.group(1) in PLAYTEST_BUYZONE_ORIGINS:
                team = team_match.group(1)
                updated = _replace_entity_transform(
                    block, PLAYTEST_BUYZONE_ORIGINS[team]
                )
                buyzone_teams.add(team)
        elif classname == "counterterrorist_wingman_intro":
            updated = _replace_entity_transform(
                block, PLAYTEST_BUYZONE_ORIGINS["3"], "0 180 0"
            )
        elif classname == "terrorist_wingman_intro":
            updated = _replace_entity_transform(
                block, PLAYTEST_BUYZONE_ORIGINS["2"], "0 0 0"
            )
        elif classname == "end_of_match":
            updated = _replace_entity_transform(
                block, PLAYTEST_OBJECTIVE_ORIGIN, "0 90 0"
            )

        if updated != block:
            replacements.append((match.start(), closing + 1, updated))

    for classname, layout in PLAYTEST_SPAWNS.items():
        if spawn_indices[classname] != len(layout):
            raise ProjectError(
                f"VMAP has {spawn_indices[classname]} {classname} entities; "
                f"expected {len(layout)}"
            )
    if objective_count != 1:
        raise ProjectError(f"VMAP has {objective_count} bomb targets; expected 1")
    missing_buyzones = set(PLAYTEST_BUYZONE_ORIGINS) - buyzone_teams
    if missing_buyzones:
        rendered = ", ".join(sorted(missing_buyzones))
        raise ProjectError(f"VMAP is missing buy zones for team values: {rendered}")

    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text


def insert_blockout_prop(text: str, model: str = BLOCKOUT_MODEL) -> str:
    """Insert the Povo prop_static into a keyvalues2 VMAP document."""
    if f'"model" "string" "{model}"' in text:
        return text

    asset_label = '"map_asset_references" "string_array"'
    asset_label_at = text.find(asset_label)
    if asset_label_at < 0:
        raise ProjectError("VMAP has no map_asset_references array")
    asset_open = text.find("[", asset_label_at)
    _matching_bracket(text, asset_open)
    text = text[: asset_open + 1] + f'\n\t\t"{model}",' + text[asset_open + 1 :]

    world_at = text.find('"world" "CMapWorld"')
    if world_at < 0:
        raise ProjectError("VMAP has no CMapWorld")
    children_at = text.find('"children" "element_array"', world_at)
    if children_at < 0:
        raise ProjectError("CMapWorld has no children array")
    children_open = text.find("[", children_at)
    _matching_bracket(text, children_open)

    node_ids = [int(value) for value in re.findall(r'"nodeID"\s+"int"\s+"(\d+)"', text)]
    node_id = max(node_ids, default=1) + 1
    entity_id = uuid.uuid5(uuid.NAMESPACE_URL, "trento-povo:blockout-prop")
    relay_id = uuid.uuid5(uuid.NAMESPACE_URL, "trento-povo:blockout-relay")
    properties_id = uuid.uuid5(uuid.NAMESPACE_URL, "trento-povo:blockout-properties")
    reference_id = entity_id.int & ((1 << 64) - 1)
    entity = f'''
\t\t\t"CMapEntity"
\t\t\t{{
\t\t\t\t"id" "elementid" "{entity_id}"
\t\t\t\t"nodeID" "int" "{node_id}"
\t\t\t\t"referenceID" "uint64" "0x{reference_id:x}"
\t\t\t\t"children" "element_array"
\t\t\t\t[
\t\t\t\t]
\t\t\t\t"variableTargetKeys" "string_array"
\t\t\t\t[
\t\t\t\t]
\t\t\t\t"variableNames" "string_array"
\t\t\t\t[
\t\t\t\t]
\t\t\t\t"relayPlugData" "DmePlugList"
\t\t\t\t{{
\t\t\t\t\t"id" "elementid" "{relay_id}"
\t\t\t\t\t"names" "string_array" [ ]
\t\t\t\t\t"dataTypes" "int_array" [ ]
\t\t\t\t\t"plugTypes" "int_array" [ ]
\t\t\t\t\t"descriptions" "string_array" [ ]
\t\t\t\t}}
\t\t\t\t"connectionsData" "element_array"
\t\t\t\t[
\t\t\t\t]
\t\t\t\t"entity_properties" "EditGameClassProps"
\t\t\t\t{{
\t\t\t\t\t"id" "elementid" "{properties_id}"
\t\t\t\t\t"classname" "string" "prop_static"
\t\t\t\t\t"targetname" "string" "povo_geographic_blockout"
\t\t\t\t\t"model" "string" "{model}"
\t\t\t\t\t"solid" "string" "6"
\t\t\t\t\t"disableshadows" "string" "0"
\t\t\t\t\t"screenspacefade" "string" "0"
\t\t\t\t\t"skin" "string" "default"
\t\t\t\t\t"lodlevel" "string" "-1"
\t\t\t\t\t"fademindist" "string" "-1"
\t\t\t\t\t"fademaxdist" "string" "0"
\t\t\t\t\t"fadescale" "string" "1"
\t\t\t\t\t"detailgeometry" "string" "0"
\t\t\t\t\t"visoccluder" "string" "0"
\t\t\t\t\t"baketoworld" "string" "0"
\t\t\t\t\t"renderamt" "string" "255"
\t\t\t\t\t"rendercolor" "string" "255 255 255"
\t\t\t\t\t"lightingorigin" "string" ""
\t\t\t\t\t"lightgroup" "string" ""
\t\t\t\t\t"rendertocubemaps" "string" "1"
\t\t\t\t\t"precomputelightprobes" "string" "1"
\t\t\t\t\t"materialoverride" "string" ""
\t\t\t\t\t"disableinlowquality" "string" "0"
\t\t\t\t\t"lightmapscalebias" "string" "0"
\t\t\t\t\t"bakelighting" "string" "-1"
\t\t\t\t\t"renderwithdynamic" "string" "0"
\t\t\t\t}}
\t\t\t\t"hitNormal" "vector3" "0 0 1"
\t\t\t\t"isProceduralEntity" "bool" "0"
\t\t\t\t"origin" "vector3" "0 0 0"
\t\t\t\t"angles" "qangle" "{BLOCKOUT_ANGLES}"
\t\t\t\t"scales" "vector3" "1 1 1"
\t\t\t\t"transformLocked" "bool" "0"
\t\t\t\t"force_hidden" "bool" "0"
\t\t\t\t"editorOnly" "bool" "0"
\t\t\t}},'''
    return text[: children_open + 1] + entity + text[children_open + 1 :]


def place_blockout(cs2_root: Path, repo_root: Path = REPO_ROOT) -> bool:
    """Round-trip the VMAP and prepare the geographic first-playable layout."""
    converter = cs2_root / "game" / "bin" / "win64" / "dmxconvert.exe"
    source_map = (
        repo_root / "cs2" / "content" / ADDON_NAME / "maps" / "trento_povo.vmap"
    )
    if not converter.is_file():
        raise ProjectError(f"DMX converter is missing: {converter}")
    if not source_map.is_file():
        raise ProjectError(f"Source map is missing: {source_map}")

    with tempfile.TemporaryDirectory(prefix="trento-vmap-") as temporary:
        temporary_root = Path(temporary)
        text_map = temporary_root / "trento_povo_text.vmap"
        binary_map = temporary_root / "trento_povo_binary.vmap"
        to_text = subprocess.run(
            [
                str(converter),
                "-i",
                str(source_map),
                "-o",
                str(text_map),
                "-oe",
                "keyvalues2",
                "-of",
                "vmap",
            ],
            check=False,
        )
        if to_text.returncode:
            raise ProjectError("dmxconvert could not decode the source VMAP")
        original = text_map.read_text(encoding="utf-8")
        updated = insert_blockout_prop(original)
        updated = normalize_template_buyzones(updated)
        updated = relocate_playtest_entities(updated)
        updated = remove_template_placeholders(updated)
        updated = configure_playtest_environment(updated)
        updated = insert_lightmap_resolution_volume(updated)
        updated = insert_gameplay_support_entities(updated)
        if updated == original:
            return False
        text_map.write_text(updated, encoding="utf-8", newline="\n")
        to_binary = subprocess.run(
            [
                str(converter),
                "-i",
                str(text_map),
                "-o",
                str(binary_map),
                "-oe",
                "binary",
                "-of",
                "vmap",
            ],
            check=False,
        )
        if to_binary.returncode or not binary_map.is_file():
            raise ProjectError("dmxconvert could not encode the updated VMAP")
        shutil.copy2(binary_map, source_map)
    return True


def doctor(repo_root: Path = REPO_ROOT, cs2_root: Path | None = None) -> int:
    required = [
        repo_root / "config" / "povo_blockout.json",
        repo_root / "exports" / "povo_blockout" / "povo_blockout.obj",
        repo_root / "cs2" / "content" / ADDON_NAME / "maps" / "trento_povo.vmap",
        repo_root
        / "cs2"
        / "content"
        / ADDON_NAME
        / "models"
        / "povo"
        / "povo_blockout.vmdl",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    print(f"Platform: {platform.platform()}")
    print(f"Python:   {platform.python_version()}")
    print(f"Repo:     {repo_root.resolve()}")
    print(f"Sources:  {'ready' if not missing else 'incomplete'}")
    for name in ("blender", "qgis", "gdalinfo"):
        print(f"{name + ':':9} {shutil.which(name) or 'not on PATH (optional here)'}")

    try:
        installed = discover_cs2_root(cs2_root)
    except ProjectError as error:
        installed = None
        print(f"CS2:      unavailable ({error})")
    else:
        print(f"CS2:      {installed}")
        print(
            "Compiler: "
            + str(installed / "game" / "bin" / "win64" / "resourcecompiler.exe")
        )
    if missing:
        for path in missing:
            print(f"Missing:  {path}")
        return 1
    return 0


def compile_resources(cs2_root: Path, target: str) -> int:
    content_target, _ = _installed_targets(cs2_root)
    compiler = cs2_root / "game" / "bin" / "win64" / "resourcecompiler.exe"
    game_directory = cs2_root / "game" / "csgo"
    resources: list[Path] = []
    # The map compiler consumes the last compiled VMDL and does not reliably
    # rebuild a changed ModelDoc dependency. Always refresh it before a map.
    if target in ("model", "map", "all"):
        resources.append(content_target / "models" / "povo" / "povo_blockout.vmdl")
    if target in ("map", "all"):
        resources.append(content_target / "maps" / "trento_povo.vmap")

    for resource in resources:
        if not resource.is_file():
            raise ProjectError(f"Deploy before compiling; missing {resource}")
        command = [
            str(compiler),
            "-nop4",
            "-fshallow2",
            "-game",
            str(game_directory),
            "-i",
            str(resource),
        ]
        print("Compiling " + str(resource))
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            return completed.returncode
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cs2-root",
        help="CS2 installation root; otherwise use CS2_ROOT/Steam discovery",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check cross-platform and Windows tools")
    deploy_parser = subparsers.add_parser(
        "deploy", help="copy repository sources into the installed addon"
    )
    deploy_parser.add_argument("--dry-run", action="store_true")
    compile_parser = subparsers.add_parser(
        "compile", help="deploy and compile Source 2 resources"
    )
    compile_parser.add_argument(
        "--target", choices=("model", "map", "all"), default="all"
    )
    compile_parser.add_argument(
        "--no-deploy", action="store_true", help="compile the installed copy as-is"
    )
    subparsers.add_parser(
        "place-blockout",
        help="insert Povo and place the Wingman entities on sampled campus terrain",
    )
    sync_parser = subparsers.add_parser(
        "sync-from-cs2", help="copy Hammer/ModelDoc source edits back into Git"
    )
    sync_parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            explicit = Path(args.cs2_root) if args.cs2_root else None
            return doctor(cs2_root=explicit)
        cs2_root = discover_cs2_root(args.cs2_root)
        if args.command == "deploy":
            _print_records(deploy(cs2_root, dry_run=args.dry_run))
            return 0
        if args.command == "sync-from-cs2":
            _print_records(sync_from_cs2(cs2_root, dry_run=args.dry_run))
            return 0
        if args.command == "place-blockout":
            changed = place_blockout(cs2_root)
            print("updated  trento_povo.vmap" if changed else "unchanged  trento_povo.vmap")
            return 0
        if args.command == "compile":
            if not args.no_deploy:
                _print_records(deploy(cs2_root))
            return compile_resources(cs2_root, args.target)
    except ProjectError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

