"""ML Residual Correction Layer for Abu Dhabi Tourism Digital Twin.

Learns residual calendar patterns, holiday spikes, major events (ADIPEC, F1),
and persistent market deviations on top of the structural scenario baseline.
Enforces monotonicity by strictly excluding flight capacity levers from residual features.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from tourism_twin.config import SETTINGS
from tourism_twin.domain.scenario import SimulationResult
from tourism_twin.models.features import extract_calendar_features
from tourism_twin.models.structural import StructuralEngine


class ResidualMLEngine:
    """Monotonic ML residual correction engine."""

    def __init__(self):
        self.models: Dict[str, RidgeCV] = {}
        self.residual_history: Dict[str, np.ndarray] = {}
        self.residual_std: Dict[str, float] = {}

    def fit(
        self,
        train_df: pd.DataFrame,
        structural_engine: StructuralEngine,
        alphas: np.ndarray = np.logspace(-2, 4, 25),
    ) -> "ResidualMLEngine":
        """Train regularized ridge residual models per market on historical actuals - structural.

        IMPORTANT — planning-mode parity:
        The structural prediction must be computed from the same planning-mode inputs
        that the simulator uses at inference time (seasonal priors, not realized actuals).
        For markets with zero P2P flights (including DOMESTIC), we fall back to
        ``p.baseline_weekly_arrivals`` (the calibrated seasonal baseline) rather than
        the contemporaneous realized ``new_arrivals`` column. Using realized arrivals
        during training would cause a training–serving mismatch: the residual model
        would learn to correct a much smaller structural error than it faces in production.
        """
        train = train_df.copy()

        # Compute structural predictions using planning-mode priors only (no leakage from realized actuals)
        struct_preds = []
        for _, row in train.iterrows():
            m = row["market"]
            s = row["season"]
            p = structural_engine.params[m][s]
            seats = row["seats"]
            lf = row["load_factor"] if not np.isnan(row["load_factor"]) else p.baseline_load_factor
            pax = seats * lf if seats > 0 else 0.0
            p2p_s = row["p2p_share"] if not np.isnan(row["p2p_share"]) else p.baseline_p2p_share
            p2p = pax * p2p_s if pax > 0 else 0.0
            # FIX (P0-A): always use the structural seasonal prior as the arrival baseline.
            # Previously: `else row["new_arrivals"]` — leaked ex-post realized data into training.
            # Now: `else p.baseline_weekly_arrivals` — matches the production planning path.
            arr = p2p * p.effective_response_multiplier if p2p > 0 else p.baseline_weekly_arrivals
            g_struct = arr * p.baseline_los
            struct_preds.append(g_struct)

        train["guests_struct"] = struct_preds
        train["residual"] = train["guests"] - train["guests_struct"]

        # Train a regularized RidgeCV model per market
        markets = sorted(train["market"].unique())
        for m in markets:
            m_df = train[train["market"] == m]
            if len(m_df) < 5:
                continue

            X = np.stack([
                extract_calendar_features(
                    iso_week=row["iso_week"],
                    quarter=row["quarter"],
                    month=row["month"],
                    is_holiday_week=row["is_holiday_week"],
                    is_major_event_week=row["is_major_event_week"],
                )
                for _, row in m_df.iterrows()
            ])
            y = m_df["residual"].values

            model = RidgeCV(alphas=alphas)
            model.fit(X, y)
            self.models[m] = model
            self.residual_history[m] = y
            self.residual_std[m] = float(np.std(y - model.predict(X)))

        return self

    def predict_residual(
        self,
        market: str,
        iso_week: int,
        quarter: int,
        month: int,
        is_holiday_week: int = 0,
        is_major_event_week: int = 0,
    ) -> float:
        """Predict the calendar residual adjustment for a market and calendar period."""
        m_norm = market.upper().strip()
        if m_norm not in self.models:
            return 0.0

        x = extract_calendar_features(
            iso_week=iso_week,
            quarter=quarter,
            month=month,
            is_holiday_week=is_holiday_week,
            is_major_event_week=is_major_event_week,
        ).reshape(1, -1)

        r_hat = float(self.models[m_norm].predict(x)[0])
        return r_hat

    def predict_hybrid(
        self,
        structural_result: SimulationResult,
        iso_week: int = 10,
        quarter: int = 1,
        month: int = 2,
        is_holiday_week: int = 0,
        is_major_event_week: int = 0,
    ) -> Dict[str, float]:
        """Combine structural simulation with residual correction."""
        r_hat = self.predict_residual(
            market=structural_result.market,
            iso_week=iso_week,
            quarter=quarter,
            month=month,
            is_holiday_week=is_holiday_week,
            is_major_event_week=is_major_event_week,
        )

        base_hybrid = max(0.0, structural_result.base_guests + r_hat)
        sim_hybrid = max(0.0, structural_result.sim_guests + r_hat)
        delta_hybrid = sim_hybrid - base_hybrid

        return {
            "market": structural_result.market,
            "season": structural_result.season,
            "structural_base": structural_result.base_guests,
            "structural_sim": structural_result.sim_guests,
            "structural_delta": structural_result.delta_guests,
            "residual_correction": r_hat,
            "hybrid_base": base_hybrid,
            "hybrid_sim": sim_hybrid,
            "hybrid_delta": delta_hybrid,
            # Monotonicity check: delta_hybrid must match or move monotonically with delta_guests
            "is_monotonic": bool(
                (structural_result.delta_guests >= 0 and delta_hybrid >= -1e-6) or
                (structural_result.delta_guests <= 0 and delta_hybrid <= 1e-6)
            ),
        }

    def save(self, model_path: Path = SETTINGS.residual_model_path) -> Path:
        """Serialize the fitted state to disk.

        Only plain containers and scikit-learn estimators are pickled, never this class, so the
        artifact does not depend on the module path this engine happens to live at.
        """
        model_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "models": self.models,
            "residual_history": self.residual_history,
            "residual_std": self.residual_std,
        }
        with open(model_path, "wb") as f:
            pickle.dump(state, f)
        return model_path

    @classmethod
    def load(cls, model_path: Path = SETTINGS.residual_model_path) -> "ResidualMLEngine":
        """Load fitted residual models from disk."""
        with open(model_path, "rb") as f:
            state = pickle.load(f)
        engine = cls()
        engine.models = state["models"]
        engine.residual_history = state["residual_history"]
        engine.residual_std = state["residual_std"]
        return engine
