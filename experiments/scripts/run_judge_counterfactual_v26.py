#!/usr/bin/env python3
"""Score only the v26 versions (explicit_refusal, coarser) with the unchanged v25 judge runner.

This wrapper does not change run_judge_counterfactual_v25.py. It adds the two version names to the runner's
VERSIONS tuple at import time and calls its main() once per version, with
  --items        experiments/datasets/judge-counterfactual-v26/items_v26_<version>.jsonl  (excluded cases left out)
  --versions     <version>
  --output-root  experiments/results/judge-counterfactual-v26
  --config       experiments/configs/judge-counterfactual-v26.json  (Ollama key pool: key 3 + key2 7)
Everything else (judge prompts, told/untold conditions, models, temperature 0, max_tokens, reasoning settings,
--retries 3, parsing, output layout, resumability, the --allow-openrouter guard) is the v25 runner's.
Any other argument is passed through to the v25 runner (e.g. --models, --workers, --dry-run, --limit).

    # all three Ollama models in ONE process (the key pool is process-wide): <=3 on key, <=7 on key2
    python3 experiments/scripts/run_judge_counterfactual_v26.py --models deepseek-v4.1-flash gpt-oss:120b glm-5.3-flash --workers 10
    # GPT-5.6 Luna on OpenRouter (paid)
    python3 experiments/scripts/run_judge_counterfactual_v26.py --models luna --allow-openrouter --workers 6

--baseline-rerun (off by default; default behaviour above is unchanged) instead re-scores the two v25 comparator
versions (allowed_form, ignored) on the same 86 cases, to check for model drift between the v25 run and the v26 run:
  --items        experiments/datasets/judge-counterfactual-v25/items_v3.jsonl  (the v25 input, unchanged)
  --versions     allowed_form ignored
  --output-root  experiments/results/judge-counterfactual-v26-baseline-rerun  (never the v25 or v26 folders)
Same config, judges, conditions, models and runner settings as the v26 run.
--baseline-versions (only with --baseline-rerun; default allowed_form ignored) picks which v25 versions to re-score,
e.g. `--baseline-rerun --baseline-versions leaked` re-scores only the v25 leaked version into the same folder
(each version is its own <version>.json file, so earlier rerun files are never overwritten).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_judge_counterfactual_v25 as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/datasets/judge-counterfactual-v26"
NEW_VERSIONS = ("explicit_refusal", "coarser")
V25_ITEMS = ROOT / "experiments/datasets/judge-counterfactual-v25/items_v3.jsonl"
BASELINE_VERSIONS = ("allowed_form", "ignored")
BASELINE_ROOT = ROOT / "experiments/results/judge-counterfactual-v26-baseline-rerun"
DEFAULTS = {"--output-root": ROOT / "experiments/results/judge-counterfactual-v26",
            "--config": ROOT / "experiments/configs/judge-counterfactual-v26.json"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new-versions", nargs="+", default=list(NEW_VERSIONS), choices=list(NEW_VERSIONS))
    ap.add_argument("--baseline-rerun", action="store_true",
                    help="re-score the v25 allowed_form/ignored versions into a separate folder (drift check)")
    ap.add_argument("--baseline-versions", nargs="+", default=list(BASELINE_VERSIONS),
                    choices=["leaked", "allowed_form", "ignored"],
                    help="with --baseline-rerun: which v25 versions to re-score (default allowed_form ignored)")
    args, passthrough = ap.parse_known_args()
    for flag in ("--items", "--versions"):
        if flag in passthrough:
            sys.exit(f"{flag} is set by this wrapper; use --new-versions")
    if "--models" not in passthrough:  # the v25 default list includes glm-5.3 and gemma4, which v26 does not use
        sys.exit("give --models explicitly (v26 uses deepseek-v4.1-flash gpt-oss:120b glm-5.3-flash luna)")
    base.VERSIONS = tuple(dict.fromkeys(base.VERSIONS + NEW_VERSIONS))
    prog = sys.argv[0]
    if args.baseline_rerun:
        if "--output-root" in passthrough:
            sys.exit("--baseline-rerun writes only to " + str(BASELINE_ROOT.relative_to(ROOT)))
        fixed = ["--output-root", str(BASELINE_ROOT), "--config", str(DEFAULTS["--config"])]
        if "--config" in passthrough:
            sys.exit("--baseline-rerun uses the v26 config")
        print(f"== baseline rerun {tuple(args.baseline_versions)}: {V25_ITEMS.relative_to(ROOT)}", flush=True)
        sys.argv = [prog, "--items", str(V25_ITEMS), "--versions", *args.baseline_versions, *fixed, *passthrough]
        base.main()
        return
    if args.baseline_versions != list(BASELINE_VERSIONS):
        sys.exit("--baseline-versions needs --baseline-rerun")
    fixed = [x for k, v in DEFAULTS.items() if k not in passthrough for x in (k, str(v))]
    for version in args.new_versions:
        items = DATA / f"items_v26_{version}.jsonl"
        print(f"== {version}: {items.relative_to(ROOT)}", flush=True)
        sys.argv = [prog, "--items", str(items), "--versions", version, *fixed, *passthrough]
        base.main()


if __name__ == "__main__":
    main()
