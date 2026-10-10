# Web app

## Commands

```bash
make export     # rm -rf web/public/data, then twin export: fit twin_daily, write the bundle
make up         # web app http://localhost:5180 (WEB_PORT), Python API http://127.0.0.1:8090 (API_PORT); make down / status / logs
make web-dev    # Vite dev server
make web-test   # vitest
make web-build  # type-check and build to web/dist
make deploy     # web-test, then vercel deploy --prod --yes from web/ (needs vercel login)
```

## Site

| Fact |
| --- |
| Static React site: Vite 6, React 19, TypeScript, Recharts 3, d3-geo, react-router 7; no Python at request time |
| Reads `web/public/data/manifest.json` → `<version>/{nowcast,whatif,planning,weekly,golden}.json` ([web bundle](../architecture/web-bundle.md)) |
| Production: Vercel project `abu-dhabi-hotel-outlook`, https://abu-dhabi-hotel-outlook.vercel.app; `web/vercel.json`: SPA rewrites, `manifest.json` cached 60 s, versioned files immutable; `web/.vercel` and `.env*` are gitignored |
| Fixed top navigation (a drop-down sheet on phones); colours from `web/src/theme/tokens.css` (palette from visitabudhabi.ae and dct.gov.ae); fonts Oswald and Inter; dark mode follows the system setting |
| The only uncertainty term in the copy is "±X% error" |

## Pages

| Route | Label | Content |
| --- | --- | --- |
| `/` | Outlook | Each full forecast month (international, UAE residents, all guests) against the same month a year earlier, with the month's own error (`NoiseModel.range_interval` at the manifest coverage); up or down only when larger than that error, else "about the same" (`engine/insights.ts`); markets growing and slowing most; "What if…?" answers to the five planning questions (new route, more flights, more seats, fuller flights, seasonal market mix) with the weekly change, its error and the extra guests over 2026 (`engine/questions.ts`); accuracy facts |
| `/simulate` | Flight scenarios | See below |
| `/nowcast` | Daily forecast | Market or total, 7/14/28/91 days and first day; forecast total with its likely range and change vs the days before ("no clear change" under ±8%); check-in sliders (residents and international 50 to 150%, selected market 0 to 200%); bars against the same days last year; daily line with its range; nationality list filtered by the top-bar search |
| `/report` | How it works | Method, validation, limits; copy and sources in `web/src/content/report.ts`; "What if…?" shows the same five answers as the landing page |

`/simulate`:

| Area | Content |
| --- | --- |
| Left panel | Market (All markets by default, then calibrated markets, then countries without calibration, labelled "estimated from similar markets"); presets (Today, 2 more flights a week, Stopover campaign, Longer stays; disabled where they do nothing); 7 levers in two groups (Flights, Visitors), each with a default mark and reset; Forecast section (week the changes start, by default the week after the real data; growth −5 to +10% a year, projected weeks only) |
| Lever scope | One market, picked in the list or on the map; locked with All markets; UAE residents have no flight levers or stopover share; seats per extra flight applies once extra flights are added; real weeks never change |
| Map tab | Play at 1x/4x over the weeks from December 2022 to February 2029; teal dots for arrivals (hotel check-ins = weekly guests ÷ the season's guests-per-visitor factor), coral for departures (check-ins minus the change in guests staying since last week); filter Both / Arriving / Leaving; scrubber chart of total weekly guests marking where real data ends; counters for the week, its guests, change vs a year before, top 3 arriving markets, guests added by the changes; event weeks named in a callout with their markets' arcs glowing; no motion with reduced motion |
| Other tabs | Over time (actuals, back-test, projection, event flags, error on event weeks; all markets summed for All markets); How it adds up (conversion chain, waterfall); Biggest levers (tornado); the last two have a season choice |
| Right panel | Totals for the Week / Month / Year / Since-a-date period around the map week (visitors arriving, hotel nights, visitors added by the changes); "Where visitors come from" for the same period |
| New route | For a country without weekly history, a "New route estimate" card gives weekly guests and the change per season from similar markets; totals fall back to all markets |

## Earlier web UI: `twin serve`

`twin serve --port 8080` (or `python -m app.server`, port from `PORT`) serves `src/app/static/index.html`, no build step: market, season and lever controls (seat-percentage shift is CLI and API only), KPI cards, waterfall, conversion chain, tornado.

| Endpoint | Returns |
| --- | --- |
| `GET /api/simulate` | Scenario for `market`, `season`, `delta_freq`, `gauge`, `delta_seats_pct`, `delta_lf`, `delta_p2p`, `delta_mult_pct`, `delta_los`; invalid season → 400 |
| `GET /api/benchmark` | Weekly benchmark |

## Nowcast API

Answers come from `output/predictions/nowcast_serving.json` (written by `twin predict`); nothing is refitted per request. Without the file the endpoints return 503; ranges outside the predicted period return 400.

| Endpoint | Returns |
| --- | --- |
| `GET /api/nowcast/series` | Series names (21 markets, `INTERNATIONAL`, `TOTAL`), the predicted period, interval coverage |
| `GET /api/nowcast/range?series=TOTAL&start=YYYY-MM-DD&end=YYYY-MM-DD` | `guests`, `p10`, `p90` (`NoiseModel.range_interval`), `previous_guests` for the same-length range just before (actuals for training days, predictions for test days), `change`, `direction`: `up` / `down` when \|change\| ≥ 0.08, else `no clear change` ([range totals](../evidence/range-totals.md)) |
| `GET /api/nowcast/nationalities?start=&end=` | Predicted guests per international nationality and its share of the international total (no interval) |
