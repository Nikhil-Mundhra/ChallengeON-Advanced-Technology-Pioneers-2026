import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";

export interface TrendPoint {
  date: string;
  pred: number;
  band: [number, number];
  whatIf?: number;
}

/** Daily prediction with its interval band, and the what-if line when arrivals are changed. */
export function TrendBand({ data, showWhatIf }: { data: TrendPoint[]; showWhatIf: boolean }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={28} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }}
               tickFormatter={(d: string) => d.slice(5)} />
        <YAxis tickFormatter={formatCount} tickLine={false} axisLine={false} width={56} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <Tooltip formatter={(value) => (Array.isArray(value) ? value.map((v) => formatCount(Number(v))).join(" – ") : formatCount(Number(value)))} />
        <Area dataKey="band" name="Interval" stroke="none" fill="var(--color-secondary-soft)" />
        <Line dataKey="pred" name="Predicted" stroke="var(--color-secondary)" strokeWidth={2} dot={false} />
        {showWhatIf && <Line dataKey="whatIf" name="What-if" stroke="var(--color-accent)" strokeWidth={2} strokeDasharray="5 4" dot={false} />}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
