# Premium-cabin share of Etihad P2P arrivals by departure origin

Descriptive flight analysis for issue #4. Question: *among Etihad's recorded
P2P passengers arriving from each departure country, what share travelled in
business or first class, and how does that share vary over time?*

Reproduce with:

```bash
python scripts/premium_share_profile.py
```

Writes three files here: `premium_share_country.csv` (origin × reporting
period), `premium_share_country_monthly.csv` (origin × month),
`premium_share_city.csv` (origin × departure city, main period).

## Population

Etihad Airways, daily-grain rows, 2023-01-01 onward.

- **Etihad only** — avoids mixing airlines with different cabin products and
  connecting-passenger mixes. It does not remove differences in aircraft,
  routes, season, or passenger purpose; those remain part of the description.
- **2023 onward, daily rows only** — 2022 records are monthly aggregates with
  no cabin detail.
- **P2P passengers** — the journey ends at Abu Dhabi; relevant to
  destination-market profiles. Transfer and transit counts are reported as
  separate descriptors, not mixed into the share.

**Reporting periods.** The MAIN period is 2023-01 to 2025-07, aligned with
the team's guest-training history. An EXTENDED period through 2026-02 is
labelled separately. Jan–Feb slices for each year let 2026 be compared
like-for-like; never compare a partial 2026 against full earlier years.

## Column definitions

All shares are **ratios of summed counts** — each passenger gets equal
weight, not each day. (Averaging daily percentages would answer a different
question.)

| Column | Definition | Answers |
| --- | --- | --- |
| `premium_p2p_share_pct` | 100 × Σ(first + business P2P) ÷ Σ total P2P | How premium-heavy are destination-bound passengers? (primary) |
| `premium_classified_share_pct` | 100 × Σ(first + business P2P) ÷ Σ(first + economy + business P2P) | Sensitivity measure: premium share among **cabin-classified** P2P. Cabin-classified totals do not exceed `total_p2p` in these aggregates (gap 0–2.08%). Row-level evidence points at infants: the gap equals the infant count on 74% of Etihad rows, never exceeds it, and correlates with it at r ≈ 0.70 — consistent with lap infants not being cabin-classified. This remains an inference, not a confirmed mechanism. |
| `unclassified_p2p_pct` | 100 × (P2P − classified P2P) ÷ P2P | Size of the denominator gap (≈ infant share of P2P, per above). |
| `premium_seat_share_pct` | 100 × Σ(first + business seats) ÷ Σ total seats | How premium-heavy is offered capacity? |
| `transfer_share_pct` | 100 × Σ transfer ÷ Σ PAX | How strongly the origin feeds connecting traffic. Transfer status does not establish whether the passenger entered Abu Dhabi or stayed overnight. |
| `p2p_pax` | Σ total P2P | Volume behind the percentage — tiny samples (Kazakhstan 69, Azerbaijan 55) make their shares unreliable. |

No share ratios and no confidence intervals: these are recorded aggregate
counts, not an independently sampled survey; passengers share flights,
routes and seasons, so a binomial interval would suggest unjustified
precision.

## Findings (main period, 2023-01 → 2025-07)

- Premium P2P share spans an order of magnitude: **Oman 3.0% → USA 39.3%**.
- Premium-heavy origins are long-haul Western and North-Asian: US 39.3,
  Canada 28.6, Japan 26.2, Poland 25.8 (small sample), France 24.5, UK 21.5,
  Switzerland 20.8, Spain 19.1.
- Economy-dominated origins are GCC/regional and South Asian: Oman 3.0,
  Israel 3.2, Kuwait 3.9, Egypt 4.6, Jordan 4.7, Saudi 5.0, Bahrain 5.0,
  India 5.8.
- **Denominator sensitivity is modest**: the classified-denominator measure
  shifts shares by up to 0.5 pp (Canada 0.51, US 0.46) and swaps some close
  rankings (Netherlands/South Korea; Saudi Arabia/Bahrain). The broad
  premium-heavy vs economy-heavy pattern is preserved.
- **The pooled number hides real change on India**: shares were approximately
  unchanged in 2023–2024 (6.2 → 6.3), then declined in 2025 (4.3). The Jan–Feb
  slices fall 17.7 → 8.2 → 5.2 → 3.6 (2023→2026). Decomposing the mechanism:
  premium *counts* grew with P2P in 2023–24 (+43% premium vs +41% P2P) but
  **fell in absolute terms in 2025** (26.8k → 23.3k, −13%) while P2P grew
  +29%. Within-city shares also fell (Mumbai 8.1 → 4.3, Delhi 9.0 → 7.4,
  Chennai 3.3 → 1.8), so the decline is not only mix-shift — though new
  lower-premium-share cities added in 2024 (Jaipur, Kozhikode, Trivandrum)
  dilute the pooled figure further. Volume context: full-year P2P +81.5%
  (2023→2025); Jan–Feb P2P +213% (2023→2026). Mechanism beyond this
  decomposition is unconfirmed.
- **City-level checks matter**: US cities are consistent (NY 41.7, Chicago
  36.2, Washington 39.8) but India conceals a ~2.5× spread between
  higher-premium-share cities (Delhi 9.2, Mumbai 7.1) and
  lower-premium-share cities (Chennai 3.5, Kochi 4.3, Ahmedabad 3.7).

## Assumptions and limits

| Boundary | What is accepted |
| --- | --- |
| Recorded counts are usable | Complete cells do not guarantee accurate classification. The denominator check above is **one** reconciliation check; passenger identities (`pax = p2p + transfer + transit`), seat totals, missing counts, and duplicate keys are separate checks covered by the lake build, not re-verified by this table. |
| Departure country defines the descriptor | Traffic *from that origin*, including expatriates and third-country nationals — not the nationality of hotel guests. |
| Counts can be added across records | Each route-airline-date record contributes once. |
| P2P is relevant to destination demand | P2P includes residents and non-hotel visitors; it is not a hotel-arrival count. |
| The selected period defines the result | No assumption the shares persist in future. |
| Cabin mix is descriptive | Premium share does not establish spending, stay duration, hotel choice, or any causal effect. |

## Defensible conclusion

Premium P2P share differs substantially across recorded departure origins —
roughly 3% on GCC/regional origins versus 25–40% on North American and
Japanese origins in the main period — **with meaningful variation over time
and between cities** (the India trend shows why every figure needs a period
label). That supports a dated flight-origin profile. It does not establish
passenger purpose, nationality, hotel behaviour, or permanence; nationality
profiles may cite it as context under the approximate origin↔nationality
mapping.
