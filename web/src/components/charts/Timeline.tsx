import { Area, Brush, CartesianGrid, ComposedChart, Legend, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";

export interface TimelinePoint {
  week: string;
  actual: number | null;
  model: number;
  holdout: number | null;
  scenario: number | null;
  band: [number, number] | null;
}

interface TimelineProps {
  data: TimelinePoint[];
  holdout: [string, string];      // back-test window
  projectedFrom: string | null;   // first week with no schedule
  scenarioFrom: string;
}

/** Weekly series over time: actual weeks, the out-of-sample back-test, the model at current
 *  service, and the scenario with its band. Shaded: back-test window, projected (unscheduled) weeks. */
export function Timeline({ data, holdout, projectedFrom, scenarioFrom }: TimelineProps) {
  const last = data[data.length - 1]?.week;
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="week" type="category" allowDuplicatedCategory={false} tickLine={false} axisLine={false} minTickGap={48} tickFormatter={(w: string) => w.slice(0, 7)}
               tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <YAxis tickFormatter={formatCount} tickLine={false} axisLine={false} width={56} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <Tooltip formatter={(value) => Array.isArray(value) ? value.map((v) => formatCount(Number(v))).join(" – ") : formatCount(Number(value))} />
        <Legend verticalAlign="top" height={28} iconType="plainline" />
        <ReferenceArea x1={holdout[0]} x2={holdout[1]} fill="var(--color-secondary)" fillOpacity={0.12}
                       label={{ value: "back-test", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        {projectedFrom && last && (
          <ReferenceArea x1={projectedFrom} x2={last} fill="var(--color-text-muted)" fillOpacity={0.08}
                         label={{ value: "projection (no flight schedule)", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        )}
        <ReferenceLine x={scenarioFrom} stroke="var(--color-accent)" strokeDasharray="4 4" />
        <Area dataKey="band" name="Scenario band" stroke="none" fill="var(--color-accent-soft)" fillOpacity={0.9} isAnimationActive={false} />
        <Line dataKey="model" name="Model, current service" stroke="var(--color-text-muted)" strokeDasharray="5 4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
        <Line dataKey="holdout" name="Back-test (out of sample)" stroke="var(--color-secondary)" dot={false} strokeWidth={2} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="actual" name="Actual" stroke="var(--color-text)" dot={false} strokeWidth={1.5} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="scenario" name="Scenario" stroke="var(--color-accent)" dot={false} strokeWidth={2.2} connectNulls={false} isAnimationActive={false} />
        <Brush dataKey="week" height={22} travellerWidth={8} stroke="var(--color-accent)" tickFormatter={(w: string) => w.slice(0, 7)} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
