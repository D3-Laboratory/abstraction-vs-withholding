# v27b coarser branch: 4-variant paired comparison (test cases, 9 cases x 3 seeds)

| variant | n | final match | oracle offered | item assump. eps | rating (n) | completed |
|---|---|---|---|---|---|---|
| raw | 27 | 15/27 | 17/27 | 18/27 (item_use) | 8.46 (27) | 27/27 |
| allowed | 27 | 12/27 | 15/27 | 15/27 (item_substitution) | 8.28 (27) | 27/27 |
| coarser | 27 | 6/27 | 13/27 | 24/27 (item_substitution) | 7.96 (27) | 27/27 |
| refuse | 27 | 3/27 | 8/27 | 27/27 (item_substitution) | 7.89 (26) | 27/27 |

| A vs B | A match, B miss | A miss, B match | tie | pairs |
|---|---|---|---|---|
| raw vs allowed | 6 | 3 | 18 | 27 |
| raw vs coarser | 11 | 2 | 14 | 27 |
| raw vs refuse | 13 | 1 | 13 | 27 |
| allowed vs coarser | 7 | 1 | 19 | 27 |
| allowed vs refuse | 11 | 2 | 14 | 27 |
| coarser vs refuse | 5 | 2 | 20 | 27 |

Per case, final match by seed s0 s1 s2:

| case | raw | allowed | coarser | refuse |
|---|---|---|---|---|
| insurance.persona1.activity_risk_profile.06 | 111 | 111 | 000 | 000 |
| insurance.persona2.mental_health_service_usage.20 | 011 | 011 | 110 | 000 |
| insurance.persona2.travel_patterns.13 | 000 | 100 | 000 | 000 |
| insurance.persona4.health_considerations.07 | 000 | 000 | 000 | 000 |
| insurance.persona4.professional_equipment_and_business_assets.22 | 111 | 111 | 011 | 000 |
| insurance.persona4.travel_patterns.15 | 000 | 001 | 001 | 010 |
| real_estate.persona1.home_office_requirements.13 | 010 | 110 | 010 | 010 |
| real_estate.persona1.smart_home_technology_interest.12 | 111 | 000 | 000 | 100 |
| travel_planning.persona4.activity_preferences.17 | 111 | 000 | 000 | 000 |
