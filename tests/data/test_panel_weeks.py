"""calendar_weeks: one row per market and Monday week for forecasting and display."""

import pandas as pd

from tourism_twin.data.panel import calendar_weeks


def test_split_weeks_join_partial_edges_scale_and_tiny_weeks_drop():
    panel = pd.DataFrame({
        "market": "M", "week_start": ["2025-07-21", "2025-07-28", "2025-07-28", "2026-02-23", "2022-12-26"],
        "dataset_split": ["train", "train", "test", "test", "train"],
        "days_in_week": [7, 4, 3, 6, 1], "seats": [700.0, 400.0, 300.0, 600.0, 100.0],
    })
    weeks = calendar_weeks(panel).set_index(pd.Index(["2025-07-21", "2025-07-28", "2026-02-23"]))
    assert len(weeks) == 3                                              # the 1-day week is dropped
    assert weeks.loc["2025-07-28", "seats"] == 700.0 and weeks.loc["2025-07-28", "dataset_split"] == "test"
    assert weeks.loc["2026-02-23", "seats"] == 700.0                    # 600 seats over 6 days -> a 7-day week
    assert weeks.loc["2025-07-21", "dataset_split"] == "train"
