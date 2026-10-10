import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";

export interface TornadoBar { label: string; low: number; high: number }

/** Tornado: change in weekly guests when each lever moves down (left) and up (right); widest first. */
export function Tornado({ rows }: { rows: TornadoBar[] }) {
  return (
    <ResponsiveContainer width="100%" height={56 + rows.length * 40}>
      <BarChart data={rows} layout="vertical" stackOffset="sign" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid horizontal={false} stroke="var(--color-border)" />
        <XAxis type="number" tickFormatter={formatCount} tickLine={false} axisLine={false} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <YAxis type="category" dataKey="label" width={170} tickLine={false} axisLine={false} tick={{ fill: "var(--color-text)", fontSize: 12 }} />
        <Tooltip formatter={(value) => formatCount(Number(value))} cursor={{ fill: "var(--color-surface-muted)" }} />
        <ReferenceLine x={0} stroke="var(--color-text-muted)" />
        <Bar dataKey="low" name="Lever down" stackId="t" fill="var(--color-secondary)" radius={[4, 4, 4, 4]} isAnimationActive={false} />
        <Bar dataKey="high" name="Lever up" stackId="t" fill="var(--color-accent)" radius={[4, 4, 4, 4]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}
