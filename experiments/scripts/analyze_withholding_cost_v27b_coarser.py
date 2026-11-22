#!/usr/bin/env python3
"""v27b coarser branch: paired comparisons over the 4-variant fixed-scorer rows.

Reads <root>/<scores-dir>/episodes.jsonl (score_withholding_cost_pilot_v27.py; scores_fixed_4var/ holds the
withholding-cost-scorer-v27-fixed rows, scores_fixed_4var_v2/ the v27-fixed2 rows) and writes paired_4var.json / paired_4var.md next to it:
paired (case, seed) final-match win/loss/tie for coarser vs raw, refuse and allowed (and the
other pairs), and checks that the raw/allowed/refuse rows equal scores_fixed/episodes.jsonl.
No model calls."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VARIANTS = ["raw", "allowed", "coarser", "refuse"]


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def paired(by: dict, a: str, b: str, keys: list[tuple[str, int]]) -> dict:
    """win = a matched and b missed; loss = a missed and b matched (from a's side)."""
    w = l = t = skipped = 0
    for cid, seed in keys:
        ra, rb = by.get((cid, seed, a)), by.get((cid, seed, b))
        if ra is None or rb is None or ra["final_match"] is None or rb["final_match"] is None:
            skipped += 1
            continue
        if ra["final_match"] and not rb["final_match"]:
            w += 1
        elif rb["final_match"] and not ra["final_match"]:
            l += 1
        else:
            t += 1
    return {"a": a, "b": b, "a_match_b_miss": w, "a_miss_b_match": l, "tie": t, "pairs": w + l + t, "skipped": skipped}


def table(rs: list[dict], variant: str) -> dict:
    item_key = "item_use_assumption_turns" if variant == "raw" else "item_substitution_assumption_turns"
    ratings = [r["utility_average_rating"] for r in rs if r["utility_average_rating"] is not None]
    return {
        "n": len(rs),
        "final_match": f"{sum(1 for r in rs if r['final_match'])}/{sum(1 for r in rs if r['final_match'] is not None)}",
        "oracle_offered_by_service": f"{sum(1 for r in rs if r['service_offer_status'] == 'offered')}/{len(rs)}",
        "item_assumption_episodes": f"{sum(1 for r in rs if r.get(item_key))}/{len(rs)}",
        "item_assumption_label": "item_use" if variant == "raw" else "item_substitution",
        "utility_rating_mean": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "utility_rating_n": len(ratings),
        "completed": f"{sum(1 for r in rs if r['completed'])}/{len(rs)}",
        "reask_episodes": sum(1 for r in rs if r["reasks"]),
        "gap_closed_by_service": sum(1 for r in rs if r["gap_closed_by"] == "service"),
        "gap_closed_by_assistant": sum(1 for r in rs if r["gap_closed_by"] == "assistant"),
        "value_violation_episodes": sum(1 for r in rs if r["policy_violations"]),
        "topic_violation_episodes": sum(1 for r in rs if r["topic_violations"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO / "experiments/results/withholding-cost-pilot-v27")
    parser.add_argument("--scores-dir", default="scores_fixed_4var_v2", help="sub-directory of the root with episodes.jsonl")
    parser.add_argument("--reference-dir", default="scores_fixed",
                        help="3-variant scores the raw/allowed/refuse rows are compared with")
    args = parser.parse_args()
    out = args.root / args.scores_dir
    rs = rows(out / "episodes.jsonl")
    test = [r for r in rs if r["case_role"] == "test"]
    by = {(r["case_id"], r["seed"], r["variant"]): r for r in test}
    keys = sorted({(r["case_id"], r["seed"]) for r in test})
    result = {
        "scorer": sorted({r["scorer"] for r in rs}),
        "per_variant_test_cases": {v: table([r for r in test if r["variant"] == v], v) for v in VARIANTS},
        "paired_test_cases": [paired(by, a, b, keys) for a, b in combinations(VARIANTS, 2)],
        "per_case": {},
    }
    for cid in sorted({k[0] for k in keys}):
        result["per_case"][cid] = {v: "".join("1" if (by.get((cid, s, v)) or {}).get("final_match") else "0"
                                              for s in (0, 1, 2)) for v in VARIANTS}
    old_path = args.root / args.reference_dir / "episodes.jsonl"
    if old_path.exists():
        old = {(r["case_id"], r["seed"], r["variant"]): r for r in rows(old_path)}
        new = {(r["case_id"], r["seed"], r["variant"]): r for r in rs if r["variant"] != "coarser"}
        strip = lambda r: {k: v for k, v in (r or {}).items() if k != "scorer"}  # scorer version may differ
        diffs = [list(k) for k in sorted(set(old) | set(new)) if strip(old.get(k)) != strip(new.get(k))]
        result["consistency_with_scores_fixed"] = {"reference_dir": args.reference_dir, "rows_compared": len(set(old) | set(new)), "rows_differing": diffs}
    (out / "paired_4var.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# v27b coarser branch: 4-variant paired comparison (test cases, 9 cases x 3 seeds)", "",
             "| variant | n | final match | oracle offered | item assump. eps | rating (n) | completed |", "|---|---|---|---|---|---|---|"]
    for v, t in result["per_variant_test_cases"].items():
        lines.append(f"| {v} | {t['n']} | {t['final_match']} | {t['oracle_offered_by_service']} | {t['item_assumption_episodes']} "
                     f"({t['item_assumption_label']}) | {t['utility_rating_mean']} ({t['utility_rating_n']}) | {t['completed']} |")
    lines += ["", "| A vs B | A match, B miss | A miss, B match | tie | pairs |", "|---|---|---|---|---|"]
    for p in result["paired_test_cases"]:
        lines.append(f"| {p['a']} vs {p['b']} | {p['a_match_b_miss']} | {p['a_miss_b_match']} | {p['tie']} | {p['pairs']} |")
    lines += ["", "Per case, final match by seed s0 s1 s2:", "", "| case | " + " | ".join(VARIANTS) + " |", "|---|" + "---|" * len(VARIANTS)]
    for cid, cells in result["per_case"].items():
        lines.append(f"| {cid.replace('.related_and_useful', '')} | " + " | ".join(cells[v] for v in VARIANTS) + " |")
    (out / "paired_4var.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if "consistency_with_scores_fixed" in result:
        print("\nconsistency with scores_fixed:", json.dumps(result["consistency_with_scores_fixed"]))


if __name__ == "__main__":
    main()
