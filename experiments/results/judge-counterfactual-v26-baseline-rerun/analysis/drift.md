# Drift check: v25 labels vs same-day rerun (allowed_form, ignored)

diff = rerun minus v25, percentage points, paired. Holm over 64 McNemar tests.

| model | judge | cond | version | n | prompt same | fav agree% | fav% v25 | fav% rerun | diff [95% CI] | McNemar p (Holm) | omit agree% | omit% v25/rerun | omit diff [CI] (Holm) | level agree% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepseek-v4.1-flash | converse | told(published) | allowed_form | 86 | 86 | 93.0 | 90.7 | 93.0 | +2.3 [-3.5, +8.1] | 0.688 (1) |  |  |  | 93.0 |
| deepseek-v4.1-flash | converse | told(published) | ignored | 86 | 86 | 66.3 | 37.2 | 43.0 | +5.8 [-7.0, +18.6] | 0.458 (1) |  |  |  | 61.6 |
| deepseek-v4.1-flash | converse | untold(modified) | allowed_form | 86 | 86 | 91.9 | 75.6 | 79.1 | +3.5 [-2.3, +9.3] | 0.453 (1) |  |  |  | 90.7 |
| deepseek-v4.1-flash | converse | untold(modified) | ignored | 86 | 86 | 79.1 | 69.8 | 79.1 | +9.3 [+0.0, +18.6] | 0.0963 (1) |  |  |  | 77.9 |
| deepseek-v4.1-flash | privacyalign | untold(published) | allowed_form | 86 | 86 | 86.0 | 29.1 | 40.7 | +11.6 [+4.7, +19.8] | 0.00635 (0.387) | 89.5 | 17.4/25.6 | +8.1 [+2.3, +15.1] (1) |  |
| deepseek-v4.1-flash | privacyalign | untold(published) | ignored | 86 | 86 | 90.7 | 52.3 | 54.7 | +2.3 [-3.5, +9.3] | 0.727 (1) | 82.6 | 20.9/33.7 | +12.8 [+4.7, +20.9] (0.443) |  |
| deepseek-v4.1-flash | privacyalign | told(modified) | allowed_form | 86 | 86 | 94.2 | 38.4 | 41.9 | +3.5 [-1.2, +9.3] | 0.375 (1) | 93.0 | 7.0/11.6 | +4.7 [+0.0, +10.5] (1) |  |
| deepseek-v4.1-flash | privacyalign | told(modified) | ignored | 86 | 86 | 95.3 | 40.7 | 40.7 | +0.0 [-4.7, +4.7] | 1 (1) | 89.5 | 32.6/38.4 | +5.8 [-1.2, +12.8] (1) |  |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | allowed_form | 86 | 86 | 70.9 | 20.9 | 31.4 | +10.5 [-1.2, +20.9] | 0.108 (1) |  |  |  |  |
| deepseek-v4.1-flash | privacylens_leak | untold(published) | ignored | 86 | 86 | 74.4 | 66.3 | 82.6 | +16.3 [+5.8, +26.7] | 0.00434 (0.269) |  |  |  |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | allowed_form | 86 | 86 | 59.3 | 47.7 | 20.9 | -26.7 [-38.4, -13.9] | 0.000117 (0.0075) |  |  |  |  |
| deepseek-v4.1-flash | privacylens_leak | told(modified) | ignored | 86 | 86 | 62.8 | 51.2 | 65.1 | +13.9 [+1.2, +25.6] | 0.0501 (1) |  |  |  |  |
| gpt-oss:120b | converse | told(published) | allowed_form | 86 | 86 | 87.2 | 84.9 | 83.7 | -1.2 [-8.1, +7.0] | 1 (1) |  |  |  | 87.2 |
| gpt-oss:120b | converse | told(published) | ignored | 86 | 86 | 74.4 | 65.1 | 62.8 | -2.3 [-12.8, +8.1] | 0.832 (1) |  |  |  | 70.9 |
| gpt-oss:120b | converse | untold(modified) | allowed_form | 86 | 86 | 83.7 | 73.3 | 70.9 | -2.3 [-11.6, +5.8] | 0.791 (1) |  |  |  | 82.6 |
| gpt-oss:120b | converse | untold(modified) | ignored | 86 | 86 | 76.7 | 68.6 | 84.9 | +16.3 [+7.0, +25.6] | 0.00258 (0.162) |  |  |  | 75.6 |
| gpt-oss:120b | privacyalign | untold(published) | allowed_form | 86 | 86 | 88.4 | 87.2 | 89.5 | +2.3 [-4.7, +9.3] | 0.754 (1) | 93.0 | 96.5/96.5 | +0.0 [-5.8, +5.8] (1) |  |
| gpt-oss:120b | privacyalign | untold(published) | ignored | 86 | 86 | 83.7 | 81.4 | 79.1 | -2.3 [-10.5, +5.8] | 0.791 (1) | 89.5 | 94.2/88.4 | -5.8 [-12.8, +1.2] (1) |  |
| gpt-oss:120b | privacyalign | told(modified) | allowed_form | 86 | 86 | 79.1 | 77.9 | 82.6 | +4.7 [-4.7, +13.9] | 0.481 (1) | 93.0 | 91.9/94.2 | +2.3 [-3.5, +8.1] (1) |  |
| gpt-oss:120b | privacyalign | told(modified) | ignored | 86 | 86 | 83.7 | 83.7 | 83.7 | +0.0 [-8.1, +8.1] | 1 (1) | 90.7 | 87.2/91.9 | +4.7 [-1.2, +11.6] (1) |  |
| gpt-oss:120b | privacylens_leak | untold(published) | allowed_form | 86 | 86 | 82.6 | 36.0 | 41.9 | +5.8 [-3.5, +15.1] | 0.302 (1) |  |  |  |  |
| gpt-oss:120b | privacylens_leak | untold(published) | ignored | 86 | 86 | 88.4 | 86.0 | 86.0 | +0.0 [-7.0, +7.0] | 1 (1) |  |  |  |  |
| gpt-oss:120b | privacylens_leak | told(modified) | allowed_form | 86 | 86 | 69.8 | 67.4 | 83.7 | +16.3 [+4.7, +27.9] | 0.00936 (0.543) |  |  |  |  |
| gpt-oss:120b | privacylens_leak | told(modified) | ignored | 86 | 86 | 80.2 | 83.7 | 82.6 | -1.2 [-10.5, +8.1] | 1 (1) |  |  |  |  |
| glm-5.3-flash | converse | told(published) | allowed_form | 86 | 86 | 98.8 | 96.5 | 95.3 | -1.2 [-3.5, +0.0] | 1 (1) |  |  |  | 98.8 |
| glm-5.3-flash | converse | told(published) | ignored | 86 | 86 | 86.0 | 82.6 | 84.9 | +2.3 [-5.8, +10.5] | 0.774 (1) |  |  |  | 86.0 |
| glm-5.3-flash | converse | untold(modified) | allowed_form | 86 | 86 | 91.9 | 89.5 | 90.7 | +1.2 [-4.7, +7.0] | 1 (1) |  |  |  | 91.9 |
| glm-5.3-flash | converse | untold(modified) | ignored | 86 | 86 | 95.3 | 91.9 | 91.9 | +0.0 [-4.7, +4.7] | 1 (1) |  |  |  | 95.3 |
| glm-5.3-flash | privacyalign | untold(published) | allowed_form | 86 | 86 | 69.8 | 54.7 | 61.6 | +7.0 [-4.7, +18.6] | 0.327 (1) | 80.2 | 40.7/41.9 | +1.2 [-8.1, +10.5] (1) |  |
| glm-5.3-flash | privacyalign | untold(published) | ignored | 86 | 86 | 83.7 | 66.3 | 73.3 | +7.0 [-1.2, +15.1] | 0.18 (1) | 83.7 | 47.7/38.4 | -9.3 [-17.4, -1.2] (1) |  |
| glm-5.3-flash | privacyalign | told(modified) | allowed_form | 86 | 86 | 88.4 | 75.6 | 73.3 | -2.3 [-9.3, +4.7] | 0.754 (1) | 95.3 | 12.8/8.1 | -4.7 [-9.3, -1.2] (1) |  |
| glm-5.3-flash | privacyalign | told(modified) | ignored | 86 | 86 | 90.7 | 64.0 | 73.3 | +9.3 [+3.5, +16.3] | 0.00781 (0.461) | 82.6 | 68.6/74.4 | +5.8 [-2.3, +15.1] (1) |  |
| glm-5.3-flash | privacylens_leak | untold(published) | allowed_form | 86 | 86 | 86.0 | 45.3 | 38.4 | -7.0 [-15.1, +0.0] | 0.146 (1) |  |  |  |  |
| glm-5.3-flash | privacylens_leak | untold(published) | ignored | 86 | 86 | 95.3 | 94.2 | 94.2 | +0.0 [-4.7, +4.7] | 1 (1) |  |  |  |  |
| glm-5.3-flash | privacylens_leak | told(modified) | allowed_form | 86 | 86 | 98.8 | 100.0 | 98.8 | -1.2 [-3.5, +0.0] | 1 (1) |  |  |  |  |
| glm-5.3-flash | privacylens_leak | told(modified) | ignored | 86 | 86 | 98.8 | 100.0 | 98.8 | -1.2 [-3.5, +0.0] | 1 (1) |  |  |  |  |
| luna | converse | told(published) | allowed_form | 86 | 86 | 96.5 | 91.9 | 88.4 | -3.5 [-8.1, +0.0] | 0.25 (1) |  |  |  | 96.5 |
| luna | converse | told(published) | ignored | 86 | 86 | 83.7 | 51.2 | 48.8 | -2.3 [-11.6, +5.8] | 0.791 (1) |  |  |  | 81.4 |
| luna | converse | untold(modified) | allowed_form | 86 | 86 | 91.9 | 80.2 | 81.4 | +1.2 [-4.7, +7.0] | 1 (1) |  |  |  | 91.9 |
| luna | converse | untold(modified) | ignored | 86 | 86 | 82.6 | 70.9 | 72.1 | +1.2 [-8.1, +10.5] | 1 (1) |  |  |  | 81.4 |
| luna | privacyalign | untold(published) | allowed_form | 86 | 86 | 86.0 | 52.3 | 45.3 | -7.0 [-15.1, +0.0] | 0.146 (1) | 83.7 | 88.4/86.0 | -2.3 [-10.5, +5.8] (1) |  |
| luna | privacyalign | untold(published) | ignored | 86 | 86 | 81.4 | 55.8 | 62.8 | +7.0 [-2.3, +16.3] | 0.21 (1) | 83.7 | 83.7/86.0 | +2.3 [-5.8, +10.5] (1) |  |
| luna | privacyalign | told(modified) | allowed_form | 86 | 86 | 95.3 | 43.0 | 43.0 | +0.0 [-4.7, +4.7] | 1 (1) | 88.4 | 65.1/69.8 | +4.7 [-2.3, +11.6] (1) |  |
| luna | privacyalign | told(modified) | ignored | 86 | 86 | 90.7 | 39.5 | 44.2 | +4.7 [-1.2, +11.6] | 0.289 (1) | 87.2 | 84.9/83.7 | -1.2 [-8.1, +7.0] (1) |  |
| luna | privacylens_leak | untold(published) | allowed_form | 86 | 86 | 87.2 | 29.1 | 32.6 | +3.5 [-4.7, +10.5] | 0.549 (1) |  |  |  |  |
| luna | privacylens_leak | untold(published) | ignored | 86 | 86 | 97.7 | 93.0 | 93.0 | +0.0 [-3.5, +3.5] | 1 (1) |  |  |  |  |
| luna | privacylens_leak | told(modified) | allowed_form | 86 | 86 | 97.7 | 98.8 | 98.8 | +0.0 [-3.5, +3.5] | 1 (1) |  |  |  |  |
| luna | privacylens_leak | told(modified) | ignored | 86 | 86 | 96.5 | 95.3 | 98.8 | +3.5 [+0.0, +8.1] | 0.25 (1) |  |  |  |  |
