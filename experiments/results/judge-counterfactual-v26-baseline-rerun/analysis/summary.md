# Judge test v26: favorable-response rates and paired comparisons (raw, not reviewed)

Comparators allowed_form/ignored from experiments/results/judge-counterfactual-v26-baseline-rerun. Holm family: 128 McNemar tests. diff = new minus reference, percentage points, paired.

| model | judge | cond | version | n | fav% new | fav% allowed | fav% removed | vs allowed: diff [95% CI] Holm p | vs removed: diff [95% CI] Holm p | omit% new/allowed/removed |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | converse | told(published) | explicit_refusal | 86 | 54.7 | 93.0 | 43.0 | -38.4 [-50.0, -26.7] p=0 | +11.6 [-1.2, +23.3] p=1 |  |
| deepseek-v4.1-flash | converse | told(published) | coarser | 79 | 59.5 | 92.4 | 40.5 | -32.9 [-44.3, -21.5] p=0 | +19.0 [+6.3, +31.6] p=0.593 |  |
| deepseek-v4.1-flash | converse | untold(modified) | explicit_refusal | 86 | 89.5 | 79.1 | 79.1 | +10.5 [+1.2, +19.8] p=1 | +10.5 [+2.3, +18.6] p=1 |  |
| deepseek-v4.1-flash | converse | untold(modified) | coarser | 79 | 83.5 | 78.5 | 78.5 | +5.1 [-6.3, +16.5] p=1 | +5.1 [-6.3, +15.2] p=1 |  |
| deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | 86 | 45.3 | 40.7 | 54.7 | +4.7 [-3.5, +12.8] p=1 | -9.3 [-17.4, -2.3] p=1 | 20.9/25.6/33.7 |
| deepseek-v4.1-flash | privacyalign | untold(published) | coarser | 79 | 43.0 | 43.0 | 57.0 | +0.0 [-3.8, +3.8] p=1 | -13.9 [-22.8, -6.3] p=0.349 | 29.1/26.6/32.9 |
| deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | 86 | 41.9 | 41.9 | 40.7 | +0.0 [-4.7, +4.7] p=1 | +1.2 [-3.5, +5.8] p=1 | 34.9/11.6/38.4 |
| deepseek-v4.1-flash | privacyalign | told(modified) | coarser | 79 | 39.2 | 44.3 | 43.0 | -5.1 [-10.1, -1.3] p=1 | -3.8 [-8.9, +0.0] p=1 | 22.8/12.7/40.5 |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | explicit_refusal | 86 | 60.5 | 31.4 | 82.6 | +29.1 [+17.4, +40.7] p=0.0025 | -22.1 [-32.6, -12.8] p=0.0072 |  |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | coarser | 79 | 48.1 | 31.6 | 82.3 | +16.5 [+5.1, +27.9] p=1 | -34.2 [-45.6, -22.8] p=0 |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | explicit_refusal | 86 | 53.5 | 20.9 | 65.1 | +32.6 [+19.8, +45.4] p=0.0005 | -11.6 [-23.3, +1.2] p=1 |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | coarser | 79 | 38.0 | 20.3 | 65.8 | +17.7 [+6.3, +29.1] p=0.654 | -27.9 [-40.5, -15.2] p=0.0211 |  |
| gpt-oss:120b | converse | told(published) | explicit_refusal | 86 | 61.6 | 83.7 | 62.8 | -22.1 [-32.6, -10.5] p=0.0333 | -1.2 [-12.8, +10.5] p=1 |  |
| gpt-oss:120b | converse | told(published) | coarser | 79 | 48.1 | 84.8 | 60.8 | -36.7 [-48.1, -25.3] p=0 | -12.7 [-26.6, +1.3] p=1 |  |
| gpt-oss:120b | converse | untold(modified) | explicit_refusal | 86 | 79.1 | 70.9 | 84.9 | +8.1 [-2.3, +18.6] p=1 | -5.8 [-15.1, +2.3] p=1 |  |
| gpt-oss:120b | converse | untold(modified) | coarser | 79 | 79.7 | 72.2 | 86.1 | +7.6 [-2.5, +17.7] p=1 | -6.3 [-15.2, +2.5] p=1 |  |
| gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | 86 | 81.4 | 89.5 | 79.1 | -8.1 [-16.3, -1.2] p=1 | +2.3 [-7.0, +11.6] p=1 | 96.5/96.5/88.4 |
| gpt-oss:120b | privacyalign | untold(published) | coarser | 79 | 83.5 | 89.9 | 82.3 | -6.3 [-15.2, +2.5] p=1 | +1.3 [-7.6, +10.1] p=1 | 97.5/96.2/87.3 |
| gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | 86 | 76.7 | 82.6 | 83.7 | -5.8 [-13.9, +2.3] p=1 | -7.0 [-15.1, +0.0] p=1 | 91.9/94.2/91.9 |
| gpt-oss:120b | privacyalign | told(modified) | coarser | 79 | 77.2 | 82.3 | 84.8 | -5.1 [-15.2, +5.1] p=1 | -7.6 [-16.5, +1.3] p=1 | 96.2/94.9/92.4 |
| gpt-oss:120b | privacylens_leak | untold(published) | explicit_refusal | 86 | 89.5 | 41.9 | 86.0 | +47.7 [+36.0, +59.3] p=0 | +3.5 [-4.7, +11.6] p=1 |  |
| gpt-oss:120b | privacylens_leak | untold(published) | coarser | 79 | 68.4 | 41.8 | 84.8 | +26.6 [+15.2, +38.0] p=0.0054 | -16.5 [-27.9, -5.1] p=1 |  |
| gpt-oss:120b | privacylens_leak | told(modified) | explicit_refusal | 86 | 91.9 | 83.7 | 82.6 | +8.1 [-1.2, +17.4] p=1 | +9.3 [+1.2, +18.6] p=1 |  |
| gpt-oss:120b | privacylens_leak | told(modified) | coarser | 79 | 81.0 | 83.5 | 82.3 | -2.5 [-13.9, +8.9] p=1 | -1.3 [-11.4, +8.9] p=1 |  |
| glm-5.3-flash | converse | told(published) | explicit_refusal | 86 | 88.4 | 95.3 | 84.9 | -7.0 [-13.9, -1.2] p=1 | +3.5 [-5.8, +11.6] p=1 |  |
| glm-5.3-flash | converse | told(published) | coarser | 79 | 88.6 | 94.9 | 83.5 | -6.3 [-12.7, +0.0] p=1 | +5.1 [-2.5, +12.7] p=1 |  |
| glm-5.3-flash | converse | untold(modified) | explicit_refusal | 86 | 94.2 | 90.7 | 91.9 | +3.5 [-3.5, +10.5] p=1 | +2.3 [-3.5, +8.1] p=1 |  |
| glm-5.3-flash | converse | untold(modified) | coarser | 79 | 94.9 | 89.9 | 91.1 | +5.1 [-1.3, +12.7] p=1 | +3.8 [+0.0, +8.9] p=1 |  |
| glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | 86 | 75.6 | 61.6 | 73.3 | +13.9 [+2.3, +25.6] p=1 | +2.3 [-5.8, +11.6] p=1 | 23.3/41.9/38.4 |
| glm-5.3-flash | privacyalign | untold(published) | coarser | 79 | 64.6 | 63.3 | 75.9 | +1.3 [-8.9, +11.4] p=1 | -11.4 [-21.5, -1.3] p=1 | 38.0/40.5/39.2 |
| glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | 86 | 76.7 | 73.3 | 73.3 | +3.5 [-2.3, +9.3] p=1 | +3.5 [-1.2, +9.3] p=1 | 75.6/8.1/74.4 |
| glm-5.3-flash | privacyalign | told(modified) | coarser | 79 | 74.7 | 74.7 | 75.9 | +0.0 [-7.6, +6.3] p=1 | -1.3 [-8.9, +6.3] p=1 | 31.6/8.9/75.9 |
| glm-5.3-flash | privacylens_leak | untold(published) | explicit_refusal | 86 | 95.3 | 38.4 | 94.2 | +57.0 [+45.4, +67.4] p=0 | +1.2 [-3.5, +5.8] p=1 |  |
| glm-5.3-flash | privacylens_leak | untold(published) | coarser | 79 | 69.6 | 38.0 | 94.9 | +31.6 [+20.2, +43.0] p=0.0002 | -25.3 [-35.4, -16.5] p=0.0002 |  |
| glm-5.3-flash | privacylens_leak | told(modified) | explicit_refusal | 86 | 100.0 | 98.8 | 98.8 | +1.2 [+0.0, +3.5] p=1 | +1.2 [+0.0, +3.5] p=1 |  |
| glm-5.3-flash | privacylens_leak | told(modified) | coarser | 79 | 100.0 | 98.7 | 98.7 | +1.3 [+0.0, +3.8] p=1 | +1.3 [+0.0, +3.8] p=1 |  |
| luna | converse | told(published) | explicit_refusal | 86 | 48.8 | 88.4 | 48.8 | -39.5 [-50.0, -29.1] p=0 | +0.0 [-11.6, +11.6] p=1 |  |
| luna | converse | told(published) | coarser | 79 | 44.3 | 87.3 | 44.3 | -43.0 [-55.7, -31.6] p=0 | +0.0 [-13.9, +13.9] p=1 |  |
| luna | converse | untold(modified) | explicit_refusal | 86 | 79.1 | 81.4 | 72.1 | -2.3 [-12.8, +8.1] p=1 | +7.0 [-2.3, +16.3] p=1 |  |
| luna | converse | untold(modified) | coarser | 79 | 78.5 | 81.0 | 69.6 | -2.5 [-13.9, +8.9] p=1 | +8.9 [-1.3, +19.0] p=1 |  |
| luna | privacyalign | untold(published) | explicit_refusal | 86 | 51.2 | 45.3 | 62.8 | +5.8 [-4.7, +15.1] p=1 | -11.6 [-22.1, -2.3] p=1 | 87.2/86.0/86.0 |
| luna | privacyalign | untold(published) | coarser | 79 | 59.5 | 45.6 | 63.3 | +13.9 [+6.3, +22.8] p=0.349 | -3.8 [-12.7, +5.1] p=1 | 87.3/87.3/87.3 |
| luna | privacyalign | told(modified) | explicit_refusal | 86 | 41.9 | 43.0 | 44.2 | -1.2 [-8.1, +5.8] p=1 | -2.3 [-9.3, +3.5] p=1 | 86.0/69.8/83.7 |
| luna | privacyalign | told(modified) | coarser | 79 | 38.0 | 44.3 | 45.6 | -6.3 [-12.7, +0.0] p=1 | -7.6 [-15.2, -1.3] p=1 | 69.6/69.6/83.5 |
| luna | privacylens_leak | untold(published) | explicit_refusal | 86 | 91.9 | 32.6 | 93.0 | +59.3 [+48.8, +69.8] p=0 | -1.2 [-5.8, +2.3] p=1 |  |
| luna | privacylens_leak | untold(published) | coarser | 79 | 51.9 | 31.6 | 92.4 | +20.2 [+10.1, +31.6] p=0.0907 | -40.5 [-51.9, -27.9] p=0 |  |
| luna | privacylens_leak | told(modified) | explicit_refusal | 86 | 96.5 | 98.8 | 98.8 | -2.3 [-7.0, +2.3] p=1 | -2.3 [-5.8, +0.0] p=1 |  |
| luna | privacylens_leak | told(modified) | coarser | 79 | 96.2 | 98.7 | 98.7 | -2.5 [-7.6, +2.5] p=1 | -2.5 [-7.6, +2.5] p=1 |  |
