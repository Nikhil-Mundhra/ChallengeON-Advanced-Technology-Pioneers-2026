import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCount } from "../../data/format";
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
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={MARGIN}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="label" {...xAxisProps} interval={0} tick={{ ...xAxisProps.tick, fontSize: 11 }} />
        <YAxis {...yAxisProps} />
        <Tooltip {...tooltipProps}
                 formatter={(_, name, item) => name === "span" ? [formatCount(item.payload.value), item.payload.total ? "Hotel nights per week" : "Change"] : [null, null]} />
        <Bar dataKey="offset" stackId="w" fill="transparent" isAnimationActive={false} />
        <Bar dataKey="span" stackId="w" radius={[4, 4, 4, 4]} isAnimationActive={false}>
          {data.map((d) => <Cell key={d.label} fill={fill(d)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
