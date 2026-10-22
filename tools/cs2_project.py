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
    """Round-trip the binary VMAP and add the geographic model deterministically."""
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
    if target in ("model", "all"):
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
        help="insert the compiled Povo geographic model into the Wingman source map",
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

