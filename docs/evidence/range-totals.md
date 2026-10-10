# Range totals

Source: rolling back-test predictions of `twin_daily`, 8 origins (2024-07 → 2025-02, 6-month horizon), segment totals; consecutive non-overlapping ranges inside each test window. Exploratory.

| Range | WAPE DOM | WAPE INTL | Direction vs previous range DOM / INTL | Error of the % change DOM / INTL (pp) |
| --- | ---: | ---: | --- | --- |
| 1 day | 6.5 | 3.8 | 87% / 78% | 3.5 / 2.0 |
| 7 days | 5.5 | 3.2 | 85% / 90% | 2.9 / 3.0 |
| 14 days | 5.3 | 2.7 | 90% / 94% | 4.0 / 2.9 |
| 28 days | 4.8 | 2.3 | 95% / 100% | 5.3 / 2.3 |

| Finding |
| --- |
| Range totals are 20 to 30% more accurate than days, not √n: daily errors are autocorrelated ([noise](noise.md)) |
| Direction over 2-week ranges is right about 90% of the time; the size of the change is off by about 3 to 4 pp; a stated change of X% is reliable when \|X\| is at least about 8% |
| Smearing (mean instead of median) changes daily WMAPE by < 0.1 pp and the 14-day range error by ≤ 0.02 |
