import { Badge, StatCard, type Tone } from "../../components/ui";
import { formatFull, formatPercent } from "../../data/format";
import { rangeError } from "../../engine/nowcastViews";
import { DIRECTION_THRESHOLD, type Direction, type RangeSummary } from "../../engine/range";

const tone = (direction: Direction | null): Tone => (direction === "up" ? "up" : direction === "down" ? "down" : "neutral");

function DirectionBadge({ summary }: { summary: RangeSummary }) {
  if (summary.change === null) return <Badge tone="neutral">nothing to compare with</Badge>;
  return <Badge tone={tone(summary.direction)}>{summary.direction === "no clear change" ? "about the same" : summary.direction} {formatPercent(summary.change)} vs the days before</Badge>;
}

/** The selected days: forecast total with its error, the total with the check-in changes, and each
 *  one's change against the same number of days before (called flat below DIRECTION_THRESHOLD). */
export function RangeCards({ predicted, scenario, changed, days }: { predicted: RangeSummary; scenario: RangeSummary; changed: boolean; days: number }) {
  return (
    <div className="stat-grid">
      <StatCard title="Forecast hotel guests" subtitle={`Total over ${days} days`} tone="accent"
                value={formatFull(predicted.guests)} caption={`±${Math.round(rangeError(predicted) * 100)}% error`} badge={<DirectionBadge summary={predicted} />} />
      <StatCard title="With your changes" subtitle={changed ? "Using the check-in sliders" : "Move a slider to compare"} tone="secondary"
                value={formatFull(scenario.guests)} caption={changed ? `${formatPercent(scenario.guests / predicted.guests - 1)} vs the forecast` : "Same as the forecast"}
                badge={<DirectionBadge summary={scenario} />} />
      <StatCard title="The days before" subtitle="Same number of days, just before" tone="neutral"
                value={predicted.previousGuests === null ? "n/a" : formatFull(predicted.previousGuests)} caption="Real guests where known, otherwise forecast"
                badge={<Badge tone="neutral">changes under ±{Math.round(DIRECTION_THRESHOLD * 100)}% count as flat</Badge>} />
    </div>
  );
}
