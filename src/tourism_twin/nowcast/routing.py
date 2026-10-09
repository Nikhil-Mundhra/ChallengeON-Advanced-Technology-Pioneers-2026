"""Serve DOMESTIC and the international markets with separate models behind one Model."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tourism_twin.domain.markets import DOMESTIC


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

    def decompose_by_group(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Per-block log contributions from whichever model serves each row (NaN where a block
        does not exist in that model)."""
        is_domestic = panel["market"] == DOMESTIC
        parts = [self.models_[flag].decompose_by_group(panel[is_domestic == flag])
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
