PYTHON := .venv/bin/python
PYTEST  := .venv/bin/pytest

.PHONY: all evaluate train charts report test clean

## Rebuild every metric and artifact from raw data (one-command reproducibility)
all: evaluate train charts report test
	@echo ""
	@echo "=========================================="
	@echo " All artifacts rebuilt successfully."
	@echo "=========================================="

## Step 1 — evaluate models, write evaluation_results.json + sync calibrator
evaluate:
	$(PYTHON) scripts/evaluate_models.py

## Step 2 — re-calibrate structural params, residual ML, conformal bounds
train:
	$(PYTHON) scripts/train_models.py

## Step 3 — regenerate scenario charts (waterfall, tornado, benchmark)
charts:
	$(PYTHON) scripts/generate_scenario_charts.py

## Step 4 — build final PDF solution report
report:
	$(PYTHON) scripts/build_solution_report.py

## Run full test suite
test:
	$(PYTEST) tests/ -v

## Remove all generated artifacts (keeps source + raw data)
clean:
	rm -rf output/figures/ output/pdf/
	rm -f lake/curated/evaluation_results.json \
	       lake/curated/conformal_calibrator.json \
	       lake/curated/structural_calibration.json \
	       lake/curated/residual_engine.pkl \
	       lake/curated/*.parquet
	@echo "Cleaned generated artifacts."
