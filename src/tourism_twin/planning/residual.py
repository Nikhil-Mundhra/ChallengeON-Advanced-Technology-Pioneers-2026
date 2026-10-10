"""ML Residual Correction Layer for Abu Dhabi Tourism Digital Twin.

Learns residual calendar patterns, holiday spikes, major events (ADIPEC, F1),
and persistent market deviations on top of the structural scenario baseline.
Enforces monotonicity by strictly excluding flight capacity levers from residual features.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from tourism_twin.config import SETTINGS
from tourism_twin.domain.scenario import SimulationResult
from tourism_twin.planning.calendar_features import residual_event_types, residual_feature_matrix
from tourism_twin.planning.structural import StructuralEngine

class ResidualMLEngine:
    """Monotonic ML residual correction engine."""

    def __init__(self, events: Optional[Sequence[str]] = None):
        """`events`: event types whose weekly exposure enters the residual (default: every type in
        domain/events.csv except one-off periods); () for the calendar-only residual."""
        self.events = tuple(residual_event_types() if events is None else events)
        self.models: Dict[str, RidgeCV] = {}
        self.residual_history: Dict[str, np.ndarray] = {}
        self.residual_std: Dict[str, float] = {}
        self.season_residual_: Dict[str, Dict[str, float]] = {}

    def fit(
        self,
        train_df: pd.DataFrame,
        structural_engine: StructuralEngine,
        alphas: np.ndarray = np.logspace(-2, 4, 25),
    ) -> "ResidualMLEngine":
        """Train regularized ridge residual models per market on historical actuals - structural.

        Planning-mode parity: the structural prediction is computed exactly as the simulator
        computes it at inference time, from scheduled seats and the calibrated seasonal priors
        (StructuralEngine.planning_guests). Realized load factor, P2P share, and arrivals are
        never used; training on them would teach the residual to correct a smaller structural
        error than the one it faces in production.
        """
        train = train_df.copy()
        train["guests_struct"] = structural_engine.planning_guests_for(train)
        train["residual"] = train["guests"] - train["guests_struct"]

        # Train a regularized RidgeCV model per market
        markets = sorted(train["market"].unique())
        for m in markets:
            m_df = train[train["market"] == m]
            if len(m_df) < 5:
                continue

            X = residual_feature_matrix(m_df, self.events)
            y = m_df["residual"].values

            model = RidgeCV(alphas=alphas)
            model.fit(X, y)
            self.models[m] = model
            self.residual_history[m] = y
            self.residual_std[m] = float(np.std(y - model.predict(X)))
            # The structural baseline is a seasonal mean over all training weeks, holidays
            # included, so the scenario residual is the mean prediction over the same weeks.
            fitted = pd.Series(model.predict(X), index=m_df.index)
            self.season_residual_[m] = {season: float(v) for season, v in fitted.groupby(m_df["season"]).mean().items()}

        return self

    def predict_residual(self, frame: pd.DataFrame) -> pd.Series:
        """Calendar residual for each row of a frame with market and the CALENDAR_COLUMNS (0 for an
        unmodelled market)."""
        out = pd.Series(0.0, index=frame.index)
        for market, rows in frame.groupby(frame["market"].str.upper().str.strip()):
            if market in self.models:
                out.loc[rows.index] = self.models[market].predict(residual_feature_matrix(rows, self.events))
        return out

    def season_residual(self, market: str, season: str) -> float:
        """Mean fitted residual over the market's training weeks in `season` (0 if none)."""
        return self.season_residual_.get(market.upper().strip(), {}).get(season, 0.0)

    def predict_hybrid(self, structural_result: SimulationResult) -> Dict[str, float]:
        """Combine a structural simulation with the residual correction for its market and season."""
        r_hat = self.season_residual(structural_result.market, structural_result.season)

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
            "season_residual": self.season_residual_,
            "events": list(self.events),
        }
        with open(model_path, "wb") as f:
            pickle.dump(state, f)
        return model_path

    @classmethod
    def load(cls, model_path: Path = SETTINGS.residual_model_path) -> "ResidualMLEngine":
        """Load fitted residual models from disk."""
        with open(model_path, "rb") as f:
            state = pickle.load(f)
        engine = cls(events=state.get("events", ()))  # artifacts saved before events: calendar only
        engine.models = state["models"]
        engine.residual_history = state["residual_history"]
        engine.residual_std = state["residual_std"]
        engine.season_residual_ = state["season_residual"]
        return engine
