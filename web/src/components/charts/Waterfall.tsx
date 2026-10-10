import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";

export interface WaterfallStep { label: string; value: number; total?: boolean }

/** Waterfall: totals as full bars, each step floating from the running sum (a transparent offset bar
 *  under a visible span), coloured by sign. */
export function Waterfall({ steps }: { steps: WaterfallStep[] }) {
  let running = 0;
  const data = steps.map((step) => {
    const start = step.total ? 0 : running;
    const end = step.total ? step.value : running + step.value;
    running = end;
    return { label: step.label, offset: Math.min(start, end), span: Math.abs(end - start), value: step.value, total: !!step.total };
  });
  const fill = (d: (typeof data)[number]) => d.total ? "var(--color-accent)" : d.value >= 0 ? "var(--color-up)" : "var(--color-down)";
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--color-border)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} interval={0} tick={{ fill: "var(--color-text-muted)", fontSize: 11 }} />
        <YAxis tickFormatter={formatCount} tickLine={false} axisLine={false} width={56} tick={{ fill: "var(--color-text-muted)", fontSize: 12 }} />
        <Tooltip cursor={{ fill: "var(--color-surface-muted)" }}
                 formatter={(_, name, item) => name === "span" ? [formatCount(item.payload.value), item.payload.total ? "Weekly guests" : "Change"] : [null, null]} />
        <Bar dataKey="offset" stackId="w" fill="transparent" isAnimationActive={false} />
        <Bar dataKey="span" stackId="w" radius={[4, 4, 4, 4]} isAnimationActive={false}>
          {data.map((d) => <Cell key={d.label} fill={fill(d)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
