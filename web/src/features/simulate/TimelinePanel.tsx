import { Timeline } from "../../components/charts/Timeline";
import { Select, SliderRow } from "../../components/ui";
import { formatMonth, formatSigned } from "../../data/format";
import type { Weekly, WeekPoint } from "../../engine/weekly";

/** Past weeks with the model's check against them, and the forecast with the changes from a chosen week. */
export function TimelinePanel({ weekly, points, error, start, growthPct, onStart, onGrowth }: {
  weekly: Weekly; points: WeekPoint[]; error: number | null; start: string; growthPct: number;
  onStart: (week: string) => void; onGrowth: (pct: number) => void;
}) {
  if (!points.length) return <p className="note">No hotel history for this market yet, so only the weekly estimate applies.</p>;
  const checked = points.filter((p) => p.holdout !== null).map((p) => p.week);
  const forecastFrom = points.find((p) => p.kind === "projected")?.week ?? null;
  const starts = points.filter((p) => p.week > weekly.last_actual_week && Number(p.week.slice(5, 7)) % 3 === 1 && Number(p.week.slice(8, 10)) <= 7);
  return (
    <div className="canvas__body">
      <p className="note">
        Weekly hotel guests.{error !== null && ` Checked against ${checked.length} real weeks, the model was off by about ±${Math.round(error)}% on average.`}
      </p>
      <div className="timeline__controls">
        <div className="timeline__field">
          <span className="timeline__label">Changes start</span>
          <Select label="Week the changes start" value={start} onChange={onStart}
                  options={[{ value: weekly.last_actual_week, label: `${formatMonth(weekly.last_actual_week)} (after the latest data)` },
                            ...starts.map((p) => ({ value: p.week, label: formatMonth(p.week) }))]} />
        </div>
        <div className="timeline__field timeline__growth">
          <SliderRow label="Expected yearly growth" hint="Your assumption. Without it the forecast stays flat." value={growthPct} defaultValue={0}
                     min={-5} max={10} step={0.5} format={(v) => `${formatSigned(v, String)}% a year`} onChange={onGrowth} />
        </div>
      </div>
      <Timeline data={points} checked={[checked[0] ?? weekly.holdout_start, checked[checked.length - 1] ?? weekly.holdout_start]}
                forecastFrom={forecastFrom} changesFrom={start} />
      <p className="note">
        Future years repeat each market's usual seasonal pattern; use the growth slider to add a trend. Public holidays are included up to {formatMonth(weekly.calendar_flags_until)}.
      </p>
    </div>
  );
}
