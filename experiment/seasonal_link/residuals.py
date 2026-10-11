"""Time-removed weekly residuals per market and series, on log values.

    trend    = centred 13-week mean of the log (as experiment/eda_coupling)
    season   = "fourier": least squares on 4 annual harmonics of the detrended log (the chain's season form)
               "woy":     week-of-year mean of the detrended log (experiment/eda_coupling)
    residual = log - trend - season

With weeks from 2023-01 to 2025-01 most weeks of the year occur twice, so the "woy" residuals of the two
years are mirror images (r_2023 = -r_2024): it cannot tell one year's half from the other's. "fourier"
spends 8 parameters per market instead of 52 and is the main form here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SERIES = ("seats", "p2p", "arrivals", "guests")
HARMONICS = 4


def annual_basis(dates: pd.Series, harmonics: int) -> np.ndarray:
    phase = 2 * np.pi * pd.to_datetime(dates).dt.dayofyear.to_numpy() / 365.25
    return np.column_stack([f(h * phase) for h in range(1, harmonics + 1) for f in (np.sin, np.cos)])


def decompose(weekly: pd.DataFrame, method: str = "fourier") -> pd.DataFrame:
    """`weekly` plus <series>_res for every series; NaN where the centred trend is undefined."""
    out = []
    for _, rows in weekly.groupby("market"):
        rows = rows.sort_values("week_start").copy()
        full = pd.date_range(rows["week_start"].min(), rows["week_start"].max(), freq="7D")
        for name in SERIES:
            log = pd.Series(np.log(rows[name].clip(lower=1).to_numpy()), index=pd.DatetimeIndex(rows["week_start"]))
            trend = log.reindex(full).rolling(13, center=True, min_periods=13).mean().reindex(log.index).to_numpy()
            detrended = log.to_numpy() - trend
            known = np.isfinite(detrended)
            if method == "fourier":
                basis = np.c_[np.ones(len(rows)), annual_basis(rows["week_start"] + pd.Timedelta(days=3), HARMONICS)]
                coef, *_ = np.linalg.lstsq(basis[known], detrended[known], rcond=None)
                season = basis @ coef
            else:
                week = rows["week_start"].dt.isocalendar().week.astype(int).to_numpy()
                season = pd.Series(detrended).groupby(week).transform("mean").to_numpy()
            rows[f"{name}_res"] = detrended - season
        out.append(rows)
    return pd.concat(out).sort_values(["market", "week_start"]).reset_index(drop=True)
