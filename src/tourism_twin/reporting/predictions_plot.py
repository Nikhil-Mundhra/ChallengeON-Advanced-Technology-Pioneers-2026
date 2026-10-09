"""Small multiples of daily guests per market: recent training actuals and test predictions with
their interval band."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from tourism_twin.reporting.palette import BLUE, MUTED, NAVY  # noqa: E402


def plot_test_predictions(train: pd.DataFrame, market_daily: pd.DataFrame, out_path: Path, history_days: int = 365) -> Path:
    markets = sorted(market_daily["market"].unique())
    columns = 4
    rows = -(-len(markets) // columns)
    fig, axes = plt.subplots(rows, columns, figsize=(4.2 * columns, 2.4 * rows), sharex=True)
    start = market_daily["date"].min() - pd.Timedelta(days=history_days)
    for ax, market in zip(axes.flat, markets):
        actual = train[(train["market"] == market) & (train["date"] >= start)]
        forecast = market_daily[market_daily["market"] == market]
        ax.plot(actual["date"], actual["guests"], color=MUTED, linewidth=0.7, label="train actual")
        ax.plot(forecast["date"], forecast["pred"], color=NAVY, linewidth=0.9, label="test prediction")
        if forecast["lower"].notna().all():
            ax.fill_between(forecast["date"], forecast["lower"], forecast["upper"], color=BLUE, alpha=0.2, linewidth=0, label="80% interval")
        ax.set_title(market.title(), fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(markets):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=7, loc="upper left")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
