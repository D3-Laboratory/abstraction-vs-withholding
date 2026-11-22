#!/usr/bin/env python3
"""Benchmark judge scores of withheld vs abstracted answers (paper Section IV-D, first paragraph).

    python3 -I experiments/scripts/benchmark_judge_scores_withheld_vs_abstracted.py [--boot 5000] [--seed 25]

No LLM/API calls. Reads only existing files:
  results/target-disclosure-outcome-v23-luna/judgments/*/*.json   GPT-5.6 Luna outcome (LEAKED / CONVEYED / WITHHELD)
  the source episode named in each judgment: privacy_judge_v5.target.parsed.appropriateness_score (0-10), the
  score of ConVerse's abstraction judge ("the benchmark's judge"; GLM-5.1 in the main runs)
Writes results/benchmark-judge-scores/{numbers.json, summary.txt}.

Selection. The five configurations in which the redactor returns flagged items or rewrites the message
(generic_feedback_v22, ci_feedback_v22, generic_gate_modify, ci_gate_modify, privacy_prompt_ci_gate_modify);
contextual guidance (ci_feedback_bare_v22) and the two configurations without a redactor are left out. One
conversation per (case, configuration); a conversation is "withheld" or "abstracted" by its Luna outcome
(CONVEYED = abstracted). This is the same selection as make_tables.py numbers["judge_scores"] and
task_metrics_case_bootstrap_v3.py.

Pooled comparison. mean(withheld scores) - mean(abstracted scores) over all selected conversations; share of
perfect 10s per group. 95% CI: percentile bootstrap that resamples cases (each case with replacement, carrying
all of its selected conversations in both groups), B draws with random.Random(seed); the interval is
[sorted[int(0.025 B)], sorted[int(0.975 B)]], the same rule as task_metrics_case_bootstrap_v3.py (B = 5,000,
seed 25). Draws in which a group is empty are skipped (none occur with these data).

Within-case comparison. Cases with at least one withheld and one abstracted conversation among the five
configurations. Per case, d_c = mean(withheld scores of c) - mean(abstracted scores of c); the estimate is the
unweighted mean of d_c, and the test is the Wilcoxon signed-rank test on the d_c, two-sided, zero differences
dropped (zero_method "wilcox"), midranks for tied |d_c|. The p-value reported in the paper is the exact one: the
null distribution of the signed-rank statistic is enumerated over all 2^n sign assignments of the nonzero d_c
(n = 19 here). scipy.stats.wilcoxon is also reported; with tied |d_c| scipy 1.13 falls back to the normal
approximation, which gives a larger p.
"""
from __future__ import annotations

import argparse
import glob
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, wilcoxon

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
OUT = RES / "benchmark-judge-scores"
GATED = ("generic_feedback_v22", "ci_feedback_v22", "generic_gate_modify", "ci_gate_modify",
         "privacy_prompt_ci_gate_modify")
GROUPS = ("WITHHELD", "CONVEYED")


def load_rows() -> list[dict]:
    rows = []
    for f in sorted(glob.glob(str(RES / "target-disclosure-outcome-v23-luna/judgments/*/*.json"))):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        o = j["judgment"]["outcome"]
        if j["condition"] not in GATED or o not in GROUPS:
            continue
        e = json.loads((ROOT / j["source_episode"]).read_text(encoding="utf-8"))
        s = e["privacy_judge_v5"]["target"]["parsed"]["appropriateness_score"]
        rows.append({"case": j["case_id"], "condition": j["condition"], "outcome": o, "score": float(s)})
    return rows


def mean(v):
    return sum(v) / len(v)


def exact_signed_rank_p(d: list[float]) -> tuple[float, float, int]:
    """Two-sided exact p of the Wilcoxon signed-rank test (zeros dropped, midranks), by full enumeration."""
    x = np.array([v for v in d if v != 0], dtype=float)
    n = len(x)
    assert n <= 22, "full enumeration only for small n"
    r = rankdata(np.abs(x))
    w_minus = float(r[x < 0].sum())
    mu = r.sum() / 2
    flips = ((np.arange(2 ** n, dtype=np.int64)[:, None] >> np.arange(n)) & 1).astype(np.int8)
    null = flips @ r  # rank sum of the "negative" signs under every assignment
    p = float(np.mean(np.abs(null - mu) >= abs(w_minus - mu) - 1e-9))
    return w_minus, p, n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=25)
    args = ap.parse_args()
    rows = load_rows()
    by = {g: [r["score"] for r in rows if r["outcome"] == g] for g in GROUPS}
    pooled = {g: {"n": len(v), "mean": mean(v), "share_10_pct": 100 * sum(x == 10 for x in v) / len(v)}
              for g, v in by.items()}
    diff = pooled["WITHHELD"]["mean"] - pooled["CONVEYED"]["mean"]

    bycase = defaultdict(list)
    for r in rows:
        bycase[r["case"]].append(r)
    cases = sorted(bycase)
    rng = random.Random(args.seed)
    ds, skipped = [], 0
    for _ in range(args.boot):
        samp = [r for c in rng.choices(cases, k=len(cases)) for r in bycase[c]]
        w = [r["score"] for r in samp if r["outcome"] == "WITHHELD"]
        a = [r["score"] for r in samp if r["outcome"] == "CONVEYED"]
        if not w or not a:
            skipped += 1
            continue
        ds.append(mean(w) - mean(a))
    ds.sort()
    ci = [ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds))]]

    within = []
    for c in cases:
        w = [r["score"] for r in bycase[c] if r["outcome"] == "WITHHELD"]
        a = [r["score"] for r in bycase[c] if r["outcome"] == "CONVEYED"]
        if w and a:
            within.append({"case": c, "n_withheld": len(w), "n_abstracted": len(a), "d": mean(w) - mean(a)})
    d = [x["d"] for x in within]
    wt = wilcoxon(d)
    nonzero = sum(x != 0 for x in d)
    w_minus, p_exact, _ = exact_signed_rank_p(d)

    res = {
        "source": "target-disclosure-outcome-v23-luna (outcome) + privacy_judge_v5.target appropriateness_score",
        "configurations": list(GATED),
        "n_cases_with_selected_conversations": len(cases),
        "pooled": {
            "withheld": pooled["WITHHELD"], "abstracted": pooled["CONVEYED"],
            "diff_withheld_minus_abstracted": diff,
            "ci95_case_bootstrap": ci,
            "bootstrap": {"draws": args.boot, "seed": args.seed, "rng": "random.Random(seed).choices over cases",
                          "percentile_rule": "sorted[int(0.025*B)], sorted[int(0.975*B)]",
                          "skipped_draws": skipped},
        },
        "within_case": {
            "n_cases": len(within), "mean_diff_withheld_minus_abstracted": mean(d),
            "n_nonzero_diffs": nonzero, "n_positive": sum(x > 0 for x in d), "n_negative": sum(x < 0 for x in d),
            "wilcoxon_statistic_w_minus": w_minus, "wilcoxon_p_exact": p_exact,
            "test": "Wilcoxon signed-rank, two-sided, zeros dropped, midranks; exact enumeration over 2^n signs",
            "scipy_wilcoxon_statistic": float(wt.statistic), "scipy_wilcoxon_p": float(wt.pvalue),
            "scipy_note": "scipy.stats.wilcoxon(d) defaults; normal approximation because of tied |d|",
        },
        "rounded_as_in_paper": {
            "n_withheld": pooled["WITHHELD"]["n"], "n_abstracted": pooled["CONVEYED"]["n"],
            "mean_withheld": round(pooled["WITHHELD"]["mean"], 2), "mean_abstracted": round(pooled["CONVEYED"]["mean"], 2),
            "diff": round(diff, 2), "ci95": [round(ci[0], 2), round(ci[1], 2)],
            "share_10_withheld_pct": round(pooled["WITHHELD"]["share_10_pct"], 1),
            "share_10_abstracted_pct": round(pooled["CONVEYED"]["share_10_pct"], 1),
            "within_case_n": len(within), "within_case_mean_diff": round(mean(d), 2),
            "wilcoxon_p_exact": round(p_exact, 5),
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    r = res["rounded_as_in_paper"]
    txt = (
        "Benchmark judge (ConVerse abstraction prompt) appropriateness score, withheld vs abstracted answers\n"
        f"configurations: {', '.join(GATED)}\n"
        f"withheld   n={r['n_withheld']}  mean={pooled['WITHHELD']['mean']:.4f}  share of 10 = {r['share_10_withheld_pct']}%\n"
        f"abstracted n={r['n_abstracted']}  mean={pooled['CONVEYED']['mean']:.4f}  share of 10 = {r['share_10_abstracted_pct']}%\n"
        f"difference {diff:.4f}  95% CI [{ci[0]:.4f}, {ci[1]:.4f}]  (case bootstrap over {len(cases)} cases, "
        f"{args.boot} draws, seed {args.seed}, {skipped} skipped)\n"
        f"within-case: {len(within)} cases withheld in one configuration and abstracted in another; "
        f"mean d = {mean(d):.4f} ({res['within_case']['n_positive']} positive, {res['within_case']['n_negative']} "
        f"negative, {len(d) - nonzero} zero)\n"
        f"Wilcoxon signed-rank (two-sided, zeros dropped): W- = {w_minus:.1f}, exact p = {p_exact:.6f} "
        f"(scipy normal approximation: p = {wt.pvalue:.6f})\n"
        f"paper (IV-D): {r['mean_withheld']} vs {r['mean_abstracted']}, difference {r['diff']} "
        f"(95% CI {r['ci95'][0]:.2f}-{r['ci95'][1]:.2f}); 10s: {r['share_10_withheld_pct']}% vs "
        f"{r['share_10_abstracted_pct']}%; within {len(within)} cases {r['within_case_mean_diff']} points, "
        f"exact p = {p_exact:.4f}\n")
    (OUT / "summary.txt").write_text(txt, encoding="utf-8")
    print(txt, end="")


if __name__ == "__main__":
    main()
