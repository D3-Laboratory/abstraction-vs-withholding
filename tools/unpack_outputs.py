#!/usr/bin/env python3
"""Expand outputs/*.jsonl.gz into the per-record JSON files the scripts read (experiments/results/...).

    python3 tools/unpack_outputs.py            # all packs
    python3 tools/unpack_outputs.py --check    # only verify SHA-256 and record counts

Each line of a pack is {"path": <relative path>, "data": <record>}; the record is written to ROOT/path.
The written tree is git-ignored. No network access.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "MANIFEST.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify packs only, write nothing")
    ap.add_argument("--only", default="", help="substring of pack names to unpack")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total = 0
    for pack in manifest["packs"]:
        if args.only and args.only not in pack["name"]:
            continue
        n = 0
        for part in pack["files"]:
            path = ROOT / part["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != part["sha256"]:
                raise SystemExit(f"checksum mismatch: {part['file']}")
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    n += 1
                    if args.check:
                        continue
                    out = (ROOT / rec["path"]).resolve()
                    if ROOT.resolve() not in out.parents:
                        raise SystemExit(f"refusing to write outside the repository: {rec['path']}")
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(rec["data"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if n != pack["records"]:
            raise SystemExit(f"{pack['name']}: {n} records, manifest says {pack['records']}")
        total += n
    print(("checked" if args.check else "unpacked"), total, "records")


if __name__ == "__main__":
    main()
