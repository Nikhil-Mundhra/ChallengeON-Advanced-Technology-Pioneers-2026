import { Badge, Card, Stat, type Tone } from "../../components/ui";
import { formatFull, formatPercent } from "../../data/format";
import type { Direction, RangeSummary } from "../../engine/range";

const tone = (direction: Direction | null): Tone => (direction === "up" ? "up" : direction === "down" ? "down" : "neutral");

function DirectionBadge({ summary }: { summary: RangeSummary }) {
  if (summary.change === null) return <Badge tone="neutral">no comparison</Badge>;
  return <Badge tone={tone(summary.direction)}>{summary.direction} · {formatPercent(summary.change)}</Badge>;
}

/** The selected range: predicted total with its interval, the what-if total, and each one's change
 *  against the range before it (stated only above the 8% threshold). */
export function RangeCards({ predicted, scenario, changed, coverage, days }: {
  predicted: RangeSummary; scenario: RangeSummary; changed: boolean; coverage: string; days: number;
}) {
  const label = `${Math.round(Number(coverage) * 100)}% interval`;
  return (
    <div className="range-cards">
      <Card title="Predicted guests" subtitle={`${days}-day total`} className="range-card range-card--accent">
        <Stat value={formatFull(predicted.guests)} caption={`${label}: ${formatFull(predicted.low)} – ${formatFull(predicted.high)}`} />
        <DirectionBadge summary={predicted} />
      </Card>
      <Card title="What-if guests" subtitle={changed ? "with the arrivals sliders" : "move a slider to compare"} className="range-card range-card--secondary">
        <Stat value={formatFull(scenario.guests)}
              caption={changed ? `${formatPercent(scenario.guests / predicted.guests - 1)} vs predicted` : "same as predicted"} />
        <DirectionBadge summary={scenario} />
      </Card>
      <Card title="Previous range" subtitle="same length, just before" className="range-card range-card--neutral">
        <Stat value={predicted.previousGuests === null ? "—" : formatFull(predicted.previousGuests)}
              caption="actual guests where known, else predicted" />
        <Badge tone="neutral">threshold ±8%</Badge>
      </Card>
    </div>
  );
}
