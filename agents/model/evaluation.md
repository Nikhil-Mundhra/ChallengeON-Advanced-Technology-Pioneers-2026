# Model evaluation

## Calls
- `docs/evidence/reference-evaluation.md` : the fixed reference evaluation and its expected values
- `docs/model/nowcast.md` : validation protocol, folds and `compare`
- `docs/results/index.md` : where each result number lives and its source artifact

## Rules
- reference: before changing a nowcast model, reproduce `docs/evidence/reference-evaluation.md` and compare with its expected values; its hyperparameters stay fixed, tuning applies to the production spec only.
- scoring: score a fitted model on later data only through `models/evaluate.evaluate_fitted` (no refitting).
- comparing: compare model choices only through `models/backtest.compare` on `VALIDATION_ORIGINS`, with `models/backtest.backtest` and `RollingOrigin` or `HoldoutSplit`; pass `period_days=7` for weekly panels.
- frozen test: score `FROZEN_TEST` once, after every choice is final.
- decisions: decide specs on `VALIDATION_ORIGINS`; never on the two reference folds or on origins overlapping the frozen test (8-origin 2024-07..2025-02, 13-origin 2024-02..2025-02); label those exploratory.
- counts: a result counts only if `compare`'s interval excludes 0 and its sign holds in most folds.
- gate: ship a component or weighting only if it lowers validation WAPE by at least 0.3 pp on both domestic and international; among variants within 0.2 pp of the best, keep the simplest.
- series: evaluate and report domestic and international separately, never only pooled.
- diagnostics: never rank `DIAGNOSTIC_SPECS` with forecast specs.
- events: judge event components only on back-test folds that contain their windows.
- tuning: hyperparameters (K, H, λ, event windows, detector thresholds, ridge α) are tuned on validation folds with time-ordered splits only, never shuffled, never on the reported folds.
- calibration: z-scores, conformal margins and noise σ come from training folds only.
- reporting: a result number goes into `docs/results/` (or `docs/evidence/` for an experiment), with the artifact or script it came from.
