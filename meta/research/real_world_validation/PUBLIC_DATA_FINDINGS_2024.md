# Independent public-data checks (7 October 2026)

## What is now established

The challenge's flight route-days are substantially anchored to real Etihad
schedules, and its 2024 hotel `New Arrivals` series follows the shape of an
independent official monthly series. Neither result proves that the challenge's
passenger or guest counts are exact, nor that a particular passenger used a
hotel. The data lacks flight numbers, flight timestamps, guest check-in times,
and a shared traveler or booking key.

## Official Abu Dhabi hotel and airport tables

I downloaded 12 monthly 2024 hotel Excel workbooks and the 2024 transport
Excel workbook from the [Statistics Centre – Abu Dhabi publication index](https://scad.gov.ae/transport-services?IndicatorID=5107&ThemeID=3294949&tab=KSI).
The original files are under `sources/`; their individual URLs, byte counts,
and SHA-256 hashes are recorded in `scad_2024_validation.json`. The extract
and challenge comparison is `scad_2024_monthly_comparison.csv`. Reproduce it
with `.venv/bin/python scripts/validate_public_2024.py` (add `--download` if
source files are missing).

| 2024 measure | Official SCAD | Challenge workbook | What can be concluded |
| --- | ---: | ---: | --- |
| Monthly hotel guests summed over 2024 vs `New Arrivals` | 5,807,555 | 5,074,677 | Challenge is 732,878 lower, or 12.6% of SCAD. Different coverage or definitions remain possible. |
| Monthly hotel guest nights summed over 2024 vs daily `Guests` | 15,913,059 | 14,688,200 | Challenge is 1,224,859 lower, or 7.7% of SCAD. This supports interpreting summed daily `Guests` as guest person-nights, pending DCT's definition. |
| Airport arrivals vs inbound route-day `Total PAX` | 14,522,288 | 11,222,004 | Challenge is 3,300,284 lower, or 22.7% of SCAD. This suggests incomplete route/airline coverage or a different passenger definition. |

SCAD hotel table 4's nationality groups reconcile to each monthly hotel total
within 5 guests, the expected scale for values rounded to thousands. SCAD's
airport table 6 region counts reconcile exactly to its 2024 total; its note
says transit passengers are excluded. The challenge `New Arrivals` and SCAD
hotel guests have Pearson **r = 0.942** across the 12 monthly observations;
omitting any one month gives r between 0.926 and 0.954. The challenge total is
84.3%–90.3% of SCAD's monthly total. This is a **descriptive shape check**, not
evidence of a shared row population or a flight-driven effect. For comparison,
challenge P2P vs SCAD hotel guests has r = 0.628 across those 12 months.
Challenge summed daily `Guests` and SCAD guest nights have monthly **r =
0.983**, with challenge/SCAD ratios of 90.1%–94.7%. The challenge's
`Guests`/`New Arrivals` ratio is higher than SCAD guest nights/hotel guests in
every 2024 month. A difference in covered properties or stay lengths could
produce this pattern; the aggregates alone do not identify the reason.

SCAD classifies hotel guests by **nationality**. The challenge's `Domestic`
category is a **residence group**, with nationality blank. Comparing its
2,623,864 new arrivals directly to SCAD's 1,104,253 UAE-nationality guests
would confuse two different concepts. The total series comparison above still
needs a DCT coverage dictionary.

The SCAD hotel tables cite DCT as their underlying source. DCT's
[2024 Hotel Performance Report](https://dct.gov.ae/DataFolder/reports/hotel-establishment/2019/2024%20Hotel%20Performance%20Report.pdf)
reports approximately 5.8 million guests, consistent with the 5,807,555
obtained by adding SCAD's monthly tables. SCAD is an independent *publication*
of the same underlying hotel administration, not an independent collection of
hotel stays. DCT [warns that its hotel reporting system changed in January
2023](https://dct.gov.ae/en/who.we.are/reports.statistics.aspx); the checks
here stay within 2024.

## Etihad route schedules and timestamps

`etihad_2024_route_checks.json` is a reproducible route-day check from
`.venv/bin/python scripts/check_etihad_route_days.py`. Published schedules are
from Etihad; the windows below are selected examples and do not audit the
entire workbook.

| Challenge departure city | Published inbound flight and scheduled AUH arrival (local) | Selected schedule window | Route-days in challenge |
| --- | --- | --- | ---: |
| Gassim / Al Qassim | [EY0628, 13:20, Mon/Wed/Fri/Sat](https://www.etihad.com/en-us/news/etihad-airways-explores-new-horizons-in-the-middle-east-with-the-launch-of-its-newest-destination) | 24 Jun–26 Oct 2024 | 72 of 72 scheduled days |
| Antalya | [EY0540, 19:45, Tue/Thu/Sat](https://www.etihad.com/en-ae/news/etihad-airways-expands-schedule-with-two-stunning-new-destinations-and-additional-flights) | 15 Jun–14 Sep 2024 | 40 of 40 scheduled days |
| Jaipur | [EY0367, 13:00, Mon/Wed/Fri/Sun](https://www.etihad.com/en-in/news/etihad-airways-adds-new-route-to-northwest-india-with-four-weekly-flights-to-jaipur) | 16 Jun–26 Jul 2024 | 23 of 24 scheduled days; 22 Jul absent |

These matches are strong evidence of schedule grounding. They do not show
whether each aircraft operated or how many passengers were on board. The
workbook has neither a flight number nor a time, and the one missing Jaipur
date could reflect cancellation, coverage, or another data issue.

A date-semantics warning: Etihad's [Kozhikode schedule](https://www.etihad.com/en/news/new-year-new-flights-as-etihad-welcomes-2024-with-more-destinations-to-india)
lists its first return flight EY0249 leaving CCJ on 1 January 2024 at 21:30
and arriving AUH at **00:05 on 2 January**. The challenge has a Kozhikode →
Abu Dhabi row dated **1 January**. Its `Date` may therefore denote the origin
departure date, a schedule/service date, or another convention. It must not be
treated as an AUH arrival timestamp until DCT defines it. The same official
announcement supplies EY0293 from Thiruvananthapuram, scheduled to arrive AUH
at 12:55 on 1 January, illustrating that the offset is route-specific.

Earlier checks in the [research README](README.md) show plausible first dates
for Boston and Osaka but absent Copenhagen and Lisbon routes. Those absences
also make a coverage statement essential.

## A real, directly linked air–hotel benchmark

I downloaded Statistics Canada's [2024 Visitor Travel Survey Air Exit Survey
public-use microdata](https://www150.statcan.gc.ca/n1/pub/24-25-0002/242500022021001-eng.htm)
(`sources/statcan_vts_2024_air_exit_csv.zip`, 45,056,310 bytes; SHA-256 in
`statcan_2024_air_hotel_metadata.json`). Its 13,204 anonymized survey records
represent commercial-air visitors and include, on the **same record**, route
of entry into Canada (`VRTEN`), province of entry (`VGPRVENP`), hotel use at
up to ten visited locations (`VACCV01A`–`VACCV10A`), and survey weight
(`VWEIGHTP`). The definitions come from the codebook bundled in the zip.

`statcan_2024_air_hotel_summary.csv` gives a reproducible weighted tabulation.
Among records with a valid hotel response, **35.8%** used a hotel at one or
more visited locations. By route of entry, the weighted descriptive shares
are **40.8%** for travelers entering from the US only, **30.1%** for direct
entry from another country, and **33.0%** for entry via the US. Reproduce with
`.venv/bin/python scripts/analyze_statcan_air_hotel.py`.

This is the kind of **within-traveler air-entry × lodging observation** that
the Abu Dhabi challenge lacks. It is Canadian survey data, with broad route
categories rather than a flight number or hotel booking, so it cannot train or
validate Abu Dhabi conversion rates directly. Differences between route
groups are descriptive and may reflect traveler purpose, origin, length of
stay, and season; they are not causal effects of routing.

## Best next data request for Abu Dhabi

Request a privacy-preserving weekly table at the grain:

`AUH arrival week × true trip origin × route/flight identifier × transfer or
P2P status × residency or nationality × paid accommodation used`.

Start with counts, not passenger or guest identities. Also request the
challenge workbook's route, airline, and nationality coverage rules and a
definition of `Date`. If a route identifier and arrival time can be supplied,
scheduled Etihad times can be checked against flight status or ADS-B data;
without them, timestamp matching would be speculative.

The [blocker register and resolution plan](BLOCKERS_AND_RESOLUTION.md) records
the remaining gaps, tests completed, and specific data needed to close each
one.

The [8 October flight pilot](FLIGHT_DATE_AND_COVERAGE_PILOT.md) adds a
12-destination Etihad sample: Copenhagen, Santorini, Mykonos, and
Bali/Denpasar have no 2024 Etihad rows in the challenge despite 2024 Etihad
schedule or launch evidence. The attempted public OpenSky historical AUH
arrival request returned HTTP 403, so this pilot did not observe EY0249's
actual arrival.
