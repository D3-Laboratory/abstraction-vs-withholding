# Judge test v26: favorable-response rates and paired comparisons (raw, not reviewed)

Holm family: 128 McNemar tests. diff = new minus reference, percentage points, paired.

| model | judge | cond | version | n | fav% new | fav% allowed | fav% removed | vs allowed: diff [95% CI] Holm p | vs removed: diff [95% CI] Holm p | omit% new/allowed/removed |
|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | converse | told(published) | explicit_refusal | 86 | 54.7 | 90.7 | 37.2 | -36.0 [-47.7, -24.4] p=0 | +17.4 [+5.8, +29.1] p=0.764 |  |
| deepseek-v4.1-flash | converse | told(published) | coarser | 79 | 59.5 | 89.9 | 35.4 | -30.4 [-41.8, -19.0] p=0.0003 | +24.1 [+11.4, +36.7] p=0.0931 |  |
| deepseek-v4.1-flash | converse | untold(modified) | explicit_refusal | 86 | 89.5 | 75.6 | 69.8 | +13.9 [+4.7, +23.3] p=1 | +19.8 [+9.3, +30.2] p=0.0522 |  |
| deepseek-v4.1-flash | converse | untold(modified) | coarser | 79 | 83.5 | 75.9 | 67.1 | +7.6 [-3.8, +19.0] p=1 | +16.5 [+5.1, +27.9] p=0.977 |  |
| deepseek-v4.1-flash | privacyalign | untold(published) | explicit_refusal | 86 | 45.3 | 29.1 | 52.3 | +16.3 [+7.0, +25.6] p=0.258 | -7.0 [-15.1, +1.2] p=1 | 20.9/17.4/20.9 |
| deepseek-v4.1-flash | privacyalign | untold(published) | coarser | 79 | 43.0 | 30.4 | 54.4 | +12.7 [+5.1, +21.5] p=0.609 | -11.4 [-19.0, -3.8] p=1 | 29.1/17.7/21.5 |
| deepseek-v4.1-flash | privacyalign | told(modified) | explicit_refusal | 86 | 41.9 | 38.4 | 40.7 | +3.5 [-2.3, +9.3] p=1 | +1.2 [+0.0, +3.5] p=1 | 34.9/7.0/32.6 |
| deepseek-v4.1-flash | privacyalign | told(modified) | coarser | 79 | 39.2 | 41.8 | 43.0 | -2.5 [-6.3, +0.0] p=1 | -3.8 [-8.9, +1.3] p=1 | 22.8/7.6/34.2 |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | explicit_refusal | 86 | 60.5 | 20.9 | 66.3 | +39.5 [+27.9, +51.2] p=0 | -5.8 [-18.6, +7.0] p=1 |  |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | coarser | 79 | 48.1 | 22.8 | 67.1 | +25.3 [+12.7, +38.0] p=0.0354 | -19.0 [-31.6, -6.3] p=0.764 |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | explicit_refusal | 86 | 53.5 | 47.7 | 51.2 | +5.8 [-9.3, +20.9] p=1 | +2.3 [-12.8, +16.3] p=1 |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | coarser | 79 | 38.0 | 46.8 | 51.9 | -8.9 [-22.8, +6.3] p=1 | -13.9 [-30.4, +2.5] p=1 |  |
| gpt-oss:120b | converse | told(published) | explicit_refusal | 86 | 61.6 | 84.9 | 65.1 | -23.3 [-34.9, -11.6] p=0.0354 | -3.5 [-16.3, +9.3] p=1 |  |
| gpt-oss:120b | converse | told(published) | coarser | 79 | 48.1 | 87.3 | 64.6 | -39.2 [-50.6, -29.1] p=0 | -16.5 [-29.1, -3.8] p=1 |  |
| gpt-oss:120b | converse | untold(modified) | explicit_refusal | 86 | 79.1 | 73.3 | 68.6 | +5.8 [-4.7, +16.3] p=1 | +10.5 [+0.0, +20.9] p=1 |  |
| gpt-oss:120b | converse | untold(modified) | coarser | 79 | 79.7 | 74.7 | 69.6 | +5.1 [-5.1, +15.2] p=1 | +10.1 [+0.0, +20.2] p=1 |  |
| gpt-oss:120b | privacyalign | untold(published) | explicit_refusal | 86 | 81.4 | 87.2 | 81.4 | -5.8 [-15.1, +3.5] p=1 | +0.0 [-7.0, +7.0] p=1 | 96.5/96.5/94.2 |
| gpt-oss:120b | privacyalign | untold(published) | coarser | 79 | 83.5 | 89.9 | 82.3 | -6.3 [-15.2, +2.5] p=1 | +1.3 [-6.3, +10.1] p=1 | 97.5/96.2/93.7 |
| gpt-oss:120b | privacyalign | told(modified) | explicit_refusal | 86 | 76.7 | 77.9 | 83.7 | -1.2 [-9.3, +7.0] p=1 | -7.0 [-17.4, +3.5] p=1 | 91.9/91.9/87.2 |
| gpt-oss:120b | privacyalign | told(modified) | coarser | 79 | 77.2 | 82.3 | 83.5 | -5.1 [-13.9, +3.8] p=1 | -6.3 [-16.5, +3.8] p=1 | 96.2/92.4/86.1 |
| gpt-oss:120b | privacylens_leak | untold(published) | explicit_refusal | 86 | 89.5 | 36.0 | 86.0 | +53.5 [+41.9, +65.1] p=0 | +3.5 [-4.7, +11.6] p=1 |  |
| gpt-oss:120b | privacylens_leak | untold(published) | coarser | 79 | 68.4 | 36.7 | 84.8 | +31.6 [+20.2, +43.0] p=0.0002 | -16.5 [-26.6, -6.3] p=0.434 |  |
| gpt-oss:120b | privacylens_leak | told(modified) | explicit_refusal | 86 | 91.9 | 67.4 | 83.7 | +24.4 [+12.8, +36.0] p=0.0211 | +8.1 [+0.0, +16.3] p=1 |  |
| gpt-oss:120b | privacylens_leak | told(modified) | coarser | 79 | 81.0 | 67.1 | 83.5 | +13.9 [+1.3, +26.6] p=1 | -2.5 [-13.9, +8.9] p=1 |  |
| glm-5.3-flash | converse | told(published) | explicit_refusal | 86 | 88.4 | 96.5 | 82.6 | -8.1 [-15.1, -2.3] p=1 | +5.8 [-3.5, +15.1] p=1 |  |
| glm-5.3-flash | converse | told(published) | coarser | 79 | 88.6 | 96.2 | 81.0 | -7.6 [-15.2, -1.3] p=1 | +7.6 [-1.3, +16.5] p=1 |  |
| glm-5.3-flash | converse | untold(modified) | explicit_refusal | 86 | 94.2 | 89.5 | 91.9 | +4.7 [-2.3, +11.6] p=1 | +2.3 [-3.5, +8.1] p=1 |  |
| glm-5.3-flash | converse | untold(modified) | coarser | 79 | 94.9 | 88.6 | 91.1 | +6.3 [-1.3, +13.9] p=1 | +3.8 [+0.0, +8.9] p=1 |  |
| glm-5.3-flash | privacyalign | untold(published) | explicit_refusal | 86 | 75.6 | 54.7 | 66.3 | +20.9 [+9.3, +32.6] p=0.0949 | +9.3 [+0.0, +19.8] p=1 | 23.3/40.7/47.7 |
| glm-5.3-flash | privacyalign | untold(published) | coarser | 79 | 64.6 | 55.7 | 67.1 | +8.9 [-1.3, +19.0] p=1 | -2.5 [-13.9, +8.9] p=1 | 38.0/39.2/49.4 |
| glm-5.3-flash | privacyalign | told(modified) | explicit_refusal | 86 | 76.7 | 75.6 | 64.0 | +1.2 [-5.8, +8.1] p=1 | +12.8 [+5.8, +20.9] p=0.338 | 75.6/12.8/68.6 |
| glm-5.3-flash | privacyalign | told(modified) | coarser | 79 | 74.7 | 77.2 | 65.8 | -2.5 [-10.1, +5.1] p=1 | +8.9 [+0.0, +19.0] p=1 | 31.6/13.9/69.6 |
| glm-5.3-flash | privacylens_leak | untold(published) | explicit_refusal | 86 | 95.3 | 45.3 | 94.2 | +50.0 [+38.4, +61.6] p=0 | +1.2 [-3.5, +5.8] p=1 |  |
| glm-5.3-flash | privacylens_leak | untold(published) | coarser | 79 | 69.6 | 45.6 | 93.7 | +24.1 [+11.4, +36.7] p=0.0931 | -24.1 [-35.4, -13.9] p=0.0024 |  |
| glm-5.3-flash | privacylens_leak | told(modified) | explicit_refusal | 86 | 100.0 | 100.0 | 100.0 | +0.0 [+0.0, +0.0] p=1 | +0.0 [+0.0, +0.0] p=1 |  |
| glm-5.3-flash | privacylens_leak | told(modified) | coarser | 79 | 100.0 | 100.0 | 100.0 | +0.0 [+0.0, +0.0] p=1 | +0.0 [+0.0, +0.0] p=1 |  |
| luna | converse | told(published) | explicit_refusal | 86 | 48.8 | 91.9 | 51.2 | -43.0 [-53.5, -32.6] p=0 | -2.3 [-13.9, +9.3] p=1 |  |
| luna | converse | told(published) | coarser | 79 | 44.3 | 91.1 | 48.1 | -46.8 [-58.2, -35.4] p=0 | -3.8 [-19.0, +11.4] p=1 |  |
| luna | converse | untold(modified) | explicit_refusal | 86 | 79.1 | 80.2 | 70.9 | -1.2 [-10.5, +8.1] p=1 | +8.1 [-2.3, +18.6] p=1 |  |
| luna | converse | untold(modified) | coarser | 79 | 78.5 | 79.7 | 68.4 | -1.3 [-12.7, +10.1] p=1 | +10.1 [-1.3, +21.5] p=1 |  |
| luna | privacyalign | untold(published) | explicit_refusal | 86 | 51.2 | 52.3 | 55.8 | -1.2 [-12.8, +10.5] p=1 | -4.7 [-13.9, +4.7] p=1 | 87.2/88.4/83.7 |
| luna | privacyalign | untold(published) | coarser | 79 | 59.5 | 53.2 | 57.0 | +6.3 [-3.8, +17.7] p=1 | +2.5 [-7.6, +12.7] p=1 | 87.3/89.9/83.5 |
| luna | privacyalign | told(modified) | explicit_refusal | 86 | 41.9 | 43.0 | 39.5 | -1.2 [-8.1, +5.8] p=1 | +2.3 [-3.5, +8.1] p=1 | 86.0/65.1/84.9 |
| luna | privacyalign | told(modified) | coarser | 79 | 38.0 | 44.3 | 40.5 | -6.3 [-12.7, -1.3] p=1 | -2.5 [-10.1, +5.1] p=1 | 69.6/65.8/86.1 |
| luna | privacylens_leak | untold(published) | explicit_refusal | 86 | 91.9 | 29.1 | 93.0 | +62.8 [+52.3, +73.3] p=0 | -1.2 [-5.8, +2.3] p=1 |  |
| luna | privacylens_leak | untold(published) | coarser | 79 | 51.9 | 29.1 | 92.4 | +22.8 [+12.7, +32.9] p=0.0134 | -40.5 [-51.9, -29.1] p=0 |  |
| luna | privacylens_leak | told(modified) | explicit_refusal | 86 | 96.5 | 98.8 | 95.3 | -2.3 [-7.0, +2.3] p=1 | +1.2 [+0.0, +3.5] p=1 |  |
| luna | privacylens_leak | told(modified) | coarser | 79 | 96.2 | 98.7 | 94.9 | -2.5 [-7.6, +2.5] p=1 | +1.3 [-5.1, +7.6] p=1 |  |
