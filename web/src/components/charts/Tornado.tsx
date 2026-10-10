import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatTooltipValue, gridProps, SERIES, tooltipProps, xAxisProps, yAxisProps } from "./theme";

export interface TornadoBar { label: string; low: number; high: number }

/** Change in weekly guests when each lever moves one step down (left) and up (right); biggest first. */
export function Tornado({ rows }: { rows: TornadoBar[] }) {
  return (
    <ResponsiveContainer width="100%" height={56 + rows.length * 40}>
      <BarChart data={rows} layout="vertical" stackOffset="sign" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid {...gridProps} vertical horizontal={false} />
        <XAxis type="number" {...yAxisProps} width={undefined} />
        <YAxis type="category" dataKey="label" {...xAxisProps} width={210} tick={{ ...xAxisProps.tick, fill: "var(--color-text)" }} />
        <Tooltip {...tooltipProps} formatter={formatTooltipValue} />
        <ReferenceLine x={0} stroke="var(--color-text-muted)" />
        <Bar dataKey="low" name="One step down" stackId="t" fill={SERIES.check} radius={[4, 4, 4, 4]} isAnimationActive={false} />
        <Bar dataKey="high" name="One step up" stackId="t" fill={SERIES.scenario} radius={[4, 4, 4, 4]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
