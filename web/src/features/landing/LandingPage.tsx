import { marketName } from "../../content/labels";
import { useMemo } from "react";
import { Link } from "react-router";
import { useActiveId, useReveal } from "../../components/layout/useInView";
import { CHAPTERS, DAILY_ERROR, OUTLOOK_BACKTEST_YEARS, SCENARIO_ASSUMPTION } from "../../content/landing";
import { formatMonthName, formatPercent, formatRounded } from "../../data/format";
import { marketMoves } from "../../engine/insights";
import { comingRows, outlookRows, rawProjection, scenarioOf, type OutlookRow } from "../../engine/outlook";
import type { Bundle } from "../../engine/types";
import { holdoutCoverage } from "../../engine/planning";
import { overallHoldoutWmape } from "../../engine/weekly";
import { QuestionAnswers } from "../questions/QuestionAnswers";
import "./landing.css";

const IDS = CHAPTERS.map((c) => c.id);
const pct = (v: number) => `${Math.round(Math.abs(v) * 1000) / 10}%`;
const monthYear = (iso: string) => `${formatMonthName(iso)} ${iso.slice(0, 4)}`;
const yearBefore = (month: string) => `${Number(month.slice(0, 4)) - 1}${month.slice(4)}`;

/** The front page: what to expect, in plain sentences, each backed by one big number. Forward months
 *  come from the bundle's outlook; until the bundle has one, the page says the forecast is being prepared. */
export function LandingPage({ bundle }: { bundle: Bundle }) {
  const { nowcast, planning, weekly, manifest, outlook } = bundle;
  const today = new Date().toISOString().slice(0, 10);
  const data = useMemo(() => {
    const moves = marketMoves(nowcast, manifest.coverage).filter((m) => m.market !== "DOMESTIC");
    return {
      risers: moves.slice(0, 5), fallers: moves.slice(-3).reverse(),
      weeklyError: overallHoldoutWmape(planning, weekly), weeklyCoverage: holdoutCoverage(planning),
    };
  }, [nowcast, planning, weekly, manifest]);
  const forecast = useMemo(() => {
    if (!outlook) return null;
    const scenario = scenarioOf(outlook);
    const total = comingRows(outlookRows(outlook, "TOTAL", scenario), today);
    if (!total.length) return null;
    return {
      scenario, dataEnd: outlook.data_end, total,
      international: rawProjection(outlook, "INTERNATIONAL", scenario),
      residents: rawProjection(outlook, "DOMESTIC", scenario),
    };
  }, [outlook, today]);
  const active = useActiveId(IDS);
  useReveal([data, forecast]);
  const lead = forecast?.total[0] ?? null;
  const assumption = (scenario: string) => SCENARIO_ASSUMPTION[scenario] ?? `the "${scenario}" arrivals scenario`;

  return (
    <div className="landing">
      <section className="hero">
        <div className="hero__inner">
          {forecast && lead ? (
            <>
              <p className="hero__eyebrow reveal">Abu Dhabi hotels · forecast to {monthYear(forecast.total[forecast.total.length - 1].month)}</p>
              <p className="hero__number reveal">{lead.change === null ? formatRounded(lead.guests) : lead.trend === "same" ? "About the same" : formatPercent(lead.change, 0)}</p>
              <h1 className="hero__sentence reveal">
                {monthYear(lead.month)}: about {formatRounded(lead.guests)} hotel nights
                {lead.change !== null && `, ${formatPercent(lead.change, 0)} on ${monthYear(yearBefore(lead.month))}${lead.previousKind === "estimate" ? " (model estimate)" : ""}`}.
              </h1>
              <p className="hero__caption reveal">
                {lead.low !== null && lead.high !== null && `Range ${formatRounded(lead.low)} to ${formatRounded(lead.high)}. `}
                Projected from {assumption(forecast.scenario)}
                {lead.calibrated && lead.band
                  ? `, then corrected by how this projection missed in ${lead.band.n ?? "past"} back-tests at the same distance, all from the ${OUTLOOK_BACKTEST_YEARS} growth period. `
                  : ". "}
                Data ends {monthYear(forecast.dataEnd)}.
              </p>
            </>
          ) : (
            <>
              <p className="hero__eyebrow reveal">Abu Dhabi hotels · forecast</p>
              <h1 className="hero__sentence reveal">The forecast for the coming months is being prepared.</h1>
              <p className="hero__caption reveal">Model estimates up to {monthYear(manifest.predicted_period.end)} are on the daily forecast page.</p>
            </>
          )}
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
        {forecast ? (
          <>
            <div className="months">
              {forecast.total.map((m, i) => (
                <MonthCard key={m.month} total={m} showChange={i > 0}
                           international={forecast.international.find((r) => r.month === m.month)} residents={forecast.residents.find((r) => r.month === m.month)} />
              ))}
            </div>
            <p className="chapter__note reveal">
              Projected hotel nights for each month from {assumption(forecast.scenario)}, against the same month a year earlier (real guests where the data has them, otherwise the model's estimate). A change inside the range is shown as "same". The total is corrected by past back-test misses from {OUTLOOK_BACKTEST_YEARS}, a growth period. The international and resident lines are the uncorrected projection. Events after {monthYear(forecast.dataEnd)} are not in the data.
            </p>
          </>
        ) : (
          <p className="chapter__note reveal">The month-by-month forecast is being prepared.</p>
        )}
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
        <p className="chapter__note reveal">Estimated hotel nights from each market, {monthYear(manifest.predicted_period.start)} to {monthYear(manifest.predicted_period.end)}, against the same months a year earlier.</p>
      </Chapter>

      <Chapter index={2}>
        <QuestionAnswers planning={planning} weekly={weekly} />
      </Chapter>

      <Chapter index={3}>
        <div className="trust">
          <Fact value={`±${Math.round((DAILY_ERROR.domestic + DAILY_ERROR.international) / 2)}%`} text="typical miss on one day's total of UAE residents, or of visitors, when that day's hotel check-ins are known. Checked on months the model had not seen." />
          {lead?.band && <Fact value={`${formatPercent(lead.band.low, 0)} to ${formatPercent(lead.band.high, 0)}`} text={`how far real months came out from the raw projection in back-tests ${lead.band.horizon_months} months past the end of the data. The month cards correct by the middle of this range.`} />}
          {data.weeklyError !== null && <Fact value={`±${Math.round(data.weeklyError)}%`} text={`typical miss on one market's weekly hotel nights in the flight scenario model, checked on 30 weeks (December 2024 to July 2025) the model had not seen.${data.weeklyCoverage === null ? "" : ` Its ranges held the real week ${Math.round(data.weeklyCoverage)}% of the time, against the 80% they aim for.`}`} />}
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
function Trend({ label, o }: { label: string; o?: Pick<OutlookRow, "trend" | "change"> }) {
  if (!o || o.trend === null || o.change === null) return null;
  return (
    <li className={`month__line month__line--${o.trend}`}>
      <span>{label}</span>
      <span>{ARROW[o.trend]} {o.trend === "same" ? "same" : pct(o.change)}</span>
    </li>
  );
}

/** A forward month: the corrected total with its range; the segment lines are the uncorrected projection.
 *  The lead month's change is in the hero, so its card leaves it out (`showChange`). */
function MonthCard({ total, international, residents, showChange }: { total: OutlookRow; international?: { guests: number }; residents?: { guests: number }; showChange: boolean }) {
  return (
    <article className="month reveal">
      <h3 className="month__name">{formatMonthName(total.month)} <span>{total.month.slice(0, 4)}</span></h3>
      <p className="month__total">{formatRounded(total.guests)}<span> hotel nights</span></p>
      <ul className="month__lines">
        {total.low !== null && total.high !== null && (
          <li className="month__line"><span>Range</span><span>{formatRounded(total.low)} to {formatRounded(total.high)}</span></li>
        )}
        {showChange && <Trend label="Vs a year earlier" o={total} />}
        {international && <li className="month__line"><span>International (uncorrected)</span><span>{formatRounded(international.guests)}</span></li>}
        {residents && <li className="month__line"><span>UAE residents (uncorrected)</span><span>{formatRounded(residents.guests)}</span></li>}
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
