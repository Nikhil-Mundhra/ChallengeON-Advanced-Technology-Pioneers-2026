"""DataHandler: everything between a panel and the fitters that is data, not math.

    panel ─► features (components' `requires`, resolved through PANEL_FEATURES)
          ─► training rows (named row rules, applied in order)
          ─► target transform (log) and training weights (a Weighting, models/weighting.py)
          ─► AdditiveLogModel fits components on the prepared rows

AdditiveLogModel owns one DataHandler; specs choose the rules and the weighting, so a new data
step is a rule or a strategy here, never a change to the model or the fitters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from tourism_twin.features import PANEL_FEATURES
from tourism_twin.models.weighting import Weighting


class RowRule:
    """A named training-row filter: keep rows where `keep(frame)` is True. Rules are small frozen
    dataclasses (no lambdas), so specs holding them stay hashable and picklable."""

    name: str
    requires: Tuple[str, ...]

    def keep(self, frame: pd.DataFrame) -> pd.Series:
        raise NotImplementedError


@dataclass(frozen=True)
class TargetPresent(RowRule):
    column: str

    @property
    def name(self) -> str:
        return f"{self.column}_present"

    @property
    def requires(self) -> Tuple[str, ...]:
        return (self.column,)

    def keep(self, frame: pd.DataFrame) -> pd.Series:
        return frame[self.column].notna()


@dataclass(frozen=True)
class NotFlagged(RowRule):
    """Drop rows whose flag is 1 (e.g. is_one_off_period: one-off shocks)."""

    flag: str

    @property
    def name(self) -> str:
        return f"not_{self.flag}"

    @property
    def requires(self) -> Tuple[str, ...]:
        return (self.flag,)

    def keep(self, frame: pd.DataFrame) -> pd.Series:
        return frame[self.flag] != 1


@dataclass(frozen=True)
class Flagged(RowRule):
    """Keep only rows whose flag is truthy (e.g. lag_complete: a full arrival-lag window)."""

    flag: str

    @property
    def name(self) -> str:
        return self.flag

    @property
    def requires(self) -> Tuple[str, ...]:
        return (self.flag,)

    def keep(self, frame: pd.DataFrame) -> pd.Series:
        return frame[self.flag].astype(bool)


@dataclass(frozen=True)
class OnOrAfter(RowRule):
    """Keep only rows dated on or after `start` (e.g. drop a one-off regime at the start of the data)."""

    column: str
    start: str

    @property
    def name(self) -> str:
        return f"{self.column}>={self.start}"

    @property
    def requires(self) -> Tuple[str, ...]:
        return (self.column,)

    def keep(self, frame: pd.DataFrame) -> pd.Series:
        return pd.to_datetime(frame[self.column]) >= pd.Timestamp(self.start)


def on_or_after(column: str, start: str) -> RowRule:
    return OnOrAfter(column, start)


def target_present(target: str) -> RowRule:
    return TargetPresent(target)


def not_flagged(flag: str) -> RowRule:
    return NotFlagged(flag)


def flagged(flag: str) -> RowRule:
    return Flagged(flag)


class DataHandler:
    def __init__(
        self,
        target: str = "guests",
        anchor: str = "date",
        feature_params: Optional[Dict[str, Any]] = None,
        rules: Sequence[RowRule] = (),
        weighting: Optional[Weighting] = None,
    ) -> None:
        self.target = target
        self.anchor = anchor
        self.feature_params = {"anchor": anchor, **(feature_params or {})}
        self.rules = (target_present(target), *rules)
        self.weighting = weighting

    def with_features(self, panel: pd.DataFrame, requires: Iterable[str]) -> pd.DataFrame:
        """`panel` plus every registered feature the components and rules need and it lacks."""
        if not panel.index.is_unique:
            raise ValueError("Panel index must be unique (reset_index after concatenating frames)")
        needed = {r for r in requires if r not in panel.columns}
        needed |= {r for rule in self.rules for r in rule.requires if r not in panel.columns}
        registered = [name for name in needed if name in PANEL_FEATURES]
        missing = needed - set(registered)
        if missing:
            raise KeyError(f"Columns not in panel and not registered features: {sorted(missing)}")
        return PANEL_FEATURES.apply(panel, registered, **self.feature_params) if registered else panel

    def training_rows(self, panel: pd.DataFrame) -> pd.DataFrame:
        """Rows that pass every rule, in order. The log target needs positive values."""
        rows = panel
        for rule in self.rules:
            rows = rows[rule.keep(rows)]
        non_positive = int((rows[self.target] <= 0).sum())
        if non_positive:
            raise ValueError(f"{non_positive} training rows have {self.target} <= 0; the log target needs positive values")
        return rows

    def y(self, rows: pd.DataFrame) -> pd.Series:
        return np.log(rows[self.target])

    def weights(self, rows: pd.DataFrame) -> Optional[pd.Series]:
        """Training weights for `rows`, or None when the spec has no weighting."""
        return None if self.weighting is None else self.weighting.weights(rows)
