# Open questions

## For the organizers

| # | Question |
| --- | --- |
| 1 | Are the 2022 flight records intended to be monthly and later records daily? |
| 2 | Does an absent nationality-day row mean zero guests or a missing report? (576 grid rows are absent; the dictionary does not say.) |
| 3 | Will room inventory, occupancy, events, aircraft type or schedule files be provided? |
| 4 | Is the competition forecast scored on international and domestic guests jointly or separately? |
| 5 | Is hotel `Guests` an end-of-day stock, a daily occupied-guest count, or another convention? |
| 6 | Should a new route be allocated to nationality markets by planner input, a comparable-market prior, or both? |

## Model

| Question | State |
| --- | --- |
| Edge effect: decompositions disagree on residual memory (last 1 to 2 days vs about 1 to 2 weeks); centred smoothers are unreliable near series ends | Unresolved |
| Coverage and % change error of arbitrary date ranges | Not scored; `evaluate_fitted` scores week and month totals and their direction |
| Weekly simulator interval coverage below nominal ([limitations](results/limitations.md)) | Open; daily predictions use `NoiseModel` |
| Smoothed `EventKernel` in the nowcast vs box windows | Untested; [slope and events](evidence/slope-and-events.md) used box windows |
| Flight block (`LinearRegressors` on flight features) | Registered, used by no spec ([factor chain](evidence/factor-chain.md)) |
| International-only spec with 182-day base-stock knots and a learned flow curve: each lowers international validation WAPE in 7 of 7 folds; their domestic intervals include 0 ([hand-set settings](evidence/hand-set-settings.md), [flow linearity](evidence/flow-linearity.md)) | Not gated; the two changes are untested together |
| Noise model memory beyond AR(1): out-of-sample error ACF stays at 0.19 to 0.35 from lag 7 to lag 14, with a bump at lag 7 ([noise](evidence/noise.md)) | Open; `NoiseModel` is AR(1) ([intervals](model/intervals.md)) |
