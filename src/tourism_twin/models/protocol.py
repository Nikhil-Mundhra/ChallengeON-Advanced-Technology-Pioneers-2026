"""The contract every forecasting model satisfies, so one back-test harness can run them all."""

from __future__ import annotations

from typing import Any, Dict, Protocol

import pandas as pd


class Model(Protocol):
    def fit(self, panel: pd.DataFrame) -> "Model": ...

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        """Predicted target on the original scale, indexed like `panel`."""
        ...


class DecomposableModel(Model, Protocol):
    """A Model that also explains itself: what AdditiveLogModel and MarketRouter provide, and what
    routing, outputs and diagnostics may rely on (baselines such as SeasonalNaive are plain Models)."""

    def decompose(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Log-scale contribution of each component, indexed like `panel`."""
        ...

    def decompose_by_group(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Log-scale contribution of each block, indexed like `panel`."""
        ...

    def explain(self) -> Dict[Any, Dict[str, Any]]: ...

    def diagnostics(self) -> Dict[str, int]: ...
