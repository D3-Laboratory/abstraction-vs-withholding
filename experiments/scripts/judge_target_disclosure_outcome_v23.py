#!/usr/bin/env python3
"""Three-way target-disclosure judge (LEAKED / CONVEYED / WITHHELD) for related-and-useful cases.

The ConVerse abstraction judge scores refusal and correct abstraction alike as "attack failed".
This judge separates them. It reads existing episodes and writes one judgment file per
(case, condition) under its own output root; source episodes are never modified.
"""
from __future__ import annotations
import argparse, json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from judge_ci_gate_results_v3 import build_evidence, load_privacy_ground_truth
from judge_ci_gate_results_v5 import call
from judge_gate_model_replay_v20 import rebuild_episode
from run_ci_gate_pilot import ChatClient, configure_ollama_request_controls, file_sha256, load_case_inputs, read_json

# Paper condition label -> episode condition name. Later roots win, as in analyze_v22_results.
CONDITIONS = {
    "Raw": "raw_prompt",
    "Privacy prompt": "privacy_prompt",
    "CI-GF": "ci_feedback_bare_v22",
    "Generic-IF": "generic_feedback_v22",
    "CI-IF": "ci_feedback_v22",
    "Generic-RW": "generic_gate_modify",
    "CI-RW": "ci_gate_modify",
    "Privacy+CI-RW": "privacy_prompt_ci_gate_modify",
}
SOURCE_ROOTS = [
    "experiments/results/ci-gate-full-pilot-v20-240",
    "experiments/results/ci-gate-formal-v20-ex-259",
    "experiments/results/ci-gate-v22-backfill-72",
    "experiments/results/ci-gate-v22-feedback-571",
    "experiments/results/ci-gate-v22-bare-571",
]
PROMPT = Path("experiments/prompts/ci_gate/target_disclosure_outcome_v23.txt")
SCHEMA = Path("experiments/configs/target-disclosure-outcome-v23.schema.json")


def load_episodes(conditions: set[str]) -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for root in SOURCE_ROOTS:
        for path in sorted(Path(root).glob("episodes/*related_and_useful*/*.json")):
            if path.stem in conditions:
                found[(path.parent.name, path.stem)] = path
    return found


def load_replays(roots: list[Path]) -> dict[tuple[str, str], dict]:
    """Rebuild each replayed conversation; the condition label is the replay folder name.

    A case is skipped when any of its replay records failed (e.g. the Gate broke its output
    contract on every retry), since its conversation cannot be rebuilt; skipped cases are printed.
    """
    found: dict[tuple[str, str], dict] = {}
    for root in roots:
        manifest = read_json(root / "replay-manifest.json")
        grouped: dict[str, list[dict]] = {}
        for path in sorted((root / "records").glob("*/*.json")):
            record = read_json(path)
            grouped.setdefault(record["case_id"], []).append(record)
        for case_id, records in grouped.items():
            if any(r.get("status") != "ok" for r in records):
                print(f"SKIP {root.name} {case_id}: failed replay record", flush=True)
                continue
            found[(case_id, root.name)] = rebuild_episode(records, manifest)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=Path("experiments/configs/ci-gate-v22-feedback-571.json"))
    ap.add_argument("--output-root", type=Path, default=Path("experiments/results/target-disclosure-outcome-v23"))
    ap.add_argument("--conditions", nargs="*", default=list(CONDITIONS), help="paper condition labels")
    ap.add_argument("--source-root", action="append", default=[],
                    help="episode roots to read instead of the default v20/v22 roots")
    ap.add_argument("--replay-root", type=Path, action="append", default=[],
                    help="judge rebuilt replay conversations instead of source episodes")
    ap.add_argument("--sample", type=int, default=0, help="judge a random sample of this many episodes")
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    # glm-5.1, the v5 privacy judge, was retired from Ollama Cloud on 2026-09-25.
    ap.add_argument("--judge-provider", choices=["ollama_cloud", "openrouter"], default="ollama_cloud")
    ap.add_argument("--judge-model", default="glm-5.3-flash")
    # With thinking off, glm-5.3-flash writes its reasoning into the content field instead of JSON.
    ap.add_argument("--judge-reasoning", default="low", help='"none" disables thinking')
    ap.add_argument("--judge-max-tokens", type=int, default=12000)
    args = ap.parse_args()

    if args.source_root:
        SOURCE_ROOTS[:] = args.source_root
    episodes = load_replays(args.replay_root) if args.replay_root else load_episodes({CONDITIONS[c] for c in args.conditions})
    keys = sorted(episodes)
    if args.sample:
        keys = sorted(random.Random(args.seed).sample(keys, min(args.sample, len(keys))))
    out = lambda k: args.output_root / "judgments" / k[0] / f"{k[1]}.json"
    if not args.overwrite:
        keys = [k for k in keys if not out(k).exists()]
    if args.dry_run:
        print(json.dumps({"episodes_found": len(episodes), "jobs": len(keys)}, indent=2))
        return

    config = read_json(args.config)
    config["models"]["request_timeout_seconds"] = config["runtime"]["request_timeout_seconds"]
    configure_ollama_request_controls(config["models"])
    config["models"]["judge"] = {"provider": args.judge_provider, "model": args.judge_model,
                                 "temperature": 0.0, "reasoning_effort": args.judge_reasoning, "max_tokens": args.judge_max_tokens}
    if args.judge_provider == "openrouter":
        config["credentials"].update({"openrouter_env_file": ".env", "openrouter_key_name": "openrouter_key"})
    prompt, schema = PROMPT.read_text(encoding="utf-8"), read_json(SCHEMA)
    converse, retries = Path(config["benchmark"]["root"]), config["runtime"]["max_format_retries"]
    manifest = {
        "version": "target-disclosure-outcome-v23",
        "judge_model": config["models"]["judge"]["model"],
        "prompt_sha256": file_sha256(PROMPT),
        "schema_sha256": file_sha256(SCHEMA),
        "script_sha256": file_sha256(Path(__file__)),
        "evaluated_surface": "released assistant-to-external conversation only",
    }

    def one(pos: int, key: tuple[str, str]) -> str:
        ep = episodes[key] if isinstance(episodes[key], dict) else read_json(episodes[key])
        gt = load_privacy_ground_truth(converse, ep["case"])
        evidence = build_evidence(ep, gt, load_case_inputs(converse, ep["case"])["user_task"])
        evidence.pop("extraction_snippets", None)
        evidence["evaluation_scope"] = "named data item only; ignore other private information"
        client = ChatClient(config["models"], config["credentials"])
        raw, parsed = call(client, prompt, evidence, schema, retries)
        record = {
            "case_id": key[0], "condition": key[1],
            "source_episode": str(episodes[key]) if isinstance(episodes[key], Path) else ep["gate_model_replay"],
            "acceptable_abstraction": gt["acceptable_abstraction"],
            "judgment": parsed, "raw": raw, "api_usage": client.usage, "manifest": manifest,
        }
        path = out(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return f"[{pos}/{len(keys)}] {key[0]} {key[1]} -> {parsed['outcome']}"

    failures = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(keys) or 1)) as pool:
        futures = {pool.submit(one, i, k): k for i, k in enumerate(keys, 1)}
        for f in as_completed(futures):
            try:
                print(f.result(), flush=True)
            except Exception as exc:
                failures.append(f"FAILED {futures[f]}: {type(exc).__name__}: {exc}")
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
