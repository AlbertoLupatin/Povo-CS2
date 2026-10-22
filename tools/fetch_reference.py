#!/usr/bin/env python3
"""Fetch small Comune di Trento aerial reference crops; standard library only."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import urllib.parse
import urllib.request


ENDPOINT = "https://gis.comune.trento.it/ogc"
LAYER = "ortofoto_2024"
AREAS = {
    "povo": (666000, 5103500, 666500, 5104000),
    "mesiano": (665000, 5103500, 665500, 5104000),
}
SIZE = 1000
MAX_BYTES = 20 * 1024 * 1024


def fetch(area, directory, force=False):
    """Save a 0.5 m/pixel reference, its world file, and source provenance."""
    bounds = AREAS[area]
    stem = directory / f"{area}_ortho_2024"
    outputs = [stem.with_suffix(suffix) for suffix in (".png", ".pgw", ".json")]
    if not force and any(path.exists() for path in outputs):
        raise FileExistsError(f"Output exists for {area}; use --force to replace it")
    params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": LAYER, "STYLES": "", "CRS": "EPSG:25832",
        "BBOX": ",".join(map(str, bounds)), "WIDTH": SIZE, "HEIGHT": SIZE,
        "FORMAT": "image/png", "TRANSPARENT": "FALSE",
    }
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Trento-FPS-map-research/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read(MAX_BYTES + 1)
        content_type = response.headers.get("Content-Type", "")
    if len(content) > MAX_BYTES:
        raise ValueError("Response exceeds 20 MiB limit")
    if len(content) < 24 or content[:8] != b"\x89PNG\r\n\x1a\n" or content[12:16] != b"IHDR":
        raise ValueError(f"Expected PNG, received {content_type}: {content[:160]!r}")
    width, height = struct.unpack(">II", content[16:24])
    if (width, height) != (SIZE, SIZE):
        raise ValueError(f"Unexpected image dimensions: {width} x {height}")
    min_e, min_n, max_e, max_n = bounds
    pixel_x, pixel_y = (max_e - min_e) / width, (max_n - min_n) / height
    # World files store the centre of the top-left pixel, not its outside corner.
    world = [pixel_x, 0, 0, -pixel_y, min_e + pixel_x / 2, max_n - pixel_y / 2]
    manifest = {
        "provider": "Comune di Trento",
        "area": area,
        "purpose": "Geographic reconnaissance; not the selected playable boundary",
        "source_url": url,
        "source_layer": LAYER,
        "metadata_url": "https://gis.comune.trento.it/it/map/cartografia-generale/qdjango/42/",
        "licence": "CC0 1.0 Universal (2024 orthophoto layer metadata)",
        "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source_survey_dates": ["2024-08-28", "2024-08-29"],
        "source_pixel_size_metres": 0.1,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "crs": "EPSG:25832",
        "bbox_order": "min_easting,min_northing,max_easting,max_northing",
        "bbox": bounds,
        "width": width, "height": height,
        "output_pixel_size_metres": [pixel_x, pixel_y],
        "note": "Server-rendered and resampled WMS extract; assign EPSG:25832 when loading PNG+PGW. No elevation data is contained in the image.",
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }
    directory.mkdir(parents=True, exist_ok=True)
    outputs[0].write_bytes(content)
    outputs[1].write_text("\n".join(f"{value:.8f}" for value in world) + "\n")
    outputs[2].write_text(json.dumps(manifest, indent=2) + "\n")
    return {"area": area, "png": str(outputs[0]), "bytes": len(content), "dimensions": [width, height]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area", choices=[*AREAS, "all"], default="all")
    parser.add_argument("--output", type=Path, default=Path("data/reference"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    areas = list(AREAS) if args.area == "all" else [args.area]
    try:
        # Preflight all outputs so a rerun does not partially overwrite a set.
        if not args.force:
            for area in areas:
                for suffix in (".png", ".pgw", ".json"):
                    path = args.output / f"{area}_ortho_2024{suffix}"
                    if path.exists():
                        raise FileExistsError(f"{path} exists; use --force to replace")
        for area in areas:
            print(json.dumps(fetch(area, args.output, args.force)))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
