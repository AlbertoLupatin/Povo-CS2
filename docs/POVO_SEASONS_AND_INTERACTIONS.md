# Seasonal atmosphere and interactions — 25 October 2026

The standard campus and winter campus share the same generated architecture,
collision, room selection, doors, spawns, objective and radar geometry.
The winter map adds a separate thin dressing model and snowfall; layout fixes
continue to originate in the single campus generator. Room furnishing work is
deferred, as requested.

## Selection and build

- `play_campus.cmd`: standard campus, retaining the saved fullscreen setting.
- `play_campus_winter.cmd`: winter campus, retaining the saved fullscreen setting.
- Either launcher accepts `-Match`, `-Fly`, and explicit `-Windowed`.
- `python tools/cs2_campus.py --season both` prepares, compiles and packages both.
- `--season standard` is the default; `--season winter` builds only winter.
- `--prepare-only` writes source without claiming a successful native build.
- `--skip-model` is for an entity-only iteration after the shared model has
  already been compiled successfully. Do not use it after geometry changes.

Packages are `build/package/trento_povo_campus.vpk` and
`build/package/trento_povo_campus_winter.vpk`. They retain distinct map resource
names and overviews, and may coexist in the dedicated test addon.

## Atmosphere

`config/povo_atmosphere.json` owns the two sunlight/sky/fog profiles and common
interior exposure and lamp strengths. Haze begins farther from the player;
garage lamps have a larger range and greater output than interior lamps.
The winter profile uses the installed overcast sky and softer, cooler sunlight.

Winter reference P024 shows light accumulation with mostly wet, clear paving.
The dressing therefore places snow on roofs, vegetation, exposed ground and
footway edges, and thin wet films on exposed paving. Building footprints and
roofs shelter floors below. The glass entrance cover also shelters its route.
Thin surface films stay below one centimetre; no slipping or movement changes
are introduced. Distant context snow uses an unlit shader to avoid enormous
lightmaps. It remains outside collision/navigation.

The original `particles/povo/snow.vpcf` uses the installed particle schema and
stock smoke sprite. Sparse emitter regions cover the street, parking and
outskirts. Runtime environment culling shortens flakes at surfaces. This is a
light snowfall effect, not an accumulating weather simulation.

## Audio and surfaces

Native `env_soundscape` zones cover rooms, halls, bridge, basement, garage,
street and surface parking. The inherited sample soundscape is disabled.
The addon soundevent file includes Valve's unchanged base templates, followed
by campus events referencing installed game sounds. Indoor ventilation, garage
ventilation, distant traffic and wind have deliberately low volumes. Different
spaces choose appropriate room/hall/concrete/outdoor reverb presets.

Surface materials declare tile, concrete, asphalt, wood, metal, grass or snow
as appropriate. The compound collision originally used one default surface;
it now imports seven physical groups with explicit ModelDoc surface properties.
The winter model adds concrete and snow physical groups. Actual compiled PHYS
tables and per-triangle material indices are checked by
`tools/audit_povo_compiled_surfaces.py`; changing render material tags alone
does not establish working footsteps. Soundevent, winter model and particle resources are explicitly
required when packaging; all included files receive CRC and source-hash checks.

## Selected interactions

Thirty-eight native door leaves replace the fixed-open visual proxies:

- Povo 1: four paired stair entrances on each of two floors (16 leaves).
- Povo 2: paired stair entrances on four floors (8 leaves).
- Four classroom doors: A208, A215, A223 and A224.
- Povo 2: both banks at both outer and inner entrance lines (8 sliding leaves).
- Povo 1: two glazed entrance leaves.

Door panels, panic bars and entrance safety bands move together. Doors start
open so the navigation bake sees the existing routes. They support use/touch;
sliding leaves close after a delay, while hinged leaves stay in their chosen
position, with the native Toggle flag for closing by use. Blocking damage is zero and forced closing is disabled. Jambs,
thresholds and service doors remain in the permanent campus model.

Only one small framed ground-floor pane at each east stair is breakable (two
total). Large facade, bridge and reception glazing remain structural. Pane
health is 20; normal round reconstruction restores native doors and breakables.

## Built packages

Both native builds completed successfully. Each reflection bake adds only its
cubemap; every previously packaged source entry remains byte-identical.
The installed dedicated test-addon copies match these packages.

| Version | Bytes | Entries | SHA-256 |
| --- | ---: | ---: | --- |
| Standard | 45,173,047 | 391 | `5de0dc71af0cc6e2aaac4570e5445611d72768f66a3ed6069ea66507bd7d461f` |
| Winter | 43,453,973 | 396 | `5f54c53436c22570695a66b58532282ece794cc63f97309187eb193f9975d2f7` |

Both packages contain the same compiled campus model, SHA-256
`56feac504df376351be20b127602940d8b90fbe5c0f14944097f74db92e03958`.
Winter adds the dressing model, SHA-256
`3c0344f355fb55afb5b84e854ca444bca1f33b4f8b602116f0d53d5a5d8d14ea`.
The compiled physical surfaces have actual contact-material assignments for all
seven campus surfaces and the winter snow/concrete groups.

Full package CRC reports, source-entry manifests and native test evidence live
under `exports/povo_campus/runtime/atmosphere/`. Native interaction checks precede
the cubemap bake; the adoption reports establish that their source entries are
unchanged. Walking and match reports retain their exact on-disk package hash.

## Verification scope

All 156 source tests pass. Standard and winter each pass 41 normal-walking
waypoints on 13 independent routes, with one initial placement per route.
Standard passes 14 native interaction checks; winter passes 15, including its
158 spawned snowfall emitters. Door checks exercise closed collision and open
passage for the fire, sliding, main entrance and classroom door families. Both
selected panes break from bullets and return with doors on the next round.

Stock ambient clips have verified loop markers;
custom soundevents, particle and model resources are included in the packages.
Physical footstep assignments were checked in compiled PHYS data. This does
not claim a listening-level calibration of ambient volume or reverb.

Local match checks use one human client and three test bots in 2v2 setups.
Standard and winter each pass all 11 local match checks.
They exercise real purchases, bomb planting, defusing and elimination. Controlled
placements and a temporary team change isolate the defuse mechanic; the tests
also let a normal bot round run. They do not establish autonomous bot completion
of an objective, competitive balance or cross-client replication. The user chose
local bot testing for this phase.

| Check | Standard | Winter |
| --- | ---: | ---: |
| Native interactions | 14/14 | 15/15 |
| Normal-walking waypoints | 41/41 | 41/41 |
| Local 2v2 mechanics | 11/11 | 11/11 |
| Package CRC entries | 391/391 | 396/396 |

The final summary is
[`validation-progress.json`](../exports/povo_campus/runtime/atmosphere/validation-progress.json)
with status `passed`; its filename is retained for continuity. Separate native
logs preserve the actual positions, events and round results. The winter map is
left running at the Povo 1 exterior entrance in solo exploration: one human,
zero bots, paused warmup and normal walking.

The source/package backup is `build/atmosphere-backup-20261024-205704/`.
Earlier geometry corrections remain documented in
[POVO_USER_CORRECTIONS.md](POVO_USER_CORRECTIONS.md).

Native winter views include the
[covered entrance stair](../exports/povo_campus/runtime/atmosphere/winter/atmosphere_winter_entrance.png),
[surface parking and snowfall](../exports/povo_campus/runtime/atmosphere/winter/atmosphere_winter_surface_parking.png),
[garage](../exports/povo_campus/runtime/atmosphere/winter/atmosphere_winter_garage.png)
and [classroom doorway](../exports/povo_campus/runtime/atmosphere/winter/atmosphere_winter_classroom.png).
The matching standard views and camera records are in the `standard/` evidence
directory.
