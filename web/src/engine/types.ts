/** Shapes of the bundle written by `twin export` (src/tourism_twin/export/bundle.py, schema 1). */

export interface Manifest {
  schema_version: number;
  version: string;
  created: string;
  git_sha: string;
  spec: string;
  coverage: number;
  predicted_period: { start: string; end: string };
  files: Record<"nowcast" | "whatif" | "planning" | "weekly" | "golden", string>;
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

export interface Bundle {
  manifest: Manifest;
  nowcast: Nowcast;
  whatif: WhatIf;
  planning: import("./planning").Planning;
  weekly: import("./weekly").Weekly;
}
