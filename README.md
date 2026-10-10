# Abu Dhabi Hotel Outlook

**Flights in, hotel demand out.** A decision tool for DCT Abu Dhabi, built for ChallengeON ATP 2026.

**Live site**: https://abu-dhabi-hotel-outlook.vercel.app · **User guide**: [docs/user_guide.md](docs/user_guide.md) · **Model design**: [docs/model_design.md](docs/model_design.md) · **Solution document**: [docs/solution_documentation.md](docs/solution_documentation.md) · **Challenge**: [DCT challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)

---

Abu Dhabi Hotel Outlook turns air-connectivity decisions into hotel guests: a weekly planning model shows what a flight change does to demand per source market and season, and a daily nowcast predicts hotel guests from new arrivals. Both are built on one validated lake of the DCT flight and hotel data and served by a CLI and a static web app.

## Key features

* **Answers planning questions**: a new route, more flights, more seats, fuller flights, a different seasonal market mix.
* **Transparent chain**: seats → passengers → visitors → hotel nights, every step a lever you can move.
* **Validated**: time-ordered validation origins and a frozen test period scored once, never shuffled.
* **Honest ranges**: every number comes with its ±error.
* **Reproducible**: one command rebuilds the lake, the models, the charts and the report from the raw workbooks.
* **Fast and static**: the site computes scenarios in the browser from a versioned data bundle. No server.

## Requirements

* Python 3.10+ (developed on 3.12) and Node 20+.
* The five competition workbooks in `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`): `data domestic_train.xlsx`, `data domestic_test.xlsx`, `data international_train.xlsx`, `data international_test.xlsx`, `flight_data.xlsx`. They are not included: they are licensed for the competition only.

The curated lake and the weekly model artifacts are committed, so the simulator, the web app and the tests run without the workbooks.

## Installation

```console
$ make install       # .venv with the package and its report and dev extras
$ make web-install   # web app dependencies (npm ci)
```

## Example

### Build everything

```console
$ make all
```

This rebuilds the lake (`lake/`), the weekly and daily panels, the forward-holdout evaluation, the model artifacts, the charts (`output/figures/`) and the solution PDF (`output/pdf/`), then runs the tests. `make export` refreshes the site data in `web/public/data/`. It overwrites the committed lake artifacts; to build into a scratch directory instead:

```console
$ TWIN_LAKE_DIR=/tmp/lake TWIN_OUTPUT_DIR=/tmp/output make all
```

### Run it

```console
$ make up
```

Web app: http://localhost:5180. JSON API: http://127.0.0.1:8090. Stop both with `make down`.

### Run it in Docker

```console
$ docker compose up
```

Web app: http://localhost:8080. API and earlier UI: http://localhost:8090. The committed data bundle and lake artifacts travel inside the images, so no raw workbooks are needed. Single images: `docker build --target web -t tourism-twin-web .` or `--target api`.

### Check it

* **Outlook** (`/`): each coming month against the same month a year earlier, the markets growing and slowing most, and answers to the five planning questions.
* **Flight scenarios** (`/simulate`): levers per market, a moving map of visitors week by week, the conversion chain, the waterfall and the biggest levers.
* **Daily forecast** (`/nowcast`): guests for any date range with its error, an arrivals what-if, and the nationality list.
* **How it works** (`/report`): the method, the validation and the limits, with the source of every number.

## Try a scenario

Two more weekly flights from the UK in winter, on 290-seat aircraft, two points fuller:

```console
$ twin simulate --market "UNITED KINGDOM" --season Winter_Peak --delta-freq 2 --gauge 290 --delta-lf 0.02

Metric                               Baseline     Scenario        Net Shift
Weekly Seat Capacity                   13,844       14,424             +580
Flight Passengers (Pax)                12,604       13,420             +817
Point-to-Point (P2P)                    3,556        3,786             +230
Hotel New Arrivals                      3,789        4,019             +230
Hotel Guests (Guest-Days)              17,645       18,717           +1,073

TOTAL ATTRIBUTED LIFT                          +1,072.7             100.0%
Scenario Outcome             P10 (Conservative)     P50 (Median) P90 (Optimistic)
Incremental Demand Lift                -6,039           +1,073           +8,185
```

The full briefing adds the waterfall by lever, the range and the tornado ranking. The same scenario runs on `/simulate` with sliders.

## Accuracy

| Model | Measure | Result |
| :--- | :--- | :--- |
| Daily nowcast (`twin_daily`) | Validation WAPE, domestic / international | **4.18% / 4.59%** |
| Weekly planning model (hybrid) | Forward-holdout WMAPE, 21 markets | **20.62%** |

The nowcast is scored on daily segment totals over 7 monthly validation origins (Feb to Aug 2024), each trained up to 21 days before the origin; it uses the predicted period's new arrivals. The planning model is calibrated on 104 weeks and scored on the next 30 weeks without any of their arrivals. Full tables: [daily nowcast](docs/solution_documentation.md#93-daily-nowcast), [weekly planning model](docs/solution_documentation.md#92-results-weekly-planning-model-forward-holdout).

## Project layout

```text
src/tourism_twin/
  config.py    every file location, overridable by environment variables
  domain/      markets, archetypes, seasons, event calendar
  features/    derived columns, declared once
  data/        raw workbooks → validated lake and market panels
  models/      shared additive log-scale model kernel and back-test harness
  nowcast/     daily guest model (twin predict)
  planning/    weekly scenario model: chain, residual, ranges, simulator
  reporting/   charts, PDF reports, slide deck
  export/      the web data bundle (twin export)
  cli/         the twin command
src/app/       earlier web UI and JSON API
web/           static React site and its TypeScript model engine
docs/          user guide, model design, solution document
tests/         Python tests, one folder per package
lake/          curated tables and model artifacts
meta/          audits, research notes, deck source
```

## Commands

| Command | Does |
| :--- | :--- |
| `make all` | Rebuild lake, panels, evaluation, models, charts and report; run tests |
| `make up` / `make down` | Start / stop the web app and the API |
| `make test` / `make web-test` | Python tests / web engine parity tests |
| `twin predict` | Test-period guest predictions with ranges (`output/predictions/`) |
| `twin simulate` | One flight scenario, printed as a briefing |
| `twin evaluate` | Weekly forward-holdout back-test |
| `twin validate` | Daily validation numbers (`output/validation_summary.json`) |
| `twin export` | Versioned data bundle for the web app |

Full list, options and outputs: [docs/user_guide.md](docs/user_guide.md#12-setup-pipeline-and-configuration).

## Dependencies

* Core: DuckDB, pandas, PyArrow, openpyxl, scikit-learn, SciPy, Matplotlib.
* `report` extra: ReportLab, python-pptx, PyYAML (PDF reports and the slide deck).
* `dev` extra: pytest.
* Web: Vite, React, TypeScript, Recharts, d3-geo, React Router; Vitest for tests.

## Data licence

The DCT competition data may be used within the competition only. The raw workbooks are never committed to this repository.
