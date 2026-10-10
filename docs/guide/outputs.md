# Outputs

## Prediction files

`twin predict` writes to `output/predictions/` (`TWIN_OUTPUT_DIR/predictions`).

| File | Rows | Columns |
| :--- | :---: | :--- |
| `domestic_test_guests.csv` | 212 | `Date`, `New Arrivals`, `Same-Day Guests`, `Residence (groups)`, `Guests` |
| `international_test_guests.csv` | 9,202 | `Date`, `New Arrivals`, `Same-Day Guests`, `Nationality`, `Residence (groups)`, `Guests` |
| `test_guests_intervals.csv` | 9,414 | `Date`, `Nationality` (empty for domestic), `Residence (groups)`, `Guests_p10`, `Guests_p50`, `Guests_p90`; international rows first; `Guests_p50` equals `Guests`; not written with `--no-intervals` |
| `test_total_guests.csv` | 212 | `Date`, `Guests_total`, `Guests_total_p10`, `Guests_total_p90` (the total's own 80% interval; empty bounds with `--no-intervals`) |
| `nowcast_serving.json` | n/a | Daily predictions per market, `INTERNATIONAL` and `TOTAL`, recent actual guests, AR(1) parameters, nationality predictions; not written with `--no-intervals` |
| `market_outputs.json` | n/a | Per-market weekly outputs; not written with `--no-intervals` |
| `test_predictions.png` | n/a | One panel per market: last 365 training days, test predictions, 80% band |

The CSVs are the test workbooks row for row with `Guests` appended. `Guests` is the model median on the original scale, floored at max(New Arrivals, 10): every training row has Guests ≥ New Arrivals (59,668 rows) and Guests ≥ 10, and the test file keeps rows with New Arrivals ≥ 10.

## market_outputs.json

```text
spec, coverage, assumptions[]
markets.<MARKET>:
  weeks[]:
    week_start               Monday; full Monday to Sunday test weeks only
    forecast                 sum of daily predicted guests (guest-nights)
    p10, p90                 NoiseModel.range_interval over the week
    direction                "increase" / "decrease" to the next week; null for the last week
    direction_prob           probability of that direction
    yoy_change               forecast ÷ actual guests of the week 364 days earlier − 1 (null if not in training)
    top_drivers[]            blocks other than flow, ≥ 0.5%, by |mean log contribution|: {block, effect_pct}
direction_backtest:
  weeks_scored               distinct market-weeks, each from the earliest origin that forecasts it
  accuracy.{model, arrivals_direction, same_direction_as_last_year, majority_direction}
  direction_prob_reliability[]  per probability range: weeks, mean_prob, share_right
  weekly_band_coverage       share of back-test weeks inside p10 to p90
```

| Fact |
| --- |
| `time` block (season, weekday, domestic slope held at its last training value) is relative to the training average; `holiday` to a day outside every event window |
| The model sees each test week's observed new arrivals; direction accuracy is nowcast skill; `arrivals_direction` is the sign of the change in new arrivals |
| `direction_prob_reliability` and `weekly_band_coverage` are in-sample for the error model; `assumptions` states this |

## validation_summary.json

`twin validate` back-tests `naive_364`, `arrivals_ratio`, `time_only`, `flow_only`, `flow_time`, `twin_daily` on `VALIDATION_ORIGINS`.

```text
protocol, folds
segment_wape:   grain, values.<spec>.{domestic,international}
compare:        grain, rows[]   twin_daily against naive_364, time_only and flow_time per segment
nationalities:  pooled-nationality and recency results, each with its commit
```

## outlook.json

```text
window, start, end, spec, guests_known_to, arrivals_known_to
previous:                  the same model one year earlier, from its actual arrivals
  window, guest_nights, months[].{month, guest_nights}
scenarios.{flat,trend}:
  guest_nights, change_pct           change vs previous.guest_nights
  domestic_share_pct
  top_source_markets[]               top 5 international markets, OTHER_* excluded: {market, share_pct}
  months[].{month, guest_nights, change_pct}
  arrivals_growth.<MARKET>           growth factor used
backtest[]:
  window, scenario, segment (total, international, domestic), train_end, arrivals_end,
  season_error_pct, daily_wape_pct
```

The console prints the previous total, each scenario's total and change, and the back-test season errors.
