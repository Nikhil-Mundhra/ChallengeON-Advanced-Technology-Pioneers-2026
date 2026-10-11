"""Weekly market series (seats, P2P, new arrivals, guests) and a time-only decomposition of each:
trend = centred 13-week mean of log, season = week-of-year mean of the detrended log, residual = the rest."""
import numpy as np, pandas as pd, duckdb
from tourism_twin.data.daily_panel import daily_seats
from pathlib import Path
from tourism_twin.config import SETTINGS
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
L = SETTINGS.lake_dir / "curated" / "daily_market_panel.parquet"
g=duckdb.connect().execute(f"select market,date,guests,new_arrivals_filled arrivals from '{L}' where dataset_split='train'").df()
g["date"]=pd.to_datetime(g.date); s=daily_seats(); s["date"]=pd.to_datetime(s.date)
d=g.merge(s,on=["market","date"],how="left"); d=d[d.date>="2023-01-01"]
d["week"]=d.date.dt.to_period("W-SUN").dt.start_time
w=d.groupby(["market","week"]).agg(guests=("guests","sum"),arrivals=("arrivals","sum"),seats=("seats","sum"),p2p=("p2p","sum"),n=("date","size")).reset_index()
w=w[w.n==7].drop(columns="n"); w=w[w.market!="DOMESTIC"]
# time-only decomposition per market and series, on logs: trend = centred 13-week mean, season = week-of-year mean of detrended
out=[]
for m,u in w.groupby("market"):
    u=u.sort_values("week").copy()
    for c in ["guests","arrivals","seats","p2p"]:
        y=np.log(u[c].clip(lower=1)); tr=y.rolling(13,center=True,min_periods=13).mean()
        u[c+"_trend"]=tr; de=y-tr; woy=u.week.dt.isocalendar().week.astype(int)
        se=de.groupby(woy).transform("mean"); u[c+"_season"]=se; u[c+"_res"]=de-se; u[c+"_log"]=y
    out.append(u)
w=pd.concat(out); w.to_pickle(OUT / "weekly.pkl"); print(w.shape, w.market.nunique())
