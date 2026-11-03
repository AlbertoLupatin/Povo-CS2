# Povo-CS2 remake

**Start with [PROJECT.md](PROJECT.md)**: status, sources, levels, tools, how to edit and how to send changes.

From-scratch rebuild of the Povo campus map. The legacy project lives next door
in `../Povo-CS2` and is used as reference data only.

## Site master (milestone 1)

```bash
python tools/fetch_site.py      # OSM, 2024 orthophoto, PAT LiDAR (skips files already present)
python tools/site_master.py     # layers, building/tree tables, renders
python tools/scale_study.py     # corridor section at candidate gameplay scales
```

| Output | Content |
| --- | --- |
| `data/lidar/` | 9 tiles x DTM / DBM / DSMF, 1.5 x 1.5 km, 0.5 m, EPSG:25832 |
| `data/ortho/` | Comune di Trento 2024 orthophoto: campus at 15 cm, site at 50 cm |
| `data/osm/povo.json` | Raw Overpass extract |
| `data/derived/buildings.csv` | Footprint, oriented size, ground and roof elevations, LiDAR height |
| `data/derived/trees.csv` | OSM trees with LiDAR height/crown, plus unmapped canopy peaks |
| `data/derived/site_layers.json` | OSM layers in EPSG:25832 |
| `out/site_master.png` | Ortho + OSM overlay, labelled, 50 m grid |
| `out/site_heights.png` | Building heights (grey) and vegetation (green) |
| `out/scale_study.png` | Corridor/door/stair vs CS2 player at scale 1.0 / 1.25 / 1.5 |

Sources and licences are recorded per file in `data/provenance.json`:
PAT LiDAR CC BY 4.0, Trento orthophoto CC0, OpenStreetMap ODbL.

## Key measurements so far

| Building | OSM id | Footprint | Ground (m a.s.l.) | LiDAR height p50 / p95 |
| --- | --- | --- | --- | --- |
| Povo 1 (Sommarive 5) | r3663359 | 81.4 x 47.3 m | 373.2-373.6 | 13.5 / 16.3 m |
| Povo 2 (Sommarive 9) | 1193371312 | 101.7 x 50.0 m | 368.0-375.4 | 16.5 / 20.9 m |
| Povo 2 east block | 1193371313 | 83.0 x 28.3 m | 368.4-378.3 | 6.6 / 12.0 m |
| BUP library | 275318462 | 54.5 x 13.8 m | 373.5-378.1 | 6.7 / 9.2 m |
| Mensa Povo 1 | 275318465 | 33.3 x 15.9 m | 373.2-378.0 | 7.1 / 9.9 m |

## Native Hammer map generation (milestone 2)

```bash
python tools/build_test_room.py   # generate, convert, compile povo_scale_test into addon povo_remake
python tools/cs2_shots.py views/scale_views.json   # screenshots from a running CS2
```

- `tools/kv2.py` reads/writes DMX keyvalues2 (text .vmap); round-trips Valve's maps exactly.
- `tools/vmap_mesh.py` builds native `CMapMesh` half-edge meshes, so generated
  geometry stays editable in Hammer (no giant static prop as in the legacy build).
- `tools/build_test_room.py` assembles a map from Valve's Wingman template:
  sky, sun, fog, post-processing and spawns kept, template geometry removed.
- CS2 is launched with `-addon povo_remake -tools -insecure -netconport 27400`;
  load with `map maps/povo_scale_test.vpk`.

## Storage

Heavy folders live on `D:\CS2_Povo` and are reached through directory junctions,
so paths under this folder keep working: `../Povo-CS2`, `data/`, `out/`, `build/`.
Code (`tools/`, this README) stays here.

## Still needed

- On-site measurements: corridor width, classroom door, floor-to-floor height,
  stair riser/tread and riser count per flight, curtain-wall mullion spacing.
