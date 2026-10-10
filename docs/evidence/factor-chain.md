# Factor chain and domestic history

Source: `analysis/factor_chain.py` (outside the repository) and repository back-tests.

## Flight-side links

33 matched countries, 2023-01 → 2025-07, calendar removed (month-of-year effects + trend per country), country-cluster bootstrap intervals.

| Link | Result | Status |
| --- | --- | --- |
| Passengers → transfer share | −0.07 per log PAX, CI [−0.15, +0.05] | Not supported |
| Transfer share → guests per arrival | −0.15 to −0.18 given arrivals; significant in 5 to 6 of 32 countries | Weak |
| Premium share → guests per arrival | Sign flips (−0.11 monthly, +0.20 weekly) | Not supported |
| P2P passengers → hotel New Arrivals | Elasticity 0.46 to 0.56, within-R² 0.27 to 0.35, positive in 31 to 33 of 33 | Supported, loose |
| Transfer or premium share in the guests forecast (2025 holdout) | Change ≤ 0.1 pp WAPE, intervals include 0; per-country fits diverge out of range | No gain |

Collinearity: condition number 9 to 12 across flight inputs (PAX vs seats r = 0.95); {arrivals, transfer share, premium share} about 1.5.

## Domestic training start

| Fact |
| --- |
| Domestic guests per arrival: 3.55 (2022Q1) → 2.5 (2022Q4) |
| Training from 2022-01, `CentredSlope` fits that drop as trend: origin 2023-08 → −8.6% bias (August to October 2023) |
| 19 rolling origins 2023-08 → 2025-02, 6-month horizon, mean / worst-fold WAPE: from 2022-01 5.72 / 7.91; from 2022-07 4.79 / 5.61; `Recency(180)` 4.94 / 6.58; `Recency(365)` 5.14 / 7.20 (exploratory: origins score months inside the frozen test) |
| On `VALIDATION_ORIGINS` training from 2022-01 wins ([nowcast validation](../results/nowcast-validation.md#shipped-choices)) |

## Date only vs nowcast

Single 3-month windows, WAPE domestic / international:

| Window | `time_only` | `twin_daily` |
| --- | --- | --- |
| August to October 2023 | 4.5 / 8.8 | 8.7 / 3.3 |
| August to October 2024 | 7.6 / 6.5 | 2.8 / 4.9 |
| February to April 2025 | 11.1 / 11.3 | 7.5 / 3.6 |
