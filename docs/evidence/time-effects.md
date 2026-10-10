# Time effects

Source: `seasonal_extract.py`, `seasonality_trig.py`, `ramadan_event_study.py`, `ramadan_conv_residual.py`, `event_detector.py` (analysis, outside the repository). Log scale; 2023 to 2025.

| Component | Finding |
| --- | --- |
| Level and trend | Linear fits best against a 365-day moving average; the level drifts: 90-day mean residual ±7% domestic, ±10% international; extrapolating the line overshot 2025 by about 20% |
| Annual season | Fourier H = 4 on day of year; shape stable across years; amplitude international ±25% (2023) and ±22% (2024), domestic ±8% and ±10% |
| Day of week | Domestic Fri +13%, Sat +23%, Sun −7% vs Mon; international ±5%; domestic lag-7 residual ACF 0.42 |
| Ramadan | Domestic −24%, international −18%; starts about 5 days before Ramadan; after the arrivals kernel: international +1.3% residual, domestic −11.5% |
| Eid al-Fitr, Eid al-Adha | Domestic +43 to 55% and +61 to 98% |
| Solar holidays | National Day +36 to 44%; Christmas to New Year international +41 to 43% for 12 to 17 days |
| One-off shocks | January 2022 international −29% for 28 days; wars (October 2023, April 2024, June 2025) produced no detectable window |
| Lunar dates | Move about 11 days earlier each year |

The test period contains National Day 2025, Christmas to New Year 2025/26 and the start of Ramadan 2026 (about 2026-02-18).
