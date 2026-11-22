#!/usr/bin/env bash
# Counterfactual judge experiment, v3 items (hand-edited: leaked / allowed_form / ignored).
# Judges: ConVerse abstraction, PrivacyAlign leak/omit, PrivacyLens leakage; each as published and with the
# allowed form added or removed. Default model: deepseek-v4.1-flash on Ollama Cloud (~1,260 new calls).
#
#   bash experiments/scripts/run_judge_counterfactual_v25_v3.sh [model ...]
set -euo pipefail
cd "$(dirname "$0")/../.."
MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && MODELS=(deepseek-v4.1-flash)
OUT=experiments/results/judge-counterfactual-v25

python3 - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, "experiments/scripts")
from run_ci_gate_pilot import ChatClient, configure_ollama_request_controls, read_json
c = read_json(Path("experiments/configs/ci-gate-v22-feedback-571.json"))
m = {k: v for k, v in c["models"].items() if not isinstance(v, dict)}
m["request_timeout_seconds"] = 60
cred = dict(c["credentials"])
configure_ollama_request_controls(m, cred)
m["judge"] = {"provider": "ollama_cloud", "model": "deepseek-v4.1-flash", "reasoning_effort": "none",
              "max_tokens": 10, "temperature": 0}
try:
    ChatClient(m, cred).call("judge", [{"role": "user", "content": "Say OK"}])
except Exception as exc:
    sys.exit(f"Ollama quota check failed, not starting: {str(exc)[:200]}")
print("Ollama quota check ok")
EOF

for model in "${MODELS[@]}"; do
  python3 experiments/scripts/run_judge_counterfactual_v25.py --models "$model" --workers "${WORKERS:-6}" \
    > "$OUT/run_v3_${model//:/_}.log" 2>&1
  echo "$model: $(grep -c -- '-> ok' "$OUT/run_v3_${model//:/_}.log") ok, $(grep -c -- 'parse_failed\|error' "$OUT/run_v3_${model//:/_}.log") failed"
done
python3 experiments/scripts/analyze_judge_counterfactual_v25.py > "$OUT/summary_v3.txt"
echo "summary: $OUT/summary_v3.txt"
