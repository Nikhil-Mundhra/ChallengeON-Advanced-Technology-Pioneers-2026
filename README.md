# Abu Dhabi Hotel Outlook

Flights in, hotel demand out. A decision tool for DCT Abu Dhabi, built for ChallengeON ATP 2026.

Live site: https://abu-dhabi-hotel-outlook.vercel.app · Docs: [docs/index.md](docs/index.md) · User guide: [docs/guide/index.md](docs/guide/index.md) · Results: [docs/results/index.md](docs/results/index.md) · Challenge: [DCT challenge statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)

---

Abu Dhabi Hotel Outlook turns air-connectivity decisions into hotel guests. A weekly planning model shows what a flight change does to demand per source market and season: a seat-ratio chain with a calendar correction sets the baseline, and a schedule change moves guests by each market's response read from a daily seats to arrivals to guests model fitted to the data. A daily nowcast predicts hotel guests from new arrivals. Both are built on one validated lake of the DCT flight and hotel data and served by a CLI and a static web app.

## Key features

* Answers planning questions: a new route, more flights, more seats, fuller flights, a different seasonal market mix.
* Transparent chain: seats → passengers → visitors → hotel nights, every step a lever you can move.
* Learned flight response: guests follow a schedule change by each market's elasticity per season, with a range from refits on earlier data; seat growth over years is an assumption with a 0 to one-for-one range.
* Validated: time-ordered validation origins and a frozen test period scored once, never shuffled.
* Ranges: every forecast number comes with its ±error.
* Reproducible: one command rebuilds the lake, the models, the charts and the report from the raw workbooks.
* Static site: scenarios are computed in the browser from a versioned data bundle; no server runs at request time.

## Requirements

* Python 3.10+ (developed on 3.12) and Node 20+.
* The five competition workbooks in `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`): `data domestic_train.xlsx`, `data domestic_test.xlsx`, `data international_train.xlsx`, `data international_test.xlsx`, `flight_data.xlsx`. They are not included: they are licensed for the competition only.

The curated lake and the weekly model artifacts are committed; the simulator, the web app and the tests run without the workbooks.

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

### Check it

* Outlook (`/`): each coming month against the same month a year earlier, the markets growing and slowing most, and answers to the five planning questions.
* Flight scenarios (`/simulate`): levers per market, a moving map of visitors week by week, the conversion chain, the waterfall and the biggest levers.
* Daily forecast (`/nowcast`): guests for any date range with its error, an arrivals what-if, and the nationality list.
* How it works (`/report`): the method, the validation and the limits, with the source of every number.

## Try a scenario

Two more weekly flights from the UK in winter, on 290-seat aircraft, load factor unchanged:

```console
$ twin simulate --market "UNITED KINGDOM" --season Winter_Peak --delta-freq 2 --gauge 290 --delta-lf 0

Metric                               Baseline     Scenario        Net Shift
Weekly Seat Capacity                   13,844       14,424             +580
Flight Passengers (Pax)                12,604       13,132             +528
Point-to-Point (P2P)                    3,556        3,705             +149
Hotel New Arrivals                      3,789        3,838              +49
Hotel Guests (Guest-Days)              17,645       17,872             +227

TOTAL ATTRIBUTED LIFT                            +227.2             100.0%
Scenario Outcome             P10 (Conservative)     P50 (Median) P90 (Optimistic)
Incremental Demand Lift                -6,563             +227           +7,018
```

A 4.2% seat increase gives 1.3% more guests: the UK's winter elasticity, read from the fitted chain, is 0.31. Without `--delta-lf 0` the command also adds 2 points of load factor (the default).

The full briefing adds the waterfall by lever, the range and the tornado ranking. The same scenario runs on `/simulate` with sliders.

## Accuracy

| Model | Measure | Result |
| :--- | :--- | :--- |
| Daily nowcast (`twin_daily`) | Validation WAPE of daily segment totals, 7 monthly origins (Feb to Aug 2024), domestic and international | [nowcast validation](docs/results/nowcast-validation.md) |
| Weekly planning model (hybrid) | Forward-holdout WMAPE, 21 markets, 30 weeks without their arrivals | [planning holdout](docs/results/planning-holdout.md) |
| Schedule response (fitted chain) | Error on the guest change in 717 market-weeks where seats moved more than 15% year on year, against the calendar-only model, 7 folds | [scenario response](docs/evidence/scenario-response.md) |

The nowcast uses the predicted period's new arrivals; the planning model does not.

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
docs/          facts: data, architecture, model, evidence, results, user guide
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

Full list, options and outputs: [docs/guide/cli.md](docs/guide/cli.md).

## Dependencies

* Core: DuckDB, pandas, PyArrow, openpyxl, scikit-learn, SciPy, Matplotlib.
* `report` extra: ReportLab, python-pptx, PyYAML (PDF reports and the slide deck).
* `dev` extra: pytest.
* Web: Vite, React, TypeScript, Recharts, d3-geo, React Router; Vitest for tests.

## Data licence

The DCT competition data may be used within the competition only. The raw workbooks are never committed to this repository.
