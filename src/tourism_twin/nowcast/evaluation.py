"""Nowcast evaluations on rolling origins, segment by segment (domestic and international are
never pooled): the block ablation of docs/model_design.md §3.1."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.models.backtest import RollingOrigin, backtest, segment_of
from tourism_twin.nowcast.specs import BLOCK_ABLATION, DAILY_SPECS

ABLATION_ORIGINS = RollingOrigin("2024-02-01", "2025-02-01", horizon_months=6)


def segment_wape(predictions: pd.DataFrame) -> pd.DataFrame:
    """Mean over folds of WAPE (%) on daily totals, per model and segment."""
    totals = (predictions.assign(segment=segment_of(predictions["market"]))
              .groupby(["model", "segment", "fold", "date"])[["pred", "actual"]].sum())
    wape = totals.groupby(["model", "segment", "fold"]).apply(
        lambda g: (g["pred"] - g["actual"]).abs().sum() / g["actual"].sum() * 100)
    return wape.groupby(["model", "segment"]).mean().unstack("segment")


def block_ablation(panel: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """WAPE on daily totals for each block combination in BLOCK_ABLATION, 13 rolling origins."""
    panel = build_daily_panel() if panel is None else panel
    result = backtest({name: DAILY_SPECS[name] for name in BLOCK_ABLATION}, panel, ABLATION_ORIGINS)
    table = segment_wape(result.predictions).reindex(list(BLOCK_ABLATION))
    return {
        "origins": f"{len(result.predictions['fold'].unique())} monthly, 2024-02-01..2025-02-01, 6-month horizon",
        "metric": "WAPE % of daily segment totals, mean over folds",
        "wape": table.astype(float).round(2).to_dict("index"),
        "non_converged_fits": int(result.diagnostics["non_converged"].sum()) if len(result.diagnostics) else 0,
    }
