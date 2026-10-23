# CS2 addon source

This directory contains the repository-owned source for the `trento_povo` CS2
addon. It is intentionally separate from the geographic master in `data/`,
`config/`, and `exports/` so that the measured local-metre source remains useful
on Linux, macOS, and Windows.

The current `maps/trento_povo.vmap` is seeded from the Wingman template shipped
with CS2 Workshop Tools build `26087496`. Its starting SHA-256 was
`9cff6309a167baaf93343a76d2239bc197caf6f70d25d4f982b045dffeb41695`.
It provides a known-current entity and lighting baseline while the geographic
terrain and campus circulation replace the placeholder layout.

Use the cross-platform project command from the repository root:

```sh
python tools/cs2_project.py doctor
python tools/cs2_project.py place-blockout
python tools/cs2_project.py deploy
python tools/cs2_project.py compile --target model
python tools/cs2_project.py compile --target map
python tools/cs2_project.py sync-from-cs2
```

`place-blockout` is the reproducible preparation step: it inserts the pitched
Povo model; removes stock-room geometry/helpers; relocates the twelve starts,
bomb target, buy zones, and cameras; and adds the fitted sky, post-processing,
lightmap resolution, probe, nav, soundscape, and minimap support. Running it
again without source changes is a no-op.

`doctor` and all geographic preparation commands run on any supported Python
platform. `deploy`, `compile`, and `sync-from-cs2` require a Windows CS2 Workshop
Tools installation. Set `CS2_ROOT` or pass `--cs2-root` if Steam is not in a
discovered library.

`compile --target map` intentionally compiles the ModelDoc source before the map;
Valve's map compiler can otherwise reuse stale model collision and materials.

Deployment is additive: it updates project-owned files but does not delete other
files from the installed addon. Hammer and ModelDoc save into the installed
`content/csgo_addons/trento_povo` tree. Run `sync-from-cs2`, review the Git diff,
and commit after an editor session so source changes are preserved in GitHub.

The Povo OBJ uses metres with east `+X`, north `+Y`, and up `+Z`. ModelDoc applies
`39.37007874` once to convert metres to Source/Hammer inches. The 1 m calibration
cube must measure 39.3701 Hammer units before that mapping is accepted in game.
Source 2's OBJ import axis order makes the unrotated model stand on edge, so the
map places `povo_geographic_blockout` at pitch `-90` degrees. Hammer then reports
the expected approximate bounds of 12,589 × 8,652 × 1,643 units (320 × 220 ×
42 m), with geographic Z pointing up.

For a direct local diagnostic after deployment and compilation, the Workshop
Tools engine accepts the packaged map path (including the `.vpk` suffix):

```powershell
cs2.exe -steam -retail -addon trento_povo -tools `
  -asset maps/trento_povo.vmap -insecure +map maps/trento_povo.vpk
```

Using only `+map trento_povo` does not select this local add-on in the tested
build. This command is a developer playtest path, not the eventual Workshop or
multiplayer launch flow.

