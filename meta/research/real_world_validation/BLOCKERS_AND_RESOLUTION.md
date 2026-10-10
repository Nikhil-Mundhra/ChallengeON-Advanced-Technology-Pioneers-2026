# Real-world validation blockers and resolution plan

Investigated 7 October 2026. Scope: the challenge's 2024 inbound flight
route-days and daily hotel guest tables. Evidence and reproducible outputs are
in [PUBLIC_DATA_FINDINGS_2024.md](PUBLIC_DATA_FINDINGS_2024.md),
`scad_2024_validation.json`, and `etihad_2024_route_checks.json`. The
[8 October flight pilot](FLIGHT_DATE_AND_COVERAGE_PILOT.md) records the attempted
historical-arrival lookup and a reproducible route-coverage sample.

| Blocker | What the investigation established | Next resolution step / closure test |
| --- | --- | --- |
| **Flight date and time semantics** | The workbook has a calendar `Date`, route, and airline, but no flight number, departure/arrival time, timezone, or schedule/actual flag. Etihad's EY0249 left Kozhikode 1 Jan 2024 and was scheduled at AUH at 00:05 **2 Jan**; an Etihad Kozhikode row exists in the challenge on **1 Jan**. Thus `Date` cannot safely be assumed to be AUH local arrival date for every row. | Ask DCT for the timestamp definition and timezone. Obtain a small flight-level extract with flight number, origin-local departure, AUH scheduled arrival, AUH actual arrival, and operational status. Compare 10 overnight and 10 same-day services; close only if the date rule explains all rows, including the first Kozhikode date. |
| **Real operation versus published schedule** | Selected Etihad route-days match published schedules: Al Qassim 72/72, Antalya 40/40, Jaipur 23/24. A scheduled service can be cancelled, retimed, or flown under another identifier. The one absent Jaipur day (22 Jul) cannot be explained from the route table. The public [OpenSky arrival endpoint](https://openskynetwork.github.io/opensky-api/rest.html) returned **HTTP 403: `You cannot access historical flights`** for the 1–2 Jan 2024 AUH pilot window. | Match `flight number + operating date` to an airport movement feed or licensed historical flight-status feed, or seek eligible historical [OpenSky access](https://opensky-network.org/about/faq). Test one known flight and AUH coverage before scaling. OpenSky has no passenger counts, so it can validate movement/timing only. |
| **Flight population and passenger definitions** | The challenge has 37,607 2024 route-airline-days, 34 airlines, 98 departure-city labels, 11,222,004 `Total PAX`, 5,726,035 P2P, and 5,495,969 transfers. Its 2024 transit sum is zero. SCAD reports 14,522,288 Zayed airport arrivals excluding transit: a 3,300,284 (22.7%) gap. Source-linked samples find [four absent Etihad destinations](etihad_2024_coverage_matrix.csv) and [nine absent Air Arabia Abu Dhabi destinations](multicarrier_2024_coverage_matrix.csv), while six sampled IndiGo routes all appear. These are evidence of incomplete/different coverage, not proof the challenge counts are false. | Request the route, airline, terminal, charter, codeshare, infant, and passenger inclusion rules plus an airport monthly reconciliation. Reconcile `P2P + transfer + transit = Total PAX` by month and split SCAD arrivals into covered/uncovered carriers/routes. Close when the residual has an explicit category and totals agree at identical grain. |
| **Hotel measure semantics and coverage** | SCAD/DCT publishes 5,807,555 hotel guests and 15,913,059 guest nights for 2024. The challenge sums to 5,074,677 `New Arrivals` and 14,688,200 daily `Guests`. Monthly correlations are 0.942 and 0.983 respectively. The stronger guest-nights match suggests that summing daily `Guests` counts guest person-nights. It does **not** establish identical establishment coverage: challenge/SCAD is 84.3%–90.3% for arrivals and 90.1%–94.7% for guest nights. | Ask DCT for included property IDs/types, reporting completeness, residence versus nationality definitions, same-day handling, and whether `Guests` is in-house guests per day. Rebuild both annual totals from the same included property set and compare monthly guest, guest-night, and stay-length ratios. Close when all three reconcile within published rounding. [DCT says its hotel system changed in Jan 2023](https://dct.gov.ae/en/who.we.are/reports.statistics.aspx), so validate historical periods separately. |
| **No shared air-to-hotel observation** | Route-day passenger counts and nationality-day hotel counts are separate aggregates. `Departure Country Name` is embarkation point; hotel `Nationality` is passport nationality; `Domestic` is residence. No traveler, booking, arrival-to-check-in, or aggregate conversion key is supplied. Even perfect flight schedules would not identify who stayed in a hotel. The [Statistics Canada 2024 Air Exit Survey](https://www150.statcan.gc.ca/n1/pub/24-25-0002/242500022021001-eng.htm) demonstrates a feasible design: one anonymized record contains air entry and hotel use, but its Canadian shares cannot calibrate Abu Dhabi. | Ask for a privacy-preserving weekly **joint** count by AUH arrival week, true trip origin, flight/route, P2P/transfer, residency/nationality, and paid accommodation use. Include an explicit unknown/other-accommodation group and survey/sample weights if derived from a survey. Reconcile margins to the flight and hotel systems; only then estimate conversion with confidence intervals. |
| **Causal interpretation** | A high monthly correlation between the challenge and SCAD hotel series checks whether they measure a similar hotel trend. It does not establish that additional flights generated those stays; seasonality, events, hotel inventory, fares, and other factors may move together. Route openings can offer natural contrasts, but this dataset has no matched source-market lodging outcome at equivalent grain. | Once the joint table or source-market lodging series exists, define route launch/event windows in advance, use comparable unaffected routes/markets, control for calendar and capacity, and test pre-trends. Until then, label route-based outputs as scenarios or associations, not causal forecasts. |

## What can be done now

1. Use the existing official schedule comparison as a **route-existence audit**;
   expand it to a stratified sample of airlines and times. Record whether each
   source is a schedule, a flight movement, or a passenger observation.
2. Use the revised `scripts/validate_public_2024.py` output to compare **both**
   guest arrivals and guest nights month by month. The February SCAD workbook
   spells its guest-night unit `Nihgt`; the extractor handles that source typo
   explicitly.
3. Build a coverage matrix from the challenge's 98 departure-city labels and
   34 airlines against published 2024 AUH routes. Each absent route should
   remain a coverage question until airport/DCT inclusion rules are obtained.
4. If historical movement access is available, pilot one AUH arrival day with
   OpenSky or an airport feed. Keep schedule time, inferred/actual arrival time,
   and challenge date in separate columns. Do not attach passenger counts to
   individual flights when the workbook has multiple flights per route-day.

## Minimum data-owner request

Request (a) a corrected data dictionary covering all five workbooks and
2022 monthly versus 2023+ daily flight grain, (b) the route/airline/property
coverage list and monthly reconciliation totals, (c) flight date and timezone
rules plus a small flight-number/timestamp sample, and (d) the joint weekly
air-entry × accommodation table above. An airport movement or OpenSky feed can
help with (c), but public schedule and ADS-B data cannot substitute for (d).

## Evidence limits

The SCAD hotel publication cites DCT as its underlying source, so it is an
independent publication/check of totals rather than an independent collection
of guest stays. The route schedule checks cover selected services, not the
whole flight table. The Canada survey provides methodological proof of a
linked air/hotel observation, not a UAE conversion estimate.
