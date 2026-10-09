"""Serve DOMESTIC and the international markets with separate models behind one Model."""

from __future__ import annotations

from typing import Callable, Dict, Iterator, Tuple

import pandas as pd

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.models.protocol import DecomposableModel


class MarketRouter:
    """Routes DOMESTIC rows to one model and every other market to another. A new series type is
    a new spec passed here, never a subclass."""

    def __init__(self, domestic: Callable[[], DecomposableModel], international: Callable[[], DecomposableModel]) -> None:
        self.factories: Dict[bool, Callable[[], DecomposableModel]] = {True: domestic, False: international}
        self.models_: Dict[bool, DecomposableModel] = {}

    @staticmethod
    def _split(panel: pd.DataFrame) -> Iterator[Tuple[bool, pd.DataFrame]]:
        """(is_domestic, rows) for each side that has rows."""
        is_domestic = panel["market"] == DOMESTIC
        for flag in (True, False):
            rows = panel[is_domestic == flag]
            if len(rows):
                yield flag, rows

    def _served(self, panel: pd.DataFrame) -> Iterator[Tuple[DecomposableModel, pd.DataFrame]]:
        if not self.models_:
            raise RuntimeError("MarketRouter is not fitted")
        for flag, rows in self._split(panel):
            if flag not in self.models_:
                side = "DOMESTIC" if flag else "international"
                raise KeyError(f"No {side} model was fitted (no {side} rows in training)")
            yield self.models_[flag], rows

    def fit(self, panel: pd.DataFrame) -> "MarketRouter":
        self.models_ = {flag: self.factories[flag]().fit(rows) for flag, rows in self._split(panel)}
        return self

    def _stack(self, panel: pd.DataFrame, method: str) -> pd.DataFrame:
        parts = [(model.decompose if method == "decompose" else model.decompose_by_group)(rows)
                 for model, rows in self._served(panel)]
        return pd.concat(parts).reindex(panel.index) if parts else pd.DataFrame(index=panel.index)

    def decompose(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Per-component log contributions from whichever model serves each row (NaN where a
        component does not exist in that model)."""
        return self._stack(panel, "decompose")

    def decompose_by_group(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Per-block log contributions from whichever model serves each row (NaN where a block
        does not exist in that model)."""
        return self._stack(panel, "decompose_by_group")

    def explain(self) -> dict:
        out: dict = {}
        for model in self.models_.values():
            for market, detail in model.explain().items():
                if market in out:
                    raise ValueError(f"Market {market!r} is served by both routed models")
                out[market] = detail
        return out

    def diagnostics(self) -> dict:
        totals: dict = {}
        for model in self.models_.values():
            for key, value in model.diagnostics().items():
                totals[key] = totals.get(key, 0) + value
        return totals

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        out = pd.Series(float("nan"), index=panel.index, dtype=float)
        for model, rows in self._served(panel):
            out.loc[rows.index] = model.predict(rows).to_numpy()
        return out
