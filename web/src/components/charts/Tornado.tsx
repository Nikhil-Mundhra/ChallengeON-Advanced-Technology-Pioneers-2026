import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount, formatSigned } from "../../data/format";
import { gridProps, SERIES, tooltipProps, xAxisProps, yAxisProps } from "./theme";

export interface TornadoBar { label: string; low: number; high: number }

/** Change in weekly guests when each lever moves one step down (left) and up (right); biggest first. */
export function Tornado({ rows }: { rows: TornadoBar[] }) {
  if (!rows.length) {
    return <p className="note">No active levers for this market.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, 68 + rows.length * 44)}>
      <BarChart data={rows} layout="vertical" stackOffset="sign" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
        <CartesianGrid {...gridProps} vertical horizontal={false} />
        <XAxis type="number" {...yAxisProps} tickFormatter={(v) => formatSigned(Number(v), formatCount)} width={undefined} />
        <YAxis type="category" dataKey="label" {...xAxisProps} width={230} tick={{ ...xAxisProps.tick, fill: "var(--color-text)", fontSize: 11 }} />
        <Tooltip {...tooltipProps} formatter={(val) => formatSigned(Number(val), formatCount)} />
        <Legend verticalAlign="top" height={30} iconType="rect" wrapperStyle={{ fontSize: "var(--text-xs)" }} />
        <ReferenceLine x={0} stroke="var(--color-text-muted)" />
        <Bar dataKey="low" name="One step down (-Δ)" stackId="t" fill={SERIES.check} radius={[1, 1, 1, 1]} isAnimationActive={false} />
        <Bar dataKey="high" name="One step up (+Δ)" stackId="t" fill={SERIES.scenario} radius={[1, 1, 1, 1]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
