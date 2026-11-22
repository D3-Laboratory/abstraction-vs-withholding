#!/usr/bin/env python3
"""Share of flagged items the redactor marks for removal vs generalization (paper Section IV-E).

    python3 -I experiments/scripts/redactor_action_shares.py

No LLM/API calls. Reads only existing files:
  results/target-disclosure-outcome-v23-luna/judgments/*/*.json   the 182 related-and-useful cases x 8
                                                                    configurations and their source episodes
  each source episode's release_records[*].parsed_gate_output.unnecessary_information (the redactor's parsed
  output; release_records[*].unnecessary_information when the parsed output is absent)
Writes results/redactor-action-shares/{numbers.json, summary.txt}.

Which configurations have per-item actions. The v22 feedback redactor (gate-feedback-v22.schema.json) returns each
flagged item as {"unit": ..., "fix": "remove" | "generalize"}; this covers contextual guidance
(ci_feedback_bare_v22), generic feedback (generic_feedback_v22) and contextual feedback (ci_feedback_v22). In
contextual guidance the redactor still flags items with an action, but the assistant receives only general advice,
not the list. The rewrite redactors of the main runs (generic_gate_modify, ci_gate_modify,
privacy_prompt_ci_gate_modify; ci-gate-modify-v20.schema.json) return the flagged items as plain strings without
an action, so they have no remove/generalize share. Configurations without a redactor have no records with items.

Counting. Every flagged item in every redactor call (all turns, PASS_THROUGH calls contribute no items) of the
182 related-and-useful conversations of a configuration; share = items with fix == "remove" / all items with a
fix. Also reported per conversation (mean of per-conversation shares over conversations with >= 1 item) as a
check that the pooled share is not driven by a few long conversations.
"""
from __future__ import annotations

import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "experiments/results"
OUT = RES / "redactor-action-shares"
CONDITIONS = ["raw_prompt", "privacy_prompt", "ci_feedback_bare_v22", "generic_feedback_v22", "ci_feedback_v22",
              "generic_gate_modify", "ci_gate_modify", "privacy_prompt_ci_gate_modify"]
LABEL = {"ci_feedback_bare_v22": "Contextual guidance", "generic_feedback_v22": "Generic feedback",
         "ci_feedback_v22": "Contextual feedback", "generic_gate_modify": "Generic rewrite",
         "ci_gate_modify": "Contextual rewrite", "privacy_prompt_ci_gate_modify": "Privacy + contextual rew.",
         "raw_prompt": "No defense", "privacy_prompt": "Privacy prompt"}


def main() -> None:
    items = defaultdict(Counter)          # condition -> fix -> count
    untyped = Counter()                   # condition -> items without an action (plain strings)
    per_conv = defaultdict(list)          # condition -> per-conversation remove share
    convs, calls = Counter(), Counter()
    for f in sorted(glob.glob(str(RES / "target-disclosure-outcome-v23-luna/judgments/*/*.json"))):
        j = json.loads(Path(f).read_text(encoding="utf-8"))
        cond = j["condition"]
        e = json.loads((ROOT / j["source_episode"]).read_text(encoding="utf-8"))
        convs[cond] += 1
        c = Counter()
        for r in e.get("release_records") or []:
            parsed = r.get("parsed_gate_output") if isinstance(r.get("parsed_gate_output"), dict) else {}
            ui = parsed.get("unnecessary_information") or r.get("unnecessary_information") or []
            if ui:
                calls[cond] += 1
            for u in ui:
                if isinstance(u, dict) and u.get("fix") in ("remove", "generalize"):
                    c[u["fix"]] += 1
                else:
                    untyped[cond] += 1
        items[cond] += c
        if sum(c.values()):
            per_conv[cond].append(c["remove"] / sum(c.values()))
    res = {"source": "release_records[*].parsed_gate_output.unnecessary_information[*].fix in the main-run episodes of the 182 "
                     "related-and-useful cases (cases as in target-disclosure-outcome-v23-luna)",
           "by_configuration": {}}
    lines = ["Redactor per-item actions in the 182 related-and-useful cases (main runs)",
             f"{'configuration':28s} {'conv':>5s} {'calls w/ items':>14s} {'remove':>7s} {'general.':>8s} "
             f"{'no action':>9s} {'remove %':>8s} {'mean per conv %':>15s}"]
    for cond in CONDITIONS:
        c = items[cond]
        n = c["remove"] + c["generalize"]
        share = 100 * c["remove"] / n if n else None
        pc = 100 * sum(per_conv[cond]) / len(per_conv[cond]) if per_conv[cond] else None
        res["by_configuration"][cond] = {
            "label": LABEL[cond], "conversations": convs[cond], "redactor_calls_with_items": calls[cond],
            "remove": c["remove"], "generalize": c["generalize"], "items_without_action": untyped[cond],
            "remove_share_pct": share, "generalize_share_pct": (100 - share) if share is not None else None,
            "mean_per_conversation_remove_share_pct": pc, "conversations_with_items": len(per_conv[cond])}
        lines.append(f"{LABEL[cond]:28s} {convs[cond]:5d} {calls[cond]:14d} {c['remove']:7d} {c['generalize']:8d} "
                     f"{untyped[cond]:9d} {('%.1f' % share) if share is not None else '--':>8s} "
                     f"{('%.1f' % pc) if pc is not None else '--':>15s}")
    fb = ["generic_feedback_v22", "ci_feedback_v22"]
    allfix = [c for c in CONDITIONS if res["by_configuration"][c]["remove_share_pct"] is not None]
    rng = lambda cs: [min(res["by_configuration"][c]["remove_share_pct"] for c in cs),
                      max(res["by_configuration"][c]["remove_share_pct"] for c in cs)]
    res["range_feedback_configurations_with_item_list"] = {"configurations": fb, "remove_share_pct": rng(fb)}
    res["range_all_configurations_with_actions"] = {"configurations": allfix, "remove_share_pct": rng(allfix)}
    a, b = rng(fb), rng(allfix)
    lines += ["",
              f"generic + contextual feedback (the redactor returns the flagged items to the assistant): "
              f"{a[0]:.1f}-{a[1]:.1f}% remove",
              f"all configurations whose redactor logs an action (adds contextual guidance): {b[0]:.1f}-{b[1]:.1f}% remove",
              "rewrite redactors (v20 schema) log flagged items without an action; no share."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    (OUT / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
