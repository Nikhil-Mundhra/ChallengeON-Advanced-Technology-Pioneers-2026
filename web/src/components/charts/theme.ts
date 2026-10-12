/** Shared chart styling, spread into Recharts elements (Recharts needs its axes as direct children,
 *  so this is props, not a wrapper component). Colours are semantic tokens with dark-mode values. */
import { formatCount } from "../../data/format";

export const MARGIN = { top: 8, right: 8, left: 0, bottom: 0 };
const TICK = { fill: "var(--color-text-muted)", fontSize: 12 };
export const gridProps = { vertical: false, stroke: "var(--color-border)" } as const;
export const xAxisProps = { tickLine: false, axisLine: false, tick: TICK } as const;
export const yAxisProps = { tickFormatter: formatCount, tickLine: false, axisLine: false, width: 56, tick: TICK } as const;
export const cursor = { fill: "var(--color-surface-muted)" };

export const SERIES = {
  actual: "var(--color-strong)",
  forecast: "var(--color-text-muted)",
  scenario: "var(--color-accent)",
  check: "var(--color-series-check)",
  comparison: "var(--color-comparison)",
  up: "var(--color-up)",
  down: "var(--color-down)",
} as const;

export const tooltipContentStyle = {
  backgroundColor: "var(--color-surface-glass)",
  borderColor: "var(--color-border)",
  borderRadius: "var(--radius-md)",
  boxShadow: "var(--shadow-elevation-2)",
  color: "var(--color-text)",
  fontSize: "var(--text-sm)",
  padding: "8px 12px",
  backdropFilter: "blur(16px) saturate(1.4)",
  WebkitBackdropFilter: "blur(16px) saturate(1.4)",
} as const;

export const tooltipItemStyle = {
  color: "var(--color-text)",
  fontSize: "var(--text-sm)",
  padding: "2px 0",
} as const;

export const tooltipLabelStyle = {
  color: "var(--color-text-muted)",
  fontSize: "var(--text-xs)",
  fontWeight: "var(--weight-bold)",
  marginBottom: "4px",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
} as const;

export const tooltipProps = {
  contentStyle: tooltipContentStyle,
  itemStyle: tooltipItemStyle,
  labelStyle: tooltipLabelStyle,
  cursor,
} as const;

/** Tooltip value: a count, or "low to high" for a range. */
export const formatTooltipValue = (value: unknown) =>
  Array.isArray(value) ? value.map((v) => formatCount(Number(v))).join(" to ") : formatCount(Number(value));
