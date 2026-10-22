#!/usr/bin/env python3
"""Convert a clipped ESRI ASCII DTM to a local-metre OBJ; standard library only."""

import argparse
from array import array
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile


MAX_CELLS = 4_000_000  # Clip the source to a small area before exporting.
HEADER_KEYS = {
    "ncols", "nrows", "xllcorner", "yllcorner", "xllcenter", "yllcenter",
    "cellsize", "nodata_value",
}


@dataclass
class Grid:
    cols: int
    rows: int
    x_center: float
    y_center: float
    cellsize: float
    nodata: float | None
    values: array
    sha256: str

    def missing(self, row, col):
        return self.nodata is not None and self.values[row * self.cols + col] == self.nodata


def finite(value, label):
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def parse_header(header):
    required = {"ncols", "nrows", "cellsize"}
    if not required <= header.keys():
        raise ValueError("Missing ncols, nrows, or cellsize header")
    try:
        cols, rows = int(header["ncols"]), int(header["nrows"])
    except ValueError as exc:
        raise ValueError("ncols and nrows must be integers") from exc
    if cols < 2 or rows < 2:
        raise ValueError("A terrain mesh requires at least 2 columns and 2 rows")
    if cols * rows > MAX_CELLS:
        raise ValueError(f"Grid exceeds {MAX_CELLS:,} cells; clip the source area first")
    cellsize = finite(header["cellsize"], "cellsize")
    if cellsize <= 0:
        raise ValueError("cellsize must be positive")
    coordinate_keys = header.keys() & {"xllcorner", "yllcorner", "xllcenter", "yllcenter"}
    if coordinate_keys == {"xllcorner", "yllcorner"}:
        xkey, ykey, shift = "xllcorner", "yllcorner", cellsize / 2
    elif coordinate_keys == {"xllcenter", "yllcenter"}:
        xkey, ykey, shift = "xllcenter", "yllcenter", 0
    else:
        raise ValueError("Use exactly xllcorner/yllcorner OR xllcenter/yllcenter")
    x = finite(header[xkey], xkey) + shift
    y = finite(header[ykey], ykey) + shift
    nodata = finite(header["nodata_value"], "NODATA_value") if "nodata_value" in header else None
    return cols, rows, x, y, cellsize, nodata


def read_grid(path):
    header, values, dimensions = {}, array("d"), None
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            fields = raw_line.decode("utf-8-sig" if line_number == 1 else "utf-8").split()
            if not fields:
                continue
            key = fields[0].lower()
            if dimensions is None and key in HEADER_KEYS:
                if len(fields) != 2 or key in header:
                    raise ValueError(f"Invalid or duplicate header on line {line_number}")
                header[key] = fields[1]
                continue
            if dimensions is None:
                dimensions = parse_header(header)
            for field in fields:
                if len(values) >= dimensions[0] * dimensions[1]:
                    raise ValueError("More samples than ncols × nrows")
                values.append(finite(field, f"Sample on line {line_number}"))
    dimensions = dimensions or parse_header(header)
    if len(values) != dimensions[0] * dimensions[1]:
        raise ValueError(f"Expected {dimensions[0] * dimensions[1]} samples, found {len(values)}")
    return Grid(*dimensions, values, digest.hexdigest())


def sample_indices(length, step):
    selected = list(range(0, length, step))
    if selected[-1] != length - 1:
        selected.append(length - 1)
    return selected


def write_mesh(stream, grid, origin, step):
    rows, cols = sample_indices(grid.rows, step), sample_indices(grid.cols, step)
    vertex_ids = array("I", [0]) * (grid.rows * grid.cols)
    vertices = faces = skipped = 0
    stream.write("# Local metres: X east, Y north, Z up. See companion JSON.\n")
    for row in rows:
        for col in cols:
            if grid.missing(row, col):
                continue
            x = grid.x_center + col * grid.cellsize - origin[0]
            y = grid.y_center + (grid.rows - 1 - row) * grid.cellsize - origin[1]
            z = grid.values[row * grid.cols + col] - origin[2]
            # Overflow is possible even for finite input values and origins.
            if not all(math.isfinite(v) for v in (x, y, z)):
                raise ValueError("Local coordinate overflow; check source units and origins")
            vertices += 1
            vertex_ids[row * grid.cols + col] = vertices
            stream.write(f"v {x:.12g} {y:.12g} {z:.12g}\n")
    for north, south in zip(rows, rows[1:]):
        for west, east in zip(cols, cols[1:]):
            corners = {(north, west), (north, east), (south, west), (south, east)}
            # A coarse triangle must not conceal holes at discarded samples.
            hidden_hole = step > 1 and any(
                grid.missing(r, c)
                for r in range(north, south + 1) for c in range(west, east + 1)
                if (r, c) not in corners
            )
            nw, ne, sw, se = [vertex_ids[r * grid.cols + c] for r, c in
                              ((north, west), (north, east), (south, west), (south, east))]
            for triangle in ((nw, sw, se), (nw, se, ne)):
                if hidden_hole or not all(triangle):
                    skipped += 1
                    continue
                stream.write("f " + " ".join(map(str, triangle)) + "\n")
                faces += 1
    if not faces:
        raise ValueError("No valid terrain triangles remain")
    return {"vertices": vertices, "triangles": faces, "skipped_triangles": skipped,
            "sampled_rows": len(rows), "sampled_columns": len(cols)}


def export(source, output, *, origin, step, crs, vertical_datum, force=False):
    source, output = Path(source), Path(output)
    if output.suffix.lower() != ".obj":
        raise ValueError("Output filename must end in .obj")
    sidecar = output.with_suffix(".json")
    if source.resolve() in {output.resolve(), sidecar.resolve()}:
        raise ValueError("Output paths must not replace the input")
    if not isinstance(step, int) or step < 1:
        raise ValueError("step must be a positive integer")
    if len(origin) != 3:
        raise ValueError("Provide easting, northing, and elevation origins")
    origin = tuple(finite(v, "Origin") for v in origin)
    if not crs.strip() or not vertical_datum.strip():
        raise ValueError("CRS and vertical-datum metadata must be nonempty")
    for path in (output, sidecar):
        if not force and os.path.lexists(path):
            raise ValueError(f"Output exists: {path}; use --force to replace both outputs")
        if path.is_dir():
            raise ValueError(f"Output is a directory: {path}")
    grid = read_grid(source)
    metadata = {
        "format_version": 1,
        "source": {"path": str(source.resolve()), "sha256": grid.sha256,
                   "columns": grid.cols, "rows": grid.rows, "cellsize": grid.cellsize,
                   "nodata_value": grid.nodata},
        "coordinate_transform": {
            "declared_crs": crs, "declared_vertical_datum": vertical_datum,
            "declarations_verified": False, "units": "metres",
            "origin_easting": origin[0], "origin_northing": origin[1],
            "origin_elevation": origin[2], "axes": {"x": "east", "y": "north", "z": "up"},
            "formula": "local = source - origin; no reprojection, scaling, or datum conversion",
            "southwest_sample_center": [grid.x_center, grid.y_center],
            "first_data_row": "north", "sampling": "cell centres", "step": step,
        },
        "accuracy_notes": [
            "CRS, vertical datum, and metre units are user declarations, not verified by this tool.",
            "Mesh accuracy is limited by the source DTM; interpolation adds no surveyed detail.",
            "Decimation preserves outer sample rows/columns, not the outer cell edges.",
            "Triangles touching NoData are omitted; coarse quads spanning discarded NoData are omitted.",
            "No skirts, collision, materials, UVs, game-unit conversion, or CS2 compilation are provided.",
        ],
    }
    temporary = []
    try:
        # Stage both artifacts so all parsing and coordinate validation precedes publication.
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent,
                                         prefix=".terrain-", delete=False) as mesh:
            temporary.append(Path(mesh.name))
            metadata["statistics"] = write_mesh(mesh, grid, origin, step)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent,
                                         prefix=".terrain-", delete=False) as record:
            temporary.append(Path(record.name))
            json.dump(metadata, record, indent=2, allow_nan=False)
            record.write("\n")
        for staged, target in zip(temporary, (output, sidecar)):
            if force:
                os.replace(staged, target)
            else:
                os.link(staged, target)  # Exclusive publication; never overwrite a race winner.
    finally:
        for staged in temporary:
            staged.unlink(missing_ok=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Clipped ESRI ASCII grid with metre coordinates/elevations")
    parser.add_argument("output", type=Path, help="Output .obj; companion .json is also written")
    parser.add_argument("--origin-easting", type=float, required=True)
    parser.add_argument("--origin-northing", type=float, required=True)
    parser.add_argument("--origin-elevation", type=float, required=True)
    parser.add_argument("--crs", required=True, help="Source CRS label; metadata only, no reprojection")
    parser.add_argument("--vertical-datum", required=True, help="Source elevation datum label; metadata only")
    parser.add_argument("--step", type=int, default=1, help="Keep every Nth sample plus boundary samples")
    parser.add_argument("--force", action="store_true", help="Replace existing OBJ and JSON outputs")
    args = parser.parse_args()
    try:
        result = export(args.input, args.output,
                        origin=(args.origin_easting, args.origin_northing, args.origin_elevation),
                        step=args.step, crs=args.crs, vertical_datum=args.vertical_datum, force=args.force)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Wrote {args.output} and {args.output.with_suffix('.json')}: "
          f"{result['statistics']['vertices']} vertices, {result['statistics']['triangles']} triangles")


if __name__ == "__main__":
    main()
