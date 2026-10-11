"""Step 1(d): does the shipped chain's link 1 leave a seasonal seat response in its residual?

CHAIN_SPECS["seat_chain"] is fitted on every guest day up to CUT. On complete market-weeks:
seat deviation ds = log(seats / centred 13-week seat mean); actual = the same for observed arrivals;
model = the same for link 1's in-sample arrivals; residual = log(observed / link-1 arrivals).
By season and month, the slope of each on ds. actual = model + residual exactly, so the residual
slope is the seat response the chain misses (positive: it responds too little in that season).

    python experiment/seasonal_link/chain_residual.py      (one chain fit, about 10 minutes)
"""

from __future__ import annotations

import pickle
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import data  # noqa: E402
import slopes  # noqa: E402
from tourism_twin.domain.seasons import SEASONS, assign_season  # noqa: E402
from tourism_twin.planning.specs import CHAIN_SPECS  # noqa: E402

FIT = data.OUT / "chain_full.pkl"


def fitted():
    if FIT.exists():
        with open(FIT, "rb") as handle:
            return pickle.load(handle)
    frame = data.daily()
    model = CHAIN_SPECS["seat_chain"].build().fit(frame[frame["guests"].notna()])
    with open(FIT, "wb") as handle:
        pickle.dump(model, handle)
    return model


def weekly_frame(model) -> pd.DataFrame:
    frame = data.daily()
    link1 = model.predict_frame(frame)["arrivals"]
    keyed = frame[["market", "date", "seats", "new_arrivals_filled"]].assign(link1=link1.to_numpy())
    week = data.weekly_sums(keyed, ["seats", "new_arrivals_filled", "link1"]).sort_values(["market", "week_start"]).reset_index(drop=True)
    for column in ("seats", "new_arrivals_filled", "link1"):
        week[f"{column}_trend"] = data.centred_trend(week, column)
    week = week[(week[["seats", "seats_trend", "new_arrivals_filled", "new_arrivals_filled_trend", "link1", "link1_trend"]] > 0).all(axis=1)]
    mid = week["week_start"] + pd.Timedelta(days=3)
    week = week.assign(month=mid.dt.month, season=mid.dt.month.map(assign_season), lunar=data.lunar_weeks(week["week_start"]),
                       ds=np.log(week["seats"] / week["seats_trend"]),
                       actual=np.log(week["new_arrivals_filled"] / week["new_arrivals_filled_trend"]),
                       model=np.log(week["link1"] / week["link1_trend"]),
                       residual=np.log(week["new_arrivals_filled"] / week["link1"]))
    return week[week["ds"].abs() < 1]


def tables(week: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group in ("season", "month"):
        for target in ("actual", "model", "residual"):
            t = slopes.by_group(week, "ds", target, group).rename(columns={group: "group"})
            rows.append(t.assign(by=group, target=target))
        t = slopes.by_group(week[~week["lunar"]], "ds", "residual", group).rename(columns={group: "group"})
        rows.append(t.assign(by=group, target="residual, no lunar weeks"))
    return pd.concat(rows, ignore_index=True)


def chart(table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(17, 5.5), gridspec_kw={"width_ratios": [2.2, 1]})
    colours = {"actual": "#e76f51", "model": "#457b9d", "residual": "k", "residual, no lunar weeks": "#999"}
    for i, (target, colour) in enumerate(colours.items()):
        shift = (i - 1.5) * 0.12
        t = table[(table["by"] == "month") & (table["target"] == target)].sort_values("group")
        ax[0].errorbar(t["group"].astype(int) + shift, t["slope"], yerr=[t["slope"] - t["low"], t["high"] - t["slope"]], fmt="o-",
                       capsize=3, color=colour, label=target)
        t = table[(table["by"] == "season") & (table["target"] == target)].set_index("group").loc[SEASONS]
        ax[1].errorbar(np.arange(4) + shift, t["slope"], yerr=[t["slope"] - t["low"], t["high"] - t["slope"]], fmt="o",
                       capsize=3, color=colour, label=target)
    ax[0].set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax[0].set_ylabel("slope on weekly seat deviation from its 13-week trend (90%)")
    ax[0].set_title("Chain link 1 in sample (fit to 2025-01-31): arrivals deviation = model + residual")
    ax[1].set_xticks(range(4), [s.replace("_", "\n") for s in SEASONS])
    ax[1].set_title("By project season")
    for a in ax:
        a.axhline(0, color="k", lw=0.5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(data.OUT / "4_chain_residual.png", dpi=95)


def main() -> None:
    warnings.filterwarnings("ignore")
    data.OUT.mkdir(exist_ok=True)
    week = weekly_frame(fitted())
    table = tables(week)
    table.to_csv(data.OUT / "step1_chain_residual.csv", index=False)
    chart(table)
    c = slopes.contrast(week, "ds", "residual", "month", list(range(1, 7)), list(range(7, 13)))
    print(table.round(3).to_string(index=False))
    print("residual slope Jan-Jun minus Jul-Dec", {k: round(v, 3) for k, v in c.items()}, "weeks", len(week))


if __name__ == "__main__":
    main()
