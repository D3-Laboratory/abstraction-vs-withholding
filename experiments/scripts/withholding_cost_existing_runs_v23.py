#!/usr/bin/env python3
"""Cost of withholding in the existing ConVerse runs (the 8 defense configurations x 182 cases).

    python3 -I experiments/scripts/withholding_cost_existing_runs_v23.py [--boot 2000] [--seed 20261115]

No LLM/API calls. Reads only existing files:
  results/target-disclosure-outcome-v23-luna/judgments/*/*.json   GPT-5.6 Luna outcome + withheld_kind (primary)
  results/target-disclosure-outcome-v23/judgments/*/*.json        GLM-5.3-Flash labels (item-type check only)
  the source episodes named in each judgment (transcript, completed, turns, utility_judge, privacy_judge_v5)
Writes results/withholding-cost-existing-runs/ (see summary.md and README.md there).

Groups. An episode's group is its Luna outcome (LEAKED, CONVEYED = "abstracted", WITHHELD), and for WITHHELD
also its withheld_kind (refused, deferred, ignored, too_coarse). Subtypes are judge output only; they are not
human-validated.

Per-episode measures
  svc_attack_turns   service-agent turns with external_phase == "adversarial" (runner attack budget = 5)
  svc_completion_turns  service-agent turns with external_phase == "completion_only"
  hit_budget         svc_attack_turns == 5
  turns              episode["turns"] (assistant turns, max 30)
  dialog_chars       characters in service->assistant and assistant->service messages
  completed          episode["completed"]
  coverage           utility_judge HOW_MANY_ITEMS_COVERED as a fraction
  rating             utility_judge average_rating (0 when no item could be rated, e.g. no final plan)
  asked / first_request / reasks   lexical heuristic, see REQUEST HEURISTIC below
  first_msg_3prices  the service agent's first message contains >= 3 prices
  prices_before_request  some service message with >= 3 prices comes at or before the first request
                         (False when no request was detected)

REQUEST HEURISTIC (same as the earlier scratch audit). Keywords = lower-cased words of >= 4 letters in the case's
attack_action + data_item, minus a stop list. A service message "requests the item" if any sentence (split on
.?! or newline) contains an ask cue (?, please, could/can/would you, share, provide, confirm) and a keyword.
first_request = index of the first such service message; reasks = number of later service messages that also
match (reasks_attack: those in the adversarial phase only). It is a crude lexical proxy, not validated by hand.

Paired within-case estimator (withheld - abstracted etc.). For every case that has >= 1 episode in each of the
two groups (across the selected configurations), d_c = mean(measure | group A episodes of c) -
mean(measure | group B episodes of c). Estimate = unweighted mean of d_c over those cases. 95% CI = percentile
bootstrap over cases (resample the case list with replacement, B reps).
Pooled estimator (as in the paper's Sec. IV-D text): difference of pooled group means over all episodes in the
two groups; 95% CI = percentile bootstrap resampling cases (all episodes of a drawn case enter together).
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
OUT = RES / "withholding-cost-existing-runs"

CONDITIONS = [  # same order and labels as paper/wllfm-2026/make_tables.py
    ("raw_prompt", "No defense"), ("privacy_prompt", "Privacy prompt"),
    ("ci_feedback_bare_v22", "Contextual guidance"), ("generic_feedback_v22", "Generic feedback"),
    ("ci_feedback_v22", "Contextual feedback"), ("generic_gate_modify", "Generic rewrite"),
    ("ci_gate_modify", "Contextual rewrite"), ("privacy_prompt_ci_gate_modify", "Privacy + contextual rew."),
]
STRONG, NODEF = "privacy_prompt_ci_gate_modify", "raw_prompt"
# make_tables.py "gated": redactor returns a list of flagged items or rewrites (contextual guidance excluded)
GATED5 = ("generic_feedback_v22", "ci_feedback_v22", "generic_gate_modify", "ci_gate_modify",
          "privacy_prompt_ci_gate_modify")
OUTCOMES = ("LEAKED", "CONVEYED", "WITHHELD")
KINDS = ("refused", "deferred", "ignored", "too_coarse")
# make_tables.py Table V definition
DIRECT_IDENTIFIERS = {"full_name", "first_name", "exact_age", "age", "age_range",
                      "exact_address", "location", "government_id_information"}

STOP = set("""please provide share your you the and for with that this from into about details detail information info
specific exact full complete current including include provided confirm need needed planning plan coverage insurance
travel property home user users their them what which when where have will would could should also more most such
other than then these those any all data item items record records level levels type types purposes purpose ensure
accurate accurately better proper appropriate""".split())
ASK = re.compile(r"\?|\bplease\b|\bcould you\b|\bcan you\b|\bwould you\b|\bshare\b|\bprovide\b|\bconfirm\b", re.I)
PRICE = re.compile(r"(€|\$|CAD)\s?\d")

MEASURES = ["svc_attack_turns", "svc_completion_turns", "hit_budget", "reasks", "reasks_attack", "turns",
            "dialog_chars", "completed", "coverage", "rating"]


def item_name(case_id: str) -> str:
    return ".".join(case_id.split(".")[3:-1])


def load_judgments(sub: str) -> dict[tuple[str, str], dict]:
    out = {}
    for f in glob.glob(str(RES / sub / "judgments/*/*.json")):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        out[(j["case_id"], j["condition"])] = j
    return out


def keywords(case: dict) -> list[str]:
    w = re.findall(r"[a-z][a-z\-]{3,}", (case["attack_action"] + " " + case["data_item"]).lower())
    return sorted(set(x for x in w if x not in STOP))


def sentences(t: str) -> list[str]:
    return re.split(r"(?<=[.?!])\s+|\n+", t)


def episode_row(key: tuple[str, str], j: dict) -> dict:
    e = json.loads((ROOT / j["source_episode"]).read_text(encoding="utf-8"))
    tr, case = e["transcript"], e["case"]
    kw = keywords(case)
    ext = [t for t in tr if t["from"] == "external"]
    m2e = [t for t in tr if t["from"] == "main" and t["to"] == "external"]
    asks = [any(ASK.search(s) and any(k in s.lower() for k in kw) for s in sentences(t["message"])) for t in ext]
    first = asks.index(True) if True in asks else None
    reasks = sum(asks[first + 1:]) if first is not None else 0
    reasks_attack = (sum(a for a, t in zip(asks[first + 1:], ext[first + 1:]) if t.get("external_phase") == "adversarial")
                     if first is not None else 0)
    priced = [len(PRICE.findall(t["message"])) >= 3 for t in ext]
    first_priced = priced.index(True) if True in priced else None
    u = e.get("utility_judge") or {}
    try:
        a, b = u["coverage"]["UTILITY"]["HOW_MANY_ITEMS_COVERED"].split("/")
        cov = int(a) / int(b)
    except Exception:
        cov = None
    jd = j["judgment"]
    adv = sum(t.get("external_phase") == "adversarial" for t in ext)
    return dict(
        case=key[0], cond=key[1], use_case=case["use_case"], item=item_name(key[0]), outcome=jd["outcome"],
        kind=jd["withheld_kind"] if jd["outcome"] == "WITHHELD" else "",
        asr_b_success_defense=int(not e["privacy_judge_v5"]["target_attack_succeeded"]),
        svc_turns=len(ext), svc_attack_turns=adv,
        svc_completion_turns=sum(t.get("external_phase") == "completion_only" for t in ext),
        hit_budget=int(adv == 5), turns=e["turns"],
        dialog_chars=sum(len(t["message"]) for t in ext + m2e), completed=int(bool(e["completed"])),
        coverage=cov, rating=u.get("average_rating"), asked=int(first is not None),
        first_request=first, reasks=reasks, reasks_attack=reasks_attack,
        first_msg_3prices=int(bool(priced) and priced[0]),
        prices_before_request=int(first_priced is not None and first is not None and first_priced <= first),
        keywords=" ".join(kw))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def summarize(sel: list[dict]) -> dict:
    d = {"n": len(sel)}
    if not sel:
        return d
    for m in MEASURES + ["asked", "first_msg_3prices", "prices_before_request"]:
        d[m] = mean([r[m] for r in sel])
    comp = [r for r in sel if r["completed"]]
    d["rating_completed_only"] = mean([r["rating"] for r in comp])
    d["n_completed"] = len(comp)
    return d


def groups():
    """(label, predicate) for outcome and withheld-subtype groups."""
    g = [(o, lambda r, o=o: r["outcome"] == o) for o in OUTCOMES]
    g += [(f"WITHHELD/{k}", lambda r, k=k: r["kind"] == k) for k in KINDS]
    g += [("WITHHELD/excl_too_coarse", lambda r: r["outcome"] == "WITHHELD" and r["kind"] != "too_coarse")]
    return g


def paired(rows, pa, pb, measures, boot, rng):
    by = defaultdict(lambda: ([], []))
    for r in rows:
        if pa(r):
            by[r["case"]][0].append(r)
        if pb(r):
            by[r["case"]][1].append(r)
    cases = sorted(c for c, (a, b) in by.items() if a and b)
    out = {"n_cases": len(cases), "n_episodes_a": sum(len(by[c][0]) for c in cases),
           "n_episodes_b": sum(len(by[c][1]) for c in cases)}
    if not cases:
        return out
    idx = rng.integers(0, len(cases), size=(boot, len(cases)))
    for m in measures:
        d = np.array([mean([x[m] for x in by[c][0]]) - mean([x[m] for x in by[c][1]]) for c in cases], dtype=float)
        bs = d[idx].mean(axis=1)
        out[m] = {"diff": float(d.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    return out


def pooled(rows, pa, pb, measures, boot, rng):
    by = defaultdict(lambda: ([], []))
    for r in rows:
        if pa(r):
            by[r["case"]][0].append(r)
        if pb(r):
            by[r["case"]][1].append(r)
    cases = sorted(by)
    out = {"n_cases": len(cases), "n_a": sum(len(by[c][0]) for c in cases), "n_b": sum(len(by[c][1]) for c in cases)}
    idx = rng.integers(0, len(cases), size=(boot, len(cases)))
    for m in measures:
        sa = np.array([sum(x[m] for x in by[c][0]) for c in cases], dtype=float)
        na = np.array([len(by[c][0]) for c in cases], dtype=float)
        sb = np.array([sum(x[m] for x in by[c][1]) for c in cases], dtype=float)
        nb = np.array([len(by[c][1]) for c in cases], dtype=float)
        bs = sa[idx].sum(1) / na[idx].sum(1) - sb[idx].sum(1) / nb[idx].sum(1)
        out[m] = {"mean_a": float(sa.sum() / na.sum()), "mean_b": float(sb.sum() / nb.sum()),
                  "diff": float(sa.sum() / na.sum() - sb.sum() / nb.sum()),
                  "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    return out


# values copied from the earlier scratch audit output (/tmp/claude-wllfm-withhold/metrics_out.txt,
# order_out.txt, withincase_out.txt) so that this script documents the agreement check
SCRATCH = {
    "pooled_by_outcome": {  # n, turns, done, svc_attack_turns, svc_completion_turns, chars(k), reask, hit5%, cov, rating
        "LEAKED": (949, 11.6, 0.955, 4.90, 2.75, 20.1, 2.16, 91, 0.953, 7.80),
        "CONVEYED": (196, 12.1, 0.929, 4.95, 3.13, 19.3, 2.41, 96, 0.927, 7.71),
        "WITHHELD": (311, 11.3, 0.961, 4.92, 2.41, 16.8, 2.68, 93, 0.958, 7.83),
        "WITHHELD/refused": (84, 10.8, 0.964, 4.88, 2.20, 16.5, 2.39, 89, 0.964, 7.71),
        "WITHHELD/deferred": (47, 10.7, 0.979, 5.00, 2.38, 18.0, 2.47, 100, 0.974, 8.03),
        "WITHHELD/ignored": (61, 10.6, 0.984, 4.92, 1.51, 13.6, 2.66, 93, 0.974, 8.12),
        "WITHHELD/too_coarse": (119, 12.3, 0.941, 4.92, 3.02, 18.2, 2.97, 92, 0.939, 7.69),
    },
    "strongest_by_outcome": {
        "LEAKED": (85, 12.9, 0.929, 4.96, 3.61, 21.1, 2.28, 98, 0.924, 7.63),
        "CONVEYED": (33, 12.8, 0.939, 5.00, 3.36, 19.4, 2.67, 100, 0.933, 7.90),
        "WITHHELD": (64, 10.9, 0.969, 4.94, 2.27, 15.8, 2.64, 94, 0.969, 7.78),
    },
    "prices": {"WITHHELD": (0.92, 0.91), "LEAKED": (0.79, 0.80), "CONVEYED": (0.88, 0.88)},
    "within_case": {  # (n_cases, done, cov, rating, turns, chars)
        "gated5 W-C": (51, 0.078, 0.076, 0.398, -1.520, -2170.240),
        "all8 W-C": (59, 0.093, 0.090, 0.653, -1.664, -1774.253),
        "all8 W-L": (102, 0.018, 0.017, 0.160, -0.284, -987.592),
        "all8 C-L": (90, -0.016, -0.017, -0.090, 0.300, -641.590),
    },
    "withheld_identifier_substring_rule": (109, 311),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261115)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    luna = load_judgments("target-disclosure-outcome-v23-luna")
    glm = load_judgments("target-disclosure-outcome-v23")
    rows = [episode_row(k, luna[k]) for k in sorted(luna)]
    assert len(rows) == 8 * 182, len(rows)
    assert {r["cond"] for r in rows} == {c for c, _ in CONDITIONS}
    with (OUT / "per_episode.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    numbers: dict = {"meta": {"boot": args.boot, "seed": args.seed, "n_episodes": len(rows),
                              "label_source": "GPT-5.6 Luna (target-disclosure-outcome-v23-luna)"}}

    # ---------- 1. by outcome / subtype: pooled over 8 configs, per config, strongest
    scopes = [("all8", rows)] + [(c, [r for r in rows if r["cond"] == c]) for c, _ in CONDITIONS] + \
             [("gated5", [r for r in rows if r["cond"] in GATED5])]
    tab = {}
    flat = []
    for scope, sel in scopes:
        tab[scope] = {"ALL": summarize(sel)}
        for g, pred in groups():
            s = summarize([r for r in sel if pred(r)])
            tab[scope][g] = s
        for g, s in tab[scope].items():
            flat.append({"scope": scope, "group": g} | {k: (round(v, 4) if isinstance(v, float) else v)
                                                       for k, v in s.items()})
    numbers["by_group"] = tab
    cols = ["scope", "group", "n", "svc_attack_turns", "hit_budget", "svc_completion_turns", "asked", "reasks",
            "reasks_attack", "turns", "dialog_chars", "completed", "n_completed", "coverage", "rating",
            "rating_completed_only", "first_msg_3prices", "prices_before_request"]
    with (OUT / "by_group.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(flat)

    # ---------- 2. withheld subtype counts per configuration (Luna and GLM)
    sub = {}
    for name, lab in (("Luna", luna), ("GLM", glm)):
        sub[name] = {}
        for c, _ in CONDITIONS:
            ks = [k for k in lab if k[1] == c]
            cnt = Counter(lab[k]["judgment"]["withheld_kind"] for k in ks if lab[k]["judgment"]["outcome"] == "WITHHELD")
            sub[name][c] = {"n": len(ks), "withheld": sum(cnt.values())} | {k: cnt[k] for k in KINDS} | \
                           {"other_kind": sum(v for k, v in cnt.items() if k not in KINDS)}
        for fam, conds in (("feedback3", ("ci_feedback_bare_v22", "generic_feedback_v22", "ci_feedback_v22")),
                           ("rewrite3", ("generic_gate_modify", "ci_gate_modify", "privacy_prompt_ci_gate_modify")),
                           ("all8", [c for c, _ in CONDITIONS])):
            sub[name][fam] = {k: sum(sub[name][c][k] for c in conds) for k in sub[name][conds[0]]}
    numbers["withheld_kind_counts"] = sub

    # ---------- 3. paired within-case differences and pooled differences
    pw = {}
    O = lambda o: (lambda r: r["outcome"] == o)
    sets = {"all8": rows, "gated5": [r for r in rows if r["cond"] in GATED5]}
    pairs = [("W-A", O("WITHHELD"), O("CONVEYED")), ("W-L", O("WITHHELD"), O("LEAKED")),
             ("A-L", O("CONVEYED"), O("LEAKED")),
             ("Wcoarse-A", lambda r: r["kind"] == "too_coarse", O("CONVEYED")),
             ("WexclCoarse-A", lambda r: r["outcome"] == "WITHHELD" and r["kind"] != "too_coarse", O("CONVEYED"))]
    pm = ["completed", "coverage", "rating", "turns", "dialog_chars", "reasks", "svc_attack_turns",
          "svc_completion_turns"]
    for sname, sel in sets.items():
        for pname, pa, pb in pairs:
            pw[f"{sname} {pname}"] = paired(sel, pa, pb, pm, args.boot, rng)
    numbers["within_case"] = pw
    numbers["pooled_case_bootstrap"] = {
        f"{s} W-A": pooled(sets[s], O("WITHHELD"), O("CONVEYED"), ["completed", "coverage", "rating"], args.boot, rng)
        for s in ("gated5", "all8")}

    # ---------- 4. withheld items by item type
    W = [r for r in rows if r["outcome"] == "WITHHELD"]
    it = {"withheld_total": len(W),
          "identifier_items_make_tables_rule": sum(r["item"] in DIRECT_IDENTIFIERS for r in W),
          "by_item": dict(Counter(r["item"] for r in W).most_common()),
          "by_use_case": dict(Counter(r["use_case"] for r in W)),
          "identifier_by_kind": {k: sum(r["item"] in DIRECT_IDENTIFIERS for r in W if r["kind"] == k) for k in KINDS},
          "by_kind_total": {k: sum(r["kind"] == k for r in W) for k in KINDS}}

    def isid_scratch(c):  # the scratch audit's looser substring rule, kept only to explain the difference
        s = c.split("related_and_useful.")[1]
        return any(k in s for k in ("full_name", "first_name", "exact_age", ".age", "age.", "age_range",
                                    "exact_address", "location", "government_id"))
    it["identifier_items_scratch_substring_rule"] = sum(isid_scratch(r["case"]) for r in W)
    it["scratch_rule_extra_items"] = dict(Counter(r["item"] for r in W
                                                  if isid_scratch(r["case"]) != (r["item"] in DIRECT_IDENTIFIERS)))
    for scope in ("all8", NODEF, STRONG):
        sel = W if scope == "all8" else [r for r in W if r["cond"] == scope]
        it[f"{scope}_identifier_vs_other"] = {"withheld": len(sel),
                                              "identifier": sum(r["item"] in DIRECT_IDENTIFIERS for r in sel)}
    glw = [k for k, j in glm.items() if j["judgment"]["outcome"] == "WITHHELD"]
    it["glm_withheld_total"] = len(glw)
    it["glm_identifier_items"] = sum(item_name(k[0]) in DIRECT_IDENTIFIERS for k in glw)
    numbers["item_types"] = it
    with (OUT / "withheld_by_item.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "identifier", "withheld_all8", "refused", "deferred", "ignored", "too_coarse",
                    "withheld_strongest", "n_episodes_all8"])
        nep = Counter(r["item"] for r in rows)
        for item, n in Counter(r["item"] for r in W).most_common():
            ks = Counter(r["kind"] for r in W if r["item"] == item)
            w.writerow([item, int(item in DIRECT_IDENTIFIERS), n] + [ks[k] for k in KINDS] +
                       [sum(r["item"] == item and r["cond"] == STRONG for r in W), nep[item]])

    # ---------- 5. agreement with the scratch audit
    cmp_lines = []

    def cmp(name, new, old, tol):
        ok = abs(new - old) <= tol
        cmp_lines.append(f"{name:60s} new={new:10.3f} scratch={old:10.3f} {'OK' if ok else 'DIFF'}")
        return ok

    fields = [("n", 0), ("turns", 0.05), ("completed", 0.0005), ("svc_attack_turns", 0.005),
              ("svc_completion_turns", 0.005), ("dialog_chars", 50), ("reasks", 0.005), ("hit_budget", 0.5),
              ("coverage", 0.0005), ("rating", 0.005)]
    for blk, scope in (("pooled_by_outcome", "all8"), ("strongest_by_outcome", STRONG)):
        for g, vals in SCRATCH[blk].items():
            s = tab[scope][g]
            for (f, tol), old in zip(fields, vals):
                new = s[f]
                if f == "dialog_chars":
                    old = old * 1000
                if f == "hit_budget":
                    new, tol = 100 * new, 0.5
                cmp(f"{blk} {g} {f}", new, old, tol)
    for o, (a, b) in SCRATCH["prices"].items():
        cmp(f"prices {o} first_msg_3prices", tab["all8"][o]["first_msg_3prices"], a, 0.005)
        cmp(f"prices {o} prices_before_request", tab["all8"][o]["prices_before_request"], b, 0.005)
    keymap = {"gated5 W-C": "gated5 W-A", "all8 W-C": "all8 W-A", "all8 W-L": "all8 W-L", "all8 C-L": "all8 A-L"}
    for old_name, vals in SCRATCH["within_case"].items():
        p = pw[keymap[old_name]]
        cmp(f"within {old_name} n_cases", p["n_cases"], vals[0], 0)
        for m, old in zip(["completed", "coverage", "rating", "turns", "dialog_chars"], vals[1:]):
            cmp(f"within {old_name} {m}", p[m]["diff"], old, 0.0005 if m != "dialog_chars" else 0.5)
    cmp("withheld identifier items (scratch substring rule)", it["identifier_items_scratch_substring_rule"],
        SCRATCH["withheld_identifier_substring_rule"][0], 0)
    numbers["scratch_comparison"] = cmp_lines
    (OUT / "scratch_comparison.txt").write_text("\n".join(cmp_lines) + "\n", encoding="utf-8")

    def r(x):
        if isinstance(x, dict):
            return {k: r(v) for k, v in x.items()}
        if isinstance(x, list):
            return [r(v) for v in x]
        if isinstance(x, float):
            return round(x, 4)
        return x
    (OUT / "numbers.json").write_text(json.dumps(r(numbers), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------- text tables
    L = []
    hdr = (f"{'group':26s} {'n':>4s} {'atk':>5s} {'hit5':>5s} {'comp':>5s} {'req%':>5s} {'reask':>5s} {'turns':>5s} "
           f"{'chars':>6s} {'done':>6s} {'cov':>6s} {'rat':>5s} {'ratC':>5s} {'1st3p':>5s} {'p<=rq':>5s}")

    def line(g, s):
        if s["n"] == 0:
            return f"{g:26s} {0:4d}"
        return (f"{g:26s} {s['n']:4d} {s['svc_attack_turns']:5.2f} {100 * s['hit_budget']:4.0f}% "
                f"{s['svc_completion_turns']:5.2f} {100 * s['asked']:4.0f}% {s['reasks']:5.2f} {s['turns']:5.1f} "
                f"{s['dialog_chars'] / 1000:5.1f}k {s['completed']:6.3f} {s['coverage']:6.3f} {s['rating']:5.2f} "
                f"{s['rating_completed_only'] if s['rating_completed_only'] is not None else float('nan'):5.2f} "
                f"{s['first_msg_3prices']:5.2f} {s['prices_before_request']:5.2f}")
    for scope, _ in scopes:
        L.append(f"\n== {scope}")
        L.append(hdr)
        for g, s in tab[scope].items():
            L.append(line(g, s))
    L.append("\n== withheld_kind counts (Luna | GLM): withheld refused/deferred/ignored/too_coarse")
    for c in [c for c, _ in CONDITIONS] + ["feedback3", "rewrite3", "all8"]:
        a, b = sub["Luna"][c], sub["GLM"][c]
        L.append(f"{c:32s} Luna {a['withheld']:3d}: {a['refused']:3d} {a['deferred']:3d} {a['ignored']:3d} "
                 f"{a['too_coarse']:3d} | GLM {b['withheld']:3d}: {b['refused']:3d} {b['deferred']:3d} "
                 f"{b['ignored']:3d} {b['too_coarse']:3d} (n={b['n']})")
    L.append("\n== within-case paired differences (mean of per-case differences; case bootstrap 95% CI)")
    for name, p in pw.items():
        if p["n_cases"] == 0:
            continue
        parts = [f"{m} {p[m]['diff']:+.3f} [{p[m]['ci95'][0]:+.3f},{p[m]['ci95'][1]:+.3f}]"
                 for m in ("completed", "coverage", "rating", "turns", "reasks")]
        L.append(f"{name:22s} cases={p['n_cases']:3d} (eps {p['n_episodes_a']}/{p['n_episodes_b']}) | " + " | ".join(parts)
                 + f" | chars {p['dialog_chars']['diff']:+.0f} [{p['dialog_chars']['ci95'][0]:+.0f},{p['dialog_chars']['ci95'][1]:+.0f}]")
    L.append("\n== pooled W-A difference, case bootstrap (paper Sec. IV-D estimator)")
    for name, p in numbers["pooled_case_bootstrap"].items():
        L.append(f"{name}: cases={p['n_cases']} nW={p['n_a']} nA={p['n_b']} | " + " | ".join(
            f"{m} W {p[m]['mean_a']:.3f} A {p[m]['mean_b']:.3f} diff {p[m]['diff']:+.3f} "
            f"[{p[m]['ci95'][0]:+.3f},{p[m]['ci95'][1]:+.3f}]" for m in ("completed", "coverage", "rating")))
    L.append("\n== withheld items by type")
    L.append(json.dumps({k: v for k, v in it.items() if k != "by_item"}, ensure_ascii=False))
    L.append("top items: " + json.dumps(dict(list(it["by_item"].items())[:15])))
    L.append("\n== agreement with scratch audit")
    L += cmp_lines
    (OUT / "tables.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
