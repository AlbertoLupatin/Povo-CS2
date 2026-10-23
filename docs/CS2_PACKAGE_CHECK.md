# Check packaged radar resources

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
No current Windows map VPK has been inspected with this tool.

The reader supports VPK versions 1 and 2, embedded data, preload bytes and numbered
chunks. It rejects malformed/truncated directories, unsafe paths, case collisions
and out-of-range data. Format reference: the primary
[ValvePak reader](https://github.com/ValveResourceFormat/ValvePak/blob/master/ValvePak/ValvePak/Package.Read.cs).
Tests include synthetic v1/v2 fixtures and radar failures. Additional temporary
upstream fixtures `preload.vpk`, `test_single.vpk`, and `test_dir.vpk` with its
numbered chunk passed all entry CRCs. A CS2 signature fixture directory parsed;
its absent numbered chunk prevented payload checking. No upstream fixture binaries
are included in this repository.
