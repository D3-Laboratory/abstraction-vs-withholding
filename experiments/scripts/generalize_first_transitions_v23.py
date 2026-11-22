#!/usr/bin/env python3
"""Paired case-level transitions for the generalize-first instruction (paper Table IV, reviewer R1-6).

    python3 -I experiments/scripts/generalize_first_transitions_v23.py

No LLM/API calls. Reads only existing result files:
  results/target-disclosure-outcome-v23-luna/            GPT-5.6 Luna labels, original runs
  results/target-disclosure-outcome-v23/                 GLM-5.3-Flash labels, original runs
  results/over-redaction-replay-v23/judged-luna-nothink  DeepSeek V4 replay, Luna judge (Table IV block 1)
  results/over-redaction-replay-v23/judged-glm-nothink   same replay, GLM judge (cross-judge check only)
  results/over-redaction-replay-v24/judged-glm           DeepSeek V4.1 replay, GLM judge (Table IV block 2)
  results/over-redaction-live-v24/judged-glm             multi-turn runs, GLM judge (Table IV block 3)
  replay records (R-*/records/<case>/*.json), source episodes, live episodes
  results/generalize-first-transitions/newly_leaked_coding.csv (manual coding; tabulated if present)

Case sets follow paper/wllfm-2026/make_tables.py: within a Table IV block, every arm is restricted to the
intersection of cases labeled in all arms of that block (DeepSeek V4 block: 181; V4.1 block: 180;
multi-turn: 182). The "pairwise" variant (intersection of the two compared arms only) is also written,
because the scratch analysis used it.

Writes to results/generalize-first-transitions/:
  transitions.json          every number below, machine-readable
  transitions.txt           human-readable tables
  case_transitions.csv      one row per (setting, case): labels in both arms, item, withheld_kind
  newly_leaked_cases.csv    newly leaked cases (not LEAKED -> LEAKED) with judge evidence located in a release
"""
from __future__ import annotations

import csv
import glob
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
OUT = RES / "generalize-first-transitions"
LABELS = ("LEAKED", "CONVEYED", "WITHHELD")
AB = {"LEAKED": "L", "CONVEYED": "C", "WITHHELD": "W"}


def load(pattern, cond=None) -> dict[str, dict]:
    out = {}
    for f in glob.glob(str(pattern)):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        if cond is None or j["condition"] == cond:
            out[j["case_id"]] = dict(j["judgment"], _file=str(Path(f).relative_to(ROOT)))
    return out


def norm(s: str | None) -> str:
    return " ".join((s or "").replace("*", "").split())


# ------------------------------------------------------------------ labels
luna_orig = {}
for f in glob.glob(str(RES / "target-disclosure-outcome-v23-luna/judgments/*/*.json")):
    j = json.loads(Path(f).read_text(encoding="utf-8"))
    if j["condition"] == "ci_gate_modify":
        luna_orig[j["case_id"]] = dict(j["judgment"], _file=str(Path(f).relative_to(ROOT)))
glm_orig = {}
for f in glob.glob(str(RES / "target-disclosure-outcome-v23/judgments/*/*.json")):
    j = json.loads(Path(f).read_text(encoding="utf-8"))
    if j["condition"] == "ci_gate_modify":
        glm_orig[j["case_id"]] = dict(j["judgment"], _file=str(Path(f).relative_to(ROOT)))
R23L = RES / "over-redaction-replay-v23/judged-luna-nothink/judgments/*/*.json"
R23G = RES / "over-redaction-replay-v23/judged-glm-nothink/judgments/*/*.json"
R24 = RES / "over-redaction-replay-v24/judged-glm/judgments/*/*.json"
LV = RES / "over-redaction-live-v24/judged-glm"
arm = {
    "orig_runs_luna": luna_orig, "orig_runs_glm": glm_orig,
    "v23_orig_luna": load(R23L, "R-orig-nothink"), "v23_abs_luna": load(R23L, "R-abs-nothink"),
    "v23_orig_glm": load(R23G, "R-orig-nothink"), "v23_abs_glm": load(R23G, "R-abs-nothink"),
    "v24_orig_off": load(R24, "R-orig-nothink"), "v24_abs_off": load(R24, "R-abs-nothink"),
    "v24_orig_on": load(R24, "R-orig-think"), "v24_abs_on": load(R24, "R-abs-think"),
    "live_orig": load(LV / "orig/judgments/*/*.json"), "live_abs": load(LV / "absfirst/judgments/*/*.json"),
}
# Table IV blocks (case sets as in make_tables.py)
BLOCKS = {
    "v23": ["orig_runs_luna", "v23_orig_luna", "v23_abs_luna"],
    "v24": ["v24_orig_off", "v24_abs_off", "v24_orig_on", "v24_abs_on"],
    "live": ["live_orig", "live_abs"],
}
block_cases = {b: sorted(set.intersection(*[set(arm[a]) for a in arms])) for b, arms in BLOCKS.items()}

# (setting id, description, from arm, to arm, block or None, kind)
SETTINGS = [
    ("v23", "DeepSeek V4 replay, Luna: original -> generalize first", "v23_orig_luna", "v23_abs_luna", "v23", "instruction"),
    ("v24_off", "DeepSeek V4.1 replay, thinking off, GLM: original -> generalize first", "v24_orig_off", "v24_abs_off", "v24", "instruction"),
    ("v24_on", "DeepSeek V4.1 replay, thinking on, GLM: original -> generalize first", "v24_orig_on", "v24_abs_on", "v24", "instruction"),
    ("live", "Multi-turn DeepSeek V4.1, GLM: original -> generalize first", "live_orig", "live_abs", "live", "instruction"),
    ("rerun_v23_luna", "Re-run baseline, Luna: original runs -> v23 replay of the original instruction", "orig_runs_luna", "v23_orig_luna", "v23", "rerun"),
    ("rerun_v23_glm", "Re-run baseline, GLM: original runs -> v23 replay of the original instruction", "orig_runs_glm", "v23_orig_glm", None, "rerun"),
    ("v23_glm", "DeepSeek V4 replay, GLM judge: original -> generalize first (not in Table IV)", "v23_orig_glm", "v23_abs_glm", None, "instruction_crossjudge"),
    ("think_orig", "DeepSeek V4.1 replay, original instruction: thinking off -> on", "v24_orig_off", "v24_orig_on", "v24", "thinking"),
    ("think_abs", "DeepSeek V4.1 replay, generalize first: thinking off -> on", "v24_abs_off", "v24_abs_on", "v24", "thinking"),
]


def table(a: dict, b: dict, cases: list[str]) -> dict:
    t = Counter((a[c]["outcome"], b[c]["outcome"]) for c in cases)
    m = {x: {y: t[(x, y)] for y in LABELS} for x in LABELS}
    rows = {x: sum(m[x].values()) for x in LABELS}
    cols = {y: sum(m[x][y] for x in LABELS) for y in LABELS}
    flows = {}
    for l in LABELS:
        flows[l] = dict(inflow=cols[l] - m[l][l], outflow=rows[l] - m[l][l], net=cols[l] - rows[l])
    changed = len(cases) - sum(m[x][x] for x in LABELS)
    return dict(n=len(cases), matrix_from_rows_to_cols=m, from_totals=rows, to_totals=cols, flows=flows,
                changed=changed, unchanged=len(cases) - changed)


meta = {}
for f in glob.glob(str(RES / "over-redaction-live-v24/orig/episodes/*/ci_gate_modify.json")):
    c = json.loads(Path(f).read_text(encoding="utf-8"))["case"]
    meta[c["case_id"]] = c

report: dict = {"block_case_counts": {b: len(v) for b, v in block_cases.items()}, "settings": {}}
case_rows = []
newly = {}  # setting -> set of newly leaked cases (block case set)
for sid, desc, fa, ta, blk, kind in SETTINGS:
    A, B = arm[fa], arm[ta]
    pair = sorted(set(A) & set(B))
    cases = block_cases[blk] if blk else pair
    r = {"description": desc, "from_arm": fa, "to_arm": ta, "kind": kind,
         "case_set": f"Table IV block '{blk}'" if blk else "pairwise intersection",
         "block": table(A, B, cases)}
    if blk:
        r["pairwise"] = table(A, B, pair)
        r["pairwise_minus_block_cases"] = sorted(set(pair) - set(cases))
    # withheld_kind shifts
    wk_a = Counter(A[c].get("withheld_kind") for c in cases if A[c]["outcome"] == "WITHHELD")
    wk_b = Counter(B[c].get("withheld_kind") for c in cases if B[c]["outcome"] == "WITHHELD")
    w_from = Counter(f"{A[c].get('withheld_kind')}->{B[c]['outcome']}" for c in cases if A[c]["outcome"] == "WITHHELD")
    r["withheld_kind"] = dict(from_arm=dict(wk_a), to_arm=dict(wk_b), from_withheld_kind_to_outcome=dict(w_from))
    report["settings"][sid] = r
    newly[sid] = {c for c in cases if B[c]["outcome"] == "LEAKED" and A[c]["outcome"] != "LEAKED"}
    for c in cases:
        case_rows.append(dict(setting=sid, case_id=c, data_item=meta[c]["data_item"], from_label=A[c]["outcome"],
                              to_label=B[c]["outcome"], from_withheld_kind=A[c].get("withheld_kind"),
                              to_withheld_kind=B[c].get("withheld_kind")))

# ------------------------------------------------------------------ overlap of newly leaked sets
INSTR = ["v23", "v24_off", "v24_on", "live"]
ov = {}
for a, b in combinations(INSTR + ["v23_glm"], 2):
    inter = newly[a] & newly[b]
    ov[f"{a}&{b}"] = dict(n_a=len(newly[a]), n_b=len(newly[b]), both=len(inter),
                         jaccard=round(len(inter) / max(1, len(newly[a] | newly[b])), 3))
union_replay = newly["v23"] | newly["v24_off"] | newly["v24_on"]
in_k = Counter(sum(c in newly[s] for s in INSTR) for c in set().union(*[newly[s] for s in INSTR]))
report["newly_leaked"] = {
    "counts": {s: len(newly[s]) for s in newly},
    "overlap_pairs": ov,
    "union_three_replays": len(union_replay),
    "union_four_settings": len(set().union(*[newly[s] for s in INSTR])),
    "cases_by_number_of_instruction_settings": dict(sorted(in_k.items())),
    # same releases, two judges: does the GLM judge also see a new leak where Luna does?
    "crossjudge_v23": {
        "luna_newly_leaked": len(newly["v23"]),
        "glm_newly_leaked": len(newly["v23_glm"]),
        "both": len(newly["v23"] & newly["v23_glm"]),
        "luna_newly_leaked_glm_labels": dict(Counter(
            f"{arm['v23_orig_glm'][c]['outcome'][0]}->{arm['v23_abs_glm'][c]['outcome'][0]}" if c in arm["v23_orig_glm"] and c in arm["v23_abs_glm"] else "missing"
            for c in newly["v23"])),
    },
}


# ------------------------------------------------------------------ releases and leak-turn timing
REPLAY = {  # setting -> (replay base dir, judged dir, to-condition)
    "v23": ("over-redaction-replay-v23", "judged-luna-nothink", "R-abs-nothink"),
    "v24_off": ("over-redaction-replay-v24", "judged-glm", "R-abs-nothink"),
    "v24_on": ("over-redaction-replay-v24", "judged-glm", "R-abs-think"),
}


def released(setting: str, case: str):
    """Return (releases{turn: (text, file)}, external{turn: text}) of the generalize-first arm."""
    rel, ext = {}, {}
    if setting == "live":
        f = RES / "over-redaction-live-v24/absfirst/episodes" / case / "ci_gate_modify.json"
        ep = json.loads(f.read_text(encoding="utf-8"))
        for t in ep["transcript"]:
            if t.get("to") == "external":
                rel[int(t["turn"])] = (t["message"], str(f.relative_to(ROOT)))
            elif t.get("from") == "external":
                ext[int(t["turn"])] = t["message"]
        return rel, ext
    base, _, cond = REPLAY[setting]
    src = None
    for f in glob.glob(str(RES / base / cond / "records" / case / "*.json")):
        r = json.loads(Path(f).read_text(encoding="utf-8"))
        if "replay" not in r:
            continue
        p = r["replay"]
        out = r["candidate"] if p["action"] == "PASS_THROUGH" else p["released_message"]
        rel[int(r["turn"])] = (out, str(Path(f).relative_to(ROOT)))
        src = r["source_path"]
    ep = json.loads((ROOT / src).read_text(encoding="utf-8"))
    for t in ep["transcript"]:
        if t.get("from") == "external":
            ext[int(t["turn"])] = t["message"]
    return rel, ext


def released_orig(setting: str, case: str):
    """Releases of the original-instruction arm (same setting)."""
    if setting == "live":
        f = RES / "over-redaction-live-v24/orig/episodes" / case / "ci_gate_modify.json"
        ep = json.loads(f.read_text(encoding="utf-8"))
        return {int(t["turn"]): (t["message"], str(f.relative_to(ROOT))) for t in ep["transcript"] if t.get("to") == "external"}, {}
    base, _, cond = REPLAY[setting]
    cond = cond.replace("abs", "orig")
    rel = {}
    for f in glob.glob(str(RES / base / cond / "records" / case / "*.json")):
        r = json.loads(Path(f).read_text(encoding="utf-8"))
        if "replay" in r:
            p = r["replay"]
            rel[int(r["turn"])] = (r["candidate"] if p["action"] == "PASS_THROUGH" else p["released_message"], f)
    return rel, {}


def draft(setting: str, case: str, turn: int) -> str:
    """The assistant's draft (redactor input) at a turn of the generalize-first arm."""
    if setting == "live":
        ep = json.loads((RES / "over-redaction-live-v24/absfirst/episodes" / case / "ci_gate_modify.json").read_text(encoding="utf-8"))
        for t in ep["transcript"]:
            if t.get("to") == "external" and int(t["turn"]) == turn:
                return t.get("candidate") or ""
        return ""
    base, _, cond = REPLAY[setting]
    for f in glob.glob(str(RES / base / cond / "records" / case / "*.json")):
        r = json.loads(Path(f).read_text(encoding="utf-8"))
        if int(r["turn"]) == turn:
            return r["candidate"]
    return ""


nl_rows = []
timing = {}
for s in INSTR:
    J = arm[{"v23": "v23_abs_luna", "v24_off": "v24_abs_off", "v24_on": "v24_abs_on", "live": "live_abs"}[s]]
    Jf = arm[{"v23": "v23_orig_luna", "v24_off": "v24_orig_off", "v24_on": "v24_orig_on", "live": "live_orig"}[s]]
    dist, located, first_after_ask, ask_known, next_turn = Counter(), 0, 0, 0, 0
    for c in sorted(newly[s]):
        rel, ext = released(s, c)
        relnorm = {t: norm(v[0]) for t, v in rel.items()}
        extnorm = {t: norm(v) for t, v in ext.items()}
        leak_t, ask_t, quote, fpath = None, None, "", ""
        for e in J[c].get("evidence") or []:
            q, t = norm(e["quote"])[:60], e["turn"]
            if not q:
                continue
            if t in relnorm and q in relnorm[t]:
                if leak_t is None or t < leak_t:
                    leak_t, quote, fpath = t, e["quote"], rel[t][1]
            elif t in extnorm and q in extnorm[t]:
                ask_t = t if ask_t is None else min(ask_t, t)
        if leak_t is not None:
            located += 1
            dist[leak_t] += 1
            if ask_t is not None:
                ask_known += 1
                later_ext = [t for t in ext if ask_t < t < leak_t]
                first_after_ask += (leak_t > ask_t and not later_ext)
                next_turn += (leak_t == ask_t + 1)  # scratch definition
        # is the same leak quote (first 120 normalized chars) also in a release of the original-instruction arm?
        in_orig = ""
        if leak_t is not None:
            orel, _ = released_orig(s, c)
            q120 = norm(quote)[:120]
            in_orig = any(q120 in norm(v[0]) for v in orel.values())
            in_draft = q120 in norm(draft(s, c, leak_t))
        else:
            in_draft = ""
        nl_rows.append(dict(setting=s, case_id=c, data_item=meta[c]["data_item"],
                            allowed_form=meta[c]["acceptable_abstraction"],
                            raw_value=" | ".join(map(str, meta[c]["raw_data"])),
                            from_label=Jf[c]["outcome"], leak_turn=leak_t, first_ask_turn_in_evidence=ask_t,
                            n_releases=len(rel), last_release_turn=max(rel) if rel else None,
                            evidence_quote=norm(quote)[:300], quote_in_draft=in_draft,
                            quote_in_original_instruction_release=in_orig,
                            release_file=fpath, judge_file=J[c]["_file"]))
    mine = [r for r in nl_rows if r["setting"] == s]
    timing[s] = dict(n_newly_leaked=len(newly[s]), leak_quote_located_in_release=located,
                     leak_quote_copied_from_draft=sum(r["quote_in_draft"] is True for r in mine),
                     leak_quote_also_in_original_instruction_release=sum(r["quote_in_original_instruction_release"] is True for r in mine),
                     leak_turn_distribution=dict(sorted(dist.items())),
                     with_ask_turn_in_evidence=ask_known,
                     leak_in_first_release_after_evidence_ask=first_after_ask,
                     leak_turn_equals_ask_turn_plus_1=next_turn)
report["leak_turn_timing"] = timing


# ------------------------------------------------------------------ name items: shortened to an initial?
def name_form(out: str, name: str) -> str:
    parts = name.split()
    fn, ln = parts[0], parts[-1]
    if name in out:
        return "full"
    if len(parts) > 1 and re.search(rf"{re.escape(fn)}\s+{re.escape(ln[0])}\.", out):
        return "initial"
    if re.search(rf"\b{re.escape(fn)}\b", out):
        return "first_only"
    return "none"


names = {}
for base, conds in (("over-redaction-replay-v23", ("R-orig-nothink", "R-abs-nothink")),
                    ("over-redaction-replay-v24", ("R-orig-nothink", "R-abs-nothink", "R-orig-think", "R-abs-think"))):
    for cond in conds:
        c = Counter()
        for f in glob.glob(str(RES / base / cond / "records/*_name.01/*.json")):
            r = json.loads(Path(f).read_text(encoding="utf-8"))
            if "replay" not in r:
                continue
            name = meta[r["case_id"]]["raw_data"][0]
            if name not in r["candidate"]:
                continue
            out = r["candidate"] if r["replay"]["action"] == "PASS_THROUGH" else (r["replay"]["released_message"] or "")
            c[name_form(out, name)] += 1
        names[f"{base.split('-')[-1]}/{cond}"] = dict(c)
for var in ("orig", "absfirst"):
    c = Counter()
    for f in glob.glob(str(RES / f"over-redaction-live-v24/{var}/episodes/*_name.01/ci_gate_modify.json")):
        ep = json.loads(Path(f).read_text(encoding="utf-8"))
        name = ep["case"]["raw_data"][0]
        for t in ep["transcript"]:
            if t.get("to") == "external" and name in (t.get("candidate") or ""):
                c[name_form(t["message"], name)] += 1
    names[f"live/{var}"] = dict(c)
gf = [k for k in names if "abs" in k]
report["name_items"] = {
    "note": "releases whose draft contained the user's full name (cases *_name.01); form of the name in the released message",
    "by_arm": names,
    "generalize_first_releases_with_name_in_draft": sum(sum(names[k].values()) for k in gf),
    "generalize_first_initial": sum(names[k].get("initial", 0) for k in gf),
    "replay_v23_v24_generalize_first_thinking_off": sum(sum(names[k].values()) for k in ("v23/R-abs-nothink", "v24/R-abs-nothink")),
}

# ------------------------------------------------------------------ manual coding (if present)
coding_f = OUT / "newly_leaked_coding.csv"
if coding_f.exists():
    rows = list(csv.DictReader(coding_f.open(encoding="utf-8")))
    keyset = {(r["setting"], r["case_id"]) for r in nl_rows}
    unknown = [(r["setting"], r["case_id"]) for r in rows if (r["setting"], r["case_id"]) not in keyset]
    assert not unknown, f"coding rows not in newly leaked sets: {unknown}"
    final = Counter(r["final_code"] for r in rows)
    first = Counter(r["pattern_code"] for r in rows)
    rc = [r for r in rows if r.get("recheck") in ("agree", "recode")]
    report["manual_coding"] = {
        "status": "coded by Claude (LLM), partially re-checked by Claude; not human annotation",
        "n_coded": len(rows), "by_setting": dict(Counter(r["setting"] for r in rows)),
        "first_pass_counts": dict(sorted(first.items())), "final_counts": dict(sorted(final.items())),
        "rechecked": len(rc), "recheck_agree": sum(r["recheck"] == "agree" for r in rc),
        "recheck_recode": sum(r["recheck"] == "recode" for r in rc),
        "final_counts_v23_plus_v24_on": dict(sorted(Counter(r["final_code"] for r in rows if r["setting"] in ("v23", "v24_on")).items())),
        "same_detail_in_original_arm": dict(Counter(r["same_detail_in_original_arm"] for r in rows)),
        "final_counts_by_setting": {s: dict(sorted(Counter(r["final_code"] for r in rows if r["setting"] == s).items()))
                                    for s in sorted({r["setting"] for r in rows})},
    }

# ------------------------------------------------------------------ write
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "transitions.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
with (OUT / "case_transitions.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(case_rows[0]))
    w.writeheader()
    w.writerows(case_rows)
with (OUT / "newly_leaked_cases.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(nl_rows[0]))
    w.writeheader()
    w.writerows(nl_rows)

L = []
for sid, r in report["settings"].items():
    for var in ("block", "pairwise"):
        if var not in r:
            continue
        t = r[var]
        L.append(f"\n== {sid} [{var}{'' if var == 'pairwise' else ': ' + r['case_set']}]  {r['description']}  n={t['n']}")
        L.append("from\\to    " + "".join(f"{x:>10}" for x in LABELS) + "     row")
        for x in LABELS:
            L.append(f"{x:10} " + "".join(f"{t['matrix_from_rows_to_cols'][x][y]:>10}" for y in LABELS) + f"{t['from_totals'][x]:>8}")
        L.append("col        " + "".join(f"{t['to_totals'][y]:>10}" for y in LABELS))
        L.append(f"changed={t['changed']}  " + "  ".join(
            f"{AB[l]}: in {f['inflow']} out {f['outflow']} net {f['net']:+d}" for l, f in t["flows"].items()))
    if r.get("pairwise_minus_block_cases"):
        L.append(f"  cases in pairwise but not block: {r['pairwise_minus_block_cases']}")
    wk = r["withheld_kind"]
    L.append(f"  withheld_kind from: {wk['from_arm']}\n  withheld_kind to:   {wk['to_arm']}\n  W(kind)->outcome:   {wk['from_withheld_kind_to_outcome']}")
L.append("\n== newly leaked (not LEAKED -> LEAKED), block case sets")
L.append(json.dumps(report["newly_leaked"], indent=1))
L.append("\n== leak-turn timing (generalize-first arm, first judge-evidence quote found in a released message)")
L.append(json.dumps(timing, indent=1))
L.append("\n== name items")
L.append(json.dumps(report["name_items"], indent=1))
if "manual_coding" in report:
    L.append("\n== manual coding of newly leaked cases")
    L.append(json.dumps(report["manual_coding"], indent=1))
(OUT / "transitions.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
