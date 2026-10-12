# Winter outlook (`nowcast/outlook.py`)

`twin outlook [--winter Y]` predicts guests for December Y to February Y+1 (default 2026/27), after the test split; no arrivals are known for it.

| Part | Definition |
| --- | --- |
| Model | The chosen daily spec (default `twin_daily`) fitted on every training day (guests known to 2025-07-31) |
| Arrivals scenario | Each market's new arrivals on the same weekday 364 days earlier × growth, compounded per further year: `flat` 1.0; `trend` the market's arrivals over the last 365 known days ÷ the 365 days before |
| Calendar | Season, weekday and `domain/events.csv` windows of the predicted window |
| Events 2027 | The 2027 lunar dates in `events.csv` (Ramadan 1448, Eid al-Fitr 1448, Chinese New Year 2027) are labelled `(expected)`: unconfirmed |
| Comparison | The same model one year earlier, from that year's actual arrivals; the change is the model's own year-on-year change, not model minus actual |
| Back-test | The same procedure on the latest same-span window ≥ 2 years earlier that starts before the frozen test, cut at its start (for 2026/27: December 2024 to January 2025); empty if it would train on under 1 year of guests; guests and arrivals cut at the live distances before the window; season error % and daily WAPE per segment; a window overlapping the frozen test raises |
| Output | `output/outlook.json` ([outputs](../guide/outputs.md#outlookjson)); `twin report deck` reads it |

Monthly outlook: `twin outlook --monthly` and `twin export` (`outlook.json`, [web bundle](../architecture/web-bundle.md)).

| Part | Definition |
| --- | --- |
| Projection | Guests per month for the 12 months after the last known arrivals (to February 2027), per arrivals scenario (`flat`, `trend`, as above) and segment (`TOTAL`, `INTERNATIONAL`, `DOMESTIC`); the model is the one fitted on every training day, fitted once for both scenarios (`monthly_outlook`) |
| Back-test (`horizon_backtest`) | Every month-end origin from the first with 365 days of training guests to the last whose next month ends before the frozen test: arrivals known to the origin, guests to the live distance before it (212 days), each later whole month up to 12 ending before 2025-02-01; 17 origins, August 2023 to December 2024 |
| Error by horizon (`horizon_errors`) | Per scenario, segment and horizon in months: n, WAPE, bias (prediction − actual over actual), and the misses actual ÷ projection − 1 |
| Range | Projection × (1 + the 10th and 90th percentiles of the misses at that horizon) (`BAND_COVERAGE` 0.8) |
| Calibrated middle | Projection × (1 + the median miss at that horizon) |
| Default scenario | The scenario with the lower mean TOTAL WAPE over the horizons (`outlook.json` `default_scenario`) |
| Year earlier | The same month's actual guests, or the shipped nowcast's estimate where guests are withheld (`previous_kind`) |
| Site | The landing page shows the calibrated `TOTAL` with its range; `INTERNATIONAL` and `DOMESTIC` are the raw projections, marked uncorrected ([web app](../guide/web.md#pages)) |

| Caveat |
| --- |
| The origins overlap: a horizon's misses come from consecutive origins whose target months share most days |
| Every back-test origin falls in the 2023/24 recovery, when guests grew; every `flat` miss is positive and the correction raises the projection at every horizon |
| Horizons beyond 9 months rest on 8 or fewer origins |
| Segment projections carry no correction or range |

Results: [winter outlook](../results/winter-outlook.md).
