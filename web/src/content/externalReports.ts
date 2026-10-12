/** Figures published by others, shown on the report page under "Reported by others (not our model)".
 *  None comes from the competition data or the model, and none can be checked from this repository.
 *  Keep a figure only with a named source; never plot it on a model chart or set it beside a model error. */

/** "reported": as published by the named source, not checked against the source here. */
export type ReportedStatus = "reported";

export interface ReportedFigure {
  metric: string;
  value: string;
  source: string;
  published: string | null;   // when the source published it, as given; null when not recorded
  status: ReportedStatus;
  note?: string;
}

export const REPORTED_FIGURES: ReportedFigure[] = [
  { metric: "Hotel occupancy, 2025", value: "81%", source: "DCT Abu Dhabi, 2025 results", published: "April 2026", status: "reported" },
  { metric: "Hotel guests, 2025", value: "5.9 million (up 2.2% on 2024)", source: "DCT Abu Dhabi, 2025 results", published: "April 2026", status: "reported" },
  { metric: "Average stay, 2025", value: "2.9 nights (all accommodation types)", source: "DCT Abu Dhabi, 2025 results", published: "April 2026", status: "reported" },
  { metric: "Hotels, first half of 2026", value: "Occupancy 66.8%, ADR AED 668.30, RevPAR AED 446.60", source: "JLL", published: "11 August 2026", status: "reported" },
  { metric: "Hotels, June 2026", value: "Occupancy 65.2%, ADR AED 486.80, RevPAR AED 317.60", source: "JLL", published: null, status: "reported" },
  { metric: "Airport passengers, 2025", value: "Over 33 million across 5 airports; Zayed International about 98% of passengers and 73% of aircraft movements", source: "Abu Dhabi Airports (ADAC)", published: null, status: "reported" },
  { metric: "Airport traffic, 26 to 30 June 2026", value: "Over 93,000 passengers and nearly 500 flights a day on average", source: "Abu Dhabi Airports (ADAC)", published: "2 July 2026", status: "reported", note: "A five-day peak, not a monthly average." },
  { metric: "Etihad passengers, 2025", value: "22.4 million, load factor 88.3%", source: "Etihad Airways", published: null, status: "reported" },
  { metric: "Etihad passengers, January 2026", value: "2.2 million (up 29%), load factor 89.9%, 127 aircraft", source: "Etihad Airways", published: null, status: "reported" },
  { metric: "UAE airspace closure", value: "Closed 28 February 2026; Etihad ran a limited schedule from 6 to 19 March 2026", source: "GCAA and Etihad Airways", published: null, status: "reported", note: "Begins on the last day of the competition data, so the model has no days after it." },
];
