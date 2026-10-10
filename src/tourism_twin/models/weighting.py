"""Training-row weights: how much each training row counts in the fit, one axis per strategy.

A Weighting maps training rows to positive weights. Axes combine by multiplication (Product), so
"recent days count more" and "this nationality counts more" are independent plug-ins. Weights are
relative: every strategy returns weights with mean 1 over the rows it is given, and the fitters
rescale again, so w and 3w fit identically. None (no weighting) means every row counts once.

The fitters apply weights to the squared errors of data rows only; penalty rows (smoothing,
ridge) are not weighted. Centring of periodic components stays unweighted: the level owner
absorbs the difference, so predictions are unaffected and only the decomposition split shifts.
"""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable

import numpy as np
import pandas as pd


@runtime_checkable
class Weighting(Protocol):
    def weights(self, rows: pd.DataFrame) -> pd.Series:
        """Positive weights indexed like `rows`, mean 1."""
        ...


def _normalised(values: pd.Series, name: str) -> pd.Series:
    values = values.astype(float)
    if not np.isfinite(values.to_numpy()).all() or (values <= 0).any():
        raise ValueError(f"{name}: weights must be finite and positive")
    return values / values.mean()


class _ValueWeighting:
    """Equality and hashing by settings, so a ModelSpec holding a weighting stays a cache key and
    survives pickling (a ModelSpec compares by value)."""

    def _key(self) -> tuple:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and other._key() == self._key()

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._key()))

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self._key()}"


class Uniform(_ValueWeighting):
    """Every row counts once (the default behaviour)."""

    def _key(self) -> tuple:
        return ()

    def weights(self, rows: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=rows.index)


class Recency(_ValueWeighting):
    """Exponential decay with age: a row `half_life_days` older than the newest training row
    counts half as much. For slowly drifting relations (guests per arrival, docs/evidence/test-period-data.md)."""

    def __init__(self, half_life_days: float, date_column: str = "date") -> None:
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        self.half_life_days = half_life_days
        self.date_column = date_column

    def _key(self) -> tuple:
        return (self.half_life_days, self.date_column)

    def weights(self, rows: pd.DataFrame) -> pd.Series:
        dates = pd.to_datetime(rows[self.date_column])
        age = (dates.max() - dates).dt.days.to_numpy(dtype=float)
        return _normalised(pd.Series(0.5 ** (age / self.half_life_days), index=rows.index), "Recency")


class ByColumn(_ValueWeighting):
    """A weight per value of a column (e.g. nationality, season); unlisted values get `default`."""

    def __init__(self, column: str, mapping: Mapping[object, float], default: float = 1.0) -> None:
        if default <= 0 or any(v <= 0 for v in mapping.values()):
            raise ValueError("ByColumn weights must be positive")
        self.column = column
        self.mapping = dict(mapping)
        self.default = default

    def _key(self) -> tuple:
        return (self.column, tuple(sorted(self.mapping.items(), key=repr)), self.default)

    def weights(self, rows: pd.DataFrame) -> pd.Series:
        values = rows[self.column].map(self.mapping).fillna(self.default)
        return _normalised(values, f"ByColumn({self.column})")


class Product(_ValueWeighting):
    """Several axes at once: the product of each strategy's weights."""

    def __init__(self, *parts: Weighting) -> None:
        if not parts:
            raise ValueError("Product needs at least one weighting")
        self.parts = parts

    def _key(self) -> tuple:
        return self.parts

    def weights(self, rows: pd.DataFrame) -> pd.Series:
        total = pd.Series(1.0, index=rows.index)
        for part in self.parts:
            total = total * part.weights(rows)
        return _normalised(total, "Product")
