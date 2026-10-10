# Lake

## Source datasets

Read from `01a - DCT Dataset/` (organizer-provided, not redistributed; SHA-256 of each file in `lake/manifest.json`).

| Dataset | Grain and coverage | Fields | Use |
| --- | --- | --- | --- |
| International guests, train | Nationality-day, 2022-01-01 to 2025-07-31 | Guests, new arrivals, same-day guests | Nowcast training, calibration, back-tests |
| International guests, test | Nationality-day, 2025-08-01 to 2026-02-28 | New arrivals, same-day guests (Guests withheld) | Competition forecast inputs |
| Domestic guests, train and test | Day | Guests, new arrivals, same-day guests | Domestic nowcast; domestic planning prior |
| Flights | Route-airline-date, 2022 (monthly) and 2023-01-01 to 2026-02-28 (daily) | Seats, pax, P2P, transfer, transit, load factor, frequency, origin, airline | Structural chain |
| Data dictionary | 8-page PDF | Field definitions | Reference |

Data dictionary vs files: it documents the two test guest files and the flight file only, lists `Guests` in the test files (absent there), lists 6 international and 5 domestic columns (the files have 5 and 4) and calls the flight file monthly (daily from 2023).

## Build checks (`twin build-lake`)

| Check (`lake/manifest.json`) | Value |
| --- | --- |
| `guest_daily` rows (1,520 dates × 45 nationalities + domestic) | 69,920 |
| Source-present guest rows / absent grid rows | 69,344 / 576 |
| Present rows, train / test | 59,930 / 9,414 |
| Flight rows total / daily (2023+) / monthly (2022) | 117,608 / 116,395 / 1,213 |
| Flight rows with load factor > 100% (kept, flagged) | 9,896 |
| Duplicate candidate keys (guest, flight) | 0, 0 |
| Passenger identity mismatches (`Total PAX = P2P + Transfer + Transit`) | 0 |

`twin build-lake` aborts unless these are all 0: duplicate keys, train rows missing `Guests`, test rows with `Guests`, passenger identity mismatches, rows with `new_arrivals > guests`, negative guest or arrival counts; and load factor equals pax ÷ seats within 1e-9 (`data/validation.py`).

## Data assets

| File | Grain | Rows | Contents | Committed |
| --- | --- | --- | --- | --- |
| `lake/curated/guest_daily.parquet` | Nationality-day | 69,920 | 1,520 dates × (45 nationalities + domestic); presence and suppression flags | yes |
| `lake/curated/flight_daily.parquet` | Route-airline-day | 116,395 | Daily flights from 2023-01-01; load-factor outlier flag | yes |
| `lake/curated/flight_monthly.parquet` | Monthly | 1,213 | 2022 records on 12 month-start dates | no |
| `lake/curated/weekly_market_panel.parquet` | Market-week | 3,507 | 21 markets, both splits, 39 columns | yes |
| `lake/curated/daily_market_panel.parquet` | Market-day | 31,920 | 21 markets × 1,520 days, both splits, arrival lags 0 to 21 | no |
| `lake/curated/structural_calibration.json` | Market-season | 21 × 4 | Calibrated seats, load factor, P2P share, multiplier, stay factor | yes |
| `lake/curated/residual_engine.pkl` | Market | 21 models | RidgeCV residual models | yes |
| `lake/curated/conformal_calibrator.json` | Market | 21 | Conformal margins, target alpha 0.2, demonstrated coverage | yes |
| `lake/curated/evaluation_results.json` | n/a | n/a | Weekly back-test metrics, benchmark leaders, market and season breakdowns | yes |
| `lake/analytics.duckdb` | n/a | n/a | Query database with analytical views | no |
| `src/tourism_twin/domain/events.csv` | Event occurrence | 63 | Event, kind, anchor date, window offsets, scope, label, source; 2021 to 2027 | yes |

Example `twin query` SQL: `src/tourism_twin/data/sql/`.
