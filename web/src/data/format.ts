/** Every number, date and tone shown in the UI is formatted here; components never format inline. */
const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const formatCount = (value: number) => (Math.abs(value) >= 10_000 ? compact.format(value) : whole.format(value));
export const formatFull = (value: number) => whole.format(value);
/** "+1,234" / "-56" / "0": a signed value, formatted by `format` (whole numbers by default). */
export const formatSigned = (value: number, format: (v: number) => string = formatFull) => `${value > 0 ? "+" : ""}${format(value)}`;
/** A change as a signed percentage: 0.034 -> "+3.4%". */
export const formatPercent = (value: number, digits = 1) => formatSigned(value, (v) => `${(v * 100).toFixed(digits)}%`);
/** A share as an unsigned percentage: 0.282 -> "28.2%". */
export const formatShare = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
/** "2025-07-21" -> "Jul 2025" (long) or "Jul 25" (short). */
export const formatMonth = (iso: string, style: "long" | "short" = "long") =>
  `${MONTHS[Number(iso.slice(5, 7)) - 1]} ${style === "long" ? iso.slice(0, 4) : iso.slice(2, 4)}`;
/** "2025-12" or "2025-12-01" -> "December". */
export const formatMonthName = (iso: string) => new Date(Date.UTC(Number(iso.slice(0, 4)), Number(iso.slice(5, 7)) - 1, 1)).toLocaleString("en", { month: "long", timeZone: "UTC" });
/** "2025-07-21" -> "07-21". */
export const formatDay = (iso: string) => iso.slice(5);
export const titleCase = (name: string) => name.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/_/g, " ");
/** Class for a change: "tone-up", "tone-down", or undefined when there is none. */
export const toneOf = (delta: number) => (delta > 0 ? "tone-up" : delta < 0 ? "tone-down" : undefined);
