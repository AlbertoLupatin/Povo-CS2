# Build the campus on another Windows computer

The recipient builds a playable CS2 map package from this repository. Use a
Windows PC with Steam, Counter-Strike 2 and its **Counter-Strike 2 Workshop Tools**
DLC installed. Launch Workshop Tools once to complete installation. Use a GPU
with hardware ray tracing for lighting compilation. A dedicated RTX GPU is
suitable; the CPU still matters for model/collision compilation. Keep the laptop
plugged in. Plan for tens of GB of spare disk space beyond the game installation.

Install Git if cloning, and 64-bit Python **3.11 or newer** with its Windows `py`
launcher. Python 3.11/3.12 are suitable starting points. Blender, QGIS, CUDA,
PyTorch and an HPC account are not required for this build.

## 1. Get the complete source

For the version committed to GitHub:

```powershell
git clone https://github.com/AlbertoLupatin/Povo-CS2.git
cd Povo-CS2
```

For the current working version, including changes that have not been committed,
the sender should run this from the repository while nobody is editing or
generating source files:

```powershell
python tools/create_build_handoff.py
```

Send `build/handoff/povo-cs2-source.zip`, then extract it and open PowerShell in
its `Povo-CS2` folder. The ZIP includes current tracked and nonignored untracked
files, reference data, generated base geometry, and a SHA-256 file manifest.
It excludes Git history, the local Python environment, Valve's installation and
ignored build tools/output. Review its contents before sharing. A GitHub clone
only contains committed changes; it does not include the sender's working edits.

Keep the full directory structure, including `data/`, `config/`, `cs2/`, and
`exports/`. Some reference files are checked against recorded hashes during
generation. Do not transfer just the tools or the VMAP. The existing blockout
export is an input to campus generation and is included in the handoff.

## 2. Install the two build dependencies

From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
```

Download the **Windows x64 CLI** archive from
[VPKEdit 4.4.2](https://github.com/craftablescience/VPKEdit/releases/tag/v4.4.2)
and extract it so this exact path exists:

```text
build/tools/vpkedit-4.4.2/vpkeditcli.exe
```

Keep any accompanying runtime files beside the executable. If Windows reports a
missing MSVC runtime, install Microsoft's x64 Visual C++ Redistributable linked
by the upstream release instructions. VPKEdit is used only for packaging;
`blake3` supplies the checksum format required by CS2. No virtual-environment
activation or PowerShell execution-policy change is needed.

## 3. Check and build

```powershell
.\build_campus.cmd --check
.\build_campus.cmd
```

For the smaller lightmap atlas, run `.\build_campus.cmd --fast-lighting`.
To reproduce the 29 October pavement preview bake, use
`.\build_campus.cmd --fast-lighting --lighting-quality 0`. The default quality
remains 1. The explicit quality is forwarded to Valve's compiler and recorded
in the build evidence. Pavement uses its own probe-lit, render-only finish;
its structural collision is unchanged.
This uses a 2048-pixel atlas and normal-quality lighting (quality 1).
Preview quality 0 produced black frontage seams and is no longer used.
Larger black courtyard patches remain under investigation; see
[exterior visibility notes](POVO_EXTERIOR_VISIBILITY.md).
Geometry and collision are unchanged.
The full source tests and package checks still run.

The default builds **standard** campus only. To include winter:

```powershell
.\build_campus.cmd --season both
```

Steam libraries are discovered automatically. For a custom installation, pass
the game root, not the Steam root or addon folder, to both commands:

```powershell
.\build_campus.cmd --check --cs2-root "D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive"
.\build_campus.cmd --cs2-root "D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive"
```

`CS2_ROOT` is also supported. `--check` checks software/file prerequisites; it
does not benchmark the GPU or prove the graphics driver can bake lighting.

Close CS2 and Hammer before building. Use one build at a time. The wrapper refuses
to start while a Valve resource compiler is running. The build regenerates
campus assets in this checkout, deploys into the installed `trento_povo` addon,
and replaces that addon's project-owned files. Use a dedicated checkout and save
any Hammer edits before building. Do not use `--skip-model` for a first build.

The wrapper runs source tests, compiles the model and map, packages assets, then
checks map/model/config presence, radar resources and every VPK entry CRC.
Any failed stage stops the run with a nonzero exit code. Long quiet periods
during model/collision compilation can happen; the later lighting stage uses
the GPU. There is no cluster or multi-H100 build mode.

## 4. Return the result

A successful run prints `Build verified`. Return:

- `build/package/trento_povo_campus.vpk` and its adjacent `.json` packaging report.
- For winter, `trento_povo_campus_winter.vpk` and its `.json` report too.
- The printed timestamped `build/handoff/<timestamp>/` folder containing logs,
  build status, source Git revision/status when available, and package checks.

An older VPK may remain after a failed run. Only send a package from a run whose
`build.json` says `"status": "passed"`. The command does not publish to Workshop.
The package check does not establish visual correctness or clean-install runtime
compatibility. Run `play_campus.cmd` for a manual smoke test after compiling;
see [the playtest guide](POVO_CAMPUS_PLAYTEST.md) and
[publishing instructions](PUBLISH_AND_HOST.md) for subsequent steps.

## Troubleshooting

- **Python unavailable:** install 64-bit Python with the `py` launcher, reopen
  PowerShell, then repeat the environment commands.
- **Missing compiler:** install Workshop Tools, launch them once, and check the
  `--cs2-root` path. The regular Linux game installation is insufficient.
- **Missing packer or `blake3`:** repeat step 2 on the recipient's PC. Neither is
  included in a source checkout or ZIP.
- **Lighting failure/device lost:** inspect `compile.log`, update the GPU driver,
  and ensure the compiler uses the dedicated ray tracing GPU in Windows graphics
  settings. A passing preflight cannot detect all driver/VRAM problems.
- **Test failure:** return `tests.log` and stop; do not bypass the test stage to
  report a successful build.
