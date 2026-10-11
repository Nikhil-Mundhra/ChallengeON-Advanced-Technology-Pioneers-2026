/** External benchmark and reported macro data (May 2025 - September 2026).
 *  Sources:
 *  - Statistics Centre - Abu Dhabi (SCAD)
 *  - Department of Culture and Tourism (DCT Abu Dhabi)
 *  - Abu Dhabi Airports (ADAC / Zayed International Airport AUH)
 *  - JLL MENA Hospitality Reports
 *  - Etihad Airways official traffic releases
 *
 *  Status categories:
 *  - "confirmed": Matches an official or third-party release (DCT, JLL, ADAC, Etihad).
 *  - "modeled": Carried over as external benchmark run-rate; unconfirmed monthly release.
 *  - "unverified": Attributed to an official source but specific monthly release unconfirmed.
 *  - "estimate": Derived / calculated estimate.
 */

export type BenchmarkStatus = "confirmed" | "modeled" | "unverified" | "estimate";

export interface ConfirmedAnchor {
  metric: string;
  value: string;
  source: string;
  status: "confirmed";
  note?: string;
}

export const CONFIRMED_ANCHORS: ConfirmedAnchor[] = [
  {
    metric: "2025 Hotel Occupancy",
    value: "81%",
    source: "DCT Abu Dhabi 2025 Results (Apr 2026)",
    status: "confirmed",
  },
  {
    metric: "2025 Hotel Guests",
    value: "5.9M (up 2.2% YoY)",
    source: "DCT Abu Dhabi",
    status: "confirmed",
  },
  {
    metric: "2025 Average Length of Stay",
    value: "2.9 nights (across all accommodation types)",
    source: "DCT Abu Dhabi",
    status: "confirmed",
  },
  {
    metric: "March 2025 Baseline",
    value: "69% occupancy, >1.2M guest nights, ~417k guests, AED 611M revenue, RevPAR AED 486",
    source: "DCT with SCAD, preliminary",
    status: "confirmed",
  },
  {
    metric: "H1 2026 Hospitality",
    value: "66.8% occupancy, ADR AED 668.30, RevPAR AED 446.60",
    source: "JLL (Aug 11, 2026)",
    status: "confirmed",
  },
  {
    metric: "June 2026 Hospitality",
    value: "65.2% occupancy, ADR AED 486.80, RevPAR AED 317.60",
    source: "JLL",
    status: "confirmed",
  },
  {
    metric: "Hotel Supply",
    value: "Flat at 33,650 keys",
    source: "JLL",
    status: "confirmed",
  },
  {
    metric: "2025 Airport Traffic",
    value: ">33M passengers across 5 airports; AUH ~98% passenger share, 73% aircraft movement share",
    source: "ADAC",
    status: "confirmed",
  },
  {
    metric: "June 26-30, 2026 Snapshot",
    value: "Daily average >93,000 passengers and nearly 500 flights/day",
    source: "ADAC (Jul 2, 2026)",
    status: "confirmed",
    note: "Five-day peak snapshot, not a monthly total.",
  },
  {
    metric: "Etihad 2025 Traffic",
    value: "22.4M passengers, 88.3% load factor",
    source: "Etihad Airways",
    status: "confirmed",
  },
  {
    metric: "Etihad January 2026 Traffic",
    value: "2.2M passengers (up 29%), 89.9% load factor, fleet of 127",
    source: "Etihad Airways",
    status: "confirmed",
  },
  {
    metric: "Airspace Crisis Window",
    value: "UAE airspace closed Feb 28, 2026; limited Etihad schedule Mar 6 to 19",
    source: "GCAA, Etihad, press",
    status: "confirmed",
  },
];

export interface ExternalMonthlyReport {
  month: string;                // YYYY-MM
  hotelNightsMonthly: number;   // total guest nights
  hotelNightsWeekly: number;    // derived weekly run rate: (monthly / days) * 7
  occupancyRate: number;        // percentage
  occupancyStatus: BenchmarkStatus;
  hotelNightsStatus: BenchmarkStatus;
  airportMovements: number;     // total aircraft movements
  airportWeeklyFlights: number; // derived weekly flights
  flightsStatus: BenchmarkStatus;
  context: string;
  note?: string;
}

export const EXTERNAL_MONTHLY_REPORTS: ExternalMonthlyReport[] = [
  {
    month: "2025-05",
    hotelNightsMonthly: 1180000,
    hotelNightsWeekly: 266500,
    occupancyRate: 71.2,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 13200,
    airportWeeklyFlights: 2980,
    flightsStatus: "modeled",
    context: "Shoulder season; solid business travel and conference baseline.",
  },
  {
    month: "2025-06",
    hotelNightsMonthly: 1010000,
    hotelNightsWeekly: 235700,
    occupancyRate: 63.8,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 13600,
    airportWeeklyFlights: 3170,
    flightsStatus: "modeled",
    context: "Standard summer slowdown; lower leisure inbound.",
  },
  {
    month: "2025-07",
    hotelNightsMonthly: 965000,
    hotelNightsWeekly: 217900,
    occupancyRate: 60.5,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14100,
    airportWeeklyFlights: 3185,
    flightsStatus: "modeled",
    context: "Mid-summer trough offset by staycation packages.",
  },
  {
    month: "2025-08",
    hotelNightsMonthly: 1025000,
    hotelNightsWeekly: 231500,
    occupancyRate: 64.1,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14300,
    airportWeeklyFlights: 3230,
    flightsStatus: "modeled",
    context: "End-of-summer domestic demand and early corporate return.",
  },
  {
    month: "2025-09",
    hotelNightsMonthly: 1140000,
    hotelNightsWeekly: 266000,
    occupancyRate: 70.4,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 13500,
    airportWeeklyFlights: 3150,
    flightsStatus: "modeled",
    context: "Rebound in business travel and regional exhibitions.",
  },
  {
    month: "2025-10",
    hotelNightsMonthly: 1290000,
    hotelNightsWeekly: 291300,
    occupancyRate: 77.8,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14200,
    airportWeeklyFlights: 3205,
    flightsStatus: "modeled",
    context: "Start of peak winter tourist season; outdoor leisure events.",
  },
  {
    month: "2025-11",
    hotelNightsMonthly: 1410000,
    hotelNightsWeekly: 329000,
    occupancyRate: 84.5,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14900,
    airportWeeklyFlights: 3475,
    flightsStatus: "modeled",
    context: "Annual peak: ADIPEC conference and Formula 1 Grand Prix demand.",
  },
  {
    month: "2025-12",
    hotelNightsMonthly: 1380000,
    hotelNightsWeekly: 311600,
    occupancyRate: 81.9,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 15200,
    airportWeeklyFlights: 3430,
    flightsStatus: "modeled",
    context: "Holiday leisure influx and major festive cultural programs.",
  },
  {
    month: "2026-01",
    hotelNightsMonthly: 1320000,
    hotelNightsWeekly: 298100,
    occupancyRate: 78.5,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14600,
    airportWeeklyFlights: 3297,
    flightsStatus: "modeled",
    context: "Strong winter baseline; steady international arrivals.",
  },
  {
    month: "2026-02",
    hotelNightsMonthly: 1050000,
    hotelNightsWeekly: 262500,
    occupancyRate: 72.0,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 11800,
    airportWeeklyFlights: 2950,
    flightsStatus: "modeled",
    context: "Airspace closure began Feb 28; full monthly decline likely overstated in modeled series.",
    note: "Decline likely overstated since closure began on Feb 28.",
  },
  {
    month: "2026-03",
    hotelNightsMonthly: 925530,
    hotelNightsWeekly: 209000,
    occupancyRate: 53.0,
    occupancyStatus: "estimate",
    hotelNightsStatus: "unverified",
    airportMovements: 9850,
    airportWeeklyFlights: 2225,
    flightsStatus: "modeled",
    context: "Crisis trough: airspace corridor closure and limited Etihad schedule (Mar 6-19). Occupancy estimated ~52-54% based on March 2025 guest nights/room nights ratio.",
    note: "Source doc cited 68.9% hotel apartment occupancy; overall hotel occupancy estimated at ~52-54% consistent with JLL H1 66.8% average.",
  },
  {
    month: "2026-04",
    hotelNightsMonthly: 1080000,
    hotelNightsWeekly: 252000,
    occupancyRate: 67.0,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 12900,
    airportWeeklyFlights: 3010,
    flightsStatus: "modeled",
    context: "Airspace corridors restored; corporate and transit travel returned.",
  },
  {
    month: "2026-05",
    hotelNightsMonthly: 1150000,
    hotelNightsWeekly: 259700,
    occupancyRate: 66.5,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14200,
    airportWeeklyFlights: 3205,
    flightsStatus: "modeled",
    context: "Regional travel normalized; steady domestic and business performance.",
  },
  {
    month: "2026-06",
    hotelNightsMonthly: 1020000,
    hotelNightsWeekly: 238000,
    occupancyRate: 65.2,
    occupancyStatus: "confirmed",
    hotelNightsStatus: "modeled",
    airportMovements: 14800,
    airportWeeklyFlights: 3450,
    flightsStatus: "modeled",
    context: "Summer off-peak; JLL confirmed occupancy at 65.2%, ADR AED 486.80, RevPAR AED 317.60. ADAC late-June snapshot showed ~500 flights/day.",
    note: "Occupancy confirmed by JLL. Nights modeled.",
  },
  {
    month: "2026-07",
    hotelNightsMonthly: 995000,
    hotelNightsWeekly: 224700,
    occupancyRate: 63.4,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 15300,
    airportWeeklyFlights: 3455,
    flightsStatus: "modeled",
    context: "Summer campaign incentives maintained baseline over July 2025.",
  },
  {
    month: "2026-08",
    hotelNightsMonthly: 1040000,
    hotelNightsWeekly: 234800,
    occupancyRate: 65.8,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 15100,
    airportWeeklyFlights: 3410,
    flightsStatus: "modeled",
    context: "Strong leisure push; citywide occupancy held ahead of August 2025.",
  },
  {
    month: "2026-09",
    hotelNightsMonthly: 1160000,
    hotelNightsWeekly: 270700,
    occupancyRate: 71.5,
    occupancyStatus: "modeled",
    hotelNightsStatus: "modeled",
    airportMovements: 14600,
    airportWeeklyFlights: 3407,
    flightsStatus: "modeled",
    context: "Pre-winter corporate ramp-up; conference calendar reopens.",
  },
];

/** Projected November 2026 outlook based on reported post-crisis trajectory (June-September 2026)
 *  and November 2025 actual baseline (1,410,000 guest nights, ~329,000/week, 84.5% occupancy).
 */
export const NOVEMBER_2026_OUTLOOK = {
  month: "2026-11",
  label: "November 2026",
  hotelNightsMonthly: 1440000,
  hotelNightsWeekly: 336000,
  changeVs2025: 0.021,        // +2.1% growth over Nov 2025 peak
  error: 0.028,               // +/-2.8% error margin
  occupancyRate: 85.8,        // 85.8% occupancy
  weeklyFlights: 3550,        // ~3,550 flights/week
  baseline2025Nights: 1410000,
  status: "estimate" as BenchmarkStatus,
  context: "Projected annual peak: ADIPEC and Formula 1 Abu Dhabi Grand Prix demand on fully normalized airspace corridors and expanded Terminal A airline frequencies.",
} as const;

/** Map of YYYY-MM to derived weekly guest nights. */
export const EXTERNAL_WEEKLY_RUN_RATES: Record<string, number> = Object.fromEntries(
  EXTERNAL_MONTHLY_REPORTS.map((r) => [r.month, r.hotelNightsWeekly])
);

/** Get external reported weekly run rate for a given week string (YYYY-MM-DD). */
export function getExternalWeeklyRate(week: string): number | null {
  const mo = week.slice(0, 7);
  return EXTERNAL_WEEKLY_RUN_RATES[mo] ?? null;
}
