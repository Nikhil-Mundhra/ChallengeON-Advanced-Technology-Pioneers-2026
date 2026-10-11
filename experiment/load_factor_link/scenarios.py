"""Scenario sanity on the last fold's fitted models: seats +-10% for four weeks in three markets.
P2P and its load factor (P2P / seats) are read over the window; arrivals and guests over the window
plus TAIL_DAYS, so the lagged response is included."""

from __future__ import annotations

import pickle

import numpy as np
import pandas as pd

import data
from passenger_chain import scenario
from passengers_link import UCurve

MARKETS = ("UNITED KINGDOM", "INDIA", "CHINA")
START, END = pd.Timestamp("2024-10-01"), pd.Timestamp("2024-10-28")
TAIL_DAYS = 28
CHANGES = (0.10, -0.10)


def _model(name: str):
    with open(data.OUT / "runs" / f"{name}__6.pkl", "rb") as handle:
        return pickle.load(handle)["model"]


def _change(frame: pd.DataFrame, column: str, mask: pd.Series) -> float:
    base, alt = frame.loc[mask, column].sum(), frame.loc[mask, f"scenario_{column}"].sum()
    return 100 * (alt / base - 1) if base > 0 else np.nan


def table(names: list) -> pd.DataFrame:
    panel = data.panel()
    rows = []
    for name in names:
        model = _model(name)
        link0 = getattr(model, "passengers", None)
        for market in MARKETS:
            for change in CHANGES:
                for via in (("gauge", "flights") if name == "C" else ("gauge",)):
                    out = scenario(model, panel, market, str(START.date()), str(END.date()), change, via=via)
                    window = out["in_window"]
                    after = (out["date"] >= START) & (out["date"] <= END + pd.Timedelta(days=TAIL_DAYS))
                    lf = 100 * out.loc[window, "p2p"].sum(min_count=1) / out.loc[window, "seats"].sum()
                    lf_alt = 100 * out.loc[window, "scenario_p2p"].sum(min_count=1) / out.loc[window, "scenario_seats"].sum()
                    row = {"variant": name, "market": market, "seats": f"{change:+.0%}", "via": via,
                           "p2p_pct": _change(out, "p2p", window), "lf_base_pct": lf, "lf_pp": lf_alt - lf,
                           "arrivals_pct": _change(out, "arrivals", after), "guests_pct": _change(out, "guests", after)}
                    if isinstance(link0, UCurve):
                        seats = panel.loc[out.index[window], "seats"]
                        relative = float(seats.mean() / link0.mean_seats_[market])
                        row["u_position"] = f"{relative:.2f} -> {relative * (1 + change):.2f}"
                    rows.append(row)
    return pd.DataFrame(rows)
