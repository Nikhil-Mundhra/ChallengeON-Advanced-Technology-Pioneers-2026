import type { MarketWhatIf } from "./types";

/**
 * Guests for one market when its predicted-period arrivals are multiplied by `factor` (1 = as
 * predicted): guests_t = max(base_t + pre_t + factor * in_t, floor) * multiplier_t, where pre_t / in_t
 * are the kernel flow from arrivals before / inside the predicted period (arrivals before it are
 * observed and do not change).
 */
export function whatIfGuests(market: MarketWhatIf, factor = 1): number[] {
  return market.date.map((_, t) => Math.max(market.base[t] + market.pre[t] + factor * market.in[t], market.floor) * market.multiplier[t]);
}
