# Judge test, fully same-day (2026-11-15) vs v25

Holm families: {"J25 (paper, removed vs allowed)": 32, "J25-leaked (allowed vs leaked)": 32, "J26 (new versions vs allowed/removed)": 128}

## Favorable % per version (n) and removed vs allowed (paper's J25 family)

| source | model | judge | cond | leaked | allowed | removed | refusal | coarser | removed−allowed (or allowed−removed for ConVerse) [CI] raw p / Holm p | allowed−leaked [CI] Holm p | omit% L/A/R | omit R−A [CI] Holm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v25 | deepseek-v4.1-flash | converse | told(published) | 10.5 (86) | 90.7 (86) | 37.2 (86) | 54.7 (86) | 59.5 (79) | +53.5 [+41.9, +64.0] <.001 / <.001 | +80.2 [+70.9, +88.4] <.001 |  |  |
| sameday | deepseek-v4.1-flash | converse | told(published) | 11.6 (86) | 93.0 (86) | 43.0 (86) | 54.7 (86) | 59.5 (79) | +50.0 [+39.5, +60.5] <.001 / <.001 | +81.4 [+72.1, +89.5] <.001 |  |  |
| v25 | deepseek-v4.1-flash | converse | untold(modified) | 14.0 (86) | 75.6 (86) | 69.8 (86) | 89.5 (86) | 83.5 (79) | +5.8 [-7.0, +18.6] .487 / 1.000 | +61.6 [+50.0, +73.3] <.001 |  |  |
| sameday | deepseek-v4.1-flash | converse | untold(modified) | 19.8 (86) | 79.1 (86) | 79.1 (86) | 89.5 (86) | 83.5 (79) | +0.0 [-10.5, +10.5] 1.000 / 1.000 | +59.3 [+48.8, +69.8] <.001 |  |  |
| v25 | deepseek-v4.1-flash | privacyalign | untold(published) | 23.3 (86) | 29.1 (86) | 52.3 (86) | 45.3 (86) | 43.0 (79) | +23.3 [+14.0, +32.6] <.001 / <.001 | +5.8 [-2.3, +14.0] 1.000 | 10.5/17.4/20.9 | +3.5 [-3.5, +10.5] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | untold(published) | 20.9 (86) | 40.7 (86) | 54.7 (86) | 45.3 (86) | 43.0 (79) | +14.0 [+7.0, +22.1] .002 / .038 | +19.8 [+11.6, +29.1] <.001 | 14.0/25.6/33.7 | +8.1 [-1.2, +17.4] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | told(modified) | 12.8 (86) | 38.4 (86) | 40.7 (86) | 41.9 (86) | 39.2 (79) | +2.3 [-3.5, +8.1] .688 / 1.000 | +25.6 [+16.3, +34.9] <.001 | 5.8/7.0/32.6 | +25.6 [+17.4, +34.9] <.001 |
| sameday | deepseek-v4.1-flash | privacyalign | told(modified) | 12.8 (86) | 41.9 (86) | 40.7 (86) | 41.9 (86) | 39.2 (79) | -1.2 [-7.0, +3.5] 1.000 / 1.000 | +29.1 [+19.8, +38.4] <.001 | 8.1/11.6/38.4 | +26.7 [+16.3, +37.2] <.001 |
| v25 | deepseek-v4.1-flash | privacylens_leak | untold(published) | 14.0 (86) | 20.9 (86) | 66.3 (86) | 60.5 (86) | 48.1 (79) | +45.3 [+32.6, +57.0] <.001 / <.001 | +7.0 [-3.5, +17.4] 1.000 |  |  |
| sameday | deepseek-v4.1-flash | privacylens_leak | untold(published) | 15.1 (86) | 31.4 (86) | 82.6 (86) | 60.5 (86) | 48.1 (79) | +51.2 [+40.7, +61.6] <.001 / <.001 | +16.3 [+5.8, +26.7] .131 |  |  |
| v25 | deepseek-v4.1-flash | privacylens_leak | told(modified) | 27.9 (86) | 47.7 (86) | 51.2 (86) | 53.5 (86) | 38.0 (79) | +3.5 [-11.6, +18.6] .761 / 1.000 | +19.8 [+5.8, +33.7] .142 |  |  |
| sameday | deepseek-v4.1-flash | privacylens_leak | told(modified) | 18.6 (86) | 20.9 (86) | 65.1 (86) | 53.5 (86) | 38.0 (79) | +44.2 [+31.4, +55.8] <.001 / <.001 | +2.3 [-9.3, +14.0] 1.000 |  |  |
| v25 | gpt-oss:120b | converse | told(published) | 8.1 (86) | 84.9 (86) | 65.1 (86) | 61.6 (86) | 48.1 (79) | +19.8 [+8.1, +31.4] .002 / .032 | +76.7 [+67.4, +86.0] <.001 |  |  |
| sameday | gpt-oss:120b | converse | told(published) | 10.5 (86) | 83.7 (86) | 62.8 (86) | 61.6 (86) | 48.1 (79) | +20.9 [+9.3, +32.6] .001 / .033 | +73.3 [+64.0, +82.6] <.001 |  |  |
| v25 | gpt-oss:120b | converse | untold(modified) | 15.1 (86) | 73.3 (86) | 68.6 (86) | 79.1 (86) | 79.7 (79) | +4.7 [-7.0, +16.3] .557 / 1.000 | +58.1 [+46.5, +69.8] <.001 |  |  |
| sameday | gpt-oss:120b | converse | untold(modified) | 18.6 (86) | 70.9 (86) | 84.9 (86) | 79.1 (86) | 79.7 (79) | -14.0 [-24.4, -3.5] .017 / .304 | +52.3 [+40.7, +64.0] <.001 |  |  |
| v25 | gpt-oss:120b | privacyalign | untold(published) | 79.1 (86) | 87.2 (86) | 81.4 (86) | 81.4 (86) | 83.5 (79) | -5.8 [-15.1, +3.5] .302 / 1.000 | +8.1 [-2.3, +18.6] 1.000 | 98.8/96.5/94.2 | -2.3 [-8.1, +3.5] 1.000 |
| sameday | gpt-oss:120b | privacyalign | untold(published) | 81.4 (86) | 89.5 (86) | 79.1 (86) | 81.4 (86) | 83.5 (79) | -10.5 [-19.8, -2.3] .035 / .598 | +8.1 [-1.2, +17.4] 1.000 | 93.0/96.5/88.4 | -8.1 [-15.1, -2.3] .625 |
| v25 | gpt-oss:120b | privacyalign | told(modified) | 70.9 (86) | 77.9 (86) | 83.7 (86) | 76.7 (86) | 77.2 (79) | +5.8 [-3.5, +16.3] .359 / 1.000 | +7.0 [-4.7, +18.6] 1.000 | 89.5/91.9/87.2 | -4.7 [-11.6, +2.3] 1.000 |
| sameday | gpt-oss:120b | privacyalign | told(modified) | 70.9 (86) | 82.6 (86) | 83.7 (86) | 76.7 (86) | 77.2 (79) | +1.2 [-7.0, +9.3] 1.000 / 1.000 | +11.6 [+1.2, +22.1] .525 | 89.5/94.2/91.9 | -2.3 [-9.3, +4.7] 1.000 |
| v25 | gpt-oss:120b | privacylens_leak | untold(published) | 7.0 (86) | 36.0 (86) | 86.0 (86) | 89.5 (86) | 68.4 (79) | +50.0 [+38.4, +62.8] <.001 / <.001 | +29.1 [+19.8, +39.5] <.001 |  |  |
| sameday | gpt-oss:120b | privacylens_leak | untold(published) | 7.0 (86) | 41.9 (86) | 86.0 (86) | 89.5 (86) | 68.4 (79) | +44.2 [+31.4, +57.0] <.001 / <.001 | +34.9 [+23.3, +46.5] <.001 |  |  |
| v25 | gpt-oss:120b | privacylens_leak | told(modified) | 41.9 (86) | 67.4 (86) | 83.7 (86) | 91.9 (86) | 81.0 (79) | +16.3 [+3.5, +29.1] .024 / .438 | +25.6 [+11.6, +39.5] .015 |  |  |
| sameday | gpt-oss:120b | privacylens_leak | told(modified) | 40.7 (86) | 83.7 (86) | 82.6 (86) | 91.9 (86) | 81.0 (79) | -1.2 [-12.8, +10.5] 1.000 / 1.000 | +43.0 [+30.2, +55.8] <.001 |  |  |
| v25 | glm-5.3-flash | converse | told(published) | 9.3 (86) | 96.5 (86) | 82.6 (86) | 88.4 (86) | 88.6 (79) | +14.0 [+7.0, +22.1] <.001 / .011 | +87.2 [+79.1, +94.2] <.001 |  |  |
| sameday | glm-5.3-flash | converse | told(published) | 8.1 (86) | 95.3 (86) | 84.9 (86) | 88.4 (86) | 88.6 (79) | +10.5 [+4.7, +17.4] .004 / .078 | +87.2 [+80.2, +94.2] <.001 |  |  |
| v25 | glm-5.3-flash | converse | untold(modified) | 16.3 (86) | 89.5 (86) | 91.9 (86) | 94.2 (86) | 94.9 (79) | -2.3 [-9.3, +4.7] .754 / 1.000 | +73.3 [+64.0, +82.6] <.001 |  |  |
| sameday | glm-5.3-flash | converse | untold(modified) | 15.1 (86) | 90.7 (86) | 91.9 (86) | 94.2 (86) | 94.9 (79) | -1.2 [-9.3, +7.0] 1.000 / 1.000 | +75.6 [+66.3, +83.7] <.001 |  |  |
| v25 | glm-5.3-flash | privacyalign | untold(published) | 47.7 (86) | 54.7 (86) | 66.3 (86) | 75.6 (86) | 64.6 (79) | +11.6 [+3.5, +20.9] .021 / .425 | +7.0 [-2.3, +16.3] 1.000 | 36.0/40.7/47.7 | +7.0 [-3.5, +17.4] 1.000 |
| sameday | glm-5.3-flash | privacyalign | untold(published) | 53.5 (86) | 61.6 (86) | 73.3 (86) | 75.6 (86) | 64.6 (79) | +11.6 [+1.2, +22.1] .052 / .787 | +8.1 [-1.2, +17.4] 1.000 | 29.1/41.9/38.4 | -3.5 [-12.8, +5.8] 1.000 |
| v25 | glm-5.3-flash | privacyalign | told(modified) | 7.0 (86) | 75.6 (86) | 64.0 (86) | 76.7 (86) | 74.7 (79) | -11.6 [-20.9, -3.5] .021 / .425 | +68.6 [+58.1, +77.9] <.001 | 17.4/12.8/68.6 | +55.8 [+45.3, +66.3] <.001 |
| sameday | glm-5.3-flash | privacyalign | told(modified) | 9.3 (86) | 73.3 (86) | 73.3 (86) | 76.7 (86) | 74.7 (79) | +0.0 [-7.0, +7.0] 1.000 / 1.000 | +64.0 [+53.5, +74.4] <.001 | 15.1/8.1/74.4 | +66.3 [+55.8, +76.7] <.001 |
| v25 | glm-5.3-flash | privacylens_leak | untold(published) | 7.1 (85) | 45.3 (86) | 94.2 (86) | 95.3 (86) | 69.6 (79) | +48.8 [+38.4, +59.3] <.001 / <.001 | +38.8 [+27.1, +50.6] <.001 |  |  |
| sameday | glm-5.3-flash | privacylens_leak | untold(published) | 8.1 (86) | 38.4 (86) | 94.2 (86) | 95.3 (86) | 69.6 (79) | +55.8 [+45.3, +66.3] <.001 / <.001 | +30.2 [+18.6, +41.9] <.001 |  |  |
| v25 | glm-5.3-flash | privacylens_leak | told(modified) | 18.6 (86) | 100.0 (86) | 100.0 (86) | 100.0 (86) | 100.0 (79) | +0.0 [+0.0, +0.0] 1.000 / 1.000 | +81.4 [+72.1, +89.5] <.001 |  |  |
| sameday | glm-5.3-flash | privacylens_leak | told(modified) | 16.3 (86) | 98.8 (86) | 98.8 (86) | 100.0 (86) | 100.0 (79) | +0.0 [-3.5, +3.5] 1.000 / 1.000 | +82.6 [+73.3, +90.7] <.001 |  |  |
| v25 | luna | converse | told(published) | 8.1 (86) | 91.9 (86) | 51.2 (86) | 48.8 (86) | 44.3 (79) | +40.7 [+30.2, +51.2] <.001 / <.001 | +83.7 [+75.6, +90.7] <.001 |  |  |
| sameday | luna | converse | told(published) | 4.7 (86) | 88.4 (86) | 48.8 (86) | 48.8 (86) | 44.3 (79) | +39.5 [+27.9, +51.2] <.001 / <.001 | +83.7 [+75.6, +90.7] <.001 |  |  |
| v25 | luna | converse | untold(modified) | 5.8 (86) | 80.2 (86) | 70.9 (86) | 79.1 (86) | 78.5 (79) | +9.3 [-1.2, +19.8] .152 / 1.000 | +74.4 [+65.1, +83.7] <.001 |  |  |
| sameday | luna | converse | untold(modified) | 7.0 (86) | 81.4 (86) | 72.1 (86) | 79.1 (86) | 78.5 (79) | +9.3 [-1.2, +18.6] .115 / 1.000 | +74.4 [+65.1, +82.6] <.001 |  |  |
| v25 | luna | privacyalign | untold(published) | 41.9 (86) | 52.3 (86) | 55.8 (86) | 51.2 (86) | 59.5 (79) | +3.5 [-8.1, +15.1] .701 / 1.000 | +10.5 [+1.2, +19.8] .826 | 77.9/88.4/83.7 | -4.7 [-14.0, +4.7] 1.000 |
| sameday | luna | privacyalign | untold(published) | 37.2 (86) | 45.3 (86) | 62.8 (86) | 51.2 (86) | 59.5 (79) | +17.4 [+8.1, +27.9] .001 / .033 | +8.1 [-2.3, +18.6] 1.000 | 82.6/86.0/86.0 | +0.0 [-8.1, +8.1] 1.000 |
| v25 | luna | privacyalign | told(modified) | 7.0 (86) | 43.0 (86) | 39.5 (86) | 41.9 (86) | 38.0 (79) | -3.5 [-10.5, +3.5] .508 / 1.000 | +36.0 [+26.7, +46.5] <.001 | 62.8/65.1/84.9 | +19.8 [+9.3, +30.2] .011 |
| sameday | luna | privacyalign | told(modified) | 7.0 (86) | 43.0 (86) | 44.2 (86) | 41.9 (86) | 38.0 (79) | +1.2 [-3.5, +5.8] 1.000 / 1.000 | +36.0 [+25.6, +46.5] <.001 | 62.8/69.8/83.7 | +14.0 [+4.7, +23.3] .143 |
| v25 | luna | privacylens_leak | untold(published) | 4.7 (86) | 29.1 (86) | 93.0 (86) | 91.9 (86) | 51.9 (79) | +64.0 [+53.5, +74.4] <.001 / <.001 | +24.4 [+15.1, +34.9] <.001 |  |  |
| sameday | luna | privacylens_leak | untold(published) | 4.7 (86) | 32.6 (86) | 93.0 (86) | 91.9 (86) | 51.9 (79) | +60.5 [+50.0, +70.9] <.001 / <.001 | +27.9 [+16.3, +38.4] <.001 |  |  |
| v25 | luna | privacylens_leak | told(modified) | 18.6 (86) | 98.8 (86) | 95.3 (86) | 96.5 (86) | 96.2 (79) | -3.5 [-9.3, +1.2] .375 / 1.000 | +80.2 [+72.1, +88.4] <.001 |  |  |
| sameday | luna | privacylens_leak | told(modified) | 27.9 (86) | 98.8 (86) | 98.8 (86) | 96.5 (86) | 96.2 (79) | +0.0 [-3.5, +3.5] 1.000 / 1.000 | +70.9 [+60.5, +80.2] <.001 |  |  |

## ConVerse scores and too-vague rates

| source | model | cond | mean score L/A/R/ref/coarser | too vague % L/A/R/ref/coarser | score removed−allowed [CI] Wilcoxon p |
|---|---|---|---|---|---|
| v25 | deepseek-v4.1-flash | told(published) | 2.40/8.83/6.90/8.02/7.80 | 0.0/0.0/45.3/37.2/31.6 | -1.93 [-2.36, -1.49] <.001 |
| sameday | deepseek-v4.1-flash | told(published) | 2.74/9.01/7.35/8.02/7.80 | 0.0/0.0/38.4/37.2/31.6 | -1.66 [-2.07, -1.26] <.001 |
| v25 | deepseek-v4.1-flash | untold(modified) | 2.74/7.31/7.41/8.76/8.11 | 1.2/4.7/10.5/4.7/6.3 | +0.09 [-0.54, +0.73] .954 |
| sameday | deepseek-v4.1-flash | untold(modified) | 3.42/7.63/8.13/8.76/8.11 | 0.0/2.3/9.3/4.7/6.3 | +0.50 [+0.01, +1.01] .150 |
| v25 | gpt-oss:120b | told(published) | 2.73/8.59/7.78/7.69/7.38 | 1.2/0.0/14.0/25.6/36.7 | -0.81 [-1.40, -0.23] .002 |
| sameday | gpt-oss:120b | told(published) | 2.83/8.59/7.62/7.69/7.38 | 0.0/0.0/22.1/25.6/36.7 | -0.98 [-1.50, -0.43] <.001 |
| v25 | gpt-oss:120b | untold(modified) | 3.16/7.58/7.70/8.37/7.95 | 0.0/1.2/5.8/2.3/5.1 | +0.12 [-0.56, +0.80] .895 |
| sameday | gpt-oss:120b | untold(modified) | 3.28/7.48/8.49/8.37/7.95 | 0.0/2.3/4.7/2.3/5.1 | +1.01 [+0.38, +1.66] .004 |
| v25 | glm-5.3-flash | told(published) | 2.50/9.40/8.44/8.91/8.62 | 0.0/0.0/8.1/8.1/3.8 | -0.95 [-1.22, -0.72] <.001 |
| sameday | glm-5.3-flash | told(published) | 2.62/9.36/8.49/8.91/8.62 | 1.2/0.0/5.8/8.1/3.8 | -0.87 [-1.15, -0.63] <.001 |
| v25 | glm-5.3-flash | untold(modified) | 2.97/8.20/8.63/8.98/8.63 | 0.0/0.0/2.3/1.2/0.0 | +0.43 [+0.05, +0.83] .016 |
| sameday | glm-5.3-flash | untold(modified) | 2.93/8.35/8.67/8.98/8.63 | 0.0/0.0/1.2/1.2/0.0 | +0.33 [-0.12, +0.78] .208 |
| v25 | luna | told(published) | 2.56/8.94/7.88/8.07/7.86 | 0.0/0.0/33.7/39.5/44.3 | -1.06 [-1.41, -0.67] <.001 |
| sameday | luna | told(published) | 2.70/8.86/7.78/8.07/7.86 | 3.5/0.0/32.6/39.5/44.3 | -1.08 [-1.49, -0.63] <.001 |
| v25 | luna | untold(modified) | 2.67/7.97/8.30/8.71/8.42 | 1.2/3.5/15.1/8.1/12.7 | +0.34 [-0.10, +0.81] .734 |
| sameday | luna | untold(modified) | 2.60/7.97/8.31/8.71/8.42 | 1.2/2.3/15.1/8.1/12.7 | +0.35 [-0.12, +0.85] .398 |

## J26: explicit refusal / coarser vs allowed and removed (same-source references; 128-test Holm family)

| source | model | judge | cond | version | measure | vs allowed: diff [CI] Holm p | vs removed: diff [CI] Holm p |
|---|---|---|---|---|---|---|---|
| v25 | deepseek-v4.1-flash | converse | told(published) | explicit_refusal | favorable | -36.0 [-47.7, -24.4] <.001 | +17.4 [+5.8, +29.1] .764 |
| sameday | deepseek-v4.1-flash | converse | told(published) | explicit_refusal | favorable | -38.4 [-50.0, -26.7] <.001 | +11.6 [-1.2, +23.3] 1.000 |
| v25 | deepseek-v4.1-flash | converse | told(published) | coarser | favorable | -30.4 [-41.8, -19.0] <.001 | +24.1 [+11.4, +36.7] .093 |
| sameday | deepseek-v4.1-flash | converse | told(published) | coarser | favorable | -32.9 [-44.3, -21.5] <.001 | +19.0 [+6.3, +31.6] .592 |
| v25 | deepseek-v4.1-flash | converse | untold(modified) | explicit_refusal | favorable | +14.0 [+4.7, +23.3] 1.000 | +19.8 [+9.3, +30.2] .052 |
| sameday | deepseek-v4.1-flash | converse | untold(modified) | explicit_refusal | favorable | +10.5 [+1.2, +19.8] 1.000 | +10.5 [+2.3, +18.6] 1.000 |
| v25 | deepseek-v4.1-flash | converse | untold(modified) | coarser | favorable | +7.6 [-3.8, +19.0] 1.000 | +16.5 [+5.1, +27.8] .977 |
| sameday | deepseek-v4.1-flash | converse | untold(modified) | coarser | favorable | +5.1 [-6.3, +16.5] 1.000 | +5.1 [-6.3, +15.2] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | favorable | +16.3 [+7.0, +25.6] .258 | -7.0 [-15.1, +1.2] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | omit | +3.5 [-5.8, +12.8] 1.000 | +0.0 [-9.3, +9.3] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | favorable | +4.7 [-3.5, +12.8] 1.000 | -9.3 [-17.4, -2.3] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | omit | -4.7 [-12.8, +3.5] 1.000 | -12.8 [-23.3, -2.3] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | untold(published) | coarser | favorable | +12.7 [+5.1, +21.5] .609 | -11.4 [-19.0, -3.8] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | untold(published) | coarser | omit | +11.4 [+2.5, +20.3] 1.000 | +7.6 [-2.5, +17.7] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | untold(published) | coarser | favorable | +0.0 [-3.8, +3.8] 1.000 | -13.9 [-22.8, -6.3] .349 |
| sameday | deepseek-v4.1-flash | privacyalign | untold(published) | coarser | omit | +2.5 [-5.1, +10.1] 1.000 | -3.8 [-13.9, +6.3] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | favorable | +3.5 [-2.3, +9.3] 1.000 | +1.2 [+0.0, +3.5] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | omit | +27.9 [+18.6, +37.2] <.001 | +2.3 [-5.8, +10.5] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | favorable | +0.0 [-4.7, +4.7] 1.000 | +1.2 [-3.5, +5.8] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | omit | +23.3 [+14.0, +32.6] .001 | -3.5 [-11.6, +4.7] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | told(modified) | coarser | favorable | -2.5 [-6.3, +0.0] 1.000 | -3.8 [-8.9, +1.3] 1.000 |
| v25 | deepseek-v4.1-flash | privacyalign | told(modified) | coarser | omit | +15.2 [+7.6, +24.1] .185 | -11.4 [-20.3, -2.5] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | told(modified) | coarser | favorable | -5.1 [-10.1, -1.3] 1.000 | -3.8 [-8.9, +0.0] 1.000 |
| sameday | deepseek-v4.1-flash | privacyalign | told(modified) | coarser | omit | +10.1 [+2.5, +19.0] 1.000 | -17.7 [-27.8, -7.6] .136 |
| v25 | deepseek-v4.1-flash | privacylens_leak | untold(published) | explicit_refusal | favorable | +39.5 [+27.9, +51.2] <.001 | -5.8 [-18.6, +7.0] 1.000 |
| sameday | deepseek-v4.1-flash | privacylens_leak | untold(published) | explicit_refusal | favorable | +29.1 [+17.4, +40.7] .002 | -22.1 [-32.6, -12.8] .007 |
| v25 | deepseek-v4.1-flash | privacylens_leak | untold(published) | coarser | favorable | +25.3 [+12.7, +38.0] .035 | -19.0 [-31.6, -6.3] .764 |
| sameday | deepseek-v4.1-flash | privacylens_leak | untold(published) | coarser | favorable | +16.5 [+5.1, +27.8] 1.000 | -34.2 [-45.6, -22.8] <.001 |
| v25 | deepseek-v4.1-flash | privacylens_leak | told(modified) | explicit_refusal | favorable | +5.8 [-9.3, +20.9] 1.000 | +2.3 [-12.8, +16.3] 1.000 |
| sameday | deepseek-v4.1-flash | privacylens_leak | told(modified) | explicit_refusal | favorable | +32.6 [+19.8, +45.3] <.001 | -11.6 [-23.3, +1.2] 1.000 |
| v25 | deepseek-v4.1-flash | privacylens_leak | told(modified) | coarser | favorable | -8.9 [-22.8, +6.3] 1.000 | -13.9 [-30.4, +2.5] 1.000 |
| sameday | deepseek-v4.1-flash | privacylens_leak | told(modified) | coarser | favorable | +17.7 [+6.3, +29.1] .654 | -27.8 [-40.5, -15.2] .021 |
| v25 | gpt-oss:120b | converse | told(published) | explicit_refusal | favorable | -23.3 [-34.9, -11.6] .035 | -3.5 [-16.3, +9.3] 1.000 |
| sameday | gpt-oss:120b | converse | told(published) | explicit_refusal | favorable | -22.1 [-32.6, -10.5] .033 | -1.2 [-12.8, +10.5] 1.000 |
| v25 | gpt-oss:120b | converse | told(published) | coarser | favorable | -39.2 [-50.6, -29.1] <.001 | -16.5 [-29.1, -3.8] 1.000 |
| sameday | gpt-oss:120b | converse | told(published) | coarser | favorable | -36.7 [-48.1, -25.3] <.001 | -12.7 [-26.6, +1.3] 1.000 |
| v25 | gpt-oss:120b | converse | untold(modified) | explicit_refusal | favorable | +5.8 [-4.7, +16.3] 1.000 | +10.5 [+0.0, +20.9] 1.000 |
| sameday | gpt-oss:120b | converse | untold(modified) | explicit_refusal | favorable | +8.1 [-2.3, +18.6] 1.000 | -5.8 [-15.1, +2.3] 1.000 |
| v25 | gpt-oss:120b | converse | untold(modified) | coarser | favorable | +5.1 [-5.1, +15.2] 1.000 | +10.1 [+0.0, +20.3] 1.000 |
| sameday | gpt-oss:120b | converse | untold(modified) | coarser | favorable | +7.6 [-2.5, +17.7] 1.000 | -6.3 [-15.2, +2.5] 1.000 |
| v25 | gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | favorable | -5.8 [-15.1, +3.5] 1.000 | +0.0 [-7.0, +7.0] 1.000 |
| v25 | gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | omit | +0.0 [-5.8, +5.8] 1.000 | +2.3 [-3.5, +8.1] 1.000 |
| sameday | gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | favorable | -8.1 [-16.3, -1.2] 1.000 | +2.3 [-7.0, +11.6] 1.000 |
| sameday | gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | omit | +0.0 [-5.8, +5.8] 1.000 | +8.1 [+2.3, +14.0] 1.000 |
| v25 | gpt-oss:120b | privacyalign | untold(published) | coarser | favorable | -6.3 [-15.2, +2.5] 1.000 | +1.3 [-6.3, +10.1] 1.000 |
| v25 | gpt-oss:120b | privacyalign | untold(published) | coarser | omit | +1.3 [-3.8, +7.6] 1.000 | +3.8 [-1.3, +10.1] 1.000 |
| sameday | gpt-oss:120b | privacyalign | untold(published) | coarser | favorable | -6.3 [-15.2, +2.5] 1.000 | +1.3 [-7.6, +10.1] 1.000 |
| sameday | gpt-oss:120b | privacyalign | untold(published) | coarser | omit | +1.3 [-3.8, +6.3] 1.000 | +10.1 [+2.5, +17.7] 1.000 |
| v25 | gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | favorable | -1.2 [-9.3, +7.0] 1.000 | -7.0 [-17.4, +3.5] 1.000 |
| v25 | gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | omit | +0.0 [-7.0, +7.0] 1.000 | +4.7 [-1.2, +10.5] 1.000 |
| sameday | gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | favorable | -5.8 [-14.0, +2.3] 1.000 | -7.0 [-15.1, +0.0] 1.000 |
| sameday | gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | omit | -2.3 [-8.1, +3.5] 1.000 | +0.0 [-7.0, +7.0] 1.000 |
| v25 | gpt-oss:120b | privacyalign | told(modified) | coarser | favorable | -5.1 [-13.9, +3.8] 1.000 | -6.3 [-16.5, +3.8] 1.000 |
| v25 | gpt-oss:120b | privacyalign | told(modified) | coarser | omit | +3.8 [-2.5, +10.1] 1.000 | +10.1 [+3.8, +16.5] .742 |
| sameday | gpt-oss:120b | privacyalign | told(modified) | coarser | favorable | -5.1 [-15.2, +5.1] 1.000 | -7.6 [-16.5, +1.3] 1.000 |
| sameday | gpt-oss:120b | privacyalign | told(modified) | coarser | omit | +1.3 [-3.8, +6.3] 1.000 | +3.8 [-3.8, +11.4] 1.000 |
| v25 | gpt-oss:120b | privacylens_leak | untold(published) | explicit_refusal | favorable | +53.5 [+41.9, +65.1] <.001 | +3.5 [-4.7, +11.6] 1.000 |
| sameday | gpt-oss:120b | privacylens_leak | untold(published) | explicit_refusal | favorable | +47.7 [+36.0, +59.3] <.001 | +3.5 [-4.7, +11.6] 1.000 |
| v25 | gpt-oss:120b | privacylens_leak | untold(published) | coarser | favorable | +31.6 [+20.3, +43.0] <.001 | -16.5 [-26.6, -6.3] .434 |
| sameday | gpt-oss:120b | privacylens_leak | untold(published) | coarser | favorable | +26.6 [+15.2, +38.0] .005 | -16.5 [-27.8, -5.1] 1.000 |
| v25 | gpt-oss:120b | privacylens_leak | told(modified) | explicit_refusal | favorable | +24.4 [+12.8, +36.0] .021 | +8.1 [+0.0, +16.3] 1.000 |
| sameday | gpt-oss:120b | privacylens_leak | told(modified) | explicit_refusal | favorable | +8.1 [-1.2, +17.4] 1.000 | +9.3 [+1.2, +18.6] 1.000 |
| v25 | gpt-oss:120b | privacylens_leak | told(modified) | coarser | favorable | +13.9 [+1.3, +26.6] 1.000 | -2.5 [-13.9, +8.9] 1.000 |
| sameday | gpt-oss:120b | privacylens_leak | told(modified) | coarser | favorable | -2.5 [-13.9, +8.9] 1.000 | -1.3 [-11.4, +8.9] 1.000 |
| v25 | glm-5.3-flash | converse | told(published) | explicit_refusal | favorable | -8.1 [-15.1, -2.3] 1.000 | +5.8 [-3.5, +15.1] 1.000 |
| sameday | glm-5.3-flash | converse | told(published) | explicit_refusal | favorable | -7.0 [-14.0, -1.2] 1.000 | +3.5 [-5.8, +11.6] 1.000 |
| v25 | glm-5.3-flash | converse | told(published) | coarser | favorable | -7.6 [-15.2, -1.3] 1.000 | +7.6 [-1.3, +16.5] 1.000 |
| sameday | glm-5.3-flash | converse | told(published) | coarser | favorable | -6.3 [-12.7, +0.0] 1.000 | +5.1 [-2.5, +12.7] 1.000 |
| v25 | glm-5.3-flash | converse | untold(modified) | explicit_refusal | favorable | +4.7 [-2.3, +11.6] 1.000 | +2.3 [-3.5, +8.1] 1.000 |
| sameday | glm-5.3-flash | converse | untold(modified) | explicit_refusal | favorable | +3.5 [-3.5, +10.5] 1.000 | +2.3 [-3.5, +8.1] 1.000 |
| v25 | glm-5.3-flash | converse | untold(modified) | coarser | favorable | +6.3 [-1.3, +13.9] 1.000 | +3.8 [+0.0, +8.9] 1.000 |
| sameday | glm-5.3-flash | converse | untold(modified) | coarser | favorable | +5.1 [-1.3, +12.7] 1.000 | +3.8 [+0.0, +8.9] 1.000 |
| v25 | glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | favorable | +20.9 [+9.3, +32.6] .095 | +9.3 [+0.0, +19.8] 1.000 |
| v25 | glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | omit | -17.4 [-27.9, -8.1] .152 | -24.4 [-34.9, -14.0] .002 |
| sameday | glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | favorable | +14.0 [+2.3, +25.6] 1.000 | +2.3 [-5.8, +11.6] 1.000 |
| sameday | glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | omit | -18.6 [-27.9, -9.3] .091 | -15.1 [-25.6, -4.7] .705 |
| v25 | glm-5.3-flash | privacyalign | untold(published) | coarser | favorable | +8.9 [-1.3, +19.0] 1.000 | -2.5 [-13.9, +8.9] 1.000 |
| v25 | glm-5.3-flash | privacyalign | untold(published) | coarser | omit | -1.3 [-11.4, +8.9] 1.000 | -11.4 [-21.5, -1.3] 1.000 |
| sameday | glm-5.3-flash | privacyalign | untold(published) | coarser | favorable | +1.3 [-8.9, +11.4] 1.000 | -11.4 [-21.5, -1.3] 1.000 |
| sameday | glm-5.3-flash | privacyalign | untold(published) | coarser | omit | -2.5 [-12.7, +7.6] 1.000 | -1.3 [-11.4, +8.9] 1.000 |
| v25 | glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | favorable | +1.2 [-5.8, +8.1] 1.000 | +12.8 [+5.8, +20.9] .338 |
| v25 | glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | omit | +62.8 [+53.5, +72.1] <.001 | +7.0 [-3.5, +17.4] 1.000 |
| sameday | glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | favorable | +3.5 [-2.3, +9.3] 1.000 | +3.5 [-1.2, +9.3] 1.000 |
| sameday | glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | omit | +67.4 [+58.1, +76.7] <.001 | +1.2 [-8.1, +10.5] 1.000 |
| v25 | glm-5.3-flash | privacyalign | told(modified) | coarser | favorable | -2.5 [-10.1, +5.1] 1.000 | +8.9 [+0.0, +19.0] 1.000 |
| v25 | glm-5.3-flash | privacyalign | told(modified) | coarser | omit | +17.7 [+8.9, +27.8] .135 | -38.0 [-50.6, -25.3] <.001 |
| sameday | glm-5.3-flash | privacyalign | told(modified) | coarser | favorable | +0.0 [-7.6, +6.3] 1.000 | -1.3 [-8.9, +6.3] 1.000 |
| sameday | glm-5.3-flash | privacyalign | told(modified) | coarser | omit | +22.8 [+13.9, +32.9] <.001 | -44.3 [-55.7, -32.9] <.001 |
| v25 | glm-5.3-flash | privacylens_leak | untold(published) | explicit_refusal | favorable | +50.0 [+38.4, +61.6] <.001 | +1.2 [-3.5, +5.8] 1.000 |
| sameday | glm-5.3-flash | privacylens_leak | untold(published) | explicit_refusal | favorable | +57.0 [+45.3, +67.4] <.001 | +1.2 [-3.5, +5.8] 1.000 |
| v25 | glm-5.3-flash | privacylens_leak | untold(published) | coarser | favorable | +24.1 [+11.4, +36.7] .093 | -24.1 [-35.4, -13.9] .002 |
| sameday | glm-5.3-flash | privacylens_leak | untold(published) | coarser | favorable | +31.6 [+20.3, +43.0] <.001 | -25.3 [-35.4, -16.5] <.001 |
| v25 | glm-5.3-flash | privacylens_leak | told(modified) | explicit_refusal | favorable | +0.0 [+0.0, +0.0] 1.000 | +0.0 [+0.0, +0.0] 1.000 |
| sameday | glm-5.3-flash | privacylens_leak | told(modified) | explicit_refusal | favorable | +1.2 [+0.0, +3.5] 1.000 | +1.2 [+0.0, +3.5] 1.000 |
| v25 | glm-5.3-flash | privacylens_leak | told(modified) | coarser | favorable | +0.0 [+0.0, +0.0] 1.000 | +0.0 [+0.0, +0.0] 1.000 |
| sameday | glm-5.3-flash | privacylens_leak | told(modified) | coarser | favorable | +1.3 [+0.0, +3.8] 1.000 | +1.3 [+0.0, +3.8] 1.000 |
| v25 | luna | converse | told(published) | explicit_refusal | favorable | -43.0 [-53.5, -32.6] <.001 | -2.3 [-14.0, +9.3] 1.000 |
| sameday | luna | converse | told(published) | explicit_refusal | favorable | -39.5 [-50.0, -29.1] <.001 | +0.0 [-11.6, +11.6] 1.000 |
| v25 | luna | converse | told(published) | coarser | favorable | -46.8 [-58.2, -35.4] <.001 | -3.8 [-19.0, +11.4] 1.000 |
| sameday | luna | converse | told(published) | coarser | favorable | -43.0 [-55.7, -31.6] <.001 | +0.0 [-13.9, +13.9] 1.000 |
| v25 | luna | converse | untold(modified) | explicit_refusal | favorable | -1.2 [-10.5, +8.1] 1.000 | +8.1 [-2.3, +18.6] 1.000 |
| sameday | luna | converse | untold(modified) | explicit_refusal | favorable | -2.3 [-12.8, +8.1] 1.000 | +7.0 [-2.3, +16.3] 1.000 |
| v25 | luna | converse | untold(modified) | coarser | favorable | -1.3 [-12.7, +10.1] 1.000 | +10.1 [-1.3, +21.5] 1.000 |
| sameday | luna | converse | untold(modified) | coarser | favorable | -2.5 [-13.9, +8.9] 1.000 | +8.9 [-1.3, +19.0] 1.000 |
| v25 | luna | privacyalign | untold(published) | explicit_refusal | favorable | -1.2 [-12.8, +10.5] 1.000 | -4.7 [-14.0, +4.7] 1.000 |
| v25 | luna | privacyalign | untold(published) | explicit_refusal | omit | -1.2 [-9.3, +7.0] 1.000 | +3.5 [-4.7, +12.8] 1.000 |
| sameday | luna | privacyalign | untold(published) | explicit_refusal | favorable | +5.8 [-4.7, +15.1] 1.000 | -11.6 [-22.1, -2.3] 1.000 |
| sameday | luna | privacyalign | untold(published) | explicit_refusal | omit | +1.2 [-7.0, +10.5] 1.000 | +1.2 [-7.0, +9.3] 1.000 |
| v25 | luna | privacyalign | untold(published) | coarser | favorable | +6.3 [-3.8, +17.7] 1.000 | +2.5 [-7.6, +12.7] 1.000 |
| v25 | luna | privacyalign | untold(published) | coarser | omit | -2.5 [-12.7, +7.6] 1.000 | +3.8 [-5.1, +12.7] 1.000 |
| sameday | luna | privacyalign | untold(published) | coarser | favorable | +13.9 [+6.3, +22.8] .349 | -3.8 [-12.7, +5.1] 1.000 |
| sameday | luna | privacyalign | untold(published) | coarser | omit | +0.0 [-7.6, +7.6] 1.000 | +0.0 [-10.1, +10.1] 1.000 |
| v25 | luna | privacyalign | told(modified) | explicit_refusal | favorable | -1.2 [-8.1, +5.8] 1.000 | +2.3 [-3.5, +8.1] 1.000 |
| v25 | luna | privacyalign | told(modified) | explicit_refusal | omit | +20.9 [+11.6, +30.2] .004 | +1.2 [-7.0, +9.3] 1.000 |
| sameday | luna | privacyalign | told(modified) | explicit_refusal | favorable | -1.2 [-8.1, +5.8] 1.000 | -2.3 [-9.3, +3.5] 1.000 |
| sameday | luna | privacyalign | told(modified) | explicit_refusal | omit | +16.3 [+7.0, +25.6] .265 | +2.3 [-7.0, +11.6] 1.000 |
| v25 | luna | privacyalign | told(modified) | coarser | favorable | -6.3 [-12.7, -1.3] 1.000 | -2.5 [-10.1, +5.1] 1.000 |
| v25 | luna | privacyalign | told(modified) | coarser | omit | +3.8 [-5.1, +12.7] 1.000 | -16.5 [-26.6, -6.3] .434 |
| sameday | luna | privacyalign | told(modified) | coarser | favorable | -6.3 [-12.7, +0.0] 1.000 | -7.6 [-15.2, -1.3] 1.000 |
| sameday | luna | privacyalign | told(modified) | coarser | omit | +0.0 [-8.9, +8.9] 1.000 | -13.9 [-24.1, -3.8] 1.000 |
| v25 | luna | privacylens_leak | untold(published) | explicit_refusal | favorable | +62.8 [+52.3, +73.3] <.001 | -1.2 [-5.8, +2.3] 1.000 |
| sameday | luna | privacylens_leak | untold(published) | explicit_refusal | favorable | +59.3 [+48.8, +69.8] <.001 | -1.2 [-5.8, +2.3] 1.000 |
| v25 | luna | privacylens_leak | untold(published) | coarser | favorable | +22.8 [+12.7, +32.9] .013 | -40.5 [-51.9, -29.1] <.001 |
| sameday | luna | privacylens_leak | untold(published) | coarser | favorable | +20.3 [+10.1, +31.6] .091 | -40.5 [-51.9, -27.8] <.001 |
| v25 | luna | privacylens_leak | told(modified) | explicit_refusal | favorable | -2.3 [-7.0, +2.3] 1.000 | +1.2 [+0.0, +3.5] 1.000 |
| sameday | luna | privacylens_leak | told(modified) | explicit_refusal | favorable | -2.3 [-7.0, +2.3] 1.000 | -2.3 [-5.8, +0.0] 1.000 |
| v25 | luna | privacylens_leak | told(modified) | coarser | favorable | -2.5 [-7.6, +2.5] 1.000 | +1.3 [-5.1, +7.6] 1.000 |
| sameday | luna | privacylens_leak | told(modified) | coarser | favorable | -2.5 [-7.6, +2.5] 1.000 | -2.5 [-7.6, +2.5] 1.000 |

## Calls that are not ok (expected vs ok)

- v25: glm-5.3-flash/privacylens_leak/published/untold/leaked 85/86 (parse_failed 1, cases insurance.persona4.related_and_useful.professional_equipment_and_business_assets.22)
- sameday: none
