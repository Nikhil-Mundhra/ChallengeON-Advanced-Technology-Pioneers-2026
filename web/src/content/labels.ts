/** Plain-language names shown in the UI for model codes (seasons, levers). */
export const SEASON_NAMES: Record<string, string> = {
  Winter_Peak: "Winter", Spring_Shoulder: "Spring", Summer_Trough: "Summer", Autumn_Shoulder: "Autumn",
};
export const SEASON_MONTHS: Record<string, string> = {
  Winter_Peak: "November to March", Spring_Shoulder: "April and May", Summer_Trough: "June to August", Autumn_Shoulder: "September and October",
};
/** Names for the engine's sensitivity rows (engine/planning.tornado lever_name prefixes). */
export const LEVER_NAMES: Record<string, string> = {
  "Seat Capacity": "Seats",
  "Load Factor": "How full flights are",
  "P2P Share": "Passengers who stop in Abu Dhabi",
  "Response Multiplier": "Visitors who book a hotel",
  "Guests-per-arrival factor": "Hotel nights per visitor",
};
export const leverName = (engineName: string) => LEVER_NAMES[engineName.replace(/ \(.*\)$/, "")] ?? engineName;

/** Plain names for event types in domain/events.csv (weekly.json `event`). */
export const EVENT_NAMES: Record<string, string> = {
  adipec: "ADIPEC", chinese_new_year: "Chinese New Year", christmas_new_year: "Christmas and New Year",
  eid_al_adha: "Eid al-Adha", eid_al_fitr: "Eid al-Fitr", f1_grand_prix: "Abu Dhabi Grand Prix",
  islamic_new_year: "Islamic New Year", morocco_winter_block: "Winter group stays", national_day: "UAE National Day",
  new_years_eve: "New Year's Eve", prophets_birthday: "Prophet's Birthday", ramadan: "Ramadan",
};
export const eventName = (code: string | null | undefined) => (code ? EVENT_NAMES[code] ?? code.replace(/_/g, " ") : null);

/** Plain market names (model codes in the bundle); anything not listed is title-cased. */
const MARKET_NAMES: Record<string, string> = {
  DOMESTIC: "UAE residents", "RUSSIAN FEDERATION": "Russia", "UNITED STATES OF AMERICA": "United States",
  OTHER_EUROPE: "Other Europe", OTHER_MENA: "Other Middle East and North Africa", OTHER_ASIA_PACIFIC: "Other Asia Pacific",
  OTHER_AMERICAS_AFRICA: "Other Americas and Africa", OTHER_EURASIA: "Other Eurasia", ALL: "All markets",
};
export const marketName = (code: string) =>
  MARKET_NAMES[code] ?? code.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()).replace(/_/g, " ");
