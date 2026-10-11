# Model experiments

## Calls
- `experiment/README.md` : the experiment folders and the question each answers
- `agents/model/evaluation.md` : folds, comparison and gate a variant is judged by
- `docs/evidence/index.md` : where a finished experiment's measurements are stated

## Rules
- layout: one folder per experiment, `experiment/<name>/`: its code, a `README.md` (question, variants, how to run, conclusion, the commit it ran at) and aggregate results (in the README or a `results.md`); its line in `experiment/README.md`.
- outputs: cached fits, predictions and figures go to `experiment/<name>/out/` (gitignored, licensed data); never commit them.
- isolation: experiment code imports `tourism_twin`, never the reverse; a variant subclasses or wraps package code inside its folder and never edits `src/`.
- order: graphs first: plot the series, residuals or responses the question is about, then change the model.
- shipping: a variant ships only through the gate (`agents/model/evaluation.md`), as its own change in `src/`; its measurements go to `docs/evidence/`, citing the folder.
