"""Stability over time: per half-year slope of each link on the time-removed residuals, residual distributions by
half-year, and the level ratios (P2P per seat, arrivals per P2P, guests per arrival) per market over time."""
from pathlib import Path
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = Path(__file__).parent / "out"
w = pd.read_pickle(OUT / "weekly.pkl")
w["half"] = w.week.dt.year.astype(str) + np.where(w.week.dt.month <= 6, " H1", " H2")
r = w.dropna(subset=["seats_res", "guests_res"])
links = [("seats", "p2p"), ("p2p", "arrivals"), ("arrivals", "guests"), ("seats", "guests")]
fig, ax = plt.subplots(1, 3, figsize=(20, 5.4))
a = ax[0]; halves = sorted(r.half.unique()); rows = []
for x, y in links:
    s, lo, hi = [], [], []
    for h in halves:
        u = r[r.half == h]; X, Y = u[x + "_res"].values, u[y + "_res"].values
        b = [np.polyfit(X[i], Y[i], 1)[0] for i in [np.random.default_rng(k).integers(0, len(X), len(X)) for k in range(200)]]
        s.append(np.polyfit(X, Y, 1)[0]); lo.append(np.percentile(b, 5)); hi.append(np.percentile(b, 95))
        rows.append(dict(link=f"{x}->{y}", half=h, slope=s[-1], lo=lo[-1], hi=hi[-1], n=len(u)))
    a.errorbar(np.arange(len(halves)), s, yerr=[np.subtract(s, lo), np.subtract(hi, s)], fmt="o-", capsize=3, label=f"{x} → {y}")
a.set_xticks(range(len(halves)), halves); a.axhline(0, color="k", lw=.5); a.set_ylabel("slope on time-removed residuals (90% bootstrap)")
a.set_title("Does each link's strength change over time?"); a.legend(fontsize=8); a.grid(alpha=.3)
a = ax[1]
for h, c in zip(halves, plt.cm.viridis(np.linspace(0, 1, len(halves)))):
    u = r[r.half == h].guests_res; a.hist(u.clip(-1, 1), bins=50, density=True, histtype="step", lw=1.8, color=c, label=f"{h}: sd {u.std():.2f}")
a.set_xlabel("guest residual after time (log)"); a.set_title("Does the guest residual distribution shift?"); a.legend(fontsize=8)
a = ax[2]
q = w.groupby(["market", "half"]).agg(seats=("seats", "sum"), p2p=("p2p", "sum"), arr=("arrivals", "sum"), g=("guests", "sum")).reset_index()
q["p2p/seat"] = q.p2p / q.seats; q["arrivals/p2p"] = q.arr / q.p2p; q["guests/arrival"] = q.g / q.arr
for col, c in [("p2p/seat", "#2a9d8f"), ("arrivals/p2p", "#e9c46a"), ("guests/arrival", "#e76f51")]:
    p = q.pivot(index="half", columns="market", values=col); rel = p / p.iloc[0]
    a.plot(range(len(rel)), rel.median(axis=1), "o-", color=c, lw=2.5, label=f"{col} (median market)")
    a.fill_between(range(len(rel)), rel.quantile(.25, axis=1), rel.quantile(.75, axis=1), color=c, alpha=.15)
a.set_xticks(range(len(halves)), halves); a.axhline(1, color="k", lw=.5); a.set_ylabel("ratio vs 2023 H1 (band: middle half of markets)")
a.set_title("Do the level ratios drift?"); a.legend(fontsize=8); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig(OUT / "5_shifts.png", dpi=95)
print(pd.DataFrame(rows).round(2).to_string(index=False))
for col in ["p2p/seat", "arrivals/p2p", "guests/arrival"]:
    p = q.pivot(index="half", columns="market", values=col); print(col, (p / p.iloc[0]).median(axis=1).round(2).tolist())
