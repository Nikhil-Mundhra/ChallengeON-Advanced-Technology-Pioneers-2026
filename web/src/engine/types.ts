/** Shapes of the bundle written by `twin export` (src/tourism_twin/export/bundle.py, schema 2; schema 3 adds `outlook`). */

export interface Manifest {
  schema_version: number;
  version: string;
  created: string;
  git_sha: string;
  spec: string;
  coverage: number;
  predicted_period: { start: string; end: string };
  files: Record<"nowcast" | "whatif" | "planning" | "weekly" | "golden", string> & { outlook?: string };   // outlook from schema 3
  sha256: Record<"nowcast" | "whatif" | "planning" | "weekly" | "golden", string>;
  weights?: Record<string, string>;   // sha256 of the saved planning artifacts the bundle was built from
}

export interface NoiseParams {
  phi: number;
  sigma_eta: number;
  v0: number;
}

export interface Series {
  date: string[];
  horizon_days: number[];
  pred: number[];
  noise: NoiseParams;
}

export interface Nowcast {
  z: Record<string, number>;
  series: Record<string, Series>;
  history: Record<string, { date: string[]; guests: number[] }>;
  nationalities: Record<string, { date: string[]; pred: number[] }>;
}

export interface MarketWhatIf {
  date: string[];
  base: number[];
  pre: number[];
  in: number[];
  floor: number;
  multiplier: number[];
}

export interface WhatIf {
  formula: string;
  markets: Record<string, MarketWhatIf>;
}

/** One projected month of one segment (TOTAL, INTERNATIONAL, DOMESTIC) under one arrivals scenario. */
export interface OutlookMonth {
  month: string;                // YYYY-MM
  guests: number;               // raw projection: hotel nights in the month under the scenario
  calibrated?: number | null;   // guests × (1 + band mid): corrected by the projection's median past miss; null without a band
  previous: number | null;      // hotel nights in the same month a year earlier; null when the data has neither
  previous_kind: "actual" | "estimate" | null;   // real guests, or the model's estimate where real guests are not in the data
  horizon_months?: number;      // months after the last month with data (1 = the month after)
}

/** How the same projection missed in back-tests at one distance from the end of the data, as relative
 *  bounds on the raw projection: range = guests × (1 + low) to guests × (1 + high). Either bound can
 *  have either sign (the flat projection under-forecast in every back-test, so its low is above 0). */
export interface OutlookBand {
  horizon_months: number;
  low: number;
  high: number;
  mid?: number;                 // median past miss
  n?: number;                   // back-test windows
  miss_min?: number;
  miss_max?: number;
  wape_pct?: number;
  bias_pct?: number;
}

/** outlook.json (schema 3): model projections past the end of the data, one per arrivals scenario. */
export interface Outlook {
  data_end: string;             // last day with real arrivals (YYYY-MM-DD)
  guests_known_to?: string;     // last day with real guests
  spec?: string;
  coverage: number;             // nominal coverage of the band, e.g. 0.8
  default_scenario?: string;    // scenario to lead with; "flat" when absent
  scenarios: Record<string, Record<string, OutlookMonth[]>>;   // scenario ("flat", "trend") -> segment -> months
  band: OutlookBand[];          // the default scenario's TOTAL bands
  bands?: Record<string, Record<string, OutlookBand[]>>;       // scenario -> segment -> bands
}

export interface Bundle {
  manifest: Manifest;
  outlook?: Outlook | null;     // null or absent until the bundle carries schema 3
  nowcast: Nowcast;
  whatif: WhatIf;
  planning: import("./planning").Planning;
  weekly: import("./weekly").Weekly;
}
