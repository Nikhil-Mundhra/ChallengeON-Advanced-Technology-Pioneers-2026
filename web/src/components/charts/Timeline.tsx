import { Area, Brush, CartesianGrid, ComposedChart, Legend, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMonth } from "../../data/format";
import type { WeekPoint } from "../../engine/weekly";
import { formatTooltipValue, gridProps, MARGIN, SERIES, xAxisProps, yAxisProps } from "./theme";

interface TimelineProps {
  data: WeekPoint[];
  checked: [string, string];      // weeks the model was checked against, fitted before them
  forecastFrom: string | null;    // first week with no flight schedule
  changesFrom: string;
}

const short = (week: string) => formatMonth(week, "short");
const NAMES: Record<string, string> = {
  actual: "Real guests", holdout: "Model check", model: "Forecast without changes", scenario: "Forecast with your changes", band: "Likely range",
};

/** Weekly hotel guests over time: real weeks, the model's check against weeks it had not seen, and
 *  the forecast without and with the changes. Shaded: the checked weeks and the forecast years. */
export function Timeline({ data, checked, forecastFrom, changesFrom }: TimelineProps) {
  const last = data[data.length - 1]?.week;
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={MARGIN}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="week" type="category" allowDuplicatedCategory={false} {...xAxisProps} minTickGap={56} tickFormatter={short} />
        <YAxis {...yAxisProps} />
        <Tooltip labelFormatter={(w) => `Week of ${w}`}
                 formatter={(value, name) => [formatTooltipValue(value), NAMES[String(name)] ?? name]} />
        <Legend verticalAlign="top" height={28} iconType="plainline" formatter={(name) => NAMES[String(name)] ?? name} />
        <ReferenceArea x1={checked[0]} x2={checked[1]} fill={SERIES.check} fillOpacity={0.1}
                       label={{ value: "Model check", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        {forecastFrom && last && (
          <ReferenceArea x1={forecastFrom} x2={last} fill="var(--color-band-forecast)" fillOpacity={0.35}
                         label={{ value: "Forecast", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        )}
        <ReferenceLine x={changesFrom} stroke={SERIES.scenario} strokeDasharray="4 4" />
        <Area dataKey="band" name="band" stroke="none" fill={SERIES.scenario} fillOpacity={0.12} isAnimationActive={false} legendType="square" />
        <Line dataKey="model" name="model" stroke={SERIES.forecast} strokeDasharray="5 4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
        <Line dataKey="holdout" name="holdout" stroke={SERIES.check} dot={false} strokeWidth={2} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="actual" name="actual" stroke={SERIES.actual} dot={false} strokeWidth={1.5} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="scenario" name="scenario" stroke={SERIES.scenario} dot={false} strokeWidth={2.2} connectNulls={false} isAnimationActive={false} />
        <Brush dataKey="week" height={20} travellerWidth={8} stroke="var(--color-comparison)" fill="var(--color-surface)" tickFormatter={short} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
