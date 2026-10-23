"""Photo-guided exterior geometry, in local metres; no gameplay collision."""

import math
import re


MATERIALS = {
    "facade_glazing": (0.16, 0.32, 0.35),
    "facade_frame": (0.70, 0.74, 0.73),
    "facade_stone": (0.78, 0.75, 0.65),
    "facade_dark": (0.15, 0.18, 0.20),
}
MAX_PARTS = 6000


def positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return value


def validate_architecture(spec, buildings):
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise ValueError("architecture must be an object")
    spec = dict(spec)
    for field in ("reference_manifest", "assumptions"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise ValueError(f"architecture {field} must be nonempty text")
    by_id = {b["id"]: b for b in buildings}
    if not isinstance(spec.get("facades"), list):
        raise ValueError("architecture facades must be a list")
    facades, seen, faces = [], set(), set()
    part_estimate = 0
    for raw in spec["facades"]:
        if not isinstance(raw, dict):
            raise ValueError("Each facade must be an object")
        f = dict(raw)
        identifier = f.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", identifier) or identifier in seen or identifier in by_id:
            raise ValueError("Facade IDs must be unique safe names")
        seen.add(identifier)
        if f.get("building") not in by_id or f.get("face") not in ("east", "west", "north", "south"):
            raise ValueError(f"{identifier}: unknown building or face")
        face = (f["building"], f["face"])
        if face in faces:
            raise ValueError("Only one facade definition is allowed per building face")
        faces.add(face)
        if f.get("style") not in ("curtain_wall", "stone_windows"):
            raise ValueError("Facade style must be curtain_wall or stone_windows")
        for field in ("bays", "rows"):
            if type(f.get(field)) is not int or not 1 <= f[field] <= 100:
                raise ValueError(f"Facade {field} must be an integer from 1 to 100")
        for field in ("frame_width", "depth", "edge_margin"):
            positive(f.get(field), f"Facade {field}")
        for field in ("bottom_elevation", "top_elevation"):
            v = f.get(field)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"Facade {field} must be finite")
        building = by_id[f["building"]]
        if not building["base_elevation"] <= f["bottom_elevation"] < f["top_elevation"] <= building["roof_elevation"]:
            raise ValueError("Facade elevations must fit inside the building envelope")
        west, south, east, north = building["bounds"]
        length = north - south if f["face"] in ("east", "west") else east - west
        bay_width = (length - 2 * f["edge_margin"]) / f["bays"]
        row_height = (f["top_elevation"] - f["bottom_elevation"]) / f["rows"]
        if min(bay_width, row_height) <= 3 * f["frame_width"]:
            raise ValueError("Facade frames/margins leave no usable window area")
        if f["style"] == "stone_windows" and min(bay_width * 0.44, row_height * 0.74) <= 2 * f["frame_width"]:
            raise ValueError("Facade frames leave no usable stone-window glazing")
        if f["depth"] > 0.5:
            raise ValueError("Facade depth must not exceed 0.5 metres")
        refs = f.get("reference_ids")
        if not isinstance(refs, list) or not refs or any(not isinstance(v, str) or not re.fullmatch(r"P\d{3}", v) for v in refs):
            raise ValueError("Facade needs reference_ids such as P002")
        if not isinstance(f.get("placement_note"), str) or not f["placement_note"].strip():
            raise ValueError("Facade needs a placement_note describing uncertainty")
        part_estimate += f["bays"] * f["rows"] * 2 + f["bays"] + f["rows"] + 5
        facades.append(f)
    if part_estimate > MAX_PARTS:
        raise ValueError("Architecture exceeds the detail-part budget")
    spec["facades"] = facades
    bridge = spec.get("bridge")
    if bridge is not None:
        if not isinstance(bridge, dict):
            raise ValueError("architecture bridge must be an object")
        bridge = dict(bridge)
        if bridge.get("building") not in by_id:
            raise ValueError("Bridge must refer to an existing building module")
        if any(f["building"] == bridge["building"] for f in facades):
            raise ValueError("Bridge cannot also receive a massing facade")
        for field in ("deck_elevation", "roof_elevation"):
            v = bridge.get(field)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"Bridge {field} must be finite")
        clearance = bridge["roof_elevation"] - bridge["deck_elevation"]
        if not 2.2 <= clearance <= 5:
            raise ValueError("Bridge roof/deck clearance must be between 2.2 and 5 metres")
        for field in ("post_spacing", "louver_spacing"):
            positive(bridge.get(field), f"Bridge {field}")
        if bridge["post_spacing"] < 1 or bridge["louver_spacing"] < 0.15:
            raise ValueError("Bridge spacing would exceed the detail budget")
        if not isinstance(bridge.get("reference_ids"), list) or not bridge["reference_ids"] or any(not isinstance(v, str) or not re.fullmatch(r"P\d{3}", v) for v in bridge["reference_ids"]):
            raise ValueError("Bridge needs photographic reference_ids")
        if not isinstance(bridge.get("placement_note"), str) or not bridge["placement_note"].strip():
            raise ValueError("Bridge needs a placement_note")
        spec["bridge"] = bridge
    return spec


def architecture_boxes(config):
    """Return closed visual boxes, avoiding coplanar surfaces on the massing."""
    spec = config.get("architecture")
    if not spec:
        return []
    buildings = {b["id"]: b for b in config["buildings"]}
    origin = config["origin"]
    boxes = []

    def add(name, minimum, maximum, material):
        if len(boxes) >= MAX_PARTS:
            raise ValueError("Architecture exceeds the detail-part budget")
        boxes.append((name, tuple(v - origin[i] for i, v in enumerate(minimum)),
                      tuple(v - origin[i] for i, v in enumerate(maximum)), material))

    for f in spec["facades"]:
        b = buildings[f["building"]]
        west, south, east, north = b["bounds"]
        face = f["face"]
        length = north - south if face in ("east", "west") else east - west
        start = south if face in ("east", "west") else west
        z0, z1 = f["bottom_elevation"], f["top_elevation"]
        margin, frame, depth = f["edge_margin"], f["frame_width"], f["depth"]
        count = 0

        def surface(u0, u1, bottom, top, material, layer):
            nonlocal count
            # Thin separated layers all sit outside the original building box.
            d0, d1 = 0.02 + layer * depth, 0.02 + (layer + 0.7) * depth
            if face == "east":
                lo, hi = (east + d0, start + u0, bottom), (east + d1, start + u1, top)
            elif face == "west":
                lo, hi = (west - d1, start + u0, bottom), (west - d0, start + u1, top)
            elif face == "north":
                lo, hi = (start + u0, north + d0, bottom), (start + u1, north + d1, top)
            else:
                lo, hi = (start + u0, south - d1, bottom), (start + u1, south - d0, top)
            add(f"arch_{f['id']}_{count:04d}", lo, hi, material)
            count += 1

        step = (length - 2 * margin) / f["bays"]
        row = (z1 - z0) / f["rows"]
        if f["style"] == "curtain_wall":
            surface(margin, length - margin, z0, z1, "facade_glazing", 0)
            for i in range(f["bays"] + 1):
                u = margin + i * step
                surface(u - frame / 2, u + frame / 2, z0, z1, "facade_frame", 1)
            for i in range(f["rows"] + 1):
                z = z0 + i * row
                surface(margin, length - margin, z - frame / 2, z + frame / 2, "facade_frame", 1)
        else:
            surface(0, length, z0, z1, "facade_stone", 0)
            for i in range(f["bays"]):
                u = margin + (i + 0.5) * step
                for j in range(f["rows"]):
                    bottom = z0 + j * row + row * 0.14
                    top = z0 + (j + 1) * row - row * 0.12
                    half_width = step * 0.22
                    surface(u - half_width, u + half_width, bottom, top, "facade_dark", 1)
                    surface(u - half_width + frame, u + half_width - frame,
                            bottom + frame, top - frame, "facade_glazing", 2)
        surface(0, length, z1 + 0.04, z1 + 0.18, "facade_dark", 1)

    bridge = spec.get("bridge")
    if bridge:
        west, south, east, north = buildings[bridge["building"]]["bounds"]
        deck, roof = bridge["deck_elevation"], bridge["roof_elevation"]
        add("arch_bridge_deck", (west, south, deck - 0.25), (east, north, deck), "facade_dark")
        add("arch_bridge_roof", (west - 0.12, south, roof - 0.2), (east + 0.12, north, roof), "facade_frame")
        # Existing source bridge runs north/south. Ends remain visually open;
        # these components never enter the arena collision/nav export.
        for side, x in (("west", west), ("east", east)):
            steps = max(1, math.ceil((north - south) / bridge["post_spacing"]))
            for i in range(steps + 1):
                y = south + (north - south) * i / steps
                add(f"arch_bridge_{side}_post_{i:02d}", (x - 0.06, y - 0.06, deck),
                    (x + 0.06, y + 0.06, roof - 0.2), "facade_dark")
            steps = max(1, math.floor((roof - deck - 0.6) / bridge["louver_spacing"]))
            for i in range(steps):
                z = deck + 0.35 + i * bridge["louver_spacing"]
                add(f"arch_bridge_{side}_louver_{i:02d}", (x - 0.10, south, z),
                    (x + 0.10, north, z + 0.08), "facade_frame")
    return boxes


def material_library():
    return "".join(f"\nnewmtl {name}\nKa 0.15 0.15 0.15\nKd {' '.join(map(str, color))}\nKs 0 0 0\nillum 1\n"
                   for name, color in MATERIALS.items())
