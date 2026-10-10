# Implementation checks

Source: analysis runs (outside the repository) and repository issues.

| Check | Finding |
| --- | --- |
| Integer-coded categoricals | Holiday and encoding fixes cut ridge MAE 3,137 → 2,623 |
| Kernel matrix | `triu(ones).T` gives a non-decreasing kernel; `triu(ones)` gives the non-increasing one |
| Unconstrained w₀ | An unconstrained fit gave w₀ = 1.15 |
| Constant base stock | A constant c cannot drop in Ramadan; domestic keeps a −11.5% Ramadan residual after the kernel |
| Weekly spikes in w | Spikes in an unconstrained kernel follow the weekday pattern |
| Pooled metrics | Raw-scale pooled metrics are dominated by domestic (MAE 17,485 vs 2,466) |
| Domestic convergence (issue #13) | With the kernel fitted on the raw scale and every other block on log-scale SSE, the shared objective rose on 33 of 119 block steps and cycled; with the log refinement, domestic results are identical at caps 20, 50, 200 and 1,000 |
| Neural networks | MLPs in `model_baselines.py` were often worse than the seasonal naive; about 1,300 daily rows per series |
