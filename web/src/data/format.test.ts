import { describe, expect, it } from "vitest";
import { formatMonth, formatPercent, formatShare, formatSigned, toneOf } from "./format";

describe("format", () => {
  it("signs values and percentages once", () => {
    expect(formatSigned(1234)).toBe("+1,234");
    expect(formatSigned(-56)).toBe("-56");
    expect(formatSigned(0)).toBe("0");
    expect(formatPercent(0.034)).toBe("+3.4%");
    expect(formatPercent(-0.1, 0)).toBe("-10%");
    expect(formatShare(0.282)).toBe("28.2%");
  });
  it("names months and tones", () => {
    expect(formatMonth("2025-07-21")).toBe("Jul 2025");
    expect(formatMonth("2026-11-30", "short")).toBe("Nov 26");
    expect(toneOf(3)).toBe("tone-up");
    expect(toneOf(-1)).toBe("tone-down");
    expect(toneOf(0)).toBeUndefined();
  });
});
