# v26 withholding-cost pilot

Controlled test of what withholding costs the user when a benign ConVerse service
needs the item for the reason the benchmark gives (`attack_rationale`). Design,
case list, call estimates and open decisions: [DESIGN.md](DESIGN.md).

Status: not run. Do not run live without the author's approval.

## Files

| file | role |
|---|---|
| `experiments/configs/withholding-cost-pilot-v26.json` | models (v24 parameters), variants, seeds, key choice, injection templates |
| `experiments/configs/withholding-cost-pilot-v26-cases.json` | 10 cases, plan rules, ratings evidence, alternates |
| `experiments/prompts/withholding_cost/*.txt` | service need adapter, service output adapter, Main hold rule, per-variant Main rules |
| `experiments/scripts/run_withholding_cost_pilot.py` | runner: shared prefix, injection, branches; `--mock`, `--dry-run`, `--estimate`, `--check-config` |
| `experiments/scripts/score_withholding_cost_pilot.py` | deterministic scoring, no model calls |
| `experiments/scripts/test_withholding_cost_pilot.py` | offline tests |

The runner imports helpers from `run_ci_gate_pilot.py` and leaves it unchanged. The
existing `judge_ci_gate_utility.py` runs unchanged on the output root.

## Offline checks (no API calls)

Run from the repository root.

```sh
env -u OLLAMA_API_KEY python3 -I experiments/scripts/test_withholding_cost_pilot.py -v
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py --dry-run
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --mock --mock-utility-judge --with-existence-only \
  --output-root /tmp/withholding-cost-mock
python3 -I experiments/scripts/score_withholding_cost_pilot.py \
  --output-root /tmp/withholding-cost-mock
```

`--mock` replaces every model with a scripted client and replaces the HTTP layer
with one that raises; the mock outcomes are scripted and say nothing about real
behaviour.

## Live run (after approval only)

Keys: the config uses the same Ollama key pool as the judge-test extension
(`credentials.ollama_key_pool`: `key` at most 3, `key2` at most 7, total 10 =
`models.max_concurrent_requests`). The runner checks each pool entry against
`ollama_key_concurrency_limits` and the sum against `max_concurrent_requests`, and refuses
to start while `OLLAMA_API_KEY` is set. The utility judge runs through
`run_withholding_cost_pilot.py --utility-judge`, which calls the unchanged
`judge_ci_gate_utility.main()` with the same pool. Run no other Ollama job on these keys
at the same time.

```sh
# 1) conversations: 10 cases x 3 variants (seed 0 for the first pass; omit --seeds for 0 1 2)
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v26.json --seeds 0
# 2) existing ConVerse utility judge, unchanged (2 glm-5.3-flash calls per episode), same key pool
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v26.json --utility-judge
# 3) deterministic scores -> experiments/results/withholding-cost-pilot-v26/scores/
python3 -I experiments/scripts/score_withholding_cost_pilot.py
```

Outputs: `prefixes/<case>__s<seed>.json` (shared prefix with its own `api_usage`),
`episodes/<variant>/<case>__s<seed>.json` (branch; `api_usage` covers the branch
only), `scores/episodes.jsonl`, `scores/summary.json`. Reruns resume; `--overwrite`
regenerates.

## v27 revision (second pilot; not run)

The v26 pilot ran once (seed 0, 30 branches; results kept unchanged in
`experiments/results/withholding-cost-pilot-v26/`). A read-only audit of all 30
transcripts found scorer bugs and oracle problems; v27 fixes them. The case list and
oracles must be shown to the author before any API call. Changes are listed in
[DESIGN.md section 12](DESIGN.md#12-v27-revision).

| file | role |
|---|---|
| `experiments/configs/withholding-cost-pilot-v27.json` | v26 config with v27 cases, v27 Main prompts, `scorer_module`, seeded sampling (T 0.7, 3 seeds), output root `withholding-cost-pilot-v27` |
| `experiments/configs/withholding-cost-pilot-v27-cases.json` | 9 test cases + 1 noise baseline; oracle definition, ratings evidence, a-priori sufficiency, replaced/rejected cases |
| `experiments/configs/withholding-cost-pilot-v26-rescore-v27scorer-cases.json` | v26 cases with the v26 oracle (`check`), the audit's redefined oracle (`alt_check`) and the audit's manual verdicts |
| `experiments/prompts/withholding_cost/main_*_v27.txt` | stronger hold rule; allowed/refuse rules cover environment items; `<affected_decision>` statement |
| `experiments/scripts/score_withholding_cost_pilot_v27.py` | fixed scorer (the v26 scorer is kept for the v26 scores) |
| `experiments/scripts/test_withholding_cost_pilot_v27.py` | tests for every scorer fix (v26 transcript snippets), v26 re-score vs manual verdicts, v27 config, mock run |

`run_withholding_cost_pilot.py` was updated in place; with the v26 config it still uses
the v26 scorer, v26 prompts and v26 schema names.

```sh
# offline (no API calls)
cd experiments/scripts && env -u OLLAMA_API_KEY python3 -I -m unittest discover -s . -p 'test_*.py'; cd ../..
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v27.json --check-config
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v27.json --estimate
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v27.json --mock --mock-utility-judge \
  --output-root /tmp/withholding-cost-v27-mock
python3 -I experiments/scripts/score_withholding_cost_pilot_v27.py \
  --config experiments/configs/withholding-cost-pilot-v27.json --output-root /tmp/withholding-cost-v27-mock

# v26 episodes re-scored with the v27 scorer (written next to the original scores)
python3 -I experiments/scripts/score_withholding_cost_pilot_v27.py \
  --config experiments/configs/withholding-cost-pilot-v26.json \
  --cases-file experiments/configs/withholding-cost-pilot-v26-rescore-v27scorer-cases.json \
  --output-root experiments/results/withholding-cost-pilot-v26 --scores-dir scores_v27scorer

# live, after the author approves the cases (key pool key<=3 + key2<=7; no other Ollama job at the same time)
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v27.json
env -u OLLAMA_API_KEY python3 -I experiments/scripts/run_withholding_cost_pilot.py \
  --config experiments/configs/withholding-cost-pilot-v27.json --utility-judge
python3 -I experiments/scripts/score_withholding_cost_pilot_v27.py \
  --config experiments/configs/withholding-cost-pilot-v27.json
```
