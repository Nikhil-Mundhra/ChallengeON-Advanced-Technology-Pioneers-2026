import { marketName } from "../../content/labels";
import { useState } from "react";
import { Badge, Card, Segmented, Select } from "../../components/ui";
import { formatCount, formatDate, formatMonth, formatSigned, toneOf } from "../../data/format";
import { periodAt, summarise, type PeriodMode } from "../../engine/periods";
import type { Playback } from "../../engine/playback";
import { ALL_MARKETS } from "./levers";

const MODES = [{ value: "week", label: "Week" }, { value: "month", label: "Month" }, { value: "year", label: "Year" }, { value: "since", label: "Since…" }] as const;
const DATA_LABEL = { real: "real", forecast: "forecast", mixed: "real and forecast" } as const;

/** Right panel: totals for the period around the week on the map (it follows playback), and
 *  where those visitors come from. */
export function ResultsPanel({ pb, week, market }: { pb: Playback; week: number; market: string }) {
  const [mode, setMode] = useState<PeriodMode>("month");
  const [since, setSince] = useState(() => Math.max(0, pb.weeks.findIndex((w) => w >= "2025-01-01")));
  const known = market !== ALL_MARKETS && Boolean(pb.markets[market]);
  const markets = known ? [market] : undefined;   // a country without hotel history: show all markets
  const period = periodAt(pb.weeks, week, mode, since);
  const sum = summarise(pb, period, markets);
  const world = summarise(pb, period);
  const added = sum.visitors - sum.visitorsBase;
  const top = world.byMarket.filter((m) => m.market !== "DOMESTIC").slice(0, 8);
  const max = top[0]?.visitors || 1;
  const sinceOptions = pb.weeks.map((w, i) => ({ w, i })).filter(({ w }) => w.slice(8, 10) <= "07").map(({ w, i }) => ({ value: String(i), label: formatMonth(w) }));
  const label = mode === "week" ? `Week of ${formatDate(period.first)}`
    : mode === "month" ? formatMonth(period.first)
    : mode === "year" ? period.first.slice(0, 4)
    : `${formatMonth(period.first)} to ${formatDate(period.last)}`;
  return (
    <>
      <Card title="Totals" subtitle={label} actions={<Badge tone="neutral">{DATA_LABEL[sum.data]}</Badge>}>
        <Segmented label="Period" value={mode} onChange={setMode} options={MODES} />
        {mode === "since" && <Select label="Since" value={String(since)} onChange={(v) => setSince(Number(v))} options={sinceOptions} />}
        <dl className="totals">
          <div><dt>Visitors arriving</dt><dd>{formatCount(sum.visitors)}</dd></div>
          <div><dt>Hotel nights</dt><dd>{formatCount(sum.guests)}</dd></div>
          {Math.abs(added) >= 1 && <div><dt>From your changes</dt><dd className={toneOf(added)}>{formatSigned(added, formatCount)} visitors</dd></div>}
        </dl>
        {!sum.covered && <p className="note">Only part of this period has data, so the totals cover the weeks we have.</p>}
        <p className="note">{known || market === ALL_MARKETS ? marketName(market) : `All markets (${marketName(market)} has no hotel history yet)`}. Follows the week on the map; press play and it moves.</p>
      </Card>
      <Card title="Where visitors come from" subtitle={`Same period, all markets (countries and regions)`}>
        <ul className="origins">
          {top.map((m) => (
            <li key={m.market} className={m.market === market ? "origins__row origins__row--selected" : "origins__row"}>
              <span className="origins__name">{marketName(m.market)}</span>
              <span className="origins__bar"><span style={{ width: `${(m.visitors / max) * 100}%` }} /></span>
              <span className="origins__value">{formatCount(m.visitors)}</span>
            </li>
          ))}
        </ul>
        <p className="note">Nationality detail is on the Daily forecast page (Aug 2025 to Feb 2026).</p>
      </Card>
    </>
  );
}
