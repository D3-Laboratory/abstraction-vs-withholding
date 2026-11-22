#!/usr/bin/env python3
"""Fully same-day recomputation of everything the paper reports about the judge test (Fig. 2), plus the v26 versions.

Sources
  same-day (2026-11-15): leaked / allowed_form / ignored from experiments/results/judge-counterfactual-v26-baseline-rerun/
                         (run_judge_counterfactual_v26.py --baseline-rerun [--baseline-versions leaked]);
                         explicit_refusal / coarser from experiments/results/judge-counterfactual-v26/ (also run that day)
  v25 (for comparison):  leaked / allowed_form / ignored from experiments/results/judge-counterfactual-v25/ (the paper's
                         source); explicit_refusal / coarser again from judge-counterfactual-v26/ (the only run)

Every measure, test and rule is copied from paper/wllfm-2026/make_tables.py (not imported, so nothing there runs):
  favorable  ConVerse abstraction_level == appropriate; PrivacyAlign not leaks; PrivacyLens not leaks_upstream_parser
  a cell (model x judge x condition) is left out if more than 2% of its 3 x 86 calls (leaked, allowed, removed) are missing
  paired removed vs allowed: exact McNemar (binomial test on discordant pairs) on ConVerse appropriate, PrivacyAlign leak
    and omit, PrivacyLens leak; paired bootstrap 95% CI (5,000 resamples, seed 25) of the percentage-point difference in
    make_tables.py's sign convention; ConVerse score difference with Wilcoxon (not in the family)
  Holm family J25: those 32 McNemar tests (24 favorable + 8 PrivacyAlign omit), exactly make_tables.py's fam1
Added here (not in make_tables.py):
  paired allowed vs leaked (favorable allowed minus leaked, PrivacyAlign omit allowed minus leaked): same tests and CI,
    their own 32-test Holm family "J25-leaked" (the paper reports leaked rates only, never a leaked test)
  J26: explicit_refusal and coarser vs allowed_form and vs removed on their own case lists
    (experiments/datasets/judge-counterfactual-v26/items_v26_<version>.jsonl), favorable + PrivacyAlign omit, one
    128-test Holm family, cells with more than 2% of new-version calls missing left out -- the rules of
    analyze_judge_counterfactual_v26.py; references are the same-day (or v25) allowed_form / ignored.

Reads only. Writes experiments/results/judge-counterfactual-v26-baseline-rerun/analysis-sameday/:
  sameday.json            all numbers for both sources
  sameday.md              tables
  fig_judges_data.csv     Fig. 2 data, five versions, both sources
  fig-judges-sameday.pdf/.png   Fig. 2 in make_tables.py's style with five versions (same-day data)
  statement_check.md      every judge-test statement in the paper with its v25 and same-day values

    python3 -I experiments/scripts/analyze_judge_counterfactual_sameday.py
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from scipy.stats import binomtest, wilcoxon

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
V25 = RES / "judge-counterfactual-v25"
V26 = RES / "judge-counterfactual-v26"
RERUN = RES / "judge-counterfactual-v26-baseline-rerun"
OUT = RERUN / "analysis-sameday"
ITEMS = [json.loads(l)["case_id"] for l in
         (ROOT / "experiments/datasets/judge-counterfactual-v25/items_v3.jsonl").read_text(encoding="utf-8").splitlines()
         if l.strip()]
NEW = ("explicit_refusal", "coarser")
NEW_ITEMS = {v: [json.loads(l)["case_id"] for l in
                 (ROOT / f"experiments/datasets/judge-counterfactual-v26/items_v26_{v}.jsonl").read_text(
                     encoding="utf-8").splitlines() if l.strip()] for v in NEW}
MODELS = [("deepseek-v4.1-flash", "DeepSeek"), ("gpt-oss:120b", "gpt-oss"), ("glm-5.3-flash", "GLM"), ("luna", "GPT-Luna")]
JUDGES = [("converse", "told", "untold"), ("privacyalign", "untold", "told"), ("privacylens_leak", "untold", "told")]
OLD = ("leaked", "allowed_form", "ignored")
ALL = OLD + NEW
LABEL = {"leaked": "Leaked", "allowed_form": "Allowed form", "ignored": "Removed",
         "explicit_refusal": "Explicit refusal", "coarser": "Coarser"}
SOURCES = {"v25": {v: V25 for v in OLD} | {v: V26 for v in NEW},
           "sameday": {v: RERUN for v in OLD} | {v: V26 for v in NEW}}


def get(src, model, judge, cond, case, version):
    f = SOURCES[src][version] / model / judge / cond / case / f"{version}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    return r.get("parsed") if r.get("status") == "ok" else None


def failed(src, model, judge, cond, case, version):
    return (SOURCES[src][version] / "_failed" / model / judge / cond / case / f"{version}.json").exists()


def fav(judge, p):
    if judge == "converse":
        return p["abstraction_level"] == "appropriate"
    if judge == "privacyalign":
        return not bool(p["leaks"])
    return not bool(p["leaks_upstream_parser"])


def boot(diffs, n=5000, seed=25):  # make_tables.py
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return [round(ms[int(0.025 * n)], 3), round(ms[int(0.975 * n)], 3)]


def holm(pvals):  # make_tables.py
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def mcn(pairs, fn_a, fn_b):
    """exact McNemar on (a, b) pairs; returns (only_a, only_b, p)"""
    oa = sum(fn_a(x) and not fn_b(y) for x, y in pairs)
    ob = sum(fn_b(y) and not fn_a(x) for x, y in pairs)
    return oa, ob, float(binomtest(oa, oa + ob).pvalue) if oa + ob else 1.0


def rates(judge, ps):
    ps = [p for p in ps if p is not None]
    if not ps:
        return {"n": 0}
    out = {"n": len(ps), "favorable": 100 * sum(fav(judge, p) for p in ps) / len(ps)}
    if judge == "converse":
        out["mean"] = sum(float(p["appropriateness_score"]) for p in ps) / len(ps)
        out["too_vague"] = 100 * sum(p["abstraction_level"] == "too_vague" for p in ps) / len(ps)
    if judge == "privacyalign":
        out["omit"] = 100 * sum(bool(p["omits"]) for p in ps) / len(ps)
    return out


def analyze(src):
    cells, fam, famL, fam26, counts = {}, {}, {}, {}, {}
    for m, _ in MODELS:
        for j, pub, mod in JUDGES:
            for cond, tag in ((pub, "published"), (mod, "modified")):
                key = f"{m}/{j}/{tag}"
                vals = {v: [get(src, m, j, cond, c, v) for c in ITEMS] for v in OLD}
                for v in NEW:
                    vals[v] = [get(src, m, j, cond, c, v) for c in NEW_ITEMS[v]]
                for v in ALL:
                    cases = ITEMS if v in OLD else NEW_ITEMS[v]
                    miss = [c for c, p in zip(cases, vals[v]) if p is None]
                    counts[f"{key}/{cond}/{v}"] = {"expected": len(cases), "ok": len(cases) - len(miss),
                                                   "parse_failed": sum(failed(src, m, j, cond, c, v) for c in miss),
                                                   "missing_cases": miss}
                n_missing = sum(p is None for v in OLD for p in vals[v])
                cell = {"cond": cond, "missing_3versions": n_missing, "rates": {v: rates(j, vals[v]) for v in ALL}}
                cells[key] = cell
                if n_missing > 0.02 * 3 * len(ITEMS):
                    cell["excluded"] = "more than 2% of the 3x86 calls missing (make_tables.py rule)"
                    continue
                # --- removed vs allowed (make_tables.py)
                pairs = [(x, y) for x, y in zip(vals["allowed_form"], vals["ignored"]) if x is not None and y is not None]
                ra = {"n_pairs": len(pairs)}
                if j == "converse":
                    ok = lambda p: p["abstraction_level"] == "appropriate"
                    a, r, p = mcn(pairs, ok, ok)
                    ra |= {"appr_allowed_only": a, "appr_removed_only": r, "p": p,
                           "appr_pp_allowed_minus_removed": sum(100 * (int(ok(x)) - int(ok(y))) for x, y in pairs) / len(pairs),
                           "ci": boot([100 * (int(ok(x)) - int(ok(y))) for x, y in pairs])}
                    d = [float(y["appropriateness_score"]) - float(x["appropriateness_score"]) for x, y in pairs]
                    nz = [x for x in d if x != 0]
                    ra |= {"score_removed_minus_allowed": sum(d) / len(d), "score_ci": boot(d),
                           "score_wilcoxon_p": float(wilcoxon(nz).pvalue) if len(nz) > 5 else 1.0}
                    fam[f"{key}/appropriate"] = p
                else:
                    k = "leaks" if j == "privacyalign" else "leaks_upstream_parser"
                    lk = lambda q: bool(q[k])
                    a, r, p = mcn(pairs, lk, lk)
                    d = [100 * (int(lk(x)) - int(lk(y))) for x, y in pairs]
                    ra |= {"leak_allowed_only": a, "leak_removed_only": r, "p": p,
                           "fav_pp_removed_minus_allowed": sum(d) / len(d), "ci": boot(d)}
                    fam[f"{key}/leak"] = p
                    if j == "privacyalign":
                        om = lambda q: bool(q["omits"])
                        ob, oa, po = mcn(pairs, om, om)  # (allowed only, removed only)
                        d = [100 * (int(om(y)) - int(om(x))) for x, y in pairs]
                        ra |= {"omit_removed_only": oa, "omit_allowed_only": ob, "omit_p": po,
                               "omit_pp_removed_minus_allowed": sum(d) / len(d), "omit_ci": boot(d)}
                        fam[f"{key}/omit"] = po
                cell["removed_vs_allowed"] = ra
                # --- allowed vs leaked (added)
                pairs = [(x, y) for x, y in zip(vals["allowed_form"], vals["leaked"]) if x is not None and y is not None]
                fa = lambda q: fav(j, q)
                a, l, p = mcn(pairs, fa, fa)
                d = [100 * (int(fa(x)) - int(fa(y))) for x, y in pairs]
                al = {"n_pairs": len(pairs), "allowed_only": a, "leaked_only": l, "p": p,
                      "fav_pp_allowed_minus_leaked": sum(d) / len(d), "ci": boot(d)}
                famL[f"{key}/favorable"] = p
                if j == "privacyalign":
                    om = lambda q: bool(q["omits"])
                    a2, l2, p2 = mcn(pairs, om, om)
                    d = [100 * (int(om(x)) - int(om(y))) for x, y in pairs]
                    al |= {"omit_allowed_only": a2, "omit_leaked_only": l2, "omit_p": p2,
                           "omit_pp_allowed_minus_leaked": sum(d) / len(d), "omit_ci": boot(d)}
                    famL[f"{key}/omit"] = p2
                cell["allowed_vs_leaked"] = al
                # --- J26: new versions vs allowed / removed
                cell["j26"] = {}
                for new in NEW:
                    cases = NEW_ITEMS[new]
                    nv = vals[new]
                    if sum(p is None for p in nv) > 0.02 * len(cases):
                        cell["j26"][new] = {"excluded": "more than 2% of new-version calls missing"}
                        continue
                    ref_by_case = {v: dict(zip(ITEMS, vals[v])) for v in ("allowed_form", "ignored")}
                    res = {}
                    for ref in ("allowed_form", "ignored"):
                        pairs = [(x, ref_by_case[ref][c]) for c, x in zip(cases, nv)
                                 if x is not None and ref_by_case[ref].get(c) is not None]
                        comp = {"n_pairs": len(pairs)}
                        ms = {"favorable": fa} | ({"omit": lambda q: bool(q["omits"])} if j == "privacyalign" else {})
                        for mn, fn in ms.items():
                            a, b, p = mcn(pairs, fn, fn)
                            d = [100 * (int(fn(x)) - int(fn(y))) for x, y in pairs]
                            comp[mn] = {"new_pct": 100 * sum(fn(x) for x, _ in pairs) / len(pairs),
                                        "ref_pct": 100 * sum(fn(y) for _, y in pairs) / len(pairs),
                                        "diff_pp_new_minus_ref": sum(d) / len(d), "ci": boot(d),
                                        "only_new": a, "only_ref": b, "p": p}
                            fam26[f"{key}/{new}/vs_{ref}/{mn}"] = p
                        res[f"vs_{ref}"] = comp
                    cell["j26"][new] = res
    adj, adjL, adj26 = holm(fam), holm(famL), holm(fam26)
    for key, cell in cells.items():
        if "excluded" in cell:
            continue
        ra = cell["removed_vs_allowed"]
        meas = "appropriate" if key.split("/")[1] == "converse" else "leak"
        ra["holm_p"] = adj[f"{key}/{meas}"]
        if "omit_p" in ra:
            ra["omit_holm_p"] = adj[f"{key}/omit"]
        al = cell["allowed_vs_leaked"]
        al["holm_p"] = adjL[f"{key}/favorable"]
        if "omit_p" in al:
            al["omit_holm_p"] = adjL[f"{key}/omit"]
        for new, res in cell["j26"].items():
            for ref, comp in res.items():
                if ref.startswith("vs_"):
                    for mn in ("favorable", "omit"):
                        if mn in comp:
                            comp[mn]["holm_p"] = adj26[f"{key}/{new}/{ref}/{mn}"]
    return {"cells": cells, "counts": counts,
            "family_sizes": {"J25 (paper, removed vs allowed)": len(fam), "J25-leaked (allowed vs leaked)": len(famL),
                             "J26 (new versions vs allowed/removed)": len(fam26)}}


# ------------------------------------------------------------------ statement check
M = [m for m, _ in MODELS]
MN = dict(MODELS)


def cell(a, m, j, tag):
    return a["cells"][f"{m}/{j}/{tag}"]


def rate(a, m, j, tag, v, meas="favorable"):
    return cell(a, m, j, tag)["rates"][v][meas]


def rng(xs, fmt="{:.0f}"):
    return f"{fmt.format(min(xs))}–{fmt.format(max(xs))}"


def P(p):
    return "<.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def ci(c):
    return f"{c[0]:.0f}–{c[1]:.0f}"


def statements(a):
    """value string per statement id for one source; plus a dict of booleans used for the verdicts"""
    s, b = {}, {}
    ok = all("excluded" not in cell(a, m, j, t) for m in M for j, _, _ in JUDGES for t in ("published", "modified"))
    b["all_cells_present"] = ok
    # PrivacyLens, released (untold)
    pl_allowed = [rate(a, m, "privacylens_leak", "published", "allowed_form") for m in M]
    pl_leaked = [rate(a, m, "privacylens_leak", "published", "leaked") for m in M]
    pl_removed = [rate(a, m, "privacylens_leak", "published", "ignored") for m in M]
    ra = {m: cell(a, m, "privacylens_leak", "published")["removed_vs_allowed"] for m in M}
    s["pl_flag_range"] = f"flags {rng([100 - x for x in pl_allowed])}% of allowed-form messages"
    s["pl_rates"] = (f"allowed {rng(pl_allowed)}%, leaked {rng(pl_leaked)}%, removed {rng(pl_removed)}% favorable")
    lo = min(M, key=lambda m: ra[m]["fav_pp_removed_minus_allowed"])
    hi = max(M, key=lambda m: ra[m]["fav_pp_removed_minus_allowed"])
    s["pl_diff"] = (f"{ra[lo]['fav_pp_removed_minus_allowed']:.0f} ({ci(ra[lo]['ci'])}) under {MN[lo]} to "
                    f"{ra[hi]['fav_pp_removed_minus_allowed']:.0f} ({ci(ra[hi]['ci'])}) under {MN[hi]}")
    s["pl_holm"] = "Holm p: " + ", ".join(f"{MN[m]} {P(ra[m]['holm_p'])}" for m in M)
    b["pl_removal_sig_all4"] = all(ra[m]["holm_p"] < 0.05 and ra[m]["fav_pp_removed_minus_allowed"] > 0 for m in M)
    b["pl_flags_majority_all4"] = all(100 - x > 50 for x in pl_allowed)
    # Raj Sharma example: insurance.persona2 full_name, released PrivacyLens prompt
    case = "insurance.persona2.related_and_useful.full_name.01"
    src = a["src"]
    flag_a = [get(src, m, "privacylens_leak", "untold", case, "allowed_form") for m in M]
    flag_r = [get(src, m, "privacylens_leak", "untold", case, "ignored") for m in M]
    fa = sum(bool(p and p["leaks_upstream_parser"]) for p in flag_a)
    fr = sum(bool(p and not p["leaks_upstream_parser"]) for p in flag_r)
    s["raj"] = f"allowed form flagged by {fa}/4; removed not flagged by {fr}/4 (" + ", ".join(
        f"{MN[m]}: {'Y' if x and x['leaks_upstream_parser'] else 'N'}/{'Y' if y and y['leaks_upstream_parser'] else 'N'}"
        for m, x, y in zip(M, flag_a, flag_r)) + ")"
    # PrivacyLens told
    s["pl_told_glm_luna"] = ("allowed " + ", ".join(f"{MN[m]} {rate(a, m, 'privacylens_leak', 'modified', 'allowed_form'):.0f}%"
                                                    for m in ("glm-5.3-flash", "luna")) +
                             "; removed " + ", ".join(f"{MN[m]} {rate(a, m, 'privacylens_leak', 'modified', 'ignored'):.0f}%"
                                                      for m in ("glm-5.3-flash", "luna")))
    s["pl_told_ds_oss"] = "allowed " + ", ".join(f"{MN[m]} {rate(a, m, 'privacylens_leak', 'modified', 'allowed_form'):.0f}%"
                                                 for m in ("deepseek-v4.1-flash", "gpt-oss:120b"))
    # PrivacyAlign released (untold)
    pa = {m: cell(a, m, "privacyalign", "published")["removed_vs_allowed"] for m in M}
    ds = pa["deepseek-v4.1-flash"]
    s["pa_ds"] = (f"removed {rate(a, 'deepseek-v4.1-flash', 'privacyalign', 'published', 'ignored'):.0f}% vs allowed "
                  f"{rate(a, 'deepseek-v4.1-flash', 'privacyalign', 'published', 'allowed_form'):.0f}%, diff "
                  f"{ds['fav_pp_removed_minus_allowed']:.0f} ({ci(ds['ci'])}), Holm p {P(ds['holm_p'])}")
    g = pa["glm-5.3-flash"]
    s["pa_glm"] = (f"removed {rate(a, 'glm-5.3-flash', 'privacyalign', 'published', 'ignored'):.0f}% vs allowed "
                   f"{rate(a, 'glm-5.3-flash', 'privacyalign', 'published', 'allowed_form'):.0f}%, raw p {P(g['p'])}, "
                   f"Holm p {P(g['holm_p'])}")
    s["pa_other2"] = ", ".join(f"{MN[m]} diff {pa[m]['fav_pp_removed_minus_allowed']:+.0f}, raw p {P(pa[m]['p'])}, "
                               f"Holm {P(pa[m]['holm_p'])}" for m in ("gpt-oss:120b", "luna"))
    b["pa_ds_sig"] = ds["holm_p"] < 0.05 and ds["fav_pp_removed_minus_allowed"] > 0
    b["pa_glm_rawsig_not_holm"] = g["p"] < 0.05 and g["holm_p"] >= 0.05 and g["fav_pp_removed_minus_allowed"] > 0
    b["pa_other2_ns"] = all(pa[m]["holm_p"] >= 0.05 for m in ("gpt-oss:120b", "luna"))
    b["pa_allowed_pref_none"] = all(not (pa[m]["holm_p"] < 0.05 and pa[m]["fav_pp_removed_minus_allowed"] < 0) for m in M)
    s["pa_omit_pub"] = ("omit removed−allowed: " + ", ".join(
        f"{MN[m]} {pa[m]['omit_pp_removed_minus_allowed']:+.0f} (Holm {P(pa[m]['omit_holm_p'])})" for m in M))
    b["pa_omit_pub_ns"] = all(pa[m]["omit_holm_p"] >= 0.05 for m in M)
    b["pa_omit_pub_max7"] = max(abs(pa[m]["omit_pp_removed_minus_allowed"]) for m in M) <= 7.5
    b["pa_omit_pub_maxabs"] = max(abs(pa[m]["omit_pp_removed_minus_allowed"]) for m in M)
    ceil = [rate(a, m, "privacyalign", "published", v, "omit") for m in ("gpt-oss:120b", "luna") for v in OLD]
    s["pa_ceiling"] = f"gpt-oss & GPT-Luna omit %, all three versions: {rng(ceil)}%"
    pm = {m: cell(a, m, "privacyalign", "modified")["removed_vs_allowed"] for m in M}
    nsig = [m for m in M if pm[m]["omit_holm_p"] < 0.05]
    s["pa_omit_told"] = (f"{len(nsig)}/4 sig ({', '.join(MN[m] for m in nsig)}); GLM omit removed "
                         f"{rate(a, 'glm-5.3-flash', 'privacyalign', 'modified', 'ignored', 'omit'):.0f}% vs allowed "
                         f"{rate(a, 'glm-5.3-flash', 'privacyalign', 'modified', 'allowed_form', 'omit'):.0f}%")
    b["pa_omit_told_n"] = len(nsig)
    # ConVerse released (told)
    cv = {m: cell(a, m, "converse", "published")["removed_vs_allowed"] for m in M}
    ca = [rate(a, m, "converse", "published", "allowed_form") for m in M]
    cr = [rate(a, m, "converse", "published", "ignored") for m in M]
    s["cv_rates"] = f"allowed {rng(ca)}% vs removed {rng(cr)}% appropriate"
    lo = min(M, key=lambda m: cv[m]["appr_pp_allowed_minus_removed"])
    hi = max(M, key=lambda m: cv[m]["appr_pp_allowed_minus_removed"])
    s["cv_diff"] = (f"{cv[lo]['appr_pp_allowed_minus_removed']:.0f} ({ci(cv[lo]['ci'])}) under {MN[lo]} to "
                    f"{cv[hi]['appr_pp_allowed_minus_removed']:.0f} ({ci(cv[hi]['ci'])}) under {MN[hi]}; max Holm p "
                    f"{P(max(cv[m]['holm_p'] for m in M))}")
    b["cv_sig_all4"] = all(cv[m]["holm_p"] < 0.05 and cv[m]["appr_pp_allowed_minus_removed"] > 0 for m in M)
    b["cv_max_holm"] = max(cv[m]["holm_p"] for m in M)
    tv = [rate(a, m, "converse", "published", "ignored", "too_vague") for m in M]
    s["cv_vague"] = f"too vague among removed: {rng(tv)}%"
    sc = [-cv[m]["score_removed_minus_allowed"] for m in M]
    s["cv_score"] = f"allowed − removed mean score {rng(sc, '{:.1f}')}"
    s["cv_luna"] = (f"appropriate allowed {rate(a, 'luna', 'converse', 'published', 'allowed_form'):.0f}% vs removed "
                    f"{rate(a, 'luna', 'converse', 'published', 'ignored'):.0f}%; mean score "
                    f"{rate(a, 'luna', 'converse', 'published', 'allowed_form', 'mean'):.1f} vs "
                    f"{rate(a, 'luna', 'converse', 'published', 'ignored', 'mean'):.1f}")
    cu = {m: cell(a, m, "converse", "modified")["removed_vs_allowed"] for m in M}
    s["cv_untold"] = (f"allowed {rng([rate(a, m, 'converse', 'modified', 'allowed_form') for m in M])}%, removed "
                      f"{rng([rate(a, m, 'converse', 'modified', 'ignored') for m in M])}%; min Holm p "
                      f"{P(min(cu[m]['holm_p'] for m in M))}, min raw p {P(min(cu[m]['p'] for m in M))}")
    b["cv_untold_ns"] = all(cu[m]["holm_p"] >= 0.05 for m in M)
    # GLM missing cell
    miss = {k: v for k, v in a["counts"].items() if v["ok"] != v["expected"]}
    s["missing"] = "; ".join(f"{k}: {v['ok']}/{v['expected']} ({v['parse_failed']} parse-failed)" for k, v in miss.items()) or "none"
    b["missing"] = miss
    # neither released prompt w/o reference prefers allowed over removal (PA leak, PA omit, PL leak; Holm)
    pl_pref_allowed = any(ra[m]["holm_p"] < 0.05 and ra[m]["fav_pp_removed_minus_allowed"] < 0 for m in M)
    pa_omit_pref_allowed = any(pa[m]["omit_holm_p"] < 0.05 and pa[m]["omit_pp_removed_minus_allowed"] > 0 for m in M)
    b["neither_prefers_allowed"] = not pl_pref_allowed and b["pa_allowed_pref_none"] and not pa_omit_pref_allowed
    return s, b


STATEMENTS = [  # (id, section, quoted text, value key, verdict function(b25,bsd,s25,ssd) -> str or None)
    ("abs1", "00 Abstract", "Neither released prompt without an allowed-form reference shows a statistically significant preference for allowed-form sharing over removal",
     None, "neither_prefers_allowed"),
    ("abs2", "00 Abstract", "across four scoring models the PrivacyLens prompt flags 55% to 79% of allowed-form messages as leaks", "pl_flag_range", None),
    ("abs3", "00 Abstract", "whereas ConVerse's prompt, which includes the reference, favors allowed-form sharing", "cv_diff", "cv_sig_all4"),
    ("c3a", "01 Intro C3", "neither released privacy-judge prompt without an allowed-form reference significantly favors allowed-form sharing over removal", None, "neither_prefers_allowed"),
    ("c3b", "01 Intro C3", "and one of them significantly favors removal under all four models", "pl_holm", "pl_removal_sig_all4"),
    ("c3c", "01 Intro C3", "the ConVerse prompt significantly favors allowed-form sharing when given that reference", "cv_diff", "cv_sig_all4"),
    ("set1", "04 setup", "One GLM call on a leaked-version message reached its output limit without an answer, so that cell has 85 cases instead of 86. (also Fig. 2 caption: except the PrivacyLens/GLM leaked condition (85))", "missing", None),
    ("pl1", "04 PL", "PrivacyLens's judge counts the allowed form as a leak under all four scoring models: only 21% to 45% of allowed-form messages receive a favorable response, against 5% to 14% for the raw value and 66% to 94% for the removed version", "pl_rates", "pl_flags_majority_all4"),
    ("pl2", "04 PL", "The paired difference between the removed version and the allowed form ranges from 45 percentage points (95% bootstrap confidence interval 33–57) under DeepSeek V4.1 Flash to 64 points (53–74) under GPT-5.6 Luna", "pl_diff", None),
    ("pl3", "04 PL", "It is significant under every model after Holm's correction across the 32 paired tests of this experiment (adjusted p < .001)", "pl_holm", "pl_removal_sig_all4"),
    ("pl4", "04 PL", "When the full name \"Raj Sharma\" is replaced by its allowed form \"Raj S.\", for example, all four models flag the message as leaking, while three of the four do not flag the version without the name", "raj", None),
    ("pl5", "04 PL", "When the allowed form is added to the prompt, GLM-5.3-Flash and GPT-5.6 Luna no longer flag it (100% and 99% favorable), but the removed version is about as favorable (100% and 95%)", "pl_told_glm_luna", None),
    ("pl6", "04 PL", "DeepSeek V4.1 Flash and gpt-oss-120b still respond favorably to only 48% and 67% of allowed-form messages", "pl_told_ds_oss", None),
    ("pa1", "04 PA", "PrivacyAlign's leak flag responds favorably to the removed version more often than to the allowed form under DeepSeek V4.1 Flash (52% against 29%, difference 23 points, 14–33; adjusted p < .001)", "pa_ds", "pa_ds_sig"),
    ("pa2", "04 PA", "Under GLM-5.3-Flash it shows the same direction without surviving correction (66% against 55%, raw p = .021, adjusted p = .40)", "pa_glm", "pa_glm_rawsig_not_holm"),
    ("pa3", "04 PA", "under the other two models it shows no significant difference between the versions", "pa_other2", "pa_other2_ns"),
    ("pa4", "04 PA", "For its omission flag ... we find no significant difference between removed and allowed-form messages under any of the four scoring models; the observed differences are at most 7 percentage points", "pa_omit_pub", "pa_omit_pub_ns"),
    ("pa5", "04 PA", "Under gpt-oss-120b and GPT-5.6 Luna, the omission flag is close to its ceiling for every version, including the leaked one (78% to 99%)", "pa_ceiling", None),
    ("pa6", "04 PA", "Once the allowed form is added to the prompt, the omission flag differs significantly between the two versions under three of the four models; under GLM-5.3-Flash, for example, it flags 69% of removed messages and 13% of allowed-form ones", "pa_omit_told", None),
    ("cv1", "04 CV", "ConVerse's judge labels allowed-form messages appropriate more often than removed messages under all four scoring models (85% to 97% against 37% to 83%)", "cv_rates", "cv_sig_all4"),
    ("cv2", "04 CV", "the paired differences range from 14 points (7–22) under GLM-5.3-Flash to 54 points (42–64) under DeepSeek V4.1 Flash and remain significant after Holm's correction (adjusted p ≤ .032)", "cv_diff", "cv_sig_all4"),
    ("cv3", "04 CV", "It labels 8% to 45% of removed messages as too vague", "cv_vague", None),
    ("cv4", "04 CV", "the allowed form scores only 0.8 to 1.9 points higher on average", "cv_score", None),
    ("cv5", "04 CV", "Under GPT-5.6 Luna, for example, 92% of allowed-form messages and 51% of removed ones are labeled appropriate, but their mean scores are 8.9 and 7.9", "cv_luna", None),
    ("cv6", "04 CV", "Without the allowed form in its prompt, ConVerse's judge labels 73% to 90% of allowed-form messages and 69% to 92% of removed ones appropriate, and none of the paired differences is significant", "cv_untold", "cv_untold_ns"),
    ("d1", "05 Discussion", "the judge that checks for partial disclosure flagged most allowed-form messages as leaking", "pl_flag_range", "pl_flags_majority_all4"),
    ("d2", "05 Discussion", "PrivacyAlign's omission flag showed no significant difference between removed and allowed-form messages", "pa_omit_pub", "pa_omit_pub_ns"),
    ("d3", "05 Discussion", "Among the released prompts, only ConVerse's, which includes the allowed form, responded more favorably to allowed-form messages", "cv_diff", "neither_prefers_allowed"),
    ("d4", "05 Discussion", "once the allowed form was added to PrivacyAlign's prompt, its omission flag also differed significantly between the two versions under three of the four scoring models", "pa_omit_told", None),
    ("k1", "07 Conclusion", "neither released prompt without an allowed-form reference shows a significant preference for allowed-form sharing over removal", None, "neither_prefers_allowed"),
    ("k2", "07 Conclusion", "PrivacyLens significantly favors removal across all four scoring models, flagging 55% to 79% of allowed-form messages as leaks", "pl_flag_range", "pl_removal_sig_all4"),
    ("k3", "07 Conclusion", "ConVerse's released prompt, the only one that includes the allowed form, significantly favors allowed-form sharing across all four models", "cv_diff", "cv_sig_all4"),
    ("k4", "07 Conclusion", "after the reference is removed, no paired difference is statistically significant", "cv_untold", "cv_untold_ns"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for src in SOURCES:
        a = analyze(src)
        a["src"] = src
        res[src] = a
    st = {src: statements(res[src]) for src in res}
    dump = {src: {k: v for k, v in res[src].items() if k != "src"} | {"statement_values": st[src][0],
                                                                       "statement_flags": st[src][1]} for src in res}
    dump["sources"] = {s: {v: str(p.relative_to(ROOT)) for v, p in d.items()} for s, d in SOURCES.items()}
    (OUT / "sameday.json").write_text(json.dumps(dump, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

    # --- tables
    L = ["# Judge test, fully same-day (2026-11-15) vs v25", "",
         "Holm families: " + json.dumps(res["sameday"]["family_sizes"]), "",
         "## Favorable % per version (n) and removed vs allowed (paper's J25 family)", "",
         "| source | model | judge | cond | leaked | allowed | removed | refusal | coarser | removed−allowed (or allowed−removed for ConVerse) [CI] raw p / Holm p | allowed−leaked [CI] Holm p | omit% L/A/R | omit R−A [CI] Holm |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, _ in MODELS:
        for j, pub, mod in JUDGES:
            for tag in ("published", "modified"):
                for src in ("v25", "sameday"):
                    c = res[src]["cells"][f"{m}/{j}/{tag}"]
                    r = c["rates"]
                    f = lambda v: f"{r[v]['favorable']:.1f} ({r[v]['n']})" if r[v].get("n") else "-"
                    if "excluded" in c:
                        L.append(f"| {src} | {m} | {j} | {c['cond']}({tag}) | {f('leaked')} | {f('allowed_form')} | "
                                 f"{f('ignored')} | {f('explicit_refusal')} | {f('coarser')} | excluded | | | |")
                        continue
                    ra, al = c["removed_vs_allowed"], c["allowed_vs_leaked"]
                    dk = "appr_pp_allowed_minus_removed" if j == "converse" else "fav_pp_removed_minus_allowed"
                    om = om2 = ""
                    if j == "privacyalign":
                        om = "/".join(f"{r[v]['omit']:.1f}" for v in OLD)
                        om2 = f"{ra['omit_pp_removed_minus_allowed']:+.1f} [{ra['omit_ci'][0]:+.1f}, {ra['omit_ci'][1]:+.1f}] {P(ra['omit_holm_p'])}"
                    L.append(f"| {src} | {m} | {j} | {c['cond']}({tag}) | {f('leaked')} | {f('allowed_form')} | "
                             f"{f('ignored')} | {f('explicit_refusal')} | {f('coarser')} | {ra[dk]:+.1f} "
                             f"[{ra['ci'][0]:+.1f}, {ra['ci'][1]:+.1f}] {P(ra['p'])} / {P(ra['holm_p'])} | "
                             f"{al['fav_pp_allowed_minus_leaked']:+.1f} [{al['ci'][0]:+.1f}, {al['ci'][1]:+.1f}] "
                             f"{P(al['holm_p'])} | {om} | {om2} |")
    L += ["", "## ConVerse scores and too-vague rates", "",
          "| source | model | cond | mean score L/A/R/ref/coarser | too vague % L/A/R/ref/coarser | score removed−allowed [CI] Wilcoxon p |",
          "|---|---|---|---|---|---|"]
    for m, _ in MODELS:
        for tag in ("published", "modified"):
            for src in ("v25", "sameday"):
                c = res[src]["cells"][f"{m}/converse/{tag}"]
                if "excluded" in c:
                    continue
                r, ra = c["rates"], c["removed_vs_allowed"]
                L.append(f"| {src} | {m} | {c['cond']}({tag}) | " + "/".join(f"{r[v]['mean']:.2f}" for v in ALL) + " | "
                         + "/".join(f"{r[v]['too_vague']:.1f}" for v in ALL) +
                         f" | {ra['score_removed_minus_allowed']:+.2f} [{ra['score_ci'][0]:+.2f}, {ra['score_ci'][1]:+.2f}] "
                         f"{P(ra['score_wilcoxon_p'])} |")
    L += ["", "## J26: explicit refusal / coarser vs allowed and removed (same-source references; 128-test Holm family)", "",
          "| source | model | judge | cond | version | measure | vs allowed: diff [CI] Holm p | vs removed: diff [CI] Holm p |",
          "|---|---|---|---|---|---|---|---|"]
    for m, _ in MODELS:
        for j, _, _ in JUDGES:
            for tag in ("published", "modified"):
                for new in NEW:
                    for src in ("v25", "sameday"):
                        c = res[src]["cells"][f"{m}/{j}/{tag}"]
                        jj = c.get("j26", {}).get(new)
                        if not jj or "excluded" in jj:
                            L.append(f"| {src} | {m} | {j} | {c['cond']}({tag}) | {new} | - | excluded | excluded |")
                            continue
                        for mn in ("favorable", "omit"):
                            if mn not in jj["vs_allowed_form"]:
                                continue
                            t = [jj[f"vs_{r}"][mn] for r in ("allowed_form", "ignored")]
                            L.append(f"| {src} | {m} | {j} | {c['cond']}({tag}) | {new} | {mn} | " + " | ".join(
                                f"{x['diff_pp_new_minus_ref']:+.1f} [{x['ci'][0]:+.1f}, {x['ci'][1]:+.1f}] {P(x['holm_p'])}"
                                for x in t) + " |")
    L += ["", "## Calls that are not ok (expected vs ok)", ""]
    for src in res:
        miss = {k: v for k, v in res[src]["counts"].items() if v["ok"] != v["expected"]}
        L.append(f"- {src}: " + ("; ".join(f"{k} {v['ok']}/{v['expected']} (parse_failed {v['parse_failed']}, cases "
                                         f"{', '.join(v['missing_cases'])})" for k, v in miss.items()) or "none"))
    (OUT / "sameday.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # --- statement check
    S = ["# Statement check: judge-test statements in the paper, v25 vs fully same-day", "",
         "Automatic flag columns: the boolean pattern the statement asserts (True = holds). Numeric wording is compared by hand.", "",
         "| id | section | statement (quoted) | v25 value | same-day value | qualitative flag v25 / same-day |",
         "|---|---|---|---|---|---|"]
    for sid, sec, quote, vk, bk in STATEMENTS:
        v25 = st["v25"][0].get(vk, "") if vk else ""
        sd = st["sameday"][0].get(vk, "") if vk else ""
        fl = f"{st['v25'][1][bk]} / {st['sameday'][1][bk]}" if bk else ""
        S.append(f"| {sid} | {sec} | {quote} | {v25} | {sd} | {fl} |")
    S += ["", "Other flags: " + json.dumps({src: {k: v for k, v in st[src][1].items() if k != "missing"} for src in st},
                                           default=str)]
    (OUT / "statement_check.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    # --- figure data and figure (make_tables.py style, five versions)
    with (OUT / "fig_judges_data.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "model", "judge", "condition", "prompt", "version", "n", "favorable_pct"])
        for src in res:
            for m, _ in MODELS:
                for j, pub, mod in JUDGES:
                    for cond, tag in ((pub, "published"), (mod, "modified")):
                        r = res[src]["cells"][f"{m}/{j}/{tag}"]["rates"]
                        for v in ALL:
                            w.writerow([src, m, j, cond, "released" if tag == "published" else "modified", v,
                                        r[v].get("n", 0), round(r[v]["favorable"], 2) if r[v].get("n") else ""])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman"],
                         "mathtext.fontset": "stix", "font.size": 7, "axes.linewidth": 0.5,
                         "xtick.major.width": 0.5, "ytick.major.width": 0.5, "pdf.fonttype": 42})
    color = {"leaked": "#9a9a9a", "allowed_form": "#1f5fa8", "ignored": "#d1641c",
             "explicit_refusal": "#7b3fa0", "coarser": "#2a8a4a"}
    marker = {"leaked": "x", "allowed_form": "o", "ignored": "s", "explicit_refusal": "^", "coarser": "D"}
    offs = {"leaked": 0.0, "allowed_form": 0.0, "ignored": 0.0, "explicit_refusal": 0.18, "coarser": -0.18}
    names = {"converse": "ConVerse", "privacyalign": "PrivacyAlign", "privacylens_leak": "PrivacyLens"}
    cells = res["sameday"]["cells"]
    fig, axs = plt.subplots(3, 2, figsize=(3.45, 3.9), sharey=True, sharex=True)
    for col, sees in enumerate((True, False)):
        for row, (j, pub, mod) in enumerate(JUDGES):
            ax = axs[row, col]
            tag = "published" if (pub == "told") == sees else "modified"
            for i, (m, _) in enumerate(MODELS):
                r = cells[f"{m}/{j}/{tag}"]["rates"]
                ax.plot([i, i], [r["allowed_form"]["favorable"], r["ignored"]["favorable"]], color="#c8c8c8", lw=1.0, zorder=1)
                for v in ALL:
                    if r[v].get("n"):
                        ax.scatter(i + offs[v], r[v]["favorable"], marker=marker[v], s=9 if v != "leaked" else 8,
                                   color=color[v], zorder=3, linewidths=0.7)
            ax.set_ylim(-5, 105); ax.set_yticks([0, 50, 100]); ax.grid(axis="y", lw=0.3, color="#e0e0e0")
            ax.set_xticks(range(len(MODELS))); ax.set_xticklabels([lab for _, lab in MODELS], fontsize=5.6)
            ax.tick_params(axis="both", length=2, pad=1.5, labelsize=5.8)
            ax.set_xlim(-0.5, len(MODELS) - 0.5)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            ax.text(0.02, 1.0, names[j] + (r"$^\dagger$" if tag == "published" else ""), transform=ax.transAxes,
                    fontsize=6.5, va="bottom")
            if col == 0:
                ax.set_ylabel("% favorable", fontsize=6, labelpad=1)
    axs[0, 0].set_title("Judge sees the allowed form", fontsize=6.8, style="italic", pad=9)
    axs[0, 1].set_title("Judge does not see it", fontsize=6.8, style="italic", pad=9)
    fig.legend(handles=[plt.Line2D([], [], marker=marker[v], ls="", color=color[v], label=LABEL[v], markersize=3.5)
                        for v in ALL], loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.53, 1.0),
               fontsize=5.6, handletextpad=0.1, columnspacing=0.6)
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=0.9, w_pad=0.5)
    fig.savefig(OUT / "fig-judges-sameday.pdf")
    fig.savefig(OUT / "fig-judges-sameday.png", dpi=300)
    plt.close(fig)
    print((OUT / "statement_check.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
