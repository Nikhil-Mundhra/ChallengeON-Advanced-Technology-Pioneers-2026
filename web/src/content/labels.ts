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
  "Guests-per-arrival factor": "Hotel guests per visitor",
};
export const leverName = (engineName: string) => LEVER_NAMES[engineName.replace(/ \(.*\)$/, "")] ?? engineName;
