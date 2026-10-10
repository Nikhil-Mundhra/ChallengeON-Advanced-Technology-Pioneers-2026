import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";

export interface BarPoint {
  label: string;
  current: number;
  comparison: number | null;
}

/** Paired bars: the predicted (or what-if) value next to its comparison (e.g. a year earlier). */
export function BarCompare({ data, currentLabel, comparisonLabel }: { data: BarPoint[]; currentLabel: string; comparisonLabel: string }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} barGap={4} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <YAxis tickFormatter={formatCount} tickLine={false} axisLine={false} width={56} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <Tooltip formatter={(value) => formatCount(Number(value))} cursor={{ fill: "var(--color-surface-muted)" }} />
        <Bar dataKey="comparison" name={comparisonLabel} fill="var(--color-comparison)" radius={[6, 6, 0, 0]} />
        <Bar dataKey="current" name={currentLabel} fill="var(--color-accent)" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
