# Vertical-slice probe

Source: an independent implementation built from the model docs (panel → kernel + calendar → back-test → test predictions); local branch, not merged. Reference folds as [component order](component-order.md), with w₀ ≤ 1 and c ≥ 0 and box-shaped event windows. WAPE %.

| Spec | DOM (2024 / 2025 → mean) | INTL (2024 / 2025 → mean) | Component order |
| --- | --- | --- | --- |
| Seasonal naive 364 | 16.07 / 16.54 → 16.31 | 24.80 / 12.39 → 18.59 | 16.3 / 18.6 |
| Calendar only | 11.14 / 12.10 → 11.62 | 7.53 / 15.79 → 11.66 | 11.3 / 11.2 |
| Kernel only | 8.09 / 8.22 → 8.15 | 5.96 / 6.31 → 6.13 | 8.1 / 6.1 |
| Joint | 3.69 / 5.63 → 4.66 | 3.79 / 4.33 → 4.06 | 4.9 / 4.7 |
| Joint, 13 monthly rolling origins 2024-02 → 2025-02, 6-month horizon | 4.75 (naive 18.8) | 5.23 (naive 19.3) | n/a |

| Finding |
| --- |
| Baselines reproduce within 0.4 points |
| The joint spec included a centred slope for both series; on the test split the slope added +10.7% international, −6.1% domestic ([slope and events](slope-and-events.md) separates it) |
| Events failed the drop-one gate (+0.06 / +0.07 points) on the February to July folds, which contain Ramadan and both Eids but no National Day or Christmas to New Year |
