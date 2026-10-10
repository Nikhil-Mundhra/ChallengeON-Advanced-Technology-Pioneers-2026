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

Results: [winter outlook](../results/winter-outlook.md).
