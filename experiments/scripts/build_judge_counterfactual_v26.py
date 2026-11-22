#!/usr/bin/env python3
"""Build the v26 counterfactual items: two further withholding versions for the 86 v3 cases.

New versions of the first leaking assistant message (everything else identical to v3):
  explicit_refusal  the item's wording is replaced by an open refusal to share it
  coarser           the item's wording is replaced by a truthful form coarser than ConVerse's allowed form
The edits were written and checked by hand (Claude Opus 5.5), case by case, as exact string replacements in
experiments/datasets/judge-counterfactual-v26/counterfactual_edits_v26.json. No model rewrote any text, and this
script makes no API call. It applies the edits to the v3 leaked message, copies the three v3 versions unchanged,
and runs the deterministic checks below (the hand-check notes are stored next to them).

    python3 -I experiments/scripts/build_judge_counterfactual_v26.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V25 = ROOT / "experiments/datasets/judge-counterfactual-v25"
DATA = ROOT / "experiments/datasets/judge-counterfactual-v26"
EDITS = DATA / "counterfactual_edits_v26.json"
NEW_VERSIONS = ("explicit_refusal", "coarser")
REFUSAL = re.compile(r"\b(can't|cannot|can not|not able to|unable to|rather not|prefer not|won't|not something I can)\b", re.I)
STOP = set("""a an the and or of for with to in on at by from as is are was were be been has have had that this
these those their there they them her his its our your my which who whom what when where while about into over under
than then also more most some such only other into very just""".split())


def apply(msg: str, edits: list[dict]) -> str:
    # Same semantics as build_judge_counterfactual_v25c.apply.
    for e in edits:
        if "old" in e:
            if msg.count(e["old"]) != 1:
                raise ValueError(f"edit text not found exactly once: {e['old'][:80]!r}")
            msg = msg.replace(e["old"], e["new"])
        else:
            if msg.count(e["from"]) != 1:
                raise ValueError(f"range start not found exactly once: {e['from'][:80]!r}")
            a = msg.find(e["from"])
            b = msg.find(e["to"], a)
            if b < 0:
                raise ValueError(f"range end not found: {e['to'][:80]!r}")
            msg = msg[:a] + e["new"] + msg[b + len(e["to"]):]
    return msg


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z'\-]+", text.lower()) if len(w) > 3 and w not in STOP}


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*", text)}


def check(item: dict, version: str, text: str, edits: list[dict]) -> dict:
    hard, soft = [], []
    vs = item["versions"]
    new_text = " ".join(e["new"] for e in edits)
    af = item["acceptable_abstraction"]
    for raw in item["raw_data"]:
        if raw.lower() in text.lower():
            hard.append(f"raw string in message: {raw!r}")
    raw_nums = set().union(*(numbers(r) for r in item["raw_data"])) - numbers(af)
    if raw_nums & numbers(new_text):
        hard.append(f"raw number in replacement: {sorted(raw_nums & numbers(new_text))}")
    raw_words = set().union(*(words(r) for r in item["raw_data"])) - words(af) - words(item["data_item"])
    if raw_words & words(new_text):
        soft.append(f"raw word in replacement: {sorted(raw_words & words(new_text))}")
    if af.lower() in text.lower():
        hard.append("allowed form appears verbatim")
    if text in (vs["leaked"], vs["allowed_form"], vs["ignored"]):
        hard.append("identical to an existing version")
    has_refusal = bool(REFUSAL.search(new_text))
    if version == "explicit_refusal":
        if not has_refusal:
            hard.append("no refusal wording in replacement")
        shared = words(af) & words(new_text) - words(item["data_item"])
        if shared:
            soft.append(f"allowed-form word in refusal (review for hint): {sorted(shared)}")
    else:
        if has_refusal:
            hard.append("refusal wording in coarser replacement")
        shared = words(af) & words(new_text)
        if shared:
            soft.append(f"allowed-form word in coarser text (review: must be strictly less specific): {sorted(shared)}")
    return {"hard_fail": hard, "flags": soft, "len": len(text),
            "len_minus_allowed_form": len(text) - len(vs["allowed_form"]),
            "len_minus_ignored": len(text) - len(vs["ignored"])}


def main() -> None:
    edits = json.loads(EDITS.read_text(encoding="utf-8"))
    v3 = [json.loads(l) for l in (V25 / "items_v3.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if sorted(edits) != sorted(r["case_id"] for r in v3):
        raise SystemExit("edit file does not cover exactly the 86 v3 cases")
    rows, excluded, checks, fails = [], [], [], []
    per_version: dict[str, list[dict]] = {v: [] for v in NEW_VERSIONS}
    for item in v3:
        cid = item["case_id"]
        d = edits[cid]
        row = {k: v for k, v in item.items() if k not in ("edits", "edit_note", "edit_method")}
        row["versions"] = dict(item["versions"])
        row["edits_v3"] = item["edits"]
        if item.get("edit_note"):
            row["edit_note_v3"] = item["edit_note"]
        row["edits_v26"], row["check_v26"] = {}, {}
        for v in NEW_VERSIONS:
            spec = d[v]
            if isinstance(spec, dict) and "exclude" in spec:
                excluded.append({"case_id": cid, "version": v, "reason": spec["exclude"]})
                row["check_v26"][v] = {"status": "excluded", "reason": spec["exclude"]}
                continue
            text = apply(item["versions"]["leaked"], spec)
            c = check(item, v, text, spec)
            c["status"] = "fail" if c["hard_fail"] else ("flag" if c["flags"] else "ok")
            c["hand_check"] = d["check_notes"][v]
            row["versions"][v] = text
            row["edits_v26"][v] = spec
            row["check_v26"][v] = c
            checks.append({"case_id": cid, "version": v, **c})
            if c["hard_fail"]:
                fails.append((cid, v, c["hard_fail"]))
        row["edit_method_v26"] = ("explicit_refusal and coarser hand-written and hand-checked by Claude Opus 5.5, "
                                  "case by case (2026-11-15); other versions copied unchanged from v25 items_v3.jsonl")
        rows.append(row)
        for v in NEW_VERSIONS:
            if v in row["versions"]:
                per_version[v].append(row)
    if fails:
        for f in fails:
            print("FAIL", *f)
        raise SystemExit(f"{len(fails)} versions fail the hard checks; nothing written")
    dump = lambda rs: "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs)
    (DATA / "items_v26.jsonl").write_text(dump(rows), encoding="utf-8")
    for v in NEW_VERSIONS:
        (DATA / f"items_v26_{v}.jsonl").write_text(dump(per_version[v]), encoding="utf-8")
    (DATA / "excluded_v26.json").write_text(json.dumps(excluded, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "checks_v26.jsonl").write_text(dump(checks), encoding="utf-8")
    write_samples(rows)
    status = Counter((c["version"], c["status"]) for c in checks)
    lens = {v: [c for c in checks if c["version"] == v] for v in NEW_VERSIONS}
    stats = {"cases": len(rows), "valid": {v: len(per_version[v]) for v in NEW_VERSIONS},
             "excluded": Counter(e["version"] for e in excluded),
             "check_status": {f"{v}/{s}": n for (v, s), n in sorted(status.items())},
             "mean_len_minus_allowed_form": {v: round(sum(c["len_minus_allowed_form"] for c in cs) / len(cs), 1) for v, cs in lens.items()},
             "mean_len_minus_ignored": {v: round(sum(c["len_minus_ignored"] for c in cs) / len(cs), 1) for v, cs in lens.items()},
             "max_abs_len_minus_allowed_form": {v: max(abs(c["len_minus_allowed_form"]) for c in cs) for v, cs in lens.items()}}
    (DATA / "build_v26_stats.json").write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=1))


def changed(leaked: str, edits: list[dict]) -> str:
    return " … ".join(repr(e["new"]) if e["new"] else "(removed)" for e in edits)


def write_samples(rows: list[dict]) -> None:
    out = ["# Counterfactual items v26: explicit refusal and coarser form\n",
           "Only the replaced text is shown. Everything else in the message and the conversation before it is "
           "identical to the v3 leaked message. `hand check` is the note recorded when the edit was checked.\n"]
    for r in rows:
        out.append(f"\n## {r['case_id']}")
        out.append(f"- item: {r['data_item']} | raw: {'; '.join(r['raw_data'])} | allowed form: {r['acceptable_abstraction']}")
        out.append(f"- **allowed_form (v3)**: {changed(r['versions']['leaked'], r['edits_v3']['allowed_form'])}")
        out.append(f"- **ignored (v3)**: {changed(r['versions']['leaked'], r['edits_v3']['ignored'])}")
        for v in NEW_VERSIONS:
            c = r["check_v26"][v]
            if c["status"] == "excluded":
                out.append(f"- **{v}**: EXCLUDED — {c['reason']}")
                continue
            old = " … ".join(repr(e.get("old") or e["from"] + " … " + e["to"])[:160] for e in r["edits_v26"][v])
            out.append(f"- **{v}** (replaces {old}): {changed(r['versions']['leaked'], r['edits_v26'][v])}")
            out.append(f"  - checks: {c['status']}{'; ' + '; '.join(c['flags']) if c['flags'] else ''}; hand check: {c['hand_check']}")
    (DATA / "samples_v26.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
