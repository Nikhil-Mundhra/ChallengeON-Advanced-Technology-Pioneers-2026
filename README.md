# ChallengeON DCT Analytics Lake & Abu Dhabi Tourism Digital Twin

This repository hosts the analytics lake and the **Abu Dhabi Tourism Digital Twin** for the [ChallengeON DCT Abu Dhabi Hackathon](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en).

The complete product specification is in [Abu Dhabi Tourism Digital Twin](docs/solution_documentation.md).

---

## 1. Quick Start

```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1. Build local analytical lake from raw Excel workbooks
python scripts/build_lake.py

# 2. Build the curated weekly market modeling panel (Jan 2023 - Feb 2026)
python scripts/build_panels.py

# 3. Run a planner scenario (e.g. +2 weekly B787 flights from the UK in Winter Peak)
python scripts/run_scenario.py --market "UNITED KINGDOM" --season "Winter_Peak" --delta_freq 2.0 --gauge 290.0 --delta_lf 0.02

# 4. Run forward temporal holdout back-tests (Jan 2025 - Jul 2025)
python scripts/evaluate_models.py

# 5. Generate high-resolution presentation figures (waterfall, tornado, benchmark)
python scripts/generate_scenario_charts.py
```

---

## 2. Core Architecture

The **Abu Dhabi Tourism Digital Twin** combines:
1. **Structural Conversion Engine (`engine/structural.py`)**: A visible conversion chain mapping aviation decisions to hotel demand:
   $$\text{Aviation Levers} \to \text{Total Pax} \to \text{P2P Traffic} \xrightarrow{C_{m, s}} \text{Hotel Arrivals} \xrightarrow{L_{m, s}} \text{Hotel Guests}$$
2. **Regularized ML Residual Layer (`engine/residual.py`)**: Captures calendar harmonics, Islamic lunar holidays (Eid al-Fitr, Eid al-Adha), UAE National Day, and major events (ADIPEC, Formula 1) without touching flight variables, mathematically guaranteeing **monotonicity**.
3. **Market Archetype Profiling (`engine/archetypes.py`)**: Categorizes top-15 markets into 6 defensible behavioral archetypes (*Direct Leisure, Resident/VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging/Sparse*).
4. **Uncertainty & Sensitivity Engine (`engine/uncertainty.py` & `engine/simulator.py`)**: Beta-distributed sampling for bounded operational ratios, time-block bootstrap residuals for autocorrelated demand, and Tornado sensitivity ranking.

---

## 3. Back-Test Benchmark Results

Evaluated on forward temporal holdout (Jan 2025 – Jul 2025, 510 forward market-week observations):

| Model Architecture | WMAPE | Directional Bias | MAE | RMSE | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Historical Seasonal Prior** | 22.55% | -5.97% | 3,755.2 | 7,072.1 | Baseline |
| **2. Pure ML / Calendar Model** | 22.74% | -7.71% | 3,787.6 | 7,064.3 | Calendar Extrapolation |
| **3. Structural-Only Engine** | 17.12% | -2.64% | 2,852.0 | 4,508.2 | Aviation Conversion Chain |
| **4. Hybrid Digital Twin (Proposed)** | **17.13%** | **-1.51%** | **2,853.5** | **4,419.9** | **Champion Model** |

- **WMAPE Error Reduction:** $>5.4$ percentage points (~24% relative reduction).
- **RMSE Error Reduction:** $37.5\%$ reduction over pure calendar ML.
- **Directional Bias:** Reduced from $-5.97\%$ down to **$-1.51\%$**.

---

## 4. Curated Data Assets

| File | Grain | Records | Description |
| :--- | :--- | :--- | :--- |
| `lake/curated/guest_daily.parquet` | Daily | 69,344 | Unified domestic & international records (train & test splits) |
| `lake/curated/flight_daily.parquet` | Daily | 117,608 | Operating metrics by route, airline, and date |
| `lake/curated/weekly_market_panel.parquet` | Weekly | 2,839 | Curated modeling panel for top 15 markets + Other + Domestic |
| `lake/curated/structural_calibration.json` | JSON | 17 markets | Calibrated seasonal conversion parameters ($C, L, LF, P2P$) |
| `lake/curated/residual_engine.pkl` | Pickle | 17 models | Trained regularized RidgeCV residual models |
| `lake/analytics.duckdb` | DuckDB | — | Local query database with analytical views |

---

## 5. Scenario CLI Usage

```bash
# Usage flags:
#   --market          Target source market (e.g. "UNITED KINGDOM", "INDIA", "RUSSIAN FEDERATION", "SAUDI ARABIA")
#   --season          Winter_Peak | Spring_Shoulder | Summer_Trough | Autumn_Shoulder
#   --delta_freq      Additional weekly flights (e.g. 2.0)
#   --gauge           Aircraft seat capacity (e.g. 290.0 for B787, 180.0 for A320)
#   --delta_seats_pct Proportional seat shift (e.g. 0.15 for +15%)
#   --delta_lf        Shift in load factor (e.g. 0.02 for +2%)
#   --delta_p2p       Shift in P2P share (e.g. 0.03)
#   --delta_conv_pct  Shift in marketing conversion (e.g. 0.05)
#   --delta_los       Shift in average length of stay in days (e.g. 0.3)

python scripts/run_scenario.py --market "INDIA" --season "Winter_Peak" --delta_seats_pct 0.10
```
