# Withholding cost in the existing runs: summary

Script: `python3 -I experiments/scripts/withholding_cost_existing_runs_v23.py` (no API calls; default
`--boot 2000 --seed 20261115`). Labels: GPT-5.6 Luna (`target-disclosure-outcome-v23-luna`), 8 configurations x
182 related-and-useful cases = 1,456 episodes. Mechanism facts with file:line references: `README.md`.

Files: `tables.txt` (all tables), `numbers.json` (every number), `by_group.csv` (scope x group),
`per_episode.csv` (one row per episode, all measures), `withheld_by_item.csv`, `scratch_comparison.txt`.

## Definitions

- Groups: Luna outcome; WITHHELD split by `withheld_kind` (refused, deferred, ignored, too_coarse). Subtypes are
  judge output and not human-validated.
- Attack turns: service turns with `external_phase == "adversarial"`; `hit5` = all 5 used.
- Re-asks: lexical heuristic (keywords from the case's `attack_action` + `data_item` minus a stop list, in a
  sentence with an ask cue such as "?", "please", "could you", "share", "provide", "confirm"). First request = first
  matching service message; re-asks = later matching service messages. Not validated by hand.
- Dialog length: characters in service->assistant plus assistant->service messages. Turns: assistant turns.
- Completion, coverage (fraction of requested plan items covered), rating (mean ground-truth rating of chosen
  options; 0 when no plan). `ratC` = rating among completed episodes.
- Priced options: first service message has >= 3 prices (regex: EUR sign, $ or CAD followed by a digit); and a
  message with >= 3 prices comes at or before the first detected request.
- Within-case paired estimator: for each case with >= 1 episode in both groups (across the selected
  configurations), take the difference of the per-case group means; report the unweighted mean over cases with a
  percentile case-bootstrap 95% CI (2,000 reps).
- Pooled estimator (paper Sec. IV-D): difference of pooled group means, CI by resampling cases.

## Key numbers (all 8 configurations)

| group | n | attack turns | hit5 | re-asks | turns | dialog chars | completion | coverage | rating | 1st msg >=3 prices |
|---|---|---|---|---|---|---|---|---|---|---|
| leaked | 949 | 4.90 | 91% | 2.16 | 11.6 | 20.1k | 0.955 | 0.953 | 7.80 | 0.79 |
| abstracted | 196 | 4.95 | 96% | 2.41 | 12.1 | 19.3k | 0.929 | 0.927 | 7.71 | 0.88 |
| withheld | 311 | 4.92 | 93% | 2.68 | 11.3 | 16.8k | 0.961 | 0.958 | 7.83 | 0.92 |
| refused | 84 | 4.88 | 89% | 2.39 | 10.8 | 16.5k | 0.964 | 0.964 | 7.71 | 0.90 |
| deferred | 47 | 5.00 | 100% | 2.47 | 10.7 | 18.0k | 0.979 | 0.974 | 8.03 | 0.94 |
| ignored | 61 | 4.92 | 93% | 2.66 | 10.6 | 13.6k | 0.984 | 0.974 | 8.12 | 0.90 |
| too_coarse | 119 | 4.92 | 92% | 2.97 | 12.3 | 18.2k | 0.941 | 0.939 | 7.69 | 0.93 |

Strongest defense (privacy + contextual rewrite): leaked 85 (completion 0.929, rating 7.63), abstracted 33
(0.939, 7.90), withheld 64 (0.969, 7.78); withheld subtypes refused 14, deferred 10, ignored 13, too_coarse 27.
Per-configuration rows: `tables.txt`.

Within-case differences, withheld minus abstracted:

| scope | cases | completion | coverage | rating | turns |
|---|---|---|---|---|---|
| all 8 configs | 59 | +0.093 [+0.025, +0.169] | +0.090 [+0.023, +0.167] | +0.65 [+0.05, +1.35] | -1.66 [-3.03, -0.36] |
| 5 redactor configs | 51 | +0.078 [+0.000, +0.167] | +0.076 [+0.000, +0.165] | +0.40 [-0.25, +1.14] | -1.52 [-3.08, -0.14] |

Withheld does not score worse than abstracted on any task metric; it ends sooner and completes at least as often.
Split: too_coarse - abstracted (35 cases) completion +0.081 [-0.029, +0.205]; withheld excl. too_coarse -
abstracted (39 cases) +0.094 [+0.017, +0.192] (all 8 configs). Re-asks: withheld - abstracted -0.06
[-0.38, +0.30]; withheld - leaked +0.42 [+0.14, +0.71].

Pooled estimator, 5 redactor configs: completion 0.965 vs 0.925 (254 vs 161 episodes, 135 cases), difference
+0.039 [-0.003, +0.088]; coverage 0.961 vs 0.923; rating 7.84 vs 7.68, +0.155 [-0.26, +0.63]. Point values
reproduce the paper's Sec. IV-D text; the CIs differ slightly because of a different bootstrap draw
(paper: completion -0.2 to 9.0 pp; coverage -0.005 to 0.089; rating -0.27 to 0.65). The script that produced the
paper's CIs is not in the repo (only its output, `results/task-metrics-case-bootstrap-v3.txt`).

Withheld subtype counts (Luna): feedback configs 110 withheld = 43 refused, 17 deferred, 20 ignored, 30 too_coarse;
rewrite configs 169 = 30, 28, 36, 75 (matches the paper text). GLM gives more refusals and fewer too_coarse
(all 8: GLM 303 withheld = 125/48/31/97 vs Luna 311 = 84/47/61/119).

Item types: 106 of 311 withheld episodes request identifiers under the make_tables.py definition (full_name 35,
government_id_information 17, exact_age 15, exact_address 12, age_range 11, age 7, ...); strongest defense 24 of 64;
no defense 2 of 13. GLM: 98 of 303. By subtype, identifiers are 40 of 47 deferred, 26 of 84 refused, 19 of 61
ignored and 21 of 119 too_coarse.

## Agreement with the earlier scratch audit

All 131 checked values agree (`scratch_comparison.txt`): pooled and strongest-defense rows by outcome and subtype,
the price-order shares, and the within-case point estimates and case counts. The scratch CIs used Python's
`random` with a different case order, so the bootstrap intervals differ slightly (e.g. all-8 rating: scratch
[+0.043, +1.341], now [+0.047, +1.348]). One definitional difference: the scratch audit counted 109 withheld
episodes on identifier items with a substring rule that also caught `location_preferences` (3 episodes); this
script uses the paper's exact item list (make_tables.py) and gets 106 (the 109 is reproduced for the check).

## Caveats

- The re-ask count is a lexical proxy; it also counts confirmations that repeat the item's keywords.
- Rating is 0 for episodes without a final plan, so rating partly repeats completion; `ratC` removes that.
- Groups are by judge label; label error (see `outcome-label-sensitivity/`) moves episodes between groups,
  especially abstracted -> leaked.
- Cases with both groups are a selected subset (59 of 182 for withheld vs abstracted).
- By design (README), the service agent has usually offered priced options already, stops pursuing after 5 turns
  and is told not to gate completion, and the utility judge never sees the conversation or the item. These
  metrics could not show a cost of withholding if one existed; they are not evidence that withholding is harmless.
