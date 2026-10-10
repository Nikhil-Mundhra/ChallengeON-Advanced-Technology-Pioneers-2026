import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDay } from "../../data/format";
import { formatTooltipValue, gridProps, MARGIN, SERIES, xAxisProps, yAxisProps } from "./theme";

export interface TrendPoint {
  date: string;
  pred: number;
  band: [number, number];
  whatIf?: number;
}

/** Daily forecast with its likely range, and the line with changes when check-ins are changed. */
export function TrendBand({ data, showWhatIf }: { data: TrendPoint[]; showWhatIf: boolean }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={MARGIN}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="date" {...xAxisProps} minTickGap={28} tickFormatter={formatDay} />
        <YAxis {...yAxisProps} />
        <Tooltip formatter={formatTooltipValue} />
        <Area dataKey="band" name="Likely range" stroke="none" fill={SERIES.scenario} fillOpacity={0.12} />
        <Line dataKey="pred" name="Forecast" stroke={SERIES.actual} strokeWidth={2} dot={false} />
        {showWhatIf && <Line dataKey="whatIf" name="With your changes" stroke={SERIES.scenario} strokeWidth={2} strokeDasharray="5 4" dot={false} />}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
