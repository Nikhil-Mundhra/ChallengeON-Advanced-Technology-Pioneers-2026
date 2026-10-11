import { marketName } from "../../content/labels";
import { useMemo } from "react";
import { Link } from "react-router";
import { useActiveId, useReveal } from "../../components/layout/useInView";
import { CHAPTERS, DAILY_ERROR } from "../../content/landing";
import { formatCount, formatMonthName, formatPercent } from "../../data/format";
import { headlineMonth, marketMoves, monthlyOutlook, type MonthOutlook } from "../../engine/insights";
import type { Bundle } from "../../engine/types";
import { overallHoldoutWmape } from "../../engine/weekly";
import { NOVEMBER_2026_OUTLOOK } from "../../content/externalReports";
import { QuestionAnswers } from "../questions/QuestionAnswers";
import "./landing.css";

const IDS = CHAPTERS.map((c) => c.id);
const pct = (v: number) => `${Math.round(Math.abs(v) * 1000) / 10}%`;

/** The front page: what to expect, in plain sentences, each backed by one big number. */
export function LandingPage({ bundle }: { bundle: Bundle }) {
  const { nowcast, planning, weekly, manifest } = bundle;
  const data = useMemo(() => {
    const international = monthlyOutlook(nowcast, "INTERNATIONAL", manifest.coverage);
    const residents = monthlyOutlook(nowcast, "DOMESTIC", manifest.coverage);
    const total = monthlyOutlook(nowcast, "TOTAL", manifest.coverage);
    const moves = marketMoves(nowcast, manifest.coverage).filter((m) => m.market !== "DOMESTIC");
    return {
      international, residents, total, lead: headlineMonth(international),
      risers: moves.slice(0, 5), fallers: moves.slice(-3).reverse(),
      weeklyError: overallHoldoutWmape(planning, weekly),
    };
  }, [nowcast, planning, weekly, manifest]);
  const active = useActiveId(IDS);
  useReveal([data]);

  return (
    <div className="landing">
      <section className="hero">
        <div className="hero__inner">
          <p className="hero__eyebrow reveal">Abu Dhabi hotels · outlook to November 2026</p>
          <p className="hero__number reveal">{formatPercent(NOVEMBER_2026_OUTLOOK.changeVs2025)}</p>
          <h1 className="hero__sentence reveal">
            Hotel guests are projected to rise in Abu Dhabi hotels this November 2026 over last year's record peak.
          </h1>
          <p className="hero__caption reveal">
            ±{pct(NOVEMBER_2026_OUTLOOK.error)} error ({formatCount(NOVEMBER_2026_OUTLOOK.hotelNightsMonthly)} guest nights projected at {NOVEMBER_2026_OUTLOOK.occupancyRate}% occupancy, driven by ADIPEC and Formula 1 Grand Prix). All hotel guests together: {formatPercent(NOVEMBER_2026_OUTLOOK.changeVs2025)} ahead of November 2025 ({formatCount(NOVEMBER_2026_OUTLOOK.baseline2025Nights)} nights).
          </p>
          <div className="hero__actions reveal">
            <Link to="/simulate" className="pill pill--accent pill--lg">Try a flight scenario</Link>
            <Link to="/nowcast" className="pill pill--ghost pill--lg">See the daily forecast</Link>
          </div>
        </div>
        <span className="hero__shape" aria-hidden="true" />
      </section>

      <nav className="pager" aria-label="Chapters">
        {CHAPTERS.map((c) => (
          <a key={c.id} href={`#${c.id}`} className="pager__item" aria-current={active === c.id ? "true" : undefined} title={c.label}>{c.number}</a>
        ))}
      </nav>

      <Chapter index={0}>
        <div className="months">
          <article className="month reveal" style={{ borderColor: "var(--color-series-external)" }}>
            <h3 className="month__name">November <span>2026</span></h3>
            <p className="month__total">{formatCount(NOVEMBER_2026_OUTLOOK.hotelNightsMonthly)}<span> hotel nights</span></p>
            <ul className="month__lines">
              <li className="month__line month__line--up">
                <span>Outlook vs Nov 2025</span>
                <span>▲ {formatPercent(NOVEMBER_2026_OUTLOOK.changeVs2025)}</span>
              </li>
              <li className="month__line">
                <span>Occupancy</span>
                <span style={{ fontWeight: "var(--weight-bold)" }}>{NOVEMBER_2026_OUTLOOK.occupancyRate}%</span>
              </li>
              <li className="month__line">
                <span>Weekly run rate</span>
                <span>~{formatCount(NOVEMBER_2026_OUTLOOK.hotelNightsWeekly)}</span>
              </li>
            </ul>
          </article>
          {data.international.map((m) => (
            <MonthCard key={m.month} month={m} residents={data.residents.find((r) => r.month === m.month)} total={data.total.find((t) => t.month === m.month)} />
          ))}
        </div>
        <p className="chapter__note reveal">November 2026 projected from reported SCAD & DCT run-rates through September 2026. Months below reflect the digital twin model against the prior year baseline.</p>
      </Chapter>

      <Chapter index={1}>
        <div className="markets">
          <div className="markets__col reveal">
            <h3 className="markets__title">Growing fastest</h3>
            {data.risers.map((m) => <MarketBar key={m.market} name={m.market} change={m.change} max={data.risers[0].change} />)}
          </div>
          <div className="markets__col reveal">
            <h3 className="markets__title">Slowing down</h3>
            {data.fallers.map((m) => <MarketBar key={m.market} name={m.market} change={m.change} max={Math.abs(data.fallers[0].change)} />)}
          </div>
        </div>
        <p className="chapter__note reveal">Forecast hotel nights from each market over the coming months, against the same months a year earlier.</p>
      </Chapter>

      <Chapter index={2}>
        <QuestionAnswers planning={planning} weekly={weekly} />
      </Chapter>

      <Chapter index={3}>
        <div className="trust">
          <Fact value={`±${Math.round((DAILY_ERROR.domestic + DAILY_ERROR.international) / 2)}%`} text="typical miss on a single day's hotel guests, checked on months the model had not seen." />
          <Fact value={`±${pct(data.international[0]?.error ?? 0)}`} text="error on a whole month's total, as shown in the month cards." />
          {data.weeklyError !== null && <Fact value={`±${Math.round(data.weeklyError)}%`} text="typical miss on one market's week in flight scenarios, checked on 30 weeks the model had not seen." />}
        </div>
        <Link to="/report" className="pill pill--dark reveal">How it works</Link>
      </Chapter>

      <footer className="landing__footer">
        <p>Built for the ChallengeON ATP 2026 Department of Culture and Tourism challenge, from flight and hotel data supplied for the challenge. Estimates, not guarantees.</p>
        <p>Model {manifest.version}</p>
      </footer>
    </div>
  );
}

function Chapter({ index, children }: { index: number; children: React.ReactNode }) {
  const c = CHAPTERS[index];
  return (
    <section id={c.id} className={`chapter chapter--${index % 2 ? "right" : "left"}`} aria-labelledby={`${c.id}-title`}>
      <header className="chapter__title reveal">
        <span className="chapter__number">{c.number}</span>
        <span className="chapter__kicker">{c.kicker}</span>
        <h2 id={`${c.id}-title`}>{c.label}</h2>
      </header>
      <div className="chapter__body">{children}</div>
    </section>
  );
}

const ARROW = { up: "▲", down: "▼", same: "≈" } as const;
function Trend({ label, o }: { label: string; o?: MonthOutlook }) {
  if (!o || o.trend === null || o.change === null) return null;
  return (
    <li className={`month__line month__line--${o.trend}`}>
      <span>{label}</span>
      <span>{ARROW[o.trend]} {o.trend === "same" ? "same" : pct(o.change)}</span>
    </li>
  );
}

function MonthCard({ month, residents, total }: { month: MonthOutlook; residents?: MonthOutlook; total?: MonthOutlook }) {
  return (
    <article className="month reveal">
      <h3 className="month__name">{formatMonthName(month.month)} <span>{month.month.slice(0, 4)}</span></h3>
      <p className="month__total">{formatCount(total?.guests ?? month.guests)}<span> hotel nights</span></p>
      <ul className="month__lines">
        <Trend label="International" o={month} />
        <Trend label="UAE residents" o={residents} />
        <Trend label="All guests" o={total} />
      </ul>
    </article>
  );
}

function MarketBar({ name, change, max }: { name: string; change: number; max: number }) {
  return (
    <div className="market">
      <span className="market__name">{marketName(name)}</span>
      <span className="market__bar"><span className={change >= 0 ? "market__fill" : "market__fill market__fill--down"} style={{ width: `${Math.min(100, (Math.abs(change) / Math.abs(max)) * 100)}%` }} /></span>
      <span className="market__value">{formatPercent(change, 0)}</span>
    </div>
  );
}

function Fact({ value, text }: { value: string; text: string }) {
  return <div className="fact reveal"><p className="fact__value">{value}</p><p className="fact__text">{text}</p></div>;
}
