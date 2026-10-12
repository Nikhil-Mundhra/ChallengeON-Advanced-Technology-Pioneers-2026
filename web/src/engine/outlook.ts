/**
 * Forward months for the landing page, from the bundle's `outlook` (schema 3): hotel nights past the
 * end of the data under one arrivals scenario, corrected by the projection's median miss in back-tests
 * at the same distance (`calibrated`), with the range of those misses and the same month a year
 * earlier. A change counts as up or down only when last year's figure lies outside the range;
 * otherwise the month is "about the same". Without a band the raw projection is shown with no range.
 */
import type { Trend } from "./insights";
import type { Outlook, OutlookBand } from "./types";

export const FALLBACK_SCENARIO = "flat";

export interface OutlookRow {
  month: string;                // YYYY-MM
  guests: number;               // figure to show: calibrated when available, else the raw projection
  raw: number;                  // raw projection
  calibrated: boolean;          // whether `guests` carries the back-test correction
  previous: number | null;
  previousKind: "actual" | "estimate" | null;
  change: number | null;        // guests / previous - 1
  horizon: number;              // months after the last month with data
  low: number | null;           // range in hotel nights: raw × (1 + band.low); null without a calibrated figure
  high: number | null;
  band: OutlookBand | null;
  trend: Trend | null;
}

const monthIndex = (month: string) => Number(month.slice(0, 4)) * 12 + Number(month.slice(5, 7)) - 1;

/** Months from the last month with data to `month` (the month after it is 1). */
export function horizonMonths(dataEnd: string, month: string): number {
  return monthIndex(month) - monthIndex(dataEnd);
}

/** The back-tested band at `horizon`: an exact match, else the nearest longer one, else the longest. */
export function bandFor(bands: OutlookBand[] | undefined, horizon: number): OutlookBand | null {
  if (!bands?.length) return null;
  const sorted = [...bands].sort((a, b) => a.horizon_months - b.horizon_months);
  return sorted.find((b) => b.horizon_months >= horizon) ?? sorted[sorted.length - 1];
}

export function scenarioOf(outlook: Outlook): string {
  const wanted = outlook.default_scenario ?? FALLBACK_SCENARIO;
  return outlook.scenarios[wanted] ? wanted : Object.keys(outlook.scenarios)[0];
}

/** The bands of one scenario and segment; the top-level `band` stands for the default scenario's TOTAL only. */
function bandsOf(outlook: Outlook, scenario: string, segment: string): OutlookBand[] | undefined {
  return outlook.bands?.[scenario]?.[segment] ?? (segment === "TOTAL" && scenario === scenarioOf(outlook) ? outlook.band : undefined);
}

/** One segment's projected months under `scenario`, each with the figure to show, its range, change and trend. */
export function outlookRows(outlook: Outlook, segment: string, scenario = scenarioOf(outlook)): OutlookRow[] {
  const months = outlook.scenarios[scenario]?.[segment] ?? [];
  const bands = bandsOf(outlook, scenario, segment);
  return months.map((m) => {
    const horizon = m.horizon_months ?? horizonMonths(outlook.data_end, m.month);
    const calibrated = typeof m.calibrated === "number";
    const band = calibrated ? bandFor(bands, horizon) : null;
    const guests = calibrated ? m.calibrated! : m.guests;
    const [low, high] = band ? [Math.max(0, m.guests * (1 + band.low)), Math.max(0, m.guests * (1 + band.high))] : [null, null];
    const change = m.previous ? guests / m.previous - 1 : null;
    const trend: Trend | null = change === null || low === null || high === null ? null
      : m.previous! >= Math.min(low, high) && m.previous! <= Math.max(low, high) ? "same" : change > 0 ? "up" : "down";
    return { month: m.month, guests, raw: m.guests, calibrated, previous: m.previous, previousKind: m.previous_kind, change, horizon, low, high, band, trend };
  });
}

/** One segment's uncorrected projection by month: the raw `guests` only, with no correction, range,
 *  change or trend (the back-test correction is shown for TOTAL only). */
export function rawProjection(outlook: Outlook, segment: string, scenario = scenarioOf(outlook)): Array<{ month: string; guests: number }> {
  return (outlook.scenarios[scenario]?.[segment] ?? []).map((m) => ({ month: m.month, guests: m.guests }));
}

/** The month to lead with: the first month after `today`'s month, else the last projected month. */
export function leadRow(rows: OutlookRow[], today: string): OutlookRow | null {
  if (!rows.length) return null;
  return rows.find((r) => r.month > today.slice(0, 7)) ?? rows[rows.length - 1];
}

/** The lead month and the ones after it. */
export function comingRows(rows: OutlookRow[], today: string): OutlookRow[] {
  const lead = leadRow(rows, today);
  return lead ? rows.filter((r) => r.month >= lead.month) : [];
}
