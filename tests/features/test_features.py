"""Feature registry, event registry and event features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from tourism_twin.features import PANEL_FEATURES, FeatureRegistry, FeatureSpec, Kind
from tourism_twin.domain.events import DEFAULT_KERNEL_EVENTS, load_event_calendar
from tourism_twin.features.events import offset_column
from tourism_twin.models.components import LinearTrend
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import JointLinear
from synthetic import _synthetic


def _toy_registry() -> FeatureRegistry:
    registry = FeatureRegistry()
    registry.register(FeatureSpec("ratio", Kind.RATIO, ("a", "b"), lambda f, **_: f["a"] / f["b"]))
    registry.register(FeatureSpec("ratio_flag", Kind.FLAG, ("ratio",), lambda f, **_: (f["ratio"] > 1).astype(int)))
    return registry


def test_registry_resolves_dependencies_once_and_rejects_bad_graphs():
    frame = pd.DataFrame({"a": [2.0, 1.0], "b": [1.0, 2.0]})
    registry = _toy_registry()
    out = registry.apply(frame, ["ratio_flag", "ratio"])
    assert list(out.columns) == ["a", "b", "ratio", "ratio_flag"]
    assert out["ratio_flag"].tolist() == [1, 0]
    assert list(frame.columns) == ["a", "b"]  # input frame is not mutated
    with pytest.raises(KeyError, match="missing column 'b'"):
        registry.apply(pd.DataFrame({"a": [1.0]}), ["ratio"])
    registry.register(FeatureSpec("x", Kind.FLAG, ("y",), lambda f, **_: f))
    registry.register(FeatureSpec("y", Kind.FLAG, ("x",), lambda f, **_: f))
    with pytest.raises(ValueError, match="cycle"):
        registry.apply(pd.DataFrame({"a": [1.0]}), ["x"])


GOLDEN_EVENT_DATES = {
    ("ramadan", "2025-03-01"), ("eid_al_fitr", "2025-03-30"), ("eid_al_adha", "2025-06-06"),
    ("ramadan", "2026-02-18"), ("eid_al_fitr", "2026-03-20"), ("eid_al_adha", "2026-05-27"),
    ("islamic_new_year", "2025-06-27"), ("prophets_birthday", "2025-09-05"), ("national_day", "2025-12-02"),
    ("f1_grand_prix", "2024-12-08"), ("f1_grand_prix", "2025-12-07"), ("f1_grand_prix", "2026-12-06"),
    ("adipec", "2025-11-03"), ("christmas_new_year", "2025-12-25"), ("international_shock_2022", "2022-01-09"),
}


def test_event_registry_matches_golden_dates_and_is_consistent():
    calendar = load_event_calendar()
    anchors = set(zip(calendar["event"], calendar["anchor_date"].dt.strftime("%Y-%m-%d")))
    assert GOLDEN_EVENT_DATES <= anchors
    assert set(DEFAULT_KERNEL_EVENTS) <= set(calendar["event"])
    for event, rows in calendar.groupby("event"):
        rows = rows.sort_values("anchor_date")
        assert (rows["window_start"].iloc[1:].to_numpy() > rows["window_end"].iloc[:-1].to_numpy()).all(), event
    assert {("national_day", "2025-12-02"), ("christmas_new_year", "2025-12-25"), ("ramadan", "2026-02-18")} <= anchors
    # Eid al-Fitr must not share a day with Ramadan, or the two kernels are not identifiable.
    ramadan, fitr = calendar[calendar["event"] == "ramadan"], calendar[calendar["event"] == "eid_al_fitr"]
    for start, end in zip(fitr["window_start"], fitr["window_end"]):
        assert not ((ramadan["window_start"] <= end) & (ramadan["window_end"] >= start)).any()


def test_event_offsets_on_the_daily_panel(daily_panel: pd.DataFrame):
    domestic = daily_panel[daily_panel["market"] == "DOMESTIC"]
    offsets = PANEL_FEATURES.apply(domestic, ["event_day_offsets"], anchor="date").set_index("date")
    ramadan = offsets[offset_column("ramadan")]
    assert ramadan.loc["2026-02-18"] == 0 and ramadan.loc["2026-02-13"] == -5 and np.isnan(ramadan.loc["2026-02-12"])
    assert offsets.loc["2025-12-02", offset_column("national_day")] == 0


def test_one_off_periods_are_flagged_and_masked_from_training():
    shock = load_event_calendar().query("kind == 'one_off'").iloc[0]
    assert shock["scope"] == "international"
    frame = _synthetic(season=0.0, event=0.0, noise=0.0, market="UNITED KINGDOM")
    frame["date"] = pd.date_range("2022-01-01", periods=len(frame), freq="D")
    window = (frame["date"] >= shock["window_start"]) & (frame["date"] <= shock["window_end"])
    frame.loc[window, "guests"] *= np.exp(-0.35)
    masked = AdditiveLogModel([LinearTrend()], fitter=JointLinear(), exclude_flag="is_one_off_period").fit(frame)
    unmasked = AdditiveLogModel([LinearTrend()], fitter=JointLinear()).fit(frame)
    assert masked.explain()["UNITED KINGDOM"]["trend"]["slope_per_year"] == pytest.approx(0.05, abs=1e-9)
    assert unmasked.explain()["UNITED KINGDOM"]["trend"]["slope_per_year"] != pytest.approx(0.05, abs=1e-3)
    both = pd.concat([frame, frame.assign(market="DOMESTIC")], ignore_index=True)
    flags = PANEL_FEATURES.apply(both[["date", "market"]], ["is_one_off_period"], anchor="date")["is_one_off_period"]
    assert flags[both["market"] == "UNITED KINGDOM"].sum() == 28 and flags[both["market"] == "DOMESTIC"].sum() == 0
