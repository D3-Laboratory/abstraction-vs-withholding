#!/usr/bin/env bash
# Over-redaction follow-up (v23): replay the CI rewrite Gate on the 182 related-and-useful
# cases with fixed drafts and External turns, crossing prompt (original vs abstraction-first)
# with thinking (off vs on), then judge every rebuilt conversation with the three-way judge.
#   R-orig-nothink   original prompt, no thinking (replay control, OpenRouter)
#   R-abs-nothink    abstraction-first prompt, no thinking (OpenRouter)
#   R-orig-think     original prompt, thinking on (OpenRouter)
#   R-abs-think      abstraction-first prompt, thinking on (OpenRouter)
# deepseek-v4-flash:0731 was retired from Ollama Cloud on 2026-09-25; OpenRouter still serves 0731.
# Usage: run_over_redaction_replay_v23.sh [--smoke]
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
export PYTHONPATH=experiments/scripts PYTHONUNBUFFERED=1

ROOT="experiments/results/over-redaction-replay-v23"
EXTRA=()
if [[ "${1:-}" == "--smoke" ]]; then
  ROOT="${ROOT}-smoke"; EXTRA=(--sample-size 3)
fi
mkdir -p "$ROOT/logs"
ORIG="experiments/prompts/ci_gate/ci_gate_modify_v20.txt"
ABS="experiments/prompts/ci_gate/ci_gate_modify_abstraction_first_v23.txt"
COMMON=(
  --config experiments/configs/ci-gate-full-pilot-v20.json
  --source-root experiments/results/ci-gate-full-pilot-v20-240
  --source-root experiments/results/ci-gate-formal-v20-ex-259
  --source-root experiments/results/ci-gate-v22-backfill-72
  --condition ci_gate_modify --case-substring related_and_useful --failure-retries 3
  ${EXTRA[@]+"${EXTRA[@]}"}
)

retry() {
  local label="$1"; shift
  for attempt in 1 2 3 4 5; do
    echo "[$(date +%H:%M:%S)] $label attempt $attempt"
    "$@" >> "$ROOT/logs/$label.log" 2>&1 && { echo "[$(date +%H:%M:%S)] $label complete"; return 0; }
  done
  echo "[$(date +%H:%M:%S)] $label FAILED after five attempts"; return 1
}

replay() {  # label provider model prompt reasoning key workers
  retry "$1" python3 experiments/scripts/run_gate_model_replay_v20.py "${COMMON[@]}" \
    --output "$ROOT/$1" --provider "$2" --model "$3" --prompt "$4" \
    --reasoning-effort "$5" --max-tokens 16000 --ollama-key-name "$6" --workers "$7"
}

judge() {  # label provider model replay-label...
  local label="$1" provider="$2" model="$3"; shift 3
  local roots=(); for r in "$@"; do roots+=(--replay-root "$ROOT/$r"); done
  retry "$label" python3 experiments/scripts/judge_target_disclosure_outcome_v23.py \
    "${roots[@]}" --output-root "$ROOT/judged-$label" \
    --judge-provider "$provider" --judge-model "$model" --workers 12
}

# Phase 1: no-thinking replays on OpenRouter (does not compete with Ollama keys).
replay R-orig-nothink openrouter deepseek/deepseek-v4-flash-0731 "$ORIG" none key2 10 &
P1=$!
replay R-abs-nothink openrouter deepseek/deepseek-v4-flash-0731 "$ABS" none key2 10 &
P2=$!

replay R-orig-think openrouter deepseek/deepseek-v4-flash-0731 "$ORIG" high key2 10 &
P3=$!
replay R-abs-think openrouter deepseek/deepseek-v4-flash-0731 "$ABS" high key2 10 &
P4=$!

wait $P1; wait $P2
judge luna-nothink openrouter openai/gpt-5.6-luna R-orig-nothink R-abs-nothink &
J1=$!
wait $P3; wait $P4
judge luna-think openrouter openai/gpt-5.6-luna R-orig-think R-abs-think &
J2=$!
# The GLM judge runs on Ollama Cloud; wait until the main GLM three-way judge has released the keys.
while pgrep -f "outcome_v23.py --workers 12$" >/dev/null; do sleep 30; done
judge glm ollama_cloud glm-5.3-flash R-orig-nothink R-abs-nothink R-orig-think R-abs-think
wait $J1; wait $J2
echo "[$(date +%H:%M:%S)] over-redaction replay pipeline finished"
