# Panels

## Panels

| Panel | Command | Grain | Contract |
| --- | --- | --- | --- |
| `weekly_market_panel.parquet` | `twin build-panel` | Market × Monday to Sunday week × split; 3,507 rows, 39 columns, week starts 2022-12-26 to 2026-02-23 | Flights and guests matched by date and market before weekly aggregation; weeks crossing the train/test boundary are split; `is_complete_week`, `is_complete_guest_inputs` flags; `load_factor_raw` unclipped with `is_load_factor_outlier`, `load_factor` clipped to [0, 1] |
| `daily_market_panel.parquet` (not committed) | `twin build-daily-panel [--max-lag K]` | Market × day, both splits; 31,920 rows (21 × 1,520) | See below |

Daily panel:

| Item | Fact |
| --- | --- |
| Lags | `arrivals_lag_0..K` (default K = 21) over the concatenated train and test series; the first test days take lags from the last train days; `lag_complete` marks a full lag window |
| Absent test rows | The test file keeps rows with New Arrivals ≥ 10 only. A test nationality-day absent from it (338 rows, mostly Finland, Norway, Denmark, Mexico, Azerbaijan) gets the nationality's mean training arrivals on days below 10 (4.5 to 6.1; 5.4 overall), counted in `n_arrivals_below_threshold` |
| Other gaps | Other suppressed or absent arrivals are linearly interpolated within each nationality's series into `new_arrivals_filled` (`n_arrivals_interpolated`, `n_absent_records`); training absences: 238 rows |
| Reconciliation | Observed `new_arrivals` leaves gaps missing; weekly sums of daily `guests` and `new_arrivals` equal the weekly panel exactly (tested) |
| Use | Input of the daily nowcast; `twin predict` and the back-test build it in memory from `guest_daily.parquet` |

## Markets

21 markets: the top 15 nationalities by training guest volume, 5 regional clusters (`OTHER_EUROPE`, `OTHER_ASIA_PACIFIC`, `OTHER_MENA`, `OTHER_AMERICAS_AFRICA`, `OTHER_EURASIA`) and `DOMESTIC`. Cluster membership: `src/tourism_twin/domain/markets.py`. Both panels use one SQL market mapping (`build_market_case`).

## Derived columns

| Fact |
| --- |
| Ratios, flags, calendar fields, archetype and arrival lags are defined once in `src/tourism_twin/features/` and resolved by `FeatureRegistry` in dependency order |
| Ratios are computed from summed parts at the panel's grain |
| Both panel builders read the lake through `LakeRepository` (`data/repository.py`) |
| The weekly panel's SQL runs on in-memory DuckDB views over the curated Parquet; `twin build-panel` does not need `lake/analytics.duckdb` |
| The weekly planning model reads `weekly_market_panel.parquet` |

## Feature contract

A feature table delivered by an analysis joins the daily panel without reshaping:

| date | market | `<feature_1>` | `<feature_2>` | ... |
| --- | --- | --- | --- | --- |
| 2023-01-01 | DOMESTIC | 1240 | 0.12 | |
| 2026-02-28 | UZBEKISTAN | 57 | NaN | |

| Column | Contract |
| --- | --- |
| `date` | Daily, `YYYY-MM-DD`, 2023-01-01 to 2026-02-28, test period included |
| `market` | `DOMESTIC` or the nationality as in the guest workbooks (uppercase); a feature that does not vary by market uses `ALL`; departure-country features are mapped to nationality and the mapping is marked approximate |
| features | One column each, raw values (no scaling, one-hot or log); missing stays NaN; imputed values get a `<col>_imputed` flag; nothing derived from `Guests`; the value for date t uses data from t or earlier |
| description | Each feature once: kind (count, ratio 0 to 1, continuous, categorical, flag), unit, range, meaning of missing |

Inside `src/`, such a feature becomes a `@PANEL_FEATURES.feature` spec.
