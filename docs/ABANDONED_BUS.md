# Abandoned bus before the bridge

The exterior generator places a 9 m bus broadside across the 6 m street and
both footways, east of the bridge. Placement is configured in
`config/povo_exterior.json`; local centre is `(25, -5, 4)` metres.

The white-and-green mountain livery includes an amber front destination display,
`5/ Università di Povo`. Font glyphs become planar geometry, so the display does
not depend on repeating world-space texture coordinates. Source generation
requires Pillow (`python -m pip install Pillow`). The preview renderer also
requires NumPy.

The current source includes open entrance doors, low steps, a supported aisle,
worn seating, broken side panes, grab poles and discarded papers. The opposite
wall retains the requested road closure. Tests check entrance and aisle clearance,
road coverage, livery meshes and destination lettering. The exterior route audit
records the road closure as `blocked_as_designed` while preserving other checks.

```sh
python -m unittest tests.test_povo_abandoned_bus tests.test_povo_exterior -q
python tools/build_povo_campus.py
python tools/render_abandoned_bus.py
```

Review images are in `exports/povo_campus/abandoned_bus*_review.png`.

The original closed-cabin livery build was uploaded successfully to the existing
friends-only [Workshop item](https://steamcommunity.com/sharedfiles/filedetails/?id=3827904476).
That upload contained a 64,645,282-byte standard package with 1,077 verified entries,
SHA-256 `20ed56e33f4fc79970a8b726f361d63bbaf64ae2eff893167fe6b9ce26463c79`.
The later open-interior source update is separate from that publication; no new
Workshop upload or native traversal of the open bus is claimed here.

GitHub source validation used a clean snapshot of the bus commit: 223 tests ran,
222 passed and one was skipped. Generated full-campus meshes and unrelated
in-progress map edits are regenerated or committed separately.
