#!/usr/bin/env python3
"""Analyze the v26 judge test (explicit_refusal, coarser) against the v25 versions on the same cases.

For every scoring model x judge prompt x condition (told/untold, tagged published/modified as in the paper),
this reports the favorable-response rate of each version, using the same measures as make_tables.py (Fig. 2):
  ConVerse      favorable = abstraction_level == "appropriate"   (also mean appropriateness score)
  PrivacyAlign  favorable = not leaks                             (also omit %)
  PrivacyLens   favorable = not leaks_upstream_parser
and paired comparisons (same case, same model/judge/condition) of each new version against
  allowed_form  (v25 results, the allowed-form version)
  ignored       (v25 results, the silent-removal "withheld" version)
Paired tests follow make_tables.py: exact McNemar (binomial test on discordant pairs) for ConVerse appropriate,
leak, and PrivacyAlign omit; bootstrap 95% CI (5,000 resamples, seed 25) of the paired percentage-point
difference; ConVerse score difference with bootstrap CI and Wilcoxon (not in the Holm family, as in v25).
Holm correction is applied over one family: every McNemar test in this script (2 new versions x 2 references x
models x judges x conditions x measures). A cell with more than 2% of its new-version calls missing is reported
but left out of the tests and the family (make_tables.py's rule for unfinished runs).

Reads only; writes experiments/results/judge-counterfactual-v26/analysis/{summary.json,summary.md}.

    python3 -I experiments/scripts/analyze_judge_counterfactual_v26.py

--baseline same-day (default: v25) takes the comparators allowed_form and ignored from the same-day re-scoring
in experiments/results/judge-counterfactual-v26-baseline-rerun/ (run_judge_counterfactual_v26.py --baseline-rerun)
instead of the original v25 results; `leaked` (rates only, never tested) still comes from v25. Same tests, CI,
McNemar, Holm family and missing-data rule. Writes to
experiments/results/judge-counterfactual-v26-baseline-rerun/analysis/ and leaves the default analysis untouched.
--out-dir overrides the output folder.

    python3 -I experiments/scripts/analyze_judge_counterfactual_v26.py --baseline same-day
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from scipy.stats import binomtest, wilcoxon

ROOT = Path(__file__).resolve().parents[2]
V25 = ROOT / "experiments/results/judge-counterfactual-v25"
V26 = ROOT / "experiments/results/judge-counterfactual-v26"
DATA = ROOT / "experiments/datasets/judge-counterfactual-v26"
OUT = V26 / "analysis"
RERUN = ROOT / "experiments/results/judge-counterfactual-v26-baseline-rerun"
REF_ROOT = V25  # where allowed_form / ignored are read from; --baseline same-day sets RERUN
MODELS = ["deepseek-v4.1-flash", "gpt-oss:120b", "glm-5.3-flash", "luna"]
JUDGES = [("converse", "told", "untold"), ("privacyalign", "untold", "told"), ("privacylens_leak", "untold", "told")]
NEW = ("explicit_refusal", "coarser")
REFS = ("allowed_form", "ignored")
OLD = ("leaked", "allowed_form", "ignored")


def items(version: str) -> list[str]:
    path = DATA / f"items_v26_{version}.jsonl"
    return [json.loads(l)["case_id"] for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def record(model: str, judge: str, cond: str, case: str, version: str):
    root = V26 if version in NEW else REF_ROOT if version in REFS else V25
    f = root / model / judge / cond / case / f"{version}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    return r.get("parsed") if r.get("status") == "ok" else None


def failed_exists(model: str, judge: str, cond: str, case: str, version: str) -> bool:
    return (V26 / "_failed" / model / judge / cond / case / f"{version}.json").exists()


def favorable(judge: str, p: dict) -> bool:
    if judge == "converse":
        return p["abstraction_level"] == "appropriate"
    if judge == "privacyalign":
        return not bool(p["leaks"])
    return not bool(p["leaks_upstream_parser"])


def measures(judge: str) -> dict:
    """Binary measures tested with McNemar; value(p) -> bool."""
    m = {"favorable": lambda p: favorable(judge, p)}
    if judge == "privacyalign":
        m["omits"] = lambda p: bool(p["omits"])
    return m


def boot(diffs, n=5000, seed=25):
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return [round(ms[int(0.025 * n)], 2), round(ms[int(0.975 * n)], 2)]


def holm(pvals: dict) -> dict:
    ordered = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def rate(judge: str, ps: list) -> dict:
    ps = [p for p in ps if p is not None]
    if not ps:
        return {"n": 0}
    out = {"n": len(ps), "favorable_pct": round(100 * sum(favorable(judge, p) for p in ps) / len(ps), 1)}
    if judge == "converse":
        out["mean_score"] = round(sum(float(p["appropriateness_score"]) for p in ps) / len(ps), 2)
        out["too_vague_pct"] = round(100 * sum(p["abstraction_level"] == "too_vague" for p in ps) / len(ps), 1)
    if judge == "privacyalign":
        out["omit_pct"] = round(100 * sum(bool(p["omits"]) for p in ps) / len(ps), 1)
    return out


def main() -> None:
    global REF_ROOT, OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", choices=("v25", "same-day"), default="v25")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    if args.baseline == "same-day":
        REF_ROOT, OUT = RERUN, RERUN / "analysis"
    if args.out_dir:
        OUT = args.out_dir
    OUT.mkdir(parents=True, exist_ok=True)
    case_lists = {v: items(v) for v in NEW}
    counts, cells, family = {}, {}, {}
    for model in MODELS:
        for judge, pub, mod in JUDGES:
            for cond, tag in ((pub, "published"), (mod, "modified")):
                for new in NEW:
                    cases = case_lists[new]
                    key = f"{model}/{judge}/{cond}({tag})/{new}"
                    vals = {v: [record(model, judge, cond, c, v) for c in cases] for v in (new,) + OLD}
                    ok = sum(p is not None for p in vals[new])
                    failed = sum(failed_exists(model, judge, cond, c, new) for c, p in zip(cases, vals[new]) if p is None)
                    counts[key] = {"expected": len(cases), "ok": ok, "parse_failed": failed,
                                   "missing": len(cases) - ok - failed}
                    cell = {"cases": len(cases), "rates": {v: rate(judge, vals[v]) for v in vals},
                            "new_missing": len(cases) - ok}
                    if len(cases) - ok > 0.02 * len(cases):
                        cell["excluded_from_tests"] = "more than 2% of new-version calls missing"
                        cells[key] = cell
                        continue
                    cell["paired"] = {}
                    for ref in REFS:
                        pairs = [(x, y) for x, y in zip(vals[new], vals[ref]) if x is not None and y is not None]
                        comp = {"n_pairs": len(pairs)}
                        for mname, fn in measures(judge).items():
                            only_new = sum(fn(x) and not fn(y) for x, y in pairs)
                            only_ref = sum(fn(y) and not fn(x) for x, y in pairs)
                            p = float(binomtest(only_new, only_new + only_ref).pvalue) if only_new + only_ref else 1.0
                            d = [100 * (int(fn(x)) - int(fn(y))) for x, y in pairs]
                            comp[mname] = {"new_pct": round(100 * sum(fn(x) for x, _ in pairs) / len(pairs), 1),
                                           "ref_pct": round(100 * sum(fn(y) for _, y in pairs) / len(pairs), 1),
                                           "diff_pp_new_minus_ref": round(sum(d) / len(d), 2), "ci95": boot(d),
                                           "only_new": only_new, "only_ref": only_ref, "mcnemar_p": p}
                            family[f"{key}/vs_{ref}/{mname}"] = p
                        if judge == "converse":
                            d = [float(x["appropriateness_score"]) - float(y["appropriateness_score"]) for x, y in pairs]
                            nz = [x for x in d if x != 0]
                            comp["score_diff_new_minus_ref"] = round(sum(d) / len(d), 3)
                            comp["score_ci95"] = boot(d)
                            comp["score_wilcoxon_p"] = float(wilcoxon(nz).pvalue) if len(nz) > 5 else None
                        cell["paired"][f"vs_{ref}"] = comp
                    cells[key] = cell
    adjusted = holm(family)
    for key, cell in cells.items():
        for ref, comp in cell.get("paired", {}).items():
            for mname in ("favorable", "omits"):
                if mname in comp:
                    comp[mname]["holm_p"] = round(adjusted[f"{key}/{ref}/{mname}"], 4)
    summary = {"note": "raw results, not yet reviewed",
               "reference_root": str(REF_ROOT.relative_to(ROOT)), "holm_family_size": len(family),
               "counts": counts, "cells": cells}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = ["# Judge test v26: favorable-response rates and paired comparisons (raw, not reviewed)", "",
             f"Comparators allowed_form/ignored from {REF_ROOT.relative_to(ROOT)}. "
             f"Holm family: {len(family)} McNemar tests. diff = new minus reference, percentage points, paired.", "",
             "| model | judge | cond | version | n | fav% new | fav% allowed | fav% removed | "
             "vs allowed: diff [95% CI] Holm p | vs removed: diff [95% CI] Holm p | omit% new/allowed/removed |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, cell in cells.items():
        model, judge, cond, new = key.split("/")
        r = cell["rates"]
        fav = lambda v: r[v].get("favorable_pct", "-")
        cmp_txt = []
        for ref in REFS:
            c = cell.get("paired", {}).get(f"vs_{ref}")
            if not c:
                cmp_txt.append("excluded")
                continue
            f = c["favorable"]
            cmp_txt.append(f"{f['diff_pp_new_minus_ref']:+.1f} [{f['ci95'][0]:+.1f}, {f['ci95'][1]:+.1f}] p={f['holm_p']:.3g}")
        omit = "/".join(str(r[v].get("omit_pct", "-")) for v in (new, "allowed_form", "ignored")) if judge == "privacyalign" else ""
        lines.append(f"| {model} | {judge} | {cond} | {new} | {r[new]['n']} | {fav(new)} | {fav('allowed_form')} | "
                     f"{fav('ignored')} | {cmp_txt[0]} | {cmp_txt[1]} | {omit} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    bad = {k: v for k, v in counts.items() if v["ok"] != v["expected"]}
    print("\nincomplete cells:", json.dumps(bad, indent=1) if bad else "none")


if __name__ == "__main__":
    main()
