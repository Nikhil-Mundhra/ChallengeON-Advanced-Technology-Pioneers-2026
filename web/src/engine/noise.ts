import type { NoiseParams } from "./types";

/** Log-error variance h days ahead (AR(1)): v0 phi^2h + sigma^2 (1 - phi^2h) / (1 - phi^2). */
export function variance(noise: NoiseParams, horizon: number): number {
  const decay = noise.phi ** (2 * horizon);
  const stationary = noise.phi < 1 ? noise.sigma_eta ** 2 / (1 - noise.phi ** 2) : Infinity;
  return noise.v0 * decay + stationary * (1 - decay);
}

/**
 * Central interval for the SUM of `pred` over days with horizons `horizon` (NoiseModel.range_interval):
 * the sum's log error is the prediction-weighted mean of the daily log errors, with
 * cov(e_i, e_j) = phi^|h_i - h_j| * var(min(h_i, h_j)).
 */
export function rangeInterval(noise: NoiseParams, horizon: number[], pred: number[], z: number): [number, number] {
  const total = pred.reduce((sum, p) => sum + p, 0);
  const weights = pred.map((p) => p / total);
  let varianceOfMean = 0;
  for (let i = 0; i < horizon.length; i += 1) {
    for (let j = 0; j < horizon.length; j += 1) {
      const earlier = Math.min(horizon[i], horizon[j]);
      varianceOfMean += weights[i] * weights[j] * noise.phi ** Math.abs(horizon[i] - horizon[j]) * variance(noise, earlier);
    }
  }
  const sd = Math.sqrt(Math.max(varianceOfMean, 0));
  return [total * Math.exp(-z * sd), total * Math.exp(z * sd)];
}

/** Daily central interval: pred * exp(+-z * sd(h)). */
export function dailyInterval(noise: NoiseParams, horizon: number, pred: number, z: number): [number, number] {
  const sd = Math.sqrt(variance(noise, horizon));
  return [pred * Math.exp(-z * sd), pred * Math.exp(z * sd)];
}
