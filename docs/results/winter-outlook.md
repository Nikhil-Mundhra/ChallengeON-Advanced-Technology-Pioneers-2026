# Winter outlook

Method: [winter outlook](../model/outlook.md).

Source: `output/outlook.json` (`twin outlook`; not committed).

| Scenario | Winter 2026/27 vs the model's 2025/26 estimate | Same method back-tested on winter 2024/25 (December to January) |
| --- | ---: | ---: |
| `flat` arrivals | +0.2% | −8.9% |
| `trend` arrivals | +7.7% | +29.1% |

Source: `outlook.json` in the web bundle (`twin export`, version 20261012-072949-beeab0f; `bands`, TOTAL); `twin outlook --monthly` at 18dc501 reproduces it and writes `output/outlook_monthly.json` (not committed). Monthly outlook back-test, 17 month-end origins August 2023 to December 2024, TOTAL monthly guests. Bias: prediction − actual over actual.

| Horizon (months) | Origins (n) | `flat` WAPE | `flat` bias | `trend` WAPE | `trend` bias |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 17 | 11.9% | −11.9% | 12.4% | +12.4% |
| 3 | 15 | 11.6% | −11.6% | 20.2% | +20.2% |
| 6 | 12 | 11.6% | −11.6% | 29.2% | +29.2% |
| 9 | 9 | 11.4% | −11.4% | 38.1% | +38.1% |
| 12 | 6 | 10.3% | −10.3% | 56.4% | +56.4% |

Source: the same `outlook.json` (`scenarios.flat.TOTAL`, `band`). Default scenario `flat`; data ends 2026-02-28.

| Month | Horizon | Raw projection | Calibrated | Range (10th to 90th percentile miss) | Origins behind the band |
| --- | ---: | ---: | ---: | --- | ---: |
| November 2026 | 9 | 1,290,233 | 1,460,352 | 1,366,192 to 1,546,319 | 9 |

The nine origins at horizon 9 overlap and all fall in the 2023/24 recovery; the site shows `INTERNATIONAL` and `DOMESTIC` uncorrected ([outlook](../model/outlook.md)).
