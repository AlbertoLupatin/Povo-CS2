#!/usr/bin/env python3
"""Build a local-metre Povo reference OBJ, not a compiled or playable CS2 map."""

import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile

try:
    from .asc_to_obj import Grid, finite, read_grid, write_mesh
except ImportError:  # Direct invocation: python3 tools/build_povo_blockout.py
    from asc_to_obj import Grid, finite, read_grid, write_mesh


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILES = ("povo_blockout.obj", "povo_blockout.mtl", "orthophoto_reference.png", "provenance.json", "CREDITS.txt")
CALIBRATION_MINIMUM = (-120.0, -170.0, 0.0)


def numbers(value, length, label):
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError(f"{label} must contain {length} numbers")
    return tuple(finite(v, label) for v in value)


def bounds(value, label):
    west, south, east, north = numbers(value, 4, label)
    if not west < east or not south < north:
        raise ValueError(f"{label} must be ordered west, south, east, north with positive area")
    if not all(math.isfinite(v) for v in (east - west, north - south)):
        raise ValueError(f"{label} extent overflow")
    return west, south, east, north


def contains(outer, inner):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object")
    required = {"origin", "horizontal_crs_label", "vertical_datum", "terrain_bounds",
                "sampling_step", "dtm", "dbm", "orthophoto", "orthophoto_bounds", "buildings"}
    missing = required - config.keys()
    if missing:
        raise ValueError("Missing configuration keys: " + ", ".join(sorted(missing)))
    config = dict(config)
    config["origin"] = numbers(config["origin"], 3, "origin")
    for key in ("horizontal_crs_label", "vertical_datum", "dtm", "dbm", "orthophoto"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f"{key} must be nonempty text")
    step = config["sampling_step"]
    if type(step) is not int or step < 1:
        raise ValueError("sampling_step must be a positive integer")
    config["terrain_bounds"] = bounds(config["terrain_bounds"], "terrain_bounds")
    config["orthophoto_bounds"] = bounds(config["orthophoto_bounds"], "orthophoto_bounds")
    if not contains(config["orthophoto_bounds"], config["terrain_bounds"]):
        raise ValueError("orthophoto_bounds must contain terrain_bounds")
    if not isinstance(config["buildings"], list):
        raise ValueError("buildings must be a list")
    seen = {"terrain", "calibration_1m"}
    buildings = []
    for entry in config["buildings"]:
        if not isinstance(entry, dict) or not {"id", "bounds", "base_elevation", "roof_elevation", "evidence"} <= entry.keys():
            raise ValueError("Each building needs id, bounds, base_elevation, roof_elevation, evidence")
        entry = dict(entry)
        identifier = entry["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", identifier) or identifier in seen:
            raise ValueError("Building IDs must be unique safe OBJ names, excluding terrain and calibration_1m")
        seen.add(identifier)
        entry["bounds"] = bounds(entry["bounds"], f"{identifier} bounds")
        if not contains(config["terrain_bounds"], entry["bounds"]):
            raise ValueError(f"{identifier} bounds must fit inside terrain_bounds")
        entry["base_elevation"] = finite(entry["base_elevation"], f"{identifier} base_elevation")
        entry["roof_elevation"] = finite(entry["roof_elevation"], f"{identifier} roof_elevation")
        if entry["base_elevation"] >= entry["roof_elevation"]:
            raise ValueError(f"{identifier} base_elevation must be below roof_elevation")
        if not isinstance(entry["evidence"], str) or not entry["evidence"].strip():
            raise ValueError(f"{identifier} evidence must be nonempty text")
        buildings.append(entry)
    config["buildings"] = buildings
    return config


def grid_bounds(grid, *, cell_edges=False):
    shift = grid.cellsize / 2 if cell_edges else 0
    extent = (grid.x_center - shift, grid.y_center - shift,
              grid.x_center + (grid.cols - 1) * grid.cellsize + shift,
              grid.y_center + (grid.rows - 1) * grid.cellsize + shift)
    return bounds(extent, "Source grid extent")


def check_alignment(dtm, dbm):
    if (dtm.cols, dtm.rows) != (dbm.cols, dbm.rows) or any(
        not math.isclose(a, b, rel_tol=0, abs_tol=1e-8)
        for a, b in ((dtm.x_center, dbm.x_center), (dtm.y_center, dbm.y_center), (dtm.cellsize, dbm.cellsize))
    ):
        raise ValueError("DTM and DBM grids must have identical dimensions, resolution and sample centres")
    for grid in (dtm, dbm):
        grid_bounds(grid)
        grid_bounds(grid, cell_edges=True)


def crop_grid(grid, requested_bounds):
    """Select existing centres inside the requested bounds, without resampling."""
    if not contains(grid_bounds(grid, cell_edges=True), requested_bounds):
        raise ValueError("terrain_bounds extend outside the source grid")
    west, south, east, north = requested_bounds
    columns = [c for c in range(grid.cols) if west <= grid.x_center + c * grid.cellsize <= east]
    rows = [r for r in range(grid.rows)
            if south <= grid.y_center + (grid.rows - 1 - r) * grid.cellsize <= north]
    if len(rows) < 2 or len(columns) < 2:
        raise ValueError("terrain_bounds must contain at least two sample rows and columns")
    data = array("d")
    for row in rows:
        data.extend(grid.values[row * grid.cols + columns[0]:row * grid.cols + columns[-1] + 1])
    return Grid(len(columns), len(rows), grid.x_center + columns[0] * grid.cellsize,
                grid.y_center + (grid.rows - 1 - rows[-1]) * grid.cellsize,
                grid.cellsize, grid.nodata, data, grid.sha256)


class TexturedTerrainWriter:
    """Add georeferenced OBJ UVs while retaining asc_to_obj's topology and NoData rules."""

    def __init__(self, stream, origin, image_bounds):
        self.stream, self.origin, self.image_bounds = stream, origin, image_bounds
        self.minimum = [math.inf] * 3
        self.maximum = [-math.inf] * 3

    def write(self, line):
        if line.startswith("v "):
            vertex = tuple(map(float, line.split()[1:]))
            for axis in range(3):
                self.minimum[axis] = min(self.minimum[axis], vertex[axis])
                self.maximum[axis] = max(self.maximum[axis], vertex[axis])
            west, south, east, north = self.image_bounds
            u = (vertex[0] + self.origin[0] - west) / (east - west)
            v = (vertex[1] + self.origin[1] - south) / (north - south)
            self.stream.write(line)
            self.stream.write(f"vt {u:.12g} {v:.12g}\n")
        elif line.startswith("f "):
            self.stream.write("f " + " ".join(f"{index}/{index}" for index in line.split()[1:]) + "\n")
        else:
            self.stream.write(line)


def write_box(stream, identifier, minimum, maximum, vertex_offset, material="building_mass"):
    """Write eight shared vertices and twelve outward-facing triangles."""
    if not all(math.isfinite(v) for v in (*minimum, *maximum)) or any(a >= b for a, b in zip(minimum, maximum)):
        raise ValueError(f"Invalid local box extent for {identifier}; check coordinate origins")
    x0, y0, z0 = minimum
    x1, y1, z1 = maximum
    vertices = ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
    triangles = ((1, 3, 2), (1, 4, 3), (5, 6, 7), (5, 7, 8),
                 (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6),
                 (3, 4, 8), (3, 8, 7), (4, 1, 5), (4, 5, 8))
    stream.write(f"o {identifier}\nusemtl {material}\ns off\n")
    for vertex in vertices:
        stream.write("v " + " ".join(f"{value:.12g}" for value in vertex) + "\n")
    for triangle in triangles:
        stream.write("f " + " ".join(str(vertex_offset + value) for value in triangle) + "\n")
    return 8, 12


def safe_path(path, root):
    """Record project paths without exposing a workstation home directory."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def raster_record(path, grid, root):
    return {"path": safe_path(path, root), "sha256": grid.sha256,
            "columns": grid.cols, "rows": grid.rows, "resolution_metres": grid.cellsize,
            "sample_center_bounds": grid_bounds(grid), "cell_edge_bounds": grid_bounds(grid, cell_edges=True),
            "nodata_value": grid.nodata}


def build_blockout(config_path, output, *, root=None, force=False):
    config_path, output = Path(config_path), Path(output)
    root = Path(root) if root is not None else config_path.resolve().parent.parent
    if os.path.lexists(output) and not force:
        raise ValueError(f"Output directory exists: {output}; use --force to replace generated files")
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError("Output must be a directory, not a file or symlink")
    raw_config = config_path.read_bytes()
    config = validate_config(json.loads(raw_config))
    sources = {key: root / config[key] for key in ("dtm", "dbm", "orthophoto")}
    targets = {(output / name).resolve() for name in OUTPUT_FILES}
    if any(path.resolve() in targets for path in (*sources.values(), config_path)):
        raise ValueError("Generated files must not replace inputs")
    if any((output / name).is_dir() for name in OUTPUT_FILES):
        raise ValueError("A generated filename is occupied by a directory")
    dtm, dbm = read_grid(sources["dtm"]), read_grid(sources["dbm"])
    check_alignment(dtm, dbm)
    terrain = crop_grid(dtm, config["terrain_bounds"])
    image_bytes = sources["orthophoto"].read_bytes()
    if len(image_bytes) < 24 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n" or image_bytes[12:16] != b"IHDR":
        raise ValueError("orthophoto must be a PNG image with an IHDR header")
    width, height = struct.unpack(">II", image_bytes[16:24])
    if not width or not height:
        raise ValueError("orthophoto dimensions must be positive")
    origin = config["origin"]
    metadata = {
        "format_version": 1,
        "title": config.get("title", "Povo - Polo Ferrari geographic blockout"),
        "status": "Intermediate geographic reference mesh; not compiled, playable, or game validated",
        "config": {"path": safe_path(config_path, root), "sha256": hashlib.sha256(raw_config).hexdigest()},
        "sources": {"dtm": raster_record(sources["dtm"], dtm, root),
                    "dbm": raster_record(sources["dbm"], dbm, root),
                    "orthophoto": {"path": safe_path(sources["orthophoto"], root),
                                   "sha256": hashlib.sha256(image_bytes).hexdigest(),
                                   "pixel_dimensions": [width, height], "bounds": config["orthophoto_bounds"],
                                   "output_copy": "orthophoto_reference.png"}},
        "coordinate_transform": {
            "declared_horizontal_crs": config["horizontal_crs_label"],
            "declared_vertical_datum": config["vertical_datum"],
            "declarations_verified_by_builder": False, "units": "metres", "origin": origin,
            "axes": {"x": "east", "y": "north", "z": "up"},
            "formula": "local = source - origin; no reprojection, scaling, rotation, or datum conversion",
        },
        "terrain": {"requested_bounds": config["terrain_bounds"],
                    "cropped_sample_center_bounds": grid_bounds(terrain),
                    "cropped_columns": terrain.cols, "cropped_rows": terrain.rows,
                    "sampling_step": config["sampling_step"],
                    "nominal_mesh_spacing_metres": terrain.cellsize * config["sampling_step"],
                    "boundary_rule": "Keep all outer sample rows and columns; last interval may be shorter",
                    "uv_formula": "u=(easting-west)/(east-west); v=(northing-south)/(north-south), using full orthophoto bounds",
                    "uv_orientation": "OBJ v=0 south / image bottom; v=1 north / image top"},
        "building_modules": config["buildings"],
        "calibration": {"object": "calibration_1m", "local_minimum": CALIBRATION_MINIMUM,
                        "dimensions_metres": [1, 1, 1],
                        "purpose": "Staging-only scale check outside the campus; delete before game packaging"},
        "attribution": config.get("attribution", "Preserve original source credits and licences in docs/DATA_SOURCES.md"),
        "config_note": config.get("note", ""),
        "limitations": [
            "Rectangular building modules are approximate volumes, not surveyed footprints or architectural models.",
            "Roof elevations and buried bases come from explicit configuration; DBM is checked for grid alignment, not automatically interpreted.",
            "The orthophoto is a reference overlay: aerial roofs remain visible on underlying ground; this is not a finished ground texture.",
            "Outer cell edges are not mesh vertices. NoData triangles and coarse quads spanning hidden NoData are omitted.",
            "DTM decimation cannot establish walkable steps, ramps, entrances, or retaining-wall geometry.",
            "No interiors, collision setup, player clipping, navigation, lighting bake, CS2 entities, or compiled map are provided.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".povo-blockout-", dir=output.parent) as temporary:
        staged = Path(temporary)
        with (staged / OUTPUT_FILES[0]).open("w", encoding="utf-8") as stream:
            stream.write("# Povo reference blockout. Metres: east X, north Y, up Z. See provenance.json.\n")
            stream.write("mtllib povo_blockout.mtl\no terrain\nusemtl terrain_reference\ns off\n")
            textured = TexturedTerrainWriter(stream, origin, config["orthophoto_bounds"])
            terrain_stats = write_mesh(textured, terrain, origin, config["sampling_step"])
            metadata["terrain"]["statistics"] = terrain_stats
            metadata["terrain"]["sampled_local_bounds"] = [textured.minimum, textured.maximum]
            metadata["terrain"]["sampled_source_bounds"] = [
                [value + origin[axis] for axis, value in enumerate(extent)]
                for extent in (textured.minimum, textured.maximum)]
            vertices, triangles = terrain_stats["vertices"], terrain_stats["triangles"]
            for building in config["buildings"]:
                west, south, east, north = building["bounds"]
                minimum = (west - origin[0], south - origin[1], building["base_elevation"] - origin[2])
                maximum = (east - origin[0], north - origin[1], building["roof_elevation"] - origin[2])
                added_vertices, added_triangles = write_box(stream, building["id"], minimum, maximum, vertices)
                vertices += added_vertices
                triangles += added_triangles
            added_vertices, added_triangles = write_box(stream, "calibration_1m", CALIBRATION_MINIMUM,
                                                        tuple(value + 1 for value in CALIBRATION_MINIMUM),
                                                        vertices, material="calibration")
            metadata["statistics"] = {"vertices": vertices + added_vertices, "triangles": triangles + added_triangles,
                                      "building_modules": len(config["buildings"]), "objects": len(config["buildings"]) + 2}
        (staged / OUTPUT_FILES[1]).write_text(
            "# Neutral massing and orthophoto reference material; no game material definitions.\n"
            "newmtl terrain_reference\nKa 0.2 0.2 0.2\nKd 1 1 1\nKs 0 0 0\nillum 1\nmap_Kd orthophoto_reference.png\n\n"
            "newmtl building_mass\nKa 0.2 0.2 0.2\nKd 0.65 0.63 0.59\nKs 0 0 0\nillum 1\n\n"
            "newmtl calibration\nKa 0.2 0.2 0.2\nKd 0.75 0.45 0.18\nKs 0 0 0\nillum 1\n", encoding="utf-8")
        (staged / OUTPUT_FILES[2]).write_bytes(image_bytes)
        (staged / "CREDITS.txt").write_text(
            "Povo - Polo Ferrari geographic blockout\n\n"
            "Source attribution and licences:\n" + json.dumps(metadata["attribution"], indent=2, ensure_ascii=False) + "\n\n"
            "Changes: DTM cropped and decimated to a local-metre terrain mesh; orthophoto copied intact and UV-mapped; "
            "approximate rectangular building volumes added using configured roof elevations and assumed bases. "
            "No interiors or playable CS2 map included. Original evidence and hashes: provenance.json.\n",
            encoding="utf-8")
        metadata["artifacts"] = {name: {"sha256": hashlib.sha256((staged / name).read_bytes()).hexdigest(),
                                        "bytes": (staged / name).stat().st_size} for name in OUTPUT_FILES if name != "provenance.json"}
        (staged / OUTPUT_FILES[3]).write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        # All source parsing and geometry validation finish before generated files are published.
        output.mkdir(exist_ok=force)
        for name in OUTPUT_FILES:
            os.replace(staged / name, output / name)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config/povo_blockout.json")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "exports/povo_blockout")
    parser.add_argument("--root", type=Path, help="Base directory for input paths; default: config parent directory's parent")
    parser.add_argument("--force", action="store_true", help="Replace generated files in an existing output directory")
    args = parser.parse_args()
    try:
        metadata = build_blockout(args.config, args.output, root=args.root, force=args.force)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    stats = metadata["statistics"]
    print(f"Wrote {args.output}: {stats['vertices']} vertices, {stats['triangles']} triangles, "
          f"{stats['building_modules']} approximate building modules; CS2 import and validation pending")


if __name__ == "__main__":
    main()
