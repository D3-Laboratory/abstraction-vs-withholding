#!/usr/bin/env python3
"""Sample a blind human-annotation set for the v23 three-way target-disclosure judge.

Draws (case, condition) items from the Luna judgments, stratified over Luna outcome
(LEAKED / CONVEYED / WITHHELD) x condition family (no_gate / feedback / rewrite), with at
most one item per case_id when possible. Where GLM judgments exist, items on which Luna and
GLM disagree are oversampled toward --disagreement-share. Deterministic for a fixed seed and
fixed judgment files; re-run after the GLM judge finishes to refresh the disagreement pool.

Writes (never touches results/):
  <out>/items.json  annotator view, no judge labels and no condition
  <out>/key.json    item_id -> case, condition, Luna / GLM / old-judge labels
Run from the repo root with PYTHONPATH=experiments/scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from judge_ci_gate_results_v3 import build_evidence, load_privacy_ground_truth
from run_ci_gate_pilot import load_case_inputs, read_json

FAMILY = {
    "raw_prompt": "no_gate",
    "privacy_prompt": "no_gate",
    "ci_feedback_bare_v22": "feedback",
    "generic_feedback_v22": "feedback",
    "ci_feedback_v22": "feedback",
    "generic_gate_modify": "rewrite",
    "ci_gate_modify": "rewrite",
    "privacy_prompt_ci_gate_modify": "rewrite",
}
OUTCOMES = ["LEAKED", "CONVEYED", "WITHHELD"]
# Cases quoted as worked examples in the annotation README; never sampled for annotation.
GUIDELINE_EXAMPLE_CASES = {
    "insurance.persona4.related_and_useful.location.03",
    "insurance.persona1.related_and_useful.government_id_information.04",
    "real_estate.persona3.related_and_useful.children's_activities.10",
    "insurance.persona1.related_and_useful.professional_status.05",
    "real_estate.persona3.related_and_useful.education_savings_status.19",
    "insurance.persona3.related_and_useful.location.03",
    "insurance.persona1.related_and_useful.work_project_responsibility.18",
}
FAMILIES = ["no_gate", "feedback", "rewrite"]


def old_judge_outcome(parsed: dict) -> str:
    """Map the v5 ConVerse abstraction judge onto the three-way scale.

    The old judge cannot separate refusal from correct abstraction: both are "appropriate".
    We map appropriate -> CONVEYED, too_vague -> WITHHELD, raw/too_detailed -> LEAKED; the
    analysis script also reports the binary leaked-vs-not view, which is the old judge's
    actual resolution.
    """
    if parsed.get("shared_raw_data") == "yes" or parsed.get("abstraction_level") == "too_detailed":
        return "LEAKED"
    if parsed.get("abstraction_level") == "too_vague":
        return "WITHHELD"
    return "CONVEYED"


def load_judgments(root: Path) -> dict[tuple[str, str], dict]:
    found = {}
    for path in sorted(root.glob("judgments/*/*.json")):
        try:
            record = read_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # a judgment still being written by a running judge
        if path.stem in FAMILY:
            found[(record["case_id"], record["condition"])] = record
    return found


def label(record: dict | None) -> dict | None:
    if record is None:
        return None
    j = record["judgment"]
    return {
        "outcome": j["outcome"],
        "requested_by_external": j.get("requested_by_external"),
        "withheld_kind": j.get("withheld_kind"),
        "model": record.get("manifest", {}).get("judge_model"),
    }


def split_targets(total: int, parts: int) -> list[int]:
    base = [total // parts] * parts
    for i in range(total - sum(base)):
        base[-1 - i] += 1  # extra items go to the gated families
    return base


def select(pool, args, rng):
    """pool: list of dicts with key, case_id, outcome, family, disagree (True/False/None)."""
    per_outcome = split_targets(args.n, 3)
    targets = {}
    for o, n_o in zip(OUTCOMES, per_outcome):
        for f, n in zip(FAMILIES, split_targets(n_o, 3)):
            targets[(o, f)] = n

    cells = defaultdict(list)
    for item in pool:
        cells[(item["outcome"], item["family"])].append(item)
    for items in cells.values():
        items.sort(key=lambda x: x["key"])
        rng.shuffle(items)

    # Shift targets of cells without enough distinct cases to sibling families of the same outcome.
    for o in OUTCOMES:
        for f in FAMILIES:
            cap = len({x["case_id"] for x in cells[(o, f)]})
            if targets[(o, f)] > cap:
                extra = targets[(o, f)] - cap
                targets[(o, f)] = cap
                for g in sorted(FAMILIES, key=lambda g: -len(cells[(o, g)])):
                    if g != f and extra:
                        targets[(o, g)] += extra
                        extra = 0

    # Disagreement quota per cell: share of target, capped by availability; deficit to cells with surplus.
    want = round(args.disagreement_share * args.n)
    avail = {c: sum(1 for x in cells[c] if x["disagree"]) for c in targets}
    quota = {c: min(avail[c], math.ceil(args.disagreement_share * targets[c])) for c in targets}
    deficit = want - sum(quota.values())
    while deficit > 0:
        open_cells = [c for c in targets if quota[c] < min(avail[c], targets[c])]
        if not open_cells:
            break
        for c in sorted(open_cells, key=lambda c: (-(avail[c] - quota[c]), c)):
            if deficit <= 0:
                break
            quota[c] += 1
            deficit -= 1

    # Greedy assignment, one item per case_id. Scarce cells choose first, and every cell prefers
    # cases that are least needed elsewhere (few scarce-cell or disagreement items), so the
    # unique-case constraint costs as little stratification and disagreement as possible.
    distinct = {c: len({x["case_id"] for x in cells[c]}) for c in targets}
    scarcity = {c: targets[c] / max(distinct[c], 1) for c in targets}
    need = defaultdict(float)
    for c in targets:
        for x in cells[c]:
            need[x["case_id"]] += scarcity[c] + (scarcity[c] if x["disagree"] else 0.0)
    order = sorted(targets, key=lambda c: (-scarcity[c], c))
    used: set[str] = set()
    picked = {c: [] for c in targets}

    def take(c, group, limit):
        for x in sorted(group, key=lambda x: need[x["case_id"]]):  # stable: ties keep shuffled order
            if len(picked[c]) >= limit:
                return
            if x["case_id"] not in used and x not in picked[c]:
                picked[c].append(x)
                used.add(x["case_id"])

    for c in order:  # phase 1: disagreement quota
        take(c, [x for x in cells[c] if x["disagree"]], quota[c])
    for c in order:  # phase 2: fill with the rest, then any remaining disagreements
        take(c, [x for x in cells[c] if not x["disagree"]], targets[c])
        take(c, [x for x in cells[c] if x["disagree"]], targets[c])
        if len(picked[c]) < targets[c] and args.allow_case_reuse:
            for x in cells[c]:
                if len(picked[c]) < targets[c] and x not in picked[c]:
                    picked[c].append(x)
    chosen = [x for c in order for x in picked[c]]
    return chosen, targets, quota


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--luna-root", type=Path, default=Path("experiments/results/target-disclosure-outcome-v23-luna"))
    ap.add_argument("--glm-root", type=Path, default=Path("experiments/results/target-disclosure-outcome-v23"))
    ap.add_argument("--converse-root", type=Path, default=Path("experiments/third_party/converse"))
    ap.add_argument("--out", type=Path, default=Path("experiments/annotation/over-redaction-v23"))
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=2310)
    ap.add_argument("--disagreement-share", type=float, default=0.40)
    ap.add_argument("--allow-case-reuse", action="store_true",
                    help="fill short cells with a second item from an already-used case")
    args = ap.parse_args()

    luna = load_judgments(args.luna_root)
    glm = load_judgments(args.glm_root)
    pool = []
    for key, rec in sorted(luna.items()):
        if key[0] in GUIDELINE_EXAMPLE_CASES:
            continue
        g = glm.get(key)
        pool.append({
            "key": key, "case_id": key[0], "condition": key[1], "family": FAMILY[key[1]],
            "outcome": rec["judgment"]["outcome"],
            "disagree": None if g is None else g["judgment"]["outcome"] != rec["judgment"]["outcome"],
        })

    rng = random.Random(args.seed)
    chosen, targets, quota = select(pool, args, rng)
    chosen.sort(key=lambda x: x["key"])
    rng.shuffle(chosen)  # presentation order is random, not grouped by stratum

    items, key_rows = [], []
    for i, x in enumerate(chosen, 1):
        item_id = f"OR{i:03d}"
        luna_rec = luna[x["key"]]
        episode = read_json(Path(luna_rec["source_episode"]))
        case = episode["case"]
        gt = load_privacy_ground_truth(args.converse_root, case)
        inputs = load_case_inputs(args.converse_root, case)
        ev = build_evidence(episode, gt, inputs["user_task"])
        items.append({
            "item_id": item_id,
            "use_case": case["use_case"],
            "external_agent_role": ev["external_agent_role"],
            "user_task": ev["user_task"],
            "data_item": ev["data_item"],
            "raw_data": ev["raw_data"],
            "acceptable_abstraction": ev["acceptable_abstraction"],
            "abstraction_examples": ev["abstraction_examples"],
            "conversation": ev["conversation"],
        })
        old = episode["privacy_judge_v5"]["target"]["parsed"]
        key_rows.append({
            "item_id": item_id,
            "case_id": x["case_id"],
            "condition": x["condition"],
            "family": x["family"],
            "stratum": f"{x['outcome']}/{x['family']}",
            "source_episode": luna_rec["source_episode"],
            "luna": label(luna_rec),
            "glm": label(glm.get(x["key"])),
            "luna_glm_disagree": x["disagree"],
            "old_judge": {
                "model": episode["privacy_judge_v5"].get("model"),
                "shared_raw_data": old.get("shared_raw_data"),
                "abstraction_level": old.get("abstraction_level"),
                "appropriateness_score": old.get("appropriateness_score"),
                "outcome_mapped": old_judge_outcome(old),
            },
        })

    items_blob = json.dumps(items, ensure_ascii=False, sort_keys=True).encode()
    sample_id = "over-redaction-v23-" + hashlib.sha256(items_blob).hexdigest()[:10]
    comp = Counter((r["luna"]["outcome"], r["family"]) for r in key_rows)
    meta = {
        "sample_id": sample_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": args.seed, "n_items": len(items),
        "n_distinct_cases": len({r["case_id"] for r in key_rows}),
        "glm_judgments_available": len(glm), "luna_judgments_available": len(luna),
        "glm_complete": len(glm) >= len(luna),
        "excluded_guideline_example_cases": sorted(GUIDELINE_EXAMPLE_CASES),
        "disagreement_target_share": args.disagreement_share,
        "n_luna_glm_disagree": sum(1 for r in key_rows if r["luna_glm_disagree"]),
        "n_without_glm": sum(1 for r in key_rows if r["luna_glm_disagree"] is None),
        "cell_targets": {f"{o}/{f}": targets[(o, f)] for o, f in targets},
        "cell_disagreement_quota": {f"{o}/{f}": quota[(o, f)] for o, f in quota},
        "composition": {f"{o}/{f}": comp[(o, f)] for o in OUTCOMES for f in FAMILIES},
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "items.json").write_text(json.dumps(
        {"sample_id": sample_id, "n_items": len(items), "items": items},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "key.json").write_text(json.dumps(
        {"meta": meta, "items": key_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in meta.items() if k not in ("cell_targets", "cell_disagreement_quota", "composition")}, indent=2))
    print(f"\n{'Luna outcome':<12}" + "".join(f"{f:>10}" for f in FAMILIES) + f"{'total':>8}{'L!=G':>7}")
    for o in OUTCOMES:
        dis = sum(1 for r in key_rows if r["luna"]["outcome"] == o and r["luna_glm_disagree"])
        print(f"{o:<12}" + "".join(f"{comp[(o, f)]:>10}" for f in FAMILIES)
              + f"{sum(comp[(o, f)] for f in FAMILIES):>8}{dis:>7}")


if __name__ == "__main__":
    main()
