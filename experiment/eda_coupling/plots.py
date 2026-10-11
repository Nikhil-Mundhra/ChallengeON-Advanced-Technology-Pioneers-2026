"""Coupling charts: raw series, time share of variance, residual coupling per link, lead/lag and trend vs trend."""
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
OUT = Path(__file__).parent / "out"
w=pd.read_pickle(OUT / "weekly.pkl"); S=["seats","p2p","arrivals","guests"]; C={"seats":"#8ab","p2p":"#2a9d8f","arrivals":"#e9c46a","guests":"#e76f51"}
M=["UNITED KINGDOM","INDIA","CHINA","GERMANY","SAUDI ARABIA","RUSSIAN FEDERATION"]
# FIG 1 raw coupling
fig,ax=plt.subplots(2,3,figsize=(19,8),sharex=True)
for a,m in zip(ax.flat,M):
    u=w[w.market==m]
    for c in S: a.plot(u.week,u[c]/u[c].mean(),color=C[c],lw=1.3,label=c)
    a.set_title(m); a.grid(alpha=.3)
ax[0,0].legend(); fig.suptitle("Step 1. Raw weekly series, each divided by its own mean (2023-01 to 2025-07)"); plt.tight_layout(); plt.savefig(OUT / "1_raw.png",dpi=95)
# FIG 2 how much is time
rows=[]
for m,u in w.groupby("market"):
    u=u.dropna(subset=[f"{c}_trend" for c in S])
    for c in S:
        y=u[c+"_log"]-u[c+"_log"].mean(); tv=np.var(y)
        rows.append(dict(market=m,series=c,trend=np.var(u[c+"_trend"]-u[c+"_trend"].mean())/tv,season=np.var(u[c+"_season"])/tv,res=np.var(u[c+"_res"])/tv))
v=pd.DataFrame(rows); v["time"]=1-v.res
fig,ax=plt.subplots(1,2,figsize=(19,6),gridspec_kw={"width_ratios":[2.2,1]})
a=ax[0]; mk=v[v.series=="guests"].sort_values("time").market.tolist(); x=np.arange(len(mk))
for i,c in enumerate(S):
    t=v[v.series==c].set_index("market").loc[mk]; a.bar(x+(i-1.5)*.2,t.time,.2,color=C[c],label=c)
a.set_xticks(x,[m[:14] for m in mk],rotation=60,fontsize=8); a.set_ylabel("share of variance explained by time (trend + season)"); a.axhline(.7,ls=":",color="k"); a.legend(); a.set_title("Step 2. How much of each series is just time")
a=ax[1]; t=v.groupby("series")[["trend","season","res"]].median().loc[S]
t.plot.bar(stacked=True,ax=a,color=["#264653","#2a9d8f","#ddd"]); a.set_title("Median over markets"); a.set_ylabel("share of variance"); a.tick_params(axis="x",rotation=0)
plt.tight_layout(); plt.savefig(OUT / "2_time_share.png",dpi=95)
# FIG 3 residual coupling and trend coupling
r=w.dropna(subset=[f"{c}_res" for c in S]); r=r[(r.seats_res.abs()<1)&(r.guests_res.abs()<1)]
fig,ax=plt.subplots(1,4,figsize=(21,5))
for a,(xc,yc) in zip(ax[:3],[("seats","p2p"),("p2p","arrivals"),("arrivals","guests")]):
    X=r[xc+"_res"];Y=r[yc+"_res"]; a.hexbin(X,Y,gridsize=40,bins="log",cmap="Blues",mincnt=1)
    k=np.polyfit(X,Y,1); xs=np.linspace(X.quantile(.01),X.quantile(.99),10); a.plot(xs,np.polyval(k,xs),"r-")
    a.set_title(f"{xc} → {yc} (time removed)\nslope {k[0]:.2f}, corr {np.corrcoef(X,Y)[0,1]:.2f}, n={len(X)}"); a.set_xlabel(f"{xc} residual (log)"); a.set_ylabel(f"{yc} residual (log)"); a.axhline(0,lw=.4,color="k"); a.axvline(0,lw=.4,color="k")
a=ax[3]; X=r.seats_res;Y=r.guests_res; a.hexbin(X,Y,gridsize=40,bins="log",cmap="Oranges",mincnt=1); k=np.polyfit(X,Y,1); xs=np.linspace(X.quantile(.01),X.quantile(.99),10); a.plot(xs,np.polyval(k,xs),"r-")
a.set_title(f"seats → guests directly (time removed)\nslope {k[0]:.2f}, corr {np.corrcoef(X,Y)[0,1]:.2f}"); a.set_xlabel("seats residual"); a.set_ylabel("guests residual")
plt.tight_layout(); plt.savefig(OUT / "3_residual_coupling.png",dpi=95)
# FIG 4 cross-correlation of residuals, and trend coupling
lags=range(-6,7)
def ccf(xc,yc):
    out=[]
    for L in lags:
        vals=[]
        for m,u in r.groupby("market"):
            u=u.sort_values("week"); x=u[xc+"_res"].values; y=u[yc+"_res"].values
            if L>=0: a_,b_=x[:len(x)-L],y[L:]
            else: a_,b_=x[-L:],y[:len(y)+L]
            if len(a_)>20: vals.append(np.corrcoef(a_,b_)[0,1])
        out.append(np.nanmedian(vals))
    return out
fig,ax=plt.subplots(1,2,figsize=(17,5))
a=ax[0]
for xc,yc,c in [("seats","guests","#8ab"),("p2p","guests","#2a9d8f"),("arrivals","guests","#e76f51"),("seats","p2p","#264653")]:
    a.plot(list(lags),ccf(xc,yc),"o-",color=c,label=f"{xc} → {yc}")
a.axvline(0,color="k",lw=.5); a.axhline(0,color="k",lw=.5); a.set_xlabel("lag in weeks (positive: x leads y)"); a.set_ylabel("median correlation over markets"); a.legend(); a.grid(alpha=.3); a.set_title("Step 4. Lead and lag of the time-removed parts")
a=ax[1]; t=w.dropna(subset=["guests_trend","seats_trend"]).copy()
t["g52"]=t.groupby("market").guests_trend.diff(52); t["s52"]=t.groupby("market").seats_trend.diff(52); t=t.dropna(subset=["g52","s52"])
for m,u in t.groupby("market"): a.scatter(u.s52,u.g52,s=6,alpha=.5)
k=np.polyfit(t.s52,t.g52,1); xs=np.linspace(t.s52.quantile(.02),t.s52.quantile(.98),10); a.plot(xs,np.polyval(k,xs),"k-",lw=2)
a.set_xlabel("seat trend change over 52 weeks (log)"); a.set_ylabel("guest trend change over 52 weeks (log)"); a.axhline(0,lw=.4,color="k"); a.axvline(0,lw=.4,color="k")
a.set_title(f"Step 5. Trends against trends (one colour per market)\nslope {k[0]:.2f}, corr {np.corrcoef(t.s52,t.g52)[0,1]:.2f}: association, not effect")
plt.tight_layout(); plt.savefig(OUT / "4_lags_trends.png",dpi=95)
print(v.groupby("series")[["trend","season","res","time"]].median().round(2))
for xc in ["seats","p2p","arrivals"]: print(xc,"→guests ccf",np.round(ccf(xc,"guests"),2))
