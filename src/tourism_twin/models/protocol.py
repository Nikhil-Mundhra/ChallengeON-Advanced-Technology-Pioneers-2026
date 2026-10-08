"""The contract every forecasting model satisfies, so one back-test harness can run them all."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class Model(Protocol):
    def fit(self, panel: pd.DataFrame) -> "Model": ...

    def predict(self, panel: pd.DataFrame) -> pd.Series:
        """Predicted target on the original scale, indexed like `panel`."""
        ...
