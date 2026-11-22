#!/usr/bin/env bash
# Over-redaction follow-up on Ollama Cloud (v24, started 2026-10-13).
# deepseek-v4-flash:0731 and glm-5.1 were retired from Ollama Cloud on 2026-09-25, so every arm
# here runs on deepseek-v4.1-flash and is judged by glm-5.3-flash (thinking on). Compare arms
# within this run only, never against the 0731 runs.
#   1. Live multi-turn: CI rewrite Gate with the original vs the abstraction-first prompt,
#      182 related-and-useful cases each (one Ollama key per arm).
#   2. Three-way judge on both live arms.
#   3. Fixed-draft replay of the CI rewrite Gate on the original 0731 drafts with a
#      deepseek-v4.1-flash Gate: prompt (orig / abstraction-first) x thinking (off / on).
#   4. Three-way judge on the four replays.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
export PYTHONPATH=experiments/scripts PYTHONUNBUFFERED=1

LIVE="experiments/results/over-redaction-live-v24"
REPLAY="experiments/results/over-redaction-replay-v24"
mkdir -p "$LIVE" "$REPLAY/logs"
ORIG="experiments/prompts/ci_gate/ci_gate_modify_v20.txt"
ABS="experiments/prompts/ci_gate/ci_gate_modify_abstraction_first_v23.txt"
JUDGE=experiments/scripts/judge_target_disclosure_outcome_v23.py
log() { echo "[$(date '+%F %T')] $*"; }

retry() {  # label logfile cmd...
  local label="$1" logfile="$2"; shift 2
  for attempt in 1 2 3; do
    log "$label attempt $attempt"
    "$@" >> "$logfile" 2>&1 && { log "$label complete"; return 0; }
  done
  log "$label FAILED after three attempts"; return 1
}

# 1. Live runs.
for v in orig absfirst; do
  retry "live-$v" "$LIVE/$v.log" python3 experiments/scripts/run_ci_gate_pilot.py \
    --config "experiments/configs/ci-gate-over-redaction-live-v24-$v.json" --workers 6 &
done
wait

# 2. Three-way judge on the live arms.
retry judge-live "$LIVE/judge-glm.log" python3 "$JUDGE" \
  --source-root "$LIVE/orig" --conditions CI-RW --output-root "$LIVE/judged-glm/orig" \
  --judge-max-tokens 32000 --workers 12
retry judge-live-abs "$LIVE/judge-glm.log" python3 "$JUDGE" \
  --source-root "$LIVE/absfirst" --conditions CI-RW --output-root "$LIVE/judged-glm/absfirst" \
  --judge-max-tokens 32000 --workers 12

# 3. Fixed-draft replays with a deepseek-v4.1-flash Gate.
replay() {  # label prompt reasoning key
  retry "$1" "$REPLAY/logs/$1.log" python3 experiments/scripts/run_gate_model_replay_v20.py \
    --config experiments/configs/ci-gate-full-pilot-v20.json \
    --source-root experiments/results/ci-gate-full-pilot-v20-240 \
    --source-root experiments/results/ci-gate-formal-v20-ex-259 \
    --source-root experiments/results/ci-gate-v22-backfill-72 \
    --condition ci_gate_modify --case-substring related_and_useful --failure-retries 3 \
    --provider ollama_cloud --model deepseek-v4.1-flash --prompt "$2" \
    --reasoning-effort "$3" --max-tokens 16000 --ollama-key-name "$4" --workers 6 \
    --output "$REPLAY/$1"
}
replay R-orig-nothink "$ORIG" none key &
replay R-abs-nothink "$ABS" none key2 &
wait
replay R-orig-think "$ORIG" high key &
replay R-abs-think "$ABS" high key2 &
wait

# 4. Three-way judge on the replays (cases with a failed replay record are skipped and listed).
retry judge-replay "$REPLAY/logs/judge-glm.log" python3 "$JUDGE" \
  --replay-root "$REPLAY/R-orig-nothink" --replay-root "$REPLAY/R-abs-nothink" \
  --replay-root "$REPLAY/R-orig-think" --replay-root "$REPLAY/R-abs-think" \
  --output-root "$REPLAY/judged-glm" --judge-max-tokens 32000 --workers 12
log "over-redaction Ollama v24 pipeline finished"
