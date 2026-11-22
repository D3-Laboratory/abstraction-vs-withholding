#!/usr/bin/env python3
"""Replay one frozen v20 Gate condition with an alternative Gate model.

The source Main candidates, External-visible history, task and CI prompt remain
fixed.  Only the Gate provider/model changes.  This runner is resumable and
accepts multiple source roots so the 240 + 259 formal segments can be treated
as one 499-case experiment.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from run_ci_gate_pilot import (
    ChatClient,
    atomic_write_json,
    configure_ollama_request_controls,
    file_sha256,
    load_case_inputs,
    read_json,
    run_modify_gate,
)


def safe_model_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


def load_rows(
    source_roots: list[Path], config: dict[str, Any], condition: str
) -> tuple[list[dict[str, Any]], int]:
    converse = Path(config["benchmark"]["root"])
    episodes: dict[str, tuple[Path, dict[str, Any]]] = {}
    for root in source_roots:
        for path in sorted((root / "episodes").glob(f"*/{condition}.json")):
            episode = read_json(path)
            case_id = episode["case_id"]
            if case_id in episodes:
                raise ValueError(
                    f"Duplicate {condition} episode for {case_id}: "
                    f"{episodes[case_id][0]} and {path}"
                )
            episodes[case_id] = (path, episode)

    rows: list[dict[str, Any]] = []
    for case_id in sorted(episodes):
        path, episode = episodes[case_id]
        inputs = load_case_inputs(converse, episode["case"])
        for release_index, release in enumerate(episode.get("release_records", [])):
            candidate = (release.get("candidate") or "").strip()
            if not candidate:
                continue
            turn = int(release.get("turn") or 0)
            history = [
                item
                for item in episode.get("transcript", [])
                if int(item.get("turn") or 0) < turn
            ]
            rows.append(
                {
                    "case_id": case_id,
                    "episode": episode,
                    "source_path": str(path),
                    "release_index": release_index,
                    "release": release,
                    "inputs": inputs,
                    "history": history,
                }
            )
    return rows, len(episodes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider", choices=("ollama_cloud", "openrouter"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--condition", default="ci_gate_modify")
    parser.add_argument("--expected-cases", type=int, default=499)
    parser.add_argument("--sample-size", type=int)
    parser.add_argument("--sample-cases", type=int)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--failure-retries", type=int, default=3)
    parser.add_argument("--ollama-key-name", default="key2")
    parser.add_argument(
        "--shard",
        help="K/N: process only rows with index %% N == K, so several workers "
        "on different credentials can split one replay without overlapping",
    )
    parser.add_argument("--prompt", type=Path, help="Gate prompt to use instead of the config's")
    parser.add_argument(
        "--case-substring",
        help="replay only cases whose id contains this text, e.g. related_and_useful",
    )
    parser.add_argument("--reasoning-effort", default="none", help='"none" disables thinking')
    parser.add_argument("--max-tokens", type=int, default=7000)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.failure_retries < 0:
        raise SystemExit("--failure-retries must be non-negative")

    config = read_json(args.config)
    config["models"]["gate"] = {
        "provider": args.provider,
        "model": args.model,
        "temperature": 0.0,
        "reasoning_effort": args.reasoning_effort,
        "max_tokens": args.max_tokens,
    }
    if args.provider == "openrouter":
        # OpenRouter makes DeepSeek V4 Flash reason by default; "none" must turn it off
        # explicitly to match the original think=false runs. Pin fp8 endpoints so the
        # serving precision does not vary between requests.
        config["models"]["gate"]["openrouter_disable_reasoning"] = args.reasoning_effort == "none"
        config["models"]["gate"]["openrouter_provider"] = {
            "quantizations": ["fp8"],
            "require_parameters": True,
        }
    config["models"]["max_concurrent_requests"] = args.workers
    config["models"]["request_timeout_seconds"] = config["runtime"][
        "request_timeout_seconds"
    ]
    credentials = dict(config["credentials"])
    credentials.pop("ollama_key_pool", None)
    credentials["ollama_key_name"] = args.ollama_key_name
    credentials.setdefault("openrouter_env_file", ".env")
    credentials.setdefault("openrouter_key_name", "openrouter_key")
    config["credentials"] = credentials
    configure_ollama_request_controls(config["models"], credentials)

    rows, case_count = load_rows(args.source_root, config, args.condition)
    if args.case_substring:
        rows = [row for row in rows if args.case_substring in row["case_id"]]
    if args.sample_size is not None and args.sample_cases is not None:
        raise SystemExit("Use only one of --sample-size and --sample-cases")
    if args.sample_cases is not None:
        if args.sample_cases < 1:
            raise SystemExit("--sample-cases must be at least 1")
        case_ids = sorted({row["case_id"] for row in rows})
        rng = random.Random(args.seed)
        rng.shuffle(case_ids)
        selected = set(case_ids[: args.sample_cases])
        rows = [row for row in rows if row["case_id"] in selected]
    elif args.sample_size is not None:
        if args.sample_size < 1:
            raise SystemExit("--sample-size must be at least 1")
        rng = random.Random(args.seed)
        rng.shuffle(rows)
        rows = rows[: args.sample_size]
    elif not args.case_substring and case_count != args.expected_cases:
        raise SystemExit(
            f"Expected {args.expected_cases} unique cases, found {case_count}; refusing partial run"
        )

    prompt_key = "ci_gate_modify" if args.condition != "generic_gate_modify" else args.condition
    prompt_path = args.prompt or Path(config["prompts"][prompt_key])
    schema_path = Path(config["schemas"][prompt_key])
    selected_case_count = len({row["case_id"] for row in rows})
    manifest = {
        "schema_version": "ci-gate-model-replay-v20-v2",
        "source_roots": [str(path) for path in args.source_root],
        "source_config": str(args.config),
        "provider": args.provider,
        "model": args.model,
        "condition": args.condition,
        "source_cases": case_count,
        "selected_cases": selected_case_count,
        "selected_releases": len(rows),
        "sample_size": args.sample_size,
        "sample_cases": args.sample_cases,
        "seed": args.seed,
        "case_substring": args.case_substring,
        "reasoning_effort": args.reasoning_effort,
        "ollama_key_name": args.ollama_key_name if args.provider == "ollama_cloud" else None,
        "prompt_sha256": file_sha256(prompt_path),
        "schema_sha256": file_sha256(schema_path),
        "runner_sha256": file_sha256(Path(__file__)),
    }
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "replay-manifest.json"
    if manifest_path.exists() and not args.overwrite:
        previous = read_json(manifest_path)
        for key in ("provider", "model", "condition", "prompt_sha256", "schema_sha256",
                    "case_substring", "reasoning_effort"):
            if previous.get(key) != manifest.get(key):
                raise SystemExit(
                    f"Existing replay manifest disagrees on {key}; use a new output root"
                )
    atomic_write_json(manifest_path, manifest)
    if args.shard:
        shard_k, shard_n = (int(part) for part in args.shard.split("/"))
        if not 0 <= shard_k < shard_n:
            raise SystemExit("--shard must be K/N with 0 <= K < N")
        rows = [row for index, row in enumerate(rows) if index % shard_n == shard_k]
        print(f"shard {args.shard}: {len(rows)} releases", flush=True)
    prompt = prompt_path.read_text(encoding="utf-8")

    def record_path(row: dict[str, Any]) -> Path:
        return output / "records" / row["case_id"] / f"{row['release_index']:03d}.json"

    pending: list[tuple[int, dict[str, Any]]] = []
    skipped = 0
    for position, row in enumerate(rows, 1):
        path = record_path(row)
        if path.exists() and not args.overwrite:
            existing = read_json(path)
            if existing.get("status") == "ok":
                skipped += 1
                continue
        pending.append((position, row))
    print(
        json.dumps(
            {
                "model": args.model,
                "cases": case_count,
                "releases": len(rows),
                "already_complete": skipped,
                "pending": len(pending),
                "workers": args.workers,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    def run_one(position: int, row: dict[str, Any]) -> tuple[bool, str]:
        last_error = ""
        usage: list[dict[str, Any]] = []
        for attempt in range(args.failure_retries + 1):
            client = ChatClient(config["models"], credentials)
            try:
                result = run_modify_gate(
                    client,
                    args.condition,
                    prompt,
                    schema_path,
                    row["release"]["candidate"],
                    {
                        "external_role": row["inputs"]["external_role"],
                        "user_task": row["inputs"]["user_task"],
                        "released_history": row["history"],
                    },
                    max_contract_retries=int(
                        config["runtime"].get("modify_gate_contract_retries", 2)
                    ),
                )
                usage.extend(client.usage)
                record = {
                    "status": "ok",
                    "case_id": row["case_id"],
                    "condition": args.condition,
                    "turn": row["release"].get("turn"),
                    "release_index": row["release_index"],
                    "candidate": row["release"]["candidate"],
                    "source_released_message": row["release"].get("released_message"),
                    "source_path": row["source_path"],
                    "replay": result,
                    "api_usage": usage,
                    "attempts": attempt + 1,
                    "manifest": manifest,
                }
                atomic_write_json(record_path(row), record)
                return True, (
                    f"[{position}/{len(rows)}] {row['case_id']} "
                    f"turn={row['release'].get('turn')} {result['action']}"
                )
            except Exception as exc:  # preserve the failed unit for resumable reruns
                usage.extend(client.usage)
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < args.failure_retries:
                    time.sleep(min(2**attempt, 4))
        record = {
            "status": "error",
            "case_id": row["case_id"],
            "condition": args.condition,
            "turn": row["release"].get("turn"),
            "release_index": row["release_index"],
            "candidate": row["release"]["candidate"],
            "source_released_message": row["release"].get("released_message"),
            "source_path": row["source_path"],
            "error": last_error,
            "api_usage": usage,
            "attempts": args.failure_retries + 1,
            "manifest": manifest,
        }
        atomic_write_json(record_path(row), record)
        return False, f"FAILED [{position}/{len(rows)}] {row['case_id']}: {last_error}"

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(pending) or 1)) as pool:
        futures = {pool.submit(run_one, position, row): row for position, row in pending}
        for future in as_completed(futures):
            ok, message = future.result()
            print(message, flush=True)
            if not ok:
                failures.append(message)
    if failures:
        raise SystemExit(f"{len(failures)} replay records failed; rerun the same command to resume")

    print(
        json.dumps(
            {"status": "complete", "model": args.model, "records": len(rows)},
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
