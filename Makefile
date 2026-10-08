PYTHON := .venv/bin/python
PYTEST  := .venv/bin/pytest
TWIN    := .venv/bin/twin

# Same overrides the code honours (see src/tourism_twin/config.py).
LAKE_DIR   := $(or $(TWIN_LAKE_DIR),lake)
OUTPUT_DIR := $(or $(TWIN_OUTPUT_DIR),output)

.PHONY: all install lake panel evaluate train charts report data-issues-pdf test clean

## Rebuild every metric and artifact from the raw workbooks (one-command reproducibility).
## Needs the organizer-provided dataset in '01a - DCT Dataset/' (or TWIN_SOURCE_DIR).
all: lake panel evaluate train charts report test
	@echo ""
	@echo "=========================================="
	@echo " All artifacts rebuilt successfully."
	@echo "=========================================="

## Create .venv and install the src/ packages in editable mode (run once)
install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[report,dev]"

## Step 1 — raw workbooks -> Parquet tables + DuckDB lake
lake:
	$(TWIN) build-lake

## Step 2 — lake -> curated weekly market panel + daily panel with arrival lags
panel:
	$(TWIN) build-panel
	$(TWIN) build-daily-panel

## Step 3 — evaluate models, write evaluation_results.json + sync calibrator
evaluate:
	$(TWIN) evaluate

## Step 4 — re-calibrate structural params, residual ML, conformal bounds
train:
	$(TWIN) train

## Step 5 — regenerate scenario charts (waterfall, tornado, benchmark)
charts:
	$(TWIN) charts

## Step 6 — build final PDF solution report
report:
	$(TWIN) report solution

## Build DATA_ISSUES.pdf from DATA_ISSUES.md
data-issues-pdf:
	$(PYTHON) scripts/build_data_issues_pdf.py

## Run full test suite
test:
	$(PYTEST) tests/ -v

## Remove generated files that are not committed: figures, PDFs, the DuckDB database, and
## staging leftovers. Committed lake artifacts are left alone (rebuild them with `make all`).
clean:
	rm -rf $(OUTPUT_DIR)/figures $(OUTPUT_DIR)/pdf $(LAKE_DIR)/.staging_build
	rm -f $(LAKE_DIR)/analytics.duckdb $(LAKE_DIR)/analytics.duckdb.wal
	@echo "Cleaned generated artifacts in $(OUTPUT_DIR)/ and $(LAKE_DIR)/."
