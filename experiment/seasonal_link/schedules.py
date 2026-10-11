"""Counterfactual seat schedules for the natural-experiment back-test, copied from
experiment/scenario_response/chain_runs.py: last year's seats, or seats scaled to the centred 13-week trend."""

from __future__ import annotations

import pandas as pd

import data


def last_year_seats(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """`frame` with seats on start..end replaced by the seats 364 days earlier."""
    earlier = frame[["market", "date", "seats"]].assign(date=frame["date"] + pd.Timedelta(days=364))
    joined = frame[["market", "date"]].merge(earlier, on=["market", "date"], how="left")
    inside = (frame["date"] >= start) & (frame["date"] <= end) & joined["seats"].notna().to_numpy()
    out = frame.copy()
    out.loc[inside, "seats"] = joined.loc[inside.to_numpy(), "seats"].to_numpy()
    return out


def trend_seats(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """`frame` with each day's seats on start..end scaled by its week's centred 13-week seat trend /
    week seats (the weekday pattern stays)."""
    weekly = data.weekly_sums(frame, ["seats"])
    weekly["ratio"] = data.centred_trend(weekly, "seats") / weekly["seats"]
    keyed = frame[["market"]].assign(week_start=data.week_start(frame["date"]))
    ratio = keyed.merge(weekly[["market", "week_start", "ratio"]], on=["market", "week_start"], how="left")["ratio"].to_numpy()
    inside = (frame["date"] >= start) & (frame["date"] <= end) & pd.notna(ratio) & (frame["seats"] > 0)
    out = frame.copy()
    out.loc[inside, "seats"] = frame.loc[inside, "seats"] * ratio[inside.to_numpy()]
    return out


def weekly_guests(frame: pd.DataFrame, guests: pd.Series) -> pd.Series:
    """Weekly sums of a daily guest prediction, complete weeks only, by (market, week_start)."""
    sums = data.weekly_sums(frame[["market", "date"]].assign(g=guests.to_numpy()), ["g"])
    return sums.set_index(["market", "week_start"])["g"]
