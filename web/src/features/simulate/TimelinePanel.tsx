import { Timeline } from "../../components/charts/Timeline";
import { eventName } from "../../content/labels";
import { formatMonth } from "../../data/format";
import { holdoutWmape } from "../../engine/weekly";
import type { Weekly, WeekPoint } from "../../engine/weekly";

/** Past weeks with the model's check against them, and the forecast with the changes from a chosen week. */
export function TimelinePanel({ weekly, points, error, start }: { weekly: Weekly; points: WeekPoint[]; error: number | null; start: string }) {
  if (!points.length) {
    return (
      <div className="canvas__body">
        <p className="note">No direct flight or hotel history for this market yet. Weekly impact is estimated using archetype priors from similar markets (see &ldquo;How it adds up&rdquo; or &ldquo;Biggest levers&rdquo;).</p>
      </div>
    );
  }
  const checked = points.filter((p) => p.holdout !== null).map((p) => p.week);
  const forecastFrom = points.find((p) => p.kind === "projected")?.week ?? null;
  const eventError = holdoutWmape(points.filter((p) => p.event));
  const flags = points.filter((p, i) => p.event && p.event !== points[i - 1]?.event).map((p) => ({ week: p.week, label: eventName(p.event)! }));
  return (
    <div className="canvas__body">
      <p className="note">
        Hotel nights per week.{error !== null && ` Checked against ${checked.length} real weeks, the model was off by about ±${Math.round(error)}% on average${eventError === null ? "" : `, and ±${Math.round(eventError)}% on event weeks`}. Dotted lines mark events; hover to inspect.`}
      </p>
      <Timeline data={points} checked={[checked[0] ?? weekly.holdout_start, checked[checked.length - 1] ?? weekly.holdout_start]}
                forecastFrom={forecastFrom} changesFrom={start} flags={flags} />
      <p className="note">
        Future years repeat each market's usual seasonal pattern; set yearly growth on the left to add a trend. Public holidays are included up to {formatMonth(weekly.calendar_flags_until)}.
      </p>
    </div>
  );
}
