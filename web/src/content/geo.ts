/** Map positions [longitude, latitude] for the modelled source markets. Regional groups sit at their
 *  region's centre and are drawn as regions, not countries. DOMESTIC is the ring at Abu Dhabi. */
export const ABU_DHABI: [number, number] = [54.37, 24.45];

export const MARKET_POSITIONS: Record<string, { at: [number, number]; region?: boolean }> = {
  CHINA: { at: [104, 35] }, EGYPT: { at: [30, 27] }, FRANCE: { at: [2.2, 46.6] }, GERMANY: { at: [10.4, 51.2] },
  INDIA: { at: [78.9, 21] }, ISRAEL: { at: [34.9, 31.5] }, ITALY: { at: [12.6, 42.8] }, KAZAKHSTAN: { at: [66.9, 48] },
  KUWAIT: { at: [47.5, 29.3] }, OMAN: { at: [57, 21.5] }, PHILIPPINES: { at: [122, 12.9] }, "RUSSIAN FEDERATION": { at: [45, 56] },
  "SAUDI ARABIA": { at: [45, 24] }, "UNITED KINGDOM": { at: [-2, 54] }, "UNITED STATES OF AMERICA": { at: [-98, 39] },
  OTHER_EUROPE: { at: [18, 49], region: true }, OTHER_MENA: { at: [8, 31], region: true }, OTHER_EURASIA: { at: [62, 41], region: true },
  OTHER_ASIA_PACIFIC: { at: [118, 0], region: true }, OTHER_AMERICAS_AFRICA: { at: [20, 2], region: true },
};
