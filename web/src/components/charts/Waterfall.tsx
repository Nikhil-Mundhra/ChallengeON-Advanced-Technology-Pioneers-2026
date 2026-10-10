import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount, formatSigned } from "../../data/format";
import { gridProps, MARGIN, SERIES, tooltipProps, xAxisProps, yAxisProps } from "./theme";

export interface WaterfallStep { label: string; value: number; total?: boolean }

/** Totals as full bars; each step floats from the running sum (a transparent offset bar under a
 *  visible span), coloured by sign. */
export function Waterfall({ steps }: { steps: WaterfallStep[] }) {
  let running = 0;
  const data = steps.map((step) => {
    const start = step.total ? 0 : running;
    const end = step.total ? step.value : running + step.value;
    running = end;
    return { label: step.label, offset: Math.min(start, end), span: Math.abs(end - start), value: step.value, total: !!step.total };
  });
  const fill = (d: (typeof data)[number]) => d.total ? SERIES.actual : d.value >= 0 ? SERIES.up : SERIES.down;
  const isCrowded = data.length > 4;

  return (
    <div className="waterfall">
      <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", fontSize: "var(--text-xs)", color: "var(--color-text-muted)", marginBottom: "4px" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
          <i style={{ width: 8, height: 8, borderRadius: 2, background: SERIES.actual, display: "inline-block" }} /> Total
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
          <i style={{ width: 8, height: 8, borderRadius: 2, background: SERIES.up, display: "inline-block" }} /> Increase (+Δ)
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
          <i style={{ width: 8, height: 8, borderRadius: 2, background: SERIES.down, display: "inline-block" }} /> Decrease (-Δ)
        </span>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ ...MARGIN, bottom: isCrowded ? 16 : 4 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="label" {...xAxisProps} interval={0}
                 height={isCrowded ? 36 : 24}
                 angle={isCrowded ? -20 : 0}
                 textAnchor={isCrowded ? "end" : "middle"}
                 tick={{ ...xAxisProps.tick, fontSize: 10 }} />
          <YAxis {...yAxisProps} />
          <Tooltip {...tooltipProps}
                   formatter={(_, name, item) => {
                     if (name !== "span") return [null, null];
                     const payload = item.payload;
                     if (payload.total) return [formatCount(payload.value), "Hotel nights per week"];
                     if (Math.abs(payload.value) < 1e-4) return ["No change", payload.label];
                     return [formatSigned(payload.value, formatCount), `${payload.label} change`];
                   }} />
          <Bar dataKey="offset" stackId="w" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="span" stackId="w" radius={[1, 1, 1, 1]} isAnimationActive={false}>
            {data.map((d) => <Cell key={d.label} fill={fill(d)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
