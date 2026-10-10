import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { cursor, formatTooltipValue, gridProps, MARGIN, SERIES, xAxisProps, yAxisProps } from "./theme";

export interface BarPoint {
  label: string;
  current: number;
  comparison: number | null;
}

/** Paired bars: the forecast (or with changes) next to its comparison (e.g. last year). */
export function BarCompare({ data, currentLabel, comparisonLabel }: { data: BarPoint[]; currentLabel: string; comparisonLabel: string }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} barGap={4} margin={MARGIN}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="label" {...xAxisProps} />
        <YAxis {...yAxisProps} />
        <Tooltip formatter={formatTooltipValue} cursor={cursor} />
        <Bar dataKey="comparison" name={comparisonLabel} fill={SERIES.comparison} radius={[6, 6, 0, 0]} />
        <Bar dataKey="current" name={currentLabel} fill={SERIES.scenario} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
