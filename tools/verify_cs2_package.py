#!/usr/bin/env python3
"""Check packaged Povo radar inclusion, overview alignment, and entry CRCs.

Read-only, cross-platform check. Does not prove gameplay, full dependency
closure, Valve signatures, or successful installation in CS2.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

try:
    from .vpk import Package, VPKError
except ImportError:
    from vpk import Package, VPKError


ROOT = Path(__file__).resolve().parents[1]
RADAR_FILES = (
    "panorama/images/overheadmaps/trento_povo_radar_tga.vtex_c",
    "panorama/images/overheadmaps/trento_povo_radar_spectate_tga.vtex_c",
    "resource/overviews/trento_povo.txt",
)


def overview_values(raw):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise VPKError("Overview is not UTF-8 text") from error
    # Tokenize comments separately so // inside a quoted value is preserved.
    tokens = re.findall(r'//[^\n]*|"[^"\\]*"|[{}]|[^\s]+', text)
    tokens = [token for token in tokens if not token.startswith("//")]
    if len(tokens)<3 or tokens[:2] != ['"trento_povo"', '{'] or tokens[-1] != '}':
        raise VPKError("Overview must contain the trento_povo block")
    pairs = tokens[2:-1]
    if len(pairs)%2 or any(not token.startswith('"') or not token.endswith('"') for token in pairs):
        raise VPKError("Overview must contain flat quoted key/value pairs")
    result = {}
    for key, value in zip(pairs[::2], pairs[1::2]):
        key, value = key[1:-1].casefold(), value[1:-1]
        if key in result:
            raise VPKError(f"Duplicate overview field: {key}")
        result[key] = value
    for key in ("pos_x", "pos_y", "scale"):
        try:
            number = float(result[key])
        except (KeyError, ValueError) as error:
            raise VPKError(f"Missing/non-numeric overview field: {key}") from error
        if not math.isfinite(number) or (key == "scale" and number <= 0):
            raise VPKError(f"Invalid overview field: {key}")
    return result


def compare_overviews(actual, expected):
    observed, wanted = overview_values(actual), overview_values(expected)
    mismatches = []
    for key, value in wanted.items():
        candidate = observed.get(key)
        if candidate is None:
            mismatches.append(key)
            continue
        if key == "material":
            matches = candidate == value
        else:
            try:
                a, b = float(candidate), float(value)
            except ValueError:
                matches = candidate == value
            else:
                matches = math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-6)
        if not matches:
            mismatches.append(key)
    return mismatches


def verify_package(path, expected_overview, *, full_crc=False):
    package = Package(path)
    expected = Path(expected_overview).read_bytes()
    overview_values(expected)
    checks = []
    errors = []
    for name in RADAR_FILES:
        entry = package.entries.get(name.casefold())
        if entry is None:
            errors.append(f"Missing packaged asset: {name}")
            checks.append({"file":name,"status":"missing"})
            continue
        try:
            package.verify(entry)
            if not entry.size:
                raise VPKError(f"Packaged radar asset is empty: {name}")
            check = {"file":name,"status":"present_crc_ok","bytes":entry.size}
            if name.endswith(".txt"):
                content = package.read(entry)
                mismatches = compare_overviews(content, expected)
                check["matches_generated_overview"] = not mismatches
                if mismatches:
                    raise VPKError("Packaged overview differs from generated fields: "+", ".join(mismatches))
            checks.append(check)
        except (OSError, VPKError) as error:
            checks.append({"file":name,"status":"failed","error":str(error)})
            errors.append(str(error))
    verified_count = sum(c["status"] == "present_crc_ok" for c in checks)
    if full_crc:
        verified_count = 0
        for entry in package.entries.values():
            try:
                package.verify(entry)
                verified_count += 1
            except (OSError, VPKError) as error:
                errors.append(str(error))
    with Path(path).open("rb") as stream:
        package_hash=hashlib.file_digest(stream,"sha256").hexdigest()
    return {"format_version":1,"status":"passed" if not errors else "failed",
            "scope":"Radar inclusion and overview alignment; entry CRCs only",
            "package":str(Path(path).resolve()),"vpk_version":package.version,
            "package_sha256":package_hash,
            "package_entries":len(package.entries),"crc_verified_entries":verified_count,
            "all_entry_crc_requested":full_crc,"signature_verification":"not performed",
            "expected_overview_sha256":hashlib.sha256(expected).hexdigest(),
            "checks":checks,"errors":errors,
            "still_required":["Actual radar lookup/alignment in CS2", "Complete custom dependency packaging",
                              "Clean-install test without loose development files", "Gameplay and independent-client validation"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package",type=Path,help="Map VPK or *_dir.vpk (numbered chunks must be beside it)")
    parser.add_argument("--overview",type=Path,default=ROOT/"exports/povo_radar/trento_povo.txt")
    parser.add_argument("--full-crc",action="store_true",help="Verify every entry CRC, not just radar assets")
    parser.add_argument("--report",type=Path,help="Save a JSON report")
    args = parser.parse_args(argv)
    try:
        report = verify_package(args.package,args.overview,full_crc=args.full_crc)
        if args.report:
            if args.report.resolve() in {args.package.resolve(),args.overview.resolve()} or args.report.suffix.lower() != ".json":
                raise VPKError("Report must be a separate .json file")
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    except (OSError,VPKError) as error:
        parser.exit(2,f"error: {error}\n")
    print(f"Packaged radar check: {report['status']} ({report['package_entries']} VPK entries)")
    for check in report["checks"]:
        print(f"  {check['status']}: {check['file']}")
    for error in report["errors"]:
        print("  "+error)
    print("In-game radar, dependency completeness, signatures and clean installation are not validated by this check.")
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
