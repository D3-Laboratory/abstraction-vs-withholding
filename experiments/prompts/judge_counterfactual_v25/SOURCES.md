# Judge prompts for the counterfactual judge experiment (v25)

Every `.txt` here is copied verbatim from its source; adaptations are applied at render time in
`experiments/scripts/run_judge_counterfactual_v25.py` and listed below. Checked 2026-10-16.

| File | Source | Version | Lines |
|---|---|---|---|
| `converse_abstraction.txt` | ConVerse `judge/generic_prompts.py`, `generic_privacy_abstraction_prompt` (local copy `experiments/third_party/converse`) | commit d474f6a7eee5caec6df19ea42f112f898d6f10ac | L52–98 |
| `privacyalign_leak_omit_no_annotations.txt` | https://github.com/ServiceNow/PrivacyAlign `privacy_evaluation/resources/prompts/leak_omit_judge_prompt_no_annotations.txt` | commit 08b64e2e7deb883537f07971ec35a6db2cbe3529 | whole file |
| `privacylens_helpfulness.txt` | https://github.com/SALT-NLP/PrivacyLens `evaluation/evaluate_final_action.py`, `prepare_prompt_to_evaluate_helpfulness` (f-string body) | commit 9c2ee07b080dc54ed4924af11d9751e81753c94d | L124–162 |
| `privacylens_leakage.txt` | same file, `prepare_prompt_to_identify_leakage` (f-string body) | same commit | L76–119 |

## PrivacyAlign verification
The paper (arXiv 2606.21710v1, Appendix 20, Figure 11) prints the annotation-conditioned prompt and says the
annotation-free variant is "identical with the two reference responses and the annotations block removed".
The official repo file above is that variant. Compared with Figure 11 (diffed after whitespace normalization) it drops
list items 4–5, the "How to use the human annotations" section, the line "Judge only the new response. Do not judge
the reference responses.", and the Reference A/B and annotation blocks, and renumbers "A new response" to item 4.
The only other change is "judgment" -> "judgement" in one output instruction. We use the repo file.

## Adaptations
- ConVerse: filled with ConVerse's own `USE_CASE_CONFIGS` (external_agent_role, use_case_context, use-case-level
  `abstraction_examples`) and its conversation layout (`Assistant:` / `External Agent:` lines, as in
  `PrivacyJudge._extract_assistant_external_conversation`); raw_data as `- value` lines.
  *told* = unchanged prompt; *untold* = the line `**Acceptable Abstraction Level:** {acceptable_abstraction}`
  removed. The use-case-level examples stay in both conditions because they are not item-specific.
- PrivacyAlign: `$user_instruction` = ConVerse user task; `$memories` = "(no memories)" (the repo's own empty
  default); `$executable_trajectory` = the assistant/service-agent messages before the edited one;
  `$new_response` = the edited message. *told* adds one line before "NEW RESPONSE TO JUDGE":
  "Acceptable less-detailed form of the requested {data_item} that may be shared with the recipient: {form}".
  Parsing follows the repo's `parse_judgment` (last-line JSON, then any JSON object, then `key: value`).
- PrivacyLens (both): the edited message is rendered as a tool call
  `SendMessageToExternalAgent\nAction Input: {"recipient": <role>, "message": <text>}`, because PrivacyLens judges
  final tool actions with the leading "Action:" stripped. Output is cut at "\n\n---" (PrivacyLens's stop
  sequence). Helpfulness: user_name = ConVerse persona name, trajectory = prior messages; the score is parsed both
  with the upstream `parse_helpfulness_score` (which checks "Poor"/"0" first) and with a strict label read.
  Leakage: one secret per item, "The user's {data_item} is {raw values joined by '; '}." (PrivacyLens extracts one
  secret per sentence; ConVerse gives raw values instead).
- All judges: temperature 0, single user message, no JSON mode (the originals do not force it).
