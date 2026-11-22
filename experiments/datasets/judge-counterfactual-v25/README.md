# Judge counterfactual dataset v25

Built by `experiments/scripts/build_judge_counterfactual_v25.py` (editor: kimi-k3, verifier: mistral-large-4,
both on Ollama Cloud, temperature 0). Neither model is one of the planned judges (GLM, DeepSeek, GPT, Gemini).

## What an item is
One related-and-useful ConVerse case. The judge-visible conversation (assistant<->external messages only) of one
conversation in which Luna labelled the item LEAKED is cut right after the first assistant message that leaks it.
`conversation_prefix` holds the earlier messages unchanged; `versions` holds three variants of the cut message:
`leaked` (original), `allowed_form` (disclosing sentences rewritten to the acceptable abstraction),
`withheld` (first disclosing sentence replaced by a refusal, the others removed). Edits are sentence-level
replacements applied by exact string replacement, so everything else in the message is unchanged.

## How the leaking message was located
Earliest assistant message among: Luna and GLM-5.3-Flash evidence quotes (quote must appear in the message;
turn numbers alone are ambiguous because assistant and service-agent messages can share a turn number),
deterministic exact matches, and raw-string matches. Then the prefix is checked: any assistant message in the prefix
that contains a raw string, or that the verifier labels as more detailed than the allowed form, moves the target
earlier (repeated). `prefix_clean` records the result; `prefix_allowed_form_disclosed` marks items whose prefix
already gives the allowed form (the withheld version is then not fully withheld).

## Checks per item
Hard (item fails): no raw string or raw number in either edited version; no allowed form in `withheld`;
text outside the edited sentences unchanged (whitespace-insensitive); verifier: allowed_form not too detailed,
conveys the abstraction, withheld reveals nothing and is a refusal, neither version unnatural.
Soft (flag only): allowed form not verbatim (paraphrase accepted by the verifier); allowed form already in prefix.

## Counts
- related-and-useful cases: 182; with no leaked conversation under any configuration: 3 (insurance.persona1.related_and_useful.work_project_responsibility.18, insurance.persona2.related_and_useful.coverage_goals.17, travel_planning.persona1.related_and_useful.available_periods.13)
- built: 179; status: {'ok': 128, 'flag': 45, 'fail': 5, 'drop': 1}
- usable (ok or flag, prefix clean): 173; usable_strict (also no allowed form in prefix): 154
- source condition of usable items: {'raw_prompt': 152, 'privacy_prompt': 13, 'ci_feedback_bare_v22': 3, 'ci_gate_modify': 1, 'privacy_prompt_ci_gate_modify': 1, 'generic_feedback_v22': 1, 'ci_feedback_v22': 1, 'generic_gate_modify': 1}
- items whose target was moved earlier by the prefix check: 24

## v2: span-level edits (items_v2.jsonl)

Built by `experiments/scripts/build_judge_counterfactual_v25b.py` (editor kimi-k3, verifier mistral-large-4,
Ollama Cloud, temperature 0) from the 173 usable v1 items, keeping the same prefix and leaked message.
v1 replaced whole sentences or lines, so the withheld version often lost content unrelated to the item and some
allowed_form versions kept words from the raw value. v2 replaces only the minimal span(s) that express the item,
by position, so all other characters are identical across the three versions.

- allowed_form: the item inside each span is replaced by the acceptable abstraction, nothing else.
- withheld: the first span becomes "<what the item is>, which I can't share", later spans "(not shared)"; nothing is deleted.
- Hard checks: no raw string anywhere; no distinctive raw word (len > 3, not in the abstraction or item name, not a
  stopword) or raw number inside a replacement; no distinctive raw word left outside the spans; text outside the
  spans identical; withheld contains the refusal and not the abstraction; spans ≤ 160 chars, no line breaks;
  verifier (mistral-large-4) finds no added detail, no content removed beyond the item, no remaining disclosure in
  withheld, a refusal, and natural text.
- Fields: `usable_v2`, `usable_strict_v2` (also no allowed form disclosed in the prefix), `spans` (start/end in the
  leaked message), `checks` (incl. `len_diff_af_minus_wh`, `af_vs_wh_changed_blocks/chars`).

Counts: usable_v2 163, usable_strict_v2 145, failed 10.
Length difference |allowed_form − withheld|: mean 29.8 chars, max 202.
Samples: `samples_v2.md`.

## v3 (2026-10-16): hand-edited items — the version used for the paper

`items_v3.jsonl` (86 items) supersedes v1/v2. The author asked that no model rewrite the text: every allowed_form and
ignored edit was written and reviewed by hand (Claude Opus 5.5), item by item, as exact string replacements stored in
`counterfactual_edits_v3.json` and applied by `experiments/scripts/build_judge_counterfactual_v25c.py`.

- Pool: 154 items whose conversation prefix is leak-free and never shows the allowed form.
- Versions of the first leaking assistant message: `leaked` (original), `allowed_form` (only the item's wording
  replaced by ConVerse's acceptable abstraction), `ignored` (the item's wording removed, rest of the message kept
  coherent; no refusal sentence). The refusal-style "withheld" version of v1/v2 was dropped.
- 68 items excluded (`excluded_v3.json`), mainly because after removal the rest of the message still conveyed the
  item at the allowed-form level, the raw value was derivable from other numbers, the flagged text was not the raw
  value, or the whole message was about the item.
- Review file: `samples_v3.md` (every edit, side by side).
- Judge run: `experiments/scripts/run_judge_counterfactual_v25_v3.sh` (checks Ollama quota first).
