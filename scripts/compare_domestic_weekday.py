"""Domestic nowcast: weekday x season vs plain weekday, and sensitivity to the backfitting cap.

Daily WAPE of the DOMESTIC series, mean over 13 monthly origins (2024-02-01 to 2025-02-01,
6-month horizon) and on the Aug-Jan fold (origin 2024-08-01). With tol=0 every fit runs to the
cap, so equal rows across caps show the result does not depend on it (issue #13).
These origins include the 8 published ones, so this choice is not independent of the reported
back-test; the simpler spec was kept because the difference is under the 0.3 pp gate.

    .venv/bin/python scripts/compare_domestic_weekday.py [--caps 20,50,200,1000]
"""

from __future__ import annotations

import argparse

from tourism_twin.data.daily_panel import build_daily_panel
from tourism_twin.models.backtest import RollingOrigin, backtest
from tourism_twin.models.components import AnnualFourier, ArrivalsConvolution, CentredSlope, DayOfWeek
from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.fitters import Backfitting

SPLITS = {"rolling_13": RollingOrigin("2024-02-01", "2025-02-01", 6), "aug_jan": RollingOrigin("2024-08-01", "2024-08-01", 6)}


def spec(by_season: bool, cap: int):
    return lambda: AdditiveLogModel(
        [ArrivalsConvolution(max_lag=21), CentredSlope(), AnnualFourier(4), DayOfWeek(by_season=by_season)],
        fitter=Backfitting(max_iter=cap, tol=0.0), exclude_flag="is_one_off_period", include_flag="lag_complete")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--caps", default="20,50,200,1000")
    caps = [int(c) for c in parser.parse_args().caps.split(",")]
    domestic = build_daily_panel().query("market == 'DOMESTIC'")
    print(f"{'weekday':<8} {'cap':>5} " + " ".join(f"{name:>12}" for name in SPLITS) + "  min prediction")
    for by_season in (True, False):
        for cap in caps:
            cells, lowest = [], float("inf")
            for splitter in SPLITS.values():
                predictions = backtest({"domestic": spec(by_season, cap)}, domestic, splitter).predictions
                wape = predictions.groupby("fold")[["pred", "actual"]].apply(
                    lambda g: (g["pred"] - g["actual"]).abs().sum() / g["actual"].sum() * 100).mean()
                cells.append(f"{wape:12.2f}")
                lowest = min(lowest, float(predictions["pred"].min()))
            print(f"{'season' if by_season else 'plain':<8} {cap:>5} " + " ".join(cells) + f"  {lowest:,.0f}")


if __name__ == "__main__":
    main()
