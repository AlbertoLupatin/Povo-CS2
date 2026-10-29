# Roadside ginkgo replacement — 29 October 2026

The 33 active roadside trees are young **Ginkgo biloba**, varied between
**2.65, 2.80 and 2.95 metres** from their planting points. The two frontage
rows, west road, bridge approach and library road garden use the same authored
asset generator. The two trees previously removed from the old library pit
remain removed. Courtyard planter trees and hedges retain their existing art.

`tools/povo_ginkgo.py` generates tapered bark, ascending branches and 390
individual bilobed fan leaves per tree, with three green leaf shades and
deterministic variation. Leaf silhouettes are geometry; the leaf material draws
both sides. Only the lower trunk has collision. Existing interior excavations
clip the new mesh at the same boundaries as the previous tree boxes.

The study OBJ and shared campus OBJ include the replacement; both seasons use
the shared campus model. Preview images are in `exports/povo_campus/ginkgo/`.

Validation:

```powershell
python -m unittest tests.test_povo_ginkgo tests.test_povo_exterior tests.test_povo_library_stair -q
python -m unittest discover -s tests -q
python tools/build_povo_exterior.py
python tools/build_povo_campus.py
```

All **282 source tests pass** (`build/ginkgo-tests.log`). The source export
completed; all ten campus OBJ hashes and leaf material remaps are verified
in `build/ginkgo/source-check.json`. On this Windows host,
`build/ginkgo/export_source.py` performs atomic sibling replacement because
some existing files reject direct truncation.

The source tests check all 33 trees, declared heights, finite nondegenerate
geometry, repeatable variation, removed pit trees and canopy exclusion from
collision, alongside the existing library and road walking checks.

Native compilation/deployment is pending: the pre-existing pavement-flicker
build owns the installed addon and Valve compiler. This change does not write
to that installation while its build and runtime verification are active.
After that work finishes, regenerate and compile/package with:

```powershell
python tools/cs2_campus.py --season both --fast-lighting
```

This document and the previews describe the source replacement, not a verified
in-game capture or an updated installed VPK.
