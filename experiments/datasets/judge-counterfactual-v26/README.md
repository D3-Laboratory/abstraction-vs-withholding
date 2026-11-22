# Judge counterfactual dataset v26: explicit refusal and coarser form

Extension of the v25 judge test (`../judge-counterfactual-v25/`, v3 items, the version used in the WLLFM paper)
for the camera-ready, after reviewers asked that the test cover forms of withholding other than silent removal.
Prepared on 2026-11-15. **No judge has been run on these items yet**: running them needs the author's approval.

## Provenance

- Cases: the same 86 cases as `../judge-counterfactual-v25/items_v3.jsonl` (182 related-and-useful → 179 with a
  leaked conversation → 154 meeting the prefix condition → 86 after the v3 exclusion rules). Conversation prefix,
  leaked message and the three v3 versions (`leaked`, `allowed_form`, `ignored`) are copied unchanged.
- New versions of the first disclosing assistant message, written by hand by Claude Opus 5.5 (the editor named in
  the paper), one case at a time, as exact string replacements on the leaked message
  (`counterfactual_edits_v26.json`); no model call was made to write or check them.
  - `explicit_refusal`: the item's wording is replaced by an open refusal to share it (e.g. "I can't share her
    claims history"); everything else unchanged.
  - `coarser`: the item's wording is replaced by a truthful statement strictly less specific than ConVerse's
    allowed form (by the paper's definition this counts as withheld; ConVerse's label for it is "too vague");
    everything else unchanged.
- Built by `experiments/scripts/build_judge_counterfactual_v26.py` (`python3 -I`, no network).

## Editing rules

Same as v3: change only the words that express the item, keep the rest of the message identical and coherent,
keep fluency and length close to the existing versions. Where v3's `ignored` edit had to touch another place in the
message (e.g. a later mention, renumbering, a total from which the value could be computed), the new versions use
the same extra edit. Most edits replace exactly the span that `allowed_form` replaced, so `explicit_refusal`,
`coarser` and `allowed_form` differ only in that span. Additional rules:

- `explicit_refusal` must decline openly and must neither leak nor hint the value: no raw value, number, place,
  type or category beyond the field name (e.g. for a medical-appointment item the refusal talks about "other
  commitments", not appointments; for mental-health use it talks about "one further plan"; for a compliance
  deadline it refuses "the specifics", not "the deadline").
- `coarser` must be truthful, strictly less specific than the allowed form (a strict superset category such as
  "20s" for "late 20s", "UK" for "London", "a university degree" for "university-educated marketing
  professional", "under €1,000/month" for "€300-500/month"), and must not be a refusal.
- A version that cannot meet the rules is excluded with a reason (`excluded_v26.json`), not dropped.

## Checks

Deterministic (in the build script; a hard failure stops the build): every edit applies exactly once; no raw
string anywhere in the message; no raw number in the replacement text; allowed form not present verbatim; the new
version differs from leaked, allowed_form and ignored; refusal wording present in `explicit_refusal` and absent
from `coarser`. Soft flags (raw words or allowed-form words inside the replacement) were reviewed by hand; most
`coarser` flags are expected, since a coarser form reuses the allowed form's head noun (e.g. "claims", "budget").
Every version also has a hand-check note (`check_v26.<version>.hand_check` in the items,
`checks_v26.jsonl`, `samples_v26.md`).

## Counts

| version | valid | excluded |
|---|---|---|
| explicit_refusal | 86 | 0 |
| coarser | 79 | 7 |

Coarser exclusions: 4 cases whose allowed form is the first name alone (only an initial would be coarser, which is
unnatural or untruthful in those sentences); 1 case where the allowed form is already the most generic statement
(family financial support); 1 case where the kept original text already gives the only coarser level, so a coarser
version would equal `ignored` (compliance requirements); 1 case where the allowed form only states availability and
anything coarser would be the ignored version (business trip specifics). Reasons per case in `excluded_v26.json`.
Mean length difference to `allowed_form`: −24 characters (refusal), −28 (coarser); to `ignored`: +50 and +49
(`build_v26_stats.json`).

## Files

- `counterfactual_edits_v26.json` — hand-written edits and exclusions per case, with hand-check notes (canonical source).
- `items_v26.jsonl` — 86 items, versions `leaked`, `allowed_form`, `ignored` (v3) plus the valid new versions;
  `edits_v3`, `edits_v26`, `check_v26`.
- `items_v26_explicit_refusal.jsonl` (86), `items_v26_coarser.jsonl` (79) — runner inputs, one per new version.
- `excluded_v26.json`, `checks_v26.jsonl`, `build_v26_stats.json`, `samples_v26.md` (side-by-side review file).

## Scoring (not yet run)

Runner: `experiments/scripts/run_judge_counterfactual_v26.py`, a wrapper that calls the unchanged
`run_judge_counterfactual_v25.py` with these items, `--versions explicit_refusal|coarser`, output root
`experiments/results/judge-counterfactual-v26/` and config `experiments/configs/judge-counterfactual-v26.json`.
Same 3 judge prompts (converse, privacyalign, privacylens_leak) × told/untold × 4 scoring models
(deepseek-v4.1-flash, gpt-oss:120b, glm-5.3-flash on Ollama Cloud; openai/gpt-5.6-luna on OpenRouter), temperature 0,
the v25 max_tokens/reasoning settings, `--retries 3`, request timeout 300 s. 990 calls per model, 3,960 in total.
The v25 runner writes `manifest.version = "judge-counterfactual-v25"` into each record (it identifies the scoring
code); the dataset is identified by the output root.

Ollama key concurrency: the config's key pool allows at most 3 concurrent requests on `key` (key 1) and 7 on
`key2`; the pool is process-wide, so all three Ollama models must run in one process, with no other Ollama job on
these keys at the same time.

```bash
# offline checks (no API call)
python3 -I experiments/scripts/build_judge_counterfactual_v26.py
python3 -I experiments/scripts/dry_run_judge_counterfactual_v26.py
# after approval: Ollama models, one process (key ≤3, key2 ≤7)
python3 experiments/scripts/run_judge_counterfactual_v26.py --models deepseek-v4.1-flash gpt-oss:120b glm-5.3-flash --workers 10 \
  > experiments/results/judge-counterfactual-v26/run_v26_ollama.log 2>&1
# after approval: GPT-5.6 Luna (paid OpenRouter)
python3 experiments/scripts/run_judge_counterfactual_v26.py --models luna --allow-openrouter --workers 6 \
  > experiments/results/judge-counterfactual-v26/run_v26_luna.log 2>&1
```
