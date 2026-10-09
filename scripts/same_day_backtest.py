"""Same-day guests: Poisson GLM vs the market-mean baseline on rolling origins (mean deviance).

    .venv/bin/python scripts/same_day_backtest.py
"""

from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.models.backtest import RollingOrigin
from tourism_twin.nowcast.same_day import same_day_backtest

if __name__ == "__main__":
    panel = build_daily_panel().query("dataset_split == 'train'")
    result = same_day_backtest(panel, RollingOrigin("2024-07-01", "2025-02-01", 6))
    print(result.groupby(["segment", "model"])["deviance"].mean().round(2).unstack())
