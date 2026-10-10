# Nationalities

## Pooled nationality model (`nowcast/pooling.py`)

| Fact |
| --- |
| The 30 nationalities of the 6 pooled markets are predicted directly by `POOLED_NATIONALITIES` |
| One model per stay family: short (Saudi Arabia, Kuwait, Oman, Bahrain, Qatar; `SHORT_STAY_FAMILY`) and long (every other international nationality) |
| Fitted on all 45 nationalities' own arrivals: shared arrivals kernel, season, weekday and events; base stock proportional to the nationality's 90-day arrivals; per-nationality scale shrunk toward the family by `GroupScale` (ridge 100) |
| Training rows weighted by `Recency(365)` |
| Intervals from that model's rolling-origin errors per nationality |
| The 15 single-nationality markets keep the market model |

## Fallback split (`nowcast/disaggregation.py`)

| Fact |
| --- |
| A pooled market's prediction is split across its nationalities by share = trailing 7-day new arrivals × the nationality's training guests ÷ new arrivals, normalised per market and day |
| Nationality bounds add the split's log-error variance (s.d. 0.18 to 0.25 per pooled market, last 365 training days) to the market's |

Results: [nowcast validation](../results/nowcast-validation.md#nationalities).
