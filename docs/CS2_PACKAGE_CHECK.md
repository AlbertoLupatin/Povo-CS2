# Check packaged radar resources

For the separate two-floor campus map, run `python tools/cs2_campus.py` to build
and package the model, map and four radar textures together. Verify its floor
sections and all entry CRCs with:

```powershell
python tools/verify_cs2_package.py build/package/trento_povo_campus.vpk --map trento_povo_campus --overview exports/povo_campus/radar/trento_povo_campus.txt --full-crc
```

Use `play_campus.cmd` for the isolated addon load test. See
[POVO_CAMPUS_PLAYTEST.md](POVO_CAMPUS_PLAYTEST.md) for the current verified package
identity and runtime checks. The outdoor-map commands below remain available.

## Build a portable map package

After `python tools/cs2_project.py compile --target all`, use the standalone
[VPKEdit 4.4.2 CLI](https://github.com/craftablescience/VPKEdit/releases/tag/v4.4.2).
Extract the Windows CLI archive into `build/tools/vpkedit-4.4.2/`. Install the
optional packager dependency locally, then build:

```powershell
python -m pip install --target build/tools/python blake3==1.0.11
python tools/package_cs2.py --vpkedit build/tools/vpkedit-4.4.2/vpkeditcli.exe
python tools/verify_cs2_package.py build/package/trento_povo.vpk --full-crc --report build/package/radar-check.json
```

Use `--force` to replace an existing packaged output after successful validation.
`--cs2-root` selects another installation and `--output` selects a separate VPK
destination. The compiler's installed VPK is preserved. The packager stages all
original map entries, the Povo model/materials and generated textures, map config,
radar and overview. No editable interiors or reference photos are included.
It adds `_radar_psd` / `_radar_spectate_psd` aliases for current CS2 lookup while
preserving the generated `_tga` resources.

The packager writes the current CS2 BLAKE3-128 chunk table in 1 MiB fractions,
the directory/table/file MD5 checksums and an empty unsigned signature descriptor.
VPKEdit 4.4.2's default Source 1 MD5 chunk table passes ordinary archive checks
but is rejected by CS2 build `26144732` with `Chunk hash not found`. Format sources
are the upstream [hash type definitions](https://github.com/ValveResourceFormat/ValvePak/blob/master/ValvePak/ValvePak/EHashType.cs)
and [verification implementation](https://github.com/ValveResourceFormat/ValvePak/blob/master/ValvePak/ValvePak/Package.Verify.cs).

The output JSON records source/package/packer hashes and each staged asset hash.
Before publication to the output path, every packaged entry must match those
staged bytes, all entry CRCs must pass and the radar overview must match.
The 23 October Windows build contains 51 entries / 10,623,229 bytes and loads in
CS2 with server and client physics. Visual radar alignment, gameplay and a
clean installation without loose addon assets still require separate checks.

## Inspect a package

`cs2_project.py` can compile radar textures as loose addon files. A successful
loose compile does not establish that the final map VPK contains them. After
building/repacking on Windows, run this read-only checker from the repository:

```powershell
python tools/verify_cs2_package.py "C:\path\to\trento_povo.vpk" --full-crc --report build/package-check.json
```

For a split package pass its `_dir.vpk` and keep numbered chunks beside it.
The checker needs only Python's standard library and works on Linux too.

It checks the packaged normal and spectator compiled radar textures, their entry
CRCs, and the packaged overview's fields against `exports/povo_radar/trento_povo.txt`.
`--full-crc` additionally streams and checks every archive entry. The JSON report
records the directory/single-package SHA256, entry count and individual failures.
For split packages that SHA256 identifies the directory file; CRCs check the
referenced chunk payloads, without recording a SHA256 for each chunk.

A passing result does not verify texture contents, Valve signatures, complete
custom dependencies, actual engine radar lookup/alignment, gameplay, or clean
installation without loose development assets. Those remain Windows checks.
The Windows package above passes this check, including both runtime radar aliases.

The reader supports VPK versions 1 and 2, embedded data, preload bytes and numbered
chunks. It rejects malformed/truncated directories, unsafe paths, case collisions
and out-of-range data. Format reference: the primary
[ValvePak reader](https://github.com/ValveResourceFormat/ValvePak/blob/master/ValvePak/ValvePak/Package.Read.cs).
Tests include synthetic v1/v2 fixtures and radar failures. Additional temporary
upstream fixtures `preload.vpk`, `test_single.vpk`, and `test_dir.vpk` with its
numbered chunk passed all entry CRCs. A CS2 signature fixture directory parsed;
its absent numbered chunk prevented payload checking. No upstream fixture binaries
are included in this repository.
