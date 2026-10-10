const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });

export const formatCount = (value: number) => (Math.abs(value) >= 10_000 ? compact.format(value) : whole.format(value));
export const formatFull = (value: number) => whole.format(value);
export const formatPercent = (value: number, digits = 1) => `${value > 0 ? "+" : ""}${(value * 100).toFixed(digits)}%`;
export const titleCase = (name: string) => name.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/_/g, " ");
