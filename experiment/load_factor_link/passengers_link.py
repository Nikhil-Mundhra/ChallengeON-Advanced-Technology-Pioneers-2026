"""Link 0 of the passenger chain: scheduled seats -> point-to-point (P2P) passengers per market-day.

Every link reads only seats and the calendar at prediction time; realized P2P is a training target only
(RealizedP2P is the labelled oracle).

    TrendResponse (variant A): load factor (P2P per seat) on a knot base, calendar and the week's
        seat deviation from the market's 91-day trailing trend; slope beta - 1 (see the class).
    LogitLoadFactor (variant L): logit of P2P per seat on the same seat deviation, season level,
        weekday and events; P2P = seats x sigmoid.
    ScheduleInputs (variant C): log P2P on flights, gauge, airlines and premium seat share, each as a
        deviation from its own 91-day trailing trend, with one coefficient per input and market.
    UCurve (variant B):
        P2P_t = seats_t * f(seats_t / mean training seats of the market), f a pooled decile step
        function of P2P per seat: the raw U, with no trend, season or market level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import event_offsets

WEEK_DAYS = 7
TREND_DAYS = 91
TREND_MIN_DAYS = 28  # shorter windows only at the start of the flight data (2023-01)
HARMONICS = 4
SEASONS = ("Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder")
GAMMA_GRID = tuple(np.round(np.arange(-3.0, 4.01, 0.25), 2))


def trailing_mean(frame: pd.DataFrame, column: str, days: int, min_days: int) -> pd.Series:
    """Trailing `days`-day mean of `column` per market (today included), on calendar time so a missing
    day shortens the window instead of shifting it."""
    out = pd.Series(np.nan, index=frame.index)
    for _, rows in frame[["market", "date", column]].groupby("market"):
        rows = rows.sort_values("date")
        series = pd.Series(rows[column].to_numpy(dtype=float), index=pd.DatetimeIndex(rows["date"]))
        window = series.rolling(f"{days}D")
        out.loc[rows.index] = np.where(window.count().to_numpy() >= min_days, window.mean().to_numpy(), np.nan)
    return out


def seat_trend(frame: pd.DataFrame) -> pd.Series:
    """log trailing 91-day mean seats (the two-speed variant's long-run input)."""
    trend = trailing_mean(frame, "seats", TREND_DAYS, TREND_MIN_DAYS)
    return pd.Series(np.log(trend.where(trend > 0)), index=frame.index)


def seat_deviation(frame: pd.DataFrame) -> pd.Series:
    """log(trailing 7-day mean seats / trailing 91-day mean seats): the week's seats against the
    market's recent trend. Day-to-day schedule changes inside a week stay out of it: daily P2P tracks
    them almost one for one (beta 0.96-0.99 when the deviation was taken on single days)."""
    week, trend = trailing_mean(frame, "seats", WEEK_DAYS, WEEK_DAYS), trailing_mean(frame, "seats", TREND_DAYS, TREND_MIN_DAYS)
    ok = (week > 0) & (trend > 0)
    return pd.Series(np.log(week.where(ok) / trend.where(ok)), index=frame.index)


def _calendar(dates: pd.Series) -> np.ndarray:
    """Annual Fourier terms on day of year plus weekday one-hot (Monday dropped)."""
    day = dates.dt.dayofyear.to_numpy() / 365.25 * 2 * np.pi
    fourier = [f(h * day) for h in range(1, HARMONICS + 1) for f in (np.sin, np.cos)]
    weekday = [(dates.dt.weekday == d).to_numpy(float) for d in range(1, 7)]
    return np.column_stack(fourier + weekday)


def _knots(dates: pd.Series, knot_days: int) -> pd.DatetimeIndex:
    n_knots = max(2, int(round((dates.max() - dates.min()).days / knot_days)) + 1)
    return pd.DatetimeIndex(np.linspace(dates.min().value, dates.max().value, n_knots).astype("datetime64[ns]")).normalize()


def _hat_basis(dates: pd.Series, knots: pd.DatetimeIndex) -> np.ndarray:
    """Piecewise-linear basis over the knots, flat outside them."""
    days = (dates - knots[0]).dt.days.to_numpy(float)
    knot_days = np.asarray((knots - knots[0]).days, float)
    return np.column_stack([np.interp(days, knot_days, np.eye(len(knots))[j]) for j in range(len(knots))])


SLOPES = ("single", "split", "usual_lf")


@dataclass
class _MarketFit:
    knots: pd.DatetimeIndex
    coef: np.ndarray
    smear: float


@dataclass
class TrendResponse:
    """Variant A, fitted per market by bounded least squares on log(P2P / seats):

        log(P2P_t / seats_t) = l(t) + season + weekday + (beta - 1) * x_t,   x_t = seat_deviation

    l(t) is a knot base (first-difference penalty), flat beyond the training days. beta in
    [0, beta_max] is the P2P elasticity to a seat deviation; load factor moves by beta - 1. Seat growth
    that the 91-day trend has absorbed passes one for one; with `long_run` (variant TS) it passes with
    beta_long in [0, beta_max] on log trend seats, and the knot base carries only the rest.

    slopes: "single" one beta; "split" beta_up (x > 0) and beta_down (x < 0), tied by a ridge of
    strength `tie`; "usual_lf" beta_up and beta_down = beta0 + gamma * (usual LF - mean usual LF), with
    usual LF = training mean pax / seats of the market and season and gamma one pooled value chosen
    by training SSE over GAMMA_GRID. `pool` shrinks each market's slopes toward the median of the
    unpooled market fits. Both ridges are in units of the market's own sum of squared deviations
    (1 = the prior weighs as much as the market's data)."""

    knot_days: int = 365
    smoothing: float = 1.0
    slopes: str = "single"
    pool: float = 0.0
    tie: float = 1.0
    beta_max: float = 1.0  # the brief's bound; with 2.0 the P2P betas leave 1 (README.md)
    long_run: bool = False
    fits_: Dict[str, _MarketFit] = field(default_factory=dict)
    unpooled_: Dict[str, np.ndarray] = field(default_factory=dict)
    pooled_target_: Optional[np.ndarray] = None
    usual_lf_: Dict[tuple, float] = field(default_factory=dict)
    usual_lf_market_: Dict[str, float] = field(default_factory=dict)
    usual_lf_mean_: float = 0.0
    gamma_: float = 0.0
    gamma_sse_: Dict[float, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.slopes not in SLOPES:
            raise ValueError(f"slopes must be one of {SLOPES}")
        if self.long_run and self.slopes != "single":
            raise ValueError("long_run needs slopes='single'")

    @property
    def n_slopes(self) -> int:
        return (1 if self.slopes == "single" else 2) + int(self.long_run)

    def _usual_lf(self, frame: pd.DataFrame) -> np.ndarray:
        cell = pd.Series(list(zip(frame["market"], frame["season"])), index=frame.index).map(self.usual_lf_)
        return (cell.fillna(frame["market"].map(self.usual_lf_market_)) - self.usual_lf_mean_).to_numpy()

    def _slope_columns(self, deviation: np.ndarray, log_trend: Optional[np.ndarray]) -> np.ndarray:
        if self.slopes == "single":
            columns = deviation[:, None]
        else:
            columns = np.column_stack([np.maximum(deviation, 0.0), np.minimum(deviation, 0.0)])
        return np.column_stack([columns, log_trend]) if self.long_run else columns

    def _gamma_offset(self, frame: pd.DataFrame, deviation: np.ndarray, gamma: float) -> np.ndarray:
        if self.slopes != "usual_lf" or not gamma:
            return np.zeros(len(deviation))
        return gamma * np.minimum(deviation, 0.0) * self._usual_lf(frame)

    def _design(self, dates: pd.Series, deviation: np.ndarray, knots: pd.DatetimeIndex,
                log_trend: Optional[np.ndarray] = None) -> np.ndarray:
        return np.column_stack([_hat_basis(dates, knots), _calendar(dates), self._slope_columns(deviation, log_trend)])

    def _fit_market(self, rows: pd.DataFrame, target: np.ndarray, prior: Optional[np.ndarray]) -> tuple:
        dates = pd.to_datetime(rows["date"])
        knots = _knots(dates, self.knot_days)
        design = self._design(dates, rows["deviation"].to_numpy(), knots, rows["log_trend"].to_numpy())
        n, width, k, n_knots = len(target), design.shape[1], self.n_slopes, len(knots)
        rows_penalty = [np.c_[np.sqrt(self.smoothing * n / n_knots) * np.diff(np.eye(n_knots), axis=0), np.zeros((n_knots - 1, width - n_knots))]]
        rhs_penalty = [np.zeros(n_knots - 1)]
        slopes = design[:, -k:].copy()
        if self.long_run:  # log trend seats is a level; its ridge scale is its spread
            slopes[:, -1] -= slopes[:, -1].mean()
        for j in range(k if prior is not None and self.pool else 0):
            row = np.zeros(width)
            row[width - k + j] = np.sqrt(self.pool * float(slopes[:, j] @ slopes[:, j]))
            rows_penalty.append(row[None, :])
            rhs_penalty.append(np.array([row[width - k + j] * prior[j]]))
        if self.slopes == "split" and self.tie:
            row = np.zeros(width)
            row[-2:] = np.sqrt(self.tie * float(np.sum(slopes ** 2)) / 2) * np.array([1.0, -1.0])
            rows_penalty.append(row[None, :])
            rhs_penalty.append(np.zeros(1))
        system = np.vstack([design, *rows_penalty])
        rhs = np.concatenate([target, *rhs_penalty])
        lower = np.r_[np.full(width - k, -np.inf), -np.ones(k)]
        upper = np.r_[np.full(width - k, np.inf), np.full(k, self.beta_max - 1.0)]
        coef = lsq_linear(system, rhs, bounds=(lower, upper)).x
        residual = target - design @ coef
        return _MarketFit(knots, coef, float(np.mean(np.exp(residual)))), float(residual @ residual)

    def _fit_all(self, rows: pd.DataFrame, target: np.ndarray, prior: Optional[np.ndarray]) -> tuple:
        fits, sse = {}, 0.0
        for market, index in rows.groupby("market").indices.items():
            fits[market], part = self._fit_market(rows.iloc[index], target[index], prior)
            sse += part
        return fits, sse

    def fit(self, frame: pd.DataFrame) -> "TrendResponse":
        usable = frame[(frame["seats"] > 0) & (frame["p2p"] > 0)]
        cells = usable.groupby(["market", "season"])
        self.usual_lf_ = (cells["pax"].sum() / cells["seats"].sum()).to_dict()
        by_market = usable.groupby("market")
        self.usual_lf_market_ = (by_market["pax"].sum() / by_market["seats"].sum()).to_dict()
        self.usual_lf_mean_ = float(np.mean(list(self.usual_lf_.values())))
        deviation = seat_deviation(frame)
        rows = usable.assign(deviation=deviation.loc[usable.index], log_trend=seat_trend(frame).loc[usable.index])
        rows = rows[rows["deviation"].notna()].reset_index(drop=True)
        base_target = np.log(rows["p2p"] / rows["seats"]).to_numpy()
        x = rows["deviation"].to_numpy()
        grid = GAMMA_GRID if self.slopes == "usual_lf" else (0.0,)
        self.gamma_sse_ = {g: self._fit_all(rows, base_target - self._gamma_offset(rows, x, g), None)[1] for g in grid}
        self.gamma_ = min(self.gamma_sse_, key=self.gamma_sse_.get)
        target = base_target - self._gamma_offset(rows, x, self.gamma_)
        unpooled, _ = self._fit_all(rows, target, None)
        self.unpooled_ = {m: f.coef[-self.n_slopes:] + 1.0 for m, f in unpooled.items()}
        self.pooled_target_ = np.median(np.vstack(list(self.unpooled_.values())), axis=0) - 1.0
        self.fits_ = self._fit_all(rows, target, self.pooled_target_)[0] if self.pool else unpooled
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        deviation, log_trend = seat_deviation(frame), seat_trend(frame)
        out = pd.Series(np.where(frame["seats"] == 0, 0.0, np.nan), index=frame.index)
        known = deviation.notna() & (frame["seats"] > 0)
        for market, index in frame[known].groupby("market").groups.items():
            fit = self.fits_.get(market)
            if fit is None:
                continue
            part = frame.loc[index]
            x = deviation.loc[index].to_numpy()
            log_rate = (self._design(pd.to_datetime(part["date"]), x, fit.knots, log_trend.loc[index].to_numpy()) @ fit.coef
                        + self._gamma_offset(part, x, self.gamma_))
            out.loc[index] = part["seats"].to_numpy() * np.exp(log_rate) * fit.smear
        return out

    def betas(self) -> pd.DataFrame:
        """Per market: fitted slopes (beta), and the unpooled fit's."""
        names = (["beta"] if self.slopes == "single" else ["beta_up", "beta_down"]) + (["beta_long"] if self.long_run else [])
        fitted = pd.DataFrame({m: f.coef[-self.n_slopes:] + 1.0 for m, f in self.fits_.items()}, index=names).T
        raw = pd.DataFrame(self.unpooled_, index=[f"{n}_unpooled" for n in names]).T
        out = fitted.join(raw)
        if self.slopes == "usual_lf":
            usual = pd.Series(self.usual_lf_market_) - self.usual_lf_mean_
            out["beta_down_at_market_lf"] = out["beta_down"] + self.gamma_ * usual.reindex(out.index)
        return out


SCHEDULE_INPUTS = ("flights", "gauge", "airlines", "premium_share")


def schedule_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """Daily flights, gauge (seats per flight), airlines and premium seat share, plus each one's
    trailing TREND_DAYS-day mean, on days with seats; seats = flights x gauge, so seats is not an input."""
    flown = frame["seats"] > 0
    values = pd.DataFrame({"market": frame["market"], "date": frame["date"],
                           "flights": frame["flights"].where(flown),
                           "gauge": (frame["seats"] / frame["flights"]).where(flown),
                           "airlines": frame["airlines"].where(flown),
                           "premium_share": (frame["premium_seats"] / frame["seats"]).where(flown)})
    for column in SCHEDULE_INPUTS:
        values[f"{column}_trend"] = trailing_mean(values, column, TREND_DAYS, TREND_MIN_DAYS)
    return values


def schedule_deviations(values: pd.DataFrame) -> pd.DataFrame:
    """Each input against its own trend: log ratios, and a difference for the premium share."""
    out = pd.DataFrame(index=values.index)
    for column in SCHEDULE_INPUTS[:3]:
        out[column] = np.log(values[column] / values[f"{column}_trend"])
    out["premium_share"] = values["premium_share"] - values["premium_share_trend"]
    return out


@dataclass
class ScheduleInputs:
    """Variant C, per market by least squares:

        log P2P_t - log(F_trend_t x G_trend_t) = l(t) + season + weekday + sum_i b_i x_i,t

    x_i = each schedule input against its own trend (schedule_deviations); daily, so a single
    cancelled flight moves x_flights. The inputs enter as if independent (one coefficient each).
    `pool` shrinks each market's b toward the cross-market median of the unpooled fits, in units of
    the input's own sum of squares (floored, so an input that never moves gets the median)."""

    knot_days: int = 365
    smoothing: float = 1.0
    pool: float = 0.3
    fits_: Dict[str, _MarketFit] = field(default_factory=dict)
    unpooled_: Dict[str, np.ndarray] = field(default_factory=dict)
    pooled_target_: Optional[np.ndarray] = None

    def _rows(self, frame: pd.DataFrame) -> tuple:
        values = schedule_inputs(frame)
        deviations = schedule_deviations(values)
        offset = np.log(values["flights_trend"] * values["gauge_trend"])
        known = deviations.notna().all(axis=1) & np.isfinite(offset)
        return values, deviations, offset, known

    def _design(self, dates: pd.Series, deviations: np.ndarray, knots: pd.DatetimeIndex) -> np.ndarray:
        return np.column_stack([_hat_basis(dates, knots), _calendar(dates), deviations])

    def _fit_market(self, dates: pd.Series, deviations: np.ndarray, target: np.ndarray, prior: Optional[np.ndarray]) -> _MarketFit:
        knots = _knots(dates, self.knot_days)
        design = self._design(dates, deviations, knots)
        n, width, k, n_knots = len(target), design.shape[1], deviations.shape[1], len(knots)
        rows = [np.c_[np.sqrt(self.smoothing * n / n_knots) * np.diff(np.eye(n_knots), axis=0), np.zeros((n_knots - 1, width - n_knots))]]
        rhs = [np.zeros(n_knots - 1)]
        scale = np.sqrt(np.maximum((deviations ** 2).sum(axis=0), n * 1e-4))
        weight = np.sqrt(self.pool) if prior is not None else 1e-3  # unpooled: a tiny ridge toward 0 for inputs that never move
        ridge = np.zeros((k, width))
        ridge[:, width - k:] = np.diag(weight * scale)
        rows.append(ridge)
        rhs.append(weight * scale * (prior if prior is not None else np.zeros(k)))
        coef = np.linalg.lstsq(np.vstack([design, *rows]), np.concatenate([target, *rhs]), rcond=None)[0]
        return _MarketFit(knots, coef, float(np.mean(np.exp(target - design @ coef))))

    def fit(self, frame: pd.DataFrame) -> "ScheduleInputs":
        values, deviations, offset, known = self._rows(frame)
        use = known & (frame["p2p"] > 0)
        target = np.log(frame["p2p"].where(use)) - offset
        groups = frame[use].groupby("market").groups
        k = len(SCHEDULE_INPUTS)

        def fits(prior):
            return {m: self._fit_market(pd.to_datetime(frame.loc[i, "date"]), deviations.loc[i].to_numpy(), target.loc[i].to_numpy(), prior)
                    for m, i in groups.items()}

        unpooled = fits(None)
        self.unpooled_ = {m: f.coef[-k:] for m, f in unpooled.items()}
        self.pooled_target_ = np.median(np.vstack(list(self.unpooled_.values())), axis=0)
        self.fits_ = fits(self.pooled_target_) if self.pool else unpooled
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        values, deviations, offset, known = self._rows(frame)
        out = pd.Series(np.where(frame["seats"] == 0, 0.0, np.nan), index=frame.index)
        for market, index in frame[known].groupby("market").groups.items():
            fit = self.fits_.get(market)
            if fit is None:
                continue
            log_rate = self._design(pd.to_datetime(frame.loc[index, "date"]), deviations.loc[index].to_numpy(), fit.knots) @ fit.coef
            out.loc[index] = np.exp(offset.loc[index].to_numpy() + log_rate) * fit.smear
        return out

    def coefficients(self) -> pd.DataFrame:
        k = len(SCHEDULE_INPUTS)
        fitted = pd.DataFrame({m: f.coef[-k:] for m, f in self.fits_.items()}, index=list(SCHEDULE_INPUTS)).T
        raw = pd.DataFrame(self.unpooled_, index=[f"{c}_unpooled" for c in SCHEDULE_INPUTS]).T
        return fitted.join(raw)


LF_CLIP = (0.005, 0.995)


def _event_columns(dates: pd.Series) -> np.ndarray:
    """One in-window indicator per DEFAULT_KERNEL_EVENTS event."""
    offsets = event_offsets(dates, load_event_calendar(), DEFAULT_KERNEL_EVENTS)
    return offsets.notna().to_numpy(float)


@dataclass
class LogitLoadFactor:
    """Variant L, per market by seat-weighted least squares on the logit of P2P per seat:

        logit(P2P_t / seats_t) = l(t) + season level + weekday + events + b * x_t,   x_t = seat_deviation

    l(t) knot base, flat beyond the training days; season level one-hot on the panel's four seasons.
    P2P = seats x sigmoid(...), so the rate stays inside (0, 1); a market's training sum of P2P is
    matched by one ratio. b is unbounded; the P2P elasticity it implies is 1 + b (1 - LF), so the
    same b moves a nearly full market's P2P almost one for one with seats. `pool` as in TrendResponse."""

    knot_days: int = 365
    smoothing: float = 1.0
    pool: float = 0.3
    fits_: Dict[str, _MarketFit] = field(default_factory=dict)
    unpooled_: Dict[str, float] = field(default_factory=dict)
    pooled_target_: Optional[float] = None

    def _design(self, frame: pd.DataFrame, deviation: np.ndarray, knots: pd.DatetimeIndex) -> np.ndarray:
        dates = pd.to_datetime(frame["date"])
        seasons = np.column_stack([(frame["season"] == s).to_numpy(float) for s in SEASONS[1:]])
        weekday = _calendar(dates)[:, 2 * HARMONICS:]
        return np.column_stack([_hat_basis(dates, knots), seasons, weekday, _event_columns(dates), deviation])

    def _fit_market(self, rows: pd.DataFrame, prior: Optional[float]) -> _MarketFit:
        dates = pd.to_datetime(rows["date"])
        knots = _knots(dates, self.knot_days)
        x = rows["deviation"].to_numpy()
        design = self._design(rows, x, knots)
        rate = np.clip(rows["p2p"] / rows["seats"], *LF_CLIP).to_numpy()
        target = np.log(rate / (1 - rate))
        weight = np.sqrt(rows["seats"].to_numpy() / rows["seats"].mean())
        n, width, n_knots = len(target), design.shape[1], len(knots)
        smooth = np.c_[np.sqrt(self.smoothing * n / n_knots) * np.diff(np.eye(n_knots), axis=0), np.zeros((n_knots - 1, width - n_knots))]
        ridge = np.zeros((width - n_knots, width))
        ridge[:, n_knots:] = 1e-3 * np.sqrt(n) * np.eye(width - n_knots)  # events absent from a window stay at 0
        rows_penalty, rhs_penalty = [smooth, ridge], [np.zeros(n_knots - 1), np.zeros(width - n_knots)]
        if prior is not None and self.pool:
            row = np.zeros(width)
            row[-1] = np.sqrt(self.pool * float(np.sum((x - x.mean()) ** 2)))
            rows_penalty.append(row[None, :])
            rhs_penalty.append(np.array([row[-1] * prior]))
        coef = np.linalg.lstsq(np.vstack([design * weight[:, None], *rows_penalty]),
                               np.concatenate([target * weight, *rhs_penalty]), rcond=None)[0]
        fitted = rows["seats"].to_numpy() / (1 + np.exp(-(design @ coef)))
        return _MarketFit(knots, coef, float(rows["p2p"].sum() / fitted.sum()))

    def _rows(self, frame: pd.DataFrame) -> pd.DataFrame:
        return frame.assign(deviation=seat_deviation(frame))

    def fit(self, frame: pd.DataFrame) -> "LogitLoadFactor":
        rows = self._rows(frame)
        rows = rows[(rows["seats"] > 0) & (rows["p2p"] > 0) & rows["deviation"].notna()]
        groups = rows.groupby("market").groups
        unpooled = {m: self._fit_market(rows.loc[i], None) for m, i in groups.items()}
        self.unpooled_ = {m: float(f.coef[-1]) for m, f in unpooled.items()}
        self.pooled_target_ = float(np.median(list(self.unpooled_.values())))
        self.fits_ = {m: self._fit_market(rows.loc[i], self.pooled_target_) for m, i in groups.items()} if self.pool else unpooled
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        rows = self._rows(frame)
        out = pd.Series(np.where(frame["seats"] == 0, 0.0, np.nan), index=frame.index)
        known = rows["deviation"].notna() & (frame["seats"] > 0)
        for market, index in rows[known].groupby("market").groups.items():
            fit = self.fits_.get(market)
            if fit is None:
                continue
            part = rows.loc[index]
            eta = self._design(part, part["deviation"].to_numpy(), fit.knots) @ fit.coef
            out.loc[index] = part["seats"].to_numpy() / (1 + np.exp(-eta)) * fit.smear
        return out

    def slopes(self) -> pd.DataFrame:
        return pd.DataFrame({"b": {m: float(f.coef[-1]) for m, f in self.fits_.items()}, "b_unpooled": self.unpooled_})


@dataclass
class UCurve:
    """Variant B: least squares of P2P per seat on a decile step function of seats / market mean seats
    (step function least squares = the mean per bin), pooled over markets and days."""

    bins: int = 10
    mean_seats_: Dict[str, float] = field(default_factory=dict)
    edges_: Optional[np.ndarray] = None
    rate_: Optional[np.ndarray] = None

    def _relative(self, frame: pd.DataFrame) -> pd.Series:
        return frame["seats"] / frame["market"].map(self.mean_seats_)

    def fit(self, frame: pd.DataFrame) -> "UCurve":
        rows = frame[frame["seats"] > 0]
        self.mean_seats_ = rows.groupby("market")["seats"].mean().to_dict()
        relative = self._relative(rows).to_numpy()
        self.edges_ = np.quantile(relative, np.linspace(0, 1, self.bins + 1)[1:-1])
        rate = (rows["p2p"] / rows["seats"]).to_numpy()
        which = np.searchsorted(self.edges_, relative)
        self.rate_ = np.array([rate[which == b].mean() for b in range(self.bins)])
        return self

    def rate(self, relative: np.ndarray) -> np.ndarray:
        return self.rate_[np.searchsorted(self.edges_, relative)]

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        relative = self._relative(frame)
        known = relative.notna().to_numpy()
        out = pd.Series(np.nan, index=frame.index)
        out[known] = frame["seats"].to_numpy()[known] * self.rate(relative.to_numpy()[known])
        return out

    def curve(self) -> pd.DataFrame:
        lows = np.r_[0.0, self.edges_]
        highs = np.r_[self.edges_, np.inf]
        return pd.DataFrame({"seats_rel_from": lows, "seats_rel_to": highs, "p2p_per_seat": self.rate_})


@dataclass
class RealizedP2P:
    """Oracle: the realized P2P of the predicted period. Not deployable; diagnostics only."""

    def fit(self, frame: pd.DataFrame) -> "RealizedP2P":
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        return frame["p2p"].astype(float)
