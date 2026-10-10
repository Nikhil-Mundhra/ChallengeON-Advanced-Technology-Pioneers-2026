import { useMemo } from "react";
import { Timeline } from "../../components/charts/Timeline";
import { Card, Select, Slider } from "../../components/ui";
import { formatCount, formatFull, formatPercent } from "../../data/format";
import type { Lever, Planning } from "../../engine/planning";
import { holdoutWmape, timeline, type Weekly, type WeekPoint } from "../../engine/weekly";

interface TimelineCardProps {
  planning: Planning;
  weekly: Weekly;
  market: string;
  lever: Lever;
  start: string;
  growthPct: number;
  onStart: (week: string) => void;
  onGrowth: (pct: number) => void;
}

/** Back-test and multi-year projection for one market, with the scenario from a chosen week. */
export function TimelineCard({ planning, weekly, market, lever, start, growthPct, onStart, onGrowth }: TimelineCardProps) {
  const series = weekly.markets[market];
  const points = useMemo(() => timeline(planning, weekly, market, lever, { start, growthPct }), [planning, weekly, market, lever, start, growthPct]);
  if (!series) {
    return <Card title="Back-test and projection"><p className="simulate__note">No weekly history for this market (cold start): only the season-level scenario above applies.</p></Card>;
  }
  const holdoutWeeks = points.filter((p) => p.holdout !== null).map((p) => p.week);
  const projectedFrom = points.find((p) => p.kind === "projected")?.week ?? null;
  const starts = points.filter((p) => p.week > weekly.last_actual_week && Number(p.week.slice(5, 7)) % 3 === 1 && Number(p.week.slice(8, 10)) <= 7);
  const wmape = holdoutWmape(points);

  return (
    <Card title="Back-test and projection"
          subtitle={`Weekly guests: actual, back-test fitted before ${weekly.holdout_start} (WMAPE ${wmape === null ? "n/a" : wmape.toFixed(1) + "%"} for this market), and ${years(points)} years ahead`}>
      <div className="timeline__controls">
        <label className="timeline__field"><span>Scenario starts</span>
          <Select label="Scenario start week" value={start} onChange={onStart}
                  options={[{ value: weekly.last_actual_week, label: `${weekly.last_actual_week} (after last actual)` }, ...starts.map((p) => ({ value: p.week, label: p.week }))]} />
        </label>
        <div className="timeline__field timeline__growth">
          <Slider label="Market growth assumption (not fitted)" value={growthPct} min={-5} max={10} step={0.5}
                  format={(v) => `${v > 0 ? "+" : ""}${v}%/yr`} onChange={onGrowth} />
        </div>
      </div>
      <Timeline data={points} holdout={[holdoutWeeks[0] ?? weekly.holdout_start, holdoutWeeks[holdoutWeeks.length - 1] ?? weekly.holdout_start]}
                projectedFrom={projectedFrom} scenarioFrom={start} />
      <YearTable points={points} />
      <p className="simulate__note">
        The weekly model has no growth term: projected years repeat the fitted seasonal profile at the calibrated seasonal seats, scaled only by the growth assumption you set.
        Holiday and event-week flags exist up to {weekly.calendar_flags_until}; later weeks carry no holiday effect.
      </p>
    </Card>
  );
}

function years(points: WeekPoint[]) {
  const projected = points.filter((p) => p.kind === "projected");
  return projected.length ? Math.round(projected.length / 52) : 0;
}

function YearTable({ points }: { points: WeekPoint[] }) {
  const rows = useMemo(() => {
    const byYear = new Map<string, { model: number; scenario: number; weeks: number }>();
    for (const p of points) {
      if (p.scenario === null) continue;
      const year = p.week.slice(0, 4);
      const row = byYear.get(year) ?? { model: 0, scenario: 0, weeks: 0 };
      row.model += p.model; row.scenario += p.scenario; row.weeks += 1;
      byYear.set(year, row);
    }
    return [...byYear.entries()];
  }, [points]);
  if (!rows.length) return null;
  return (
    <table className="chain">
      <caption className="visually-hidden">Guests per year in the scenario window</caption>
      <thead><tr><th scope="col">Year (scenario weeks)</th><th scope="col">Current service</th><th scope="col">Scenario</th><th scope="col">Change</th></tr></thead>
      <tbody>
        {rows.map(([year, r]) => (
          <tr key={year}>
            <th scope="row">{year} ({r.weeks} wk)</th>
            <td>{formatFull(r.model)}</td>
            <td>{formatFull(r.scenario)}</td>
            <td className={r.scenario >= r.model ? "up" : "down"}>{r.scenario >= r.model ? "+" : ""}{formatCount(r.scenario - r.model)} ({formatPercent(r.model > 0 ? r.scenario / r.model - 1 : 0)})</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
