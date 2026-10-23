#!/usr/bin/env python3
"""Generate a schematic Povo radar and alignment review using only stdlib.

This describes the configured blockout, not a surveyed floor plan or a navmesh.
Valve texture compilation, packaging, and in-game alignment require Windows.
"""

from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import zlib

try:
    from .build_povo_blockout import boundary_segments, validate_config
    from . import cs2_project
except ImportError:  # python tools/build_povo_radar.py
    from build_povo_blockout import boundary_segments, validate_config
    import cs2_project


ROOT = Path(__file__).resolve().parents[1]
SIZE = 1024
UNITS_PER_METRE = 39.37007874
RADAR_IMAGE = "trento_povo_radar.png"
TEXTURES = ("trento_povo_radar_tga.vtex", "trento_povo_radar_spectate_tga.vtex")
OUTPUT_FILES = (RADAR_IMAGE, *TEXTURES, "trento_povo.txt", "review.svg",
                "radar.json", "CREDITS.txt")
FLOOR = (98, 113, 119, 255)
WALL = (215, 226, 220, 255)
COVER_LOW = (167, 190, 180, 255)
COVER_HIGH = (227, 214, 174, 255)


def geographic_to_world(easting, northing, origin):
    """Verified OBJ import + -90 degree pitch: world X=north, Y=east."""
    return ((northing - origin[1]) * UNITS_PER_METRE,
            (easting - origin[0]) * UNITS_PER_METRE)


def world_to_pixel(x, y, overview):
    return ((x - overview["pos_x"]) / overview["scale"],
            (overview["pos_y"] - y) / overview["scale"])


def pixel_to_world(x, y, overview):
    return (overview["pos_x"] + x * overview["scale"],
            overview["pos_y"] - y * overview["scale"])


def overview_for(config, padding):
    if not math.isfinite(padding) or padding < 1:
        raise ValueError("padding must be finite and at least one metre")
    west, south, east, north = config["gameplay"]["playable_bounds"]
    if padding <= config["gameplay"]["boundary"]["thickness_metres"]:
        raise ValueError("padding must exceed boundary thickness")
    centre_x, centre_y = geographic_to_world(
        (west + east) / 2, (south + north) / 2, config["origin"]
    )
    side = (max(east - west, north - south) + 2 * padding) * UNITS_PER_METRE
    if not math.isfinite(side):
        raise ValueError("radar extent overflow")
    return {"pos_x": centre_x - side / 2, "pos_y": centre_y + side / 2,
            "scale": side / SIZE, "rotate": 0, "zoom": 1.0}


def pixel_bounds(bounds, origin, overview):
    west, south, east, north = bounds
    left, bottom = world_to_pixel(*geographic_to_world(west, south, origin), overview)
    right, top = world_to_pixel(*geographic_to_world(east, north, origin), overview)
    return left, top, right, bottom


def markers_for(overview):
    markers = {}
    for classname, label in (("info_player_counterterrorist", "CTSpawn"),
                             ("info_player_terrorist", "TSpawn")):
        starts = [tuple(map(float, position.split()))
                  for position, _angles in cs2_project.PLAYTEST_SPAWNS[classname]]
        centre = tuple(sum(p[axis] for p in starts) / len(starts) for axis in (0, 1))
        markers[label] = world_to_pixel(*centre, overview)
    objective = tuple(map(float, cs2_project.PLAYTEST_OBJECTIVE_ORIGIN.split()))
    markers["bombA"] = world_to_pixel(*objective[:2], overview)
    if any(not (0 <= coordinate <= SIZE)
           for position in markers.values() for coordinate in position):
        raise ValueError("Playtest markers fall outside the radar; review the layout")
    return markers


def shapes_for(config, overview):
    origin = config["origin"]
    west, south, east, north = config["gameplay"]["playable_bounds"]
    shapes = [("floor", pixel_bounds((west, south, east, north), origin, overview), FLOOR)]
    # Reuse the mesh generator: walls straddle the configured boundary.
    shapes.extend((name, pixel_bounds(b, origin, overview), WALL)
                  for name, b in boundary_segments(
                      config["gameplay"]["playable_bounds"], config["gameplay"]["boundary"]))
    for cover in config["gameplay"]["cover"]:
        color = COVER_HIGH if cover["height_metres"] >= 2 else COVER_LOW
        shapes.append((cover["id"], pixel_bounds(cover["bounds"], origin, overview), color))
    return shapes


def png_bytes(shapes):
    """Lossless RGBA PNG with transparent non-playable space."""
    pixels = bytearray(SIZE * SIZE * 4)
    for _name, (left, top, right, bottom), color in shapes:
        x0, y0 = max(0, round(left)), max(0, round(top))
        x1, y1 = min(SIZE, round(right)), min(SIZE, round(bottom))
        row = bytes(color) * max(0, x1 - x0)
        for y in range(y0, y1):
            offset = (y * SIZE + x0) * 4
            pixels[offset:offset + len(row)] = row

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)))

    scanlines = b"".join(b"\0" + pixels[y * SIZE * 4:(y + 1) * SIZE * 4]
                         for y in range(SIZE))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def objective_glyph(position):
    """Small A at the entity origin; it does not imply a plantable outline."""
    x, y = position
    rows = ("01110", "11011", "11011", "11111", "11011", "11011", "11011")
    return [("objective_A", (x + (col - 2.5) * 3, y + (row - 3.5) * 3,
                             x + (col - 1.5) * 3, y + (row - 2.5) * 3),
             (242, 213, 145, 255))
            for row, line in enumerate(rows) for col, bit in enumerate(line) if bit == "1"]


def overview_text(overview, markers):
    values = {"material": "overviews/trento_povo", **overview}
    for label, (x, y) in markers.items():
        values[label + "_x"] = x / SIZE
        values[label + "_y"] = y / SIZE
    lines = ['// Generated by tools/build_povo_radar.py; see docs/POVO_RADAR.md.',
             '"trento_povo"', '{']
    for key, value in values.items():
        formatted = f"{value:.9f}" if isinstance(value, float) else str(value)
        lines.append(f'    "{key}" "{formatted}"')
    return "\n".join([*lines, "}", ""])


def texture_text():
    """Explicit texture names avoid reliance on image-import hash suffixes."""
    return f'''<!-- dmx encoding keyvalues2_noids 1 format vtex 1 -->
"CDmeVtex"
{{
    "m_inputTextureArray" "element_array" [
        "CDmeInputTexture" {{
            "m_name" "string" "radar"
            "m_fileName" "string" "panorama/images/overheadmaps/{RADAR_IMAGE}"
            "m_colorSpace" "string" "srgb"
            "m_typeString" "string" "2D"
        }}
    ]
    "m_outputTypeString" "string" "2D"
    "m_outputFormat" "string" "BGRA8888"
    "m_textureOutputChannelArray" "element_array" [
        "CDmeTextureOutputChannel" {{
            "m_inputTextureArray" "string_array" [ "radar" ]
            "m_srcChannels" "string" "rgba"
            "m_dstChannels" "string" "rgba"
            "m_outputColorSpace" "string" "srgb"
        }}
    ]
    "m_bNoLod" "bool" "1"
}}
'''


def review_svg(config, overview, shapes, markers):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="900" viewBox="0 0 1280 900">',
             '<rect width="1280" height="900" fill="#111e25"/>',
             '<g font-family="DejaVu Sans, sans-serif" fill="#e9eeeb">',
             '<text x="64" y="74" font-size="16" letter-spacing="3" fill="#8ea8ad">TRENTO / WINGMAN BLOCKOUT</text>',
             '<text x="64" y="124" font-size="38" font-weight="bold">POVO · EAST FORECOURT</text>',
             '<text x="64" y="162" font-size="18" fill="#a7b9bd">25 × 130 m · Six cover volumes · Twelve configured starts</text>',
             # Keep square radar coordinates; crop only the review's empty margin.
             '<g transform="translate(64 -40) scale(1.125)">']
    for name, (left, top, right, bottom), color in shapes:
        fill = "#" + "".join(f"{v:02x}" for v in color[:3])
        parts.append(f'<rect id="{escape(name)}" x="{left:.3f}" y="{top:.3f}" width="{right-left:.3f}" height="{bottom-top:.3f}" fill="{fill}"/>')
    for classname, color in (("info_player_counterterrorist", "#82b9e3"),
                              ("info_player_terrorist", "#e8bb74")):
        for position, _angles in cs2_project.PLAYTEST_SPAWNS[classname]:
            x, y, _z = map(float, position.split())
            px, py = world_to_pixel(x, y, overview)
            parts.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="4" fill="{color}" stroke="#14222a" stroke-width="1.5"/>')
    for label, color, text in (("TSpawn", "#e8bb74", "T / SOUTH"),
                                ("CTSpawn", "#82b9e3", "CT / NORTH"),
                                ("bombA", "#f2d591", "A")):
        x, y = markers[label]
        if label == "bombA":
            parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="16" fill="#14222a" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<text x="{x:.3f}" y="{y+6:.3f}" text-anchor="middle" font-size="18" font-weight="bold" fill="{color}">{text}</text>')
        else:
            parts.append(f'<text x="{x:.3f}" y="650" text-anchor="middle" font-size="16" fill="{color}">{text}</text>')
    for cover in config["gameplay"]["cover"]:
        left, top, right, bottom = pixel_bounds(cover["bounds"], config["origin"], overview)
        above = top < SIZE / 2
        label_y = 375 if above else 675
        line_y = top if above else bottom
        x = (left + right) / 2
        parts.append(f'<path d="M{x:.3f},{line_y:.3f} V{label_y + (8 if above else -20)}" stroke="#71888e" stroke-width="1"/>')
        parts.append(f'<text x="{x:.3f}" y="{label_y}" text-anchor="middle" font-size="14" fill="#b6c5c8">{cover["height_metres"]:g} m</text>')
    parts.extend(['</g>',
                  '<text x="64" y="266" font-size="16" fill="#a7b9bd">GEOGRAPHIC NORTH →</text>',
                  '<text x="1216" y="266" text-anchor="end" font-size="16" fill="#a7b9bd">EAST ↑</text>'])
    scale_length = 10 * UNITS_PER_METRE / overview["scale"] * 1.125
    parts.extend([f'<path d="M64,716 v-8 m0,4 h{scale_length:.3f} m0,-4 v8" stroke="#e9eeeb" stroke-width="2"/>',
                  '<text x="64" y="742" font-size="14">10 m</text>',
                  '<rect x="64" y="786" width="14" height="14" fill="#a7beb4"/>',
                  '<text x="90" y="798" font-size="15">Cover 1.2–1.5 m</text>',
                  '<rect x="300" y="786" width="14" height="14" fill="#e3d6ae"/>',
                  '<text x="326" y="798" font-size="15">Cover 2 m</text>',
                  '<text x="64" y="846" font-size="14" fill="#8ea8ad">Schematic of configured geometry. A marks the objective origin; trigger extents and walkability need in-game checks.</text>',
                  '</g></svg>'])
    return "\n".join(parts) + "\n"


def build_radar(config_path, output, *, padding=7.0, force=False):
    config_path, output = Path(config_path), Path(output)
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError("Output must be a directory, not a file or symlink")
    if output.exists() and not force:
        raise ValueError(f"Output directory exists: {output}; use --force")
    if any((output / name).is_dir() or (output / name).is_symlink() for name in OUTPUT_FILES):
        raise ValueError("A generated filename is occupied by a directory or symlink")
    if config_path.resolve() in {(output / name).resolve() for name in OUTPUT_FILES}:
        raise ValueError("Generated files must not replace the configuration")
    raw = config_path.read_bytes()
    config = validate_config(json.loads(raw))
    if not config["gameplay"]:
        raise ValueError("Radar generation requires gameplay configuration")
    overview = overview_for(config, padding)
    shapes = shapes_for(config, overview)
    markers = markers_for(overview)
    # Reject stale spawn layouts, even when they happen to fit in the square image.
    floor = shapes[0][1]
    for classname, starts in cs2_project.PLAYTEST_SPAWNS.items():
        for position, _angles in starts:
            x, y, _z = map(float, position.split())
            px, py = world_to_pixel(x, y, overview)
            if not (floor[0] < px < floor[2] and floor[1] < py < floor[3]):
                raise ValueError(f"{classname} start lies outside playable_bounds")
    ax, ay = markers["bombA"]
    if not (floor[0] < ax < floor[2] and floor[1] < ay < floor[3]):
        raise ValueError("Objective lies outside playable_bounds")
    files = {RADAR_IMAGE: png_bytes([*shapes, *objective_glyph(markers["bombA"])]),
             **{name: texture_text().encode("utf-8") for name in TEXTURES},
             "trento_povo.txt": overview_text(overview, markers).encode("utf-8"),
             "review.svg": review_svg(config, overview, shapes, markers).encode("utf-8"),
             "CREDITS.txt": ("Povo schematic radar: derived from the configured geographic/gameplay blockout.\n"
                             + json.dumps(config.get("attribution", {}), indent=2, ensure_ascii=False)
                             + "\nNo aerial pixels or third-party radar artwork are included.\n").encode("utf-8")}
    metadata = {"format_version": 1, "image_size": [SIZE, SIZE],
                "status": "Generated source; Valve compilation, in-game alignment and packaging unverified",
                "config_sha256": hashlib.sha256(raw).hexdigest(),
                "layout_source_sha256": cs2_project.sha256(Path(cs2_project.__file__)),
                "units_per_metre": UNITS_PER_METRE, "padding_metres": padding,
                "transform": "world_x=(northing-N0)*units; world_y=(easting-E0)*units; pixel_x=(world_x-pos_x)/scale; pixel_y=(pos_y-world_y)/scale",
                "geographic_north_in_image": "right", "overview": overview,
                "markers_pixels": markers,
                "limitations": ["Schematic rectangular ground; not a navmesh or terrain-height rendering.",
                                "A marks the objective origin, not verified plantable trigger bounds.",
                                "Review spawn dots are omitted from the runtime image.",
                                "Map compilation can overwrite loose radar assets; compile/install radar afterward.",
                                "Loose addon files do not prove that the map VPK contains the radar."],
                "artifacts": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                              for name, data in files.items()}}
    files["radar.json"] = (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".povo-radar-", dir=output.parent) as temporary:
        staged = Path(temporary)
        for name, data in files.items():
            (staged / name).write_bytes(data)
        output.mkdir(exist_ok=True)
        for name in OUTPUT_FILES:
            (staged / name).replace(output / name)
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/povo_blockout.json")
    parser.add_argument("--output", type=Path, default=ROOT / "exports/povo_radar")
    parser.add_argument("--padding", type=float, default=7.0, help="margin in metres, default 7")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        metadata = build_radar(args.config, args.output, padding=args.padding, force=args.force)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Saved {args.output}: 1024 × 1024 radar; scale {metadata['overview']['scale']:.9f} units/pixel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
