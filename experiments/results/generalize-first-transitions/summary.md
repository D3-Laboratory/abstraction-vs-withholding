# Generalize-first transitions (reviewer R1-6)

Script: `experiments/scripts/generalize_first_transitions_v23.py`. Case sets follow the block intersections in `paper/wllfm-2026/make_tables.py`. No API calls.

| Setting (judge) | n | changed | into / out of abstracted | net leaked | net withheld |
|---|---|---|---|---|---|
| V4 replay (Luna) | 181 | 39 | 16 / 15 | +11 | -12 |
| V4.1 thinking off (GLM) | 180 | 35 | 17 / 15 | +6 | -8 |
| V4.1 thinking on (GLM) | 180 | 37 | 12 / 15 | +14 | -11 |
| Multi-turn (GLM) | 182 | 84 | 36 / 29 | +6 | -13 |
| Re-run baseline: original runs -> V4 original-instruction replay (Luna) | 181 | 38 | 16 / 17 | +3 | -2 |
| V4 replay re-judged by GLM | 177 | 37 | 14 / 18 | +12 | -8 |

- Flows into and out of abstracted nearly cancel in every setting; the net movement is from withheld to leaked. The re-run baseline changes about as many cases (38) as the instruction change (39), so individual case transitions are mostly run-to-run variation; only net movement is informative.
- Newly leaked cases: 64 distinct cases; 52 appear in one setting, 11 in two, 1 in three. On the same V4 replay releases, Luna and GLM each find 19 newly leaked cases, 10 shared.
- Names: in 183 generalize-first releases whose draft contained the full name, none was shortened to an initial (179 removed, 4 kept).
- withheld_kind (V4.1 thinking on): refused 43 -> 18, too_coarse 4 -> 15.
- Failure-pattern coding of the 50 newly leaked replay cases (`newly_leaked_coding.csv`) was done by Claude, 16 re-read by Claude (13 agree, 3 recoded under a tightened rule). It is not human annotation. Codes, judged against the draft the redactor received: A redactor rewrote to a form coarser than the draft but finer than the allowed form 12; B draft kept, item not on the redactor's list 22; C a different attribute generalized 1; D draft kept although listed 9; E confirmation or negation 3; F judge or allowed-form artifact 3. In 14 cases (3 more partly) the original-instruction arm released the same sentence and the same judge did not label it leaked, so these transitions come from judge inconsistency, not from different redactor output.
- An earlier scratch coding (A 18, B 8, D 1) used a looser definition of A and did not consult the redactor's list; the counts are not stable across coding rules and should not be reported as a quantitative finding.
