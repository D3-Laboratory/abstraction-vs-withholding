#!/usr/bin/env python3
"""Backfill the original ConVerse UtilityJudge design with the configured judge LLM.

Each episode receives two calls: package coverage, then persona-rating mapping.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from ci_gate_runtime import GateDecisionError, extract_json_object
from run_ci_gate_pilot import (
    ChatClient,
    configure_ollama_request_controls,
    file_sha256,
    load_case_inputs,
    read_json,
)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".utility-judge.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def import_utility_prompts(converse_root: Path) -> tuple[Callable[..., str], Callable[..., str]]:
    sys.path.insert(0, str(converse_root.resolve()))
    from judge.utility_prompts import ratings_prompt, utility_questions_prompt  # type: ignore

    return utility_questions_prompt, ratings_prompt


def final_package(episode: dict[str, Any]) -> str:
    finals = [
        entry.get("message", "")
        for entry in episode.get("transcript", [])
        if entry.get("from") == "main" and entry.get("to") == "user"
    ]
    return finals[-1] if finals else ""


def ratings_path(converse_root: Path, episode: dict[str, Any]) -> Path:
    use_case = episode["case"]["use_case"]
    persona = episode["case"]["persona_id"]
    return (
        converse_root
        / "resources"
        / f"{use_case}_usecase"
        / "ratings"
        / f"ratings_persona{persona}.json"
    )


def validate_coverage(parsed: dict[str, Any]) -> None:
    value = parsed.get("UTILITY", {}).get("HOW_MANY_ITEMS_COVERED")
    if not isinstance(value, str) or not re.fullmatch(r"\s*\d+\s*/\s*\d+\s*", value):
        raise ValueError("UTILITY.HOW_MANY_ITEMS_COVERED must be number_included/number_total")
    included, total = (int(piece.strip()) for piece in value.split("/"))
    if total < 1 or included > total:
        raise ValueError("coverage fraction is invalid")


def validate_ratings(parsed: dict[str, Any]) -> None:
    ratings = parsed.get("RATINGS")
    if not isinstance(ratings, dict):
        raise ValueError("RATINGS must be an object")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in ratings.values()):
        raise ValueError("every mapped rating must be numeric")


def call_json(
    client: ChatClient,
    prompt: str,
    validator: Callable[[dict[str, Any]], None],
    retries: int,
) -> tuple[str, dict[str, Any]]:
    messages = [{"role": "user", "content": prompt}]
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        raw = client.call("judge", messages, json_mode=True)
        try:
            parsed = extract_json_object(raw)
            validator(parsed)
            return raw, parsed
        except (GateDecisionError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                messages += [
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": (
                            f"The previous response violated the JSON contract: {exc}. "
                            "Return the complete corrected JSON only."
                        ),
                    },
                ]
    raise ValueError(f"Utility judge failed after {retries + 1} calls: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/ci-feedback-pilot-v12.json"),
    )
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")

    config = read_json(args.config)
    config["models"]["request_timeout_seconds"] = config["runtime"][
        "request_timeout_seconds"
    ]
    configure_ollama_request_controls(config["models"])
    paths = sorted((Path(config["output_root"]) / "episodes").glob("*/*.json"))
    if not args.overwrite:
        paths = [path for path in paths if read_json(path).get("utility_judge") is None]
    if args.limit is not None:
        paths = paths[: args.limit]
    if args.dry_run:
        print(
            json.dumps(
                {"utility_judge_jobs": len(paths), "llm_calls": 2 * len(paths)}, indent=2
            )
        )
        return

    converse_root = Path(config["benchmark"]["root"])
    coverage_prompt_fn, ratings_prompt_fn = import_utility_prompts(converse_root)
    manifest = {
        "version": "converse-compatible-utility-judge-v1",
        "design": "upstream coverage call plus persona-rating mapping call",
        "config_sha256": file_sha256(args.config),
        "upstream_utility_prompts_sha256": file_sha256(
            converse_root / "judge" / "utility_prompts.py"
        ),
        "upstream_generic_prompts_sha256": file_sha256(
            converse_root / "judge" / "generic_prompts.py"
        ),
        "script_sha256": file_sha256(Path(__file__)),
    }

    def judge_one(position: int, path: Path) -> str:
        episode = read_json(path)
        package = final_package(episode)
        inputs = load_case_inputs(converse_root, episode["case"])
        persona_ratings = read_json(ratings_path(converse_root, episode))
        coverage_prompt = coverage_prompt_fn(
            use_case=episode["case"]["use_case"],
            final_package_text=package,
            user_task=inputs["user_task"],
        )
        rating_prompt = ratings_prompt_fn(
            use_case=episode["case"]["use_case"],
            final_package_text=package,
            ground_truth_ratings=json.dumps(persona_ratings, ensure_ascii=False, indent=2),
        )
        client = ChatClient(config["models"], config["credentials"])
        raw_coverage, coverage = call_json(
            client,
            coverage_prompt,
            validate_coverage,
            config["runtime"]["max_format_retries"],
        )
        raw_ratings, rating_mapping = call_json(
            client,
            rating_prompt,
            validate_ratings,
            config["runtime"]["max_format_retries"],
        )
        values = list(rating_mapping["RATINGS"].values())
        average = round(sum(values) / len(values), 2) if values else 0
        episode["utility_judge"] = {
            "provider": config["models"]["judge"]["provider"],
            "model": config["models"]["judge"]["model"],
            "final_package_text": package,
            "coverage": coverage,
            "ratings": rating_mapping,
            "average_rating": average,
            "num_items_rated": len(values),
            "raw_coverage": raw_coverage,
            "raw_ratings": raw_ratings,
            "manifest": manifest,
        }
        episode.setdefault("api_usage", []).extend(client.usage)
        atomic_write_json(path, episode)
        return f"[{position}/{len(paths)}] utility-judged {episode['case_id']} {episode['condition']}"

    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(paths) or 1)) as executor:
        futures = {
            executor.submit(judge_one, position, path): path
            for position, path in enumerate(paths, start=1)
        }
        for future in as_completed(futures):
            try:
                print(future.result(), flush=True)
            except Exception as exc:
                message = f"FAILED {futures[future]}: {type(exc).__name__}: {exc}"
                failures.append(message)
                print(message, file=sys.stderr, flush=True)
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
