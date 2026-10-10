PYTEST  := .venv/bin/pytest
TWIN    := .venv/bin/twin

# Same overrides the code honours (see src/tourism_twin/config.py).
LAKE_DIR   := $(or $(TWIN_LAKE_DIR),lake)
OUTPUT_DIR := $(or $(TWIN_OUTPUT_DIR),output)

.PHONY: all install lake panel evaluate train charts report test clean \
        backend export validate frontend web-install web-dev web-build web-test deploy \
        up down status logs api-up api-down web-up web-down

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

## Run full test suite
test:
	$(PYTEST) tests/ -v

## ---- Web app (web/): a static React site; no Python runs at request time ----
## The Python side ("backend") only produces the versioned JSON bundle the site reads.
WEB_DATA := web/public/data

## Python side: run the tests, then write the model bundle into the web app
backend: test export

## Fit the shipped nowcast and replace web/public/data with a fresh bundle (manifest + one versioned folder)
export:
	rm -rf $(WEB_DATA)
	$(TWIN) export --out $(WEB_DATA)

## #11 validation summary (validation origins only; never the frozen test) -> output/validation_summary.json
validate:
	$(TWIN) validate

## Web side: install, check parity with the bundle, type-check and build to web/dist
frontend: web-install web-test web-build

web-install:
	cd web && npm ci

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

web-test:
	cd web && npm test

## Deploy web/ to Vercel production (project abu-dhabi-hotel-outlook; needs `vercel login`)
deploy: web-test
	cd web && vercel deploy --prod --yes

## ---- Local servers (background, pid files in .run/) ----
## make up        start both: web app http://localhost:$(WEB_PORT), Python API http://127.0.0.1:$(API_PORT)
## make down      stop both;  make status / make logs
WEB_PORT ?= 5180
API_PORT ?= 8090
RUN_DIR  := .run

up: api-up web-up
	@$(MAKE) --no-print-directory status

down: web-down api-down

## Python API + legacy UI (src/app/server.py: /api/simulate, /api/nowcast/*)
api-up:
	@mkdir -p $(RUN_DIR)
	@if [ -f $(RUN_DIR)/api.pid ] && kill -0 $$(cat $(RUN_DIR)/api.pid) 2>/dev/null; then echo "api already running"; else \
	  (PORT=$(API_PORT) exec nohup .venv/bin/python -m app.server > $(RUN_DIR)/api.log 2>&1) & echo $$! > $(RUN_DIR)/api.pid; fi

api-down:
	@if [ -f $(RUN_DIR)/api.pid ]; then kill $$(cat $(RUN_DIR)/api.pid) 2>/dev/null || true; rm -f $(RUN_DIR)/api.pid; echo "api stopped"; fi

## React app (Vite dev server, hot reload; reads web/public/data)
web-up:
	@mkdir -p $(RUN_DIR)
	@test -d web/node_modules || (cd web && npm ci)
	@if [ -f $(RUN_DIR)/web.pid ] && kill -0 $$(cat $(RUN_DIR)/web.pid) 2>/dev/null; then echo "web already running"; else \
	  (cd web && exec nohup ./node_modules/.bin/vite --port $(WEB_PORT) --strictPort > ../$(RUN_DIR)/web.log 2>&1) & echo $$! > $(RUN_DIR)/web.pid; fi

web-down:
	@if [ -f $(RUN_DIR)/web.pid ]; then kill $$(cat $(RUN_DIR)/web.pid) 2>/dev/null || true; rm -f $(RUN_DIR)/web.pid; echo "web stopped"; fi

status:
	@for s in web api; do if [ -f $(RUN_DIR)/$$s.pid ] && kill -0 $$(cat $(RUN_DIR)/$$s.pid) 2>/dev/null; \
	  then echo "$$s  running  pid $$(cat $(RUN_DIR)/$$s.pid)"; else echo "$$s  stopped"; fi; done
	@echo "web  http://localhost:$(WEB_PORT)/report   api  http://127.0.0.1:$(API_PORT)/"

logs:
	@tail -n 20 $(RUN_DIR)/web.log $(RUN_DIR)/api.log 2>/dev/null || true

## Remove generated files that are not committed: figures, PDFs, the DuckDB database, and
## staging leftovers. Committed lake artifacts are left alone (rebuild them with `make all`).
clean:
	rm -rf $(OUTPUT_DIR)/figures $(OUTPUT_DIR)/pdf $(LAKE_DIR)/.staging_build
	rm -f $(LAKE_DIR)/analytics.duckdb $(LAKE_DIR)/analytics.duckdb.wal
	@echo "Cleaned generated artifacts in $(OUTPUT_DIR)/ and $(LAKE_DIR)/."
