#!/usr/bin/env python3
"""Holm's correction over the significance tests on the main runs (paper Sections IV-C to IV-E).

    python3 -I experiments/scripts/holm_main_runs_tests.py

No LLM/API calls. Reads only existing files:
  results/target-disclosure-outcome-v23-luna/judgments/*/*.json   GPT-5.6 Luna outcomes (182 cases x 8)
  the source episodes (privacy_judge_v5 appropriateness_score, completed, utility_judge)
Writes results/holm-main-runs/{numbers.json, summary.txt}.

The tests (all on GPT-5.6 Luna outcomes; the same rules as make_tables.py and
benchmark_judge_scores_withheld_vs_abstracted.py):
  T1  withheld, no defense vs strongest defense (privacy + contextual rewrite): exact McNemar (two-sided binomial)
  T2  abstracted, same pair: exact McNemar
  T3  benchmark judge score, withheld minus abstracted, within the cases that are withheld in one and abstracted in
      another of the five configurations whose redactor returns flagged items or rewrites the message: exact
      Wilcoxon signed-rank test (two-sided, zeros dropped, midranks, full enumeration)
  T4  task completion, withheld vs abstracted conversations in those five configurations: Fisher's exact test
  T5  plan coverage, same groups: Mann-Whitney U (scipy default, two-sided)
  T6  option rating, same groups: Mann-Whitney U
  T7  withheld rate, identifiers vs other items, contextual rewrite: Fisher's exact test
  T8  withheld rate, identifiers vs other items, strongest defense: Fisher's exact test
T1-T8 are the eight tests that versions v1-v4 of the paper reported in this experiment (T4-T6 treat conversations
of the same case as independent; from v3 on the paper replaced them by case-resampled confidence intervals and no
longer reports their p-values). The family of the tests still reported in the paper is T1, T2, T3, T7, T8.
Holm's step-down adjustment is applied to each family.
"""
from __future__ import annotations

import glob
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu, rankdata

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
OUT = RES / "holm-main-runs"
GATED = ("generic_feedback_v22", "ci_feedback_v22", "generic_gate_modify", "ci_gate_modify",
         "privacy_prompt_ci_gate_modify")
DIRECT_IDENTIFIERS = {"full_name", "first_name", "exact_age", "age", "age_range",
                      "exact_address", "location", "government_id_information"}  # as in make_tables.py


def mcnemar(a: dict, b: dict, cases, label) -> tuple[float, int, int]:
    lost = sum(1 for c in cases if a[c] == label and b[c] != label)
    gained = sum(1 for c in cases if a[c] != label and b[c] == label)
    m, k = lost + gained, min(lost, gained)
    return (1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)), gained, lost


def fisher(a: int, b: int, c: int, d: int) -> float:
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if p(x) <= p0 * (1 + 1e-9)))


def exact_signed_rank_p(d) -> float:
    x = np.array([v for v in d if v != 0], dtype=float)
    n = len(x)
    r = rankdata(np.abs(x))
    w_minus, mu = float(r[x < 0].sum()), r.sum() / 2
    flips = ((np.arange(2 ** n, dtype=np.int64)[:, None] >> np.arange(n)) & 1).astype(np.int8)
    return float(np.mean(np.abs(flips @ r - mu) >= abs(w_minus - mu) - 1e-9))


def holm(pvals: dict) -> dict:  # same as make_tables.py
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def main() -> None:
    luna = {}
    for f in sorted(glob.glob(str(RES / "target-disclosure-outcome-v23-luna/judgments/*/*.json"))):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        luna[(j["case_id"], j["condition"])] = j
    out = {k: j["judgment"]["outcome"] for k, j in luna.items()}
    cases = sorted({c for c, _ in luna})
    raw = {c: out[(c, "raw_prompt")] for c in cases}
    strong = {c: out[(c, "privacy_prompt_ci_gate_modify")] for c in cases}
    tests, detail = {}, {}
    tests["T1 withheld McNemar"], g, l = mcnemar(raw, strong, cases, "WITHHELD")
    detail["T1 withheld McNemar"] = {"to_withheld": g, "away_from_withheld": l}
    tests["T2 abstracted McNemar"], g, l = mcnemar(raw, strong, cases, "CONVEYED")
    detail["T2 abstracted McNemar"] = {"to_abstracted": g, "away_from_abstracted": l}

    rows = []
    for (c, cond), j in luna.items():
        o = out[(c, cond)]
        if cond in GATED and o in ("WITHHELD", "CONVEYED"):
            e = json.loads((ROOT / j["source_episode"]).read_text(encoding="utf-8"))
            u = e.get("utility_judge") or {}
            cov = None
            try:
                a, b = u["coverage"]["UTILITY"]["HOW_MANY_ITEMS_COVERED"].split("/")
                cov = int(a) / int(b)
            except Exception:
                pass
            rows.append({"case": c, "o": o, "score": float(e["privacy_judge_v5"]["target"]["parsed"]["appropriateness_score"]),
                         "done": bool(e["completed"]), "cov": cov, "rat": u.get("average_rating")})
    bycase = defaultdict(list)
    for r in rows:
        bycase[r["case"]].append(r)
    d = []
    for c in sorted(bycase):
        w = [r["score"] for r in bycase[c] if r["o"] == "WITHHELD"]
        a = [r["score"] for r in bycase[c] if r["o"] == "CONVEYED"]
        if w and a:
            d.append(sum(w) / len(w) - sum(a) / len(a))
    tests["T3 judge score within-case Wilcoxon"] = exact_signed_rank_p(d)
    detail["T3 judge score within-case Wilcoxon"] = {"n_cases": len(d), "mean_diff": sum(d) / len(d)}
    W = [r for r in rows if r["o"] == "WITHHELD"]
    A = [r for r in rows if r["o"] == "CONVEYED"]
    wd, ad = sum(r["done"] for r in W), sum(r["done"] for r in A)
    tests["T4 completion Fisher"] = fisher(wd, len(W) - wd, ad, len(A) - ad)
    detail["T4 completion Fisher"] = {"withheld": [wd, len(W)], "abstracted": [ad, len(A)]}
    for key, m in (("T5 coverage Mann-Whitney", "cov"), ("T6 rating Mann-Whitney", "rat")):
        x = [r[m] for r in W if r[m] is not None]
        y = [r[m] for r in A if r[m] is not None]
        tests[key] = float(mannwhitneyu(x, y, alternative="two-sided").pvalue)
        detail[key] = {"n_withheld": len(x), "n_abstracted": len(y), "mean_withheld": sum(x) / len(x),
                       "mean_abstracted": sum(y) / len(y)}
    for key, cond in (("T7 identifiers Fisher, contextual rewrite", "ci_gate_modify"),
                      ("T8 identifiers Fisher, strongest defense", "privacy_prompt_ci_gate_modify")):
        cnt = {True: Counter(), False: Counter()}
        for c in cases:
            member = ".".join(c.split(".")[3:-1]) in DIRECT_IDENTIFIERS
            cnt[member][out[(c, cond)] == "WITHHELD"] += 1
        di, ot = cnt[True], cnt[False]
        tests[key] = fisher(di[True], di[False], ot[True], ot[False])
        detail[key] = {"identifiers_withheld": [di[True], di[True] + di[False]],
                       "other_withheld": [ot[True], ot[True] + ot[False]]}

    fam8 = dict(tests)
    fam5 = {k: v for k, v in tests.items() if k.split()[0] in ("T1", "T2", "T3", "T7", "T8")}
    res = {"tests_raw_p": tests, "detail": detail,
           "family_v1_v4_eight_tests": {"n": len(fam8), "adjusted": holm(fam8),
                                        "significant_raw": sorted(k for k, p in fam8.items() if p < 0.05),
                                        "significant_adjusted": sorted(k for k, p in holm(fam8).items() if p < 0.05)},
           "family_reported_in_v5": {"n": len(fam5), "adjusted": holm(fam5),
                                     "significant_raw": sorted(k for k, p in fam5.items() if p < 0.05),
                                     "significant_adjusted": sorted(k for k, p in holm(fam5).items() if p < 0.05)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    a8, a5 = holm(fam8), holm(fam5)
    lines = ["Holm's correction over the tests on the main runs (GPT-5.6 Luna outcomes)",
             f"{'test':45s} {'raw p':>10s} {'Holm (8)':>10s} {'Holm (5)':>10s}"]
    for k, p in tests.items():
        lines.append(f"{k:45s} {p:10.2e} {a8[k]:10.2e} {(f'{a5[k]:10.2e}' if k in a5 else '--'):>10s}")
    same8 = res["family_v1_v4_eight_tests"]["significant_raw"] == res["family_v1_v4_eight_tests"]["significant_adjusted"]
    same5 = res["family_reported_in_v5"]["significant_raw"] == res["family_reported_in_v5"]["significant_adjusted"]
    lines += ["", f"eight-test family (v1-v4): significance at .05 unchanged by Holm: {same8}",
              f"five-test family (tests still reported in v5): significance at .05 unchanged by Holm: {same5}",
              "details: " + json.dumps(detail)]
    (OUT / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
