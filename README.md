# ChallengeON DCT analytics lake

This repository keeps the supplied Excel workbooks unchanged and builds a small analytical lake from them:

- `lake/curated/guest_daily.parquet`: unified domestic and international train/test records.
- `lake/curated/flight_daily.parquet`: typed daily flight operations records.
- `lake/analytics.duckdb`: local query database with curated tables and convenience views.
- `lake/manifest.json`: source hashes, row counts, validation results, and semantic notes.

## Build

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_lake.py
```

The build is repeatable and replaces generated lake outputs while leaving the source workbooks untouched.

## Query

Run a query through the included helper:

```bash
.venv/bin/python scripts/query_lake.py \
  "SELECT date, guests, total_pax FROM guest_flight_daily ORDER BY date DESC LIMIT 10"
```

Or connect any DuckDB-compatible client to `lake/analytics.duckdb`. Example queries are in `sql/example_queries.sql`.

## Tables and views

| Name | Type | Description |
| --- | --- | --- |
| `guest_daily` | Table | Domestic and international guest observations and prediction rows |
| `flight_daily` | Table | Daily route and airline operating metrics |
| `guest_actuals` | View | Guest rows where the target is available |
| `guest_prediction_rows` | View | Guest rows where the target must be predicted |
| `guest_daily_totals` | View | Daily guest totals without nationality-level duplication |
| `flight_daily_totals` | View | Daily passenger, capacity, and weighted load-factor totals |
| `guest_flight_daily` | View | Safe daily join of aggregated guest and flight measures |

## Data semantics

- Missing `same_day_guests` values remain `NULL`. The data dictionary uses the original asterisk for several meanings, including suppressed or unavailable values, so replacing it with zero would discard information.
- The flight workbook is modeled at daily grain because its dates are daily from 2023 onward. The supplied data dictionary describes it as monthly, which does not match the file.
- `analytics.duckdb` is generated and intentionally ignored by Git. The curated Parquet files and manifest are portable source-of-truth outputs.
