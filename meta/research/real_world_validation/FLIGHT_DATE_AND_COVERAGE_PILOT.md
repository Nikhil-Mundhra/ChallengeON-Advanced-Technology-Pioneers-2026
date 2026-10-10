# Flight-date and route-coverage pilot (8 October 2026)

## Historical arrival attempt

Etihad's [Kozhikode launch timetable](https://www.etihad.com/en/news/new-year-new-flights-as-etihad-welcomes-2024-with-more-destinations-to-india)
lists EY0249 departing CCJ on 1 January 2024 at 21:30 local and scheduled to
arrive AUH at **00:05 on 2 January**. The challenge has an Etihad Kozhikode
route-day row dated **1 January**, with `Total PAX = 157`. The row has no flight
number, so that passenger count must not be attributed to EY0249 without a
flight-level source.

I attempted a public [OpenSky AUH arrivals](https://openskynetwork.github.io/opensky-api/rest.html)
request covering 1 January 18:00 through 2 January 06:00 UTC, which brackets
the scheduled arrival:

```text
GET https://opensky-network.org/api/flights/arrival?airport=OMAA&begin=1704132000&end=1704175200
HTTP 403: You cannot access historical flights
```

This is an **access blocker**, not evidence that EY0249 did or did not operate.
OpenSky's [FAQ](https://opensky-network.org/about/faq) describes historical
access for eligible researchers and states that its data has no passenger
counts. We found no primary public record of EY0249's *actual* 1–2 January
arrival in this pilot. The Etihad timetable establishes the scheduled
overnight date shift; the challenge row remains ambiguous between service
date, origin departure date, and another reporting convention.

**Closure path:** obtain either (1) authorized historical AUH movement data,
or (2) an airport/DCT sample with flight number, origin departure timestamp,
AUH scheduled and actual arrival timestamps, timezone, and the challenge
reporting date. Test overnight and same-day arrivals separately. A movement
feed alone cannot map the route-day passenger aggregate to a particular
flight if more than one service shares the same route and day.

## Reproducible 2024 Etihad route sample

Run `.venv/bin/python scripts/build_2024_etihad_coverage_matrix.py` to rebuild
[`etihad_2024_coverage_matrix.csv`](etihad_2024_coverage_matrix.csv). It checks
12 specifically cited destinations against 2024 challenge Etihad route-days,
using explicit challenge city labels (`Trivandrum` for Thiruvananthapuram and
`Gassim` for Al Qassim). Eight have rows. Four have **none**:

| Published 2024 service | Primary evidence | Challenge Etihad route-days |
| --- | --- | ---: |
| Copenhagen, year-round at four weekly from 31 March | [Etihad summer 2024 schedule](https://www.etihad.com/en-us/news/etihad-unleashes-sizzling-summer-schedule) | 0 |
| Santorini, summer service | [Etihad June 2024 launch report](https://www.etihad.com/en-us/news/etihad-airways-celebrates-launch-flights-to-eight-more-destinations-this-june) | 0 |
| Mykonos, returning summer service | [Etihad June 2024 launch report](https://www.etihad.com/en-us/news/etihad-airways-celebrates-launch-flights-to-eight-more-destinations-this-june) | 0 |
| Bali/Denpasar, four weekly from late June | [Etihad inaugural Bali report](https://www.etihad.com/en-de/news/etihad-airways-celebrates-launch-of-direct-flights-to-bali) | 0 |

These omissions strengthen the case that the challenge flight extract is a
subset or uses undocumented exclusions. They do not quantify missing passenger
volume: the source releases give frequencies, not actual 2024 inbound
passenger totals. Lisbon was omitted from this 2024 sample because the earlier
source confirms a 2023 launch but does not establish its 2024 operating window.
Nairobi was omitted because a pre-launch schedule is weaker evidence than a
confirmed 2024 operation.

**Closure path:** request DCT/airport coverage rules and monthly inbound
passenger totals by operating carrier and origin airport. Reconcile the
challenge's 11.22 million `Total PAX` to SCAD's 14.52 million 2024 airport
arrivals with explicit excluded categories. Route labels and press releases
alone cannot allocate the 3.30 million gap.

## Additional carrier audit

Run `.venv/bin/python scripts/build_2024_multicarrier_coverage_matrix.py` to
rebuild [`multicarrier_2024_coverage_matrix.csv`](multicarrier_2024_coverage_matrix.csv).
This checks 29 destinations **named** in [Air Arabia Abu Dhabi's 27 December
2024 network announcement](https://press.airarabia.com/air-arabia-abu-dhabi-takes-off-to-yekaterinburg/)
and six routes from IndiGo's 2024 releases. It is a cited sample/network
snapshot, not a complete 2024 operating schedule.

| Carrier and source sample | Present in challenge | Absent in challenge |
| --- | ---: | ---: |
| Air Arabia Abu Dhabi, 29 named destinations | 20 | 9 |
| IndiGo, six announced inbound routes | 6 | 0 |

The nine absent Air Arabia Abu Dhabi city labels are **Almaty, Baghdad,
Chittagong, Colombo, Dhaka, Faisalabad, Kathmandu, Multan, and Tbilisi**.
Colombo has extra support beyond the December network list: the carrier
[reported its inaugural flight in December 2023](https://press.airarabia.com/air-arabia-abu-dhabi-marks-its-first-flight-to-colombo/)
and [listed Colombo as a 2024 route](https://www.airarabia.com/sites/airarabia/files/gallery/G95078_E5_HBE_Nawras_Q4_Booklet_Oct-Dec24_Screen.pdf).
These gaps are substantial enough to warrant a route-level coverage rule,
though no public source here supplies their missing passenger counts.

The IndiGo sample shows why an announced start is not always the best date
anchor. [IndiGo initially announced](https://www.goindigo.in/press-releases/indigo-announces-direct-flights-between-abu-dhabi-and-kannur.html)
Kannur–AUH for **9 May 2024**, while [Kannur airport later stated](https://www.linkedin.com/posts/airportcnn_kannurinternationalairport-abudhabi-kial-activity-7192471653904261120-IIJP)
daily service would start **18 May**. The challenge's first IndiGo Kannur row
is **18 May**. This is a stronger real-world alignment than the original
announcement suggests, but it still does not identify an individual flight or
verify its passenger count. The other five IndiGo routes all appear, allowing
for city spelling aliases and possible one-day date offsets.
