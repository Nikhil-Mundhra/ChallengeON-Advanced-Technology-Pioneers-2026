import { Badge, StatCard, type Tone } from "../../components/ui";
import { formatDate, formatFull, formatPercent } from "../../data/format";
import { rangeError } from "../../engine/nowcastViews";
import { DIRECTION_THRESHOLD, type Direction, type RangeSummary } from "../../engine/range";

const tone = (direction: Direction | null): Tone => (direction === "up" ? "up" : direction === "down" ? "down" : "neutral");

function DirectionBadge({ summary }: { summary: RangeSummary }) {
  if (summary.change === null) return <Badge tone="neutral">nothing to compare with</Badge>;
  const text = summary.direction === "no clear change"
    ? `no clear change (${formatPercent(summary.change)})`
    : `guests ${summary.direction} ${formatPercent(summary.change)}`;
  return <Badge tone={tone(summary.direction)}>{text} vs the days before</Badge>;
}

const DAY = 86_400_000;

interface RangeCardsProps {
  predicted: RangeSummary;
  scenario: RangeSummary;
  changed: boolean;
  days: number;
  start?: string;
  end?: string;
}

/** The selected days: forecast total with its error interval, the total with the check-in changes,
 *  and each one's change against the same number of days before (called flat below DIRECTION_THRESHOLD). */
export function RangeCards({ predicted, scenario, changed, days, start, end }: RangeCardsProps) {
  const prevStart = start ? new Date(Date.parse(`${start}T00:00:00Z`) - days * DAY).toISOString().slice(0, 10) : null;
  const prevEnd = start ? new Date(Date.parse(`${start}T00:00:00Z`) - DAY).toISOString().slice(0, 10) : null;
  return (
    <div className="stat-grid">
      <StatCard title="Forecast hotel guests"
                subtitle={start && end ? `${formatDate(start)} → ${formatDate(end)} (${days} days)` : `Total over ${days} days`}
                tone="accent"
                value={formatFull(predicted.guests)}
                caption={`Likely range: ${formatFull(predicted.low)} to ${formatFull(predicted.high)} (±${Math.round(rangeError(predicted) * 100)}% error)`}
                badge={<DirectionBadge summary={predicted} />} />
      <StatCard title="With your changes"
                subtitle={changed ? "Using the check-in sliders" : "Move a slider to compare"}
                tone="secondary"
                value={formatFull(scenario.guests)}
                caption={changed ? `Likely range: ${formatFull(scenario.low)} to ${formatFull(scenario.high)} (${formatPercent(scenario.guests / predicted.guests - 1)} vs forecast)` : "Same as the forecast"}
                badge={<DirectionBadge summary={scenario} />} />
      <StatCard title="The days before"
                subtitle={prevStart && prevEnd ? `${formatDate(prevStart)} → ${formatDate(prevEnd)} (${days} days prior)` : "Same number of days, just before"}
                tone="neutral"
                value={predicted.previousGuests === null ? "n/a" : formatFull(predicted.previousGuests)}
                caption="Real guests where known, otherwise forecast"
                badge={<Badge tone="neutral">changes under ±{Math.round(DIRECTION_THRESHOLD * 100)}% count as no clear change</Badge>} />
    </div>
  );
}
