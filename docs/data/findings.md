# Data findings

## Guests and markets

| # | Finding |
| --- | --- |
| 1 | Guests: 1,308 labelled days, then 212 test days |
| 2 | 45 guest nationalities vs 33 flight departure countries; the fields differ in meaning even when labels match. 12 nationalities have no flight-origin rows: Australia, Brazil, Czechia, Denmark, Finland, Mexico, Morocco, Norway, Pakistan, Romania, South Africa, Sweden |
| 3 | 2022 flights exist on 12 month-start dates only; daily flights start 2023-01-01. 2022 flights are isolated in `flight_monthly.parquet`; the `guest_flight_daily` view has NULL flight measures for 2022 dates |
| 4 | `*` (suppressed or unavailable) is kept as null: 264 new-arrival and 39,428 same-day values, flagged by `is_suppressed_arrival` and `is_suppressed_same_day` (840 and 40,004 including the 576 flagged absent grid rows). Same-day guests never exceed guests |
| 5 | Domestic demand is modelled separately; international flight changes create no domestic guests |
| 6 | Realized pax, P2P, load factor and new arrivals are known for calibration and unknown before a future flight operates |
| 7 | International train-split guests ÷ new arrivals = 3.61, a stock-to-flow ratio, not a measured length of stay |

## Flights (analysis)

| Finding | Meaning |
| --- | --- |
| `Total PAX = P2P + Transfer + Transit` on every row; transfer is about half of passengers | P2P passengers are the hotel-eligible ones; "transfer" means connecting at AUH |
| Etihad: 73% of passengers transfer; low-cost carriers about 0% | Transfer rate is an airline-mix property, not a cabin property |
| Business vs economy transfer: 64% vs 49% pooled, 69% vs 74% within Etihad | Cabin-class effects reverse under an airline control |
| Premium share vs transfer rate across Etihad routes: r = 0.44; spread narrows above about 9% premium share | Both track route type (long-haul hub feed vs regional); not causal |
| First-class transfer share 3.6% (Etihad 6.5%) | Implausible for a hub carrier; first-class transfer columns are suspect |
| Cabin columns exclude infants (gap to `Total P2P`: median 1, max 28) | Not a data error |
| Load factor up to 108% in daily data | Bounded, saturating input |
| 2022 flights are monthly; a day-of-week profile explains 26% of within-month variance at market level and gives 27% MAPE at route level | Flight features use daily data from 2023-01-01 only |
