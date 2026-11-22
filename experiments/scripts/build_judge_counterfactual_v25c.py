#!/usr/bin/env python3
"""Build the v3 counterfactual items from hand-written edits (counterfactual_edits_v3.json).

Each kept item has three versions of the first leaking assistant message: the original (leaked), an edit that
shares only the allowed form (allowed_form), and an edit that drops the item without a refusal (ignored).
The edits were written and reviewed by hand, item by item; no model rewrote any text.

    python3 experiments/scripts/build_judge_counterfactual_v25c.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/judge-counterfactual-v25"
EDITS = DATA / "counterfactual_edits_v3.json"
OUT = DATA / "items_v3.jsonl"
KEEP = ("case_id", "domain", "data_item", "raw_data", "acceptable_abstraction", "attack_action", "user_task",
        "source_episode", "source_condition", "edited_turn", "conversation_prefix")


def apply(msg: str, edits: list[dict]) -> str:
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


def main() -> None:
    edits = json.loads(EDITS.read_text(encoding="utf-8"))
    v1 = {json.loads(l)["case_id"]: json.loads(l) for l in (DATA / "items.jsonl").read_text(encoding="utf-8").splitlines()}
    rows, excluded = [], []
    for cid in sorted(edits):
        d = edits[cid]
        if "exclude" in d:
            excluded.append({"case_id": cid, "reason": d["exclude"]})
            continue
        src = v1[cid]
        leaked = src["versions"]["leaked"]
        row = {k: src[k] for k in KEEP if k in src}
        row["versions"] = {"leaked": leaked, "allowed_form": apply(leaked, d["allowed"]),
                           "ignored": apply(leaked, d["ignored"])}
        row["edits"] = {"allowed_form": d["allowed"], "ignored": d["ignored"]}
        if d.get("note"):
            row["edit_note"] = d["note"]
        row["edit_method"] = "hand-written by Claude Opus 5.5, reviewed item by item (2026-10-16)"
        rows.append(row)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (DATA / "excluded_v3.json").write_text(json.dumps(excluded, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"kept {len(rows)}, excluded {len(excluded)} -> {OUT.name}, excluded_v3.json")


if __name__ == "__main__":
    main()
