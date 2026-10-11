# Coupling of flights, arrivals and guests

## Question

Before modelling: how do seats, P2P passengers, new arrivals and guests move together once time (trend and season) is taken out, and at which lag?

## Method

Weekly market series, 20 international markets, complete weeks from 2023-01-02 to 2025-07 (train split). Seats and P2P come from `flight_daily` (departure country mapped to market); arrivals (`new_arrivals_filled`) and guests from `daily_market_panel.parquet`. On log values per market and series: trend = centred 13-week mean; season = week-of-year mean of the detrended series; residual = the rest. Descriptive only; nothing is fitted out of sample.

Run (needs the built lake; `daily_market_panel.parquet` is not committed):

```console
$ PYTHONPATH=src python experiment/eda_coupling/prep.py
$ python experiment/eda_coupling/plots.py
```

Charts go to `experiment/eda_coupling/out/` (gitignored).

## Results

Share of variance of the log series explained by time, median over markets:

| Series | Trend | Season | Left after time |
| --- | ---: | ---: | ---: |
| Seats | 0.88 | 0.04 | 0.05 |
| P2P passengers | 0.53 | 0.25 | 0.13 |
| New arrivals | 0.52 | 0.29 | 0.13 |
| Guests | 0.51 | 0.29 | 0.12 |

With 2.5 years of data the week-of-year season rests on 2 or 3 values per week, so it overstates the time share.

Residual coupling, pooled market-weeks (n = 2,432):

| Link | Slope | Correlation |
| --- | ---: | ---: |
| Seats to P2P | 1.19 | 0.52 |
| P2P to arrivals | 0.66 | 0.54 |
| Arrivals to guests | 0.78 | 0.91 |
| Seats to guests | 0.47 | 0.19 |

Lead and lag of the residuals (median correlation over markets): every link peaks at lag 0 weeks, with a smaller value at +1 week. Seats never lead guests by more than a week.

Trend against trend (52-week change of the 13-week trend): guests on seats slope 0.56, correlation 0.67. This is association, not effect.

## Conclusion

Seats are almost all slow trend. After time is removed, seats explain about 4% of the remaining guest variance (correlation 0.19). The signal is lost at seats to P2P and P2P to arrivals; arrivals to guests is strong. A planning model that knows only scheduled seats cannot do much better than a good time model plus a modest seat response, which is what `experiment/scenario_response/` measures.
