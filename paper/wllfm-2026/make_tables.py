#!/usr/bin/env python3
"""Compute every number in the paper's tables from the result files and write floats/*.tex.

    python3 paper/wllfm-2026/make_tables.py      (release copy: run via reproduce.py; see the README)

Sources (all under experiments/):
  results/target-disclosure-outcome-v23-luna/      three-way labels, GPT-5.6 Luna, original runs
  results/target-disclosure-outcome-v23/           three-way labels, GLM-5.3-Flash, original runs
  results/over-redaction-replay-v23/judged-*       replay of the CI rewrite redactor, deepseek-v4-flash-0731
  results/over-redaction-replay-v24/judged-glm     replay with a deepseek-v4.1-flash redactor, thinking off/on
  results/over-redaction-live-v24/judged-glm       new multi-turn runs, deepseek-v4.1-flash
v5 (camera-ready) sources, added 2026-11-15:
  results/label-reliability-consensus143/numbers.json   Table II and the IV-B statistics
  results/judge-counterfactual-v26-baseline-rerun/  same-day judge test: leaked, allowed_form, ignored (= removed)
  results/judge-counterfactual-v26/                 explicit_refusal, coarser (Fig. 2, judge_sameday)
  results/judge-counterfactual-v25/                 the v4 judge test (kept as judge_v25 / table_judges)
  results/withholding-cost-pilot-v27/scores_fixed_4var_v2/  withholding-cost diagnostic, four variants (tab-cost;
                                                    scorer v27-fixed2, paired counts from paired_4var.json)
  results/{outcome-label-sensitivity, c1-coarser-split, table-iv-label-calibration, withholding-cost-existing-runs,
           withholding-cost-necessity-subset, generalize-first-transitions}/   copied into numbers.json["calibration"]
A machine-readable copy of every number is written to floats/numbers.json.
The v4 generator is frozen as make_tables_v4.py (writes to a separate folder; see its docstring).
"""
from __future__ import annotations

import glob
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "experiments/results"
# ---- release configuration: the only place where paths are set ------------------------------------------
# ROOT (above) is the repository root. Regenerated floats go to reproduced/; the published copies stay in
# paper/wllfm-2026/floats/ and paper/wllfm-2026/figures/ (reproduce.py compares the two).
OUT = ROOT / "reproduced" / "floats"
FIG = ROOT / "reproduced" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
import os as _os
_os.chdir(ROOT)  # source_episode paths stored in the judgments are relative to the repository root
# ------------------------------------------------------------------------------------------------------------

CONDITIONS = [  # episode condition, table label, redactor, mode, instruction, privacy prompt
    ("raw_prompt", "No defense", "--", "--", "--", "no"),
    ("privacy_prompt", "Privacy prompt", "--", "--", "--", "yes"),
    ("ci_feedback_bare_v22", "Contextual guidance", "yes", "feedback", "contextual, no list", "no"),
    ("generic_feedback_v22", "Generic feedback", "yes", "feedback", "generic", "no"),
    ("ci_feedback_v22", "Contextual feedback", "yes", "feedback", "contextual", "no"),
    ("generic_gate_modify", "Generic rewrite", "yes", "rewrite", "generic", "no"),
    ("ci_gate_modify", "Contextual rewrite", "yes", "rewrite", "contextual", "no"),
    ("privacy_prompt_ci_gate_modify", "Privacy + contextual rew.", "yes", "rewrite", "contextual", "yes"),
]
LABELS = ("LEAKED", "CONVEYED", "WITHHELD")
WITHHELD_KINDS = ("refused", "deferred", "ignored", "too_coarse")  # GPT-Luna withheld_kind, Table II order
numbers: dict = {}


def load_judgments(pattern: str) -> dict[tuple[str, str], dict]:
    out = {}
    for f in glob.glob(str(pattern)):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        out[(j["case_id"], j["condition"])] = j
    return out


def pct(k: int, n: int) -> str:
    return f"{100 * k / n:.1f}"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return 100 * (c - h) / d, 100 * (c + h) / d


def mcnemar(a: dict, b: dict, cases: list[str], label: str) -> float:
    lost = sum(1 for c in cases if a[c] == label and b[c] != label)
    gained = sum(1 for c in cases if a[c] != label and b[c] == label)
    m, k = lost + gained, min(lost, gained)
    return 1.0 if m == 0 else min(1.0, 2 * sum(math.comb(m, i) for i in range(k + 1)) / 2 ** m)


def kappa(pairs: list[tuple], labels) -> float:
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pe = sum((sum(x == l for x, _ in pairs) / n) * (sum(y == l for _, y in pairs) / n) for l in labels)
    return (po - pe) / (1 - pe)


def write(name: str, tex: str) -> None:
    (OUT / name).write_text(tex, encoding="utf-8")


def fmt_p(p: float) -> str:
    return "$<$.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


# ---------------------------------------------------------------- Table I: configurations
rows = [f"{lab} & {red} & {mode} & {ins} & {pp} \\\\" for _, lab, red, mode, ins, pp in CONDITIONS]
write("tab-configurations.tex", r"""\begin{table}[!t]
\caption{Defense configurations}
\label{tab:configurations}
\centering\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lcccc@{}}
\toprule
Configuration & Redactor & Redaction & Instruction & Priv. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{\columnwidth}{\scriptsize\textit{Note.} Contextual: contextual-integrity instruction. Priv.: privacy prompt.}
\end{table}
""")

# ---------------------------------------------------------------- Table II: outcomes
luna = load_judgments(RES / "target-disclosure-outcome-v23-luna/judgments/*/*.json")
glm = load_judgments(RES / "target-disclosure-outcome-v23/judgments/*/*.json")
rows, t2 = [], {}
for cond, lab, *_ in CONDITIONS:
    keys = [k for k in luna if k[1] == cond]
    n = len(keys)
    c = Counter(luna[k]["judgment"]["outcome"] for k in keys)
    eps = {k: json.loads(Path(luna[k]["source_episode"]).read_text(encoding="utf-8")) for k in keys}
    asr = sum(eps[k]["privacy_judge_v5"]["target_attack_succeeded"] for k in keys)
    succ = [k for k in keys if not eps[k]["privacy_judge_v5"]["target_attack_succeeded"]]
    w_succ = sum(luna[k]["judgment"]["outcome"] == "WITHHELD" for k in succ)
    gk = [k for k in glm if k[1] == cond]
    gw = sum(glm[k]["judgment"]["outcome"] == "WITHHELD" for k in gk)
    lo, hi = wilson(c["WITHHELD"], n)
    kinds = Counter(luna[k]["judgment"]["withheld_kind"] for k in keys if luna[k]["judgment"]["outcome"] == "WITHHELD")
    sub = {kd: kinds[kd] for kd in WITHHELD_KINDS} | {"other_kind": sum(v for kd, v in kinds.items()
                                                                          if kd not in WITHHELD_KINDS)}
    t2[cond] = dict(n=n, leaked=c["LEAKED"], abstracted=c["CONVEYED"], withheld=c["WITHHELD"],
                    withheld_ci=[round(lo, 1), round(hi, 1)], glm_withheld=gw, glm_n=len(gk),
                    benchmark_asr=asr, benchmark_successes=len(succ), withheld_among_successes=w_succ,
                    withheld_kind=sub)
    rows.append(f"{lab} & {pct(c['LEAKED'], n)} & {pct(c['CONVEYED'], n)} & {pct(c['WITHHELD'], n)} & "
                f"{pct(gw, len(gk))} & "
                + " & ".join(pct(sub[kd], c["WITHHELD"]) for kd in WITHHELD_KINDS) + f" & {c['WITHHELD']} & "
                f"{pct(asr, n)} & {w_succ}/{len(succ)}" + r" \\")
numbers["table_outcomes"] = t2
# the subtype counts must match the withholding-cost analysis of the existing runs
_wk = json.loads((RES / "withholding-cost-existing-runs/numbers.json").read_text(encoding="utf-8"))
for cond, d in t2.items():
    ref = _wk["withheld_kind_counts"]["Luna"][cond]
    assert all(d["withheld_kind"][kd] == ref[kd] for kd in WITHHELD_KINDS + ("other_kind",)) \
        and d["withheld"] == ref["withheld"], (cond, d["withheld_kind"], ref)
numbers["withheld_kind_counts"] = {
    "source": "GPT-5.6 Luna withheld_kind (target-disclosure-outcome-v23-luna); equals "
              "results/withholding-cost-existing-runs/numbers.json withheld_kind_counts.Luna",
    "by_configuration": {cond: d["withheld_kind"] | {"withheld": d["withheld"], "n": d["n"]} for cond, d in t2.items()},
    "total": {kd: sum(d["withheld_kind"][kd] for d in t2.values()) for kd in WITHHELD_KINDS + ("other_kind",)}
             | {"withheld": sum(d["withheld"] for d in t2.values())}}
# With the four withheld-kind columns the table is 42pt wider than one IEEE column at \footnotesize (6pt at
# \scriptsize), so v5 sets it across both columns (table*); v4 was a one-column table without these columns.
write("tab-outcomes.tex", r"""\begin{table*}[!t]
\caption{Outcomes by defense configuration}
\label{tab:outcomes}
\centering\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lccccrrrrrcc@{}}
\toprule
\multirow{2}{*}{Configuration} & \multicolumn{3}{c}{GPT-Luna (\%)} & GLM (\%) & \multicolumn{4}{c}{GPT-Luna withheld (\%)} & \multirow{2}{*}{Total} & \multicolumn{2}{c}{Benchmark's judge} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-9}\cmidrule(l){11-12}
 & Leak. & Abstr. & Withh. & Withh. & Ref. & Def. & Ign. & Crs. & & $\mathrm{ASR}_{\mathrm{B}}$ (\%) & Withh./succ. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{0.8\textwidth}{\raggedright\scriptsize\textit{Note.} Leak./Abstr./Withh. and $\mathrm{ASR}_{\mathrm{B}}$: percent of 182 cases. $\mathrm{ASR}_{\mathrm{B}}$: attack success rate from the benchmark's judge. Ref./Def./Ign./Crs.: refused, deferred, ignored, too coarse, as percent of withheld cases; Total: number of withheld cases. Withh./succ.: among cases the benchmark's judge does not count as attack successes, those GPT-Luna labels withheld. GLM n is 182 except for privacy prompt, generic feedback, contextual rewrite, and privacy + contextual rew. (181) and generic rewrite (180).}
\end{table*}
""")

# ---------------------------------------------------------------- benchmark measures (text numbers)
gated = [c for c, *_ in CONDITIONS if c in ("generic_feedback_v22", "ci_feedback_v22", "generic_gate_modify",
                                            "ci_gate_modify", "privacy_prompt_ci_gate_modify")]
grp = {"WITHHELD": [], "CONVEYED": []}
for k, j in luna.items():
    o = j["judgment"]["outcome"]
    if k[1] in gated and o in grp:
        e = json.loads(Path(j["source_episode"]).read_text(encoding="utf-8"))
        grp[o].append(e["privacy_judge_v5"]["target"]["parsed"]["appropriateness_score"])
numbers["judge_scores"] = {o: dict(n=len(v), mean=round(sum(v) / len(v), 2),
                                   share_10=round(100 * sum(x == 10 for x in v) / len(v), 1)) for o, v in grp.items()}

# ---------------------------------------------------------------- Table III: human validation (v5: 143-item consensus)
LREL = RES / "label-reliability-consensus143/numbers.json"
# Table II and numbers["labels"]["recomputed"] are read from the aggregate output
# experiments/results/label-reliability-consensus143/numbers.json.
print("note: Table II (tab-human) is read from", LREL.relative_to(ROOT))
lrel = json.loads(LREL.read_text(encoding="utf-8"))
TAB_CONSENSUS = "143"
_aa, _q2 = lrel["annotator_annotator"], lrel["q2"]
t3 = {"human_human": {"three_way": round(_aa["three_way"], 2), "withheld": round(_aa["withheld"], 2),
                      "leaked": round(_aa["leaked"], 2), "q2_needed": round(_q2["kappa"], 2), "n": _aa["n"],
                      "consensus_n": lrel[f"consensus_{TAB_CONSENSUS}"]["n"]}, "consensus": TAB_CONSENSUS}
judges = {"GPT-Luna": None, "GLM": None, "Benchmark's judge": None}
_F = ("n", "three_way", "withheld", "precision", "recall", "tp", "judge_withheld", "consensus_withheld",
      "confusion_consensus_rows_judge_cols")
by_consensus, tab_rows = {}, {}
for cname in ("121", "143"):
    _src = lrel[f"consensus_{cname}"]
    rows = [f"Annotator 1 vs.\\ annotator 2 & {_aa['n']} & {t3['human_human']['three_way']:.2f} & "
            f"{t3['human_human']['withheld']:.2f} & -- & -- \\\\", r"\midrule"]
    blk = {"n": _src["n"], "label_counts": {l: _src["label_counts"][l] for l in LABELS}}
    for name in judges:
        _r = _src[name]
        blk[name] = {m: _r[m] for m in _F} | {"weighted": {m: _r["weighted"][m] for m in
                                                            ("three_way", "withheld", "precision", "recall")}}
        rows.append(f"{name} vs.\\ consensus & {_r['n']} & {_r['three_way']:.2f} & "
                    f"{_r['withheld']:.2f} & {_r['precision']:.2f} & {_r['recall']:.2f} \\\\")
    by_consensus[cname], tab_rows[cname] = blk, rows
for name in judges:
    t3[name] = {m: round(by_consensus[TAB_CONSENSUS][name][m], 2) if m != "n" else by_consensus[TAB_CONSENSUS][name][m]
                for m in ("n", "three_way", "withheld", "precision", "recall")}
t3["q2_consensus"] = dict(n=_q2["agreed"], needed=_q2["needed"])
numbers["table_human"] = t3
numbers["labels"] = {
    "note": "Sec. IV-B. 'consensus_121' / 'consensus_143' point estimates and weighted point estimates are recomputed "
            "by make_tables.py and checked against the 'source' file; bootstrap CIs (unweighted: 2000 reps, "
            "random.Random(23); weighted: within-cell bootstrap, 2000 reps, seed 20261115), judge-judge agreement, "
            "Q2, benchmark-judge levels and the ASR_B disagreement items are copied from that file.",
    "source": str(LREL.relative_to(ROOT)), "printed_in_tab_human": TAB_CONSENSUS,
    "recomputed": by_consensus} | {k: v for k, v in lrel.items() if k != "tab_human_121_identical_to_paper_float"}
_note143 = (" Consensus: label shared by both annotators, or by two of three annotators after a third annotator "
            "labeled the 28 disagreements (6 three-way splits left out).")
write("tab-human.tex", r"""\begin{table}[!t]
\caption{Agreement with human annotation}
\label{tab:human}
\centering\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}
\toprule
 & & \multicolumn{2}{c}{$\kappa$} & \multicolumn{2}{c}{Withheld} \\
\cmidrule(lr){3-4}\cmidrule(l){5-6}
Comparison & $n$ & 3-way & Withh. & Prec. & Rec. \\
\midrule
""" + "\n".join(tab_rows[TAB_CONSENSUS]) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{\columnwidth}{\scriptsize\textit{Note.} Cohen's $\kappa$. Prec./Rec.: withheld label against the consensus.""" + (_note143 if TAB_CONSENSUS == "143" else "") + r"""}
\end{table}
""")

# ---------------------------------------------------------------- Table IV: instruction and thinking
def outcomes(pattern: str, cond: str | None = None) -> dict[str, str]:
    out = {}
    for f in glob.glob(str(pattern)):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        if cond is None or j["condition"] == cond:
            out[j["case_id"]] = j["judgment"]["outcome"]
    return out


blocks = []
t4 = {}
r23 = RES / "over-redaction-replay-v23/judged-luna-nothink/judgments/*/*.json"
src = {k[0]: v["judgment"]["outcome"] for k, v in luna.items() if k[1] == "ci_gate_modify"}
arms = [("Original runs", src),
        ("Original instruction", outcomes(r23, "R-orig-nothink")),
        ("Generalize first", outcomes(r23, "R-abs-nothink"))]
blocks.append(("Replay, DeepSeek V4 redactor, GPT-Luna judge", arms, 1))
r24 = RES / "over-redaction-replay-v24/judged-glm/judgments/*/*.json"
blocks.append(("Replay, DeepSeek V4.1 redactor, GLM judge", [
    ("Original instruction", outcomes(r24, "R-orig-nothink")),
    ("Generalize first", outcomes(r24, "R-abs-nothink")),
    ("Original, thinking on", outcomes(r24, "R-orig-think")),
    ("Generalize first, thinking on", outcomes(r24, "R-abs-think"))], 0))
lv = RES / "over-redaction-live-v24/judged-glm"
blocks.append(("Multi-turn, DeepSeek V4.1 redactor, GLM judge", [
    ("Original instruction", outcomes(lv / "orig/judgments/*/*.json")),
    ("Generalize first", outcomes(lv / "absfirst/judgments/*/*.json"))], 0))
rows = []
for title, arm_list, ref in blocks:
    cases = sorted(set.intersection(*[set(a) for _, a in arm_list]))
    n = len(cases)
    rows.append(f"\\multicolumn{{4}}{{@{{}}l}}{{\\emph{{{title}}} ($n={n}$)}} \\\\")
    t4[title] = {}
    for name, arm in arm_list:
        c = Counter(arm[x] for x in cases)
        t4[title][name] = {l: c[l] for l in LABELS} | {"n": n}
        rows.append(f"\\quad {name} & {pct(c['LEAKED'], n)} & {pct(c['CONVEYED'], n)} & {pct(c['WITHHELD'], n)} \\\\")
    # paired tests: generalize-first vs original instruction (same thinking setting)
    pairs = [(arm_list[ref][1], arm_list[ref + 1][1], "instruction")]
    if len(arm_list) == 4:
        pairs.append((arm_list[2][1], arm_list[3][1], "instruction, thinking on"))
        pairs.append((arm_list[0][1], arm_list[2][1], "thinking, original"))
        pairs.append((arm_list[1][1], arm_list[3][1], "thinking, generalize first"))
    t4[title]["mcnemar"] = {lab: {l: round(mcnemar(a, b, cases, l), 4) for l in LABELS} for a, b, lab in pairs}
    rows.append(r"\addlinespace")
numbers["table_instruction"] = t4
write("tab-instruction.tex", r"""\begin{table}[!t]
\caption{Effect of the generalize-first instruction and the thinking mode}
\label{tab:instruction}
\centering\footnotesize
\begin{tabular}{@{}lccc@{}}
\toprule
 & Leaked & Abstracted & Withheld \\
\midrule
""" + "\n".join(rows[:-1]) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{\columnwidth}{\scriptsize\textit{Note.} Percent. Arms in a block share the same cases.}
\end{table}
""")

# ---------------------------------------------------------------- Table V: direct identifiers
DIRECT_IDENTIFIERS = {"full_name", "first_name", "exact_age", "age", "age_range",
                      "exact_address", "location", "government_id_information"}


def item_name(case_id: str) -> str:
    return ".".join(case_id.split(".")[3:-1])


def fisher(a: int, b: int, c: int, d: int) -> float:
    n, r1, c1 = a + b + c + d, a + b, a + c
    p = lambda x: math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if p(x) <= p0 * (1 + 1e-9)))


t5, rows = {}, []
for cond, lab in [("raw_prompt", "No defense"), ("ci_gate_modify", "Contextual rewrite"),
                  ("privacy_prompt_ci_gate_modify", "Privacy + contextual rew.")]:
    t5[cond] = {}
    for grp, member in [("direct identifiers", True), ("other items", False)]:
        ks = [k for k in luna if k[1] == cond and (item_name(k[0]) in DIRECT_IDENTIFIERS) == member]
        gk = [k for k in glm if k[1] == cond and (item_name(k[0]) in DIRECT_IDENTIFIERS) == member]
        c = Counter(luna[k]["judgment"]["outcome"] for k in ks)
        gw = sum(glm[k]["judgment"]["outcome"] == "WITHHELD" for k in gk)
        t5[cond][grp] = {l: c[l] for l in LABELS} | {"n": len(ks), "glm_withheld": gw, "glm_n": len(gk)}
    di, ot = t5[cond]["direct identifiers"], t5[cond]["other items"]
    t5[cond]["fisher_p_withheld"] = fisher(di["WITHHELD"], di["n"] - di["WITHHELD"], ot["WITHHELD"], ot["n"] - ot["WITHHELD"])
    t5[cond]["fisher_p_withheld_glm"] = fisher(di["glm_withheld"], di["glm_n"] - di["glm_withheld"],
                                               ot["glm_withheld"], ot["glm_n"] - ot["glm_withheld"])
    rows.append(f"\\multicolumn{{5}}{{@{{}}l}}{{\\emph{{{lab}}}}} \\\\")
    for grp, d in [("Identifiers", di), ("Other items", ot)]:
        rows.append(f"\\quad {grp} ($n={d['n']}$) & {pct(d['LEAKED'], d['n'])} & {pct(d['CONVEYED'], d['n'])} & "
                    f"{pct(d['WITHHELD'], d['n'])} & {pct(d['glm_withheld'], d['glm_n'])} \\\\")
numbers["table_identifiers"] = t5
write("tab-identifiers.tex", r"""\begin{table}[!t]
\caption{Outcomes for identifiers and other items}
\label{tab:identifiers}
\centering\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lcccc@{}}
\toprule
 & \multicolumn{3}{c}{GPT-Luna} & GLM \\
\cmidrule(lr){2-4}
 & Leak. & Abstr. & Withh. & Withh. \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{\columnwidth}{\scriptsize\textit{Note.} Percent. Identifiers: identifiers and quasi-identifiers (name, age, address, location, government ID). Other items: all remaining related-and-useful items. GLM n for other items is 151 under contextual rewrite and privacy + contextual rew.}
\end{table}
""")

item_stats = {}
for (case_id, cond), j in luna.items():
    if cond == "privacy_prompt_ci_gate_modify":
        item_stats.setdefault(item_name(case_id), Counter())[j["judgment"]["outcome"]] += 1
numbers["item_extremes_strongest"] = {
    it: {l: c[l] for l in LABELS} | {"n": sum(c.values())} for it, c in item_stats.items() if sum(c.values()) >= 3}

# ---------------------------------------------------------------- Table VI: benchmark judges on edited messages
from scipy.stats import wilcoxon, binomtest

CF = RES / "judge-counterfactual-v25"
CF_ITEMS = [json.loads(l)["case_id"] for l in
            (ROOT / "experiments/datasets/judge-counterfactual-v25/items_v3.jsonl").read_text(encoding="utf-8").splitlines()]
CF_MODELS = [("deepseek-v4.1-flash", "DeepSeek"), ("gpt-oss:120b", "gpt-oss"), ("glm-5.3-flash", "GLM"), ("luna", "GPT-Luna")]
CF_VERSIONS = [("leaked", "Leaked"), ("allowed_form", "Allowed form"), ("ignored", "Removed")]
# (judge, condition as published, condition with the allowed form added or removed)
CF_JUDGES = [("converse", "told", "untold"), ("privacyalign", "untold", "told"), ("privacylens_leak", "untold", "told")]


def cf_get(model, judge, cond, case, version):
    f = CF / model / judge / cond / case / f"{version}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    return r.get("parsed") if r.get("status") == "ok" else None


def cf_cell(model, judge, cond):
    """Per version: ConVerse mean score; PrivacyAlign (leak %, omit %); PrivacyLens leak %.
    Missing calls are left out of that version's rate; paired tests use cases with both versions.
    Returns None if more than 2% of the calls for this cell are missing (run not finished)."""
    vals = {v: [cf_get(model, judge, cond, c, v) for c in CF_ITEMS] for v, _ in CF_VERSIONS}
    n_missing = sum(p is None for ps in vals.values() for p in ps)
    if n_missing > 0.02 * 3 * len(CF_ITEMS):
        return None
    out = {"missing": n_missing}
    for v, ps in vals.items():
        ps = [p for p in ps if p is not None]
        if judge == "converse":
            out[v] = {"n": len(ps), "mean": sum(float(p["appropriateness_score"]) for p in ps) / len(ps),
                      "appropriate": 100 * sum(p["abstraction_level"] == "appropriate" for p in ps) / len(ps),
                      "too_vague": 100 * sum(p["abstraction_level"] == "too_vague" for p in ps) / len(ps),
                      "score_ge7": 100 * sum(float(p["appropriateness_score"]) >= 7 for p in ps) / len(ps)}
        elif judge == "privacyalign":
            out[v] = {"n": len(ps), "leak": 100 * sum(bool(p["leaks"]) for p in ps) / len(ps),
                      "omit": 100 * sum(bool(p["omits"]) for p in ps) / len(ps)}
        else:
            out[v] = {"n": len(ps), "leak": 100 * sum(bool(p["leaks_upstream_parser"]) for p in ps) / len(ps)}
    pairs = [(x, y) for x, y in zip(vals["allowed_form"], vals["ignored"]) if x is not None and y is not None]
    out["n_pairs"] = len(pairs)
    if judge == "converse":
        d = [float(y["appropriateness_score"]) - float(x["appropriateness_score"]) for x, y in pairs]
        nz = [x for x in d if x != 0]
        out["removed_minus_allowed"] = sum(d) / len(d)
        out["share_removed_ge_allowed"] = 100 * sum(x >= 0 for x in d) / len(d)
        out["wilcoxon_p"] = float(wilcoxon(nz).pvalue) if len(nz) > 5 else 1.0
        ok = lambda p: p["abstraction_level"] == "appropriate"
        only_a = sum(ok(x) and not ok(y) for x, y in pairs)
        only_r = sum(ok(y) and not ok(x) for x, y in pairs)
        out["appr_allowed_only"], out["appr_removed_only"] = only_a, only_r
        out["appr_mcnemar_p"] = float(binomtest(only_a, only_a + only_r).pvalue) if only_a + only_r else 1.0
    else:
        key = "leaks" if judge == "privacyalign" else "leaks_upstream_parser"
        only_a = sum(bool(x[key]) and not bool(y[key]) for x, y in pairs)
        only_r = sum(bool(y[key]) and not bool(x[key]) for x, y in pairs)
        out["leak_allowed_only"], out["leak_removed_only"] = only_a, only_r
        out["leak_mcnemar_p"] = float(binomtest(only_a, only_a + only_r).pvalue) if only_a + only_r else 1.0
        if judge == "privacyalign":
            oa = sum(bool(y["omits"]) and not bool(x["omits"]) for x, y in pairs)
            ob = sum(bool(x["omits"]) and not bool(y["omits"]) for x, y in pairs)
            out["omit_mcnemar_p"] = float(binomtest(oa, oa + ob).pvalue) if oa + ob else 1.0
    return out


t6 = {"n": len(CF_ITEMS)}
for m, _ in CF_MODELS:
    for j, pub, mod in CF_JUDGES:
        for cond, tag in ((pub, "published"), (mod, "modified")):
            t6[f"{m}/{j}/{tag}"] = cf_cell(m, j, cond)
numbers["table_judges"] = t6


# ---------------------------------------------------------------- Holm correction and paired CIs
import random as _random


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def boot(diffs, n=5000, seed=25):
    rng = _random.Random(seed)
    ms = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(n))
    return [round(ms[int(0.025 * n)], 3), round(ms[int(0.975 * n)], 3)]


# family 1: paired allowed-form vs removed tests in the judge experiment (every model, judge, condition)
fam1 = {}
for m, _ in CF_MODELS:
    for j, _, _ in CF_JUDGES:
        for tag in ("published", "modified"):
            cell = t6.get(f"{m}/{j}/{tag}")
            if not cell:
                continue
            if j == "converse":
                fam1[f"{m}/{j}/{tag}/appropriate"] = cell["appr_mcnemar_p"]
            else:
                fam1[f"{m}/{j}/{tag}/leak"] = cell["leak_mcnemar_p"]
            if j == "privacyalign":
                fam1[f"{m}/{j}/{tag}/omit"] = cell["omit_mcnemar_p"]
# paired CIs (allowed form vs removed) for the judge experiment
cis = {}
for m, _ in CF_MODELS:
    for j, pub, mod in CF_JUDGES:
        for cond, tag in ((pub, "published"), (mod, "modified")):
            if not t6.get(f"{m}/{j}/{tag}"):
                continue
            ar = [(cf_get(m, j, cond, c, "allowed_form"), cf_get(m, j, cond, c, "ignored")) for c in CF_ITEMS]
            ar = [(x, y) for x, y in ar if x is not None and y is not None]
            a, r = [x for x, _ in ar], [y for _, y in ar]
            if j == "converse":
                d = [float(y["appropriateness_score"]) - float(x["appropriateness_score"]) for x, y in zip(a, r)]
                cis[f"{m}/{j}/{tag}/score_removed_minus_allowed"] = boot(d)
                ok = lambda p: p["abstraction_level"] == "appropriate"
                d = [100 * (int(ok(x)) - int(ok(y))) for x, y in zip(a, r)]
                cis[f"{m}/{j}/{tag}/appr_pp_allowed_minus_removed"] = boot(d)
            else:
                key = "leaks" if j == "privacyalign" else "leaks_upstream_parser"
                d = [100 * (int(bool(x[key])) - int(bool(y[key]))) for x, y in zip(a, r)]
                cis[f"{m}/{j}/{tag}/leak_pp_allowed_minus_removed"] = boot(d)
                if j == "privacyalign":
                    d = [100 * (int(bool(y["omits"])) - int(bool(x["omits"]))) for x, y in zip(a, r)]
                    cis[f"{m}/{j}/{tag}/omit_pp_removed_minus_allowed"] = boot(d)
# family 2: tests in the generalize-first / thinking experiments
fam2 = {}
for title, block in numbers["table_instruction"].items():
    for lab, ps in block["mcnemar"].items():
        for outcome, pv in ps.items():
            fam2[f"{title}/{lab}/{outcome}"] = pv
numbers["holm"] = {"judge_tests": {"n": len(fam1), "raw": fam1, "adjusted": holm(fam1)},
                   "instruction_tests": {"n": len(fam2), "raw": fam2, "adjusted": holm(fam2)}}
numbers["judge_paired_ci"] = cis

# ---------------------------------------------------------------- Fig. 2: judge test, same-day data, five versions
# Same computation as experiments/scripts/analyze_judge_counterfactual_sameday.py (which copies this file's v4 rules):
#   favorable: ConVerse abstraction_level == appropriate; PrivacyAlign not leaks; PrivacyLens not leaks_upstream_parser
#   a cell (model x judge x condition) is left out if more than 2% of its 3 x 86 calls (leaked/allowed/removed) are missing
#   removed vs allowed: exact McNemar, paired bootstrap 95% CI (5,000 resamples, seed 25), Holm over 32 tests (J25)
#   allowed vs leaked: same tests, own 32-test Holm family (J25-leaked; rates only are reported in the paper)
#   explicit_refusal / coarser vs allowed and vs removed on their own case lists: one 128-test Holm family (J26,
#   analyze_judge_counterfactual_v26.py; a new-version cell with more than 2% missing calls is left out)
JT_RERUN = RES / "judge-counterfactual-v26-baseline-rerun"
JT_V26 = RES / "judge-counterfactual-v26"
JT_OLD = ("leaked", "allowed_form", "ignored")
JT_NEW = ("explicit_refusal", "coarser")
JT_ALL = JT_OLD + JT_NEW
JT_LABEL = {"leaked": "Raw value", "allowed_form": "Allowed form", "ignored": "Removed",
            "explicit_refusal": "Refusal", "coarser": "Coarser"}
JT_NEW_ITEMS = {v: [json.loads(l)["case_id"] for l in
                    (ROOT / f"experiments/datasets/judge-counterfactual-v26/items_v26_{v}.jsonl").read_text(
                        encoding="utf-8").splitlines() if l.strip()] for v in JT_NEW}
JT_SOURCES = {"sameday": {v: JT_RERUN for v in JT_OLD} | {v: JT_V26 for v in JT_NEW},
              "v25": {v: CF for v in JT_OLD} | {v: JT_V26 for v in JT_NEW}}


def jt_get(src, model, judge, cond, case, version):
    f = JT_SOURCES[src][version] / model / judge / cond / case / f"{version}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    return r.get("parsed") if r.get("status") == "ok" else None


def jt_fav(judge, p):
    if judge == "converse":
        return p["abstraction_level"] == "appropriate"
    if judge == "privacyalign":
        return not bool(p["leaks"])
    return not bool(p["leaks_upstream_parser"])


def jt_mcn(pairs, fn_a, fn_b):
    """exact McNemar on (a, b) pairs; returns (only_a, only_b, p)"""
    oa = sum(fn_a(x) and not fn_b(y) for x, y in pairs)
    ob = sum(fn_b(y) and not fn_a(x) for x, y in pairs)
    return oa, ob, float(binomtest(oa, oa + ob).pvalue) if oa + ob else 1.0


def jt_rates(judge, ps):
    ps = [p for p in ps if p is not None]
    if not ps:
        return {"n": 0}
    out = {"n": len(ps), "favorable": 100 * sum(jt_fav(judge, p) for p in ps) / len(ps)}
    if judge == "converse":
        out["mean"] = sum(float(p["appropriateness_score"]) for p in ps) / len(ps)
        out["too_vague"] = 100 * sum(p["abstraction_level"] == "too_vague" for p in ps) / len(ps)
    if judge == "privacyalign":
        out["omit"] = 100 * sum(bool(p["omits"]) for p in ps) / len(ps)
    return out


def jt_analyze(src):
    cells, fam, famL, fam26, missing = {}, {}, {}, {}, {}
    for m, _ in CF_MODELS:
        for j, pub, mod in CF_JUDGES:
            for cond, tag in ((pub, "published"), (mod, "modified")):
                key_ = f"{m}/{j}/{tag}"
                vals = {v: [jt_get(src, m, j, cond, c, v) for c in CF_ITEMS] for v in JT_OLD}
                for v in JT_NEW:
                    vals[v] = [jt_get(src, m, j, cond, c, v) for c in JT_NEW_ITEMS[v]]
                for v in JT_ALL:
                    cases = CF_ITEMS if v in JT_OLD else JT_NEW_ITEMS[v]
                    miss = [c for c, p in zip(cases, vals[v]) if p is None]
                    if miss:
                        missing[f"{key_}/{v}"] = {"expected": len(cases), "ok": len(cases) - len(miss), "cases": miss}
                n_missing = sum(p is None for v in JT_OLD for p in vals[v])
                cell = {"cond": cond, "missing_3versions": n_missing, "rates": {v: jt_rates(j, vals[v]) for v in JT_ALL}}
                cells[key_] = cell
                if n_missing > 0.02 * 3 * len(CF_ITEMS):
                    cell["excluded"] = "more than 2% of the 3x86 calls missing"
                    continue
                fa = lambda q, j=j: jt_fav(j, q)
                om = lambda q: bool(q["omits"])
                # removed vs allowed (J25)
                pairs = [(x, y) for x, y in zip(vals["allowed_form"], vals["ignored"]) if x is not None and y is not None]
                ra = {"n_pairs": len(pairs)}
                if j == "converse":
                    a, r, p = jt_mcn(pairs, fa, fa)
                    d = [100 * (int(fa(x)) - int(fa(y))) for x, y in pairs]
                    ra |= {"appr_allowed_only": a, "appr_removed_only": r, "p": p,
                           "appr_pp_allowed_minus_removed": sum(d) / len(d), "ci": boot(d)}
                    d = [float(y["appropriateness_score"]) - float(x["appropriateness_score"]) for x, y in pairs]
                    nz = [x for x in d if x != 0]
                    ra |= {"score_removed_minus_allowed": sum(d) / len(d), "score_ci": boot(d),
                           "score_wilcoxon_p": float(wilcoxon(nz).pvalue) if len(nz) > 5 else 1.0}
                    fam[f"{key_}/appropriate"] = p
                else:
                    k = "leaks" if j == "privacyalign" else "leaks_upstream_parser"
                    lk = lambda q, k=k: bool(q[k])
                    a, r, p = jt_mcn(pairs, lk, lk)
                    d = [100 * (int(lk(x)) - int(lk(y))) for x, y in pairs]
                    ra |= {"leak_allowed_only": a, "leak_removed_only": r, "p": p,
                           "fav_pp_removed_minus_allowed": sum(d) / len(d), "ci": boot(d)}
                    fam[f"{key_}/leak"] = p
                    if j == "privacyalign":
                        ob, oa, po = jt_mcn(pairs, om, om)
                        d = [100 * (int(om(y)) - int(om(x))) for x, y in pairs]
                        ra |= {"omit_removed_only": oa, "omit_allowed_only": ob, "omit_p": po,
                               "omit_pp_removed_minus_allowed": sum(d) / len(d), "omit_ci": boot(d)}
                        fam[f"{key_}/omit"] = po
                cell["removed_vs_allowed"] = ra
                # allowed vs leaked (J25-leaked)
                pairs = [(x, y) for x, y in zip(vals["allowed_form"], vals["leaked"]) if x is not None and y is not None]
                a, l, p = jt_mcn(pairs, fa, fa)
                d = [100 * (int(fa(x)) - int(fa(y))) for x, y in pairs]
                al = {"n_pairs": len(pairs), "allowed_only": a, "leaked_only": l, "p": p,
                      "fav_pp_allowed_minus_leaked": sum(d) / len(d), "ci": boot(d)}
                famL[f"{key_}/favorable"] = p
                if j == "privacyalign":
                    a2, l2, p2 = jt_mcn(pairs, om, om)
                    d = [100 * (int(om(x)) - int(om(y))) for x, y in pairs]
                    al |= {"omit_allowed_only": a2, "omit_leaked_only": l2, "omit_p": p2,
                           "omit_pp_allowed_minus_leaked": sum(d) / len(d), "omit_ci": boot(d)}
                    famL[f"{key_}/omit"] = p2
                cell["allowed_vs_leaked"] = al
                # refusal / coarser vs allowed and vs removed (J26)
                cell["j26"] = {}
                for new in JT_NEW:
                    cases, nv = JT_NEW_ITEMS[new], vals[new]
                    if sum(p is None for p in nv) > 0.02 * len(cases):
                        cell["j26"][new] = {"excluded": "more than 2% of new-version calls missing"}
                        continue
                    ref_by_case = {v: dict(zip(CF_ITEMS, vals[v])) for v in ("allowed_form", "ignored")}
                    res = {}
                    for ref in ("allowed_form", "ignored"):
                        pairs = [(x, ref_by_case[ref][c]) for c, x in zip(cases, nv)
                                 if x is not None and ref_by_case[ref].get(c) is not None]
                        comp = {"n_pairs": len(pairs)}
                        for mn, fn in ({"favorable": fa} | ({"omit": om} if j == "privacyalign" else {})).items():
                            a, b, p = jt_mcn(pairs, fn, fn)
                            d = [100 * (int(fn(x)) - int(fn(y))) for x, y in pairs]
                            comp[mn] = {"new_pct": 100 * sum(fn(x) for x, _ in pairs) / len(pairs),
                                        "ref_pct": 100 * sum(fn(y) for _, y in pairs) / len(pairs),
                                        "diff_pp_new_minus_ref": sum(d) / len(d), "ci": boot(d),
                                        "only_new": a, "only_ref": b, "p": p}
                            fam26[f"{key_}/{new}/vs_{ref}/{mn}"] = p
                        res[f"vs_{ref}"] = comp
                    cell["j26"][new] = res
    adj, adjL, adj26 = holm(fam), holm(famL), holm(fam26)
    for key_, cell in cells.items():
        if "excluded" in cell:
            continue
        ra = cell["removed_vs_allowed"]
        ra["holm_p"] = adj[f"{key_}/{'appropriate' if key_.split('/')[1] == 'converse' else 'leak'}"]
        if "omit_p" in ra:
            ra["omit_holm_p"] = adj[f"{key_}/omit"]
        al = cell["allowed_vs_leaked"]
        al["holm_p"] = adjL[f"{key_}/favorable"]
        if "omit_p" in al:
            al["omit_holm_p"] = adjL[f"{key_}/omit"]
        for new, res in cell["j26"].items():
            for ref, comp in res.items():
                if ref.startswith("vs_"):
                    for mn in ("favorable", "omit"):
                        if mn in comp:
                            comp[mn]["holm_p"] = adj26[f"{key_}/{new}/{ref}/{mn}"]
    return {"sources": {v: str(p.relative_to(ROOT)) for v, p in JT_SOURCES[src].items()},
            "n_items": {v: len(CF_ITEMS) for v in JT_OLD} | {v: len(JT_NEW_ITEMS[v]) for v in JT_NEW},
            "version_labels": JT_LABEL,
            "family_sizes": {"J25 removed vs allowed": len(fam), "J25-leaked allowed vs leaked": len(famL),
                             "J26 refusal/coarser vs allowed/removed": len(fam26)},
            "missing_calls": missing, "cells": cells}


numbers["judge_sameday"] = judge_sd = jt_analyze("sameday")
numbers["judge_v25"] = jt_analyze("v25")
for _a in (numbers["judge_sameday"], numbers["judge_v25"]):
    assert _a["family_sizes"] == {"J25 removed vs allowed": 32, "J25-leaked allowed vs leaked": 32,
                                  "J26 refusal/coarser vs allowed/removed": 128}, _a["family_sizes"]
    _a["readme"] = ("cells['<model>/<judge>/<published|modified>']: published = the judge's released prompt "
                    "(ConVerse told, PrivacyAlign/PrivacyLens untold). rates[version]: n, favorable %, ConVerse mean "
                    "score and too_vague %, PrivacyAlign omit %. removed_vs_allowed: J25 (32-test Holm). "
                    "allowed_vs_leaked: J25-leaked (32-test Holm). j26[new][vs_allowed_form|vs_ignored]: 128-test Holm. "
                    "ignored = removed; leaked = raw value.")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman"],
                     "mathtext.fontset": "stix", "font.size": 7, "axes.linewidth": 0.5,
                     "xtick.major.width": 0.5, "ytick.major.width": 0.5, "pdf.fonttype": 42})
cf_color = {"leaked": "#9a9a9a", "allowed_form": "#1f5fa8", "ignored": "#d1641c",
            "explicit_refusal": "#7b3fa0", "coarser": "#2a8a4a"}
cf_marker = {"leaked": "x", "allowed_form": "o", "ignored": "s", "explicit_refusal": "^", "coarser": "D"}
cf_offset = {"leaked": 0.0, "allowed_form": 0.0, "ignored": 0.0, "explicit_refusal": 0.18, "coarser": -0.18}
cf_names = {"converse": "ConVerse", "privacyalign": "PrivacyAlign", "privacylens_leak": "PrivacyLens"}


def draw_judges(path_pdf, path_png=None):
    fig, axs = plt.subplots(3, 2, figsize=(3.45, 3.9), sharey=True, sharex=True)
    for col, sees in enumerate((True, False)):
        for row, (j, pub, mod) in enumerate(CF_JUDGES):
            ax = axs[row, col]
            tag = "published" if (pub == "told") == sees else "modified"
            for i, (m, _) in enumerate(CF_MODELS):
                r = judge_sd["cells"][f"{m}/{j}/{tag}"]["rates"]
                ax.plot([i, i], [r["allowed_form"]["favorable"], r["ignored"]["favorable"]], color="#c8c8c8",
                        lw=1.0, zorder=1)
                for v in JT_ALL:
                    if r[v].get("n"):
                        ax.scatter(i + cf_offset[v], r[v]["favorable"], marker=cf_marker[v],
                                   s=9 if v != "leaked" else 8, color=cf_color[v], zorder=3, linewidths=0.7)
            ax.set_ylim(-5, 105); ax.set_yticks([0, 50, 100]); ax.grid(axis="y", lw=0.3, color="#e0e0e0")
            ax.set_xticks(range(len(CF_MODELS))); ax.set_xticklabels([lab for _, lab in CF_MODELS], fontsize=5.6)
            ax.tick_params(axis="both", length=2, pad=1.5, labelsize=5.8)
            ax.set_xlim(-0.5, len(CF_MODELS) - 0.5)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            ax.text(0.02, 1.0, cf_names[j] + (r"$^\dagger$" if tag == "published" else ""),
                    transform=ax.transAxes, fontsize=6.5, va="bottom")
            if col == 0:
                ax.set_ylabel("% favorable", fontsize=6, labelpad=1)
    axs[0, 0].set_title("Judge sees the allowed form", fontsize=6.8, style="italic", pad=9)
    axs[0, 1].set_title("Judge does not see it", fontsize=6.8, style="italic", pad=9)
    fig.legend(handles=[plt.Line2D([], [], marker=cf_marker[v], ls="", color=cf_color[v], label=JT_LABEL[v],
                                   markersize=3.5) for v in JT_ALL],
               loc="upper center", ncol=5, frameon=False, bbox_to_anchor=(0.53, 1.0), fontsize=6.2,
               handletextpad=0.1, columnspacing=0.8)
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=0.9, w_pad=0.5)
    fig.savefig(path_pdf, metadata={"CreationDate": None})  # no timestamp: identical bytes on every run
    if path_png:
        fig.savefig(path_png, dpi=300)
    plt.close(fig)


FIG.mkdir(parents=True, exist_ok=True)
draw_judges(FIG / "fig-judges.pdf")
_miss = judge_sd["missing_calls"]
_n_new = ", ".join(f"{JT_LABEL[v].lower()}: {len(JT_NEW_ITEMS[v])}" for v in JT_NEW
                   if len(JT_NEW_ITEMS[v]) != len(CF_ITEMS))
write("fig-judges.tex", r"""\begin{figure}[!t]
\centering
\includegraphics[width=\columnwidth]{figures/fig-judges.pdf}
\caption{Benchmark judges on five versions of the same message. Favorable: labeled appropriate (ConVerse) or not flagged as leaking (PrivacyAlign, PrivacyLens); the measures differ across judges and are compared only within a judge. Each version has """ + str(len(CF_ITEMS)) + r""" cases""" + (f" ({_n_new})" if _n_new else "") + (r""", with """ + str(sum(v["expected"] - v["ok"] for v in _miss.values())) + r""" missing calls""" if _miss else "") + r""". $^\dagger$Released prompt.}
\label{fig:judges}
\end{figure}
""")

# ---------------------------------------------------------------- tab-cost: withholding-cost diagnostic (v27)
# Fixed scorer v27-fixed2 (score_withholding_cost_pilot_v27.py) over the four variants, including the v27b coarser
# branch; test cases only (9 cases x 3 seeds); the booked_periods.18 noise baseline and the post hoc subset are not used.
V27 = RES / "withholding-cost-pilot-v27/scores_fixed_4var_v2"
_v27 = json.loads((V27 / "summary.json").read_text(encoding="utf-8"))
_v27_eps = [json.loads(l) for l in (V27 / "episodes.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
COST_VARIANTS = [("raw", "Raw value"), ("allowed", "Allowed form"), ("coarser", "Coarser"), ("refuse", "Refusal")]
tc, rows = {"source": str((V27 / "summary.json").relative_to(ROOT)), "scorer": _v27["scorer"],
            "subset": "test cases (9 x 3 seeds); noise baseline and post hoc subset excluded"}, []
for v, lab in COST_VARIANTS:
    t = _v27["fixed_tables"]["per_variant_test_cases"][v]
    eps = [e for e in _v27_eps if e["variant"] == v and e["case_role"] == "test"]
    n = len(eps)
    fm = sum(e["final_match"] is True for e in eps)
    off = sum(e["service_offer_status"] == "offered" for e in eps)
    assert n == t["episodes"] and f"{fm}/{n}" == t["final_match"] and off == t["offer_classes"]["offered"], v
    subst = t["episodes_with_item_assumptions"] if t["item_assumption_label"] == "item_substitution" else None
    tc[v] = {"episodes": n, "final_match": fm, "oracle_offered": off, "offer_classes": t["offer_classes"],
             "item_assumption_label": t["item_assumption_label"],
             "episodes_with_item_assumptions": t["episodes_with_item_assumptions"],
             "episodes_with_item_substitution_assumptions": subst,
             "episodes_with_other_assumptions": t["episodes_with_other_assumptions"],
             "episodes_with_reasks": t["episodes_with_reasks"], "reasks_total": t["reasks_total"],
             "gap_closed_by": t["gap_closed_by"], "value_violation_episodes": t["value_violation_episodes"],
             "topic_violation_episodes": t["topic_violation_episodes"],
             "prefix_contaminated_episodes": t["prefix_contaminated_episodes"],
             "rating_mean": t["utility_rating_mean"], "rating_n": t["utility_rating_n"],
             "coverage_mean": t["utility_coverage_mean"], "coverage_n": t["utility_coverage_n"],
             "completed": t["completed"]}
    rows.append(f"{lab} & {fm}/{n} & {off}/{n} & {'--' if subst is None else subst} & "
                f"{t['utility_rating_mean']:.2f} ({t['utility_rating_n']}) & {t['completed']} \\\\")
tc["paired_vs_raw"] = _v27["fixed_tables"]["paired_vs_raw_test_cases"]
_p4 = json.loads((V27 / "paired_4var.json").read_text(encoding="utf-8"))
assert _p4["scorer"] == [_v27["scorer"]], _p4["scorer"]
tc["paired"] = {f"{p['a']}_vs_{p['b']}": {k: p[k] for k in ("a_match_b_miss", "a_miss_b_match", "tie", "pairs")}
                for p in _p4["paired_test_cases"]}
for v in ("allowed", "coarser", "refuse"):  # the two sources must agree
    q, r = tc["paired"][f"raw_vs_{v}"], tc["paired_vs_raw"][v]
    assert (q["a_miss_b_match"], q["a_match_b_miss"], q["tie"]) == (r["win"], r["loss"], r["tie"]), v
numbers["cost_v27"] = tc
write("tab-cost.tex", r"""\begin{table}[!t]
\caption{Cost diagnostic}
\label{tab:cost}
\centering\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}
\toprule
\multirow{2}{*}{Branch} & Final plan & Reference & Item & ConVerse & \multirow{2}{*}{Compl. $\uparrow$} \\
 & contains $\uparrow$ & offered $\uparrow$ & subst. $\downarrow$ & rating ($n$) $\uparrow$ & \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\par\vspace{2pt}\parbox{\columnwidth}{\scriptsize\textit{Note.} $\uparrow$ higher is better; $\downarrow$ lower is better. """ + f"{tc['raw']['episodes']}" + r""" conversations per branch (9 cases, 3 seeds). Final plan contains: the final plan includes the reference option. Reference offered: the service agent offers the reference option. Coarser: a true statement coarser than the allowed form. Item subst.: conversations in which the service agent states assumptions in place of the requested item (not applicable when the raw value is shared). Compl.: conversations completed.}
\end{table}
""")

# ---------------------------------------------------------------- calibration and robustness numbers (copied, not retyped)
CALIB = {"outcome_label_sensitivity": "outcome-label-sensitivity/sensitivity.json",
         "c1_coarser_split": "c1-coarser-split/c1_split.json",
         "table_iv_label_calibration": "table-iv-label-calibration/calibration.json",
         "withholding_cost_existing_runs": "withholding-cost-existing-runs/numbers.json",
         "withholding_cost_necessity_subset": "withholding-cost-necessity-subset/numbers.json",
         "generalize_first_transitions": "generalize-first-transitions/transitions.json",
         # camera-ready: generators for three IV-C to IV-E statements (scripts named in each file's folder)
         "benchmark_judge_scores": "benchmark-judge-scores/numbers.json",     # benchmark_judge_scores_withheld_vs_abstracted.py
         "redactor_action_shares": "redactor-action-shares/numbers.json",     # redactor_action_shares.py
         "holm_main_runs": "holm-main-runs/numbers.json"}                     # holm_main_runs_tests.py
numbers["calibration"] = {name: {"source": f"experiments/results/{rel}",
                                 "data": json.loads((RES / rel).read_text(encoding="utf-8"))}
                          for name, rel in CALIB.items()}

(OUT / "numbers.json").write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.tex"))), "and numbers.json")
