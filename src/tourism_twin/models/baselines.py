"""The weekly benchmark models behind the Model protocol, so the back-test harness runs them
like any other model. Each fits on the rows it is given and predicts level-scale guests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.models.features import calendar_feature_matrix
from tourism_twin.models.residual import ResidualMLEngine
from tourism_twin.models.structural import StructuralEngine


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
    """Diagnostic: realized P2P passengers x calibrated multiplier x length of stay (domestic:
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
    """The shipped hybrid: structural planning prediction plus the residual ridge, floored at 0."""

    def fit(self, panel: pd.DataFrame) -> "LegacyHybrid":
        self.structural_ = StructuralEngine.calibrate(panel)
        self.residual_ = ResidualMLEngine().fit(panel, self.structural_)
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        planning = self.structural_.planning_guests_for(panel)
        residual = np.array([
            self.residual_.predict_residual(m, w, q, mo, h, e)
            for m, w, q, mo, h, e in zip(panel["market"], panel["iso_week"], panel["quarter"], panel["month"],
                                         panel["is_holiday_week"], panel["is_major_event_week"])
        ])
        return pd.Series(np.maximum(0.0, planning + residual), index=panel.index)


class SeasonalNaive:
    """Daily: the same market's value `period` days earlier (364 keeps the weekday), stepping back
    whole periods until the source date lies in the training data."""

    def __init__(self, period: int = 364, date_column: str = "date", max_periods: int = 4) -> None:
        self.period, self.date_column, self.max_periods = period, date_column, max_periods

    def fit(self, panel: pd.DataFrame) -> "SeasonalNaive":
        dates = pd.to_datetime(panel[self.date_column])
        self.history_ = pd.Series(panel["guests"].to_numpy(), index=pd.MultiIndex.from_arrays([panel["market"], dates]))
        self.last_ = dates.groupby(panel["market"]).max().to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        dates = pd.to_datetime(panel[self.date_column])
        last = panel["market"].map(self.last_)
        out = pd.Series(np.nan, index=panel.index, dtype=float)
        for k in range(1, self.max_periods + 1):
            source = dates - pd.to_timedelta(self.period * k, unit="D")
            todo = out.isna() & (source <= last)
            if not todo.any():
                break
            keys = pd.MultiIndex.from_arrays([panel.loc[todo, "market"], source[todo]])
            out.loc[todo] = self.history_.reindex(keys).to_numpy()
        return out


class MarketRouter:
    """Routes DOMESTIC rows to one model and every other market to another."""

    def __init__(self, domestic, international) -> None:
        self.factories = {True: domestic, False: international}

    def fit(self, panel: pd.DataFrame) -> "MarketRouter":
        is_domestic = panel["market"] == DOMESTIC
        self.models_ = {flag: self.factories[flag]().fit(panel[is_domestic == flag])
                        for flag in (True, False) if (is_domestic == flag).any()}
        return self

    def decompose(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Per-component log contributions from whichever model serves each row (NaN where a
        component does not exist in that model)."""
        is_domestic = panel["market"] == DOMESTIC
        parts = [self.models_[flag].decompose(panel[is_domestic == flag])
                 for flag in self.models_ if (is_domestic == flag).any()]
        return pd.concat(parts).reindex(panel.index)

    def explain(self) -> dict:
        return {market: detail for model in self.models_.values() for market, detail in model.explain().items()}

    def diagnostics(self) -> dict:
        totals: dict = {}
        for model in self.models_.values():
            for key, value in getattr(model, "diagnostics", lambda: {})().items():
                totals[key] = totals.get(key, 0) + value
        return totals

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        is_domestic = panel["market"] == DOMESTIC
        out = pd.Series(np.nan, index=panel.index, dtype=float)
        for flag, model in self.models_.items():
            rows = panel[is_domestic == flag]
            if len(rows):
                out.loc[rows.index] = model.predict(rows).to_numpy()
        return out


class ArrivalsRatio:
    """Daily nowcast baseline: new arrivals times the market's training guests / arrivals ratio."""

    def fit(self, panel: pd.DataFrame) -> "ArrivalsRatio":
        totals = panel.groupby("market")[["guests", "new_arrivals_filled"]].sum()
        self.ratio_ = (totals["guests"] / totals["new_arrivals_filled"]).to_dict()
        return self

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        unseen = sorted(set(panel["market"]) - set(self.ratio_))
        if unseen:
            raise ValueError(f"ArrivalsRatio has no ratio for markets {unseen}")
        return panel["new_arrivals_filled"] * panel["market"].map(self.ratio_)
