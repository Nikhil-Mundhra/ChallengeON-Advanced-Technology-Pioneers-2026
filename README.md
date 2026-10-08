# ChallengeON DCT Analytics Lake & Abu Dhabi Tourism Digital Twin

This repository hosts the analytics lake and the **Abu Dhabi Tourism Digital Twin** for the [ChallengeON DCT Abu Dhabi Hackathon](https://challengeon.atrc.ae/en/challenges/atp2026/pages/dct-challenge-statement?lang=en).

The master solution specification is documented in [Abu Dhabi Tourism Digital Twin](docs/solution_documentation.md) and the operational guide in [User Guide](docs/user_guide.md).

---

## 1. Quickstart & Deterministic Pipeline

Every stage of the pipeline is 100% repeatable, deterministic, and self-contained:

```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[report,dev]"   # editable install: src/ packages import without sys.path hacks

# --- One-command full rebuild (all metrics + artifacts) ---
make all

# --- Or run individual steps manually ---

# 1. Build local analytical lake from raw Excel workbooks
python scripts/build_lake.py

# 2. Build the curated weekly market modeling panel (Jan 2023 - Feb 2026)
python scripts/build_panels.py

# 3. Run strict forward temporal holdout back-tests (writes evaluation_results.json)
python scripts/evaluate_models.py

# 4. Deterministically train and calibrate models & uncertainty bounds
python scripts/train_models.py --max_date 2025-07-27

# 5. Run automated unit and integration tests (14/14 passing)
pytest tests/ -v

# 6. Run a planner scenario via CLI
python scripts/run_scenario.py --market "UNITED KINGDOM" --season "Winter_Peak" --delta_freq 2.0 --gauge 290.0 --delta_lf 0.02

# 7. Launch the interactive web application dashboard
python scripts/run_app.py --port 8080

# 8. Rebuild dynamic presentation figures and 3-page PDF dossier
python scripts/generate_scenario_charts.py
python scripts/build_solution_report.py
```

---

## 2. Core Architecture

The **Abu Dhabi Tourism Digital Twin** combines:
1. **Structural Conversion Engine (`src/engine/structural.py`)**: A visible conversion chain mapping aviation decisions to hotel demand:
   $$\text{Aviation Levers} \to \text{Total Pax} \to \text{P2P Traffic} \xrightarrow{M_{m, s}} \text{Hotel Arrivals} \xrightarrow{L_{m, s}} \text{Hotel Guests}$$
   Includes **Exact Waterfall Attribution Decomposition** with $0.000000$ verified discrepancy and cold-start support for unmodeled source markets.
2. **Regularized ML Residual Layer (`src/engine/residual.py`)**: Captures calendar harmonics, Islamic lunar holidays (Eid al-Fitr, Eid al-Adha), UAE National Day, and major events (ADIPEC, Formula 1) without touching flight variables, mathematically guaranteeing **monotonicity**.
3. **Market Archetype Profiling (`src/engine/archetypes.py`)**: Categorizes source markets into 6 defensible behavioral archetypes (*Direct Leisure, Resident/VFR, Regional GCC, Hub-Mediated, Highly Seasonal, Emerging/Sparse*) with hierarchical regional shrinkage for cold-start markets.
4. **Uncertainty & Sensitivity Engine (`src/engine/uncertainty.py` & `src/engine/simulator.py`)**: Beta-distributed sampling for bounded operational ratios, parameter shocks, time-block bootstrap residuals, and Tornado sensitivity ranking.

---

## 3. Strict Forward-Holdout Evaluation Results

Evaluated on 30 complete 7-day holdout weeks with complete guest inputs (Jan 2025 – Jul 2025, 621 market-weeks across all 21 markets) calibrated on 104 complete weeks (Jan 2023 – Dec 2024, 2,132 market-weeks):

### Diagnostic Separation

| Evaluation Setting | WMAPE | Directional Bias | MAE | RMSE | Operational Scope |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **International Planning Mode** | **27.52%** | **+1.52%** | 2,466.5 | 3,920.7 | Scheduled seats + training priors only (true pre-flight planning). |
| **International Realized-Chain** | **24.54%** | **-5.67%** | 2,199.9 | 3,308.7 | Downstream conversion holding realized P2P fixed. |
| **Domestic Forecast Mode** | **16.04%** | **+13.05%** | 17,485.2 | 21,078.9 | Dedicated seasonal prior; NO holdout arrival leakage. |
| **Combined Planning Mode** | **23.14%** | **+5.93%** | 3,192.1 | 6,007.8 | Full territory diagnostic (International + Domestic). |
| **Combined Realized-Chain** | **21.30%** | **+1.48%** | 2,938.3 | 5,646.6 | Realized aviation P2P across entire territory. |

### Model Benchmark (All Markets)

| Model Architecture | WMAPE | Directional Bias | MAE | RMSE | Model Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Historical Seasonal Prior** | 23.00% | -6.60% | 3,172.8 | 6,156.5 | Naive Baseline |
| **2. Pure ML / Calendar Model** | 22.00% | -8.50% | 3,035.6 | 5,839.0 | Calendar Extrapolation |
| **3. Structural-Only Engine** | 23.14% | +5.93% | 3,192.1 | 6,007.8 | Pre-Flight Decision Chain |
| **4. Hybrid Digital Twin (Proposed)** | **21.73%** | **+5.37%** | **2,998.8** | **5,673.5** | **Champion (Lowest MAE & RMSE)** |

*Demonstrated Empirical Holdout Coverage: 65.2% (Nominal target: 80.0%, reflecting positive 2025 secular trend drift relative to 2023–2024 base).*

> **Market Bridge Specification:** The challenge dataset does not contain individual passenger manifests or booking PNRs linking guest nationality to flight origin. An unrestricted cross-allocation matrix ($45 \times 33 = 1,485$ parameters) is unidentifiable from aggregate weekly time series. The digital twin deploys a regularized same-market operational proxy where departure country is linked to guest nationality, and market-season-specific effective multipliers $\beta_{m,s} = \frac{\text{arrivals}_{m,s}}{\text{P2P}_{m,s}}$ empirically absorb non-national travelers, non-hub transit, and overland transit into Abu Dhabi.


---

## 4. Curated Data Assets

| File | Grain | Records | Description |
| :--- | :--- | :--- | :--- |
| `lake/curated/guest_daily.parquet` | Daily | 69,920 | Complete date-nationality grid with presence & suppression flags |
| `lake/curated/flight_daily.parquet` | Daily | 116,395 | True daily operating metrics (2023+) with outlier quality flags |
| `lake/curated/flight_monthly.parquet` | Monthly | 1,213 | Isolated 2022 monthly records on distinct month-start dates |
| `lake/curated/weekly_market_panel.parquet` | Weekly | 3,507 | Cleanly matched panel with 21 unified markets (Top 15 + 5 regional clusters + Domestic) |
| `lake/curated/structural_calibration.json` | JSON | 21 markets | Calibrated seasonal parameters ($M, L, LF, P2P$) |
| `lake/curated/residual_engine.pkl` | Pickle | 21 models | Trained regularized RidgeCV residual models |
| `lake/curated/conformal_calibrator.json` | JSON | 21 markets | Non-conformity margins and holdout coverage metrics |
| `lake/curated/evaluation_results.json` | JSON | — | Structured output from strict forward back-test |
| `lake/analytics.duckdb` | DuckDB | — | Local query database with analytical views |

---

## 5. Deliverables & Documentation

- **Master Specification:** [`docs/solution_documentation.md`](docs/solution_documentation.md)
- **User Guide & Archetype Manual:** [`docs/user_guide.md`](docs/user_guide.md)
- **Executive PDF Report:** [`output/pdf/challengeon_solution_report.pdf`](output/pdf/challengeon_solution_report.pdf)
- **Schema & Database Audit Report:** [`output/pdf/challengeon_schema_database_report.pdf`](output/pdf/challengeon_schema_database_report.pdf)
- **Interactive Web UI:** Run `python scripts/run_app.py --port 8080` and visit `http://127.0.0.1:8080`
