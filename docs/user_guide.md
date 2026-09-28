# Abu Dhabi Tourism Digital Twin — User Guide

This guide is designed for DCT tourism planners, aviation strategists, and data science evaluators working with the **Abu Dhabi Tourism Digital Twin**.

---

## 1. Overview

The **Abu Dhabi Tourism Digital Twin** is an operational scenario simulator that translates aviation decisions (introducing flights, expanding seat capacity, adjusting load factors) into hotel guest demand outcomes.

Unlike black-box statistical forecasting, the Digital Twin provides:
1. **A Visible Conversion Chain:** Traceable steps from seats to passengers, P2P traffic, hotel arrivals, and daily guests.
2. **Exact Waterfall Attribution:** Mathematical decomposition of incremental guests with zero residual error.
3. **Monotonicity Protection:** Guarantees that capacity additions never produce counter-intuitive negative demand shifts.
4. **Empirical Uncertainty:** Calibrated P10, P50, and P90 confidence intervals derived from Beta sampling and historical block-bootstrap residuals.
5. **Non-Technical Executive Summaries:** Actionable recommendations ready for leadership briefings.

---

## 2. Command-Line Interface (CLI) Usage

The primary scenario simulator is located in [`scripts/run_scenario.py`](../scripts/run_scenario.py).

### Basic Command

```bash
# Activate environment
source .venv/bin/activate

# Simulate adding 2 weekly flights from the UK during Winter Peak
python scripts/run_scenario.py \
  --market "UNITED KINGDOM" \
  --season "Winter_Peak" \
  --delta_freq 2.0 \
  --gauge 290.0 \
  --delta_lf 0.02
```

### Supported Arguments & Levers

| Argument | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--market` | `str` | `"UNITED KINGDOM"` | Source market name (must match one of the 15 top markets, or `OTHER INTERNATIONAL`, `DOMESTIC`). |
| `--season` | `str` | `"Winter_Peak"` | Season: `Winter_Peak` (Nov–Mar), `Spring_Shoulder` (Apr–May), `Summer_Trough` (Jun–Aug), `Autumn_Shoulder` (Sep–Oct). |
| `--delta_freq` | `float` | `0.0` | Additional weekly round-trip flights (e.g. `+2.0` flights/week). |
| `--gauge` | `float` | `290.0` | Seat capacity per added flight (e.g. `290` for Boeing 787-9, `180` for Airbus A320). |
| `--delta_seats_pct` | `float` | `0.0` | Proportional seat capacity shift across existing flights (e.g. `0.15` for $+15\%$). |
| `--delta_lf` | `float` | `0.0` | Absolute shift in target load factor (e.g. `0.02` for $+2.0\%$ LF). |
| `--delta_p2p` | `float` | `0.0` | Absolute shift in P2P passenger share (e.g. `0.03` for $+3.0\%$). |
| `--delta_mult_pct` | `float` | `0.0` | Proportional shift in response multiplier from marketing (e.g. `0.05` for $+5\%$). |
| `--delta_los` | `float` | `0.0` | Shift in average length of stay days (e.g. `0.3` for $+0.3$ days). |

---

## 3. Interpreting Output Sections

When you execute a scenario, the Digital Twin outputs five structured sections:

### 1. Executive Briefing
A concise, non-technical paragraph designed for leadership. It states:
- Total weekly incremental guest-days.
- Percentage change relative to the historical baseline.
- 80% empirical scenario interval (P10 conservative to P90 optimistic).
- The single highest-leverage driver identified by sensitivity analysis.

### 2. End-to-End Conversion Chain
A side-by-side comparison of baseline vs. scenario rates across each operational stage:
- **Weekly Seat Capacity:** Scheduled seats offered.
- **Flight Passengers (Pax):** Expected passengers based on simulated load factor.
- **Point-to-Point (P2P):** Passengers deplaning in Abu Dhabi (excluding transfer/transit).
- **Hotel New Arrivals:** Estimated weekly flow of new check-ins.
- **Hotel Guests (Guest-Days):** Daily active guest stock multiplied over the week.

### 3. Exact Waterfall Attribution
Decomposes total incremental guest-days into 5 independent operational drivers:
$$\Delta Guests = \Delta G_{Seats} + \Delta G_{LF} + \Delta G_{P2P} + \Delta G_{Mult} + \Delta G_{Stay}$$
- The sum of components **exactly matches** the total net lift with $0.000000$ discrepancy.

### 4. Uncertainty Quantification
Rather than assuming a Gaussian distribution, the Digital Twin reports:
- **P10 (Conservative / Downside):** 10th percentile demand outcome under adverse operational conditions.
- **P50 (Median Expectation):** Expected central trajectory.
- **P90 (Optimistic / Upside):** 90th percentile demand outcome under favorable operational conditions.

### 5. Tornado Sensitivity Ranking
Evaluates the elasticity of hotel guest demand with respect to each lever under standard shocks:
- Identifies which operational lever creates the greatest swing for that specific market archetype.

---

## 4. Market Archetype Directory

| Market | Assigned Archetype | Baseline LOS | Baseline Conversion | Strategic Behavior |
| :--- | :--- | :---: | :---: | :--- |
| **India** | Resident / VFR | 3.37 days | 0.172 | High P2P traffic, large expat diaspora staying with family. Highly sensitive to seat volume. |
| **Russian Federation** | Direct Leisure | 4.97 days | 1.542 | Long vacation stays, extreme winter sun preference, high hotel capture. |
| **United Kingdom** | Direct Leisure | 4.87 days | 0.995 | High hotel capture, long vacation stays, responsive to route frequency. |
| **China** | Hub-Mediated | 2.26 days | 6.878 | High visitor footprint entering via connecting flights and regional hubs. |
| **Germany** | Direct Leisure | 4.94 days | 0.986 | Strong winter preference, high hotel capture rate. |
| **Saudi Arabia** | Regional GCC | 2.47 days | 0.397 | Short-haul leisure, strong summer school break and long-weekend elasticity. |
| **United States** | Hub-Mediated | 3.84 days | 2.085 | Long-haul visitors entering via European/Gulf hubs or DXB transfers. |
| **Kuwait** | Regional GCC | 3.28 days | 0.592 | High summer holiday surge to indoor Abu Dhabi attractions. |
| **France** | Direct Leisure | 3.55 days | 1.232 | Cultural and leisure tourists with strong winter preference. |
| **Egypt** | Resident / VFR | 5.01 days | 0.116 | High diaspora / business traffic, lower hotel conversion rate. |
| **Italy** | Direct Leisure | 3.70 days | 0.492 | Leisure tourists with seasonal winter peaks. |
| **Kazakhstan** | Highly Seasonal | 3.84 days | 0.463 | Severe winter sun preference with low summer presence. |
| **Israel** | Direct Leisure | 2.92 days | 0.870 | Leisure visitors responsive to direct connectivity. |
| **Armenia** | Highly Seasonal | 4.98 days | 4.980 | High winter peak, long average stay. |
| **Oman** | Regional GCC | 1.63 days | 0.422 | Shortest stay duration (weekend driving/flying cross-border traffic). |
| **Other International** | Emerging / Sparse | 3.53 days | 0.409 | 30 pooled markets under regularized Bayesian shrinkage. |
| **Domestic** | Domestic Staycation | 2.35 days | 1.000 | UAE resident staycations and corporate events. Modeled separately. |

---

## 5. Python API Usage

To embed the simulator into automated pipelines or custom dashboards:

```python
from engine.simulator import TourismDigitalTwin
from engine.structural import ScenarioLever

# Instantiate simulator (loads calibrated structural and residual models)
twin = TourismDigitalTwin()

# Define scenario
lever = ScenarioLever(
    market="GERMANY",
    delta_frequency=1.0,      # +1 weekly flight
    aircraft_gauge=250.0,     # A330 / 250 seats
    delta_load_factor=0.03,   # +3% load factor
)

# Run simulation
report = twin.run_scenario(
    market="GERMANY",
    season="Winter_Peak",
    lever=lever,
    n_draws=1500,
)

# Access results
print(f"Incremental Guests: {report.structural_result.delta_guests:+,.0f}")
print(f"Conservative P10:   {report.uncertainty_bands.delta_p10:+,.0f}")
print(f"Optimistic P90:     {report.uncertainty_bands.delta_p90:+,.0f}")
print(f"Executive Summary:  {report.recommendation_summary}")
```

---

## 6. Interactive Web Simulator

The solution includes a self-contained, interactive single-page web simulator located in `app/`. It requires no external frontend build tools or internet connection.

### Launching the Web App

```bash
# Start the web simulator on port 8080
python scripts/run_app.py --port 8080
```

Open `http://localhost:8080` in your web browser.

### Key Capabilities

1. **Preset Scenarios:** Instant one-click selection of policy scenarios:
   - UK Winter Peak (+2 B787 flights, +2% LF)
   - India Capacity Surge (+5 A320 flights, +3% P2P)
   - Germany Winter Expansion (+1 A330 flight, +3% LF)
   - Saudi Summer Campaign (+3 A320 flights, +5% LF)
   - China Hub Recovery (+2 B787 flights, +5% LF)
2. **Interactive Levers:** Real-time sliders for market selection, season, weekly flight delta, aircraft gauge, seat capacity shift, load factor, P2P share, response multiplier, and stay duration.
3. **Live Conversion Chain Visualization:** Visual flow of seats $\rightarrow$ pax $\rightarrow$ P2P $\rightarrow$ arrivals $\rightarrow$ hotel guests with baseline vs. scenario comparisons.
4. **Waterfall Breakdown:** Dynamic bar chart of exact waterfall attribution components.
5. **Tornado Sensitivity Chart:** Real-time ranking of operational levers by elasticity.
6. **Executive Briefing Card:** Auto-generated natural language briefing for tourism executives.

---

## 7. Deterministic Training & Model Retraining

To recalibrate the structural parameters and train the monotonic residual engine from curated data:

```bash
python scripts/train_models.py
```

### Generated Artifacts

- `lake/curated/structural_calibration.json`: Calibrated baseline parameters across 17 market archetypes and 4 seasons.
- `lake/curated/residual_engine.pkl`: Trained scikit-learn RidgeCV model fitted on calendar, seasonal, and lagged demand features with aviation features excluded to protect monotonicity.
- `lake/curated/conformal_calibrator.json`: Calibrated historical residual distributions used for empirical uncertainty intervals.

---

## 8. Holdout Back-Testing & Model Evaluation

To execute the temporal back-test against the 2025 holdout window (Jan 6, 2025 to Jul 27, 2025, 30 complete ISO weeks, 510 market-weeks):

```bash
python scripts/evaluate_models.py
```

### Evaluation Reporting Modes

The evaluation script rigorously separates planning simulations from realized data:

1. **International Planning Mode:** Simulates purely from scheduled aviation capacity and calibrated conversion rates without looking at holdout load factor, P2P mix, or arrival numbers.
2. **International Realized-Chain Mode:** Uses actual holdout load factors and P2P shares to isolate error in the downstream conversion stages.
3. **Domestic Forecast Mode:** Pure seasonal prior forecast with zero holdout arrival leakage.
4. **Combined Diagnostic:** Full territory evaluation across all international markets and domestic demand.

Benchmark metrics are written to `lake/curated/evaluation_results.json`.

---

## 9. Automated Verification & Test Suite

The digital twin includes an automated test suite verifying core mathematical properties:

```bash
# Run tests with pytest
pytest tests/test_digital_twin.py -v

# Or run with standard library unittest
python -m unittest tests/test_digital_twin.py
```

### Verified Test Cases

1. `test_weekly_market_panel_integrity`: Asserts panel schema, non-negative flight metrics, and valid date bounds.
2. `test_structural_engine_waterfall_identity`: Verifies that exact waterfall attribution decomposes net guest lift with zero residual ($|\text{sum} - \Delta Guests| < 10^{-6}$).
3. `test_monotonicity_guarantee`: Confirms that increasing flight frequency or seats strictly increases or maintains guest demand ($\Delta Guests \ge 0$).
4. `test_cold_start_unmodeled_country`: Tests dynamic fallback to regional priors for unmodeled source markets (e.g. Sweden, Brazil).
5. `test_artifact_reload_consistency`: Confirms that reloaded calibration artifacts produce deterministic, reproducible scenario predictions.

---

## 10. Publication-Grade PDF & Scenario Chart Generation

To compile the executive PDF dossier and high-resolution figures:

```bash
# 1. Generate scenario figures dynamically from evaluation results
python scripts/generate_scenario_charts.py

# 2. Compile publication-grade 3-page PDF dossier
python scripts/build_solution_report.py
```

Generated outputs:
- `output/figures/waterfall_attribution.png`: High-resolution waterfall attribution graphic.
- `output/figures/tornado_sensitivity.png`: Tornado sensitivity graphic.
- `output/figures/model_benchmark.png`: Model benchmark comparison graphic.
- `output/pdf/challengeon_solution_report.pdf`: 3-page publication-grade executive dossier.

