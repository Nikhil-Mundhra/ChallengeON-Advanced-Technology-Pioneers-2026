"""The weekly benchmark models behind the Model protocol, so the back-test harness runs them
like any other model. Each fits on the rows it is given and predicts level-scale guests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.planning.calendar_features import calendar_feature_matrix
from tourism_twin.planning.residual import ResidualMLEngine
from tourism_twin.planning.structural import StructuralEngine


class SeasonalPrior:
    """Mean weekly guests of the market and season in the training rows."""

    def fit(self, panel: pd.DataFrame) -> "SeasonalPrior":
        self.priors_ = panel.groupby(["market", "season"])["guests"].mean().to_dict()
        self.market_means_ = panel.groupby("market")["guests"].mean().to_dict()
        self.overall_ = panel["guests"].mean()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        """Market-season mean; the market's own mean for an unseen season; the pooled mean only
        for an unseen market."""
        values = [self.priors_.get((m, s), self.market_means_.get(m, self.overall_))
                  for m, s in zip(panel["market"], panel["season"])]
        return pd.Series(values, index=panel.index, dtype=float)



class CalendarRidge:
    """Per-market ridge on calendar features only; no aviation input."""

    def __init__(self, alphas: np.ndarray = np.logspace(-2, 4, 20)) -> None:
        self.alphas = alphas

    def fit(self, panel: pd.DataFrame) -> "CalendarRidge":
        self.models_ = {
            market: RidgeCV(alphas=self.alphas).fit(calendar_feature_matrix(rows), rows["guests"].values)
            for market, rows in panel.groupby("market", sort=False)
        }
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        unseen = sorted(set(panel["market"]) - set(self.models_))
        if unseen:
            raise ValueError(f"CalendarRidge has no model for markets {unseen}")
        out = pd.Series(np.nan, index=panel.index, dtype=float)
        for market, rows in panel.groupby("market", sort=False):
            out.loc[rows.index] = np.maximum(0.0, self.models_[market].predict(calendar_feature_matrix(rows)))
        return out



class StructuralPlanning:
    """Scheduled seats x calibrated seasonal priors (the planning chain)."""

    def fit(self, panel: pd.DataFrame) -> "StructuralPlanning":
        self.engine_ = StructuralEngine.calibrate(panel)
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        return pd.Series(self.engine_.planning_guests_for(panel), index=panel.index)



class RealizedChain:
    """Diagnostic: realized P2P passengers x calibrated multiplier x guests-per-arrival factor (domestic:
    the planning prediction). Needs realized aviation data, so it is not a planning model."""

    def fit(self, panel: pd.DataFrame) -> "RealizedChain":
        self.engine_ = StructuralEngine.calibrate(panel)
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        planning = self.engine_.planning_guests_for(panel)
        params = [self.engine_.get_or_create_params(m, s) for m, s in zip(panel["market"], panel["season"])]
        realized = np.array([p2p * p.effective_response_multiplier * p.baseline_los for p2p, p in zip(panel["p2p"], params)])
        return pd.Series(np.where(panel["market"] == DOMESTIC, planning, realized), index=panel.index)



class LegacyHybrid:
    """The shipped hybrid: structural planning prediction plus the residual ridge (calendar and
    event exposure), floored at 0. `events=()` is the calendar-only residual it replaced."""

    def __init__(self, events=None) -> None:
        self.events = events

    def fit(self, panel: pd.DataFrame) -> "LegacyHybrid":
        self.structural_ = StructuralEngine.calibrate(panel)
        self.residual_ = ResidualMLEngine(events=self.events).fit(panel, self.structural_)
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        planning = self.structural_.planning_guests_for(panel)
        residual = self.residual_.predict_residual(panel).to_numpy()
        return pd.Series(np.maximum(0.0, planning + residual), index=panel.index)
