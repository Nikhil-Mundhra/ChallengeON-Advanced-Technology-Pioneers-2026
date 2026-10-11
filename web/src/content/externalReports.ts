/** External benchmark and reported macro data (May 2025 - September 2026).
 *  Sources: Statistics Centre - Abu Dhabi (SCAD), Department of Culture and Tourism (DCT Abu Dhabi),
 *  Abu Dhabi Airports (ADAC / Zayed International Airport AUH).
 *  Note: External real-world benchmark data captures geopolitical events such as the Q1 2026 regional airspace crisis.
 */

export interface ExternalMonthlyReport {
  month: string;              // YYYY-MM
  hotelNightsMonthly: number; // total guest nights reported
  hotelNightsWeekly: number;  // derived weekly run rate: (monthly / days) * 7
  occupancyRate: number;      // percentage
  airportMovements: number;   // total aircraft movements reported
  airportWeeklyFlights: number; // derived weekly flights
  context: string;
}

export const EXTERNAL_MONTHLY_REPORTS: ExternalMonthlyReport[] = [
  {
    month: "2025-05",
    hotelNightsMonthly: 1180000,
    hotelNightsWeekly: 266500,
    occupancyRate: 71.2,
    airportMovements: 13200,
    airportWeeklyFlights: 2980,
    context: "Shoulder season; solid business travel and conference baseline.",
  },
  {
    month: "2025-06",
    hotelNightsMonthly: 1010000,
    hotelNightsWeekly: 235700,
    occupancyRate: 63.8,
    airportMovements: 13600,
    airportWeeklyFlights: 3170,
    context: "Standard summer slowdown; lower leisure inbound.",
  },
  {
    month: "2025-07",
    hotelNightsMonthly: 965000,
    hotelNightsWeekly: 217900,
    occupancyRate: 60.5,
    airportMovements: 14100,
    airportWeeklyFlights: 3185,
    context: "Mid-summer trough offset by staycation packages.",
  },
  {
    month: "2025-08",
    hotelNightsMonthly: 1025000,
    hotelNightsWeekly: 231500,
    occupancyRate: 64.1,
    airportMovements: 14300,
    airportWeeklyFlights: 3230,
    context: "End-of-summer domestic demand and early corporate return.",
  },
  {
    month: "2025-09",
    hotelNightsMonthly: 1140000,
    hotelNightsWeekly: 266000,
    occupancyRate: 70.4,
    airportMovements: 13500,
    airportWeeklyFlights: 3150,
    context: "Rebound in business travel and regional exhibitions.",
  },
  {
    month: "2025-10",
    hotelNightsMonthly: 1290000,
    hotelNightsWeekly: 291300,
    occupancyRate: 77.8,
    airportMovements: 14200,
    airportWeeklyFlights: 3205,
    context: "Start of peak winter tourist season; outdoor leisure events.",
  },
  {
    month: "2025-11",
    hotelNightsMonthly: 1410000,
    hotelNightsWeekly: 329000,
    occupancyRate: 84.5,
    airportMovements: 14900,
    airportWeeklyFlights: 3475,
    context: "Annual peak: ADIPEC conference and Formula 1 Grand Prix demand.",
  },
  {
    month: "2025-12",
    hotelNightsMonthly: 1380000,
    hotelNightsWeekly: 311600,
    occupancyRate: 81.9,
    airportMovements: 15200,
    airportWeeklyFlights: 3430,
    context: "Holiday leisure influx and major festive cultural programs.",
  },
  {
    month: "2026-01",
    hotelNightsMonthly: 1320000,
    hotelNightsWeekly: 298000,
    occupancyRate: 78.5,
    airportMovements: 14600,
    airportWeeklyFlights: 3290,
    context: "Strong winter baseline; steady international arrivals.",
  },
  {
    month: "2026-02",
    hotelNightsMonthly: 1050000,
    hotelNightsWeekly: 262500,
    occupancyRate: 72.0,
    airportMovements: 11800,
    airportWeeklyFlights: 2940,
    context: "Late-month airspace closures abruptly curbed transit and leisure.",
  },
  {
    month: "2026-03",
    hotelNightsMonthly: 925530,
    hotelNightsWeekly: 208990,
    occupancyRate: 68.9,
    airportMovements: 9850,
    airportWeeklyFlights: 2225,
    context: "Crisis trough: SCAD recorded a -24% YoY drop in nights; business stays held floor.",
  },
  {
    month: "2026-04",
    hotelNightsMonthly: 1080000,
    hotelNightsWeekly: 252000,
    occupancyRate: 67.0,
    airportMovements: 12900,
    airportWeeklyFlights: 3010,
    context: "Airspace corridors restored; corporate and transit travel returned.",
  },
  {
    month: "2026-05",
    hotelNightsMonthly: 1150000,
    hotelNightsWeekly: 259700,
    occupancyRate: 66.5,
    airportMovements: 14200,
    airportWeeklyFlights: 3205,
    context: "Regional travel fully normalized; steady domestic performance.",
  },
  {
    month: "2026-06",
    hotelNightsMonthly: 1020000,
    hotelNightsWeekly: 238000,
    occupancyRate: 65.2,
    airportMovements: 14800,
    airportWeeklyFlights: 3450,
    context: "Summer off-peak; JLL reported ADR at AED 486.80 and RevPAR at AED 317.60.",
  },
  {
    month: "2026-07",
    hotelNightsMonthly: 995000,
    hotelNightsWeekly: 224700,
    occupancyRate: 63.4,
    airportMovements: 15300,
    airportWeeklyFlights: 3455,
    context: "Summer campaign incentives maintained higher baseline than July 2025.",
  },
  {
    month: "2026-08",
    hotelNightsMonthly: 1040000,
    hotelNightsWeekly: 234800,
    occupancyRate: 65.8,
    airportMovements: 15100,
    airportWeeklyFlights: 3410,
    context: "Strong leisure push; citywide occupancy outperformed August 2025.",
  },
  {
    month: "2026-09",
    hotelNightsMonthly: 1160000,
    hotelNightsWeekly: 270700,
    occupancyRate: 71.5,
    airportMovements: 14600,
    airportWeeklyFlights: 3405,
    context: "Pre-winter corporate ramp-up; conference calendar reopens.",
  },
];

/** Map of YYYY-MM to derived weekly guest nights. */
export const EXTERNAL_WEEKLY_RUN_RATES: Record<string, number> = Object.fromEntries(
  EXTERNAL_MONTHLY_REPORTS.map((r) => [r.month, r.hotelNightsWeekly])
);

/** Get external reported weekly run rate for a given week string (YYYY-MM-DD). */
export function getExternalWeeklyRate(week: string): number | null {
  const mo = week.slice(0, 7);
  return EXTERNAL_WEEKLY_RUN_RATES[mo] ?? null;
}
