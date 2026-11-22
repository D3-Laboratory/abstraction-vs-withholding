# Distinguishing Abstraction from Withholding in LLM Agent Privacy Evaluation

Code, prompts, configurations, full conversation logs and judge outputs for the paper *Distinguishing Abstraction
from Withholding in LLM Agent Privacy Evaluation* (Yi-Kai Yang, Pei-Cing Huang, Ci-Siang Chen, Chan-Tung Ku,
Yihuang Kang; National Sun Yat-Sen University), Fourth Workshop on Large Language and Foundation Models
(WLLFM 2026) at IEEE BigData 2026.

One-line summary: on the ConVerse benchmark, LLM redaction lowers the attack success rate largely by withholding
the requested item rather than sharing it in the benchmark's allowed form, and the released judge prompts of
agent privacy benchmarks do not reward the allowed form unless they are given it.

Repository: https://github.com/D3-Laboratory/abstraction-vs-withholding

## Key findings (numbers as reported in the paper)

- Without a defense, the assistant leaks the requested item in 86.8% of the 182 related-and-useful ConVerse cases
  and withholds it in 7.1%. Under the strongest defense (privacy prompt + contextual rewrite redaction),
  withholding reaches 35.2% (95% CI 28.6–42.3%) and abstraction rises from 6.0% to 18.1% (Table III).
- Of the 128 cases the benchmark counts as successful defenses under the strongest defense, 64 are withheld.
  After correcting for labeling errors (Section III-D; the correction rests on assumptions stated in the paper),
  about 62 of the 128 remain withheld and corrected abstraction is 9.8%.
- In an exploratory grouping, identifiers and quasi-identifiers are withheld in 80.0% of cases under the
  strongest defense, against 26.3% for other items (Fisher's exact test, p < .001) (Table IV).
- A generalize-first instruction lowers withholding from 27.1% to 20.4% and raises leakage from 51.9% to 58.0%,
  but abstraction does not rise (21.0% to 21.5%); none of the 18 paired tests is significant after Holm's
  correction (Table V).
- Judge test (86 controlled messages, four scoring models, Fig. 2): with its released prompt, PrivacyLens's judge
  gives a favorable response to only 31% to 42% of allowed-form messages, against 83% to 94% for the removed
  version, and prefers an explicit refusal to the allowed form under all four models (29 to 59 points).
  ConVerse's abstraction judge, whose prompt includes the allowed form, favors allowed-form messages over removed
  ones, significantly under three of the four models.
- Cost diagnostic (9 cases x 3 seeds, Table VI): the final plan contains the reference option in 15 of 27
  conversations given the raw value, 12 given the allowed form, 6 given a coarser statement and 3 given a refusal,
  while ConVerse's task metrics barely move (mean option rating 8.46, 8.28, 7.96, 7.89).

The paper is the authoritative source for these numbers, their tests and their limitations.

## Repository structure

| Path | Content | Paper |
|---|---|---|
| `paper/wllfm-2026/make_tables.py` | regenerates every table, Fig. 2 and `numbers.json` (release copy, see "Changes in this release") | Tables I–VI, Fig. 2 |
| `paper/wllfm-2026/floats/`, `paper/wllfm-2026/figures/` | the tables, figure and `numbers.json` as published (reference for `reproduce.py`); `fig-example.tex` is the hand-drawn Fig. 1 | all |
| `reproduce.py` | one-command offline regeneration and comparison | all |
| `tools/unpack_outputs.py` | expands `outputs/*.jsonl.gz` into the per-record JSON tree the scripts read | — |
| `outputs/` | gzip JSONL packs of all conversations and judge outputs; `MANIFEST.json`, `USAGE.json`, `examples/` | — |
| `experiments/scripts/` | runners, judges and analyses (table below) | III, IV |
| `experiments/prompts/ci_gate/` | assistant, redactor, service-agent adapters and judge prompts | III-B, III-C |
| `experiments/prompts/judge_counterfactual_v25/` | the three released judge prompts as run in the judge test (`SOURCES.md`) | III-F, IV-G |
| `experiments/prompts/withholding_cost/` | prompts of the cost diagnostic | III-G, IV-H |
| `experiments/configs/` | run configurations and JSON schemas | IV-A |
| `experiments/datasets/judge-counterfactual-v25/`, `-v26/` | the 86 edited judge-test cases (five message versions) and exclusions | III-F, IV-G |
| `experiments/data/processed/converse-ci-gate/` | the ConVerse case split (611 cases, 571 executable) | IV-A |
| `experiments/results/<analysis>/` | small analysis outputs (aggregates) used in the text | IV |
| `experiments/withholding-cost-pilot/` | design notes of the cost diagnostic | III-G |
| `experiments/third_party/converse/` | minimal subset of ConVerse (MIT), see `THIRD_PARTY_NOTICES.md` | III-A |

Mapping of paper elements to files:

| Paper element | Computed by | Inputs |
|---|---|---|
| Table I (defense configurations) | `make_tables.py` | — |
| Table II (agreement with human annotation), IV-B | `make_tables.py` (reads the aggregate statistics) | `experiments/results/label-reliability-consensus143/` |
| Table III (outcomes), IV-C | `make_tables.py` | `outputs/outcome-judge/*`, `outputs/main-runs/*` (benchmark's judge), `experiments/results/withholding-cost-existing-runs/numbers.json` (consistency check) |
| IV-C corrected rates | aggregate outputs, copied into `numbers.json` by `make_tables.py` | `experiments/results/outcome-label-sensitivity/`, `c1-coarser-split/` |
| IV-C to IV-E, Holm's correction over the main-run tests | `holm_main_runs_tests.py` | `outputs/outcome-judge/*`, `outputs/main-runs/*`; output in `experiments/results/holm-main-runs/` |
| IV-D benchmark judge scores (withheld vs abstracted) | `benchmark_judge_scores_withheld_vs_abstracted.py` | `outputs/outcome-judge/*`, `outputs/main-runs/*`; output in `experiments/results/benchmark-judge-scores/` |
| IV-D task metrics | `task_metrics_case_bootstrap_v3.py`, `withholding_cost_existing_runs_v23.py`; cases whose allowed form is needed: aggregate output | `experiments/results/task-metrics-case-bootstrap-v3.txt`, `withholding-cost-existing-runs/`, `withholding-cost-necessity-subset/` |
| Table IV (identifiers), IV-E | `make_tables.py`; withheld kinds in `withholding_cost_existing_runs_v23.py`; redactor actions in `redactor_action_shares.py` | outcome-judge packs, main-run packs; `experiments/results/redactor-action-shares/` |
| Table V (generalize-first, thinking), IV-F | `make_tables.py`, `generalize_first_transitions_v23.py`; label correction: aggregate output | `outputs/over-redaction-replay-v23/*`, `-v24/*`, `outputs/over-redaction-live-v24/*`, `experiments/results/generalize-first-transitions/`, `table-iv-label-calibration/` |
| Fig. 2 (judge test), IV-G | `make_tables.py` (same rules as `analyze_judge_counterfactual_sameday.py`), `analyze_judge_counterfactual_v26.py`, `analyze_judge_counterfactual_v26_drift.py` | `outputs/judge-test/*`, `experiments/datasets/judge-counterfactual-v2{5,6}/`, `experiments/results/judge-counterfactual-v26*/analysis*/` |
| Table VI (cost diagnostic), IV-H | `score_withholding_cost_pilot_v27.py`, `analyze_withholding_cost_v27b_coarser.py`, `make_tables.py` | `outputs/cost-v27/*`, `experiments/results/withholding-cost-pilot-v27/scores_fixed_4var_v2/` |
| Fig. 1 | hand-drawn TikZ (`floats/fig-example.tex`) | — |

| Script (`experiments/scripts/`) | Role |
|---|---|
| `prepare_converse_ci_gate_split.py` | builds the ConVerse case split (split-manifest.json) |
| `run_ci_gate_pilot.py` | conversation runner for all defense configurations (main runs, multi-turn runs) |
| `judge_ci_gate_results_v5.py` | benchmark's judge (ConVerse privacy prompts) called by the runner |
| `judge_ci_gate_utility.py` | ConVerse task metrics (coverage, ratings) called by the runner |
| `judge_target_disclosure_outcome_v23.py` | three-outcome judge (leaked / abstracted / withheld) |
| `run_gate_model_replay_v20.py` | replay of the rewrite redactor on fixed drafts |
| `run_over_redaction_replay_v23.sh` | pipeline: DeepSeek V4 replays + judges (Table V block 1) |
| `run_over_redaction_ollama_v24.sh` | pipeline: DeepSeek V4.1 replays and multi-turn runs + judge (Table V) |
| `build_judge_counterfactual_v25.py` | judge test: candidate pool (first leaking message, prefix check) |
| `build_judge_counterfactual_v25c.py` | judge test: applies the hand-written allowed-form / removed edits |
| `build_judge_counterfactual_v26.py` | judge test: applies the explicit-refusal / coarser edits |
| `run_judge_counterfactual_v25.py` | judge test runner (three released judge prompts) |
| `run_judge_counterfactual_v26.py` | judge test runner for the v26 versions and the same-day rerun |
| `run_judge_counterfactual_v25_v3.sh` | judge test pipeline for the earlier (v25) run |
| `analyze_judge_counterfactual_v25.py` | summary of the earlier (v25) judge run |
| `analyze_judge_counterfactual_v26.py` | J26 tests (refusal / coarser vs allowed form / removed) |
| `analyze_judge_counterfactual_v26_drift.py` | run-to-run agreement between v25 and the same-day rerun |
| `analyze_judge_counterfactual_sameday.py` | Fig. 2 data and tests on the same-day data |
| `run_withholding_cost_pilot.py` | cost diagnostic runner (shared prefix, injected reply, branches) |
| `score_withholding_cost_pilot_v27.py` | cost diagnostic scorer (v27-fixed2) |
| `analyze_withholding_cost_v27b_coarser.py` | cost diagnostic: four-branch paired comparison |
| `withholding_cost_existing_runs_v23.py` | withheld kinds, task metrics by outcome, ConVerse mechanism (IV-D/E) |
| `generalize_first_transitions_v23.py` | case transitions under the generalize-first instruction (IV-F) |
| `task_metrics_case_bootstrap_v3.py` | task metrics of withheld vs abstracted answers (IV-D) |
| `benchmark_judge_scores_withheld_vs_abstracted.py` | benchmark judge scores of withheld vs abstracted answers, case-resampled CI and within-case Wilcoxon test (IV-D) |
| `redactor_action_shares.py` | share of flagged items the redactor marks for removal vs generalization (IV-E) |
| `holm_main_runs_tests.py` | Holm's correction over the tests on the main runs (IV-C to IV-E) |
| `sample_over_redaction_annotation_v23.py` | draws the stratified annotation sample (III-C) |

### Version suffixes

File names are kept as they were in the research repository. A suffix records when a file was introduced, not
whether it is outdated; only the versions behind the paper's numbers are released, so several suffixes appear side
by side:

- `v13`, `v18` (feedback-redactor prompts and schemas): loaded by the main-run configurations of `v20` but used
  only by two older feedback configurations that are not in the paper; they are released so that the configurations
  load unchanged. The paper's feedback configurations use the `v22` prompts in `prompts/ci_gate/v22/`.
- `v18` judge prompts (`privacy_target_*_v18`, `privacy_other_v18`): the benchmark's judge (ConVerse prompts, run
  on GLM-5.1) used in all main runs.
- `v20`: rewrite redactor prompts (`ci_gate_modify_v20.txt` = the paper's "original instruction"), main-run
  configurations of the first 499 cases, the replay runner.
- `v22`: feedback redactor prompts and the configurations of the 72 backfill cases and the feedback runs.
- `v23`: three-outcome judge, generalize-first instruction (`ci_gate_modify_abstraction_first_v23.txt`), DeepSeek V4
  replays, the annotation sample.
- `v24`: DeepSeek V4.1 replays and multi-turn runs (after DeepSeek V4 Flash 0731 and GLM-5.1 were retired).
- `v25`: judge test, earlier run (`items_v3.jsonl` = the hand-edited items; `items.jsonl` is the candidate pool
  produced by the first builder, whose model-written edits are not used).
- `v26`: judge test, explicit-refusal and coarser versions and the same-day rerun of the first three versions.
- `v27` / `v27b`: cost diagnostic (three branches) and its coarser branch; scored with scorer `v27-fixed2`
  (`scores_fixed_4var_v2/`). `score_withholding_cost_pilot.py` (the v26 scorer) is released only because the v27
  scorer imports its helpers; the v26 pilot itself is not released.

The main runs were produced with earlier revisions of `run_ci_gate_pilot.py` (the SHA-256 of the revision used is
stored in each conversation's `run_manifest.runtime_sha256`); the released revision is the one used for the
multi-turn runs and is the final one. `ci_gate_runtime.py`, `prepare_converse_ci_gate_split.py` and every prompt
match the hashes stored in the runs. The stored `config_sha256` of `ci-gate-formal-v20-ex.json` and
`ci-gate-v22-bare-571.json` differs from the released files, which were edited after those runs.

## Installation

Python 3.9 or later (tested with 3.9.10). Offline reproduction needs `numpy`, `scipy` and `matplotlib`; re-running
the experiments also needs `requests`, `jsonschema` and `certifi`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Only needed to re-run model calls. Copy `.env.example` to `.env` in the repository root and fill in the keys.
The runners read Ollama Cloud keys by the names given in each configuration (`key`, `key2`), OpenRouter from
`openrouter_key` or `OPENROUTER_API_KEY`; `OLLAMA_API_KEY` in the environment overrides `key` for single-key runs
(the cost-diagnostic runner refuses to start if it is set). Keys are never written to outputs.

## Reproduce all tables and figures offline (one command)

```bash
python3 reproduce.py
```

This expands `outputs/` into `experiments/results/` (about 0.9 GB, git-ignored), runs
`paper/wllfm-2026/make_tables.py`, writes the tables, Fig. 2 and `numbers.json` to `reproduced/`, and compares them
with the published copies in `paper/wllfm-2026/floats/` and `paper/wllfm-2026/figures/`. No model is called.
`python3 reproduce.py --check-analyses` also re-runs the analyses on the released outputs
(`withholding_cost_existing_runs_v23.py`, `generalize_first_transitions_v23.py`,
`task_metrics_case_bootstrap_v3.py`, `benchmark_judge_scores_withheld_vs_abstracted.py`,
`redactor_action_shares.py`, `holm_main_runs_tests.py`, the judge-test analyses and the cost-diagnostic scorer)
and compares their outputs with the released ones (the released files are restored afterwards).

Table II (`tab-human.tex`), the `numbers.json` keys `table_human` and `labels`, and the `calibration` entries
are read by `make_tables.py` from the aggregate outputs in `experiments/results/` (for Table II,
`experiments/results/label-reliability-consensus143/numbers.json`), as listed in the mapping table above.

Result of the last build check: `python3 reproduce.py --check-analyses` (Python 3.9.10, numpy 2.0.2, scipy 1.13.1, matplotlib 3.9.4): all seven
generated tables, `fig-judges.tex` and `numbers.json` are byte-identical to the published copies, and so is
`figures/fig-judges.pdf`. The re-run analyses reproduce the released outputs; `transitions.txt` matches up to line
order, and `judge-counterfactual-v26/analysis/summary.{json,md}` differ only by a field and a sentence that the
final revision of `analyze_judge_counterfactual_v26.py` adds (all numbers identical).

## Re-running the experiments

All runs call hosted models; outputs are not byte-reproducible (see "Limitations"). Run from the repository
root. The runners take `--dry-run` (and the cost runner `--estimate`, `--mock`) to check a configuration without
model calls. Examples:

```bash
python3 experiments/scripts/prepare_converse_ci_gate_split.py --check
# main runs (one configuration file per batch of cases; conditions are listed in each file)
python3 experiments/scripts/run_ci_gate_pilot.py --config experiments/configs/ci-gate-v22-feedback-571.json --workers 6
# three-outcome judge on the main runs (GPT-5.6 Luna via OpenRouter; default is GLM-5.3-Flash on Ollama Cloud)
python3 experiments/scripts/judge_target_disclosure_outcome_v23.py --judge-provider openrouter \
    --judge-model openai/gpt-5.6-luna --output-root experiments/results/target-disclosure-outcome-v23-luna
# replays and multi-turn runs
bash experiments/scripts/run_over_redaction_replay_v23.sh
bash experiments/scripts/run_over_redaction_ollama_v24.sh
# judge test
bash experiments/scripts/run_judge_counterfactual_v25_v3.sh deepseek-v4.1-flash gpt-oss:120b glm-5.3-flash
python3 experiments/scripts/run_judge_counterfactual_v25.py --models luna --allow-openrouter
python3 experiments/scripts/run_judge_counterfactual_v26.py              # explicit refusal, coarser
python3 experiments/scripts/run_judge_counterfactual_v26.py --baseline-rerun
# cost diagnostic
python3 experiments/scripts/run_withholding_cost_pilot.py --config experiments/configs/withholding-cost-pilot-v27.json
python3 experiments/scripts/run_withholding_cost_pilot.py --config experiments/configs/withholding-cost-pilot-v27b-coarser.json
python3 experiments/scripts/score_withholding_cost_pilot_v27.py \
    --config experiments/configs/withholding-cost-pilot-v27b-coarser.json \
    --cases-file experiments/configs/withholding-cost-pilot-v27-cases.json --scores-dir scores_fixed_4var_v2
python3 experiments/scripts/analyze_withholding_cost_v27b_coarser.py
```

Models and providers (paper Section IV-A): assistant, redactor, service agent and environment use DeepSeek V4
Flash (`deepseek-v4-flash:0731`, Ollama Cloud; `deepseek/deepseek-v4-flash-0731` on OpenRouter for the V4
replays) at temperature 0; DeepSeek V4.1 Flash for the V4.1 replays, the multi-turn runs and the cost diagnostic
(temperature 0.7, three seeds); outcome judges GPT-5.6 Luna (OpenRouter) and GLM-5.3-Flash (Ollama Cloud,
thinking on); the benchmark's judge and task metrics GLM-5.1 (Ollama Cloud; GLM-5.3-Flash for the multi-turn runs
and the cost diagnostic); judge test on DeepSeek V4.1 Flash, gpt-oss-120b, GLM-5.3-Flash (Ollama Cloud) and
GPT-5.6 Luna (OpenRouter). DeepSeek V4 Flash 0731 and GLM-5.1 were retired from Ollama Cloud on 2026-09-25, so
the main runs cannot be repeated with the same models there.

Calls and tokens recorded in the released outputs (`outputs/USAGE.json`; failed attempts and retries that left no
record are not counted; Ollama Cloud was used under a subscription, so no per-call cost was recorded; OpenRouter
costs are the provider-reported amounts):

| Experiment | Provider / model | Recorded calls | Prompt tokens | Completion tokens | Recorded cost (USD) |
|---|---|---:|---:|---:|---:|
| Main runs (8 configurations x 571 cases; includes the benchmark's judge and task metrics) | ollama_cloud / `deepseek-v4-flash:0731` | 139,318 | 961,972,416 | 54,590,183 | n/a (subscription) |
|  | ollama_cloud / `glm-5.1` | 22,556 | 88,180,320 | 4,821,189 | n/a (subscription) |
| Three-outcome judges on the main runs (182 related-and-useful cases x 8) | ollama_cloud / `glm-5.3-flash` | 1,458 | 8,020,482 | 3,958,781 | n/a (subscription) |
|  | openrouter / `openai/gpt-5.6-luna` | 1,457 | 7,863,464 | 531,447 | 2.55 |
| Replay, DeepSeek V4 redactor + judges (Table V, block 1) | ollama_cloud / `glm-5.3-flash` | 362 | 1,943,475 | 1,223,942 | n/a (subscription) |
|  | openrouter / `deepseek/deepseek-v4-flash-0731` | 2,871 | 11,368,594 | 528,878 | 1.89 |
|  | openrouter / `openai/gpt-5.6-luna` | 363 | 1,935,381 | 111,068 | 0.61 |
| Replay, DeepSeek V4.1 redactor + GLM judge (Table V, block 2) | ollama_cloud / `deepseek-v4.1-flash` | 6,098 | 23,211,026 | 13,609,689 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 732 | 3,908,973 | 2,640,480 | n/a (subscription) |
| Multi-turn runs, DeepSeek V4.1 (Table V, block 3) | ollama_cloud / `deepseek-v4.1-flash` | 9,362 | 55,976,548 | 3,393,261 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 2,144 | 7,790,046 | 5,293,370 | n/a (subscription) |
| Judge test, earlier run (v25) | ollama_cloud / `deepseek-v4.1-flash` | 3,544 | 3,884,109 | 364,260 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 1,724 | 2,062,229 | 7,191,495 | n/a (subscription) |
|  | ollama_cloud / `gpt-oss:120b` | 1,992 | 2,481,667 | 1,064,630 | n/a (subscription) |
|  | openrouter / `openai/gpt-5.6-luna` | 1,548 | 1,825,841 | 425,109 | 0.93 |
| Judge test, refusal / coarser (v26) | ollama_cloud / `deepseek-v4.1-flash` | 990 | 1,191,618 | 180,904 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 1,022 | 1,230,422 | 3,653,367 | n/a (subscription) |
|  | ollama_cloud / `gpt-oss:120b` | 995 | 1,232,756 | 540,934 | n/a (subscription) |
|  | openrouter / `openai/gpt-5.6-luna` | 990 | 1,167,171 | 287,099 | 0.61 |
| Judge test, same-day rerun (v26) | ollama_cloud / `deepseek-v4.1-flash` | 1,548 | 1,862,833 | 279,089 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 1,602 | 1,930,307 | 5,362,664 | n/a (subscription) |
|  | ollama_cloud / `gpt-oss:120b` | 1,553 | 1,925,326 | 834,110 | n/a (subscription) |
|  | openrouter / `openai/gpt-5.6-luna` | 1,548 | 1,825,841 | 423,480 | 0.92 |
| Cost diagnostic (v27, four branches) | ollama_cloud / `deepseek-v4.1-flash` | 1,308 | 8,981,037 | 616,726 | n/a (subscription) |
|  | ollama_cloud / `glm-5.3-flash` | 345 | 1,112,855 | 497,563 | n/a (subscription) |

## Data formats

Each `outputs/**/*.jsonl.gz` file holds one JSON object per line: `{"path": "<original path>", "data": {...}}`.
`path` is the file's location in the research repository (relative), which is where `tools/unpack_outputs.py`
writes it, so the scripts read the same tree as in the original pipeline. `data` is the original record with the
fields listed under "Sanitization" removed. `outputs/MANIFEST.json` lists every pack with its record count, SHA-256
and source directory; `outputs/examples/` holds a few readable records.

| Pack | Records | Size (MB) | Content |
|---|---:|---:|---|
| `outputs/main-runs/main_raw_prompt.jsonl.gz` | 571 | 10.3 | main runs, raw_prompt: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_privacy_prompt.jsonl.gz` | 571 | 10.2 | main runs, privacy_prompt: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_ci_feedback_bare_v22.jsonl.gz` | 571 | 11.5 | main runs, ci_feedback_bare_v22: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_generic_feedback_v22.jsonl.gz` | 571 | 12.2 | main runs, generic_feedback_v22: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_ci_feedback_v22.jsonl.gz` | 571 | 12.1 | main runs, ci_feedback_v22: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_generic_gate_modify.jsonl.gz` | 571 | 11.2 | main runs, generic_gate_modify: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_ci_gate_modify.jsonl.gz` | 571 | 11.3 | main runs, ci_gate_modify: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/main-runs/main_privacy_prompt_ci_gate_modify.jsonl.gz` | 571 | 11.0 | main runs, privacy_prompt_ci_gate_modify: full conversations, benchmark judge and task metrics (571 cases) |
| `outputs/outcome-judge/luna_raw_prompt.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), raw_prompt |
| `outputs/outcome-judge/luna_privacy_prompt.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), privacy_prompt |
| `outputs/outcome-judge/luna_ci_feedback_bare_v22.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), ci_feedback_bare_v22 |
| `outputs/outcome-judge/luna_generic_feedback_v22.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), generic_feedback_v22 |
| `outputs/outcome-judge/luna_ci_feedback_v22.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), ci_feedback_v22 |
| `outputs/outcome-judge/luna_generic_gate_modify.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), generic_gate_modify |
| `outputs/outcome-judge/luna_ci_gate_modify.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), ci_gate_modify |
| `outputs/outcome-judge/luna_privacy_prompt_ci_gate_modify.jsonl.gz` | 182 | 0.1 | three-outcome judge (GPT-5.6 Luna), privacy_prompt_ci_gate_modify |
| `outputs/outcome-judge/glm_raw_prompt.jsonl.gz` | 182 | 0.1 | three-outcome judge (GLM-5.3-Flash), raw_prompt |
| `outputs/outcome-judge/glm_privacy_prompt.jsonl.gz` | 181 | 0.1 | three-outcome judge (GLM-5.3-Flash), privacy_prompt |
| `outputs/outcome-judge/glm_ci_feedback_bare_v22.jsonl.gz` | 182 | 0.1 | three-outcome judge (GLM-5.3-Flash), ci_feedback_bare_v22 |
| `outputs/outcome-judge/glm_generic_feedback_v22.jsonl.gz` | 181 | 0.1 | three-outcome judge (GLM-5.3-Flash), generic_feedback_v22 |
| `outputs/outcome-judge/glm_ci_feedback_v22.jsonl.gz` | 182 | 0.1 | three-outcome judge (GLM-5.3-Flash), ci_feedback_v22 |
| `outputs/outcome-judge/glm_generic_gate_modify.jsonl.gz` | 180 | 0.1 | three-outcome judge (GLM-5.3-Flash), generic_gate_modify |
| `outputs/outcome-judge/glm_ci_gate_modify.jsonl.gz` | 181 | 0.1 | three-outcome judge (GLM-5.3-Flash), ci_gate_modify |
| `outputs/outcome-judge/glm_privacy_prompt_ci_gate_modify.jsonl.gz` | 181 | 0.1 | three-outcome judge (GLM-5.3-Flash), privacy_prompt_ci_gate_modify |
| `outputs/over-redaction-replay-v23/R-orig-nothink.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v23: redactor replay records, R-orig-nothink |
| `outputs/over-redaction-replay-v23/judged-luna-nothink_R-orig-nothink.jsonl.gz` | 181 | 0.1 | over-redaction-replay-v23: judged-luna-nothink judgments, R-orig-nothink |
| `outputs/over-redaction-replay-v23/judged-glm-nothink_R-orig-nothink.jsonl.gz` | 180 | 0.1 | over-redaction-replay-v23: judged-glm-nothink judgments, R-orig-nothink |
| `outputs/over-redaction-replay-v23/R-abs-nothink.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v23: redactor replay records, R-abs-nothink |
| `outputs/over-redaction-replay-v23/judged-luna-nothink_R-abs-nothink.jsonl.gz` | 182 | 0.1 | over-redaction-replay-v23: judged-luna-nothink judgments, R-abs-nothink |
| `outputs/over-redaction-replay-v23/judged-glm-nothink_R-abs-nothink.jsonl.gz` | 179 | 0.1 | over-redaction-replay-v23: judged-glm-nothink judgments, R-abs-nothink |
| `outputs/over-redaction-replay-v24/R-orig-nothink.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v24: redactor replay records, R-orig-nothink |
| `outputs/over-redaction-replay-v24/judged-glm_R-orig-nothink.jsonl.gz` | 182 | 0.1 | over-redaction-replay-v24: judged-glm judgments, R-orig-nothink |
| `outputs/over-redaction-replay-v24/R-abs-nothink.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v24: redactor replay records, R-abs-nothink |
| `outputs/over-redaction-replay-v24/judged-glm_R-abs-nothink.jsonl.gz` | 182 | 0.1 | over-redaction-replay-v24: judged-glm judgments, R-abs-nothink |
| `outputs/over-redaction-replay-v24/R-orig-think.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v24: redactor replay records, R-orig-think |
| `outputs/over-redaction-replay-v24/judged-glm_R-orig-think.jsonl.gz` | 180 | 0.1 | over-redaction-replay-v24: judged-glm judgments, R-orig-think |
| `outputs/over-redaction-replay-v24/R-abs-think.jsonl.gz` | 1429 | 0.8 | over-redaction-replay-v24: redactor replay records, R-abs-think |
| `outputs/over-redaction-replay-v24/judged-glm_R-abs-think.jsonl.gz` | 182 | 0.1 | over-redaction-replay-v24: judged-glm judgments, R-abs-think |
| `outputs/over-redaction-live-v24/orig.jsonl.gz` | 182 | 3.2 | multi-turn runs (DeepSeek V4.1 Flash), orig: full conversations |
| `outputs/over-redaction-live-v24/judged-glm_orig.jsonl.gz` | 182 | 0.1 | multi-turn runs, GLM-5.3-Flash three-outcome judgments, orig |
| `outputs/over-redaction-live-v24/absfirst.jsonl.gz` | 182 | 3.3 | multi-turn runs (DeepSeek V4.1 Flash), absfirst: full conversations |
| `outputs/over-redaction-live-v24/judged-glm_absfirst.jsonl.gz` | 182 | 0.1 | multi-turn runs, GLM-5.3-Flash three-outcome judgments, absfirst |
| `outputs/judge-test/judge-counterfactual-v25/deepseek-v4.1-flash_converse.jsonl.gz` | 618 | 0.4 | judge test v25 (earlier run: leaked, allowed form, removed): deepseek-v4.1-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v25/deepseek-v4.1-flash_privacyalign.jsonl.gz` | 618 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): deepseek-v4.1-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v25/deepseek-v4.1-flash_privacylens_leak.jsonl.gz` | 516 | 0.0 | judge test v25 (earlier run: leaked, allowed form, removed): deepseek-v4.1-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v25/gpt-oss-120b_converse.jsonl.gz` | 618 | 0.3 | judge test v25 (earlier run: leaked, allowed form, removed): gpt-oss:120b, converse prompt |
| `outputs/judge-test/judge-counterfactual-v25/gpt-oss-120b_privacyalign.jsonl.gz` | 618 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): gpt-oss:120b, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v25/gpt-oss-120b_privacylens_leak.jsonl.gz` | 557 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): gpt-oss:120b, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v25/glm-5.3-flash_converse.jsonl.gz` | 516 | 0.5 | judge test v25 (earlier run: leaked, allowed form, removed): glm-5.3-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v25/glm-5.3-flash_privacyalign.jsonl.gz` | 516 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): glm-5.3-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v25/glm-5.3-flash_privacylens_leak.jsonl.gz` | 515 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): glm-5.3-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v25/luna_converse.jsonl.gz` | 516 | 0.3 | judge test v25 (earlier run: leaked, allowed form, removed): luna, converse prompt |
| `outputs/judge-test/judge-counterfactual-v25/luna_privacyalign.jsonl.gz` | 516 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): luna, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v25/luna_privacylens_leak.jsonl.gz` | 516 | 0.1 | judge test v25 (earlier run: leaked, allowed form, removed): luna, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26/deepseek-v4.1-flash_converse.jsonl.gz` | 330 | 0.2 | judge test v26 (explicit refusal, coarser; same day as the rerun): deepseek-v4.1-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26/deepseek-v4.1-flash_privacyalign.jsonl.gz` | 330 | 0.0 | judge test v26 (explicit refusal, coarser; same day as the rerun): deepseek-v4.1-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26/deepseek-v4.1-flash_privacylens_leak.jsonl.gz` | 330 | 0.0 | judge test v26 (explicit refusal, coarser; same day as the rerun): deepseek-v4.1-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26/gpt-oss-120b_converse.jsonl.gz` | 330 | 0.2 | judge test v26 (explicit refusal, coarser; same day as the rerun): gpt-oss:120b, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26/gpt-oss-120b_privacyalign.jsonl.gz` | 330 | 0.0 | judge test v26 (explicit refusal, coarser; same day as the rerun): gpt-oss:120b, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26/gpt-oss-120b_privacylens_leak.jsonl.gz` | 330 | 0.1 | judge test v26 (explicit refusal, coarser; same day as the rerun): gpt-oss:120b, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26/glm-5.3-flash_converse.jsonl.gz` | 330 | 0.4 | judge test v26 (explicit refusal, coarser; same day as the rerun): glm-5.3-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26/glm-5.3-flash_privacyalign.jsonl.gz` | 330 | 0.1 | judge test v26 (explicit refusal, coarser; same day as the rerun): glm-5.3-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26/glm-5.3-flash_privacylens_leak.jsonl.gz` | 330 | 0.1 | judge test v26 (explicit refusal, coarser; same day as the rerun): glm-5.3-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26/luna_converse.jsonl.gz` | 330 | 0.2 | judge test v26 (explicit refusal, coarser; same day as the rerun): luna, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26/luna_privacyalign.jsonl.gz` | 330 | 0.1 | judge test v26 (explicit refusal, coarser; same day as the rerun): luna, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26/luna_privacylens_leak.jsonl.gz` | 330 | 0.0 | judge test v26 (explicit refusal, coarser; same day as the rerun): luna, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/deepseek-v4.1-flash_converse.jsonl.gz` | 516 | 0.3 | judge test v26 same-day rerun of leaked, allowed form, removed: deepseek-v4.1-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/deepseek-v4.1-flash_privacyalign.jsonl.gz` | 516 | 0.1 | judge test v26 same-day rerun of leaked, allowed form, removed: deepseek-v4.1-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/deepseek-v4.1-flash_privacylens_leak.jsonl.gz` | 516 | 0.0 | judge test v26 same-day rerun of leaked, allowed form, removed: deepseek-v4.1-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/gpt-oss-120b_converse.jsonl.gz` | 516 | 0.3 | judge test v26 same-day rerun of leaked, allowed form, removed: gpt-oss:120b, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/gpt-oss-120b_privacyalign.jsonl.gz` | 516 | 0.1 | judge test v26 same-day rerun of leaked, allowed form, removed: gpt-oss:120b, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/gpt-oss-120b_privacylens_leak.jsonl.gz` | 516 | 0.1 | judge test v26 same-day rerun of leaked, allowed form, removed: gpt-oss:120b, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/glm-5.3-flash_converse.jsonl.gz` | 516 | 0.6 | judge test v26 same-day rerun of leaked, allowed form, removed: glm-5.3-flash, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/glm-5.3-flash_privacyalign.jsonl.gz` | 516 | 0.2 | judge test v26 same-day rerun of leaked, allowed form, removed: glm-5.3-flash, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/glm-5.3-flash_privacylens_leak.jsonl.gz` | 516 | 0.2 | judge test v26 same-day rerun of leaked, allowed form, removed: glm-5.3-flash, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/luna_converse.jsonl.gz` | 516 | 0.3 | judge test v26 same-day rerun of leaked, allowed form, removed: luna, converse prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/luna_privacyalign.jsonl.gz` | 516 | 0.1 | judge test v26 same-day rerun of leaked, allowed form, removed: luna, privacyalign prompt |
| `outputs/judge-test/judge-counterfactual-v26-baseline-rerun/luna_privacylens_leak.jsonl.gz` | 516 | 0.1 | judge test v26 same-day rerun of leaked, allowed form, removed: luna, privacylens_leak prompt |
| `outputs/judge-test/judge-counterfactual-v25/_failed.jsonl.gz` | 635 | 0.1 | judge test v25: responses that failed to parse (kept for the counts of analyze_judge_counterfactual_sameday.py); not used for any rate |
| `outputs/cost-v27/episodes_raw.jsonl.gz` | 30 | 0.4 | withholding-cost diagnostic v27, raw branch: full conversations and task metrics |
| `outputs/cost-v27/episodes_allowed.jsonl.gz` | 30 | 0.4 | withholding-cost diagnostic v27, allowed branch: full conversations and task metrics |
| `outputs/cost-v27/episodes_coarser.jsonl.gz` | 27 | 0.4 | withholding-cost diagnostic v27, coarser branch: full conversations and task metrics |
| `outputs/cost-v27/episodes_refuse.jsonl.gz` | 30 | 0.4 | withholding-cost diagnostic v27, refuse branch: full conversations and task metrics |
| `outputs/cost-v27/prefixes.jsonl.gz` | 30 | 0.1 | withholding-cost diagnostic v27: shared conversation prefixes |

Main record types:

- Conversation (`main-runs`, `over-redaction-live-v24/{orig,absfirst}`, `cost-v27/episodes_*`): `case` (ConVerse
  case and requested item), `transcript` (every message with sender, receiver and raw model output),
  `release_records` (redactor input, raw and parsed output, released message), `privacy_judge_v5` (benchmark's
  judge), `utility_judge` (task metrics), `api_usage`, `run_manifest` (config, prompt and code hashes).
- Outcome judgment (`outcome-judge`, `*/judged-*`): `case_id`, `condition`, `source_episode`, `judgment`
  (`outcome` LEAKED / CONVEYED (= abstracted) / WITHHELD, `withheld_kind`, evidence quotes), `raw`, `api_usage`,
  `manifest`.
- Replay record (`over-redaction-replay-*/R-*`): one redactor call on a stored draft (`candidate`,
  `source_released_message`, `replay`), plus `replay-manifest.json`.
- Judge-test response (`judge-test`): `model`, `judge`, `condition` (`told` / `untold`: whether the prompt
  contains the allowed form), `case_id`, `version` (`leaked`, `allowed_form`, `ignored` = removed,
  `explicit_refusal`, `coarser`), `parsed`, `raw`, `status`.

Sanitization: the keys `api_key`, `apikey`, `authorization`, `credential_alias`, `credentials`, `headers`, `key_name`, `ollama_env_file`, `ollama_key_concurrency_limits`, `ollama_key_name`, `ollama_key_pool`, `openrouter_env_file`, `openrouter_key_name`, `request_headers`, `user_agent`, `x-api-key` were removed from every record (credential names, key aliases and account
pools); absolute paths were made relative. No record contained an API key, request header or endpoint
credential. Emails, names and other personal details inside the conversations belong to ConVerse's synthetic
personas or were generated by the models.

## Third-party code and licenses

`experiments/third_party/converse/` contains the minimal subset of ConVerse (https://github.com/amrgomaaelhady/ConVerse, commit
`d474f6a7eee5caec6df19ea42f112f898d6f10ac`, MIT License) that the runners import: prompt modules and the
persona, attack, rating and option resources. No upstream file was modified. Our prompts in `prompts/ci_gate/`
(`privacy_*_converse_v3`, `privacy_target_*_v18`, `privacy_other_v18`) and `prompts/judge_counterfactual_v25/` are
adapted from ConVerse, PrivacyAlign and PrivacyLens as documented in `SOURCES.md`. See `THIRD_PARTY_NOTICES.md`.

## Limitations and intended use

- Outputs of hosted LLMs are not byte-reproducible across providers, model versions or runs, even at temperature
  0; the paper itself reports that a same-day rerun of the judge test changed four significance results. The
  released outputs are the frozen artifacts behind the paper; re-running produces new data, not the same numbers.
- Results cover one benchmark (ConVerse), one model family for the agents, one run per configuration, and judge
  prompts transferred to ConVerse inputs. The three-outcome labels come from LLM judges whose abstracted label was
  confirmed by the annotators in about a third of sampled cases (Section IV-B).
- The conversations are synthetic. They contain fictional personal data from ConVerse's personas and adversarial
  extraction attempts; they are intended for research on privacy evaluation and defenses, not for training models
  to extract personal information.

## Citation

Accepted at WLLFM 2026; to appear in the Proceedings of the 2026 IEEE International Conference on Big Data
(BigData) workshops. The DOI will be added after publication.

```bibtex
@inproceedings{yang2026abstraction,
  title     = {Distinguishing Abstraction from Withholding in {LLM} Agent Privacy Evaluation},
  author    = {Yang, Yi-Kai and Huang, Pei-Cing and Chen, Ci-Siang and Ku, Chan-Tung and Kang, Yihuang},
  booktitle = {Proceedings of the 2026 IEEE International Conference on Big Data (BigData) Workshops,
               Fourth Workshop on Large Language and Foundation Models (WLLFM 2026)},
  publisher = {IEEE},
  year      = {2026},
  note      = {To appear}
}
```

See also `CITATION.cff`.

## License

Code: MIT License (`LICENSE`). Data and outputs (conversation logs, judge outputs, edited judge-test messages,
analysis outputs): Creative Commons Attribution 4.0 International (`LICENSE-DATA`); model outputs may also be
subject to the terms of the model providers. ConVerse files keep their MIT License (`THIRD_PARTY_NOTICES.md`).

## Changes in this release

- `paper/wllfm-2026/make_tables.py` differs from the research copy only in: paths set in one block (OUT, FIG, chdir to ROOT); Table II is read from the aggregate output in experiments/results/label-reliability-consensus143/; source list in the docstring; unused path constants removed; figure written to FIG; docstring usage line.
- Records in `outputs/` are sanitized as described above; text files had absolute paths made relative.
- Not included: superseded prompts, configurations and runs (pilots v1–v19, the v20/v22 runs of configurations not
  in the paper, the v26 cost pilot, invalid or smoke runs), progress and failure logs of the runners, runner stdout
  logs, and the paper sources.
