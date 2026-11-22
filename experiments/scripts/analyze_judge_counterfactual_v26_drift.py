#!/usr/bin/env python3
"""Drift check: original v25 labels vs the same-day re-scoring of allowed_form / ignored (v26 baseline rerun).

For every scoring model x judge x condition x version, pairs the v25 record and the rerun record of the same case
and reports: n pairs, prompt-hash matches (identical prompt text), label agreement % for the favorable label
(same definition as analyze_judge_counterfactual_v26.py) and, where defined, for PrivacyAlign omit and the
ConVerse abstraction level; favorable rate v25 vs rerun, paired difference (rerun minus v25, percentage points)
with bootstrap 95% CI (5,000 resamples, seed 25) and exact McNemar p (uncorrected and Holm over this script's
favorable + omit tests). Mean ConVerse score difference is also given.

Reads only; writes experiments/results/judge-counterfactual-v26-baseline-rerun/analysis/drift.{json,md}.

    python3 -I experiments/scripts/analyze_judge_counterfactual_v26_drift.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_judge_counterfactual_v26 import JUDGES, MODELS, boot, favorable, holm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
V25 = ROOT / "experiments/results/judge-counterfactual-v25"
RERUN = ROOT / "experiments/results/judge-counterfactual-v26-baseline-rerun"
ITEMS = ROOT / "experiments/datasets/judge-counterfactual-v25/items_v3.jsonl"
VERSIONS = ("allowed_form", "ignored")
OUT = RERUN / "analysis"


def load(root: Path, model: str, judge: str, cond: str, case: str, version: str):
    f = root / model / judge / cond / case / f"{version}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    return r if r.get("status") == "ok" else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(l)["case_id"] for l in ITEMS.read_text(encoding="utf-8").splitlines() if l.strip()]
    cells, family = {}, {}
    for model in MODELS:
        for judge, pub, mod in JUDGES:
            for cond, tag in ((pub, "published"), (mod, "modified")):
                for v in VERSIONS:
                    key = f"{model}/{judge}/{cond}({tag})/{v}"
                    pairs = [(load(V25, model, judge, cond, c, v), load(RERUN, model, judge, cond, c, v)) for c in cases]
                    pairs = [(a, b) for a, b in pairs if a and b]
                    cell = {"n_pairs": len(pairs),
                            "prompt_hash_match": sum(a["prompt_sha256"] == b["prompt_sha256"] for a, b in pairs)}
                    fns = {"favorable": lambda p, j=judge: favorable(j, p)}
                    if judge == "privacyalign":
                        fns["omits"] = lambda p: bool(p["omits"])
                    for name, fn in fns.items():
                        x = [(fn(a["parsed"]), fn(b["parsed"])) for a, b in pairs]
                        only_v25 = sum(o and not n for o, n in x)
                        only_new = sum(n and not o for o, n in x)
                        d = [100 * (int(n) - int(o)) for o, n in x]
                        p = float(binomtest(only_new, only_new + only_v25).pvalue) if only_new + only_v25 else 1.0
                        cell[name] = {"agree_pct": round(100 * sum(o == n for o, n in x) / len(x), 1),
                                      "v25_pct": round(100 * sum(o for o, _ in x) / len(x), 1),
                                      "rerun_pct": round(100 * sum(n for _, n in x) / len(x), 1),
                                      "diff_pp_rerun_minus_v25": round(sum(d) / len(d), 2), "ci95": boot(d),
                                      "only_v25": only_v25, "only_rerun": only_new, "mcnemar_p": p}
                        family[f"{key}/{name}"] = p
                    if judge == "converse":
                        lv = [(a["parsed"]["abstraction_level"], b["parsed"]["abstraction_level"]) for a, b in pairs]
                        cell["abstraction_level_agree_pct"] = round(100 * sum(o == n for o, n in lv) / len(lv), 1)
                        sd = [float(b["parsed"]["appropriateness_score"]) - float(a["parsed"]["appropriateness_score"])
                              for a, b in pairs]
                        cell["score_diff_rerun_minus_v25"] = round(sum(sd) / len(sd), 3)
                        cell["score_ci95"] = boot(sd)
                    cells[key] = cell
    adj = holm(family)
    for key, cell in cells.items():
        for name in ("favorable", "omits"):
            if name in cell:
                cell[name]["holm_p"] = round(adj[f"{key}/{name}"], 4)
    (OUT / "drift.json").write_text(json.dumps({"holm_family_size": len(family), "cells": cells}, indent=2) + "\n",
                                    encoding="utf-8")
    lines = ["# Drift check: v25 labels vs same-day rerun (allowed_form, ignored)", "",
             f"diff = rerun minus v25, percentage points, paired. Holm over {len(family)} McNemar tests.", "",
             "| model | judge | cond | version | n | prompt same | fav agree% | fav% v25 | fav% rerun | "
             "diff [95% CI] | McNemar p (Holm) | omit agree% | omit% v25/rerun | omit diff [CI] (Holm) | level agree% |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, c in cells.items():
        model, judge, cond, v = key.split("/")
        f = c["favorable"]
        o = c.get("omits")
        omit = (f"{o['agree_pct']} | {o['v25_pct']}/{o['rerun_pct']} | {o['diff_pp_rerun_minus_v25']:+.1f} "
                f"[{o['ci95'][0]:+.1f}, {o['ci95'][1]:+.1f}] ({o['holm_p']:.3g})") if o else " |  | "
        lines.append(f"| {model} | {judge} | {cond} | {v} | {c['n_pairs']} | {c['prompt_hash_match']} | {f['agree_pct']} | "
                     f"{f['v25_pct']} | {f['rerun_pct']} | {f['diff_pp_rerun_minus_v25']:+.1f} "
                     f"[{f['ci95'][0]:+.1f}, {f['ci95'][1]:+.1f}] | {f['mcnemar_p']:.3g} ({f['holm_p']:.3g}) | {omit} | "
                     f"{c.get('abstraction_level_agree_pct', '')} |")
    (OUT / "drift.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
