import { useMemo } from "react";
import { Area, Brush, CartesianGrid, ComposedChart, Legend, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDate, formatMonth } from "../../data/format";
import { eventName } from "../../content/labels";
import type { WeekPoint } from "../../engine/weekly";
import { formatTooltipValue, gridProps, MARGIN, SERIES, tooltipProps, xAxisProps, yAxisProps } from "./theme";

interface TimelineProps {
  data: WeekPoint[];
  checked: [string, string];      // weeks the model was checked against, fitted before them
  forecastFrom: string | null;    // first week with no flight schedule
  changesFrom: string;
  flags?: Array<{ week: string; label: string }>;   // event starts to mark
}

const short = (week: string) => formatMonth(week, "short");
const NAMES: Record<string, string> = {
  actual: "Real", holdout: "Model check", model: "Forecast without changes", scenario: "Forecast with your changes", band: "Likely range",
};

/** Weekly hotel guests over time: real weeks, the model's check against weeks it had not seen, and
 *  the forecast without and with the changes. Shaded: the checked weeks and the forecast years. */
export function Timeline({ data, checked, forecastFrom, changesFrom, flags = [] }: TimelineProps) {
  const last = data[data.length - 1]?.week;
  const eventByWeek = useMemo(() => new Map(data.filter((d) => d.event).map((d) => [d.week, eventName(d.event)!])), [data]);

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={MARGIN}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="week" type="category" allowDuplicatedCategory={false} {...xAxisProps} minTickGap={56} tickFormatter={short} />
        <YAxis {...yAxisProps} />
        <Tooltip {...tooltipProps}
                 content={({ active, payload, label }) => {
                   if (!active || !payload?.length) return null;
                   const weekStr = String(label ?? "");
                   const evt = eventByWeek.get(weekStr);
                   const validItems = payload.filter((p) => p.value !== null && p.value !== undefined);
                   return (
                     <div style={tooltipProps.contentStyle}>
                       <div style={tooltipProps.labelStyle}>Week of {formatDate(weekStr)}</div>
                       {evt && (
                         <div style={{ color: "var(--color-series-check)", fontWeight: "var(--weight-bold)", fontSize: "var(--text-xs)", marginBottom: 6 }}>
                           ★ {evt}
                         </div>
                       )}
                       {validItems.map((p, idx) => (
                         <div key={String(p.dataKey ?? p.name ?? idx)} style={{ display: "flex", justifyContent: "space-between", gap: 12, ...tooltipProps.itemStyle }}>
                           <span style={{ color: p.color ?? "var(--color-text-muted)" }}>{NAMES[String(p.name)] ?? p.name}:</span>
                           <span style={{ fontWeight: "var(--weight-bold)", fontVariantNumeric: "tabular-nums" }}>{formatTooltipValue(p.value)}</span>
                         </div>
                       ))}
                     </div>
                   );
                 }} />
        <Legend verticalAlign="top" height={28} iconType="plainline" formatter={(name) => NAMES[String(name)] ?? name} />
        <ReferenceArea x1={checked[0]} x2={checked[1]} fill={SERIES.check} fillOpacity={0.1}
                       label={{ value: "Model check", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        {forecastFrom && last && (
          <ReferenceArea x1={forecastFrom} x2={last} fill="var(--color-band-forecast)" fillOpacity={0.35}
                         label={{ value: "Forecast", position: "insideTop", fill: "var(--color-text-muted)", fontSize: 11 }} />
        )}
        <ReferenceLine x={changesFrom} stroke={SERIES.scenario} strokeDasharray="4 4" />
        {flags.map((f) => (
          <ReferenceLine key={f.week} x={f.week} stroke="var(--color-series-check)" strokeOpacity={0.25} strokeDasharray="2 3" />
        ))}
        <Area dataKey="band" name="band" stroke="none" fill={SERIES.scenario} fillOpacity={0.12} isAnimationActive={false} legendType="rect" />
        <Line dataKey="model" name="model" stroke={SERIES.forecast} strokeDasharray="5 4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
        <Line dataKey="holdout" name="holdout" stroke={SERIES.check} dot={false} strokeWidth={2} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="actual" name="actual" stroke={SERIES.actual} dot={false} strokeWidth={1.5} connectNulls={false} isAnimationActive={false} />
        <Line dataKey="scenario" name="scenario" stroke={SERIES.scenario} dot={false} strokeWidth={2.2} connectNulls={false} isAnimationActive={false} />
        <Brush dataKey="week" height={22} travellerWidth={14} stroke="var(--color-comparison)" fill="var(--color-surface)" tickFormatter={short} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
