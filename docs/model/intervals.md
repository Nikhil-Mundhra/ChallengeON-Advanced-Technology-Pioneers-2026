# Intervals

## Noise model (`models/noise.py`)

Fitted per series on the log errors e = log(actual) − log(pred) of the spec's rolling-origin back-test. Along the horizon h (days from the origin, h = 0 the first day), e_h = φ e_{h−1} + η_h with first-day variance v₀:

```text
var(h) = v₀ φ^(2h) + σ_η² (1 − φ^(2h)) / (1 − φ²)
bounds = pred × exp(± z · sqrt(var(h))),   z = Φ⁻¹(0.9) for 80%
```

| Fact |
| --- |
| `twin predict` fits it on 8 monthly origins (2024-07-01 to 2025-02-01) with a 7-month horizon and counts h from 2025-08-01 |
| No month or bias factor |
| Daily predictions only; the weekly simulator uses conformal margins and Monte Carlo ([planning](planning.md)) |

## Sums

| Fact |
| --- |
| A sum over days (week, any date range) uses the AR(1) covariance cov(eᵢ, eⱼ) = φ^\|hᵢ−hⱼ\| · var(min(hᵢ, hⱼ)); the sum's log error is the prediction-weighted mean of the daily ones (`NoiseModel.range_interval`, `weighted_sd`) |
| The daily total over all markets (`test_total_guests.csv`) has its own error series, `TOTAL`, fitted on back-test predictions summed per fold and day; `INTERNATIONAL` likewise |
| `NowcastService` serves any [A, B] range with `range_interval` (`/api/nowcast/range`) |
| Pooled-market nationalities take intervals from their own model's back-test errors per nationality ([nationalities](nationalities.md)) |

Coverage: [nowcast validation](../results/nowcast-validation.md#intervals).
