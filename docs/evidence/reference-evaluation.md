# Reference evaluation

A fixed procedure with fixed hyperparameters. Its results: [component order](component-order.md), [vertical-slice probe](vertical-slice-probe.md), [slope and events](slope-and-events.md).

| Item | Specification |
| --- | --- |
| Series | `DOMESTIC`, and the international total = sum of the 20 non-domestic daily-panel markets (lags summed per day) |
| Arrivals input | `new_arrivals_filled` |
| Training rows | date ≥ 2023-01-01, `lag_complete`, `guests` not null; 2022 guests unused |
| Folds | Test 2024-02-01 → 2024-07-31 (train before 2024-02-01) and test 2025-02-01 → 2025-07-31 (train before 2025-02-01); each fold and the mean |
| Hyperparameters | K = 21, H = 4, ridge α = 1 |
| Kernel | `flow = c + Σ_{k=0..21} w_k·A_{t−k}`, `w = triu(ones) @ d`, `d ≥ 0`, `w_0 ≤ 1`, `c ≥ 0`; fitted on Guests / m in raw scale, rows weighted by m (minimise Σ(G − m·flow)²); `w_0 ≤ 1` exact (bounded solve when it binds) |
| Calendar (log) | Fourier on day of year / 365.25, H = 4; day of week one-hot (Monday reference); event windows as 0/1 boxes: Ramadan (first day − 5 → day before the Eid al-Fitr window), Eid al-Fitr and Eid al-Adha (−1 → +3), National Day (30 Nov → 4 Dec), Christmas to New Year (22 Dec → 7 Jan). The boxes differ from the `domain/events.csv` windows of `EventKernel`. Ridge α = 1 on the raw centred columns (scikit-learn `Ridge` convention); level owner and slope unpenalised. Periodic terms and event boxes centred on the training rows |
| Per-series terms | DOMESTIC: + centred log-slope (years since 2023-01-01), no events. INTERNATIONAL: events, no slope |
| Fit | Backfitting: kernel on Guests / m, calendar on log(Guests / flow), until the largest change in any log contribution < 1e-6 |
| Metric | WAPE = Σ\|actual − predicted\| / Σ actual, per series and fold |
| Not inputs | Same-day guests; anything derived from `Guests` |

Expected values (WAPE %):

| Spec | Reference folds | Rolling-13 |
| --- | ---: | ---: |
| DOMESTIC, per-series spec | 4.72 | 4.65 |
| INTERNATIONAL, per-series spec | 4.92 | 5.11 |
| Same spec for both, no slope, with events: DOMESTIC / INTERNATIONAL | 5.10 / 4.92 | n/a |
| Seasonal naive DOMESTIC / INTERNATIONAL | 16.3 / 18.6 | n/a |
| Calendar only (with trend) | about 11.6 | n/a |
| Kernel only DOMESTIC / INTERNATIONAL | 8.1 / 6.1 | n/a |
