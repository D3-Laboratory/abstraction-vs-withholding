#!/usr/bin/env python3
"""Build the deterministic ConVerse split used by the CI Gate experiments.

The upstream release contains 611 privacy items. Its own runner skips items whose
``attack_action`` is empty, leaving 571 executable privacy attacks.  This script
uses only that executable population.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SALT = "ci-gate:converse:d474f6a7:split-v1"
USE_CASES = ("insurance", "real_estate", "travel_planning")
PERSONAS = (1, 2, 3, 4)
PILOT_TIER_ORDER = (
    "unrelated",
    "related_but_private",
    "related_and_useful",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_key(*parts: str) -> str:
    joined = "|".join((SALT, *parts))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def canonical_tier(raw_category: str) -> str:
    if raw_category.startswith("unrelated_to_"):
        return "unrelated"
    if raw_category in {"related_but_private", "related_and_useful"}:
        return raw_category
    raise ValueError(f"Unknown ConVerse privacy category: {raw_category}")


def load_cases(converse_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    executable: list[dict[str, Any]] = []
    non_executable: list[dict[str, Any]] = []
    resources = converse_root / "resources"

    for use_case in USE_CASES:
        for persona_id in PERSONAS:
            source = (
                resources
                / f"{use_case}_usecase"
                / "privacy_attacks"
                / f"privacy_attacks_persona{persona_id}.json"
            )
            raw = source.read_bytes()
            payload = json.loads(raw)
            persona_name = payload.get("persona_name", "")
            for raw_category, category in payload["categories"].items():
                tier = canonical_tier(raw_category)
                for index, item in enumerate(category.get("items", []), start=1):
                    normalized_name = "_".join(item["data_item"].lower().split())
                    case_id = (
                        f"{use_case}.persona{persona_id}.{tier}."
                        f"{normalized_name}.{index:02d}"
                    )
                    record = {
                        "case_id": case_id,
                        "use_case": use_case,
                        "persona_id": persona_id,
                        "persona_name": persona_name,
                        "semantic_tier": tier,
                        "raw_category": raw_category,
                        "privacy_level": item.get("privacy_level", ""),
                        "data_category": item.get("category", ""),
                        "data_item": item["data_item"],
                        "extraction_snippets": item.get("extraction_snippets", []),
                        "raw_data": item.get("raw_data", []),
                        "acceptable_abstraction": item.get("acceptable_abstraction", ""),
                        "abstraction_examples": item.get("abstraction_examples", []),
                        "attack_action": item.get("attack_action", ""),
                        "attack_rationale": item.get("attack_rationale", ""),
                        "reason_not_share": item.get("reason_not_share", ""),
                        "source_file": str(source.relative_to(converse_root)),
                        "source_sha256": sha256_bytes(raw),
                    }
                    if record["attack_action"].strip():
                        executable.append(record)
                    else:
                        record["exclusion_reason"] = "empty_attack_action"
                        non_executable.append(record)

    return executable, non_executable


def assign_splits(cases: list[dict[str, Any]]) -> None:
    by_cell: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        cell = (case["use_case"], case["persona_id"], case["semantic_tier"])
        by_cell[cell].append(case)

    expected_cells = {
        (use_case, persona_id, tier)
        for use_case in USE_CASES
        for persona_id in PERSONAS
        for tier in PILOT_TIER_ORDER
    }
    if set(by_cell) != expected_cells:
        raise ValueError("ConVerse tier/persona cells do not match the expected 36 cells")

    for cell, members in by_cell.items():
        members.sort(key=lambda c: stable_key("development", c["case_id"]))
        if len(members) < 2:
            raise ValueError(f"Cell {cell} has fewer than two executable attacks")
        for case in members:
            case["split"] = "formal"
            case["pilot"] = False
        for case in members[:2]:
            case["split"] = "development"

    personas = [(use_case, persona_id) for use_case in USE_CASES for persona_id in PERSONAS]
    personas.sort(key=lambda x: stable_key("pilot-tier-order", x[0], str(x[1])))
    for position, (use_case, persona_id) in enumerate(personas):
        tier = PILOT_TIER_ORDER[position % len(PILOT_TIER_ORDER)]
        candidates = [
            case
            for case in cases
            if case["use_case"] == use_case
            and case["persona_id"] == persona_id
            and case["semantic_tier"] == tier
            and case["split"] == "development"
        ]
        candidates.sort(key=lambda c: stable_key("pilot", c["case_id"]))
        candidates[0]["pilot"] = True


def commitment(case_ids: list[str]) -> str:
    payload = "".join(f"{case_id}\n" for case_id in sorted(case_ids))
    return sha256_bytes(payload.encode("utf-8"))


def build_manifest(converse_root: Path) -> dict[str, Any]:
    cases, non_executable = load_cases(converse_root)
    assign_splits(cases)
    cases.sort(key=lambda c: c["case_id"])
    non_executable.sort(key=lambda c: c["case_id"])

    split_counts = Counter(case["split"] for case in cases)
    pilot = [case for case in cases if case["pilot"]]
    development = [case for case in cases if case["split"] == "development"]
    formal = [case for case in cases if case["split"] == "formal"]

    if (len(cases), len(non_executable)) != (571, 40):
        raise ValueError(
            f"Expected 571 executable and 40 excluded items, got "
            f"{len(cases)} and {len(non_executable)}"
        )
    if split_counts != {"development": 72, "formal": 499}:
        raise ValueError(f"Unexpected split counts: {dict(split_counts)}")
    if len(pilot) != 12:
        raise ValueError(f"Expected 12 pilot cases, got {len(pilot)}")

    pilot_personas = Counter((c["use_case"], c["persona_id"]) for c in pilot)
    pilot_tiers = Counter(c["semantic_tier"] for c in pilot)
    if set(pilot_personas.values()) != {1} or pilot_tiers != {
        "unrelated": 4,
        "related_but_private": 4,
        "related_and_useful": 4,
    }:
        raise ValueError("Pilot is not balanced across personas and semantic tiers")

    return {
        "schema_version": "ci-gate-converse-split-v1",
        "upstream": {
            "repository": "https://github.com/amrgomaaelhady/ConVerse",
            "commit": "d474f6a7eee5caec6df19ea42f112f898d6f10ac",
        },
        "salt": SALT,
        "population": {
            "reported_privacy_items": len(cases) + len(non_executable),
            "executable_privacy_attacks": len(cases),
            "excluded_empty_attack_action": len(non_executable),
        },
        "counts": {
            "development": len(development),
            "pilot": len(pilot),
            "development_reserve": len(development) - len(pilot),
            "formal": len(formal),
        },
        "commitments": {
            "executable": commitment([c["case_id"] for c in cases]),
            "development": commitment([c["case_id"] for c in development]),
            "pilot": commitment([c["case_id"] for c in pilot]),
            "formal": commitment([c["case_id"] for c in formal]),
        },
        "pilot_distribution": {
            "semantic_tier": dict(sorted(pilot_tiers.items())),
            "privacy_level": dict(sorted(Counter(c["privacy_level"] for c in pilot).items())),
            "use_case": dict(sorted(Counter(c["use_case"] for c in pilot).items())),
        },
        "cases": cases,
        "excluded_items": non_executable,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--converse-root",
        type=Path,
        default=Path("experiments/third_party/converse"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/data/processed/converse-ci-gate/split-manifest.json"),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(args.converse_root)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("FAIL: split manifest is missing or stale")
        print("PASS: split manifest is reproducible")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        "Wrote split manifest: "
        f"pilot={manifest['counts']['pilot']}, "
        f"development={manifest['counts']['development']}, "
        f"formal={manifest['counts']['formal']}"
    )


if __name__ == "__main__":
    main()
