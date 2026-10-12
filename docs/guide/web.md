# Web app

## Commands

```bash
make export     # rm -rf web/public/data, then twin export: fit twin_daily, write the bundle
make export-fast  # same with twin export --fast: cached noise model (lake/curated/noise_model.json)
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
| Reads `web/public/data/manifest.json` → `<version>/{nowcast,whatif,planning,weekly,outlook,golden}.json` ([web bundle](../architecture/web-bundle.md)) |
| Production: Vercel project `abu-dhabi-hotel-outlook`, https://abu-dhabi-hotel-outlook.vercel.app; `web/vercel.json`: SPA rewrites, `manifest.json` cached 60 s, versioned files immutable; `web/.vercel` and `.env*` are gitignored |
| Site name AeroLodge Metrics (page title, top bar logo `web/public/logo.svg`) |
| A failed load of a lazily imported page after a new deploy (`vite:preloadError`) reloads the page (`web/src/main.tsx`) |
| Fixed top navigation (a drop-down sheet on phones); colours from `web/src/theme/tokens.css` (palette from visitabudhabi.ae and dct.gov.ae); fonts Oswald and Inter; dark mode follows the system setting |
| Uncertainty in the copy: "±X% error" for a measured error, "Range A to B" for the outlook, "no measured error" for estimates without one (new routes, markets without their own conformal margin) |

## Pages

| Route | Label | Content |
| --- | --- | --- |
| `/` | Outlook | From the bundle's `outlook.json` ([outlook](../model/outlook.md)), default scenario (`default_scenario`), months from the first after today's month to the last projected month: the hero names the lead month's calibrated total hotel nights, its range and its change on the same month a year earlier (real guests, or the model's estimate, labelled), the arrivals assumption, the number of back-tests behind the correction and the 2023 to 2024 back-test period; one card per month with the calibrated total, its range, the change on a year earlier (up or down only when last year's figure lies outside the range, else "same"; `engine/outlook.ts`) and the international and UAE-resident projections marked uncorrected; without `outlook.json` the page says the forecast is being prepared. Markets growing and slowing most over the predicted period (`engine/insights.ts`); "What if…?" answers to the five planning questions (new route, more flights, more seats, fuller flights, seasonal market mix) with the weekly change, its error and the extra guests over 2026 (`engine/questions.ts`); each card's "Try your own numbers" links to `/simulate` carrying that card's own market, season and levers; accuracy facts |
| `/simulate` | Flight scenarios | See below |
| `/nowcast` | Daily forecast | Market or total, 7/14/28/91 days and first day; forecast total with its likely range and change vs the days before ("no clear change" under ±8%); check-in sliders (residents and international 50 to 150%, selected market 0 to 200%); bars against the same days last year; daily line with its range; nationality list with its own search box |
| `/report` | How it works | Method, validation, limits, the outlook method; copy and sources in `web/src/content/report.ts`; "What if…?" shows the same five answers as the landing page; "Reported by others (not our model)": a table of hotel, airport and airline figures published by DCT, JLL, Abu Dhabi Airports, Etihad and the GCAA, each with its source and publication date (`content/externalReports.ts`, `REPORTED_FIGURES`), not used by any model or chart |

`/simulate`:

| Area | Content |
| --- | --- |
| Layout | Left panel, canvas and right panel; the two side panels resize by dragging their gutters or with the arrow keys (10 px, 25 px with Shift), Home and End; Enter, Space or a double click resets; widths are kept in `localStorage`. Above 1280 px wide each pane scrolls on its own and the page does not |
| Scenario in the URL | `?market=&season=&start=` plus any moved slider in display units, written on every change and read on arrival (`levers.ts`): the page opens on the linked scenario and a reload or a shared link keeps it. Unknown markets, seasons and start weeks fall back to the defaults; a workbench nobody touched keeps a clean `/simulate` |
| Left panel | Market (All markets by default, then calibrated markets, then countries without calibration, labelled "estimated from similar markets"); presets (Today, 2 more flights a week, Stopover campaign, Longer stays; disabled where they do nothing); 8 levers in three groups, each with a default mark and reset: Schedule change (extra flights per week, seats per extra flight, seats on existing flights; learned; a line gives the season's seat change and the hotel-night change with its range, or says the market uses the pooled response, is a new route or is closed), Capacity growth (seat growth −5 to +15% a year; marked "Assumption"; a line gives the change after 3 years at the central line and its range from no effect to one for one), Assumptions (how full flights are, stopover share, visitors who book a hotel, hotel nights per visitor); Forecast section (week the changes start: by default the first week starting on or after today's date in the browser, labelled "today", or the week after the real data when no projected week is later; other choices the week after the real data, then every third month; demand growth for all markets −5 to +10% a year, projected weeks only) |
| Lever scope | One market, picked in the list or on the map; locked with All markets; UAE residents have no schedule, capacity, load-factor or stopover levers; seats per extra flight applies once extra flights are added; capacity growth applies to the selected market, demand growth to every market; real weeks never change |
| Map tab | World map (Natural Earth projection with graticules); zoom 1x to 5x with the +, − and Fit buttons or the mouse wheel, drag to pan; labels, dots and planes keep their size when zoomed. Play at 1x/4x over the weeks from December 2022 to February 2029; teal dots for arrivals (hotel check-ins = weekly guests ÷ the season's guests-per-visitor factor), coral for departures (check-ins minus the change in guests staying since last week); filter Both / Arriving / Leaving; scrubber chart of total weekly guests marking where real data ends; counters for the week, its guests, change vs a year before, top 3 arriving markets, guests added by the changes; event weeks shown as a stack of cards over the map (newest on top, at most 4; a continuing event extends its card's dates; each card fades after about 4 s at 1x and 2 s at 4x and stays while paused; a scrubber jump or reset shows only the landed week's events) with their markets' arcs glowing; no motion with reduced motion |
| Other tabs | Over time (actuals, back-test, projection, event flags, error on event weeks, the capacity-growth range when seat growth is set; all markets summed for All markets); How it adds up (conversion chain, waterfall); Biggest levers (tornado); the last two have a season choice |
| Right panel | Totals for the Week / Month / Year / Since-a-date period around the map week (visitors arriving, hotel nights, visitors added by the changes); with Since and the map week before the start date the totals are empty and a note says so; "Where visitors come from" for the same period |
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
