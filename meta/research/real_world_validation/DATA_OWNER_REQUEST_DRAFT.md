# Draft data request to DCT / airport data owners

Prepared 8 October 2026. This is a draft for review, not a sent request.
The [ChallengeON DCT statement](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en)
says that no pre-joined table will be supplied and that all challenge data is
aggregate. Its listed data pack also includes schedule/capacity, reference,
passenger, and monthly hotel-performance material beyond the five files we
currently see. The first question to organizers should be whether that
additional material is available now or only after team selection. The joint
air-entry × accommodation table below is a **future validation/partnership
request**, not a condition for submitting a transparent challenge prototype.

## Purpose

We are validating the supplied flight and hotel challenge workbooks against
2024 public statistics. The flight data has route-airline-day passenger
aggregates but no flight identifier or time; the hotel data has
nationality/residence-day aggregates but no air-arrival link. We seek aggregate
definitions and a small validation extract, not names or passenger manifests.

## Requested items

1. **Corrected dictionary for all five supplied workbooks.** Define each
   field's unit, timezone, date convention, route/airline/property coverage,
   missing and suppressed values, and aggregation grain. In particular,
   explain the flight file's 2022 monthly versus 2023 onward daily records;
   whether `Date` means origin departure, AUH scheduled/actual arrival, or
   reporting/service date; whether `Guests` means in-house guests for each
   day; and whether `New Arrivals` means hotel check-ins.
2. **2024 flight reconciliation.** Monthly AUH inbound passenger counts at
   matching scope, split into P2P, transfer, transit, and any remaining
   passenger category. Supply counts of excluded carriers, origin airports,
   charters, codeshares, terminals, infants, and cancelled services, with
   inclusion rules. Please explain why the challenge totals 11,222,004
   `Total PAX` while [SCAD's Zayed airport arrivals table](https://scad.gov.ae/transport-services?IndicatorID=5107&ThemeID=3294949&tab=KSI)
   totals 14,522,288 excluding transit for 2024. The attached
   [`etihad_2024_coverage_matrix.csv`](etihad_2024_coverage_matrix.csv)
   highlights four published Etihad destinations absent from the challenge;
   [`multicarrier_2024_coverage_matrix.csv`](multicarrier_2024_coverage_matrix.csv)
   identifies nine named Air Arabia Abu Dhabi destinations absent as well.
3. **2024 hotel reconciliation.** Monthly hotel guests, guest nights, and
   establishment counts for the **same properties represented in the
   challenge**, plus the equivalent full-emirate totals. Clarify whether
   `Domestic` is residence and how it relates to nationality. This should
   explain the challenge's 5,074,677 `New Arrivals` versus SCAD's 5,807,555
   hotel guests and 14,688,200 summed daily `Guests` versus SCAD's 15,913,059
   guest nights.
4. **Small flight-date validation extract.** For 20 selected 2024 AUH inbound
   services, including EY0249 from Kozhikode on 1 January, provide operating
   carrier, flight number, origin airport, origin-local departure date/time,
   AUH scheduled and actual arrival date/time, timezone, operation/cancellation
   status, and the `Date` used in the challenge aggregate. Include overnight
   and same-day arrivals. Flight-level passenger counts are useful if
   permitted, but not required for the date-semantics test.
5. **Privacy-preserving air-entry × accommodation table.** At weekly grain,
   provide joint counts by AUH arrival week, true trip origin region,
   P2P/transfer status, broad residency/nationality group, and accommodation
   outcome (paid hotel, other accommodation, no stay, unknown). A route or
   flight grouping would help if counts remain sufficiently large. Include
   the source/matching method, coverage period, sample weights if from a
   survey, and a suppressed/unknown bucket. Suppress small cells and provide
   reconciled margins; no individual identifiers are requested.

## Acceptance checks

- The flight-date rule explains the overnight EY0249 example and all 20
  sampled services without manual exceptions.
- Monthly flight categories sum to the published inbound total for the same
  airport and population, with each excluded category quantified.
- Monthly hotel arrivals and person-nights reconcile for the same property
  set, with a documented bridge to full-emirate SCAD totals.
- The joint table's flight and hotel margins are documented, and any
  unmatched/unknown share is reported. Conversion estimates will only be
  calculated within the population that the joint table actually covers.

## Official inquiry route

The [ChallengeON contact page](https://challengeon.atrc.ae/en) lists
`talents@atrc.ae` for student challenges. That is the most relevant channel
for a prompt question about the competition's data pack and mentorship.
[DCT's contact page](https://dct.gov.ae/en/contact.us.aspx) offers a general
government contact route, and [SCAD's statistical-data request
service](https://www.scad.gov.ae/w/statistical-data-request) is scoped mainly
to government and semi-government entities and may require an official letter
for unpublished data. The organizer route should be tried first for these
competition-specific questions. No inquiry has been sent from this workspace.
