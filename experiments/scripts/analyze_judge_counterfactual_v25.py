#!/usr/bin/env python3
"""Summarize the counterfactual judge experiment: for each judge model, judge prompt, and condition, compare the
withheld version of each item with its allowed-form version (paired by item).

    python3 experiments/scripts/analyze_judge_counterfactual_v25.py [--strict]
"""
from __future__ import annotations

import argparse
import glob
import json
import random
from collections import defaultdict
from pathlib import Path

from scipy.stats import wilcoxon, binomtest

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results/judge-counterfactual-v25"
DATA = ROOT / "experiments/datasets/judge-counterfactual-v25"
VERSIONS = ("leaked", "allowed_form", "ignored")


def load() -> dict:
    out = defaultdict(dict)  # (model, judge, cond) -> {(case, version): parsed}
    for f in glob.glob(str(RES / "*/*/*/*/*.json")):
        r = json.loads(Path(f).read_text(encoding="utf-8"))
        if r.get("status") == "ok" and r.get("parsed"):
            out[(r["model"], r["judge"], r["condition"])][(r["case_id"], r["version"])] = r["parsed"]
    return out


def boot_ci(diffs: list[float], n: int = 5000, seed: int = 25) -> tuple[float, float]:
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def score(judge: str, p: dict):
    if judge == "converse":
        return float(p["appropriateness_score"])
    if judge == "privacylens_help":
        return float(p["score_label"] if p.get("score_label") is not None else p["score_upstream_parser"])
    return None


def binary(judge: str, p: dict) -> dict:
    if judge == "converse":
        lvl = str(p.get("abstraction_level", "")).lower()
        return {"appropriate": lvl == "appropriate", "too_vague": lvl == "too_vague", "score_10": float(p["appropriateness_score"]) == 10}
    if judge == "privacyalign":
        return {"leaks": bool(p.get("leaks")), "omits": bool(p.get("omits"))}
    if judge == "privacylens_leak":
        return {"leak": bool(p["leaks_upstream_parser"])}
    return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="only items whose prefix never disclosed the allowed form")
    args = ap.parse_args()
    items = [json.loads(l) for l in (DATA / "items_v3.jsonl").read_text(encoding="utf-8").splitlines()]
    keep = {i["case_id"] for i in items if True}
    data = load()
    summary = {}
    for key in sorted(data):
        model, judge, cond = key
        d = data[key]
        cases = sorted(c for c in keep if all((c, v) in d for v in VERSIONS))
        if not cases:
            continue
        row = {"n": len(cases)}
        for v in VERSIONS:
            vals = [score(judge, d[(c, v)]) for c in cases]
            if vals[0] is not None:
                row[f"mean_{v}"] = round(sum(vals) / len(vals), 3)
            for b, _ in binary(judge, d[(cases[0], v)]).items():
                row[f"{b}_{v}"] = round(100 * sum(binary(judge, d[(c, v)])[b] for c in cases) / len(cases), 1)
        if score(judge, d[(cases[0], "ignored")]) is not None:
            diffs = [score(judge, d[(c, "ignored")]) - score(judge, d[(c, "allowed_form")]) for c in cases]
            row["diff_withheld_minus_allowed"] = round(sum(diffs) / len(diffs), 3)
            row["diff_ci95"] = [round(x, 3) for x in boot_ci(diffs)]
            row["share_withheld_ge_allowed"] = round(100 * sum(x >= 0 for x in diffs) / len(diffs), 1)
            row["share_withheld_gt_allowed"] = round(100 * sum(x > 0 for x in diffs) / len(diffs), 1)
            nz = [x for x in diffs if x != 0]
            row["wilcoxon_p"] = float(wilcoxon(nz).pvalue) if len(nz) > 5 else None
        if judge == "privacyalign":
            # paired: is the withheld version flagged as omitting more often than the allowed form?
            a = sum(binary(judge, d[(c, "ignored")])["omits"] and not binary(judge, d[(c, "allowed_form")])["omits"] for c in cases)
            b = sum(binary(judge, d[(c, "allowed_form")])["omits"] and not binary(judge, d[(c, "ignored")])["omits"] for c in cases)
            row["omits_mcnemar_p"] = float(binomtest(a, a + b).pvalue) if a + b else 1.0
        summary["/".join(key)] = row
    name = "summary_strict.json" if args.strict else "summary.json"
    (RES / name).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for k, r in summary.items():
        print(k, json.dumps(r))


if __name__ == "__main__":
    main()
