# Data and artifacts

## Calls
- `docs/data/lake.md` : datasets, lake checks, committed assets
- `docs/guide/setup.md` : pipeline steps, configuration, `make clean`
- `docs/guide/outputs.md` : files each command writes

## Rules
- raw workbooks: `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`) is gitignored and supplied locally; never edit or commit it.
- committed lake: `lake/manifest.json` and the tracked files in `lake/curated/` are committed despite `.gitignore` (check with `git ls-files lake`).
- scratch: commands that write the lake or `output/` (`build-lake`, `build-panel`, `build-daily-panel`, `train`, `evaluate`, `make all`, `predict`, `charts`, `report`, `evaluate-model`, `ablate-blocks`, `outlook`) run against scratch dirs, never the checkout: `TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/out make all`.
- submission: never use a submission file unless `validate_predictions` returns no problems.
- floor: nationality Guests are floored at max(New Arrivals, 10); absent test days get below-threshold arrivals, never interpolation.
- same-day: read `*` as 0; never publish Poisson same-day intervals.
- narration: narration and LLM text read `market_outputs.json` fields only and never compute numbers; a new number is added in `nowcast/outputs.py`.
- pickle: `residual_engine.pkl` pickles a plain dict of scikit-learn estimators, never a project class.
- bundle: after any model or artifact change, run `make export` and commit `web/public/data` with the change; never hand-edit bundle files.
- raw arrivals: the bundle exports derived terms (what-if base, pre, in, floor, multiplier), never raw arrivals.
