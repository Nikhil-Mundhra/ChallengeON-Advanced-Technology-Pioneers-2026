"""SeatChain: the daily planning chain, scheduled seats -> hotel new arrivals -> guests, international.

    link 1 (arrivals):  NewArrivals_t = (c_t + sum_{k<=K} w_k Seats_{t-k}) x exp(season + weekday + events)
    link 2 (guests):    Guests_t      = (c_t + sum_{k<=21} v_k Arrivals_{t-k}) x exp(season + weekday + events)

One equation per link (agents/model/guest-model.md "planning chain"), each a ModelSpec fitted per market on the daily
panel; link 2 is the international guests nowcast form. Prediction runs the links end to end: link 2
reads the arrival lags of link 1's predicted arrivals, never observed ones, so a seat change moves
arrivals over the next K days and guests over the next 21 + K days, and the calendar, event and
base-stock terms of both links respond to it. A scenario re-runs both fitted links on changed seats;
there is no ratio algebra.

DOMESTIC has no flights: its rows are left out (NaN) and it keeps its own model. Frames passed to
predict() must hold each market's daily history: the first K + 21 days of a market only warm the
lags up and get no prediction, and a missing day leaves the lags that would read it unknown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Hashable, Optional

import numpy as np
import pandas as pd

from tourism_twin.domain.markets import DOMESTIC
from tourism_twin.features import PANEL_FEATURES
from tourism_twin.features.lags import DEFAULT_MAX_LAG, DEFAULT_SEAT_MAX_LAG
from tourism_twin.models.spec import ModelSpec

GUEST_INPUTS = ("observed", "predicted")


@dataclass(frozen=True)
class ChainSpec:
    """The two links as data. `guests_trained_on`: link 2 learns from observed arrivals, or from link
    1's in-sample predicted arrivals (what it reads at prediction time)."""

    arrivals: ModelSpec
    guests: ModelSpec
    guests_trained_on: str = "observed"
    seat_max_lag: int = DEFAULT_SEAT_MAX_LAG  # seat lags computed for link 1 (>= its kernel's max_lag)
    arrival_max_lag: int = DEFAULT_MAX_LAG    # arrival lags computed for link 2 (>= its kernel's max_lag)
    # Partial pooling of link 1's base/seat split: None fits each market alone; a value refits link 1
    # with each market's base share shrunk toward the median base share of the unpooled fits (learned
    # per fit) with this ridge strength (chosen on VALIDATION_ORIGINS).
    pooled_share_ridge: Optional[float] = None

    def __post_init__(self) -> None:
        if self.guests_trained_on not in GUEST_INPUTS:
            raise ValueError(f"guests_trained_on must be one of {GUEST_INPUTS}")

    def build(self) -> "SeatChain":
        return SeatChain(self)

    def _seat_kernel_params(self) -> Dict[str, Any]:
        entry = next(e for e in self.arrivals.components if (e if isinstance(e, str) else e[0]) == "seat_kernel")
        return {} if isinstance(entry, str) else dict(entry[1])

    def arrivals_pooled_toward(self, base_share: float) -> ModelSpec:
        """Link 1 with its seat kernel shrunk toward `base_share` at strength pooled_share_ridge."""
        params = {**self._seat_kernel_params(), "share_target": base_share, "share_ridge": self.pooled_share_ridge}
        return self.arrivals.replace_component("seat_kernel", ("seat_kernel", params))


def _refreshed(frame: pd.DataFrame, feature: str, prefix: str, flag: str, **params: Any) -> pd.DataFrame:
    """`frame` with the lag feature recomputed from its current input column. Lags are taken on each
    market's full daily calendar, so a missing day (e.g. a day without guests in a training frame)
    leaves its lags unknown instead of shifting them; `flag` is true only where every lag is known."""
    frame = frame.drop(columns=[c for c in frame.columns if c.startswith(prefix) or c == flag])
    source = PANEL_FEATURES.spec(feature).requires[-1]
    span = frame.groupby("market")["date"].agg(["min", "max"])
    grid = pd.concat([pd.DataFrame({"market": market, "date": pd.date_range(first, last, freq="D")})
                      for market, first, last in zip(span.index, span["min"], span["max"])], ignore_index=True)
    grid = grid.merge(frame[["market", "date", source]].assign(_row=frame.index), on=["market", "date"], how="left")
    lags = PANEL_FEATURES.apply(grid, [feature], **params)
    lag_columns = [c for c in lags.columns if c.startswith(prefix)]
    lags[flag] = lags[flag].astype(bool) & lags[lag_columns].notna().all(axis=1)
    lags = lags[lags["_row"].notna()].set_index("_row")[[*lag_columns, flag]]
    lags.index = lags.index.astype(frame.index.dtype)
    return frame.join(lags)


class SeatChain:
    def __init__(self, spec: ChainSpec) -> None:
        self.spec = spec

    # --- the two links ------------------------------------------------------------------------
    def _with_seat_lags(self, frame: pd.DataFrame) -> pd.DataFrame:
        return _refreshed(frame, "seat_lags", "seats_lag_", "seat_lag_complete", max_seat_lag=self.spec.seat_max_lag)

    def _arrivals(self, frame: pd.DataFrame) -> pd.Series:
        """Link 1 on every row with a full seat-lag window (others dropped)."""
        rows = self._with_seat_lags(frame)
        rows = rows[rows["seat_lag_complete"]]
        return self.arrivals_model_.predict(rows) if len(rows) else pd.Series(dtype=float)

    def _with_arrivals(self, frame: pd.DataFrame, arrivals: pd.Series) -> pd.DataFrame:
        """Rows that have a link-1 arrival, with `new_arrivals_filled` replaced by it and its lags."""
        rows = frame.loc[arrivals.index].assign(new_arrivals_filled=arrivals.to_numpy())
        rows = rows.drop(columns=[c for c in ("arrivals_mean_90",) if c in rows.columns])
        return _refreshed(rows, "arrival_lags", "arrivals_lag_", "lag_complete", max_lag=self.spec.arrival_max_lag)

    # --- Model protocol -----------------------------------------------------------------------
    def fit(self, panel: pd.DataFrame) -> "SeatChain":
        rows = panel[panel["market"] != DOMESTIC]
        seat_rows = self._with_seat_lags(rows)
        self.arrivals_model_ = self.spec.arrivals.build().fit(seat_rows)
        self.pooled_base_share_ = None
        if self.spec.pooled_share_ridge:
            name = self.spec._seat_kernel_params().get("name", "seats")
            shares = [parts[name]["base_stock_share"] for parts in self.arrivals_model_.explain().values()]
            self.pooled_base_share_ = float(np.median(shares))
            self.arrivals_model_ = self.spec.arrivals_pooled_toward(self.pooled_base_share_).build().fit(seat_rows)
        if self.spec.guests_trained_on == "observed":
            guest_rows = rows
        else:
            guest_rows = self._with_arrivals(rows, self._arrivals(rows))
        self.guests_model_ = self.spec.guests.build().fit(guest_rows)
        return self

    def predict_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Daily `arrivals` (link 1) and `guests` (link 2 on link-1 arrivals) per row of `frame`;
        NaN for DOMESTIC and for rows inside a market's lag warm-up."""
        rows = frame[frame["market"] != DOMESTIC]
        out = pd.DataFrame({"arrivals": np.nan, "guests": np.nan}, index=frame.index)
        if rows.empty:
            return out
        arrivals = self._arrivals(rows)
        if arrivals.empty:
            return out
        out.loc[arrivals.index, "arrivals"] = arrivals.to_numpy()
        lagged = self._with_arrivals(rows, arrivals)
        lagged = lagged[lagged["lag_complete"]]
        if len(lagged):
            out.loc[lagged.index, "guests"] = self.guests_model_.predict(lagged).to_numpy()
        return out

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        return self.predict_frame(frame)["guests"].rename("guests_pred")

    # --- planning -----------------------------------------------------------------------------
    def scenario(self, frame: pd.DataFrame, market: str, start: str, end: str, seat_change: float,
                 relative: bool = True) -> pd.DataFrame:
        """Re-run both fitted links for `market` with seats changed on start..end (inclusive):
        by the fraction `seat_change` (relative) or by `seat_change` seats per day. Returns per day
        the seats, arrivals and guests of the baseline and of the scenario."""
        rows = frame[frame["market"] == market]
        if rows.empty:
            raise KeyError(f"No rows for market {market!r}")
        dates = pd.to_datetime(rows["date"])
        window = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
        seats = rows["seats"].astype(float)
        changed = seats.where(~window, seats * (1.0 + seat_change) if relative else seats + seat_change).clip(lower=0.0)
        base, alt = self.predict_frame(rows), self.predict_frame(rows.assign(seats=changed))
        return pd.DataFrame({"date": dates, "in_window": window, "seats": seats, "scenario_seats": changed,
                             "arrivals": base["arrivals"], "scenario_arrivals": alt["arrivals"],
                             "guests": base["guests"], "scenario_guests": alt["guests"]}, index=rows.index)

    def explain(self) -> Dict[Hashable, Dict[str, Any]]:
        """Per market: each link's fitted parts."""
        arrivals, guests = self.arrivals_model_.explain(), self.guests_model_.explain()
        return {market: {"arrivals_link": arrivals.get(market), "guests_link": guests.get(market)}
                for market in sorted(set(arrivals) | set(guests))}

    def diagnostics(self) -> Dict[str, int]:
        one, two = self.arrivals_model_.diagnostics(), self.guests_model_.diagnostics()
        return {key: one[key] + two[key] for key in one}

