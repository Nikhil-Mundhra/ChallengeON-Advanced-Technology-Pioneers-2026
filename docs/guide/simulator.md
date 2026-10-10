# Simulator

## Outputs

For one source market and one season, the simulator compares a baseline week with a scenario week.

| Output | Content |
| :--- | :--- |
| Conversion chain | Seats → passengers → P2P passengers → hotel new arrivals → hotel guests, baseline vs scenario |
| Waterfall | Guest lift split sequentially across 5 levers; the parts sum to the total |
| Hybrid lift | Structural lift plus the residual adjustment |
| Uncertainty | P10 / P50 / P90 of total guests and of the lift (Monte Carlo) |
| Tornado | Swing in guests for a fixed up and down shock to each lever |
| Briefing | One-paragraph summary |

Method: [planning model](../model/planning.md).

## `twin simulate`

Source: `src/tourism_twin/cli/simulate.py`.

```bash
twin simulate --market "UNITED KINGDOM" --season Winter_Peak \
  --delta-freq 2.0 --gauge 290.0 --delta-lf 0.02
```

| Argument | Default | Meaning |
| :--- | :---: | :--- |
| `--market` | `UNITED KINGDOM` | One of the 21 modelled markets, or an unmodelled country (`SWEDEN`, `BRAZIL`) with its archetype's defaults (cold start) |
| `--season` | `Winter_Peak` | `Winter_Peak` (Nov to Mar), `Spring_Shoulder` (Apr to May), `Summer_Trough` (Jun to Aug), `Autumn_Shoulder` (Sep to Oct) |
| `--delta-freq` | `2.0` | Added weekly round-trip flights; each adds `--gauge` inbound seats per week |
| `--gauge` | `290.0` | Seats per added flight (290 B787-9, 180 A320) |
| `--delta-seats-pct` | `0.0` | Proportional change in existing seats (`0.15` = +15%; `-1.0` = route closure) |
| `--delta-lf` | `0.02` | Absolute change in load factor (`0.02` = +2 pp) |
| `--delta-p2p` | `0.0` | Absolute change in P2P share |
| `--delta-mult-pct` | `0.0` | Proportional change in response multiplier (`0.05` = +5%) |
| `--delta-los` | `0.0` | Absolute change in the stay factor L (guests ÷ hotel arrivals) |

`DOMESTIC` has no aviation input: only `--delta-mult-pct` and `--delta-los` change domestic guests.

## Reading the briefing

| Section | Content |
| --- | --- |
| Executive recommendation | Weekly guest lift, % vs baseline, P10 to P90 range of the lift, holdout coverage, top tornado driver |
| Conversion chain | Weekly seats, passengers, P2P, hotel new arrivals, hotel guests (guest-days), load factor, P2P share, response multiplier; baseline vs scenario |
| Waterfall | Lift in the order seats, load factor, P2P share, response multiplier, stay factor; a lever's share depends on its position |
| Uncertainty | P10/P50/P90 of simulated total guests and of the lift; deterministic for identical inputs; the P10 of the lift can be negative when capacity is added |
| Tornado | Swing for ±15% seats, ±4 pp load factor, ±5 pp P2P share, ±10% multiplier, ±0.5 stay factor, ranked |

## Market directory

Archetypes: `src/tourism_twin/domain/archetypes.py`. Ratios of sums over the train split of `weekly_market_panel.parquet`. Guests per new arrival is a stock-to-flow ratio; pooled markets mix nationalities. The simulator uses the per-season values in `structural_calibration.json`.

| Market | Archetype | Guests per new arrival | Arrivals per P2P pax |
| :--- | :--- | :---: | :---: |
| INDIA | Resident / VFR | 3.25 | 0.169 |
| RUSSIAN FEDERATION | Direct Leisure | 4.96 | 1.484 |
| UNITED KINGDOM | Direct Leisure | 4.79 | 0.994 |
| UNITED STATES OF AMERICA | Hub-Mediated | 3.84 | 2.094 |
| GERMANY | Direct Leisure | 4.94 | 0.989 |
| CHINA | Hub-Mediated | 2.12 | 6.011 |
| SAUDI ARABIA | Regional GCC | 2.47 | 0.399 |
| FRANCE | Direct Leisure | 3.55 | 1.236 |
| EGYPT | Resident / VFR | 5.01 | 0.116 |
| KUWAIT | Regional GCC | 3.28 | 0.594 |
| ITALY | Direct Leisure | 3.70 | 0.493 |
| KAZAKHSTAN | Highly Seasonal | 3.84 | 0.465 |
| ISRAEL | Direct Leisure | 2.92 | 0.877 |
| PHILIPPINES | Resident / VFR | 3.25 | 0.582 |
| OMAN | Regional GCC | 1.63 | 0.423 |
| OTHER_EUROPE | Direct Leisure | 3.83 | 0.764 |
| OTHER_ASIA_PACIFIC | Hub-Mediated | 3.18 | 2.218 |
| OTHER_MENA | Regional GCC | 3.14 | 0.174 |
| OTHER_AMERICAS_AFRICA | Hub-Mediated | 3.96 | 6.395 |
| OTHER_EURASIA | Highly Seasonal | 3.77 | 0.165 |
| DOMESTIC | Domestic Staycation | 2.32 | n/a (no flights) |

A multiplier above 1 means more hotel arrivals of that nationality than P2P passengers from the same-named country.
