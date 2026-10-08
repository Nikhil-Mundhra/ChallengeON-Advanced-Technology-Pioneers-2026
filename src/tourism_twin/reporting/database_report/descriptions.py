"""Human descriptions of the curated tables' columns and the analytical views."""


GUEST_DESCRIPTIONS = {
    "date": "Calendar date for the guest observation.",
    "residence_group": "Domestic or International segment.",
    "nationality": "Guest nationality; NULL for domestic rows.",
    "guests": "Prediction target. NULL in the test/prediction split.",
    "new_arrivals": "Guests newly arriving on the date.",
    "same_day_guests": "Same-day visitors. NULL can mean suppressed, unavailable, or not applicable.",
    "dataset_split": "Train or test source classification.",
    "source_file": "Original workbook filename for lineage.",
    "source_grain": "Explicit observation grain ('daily').",
    "is_source_present": "True if present in source, False if absent from expected date grid.",
    "target_available": "True if target 'guests' is populated (train split).",
    "is_suppressed_arrival": "True if raw arrival value was missing/suppressed.",
    "is_suppressed_same_day": "True if raw same-day guest value was missing/suppressed.",
}


FLIGHT_DESCRIPTIONS = {
    "date": "Operating date represented by the record.",
    "departure_country_name": "Country from which the flight departs.",
    "departure_city": "Origin city.",
    "arrival_city": "Arrival city; currently Abu Dhabi.",
    "airline_name": "Operating carrier name.",
    "average_weekly_frequency": "Average weekly service frequency where supplied.",
    "business_class_p2p_count": "Point-to-point Business Class passengers.",
    "business_class_seat_capacity": "Business Class seats offered.",
    "economy_class_p2p_count": "Point-to-point Economy Class passengers.",
    "economy_class_seat_capacity": "Economy Class seats offered.",
    "first_class_p2p_count": "Point-to-point First Class passengers.",
    "first_class_seat_capacity": "First Class seats offered.",
    "load_factor": "Total passengers divided by total seats.",
    "total_p2p": "All point-to-point passengers.",
    "total_pax": "All passengers, including P2P, transfer, and transit.",
    "total_pax_excluding_infant": "Passengers excluding infants.",
    "total_seats": "Total seat capacity.",
    "total_transfer": "Passengers transferring to another flight at Abu Dhabi.",
    "total_transit": "Passengers transiting through Abu Dhabi.",
    "transfer_business_class_count": "Transfer passengers in Business Class.",
    "transfer_economy_class_count": "Transfer passengers in Economy Class.",
    "transfer_first_class_count": "Transfer passengers in First Class.",
    "transit_business_class_count": "Transit passengers in Business Class.",
    "transit_first_count": "Transit passengers in First Class.",
    "destination": "Destination IATA code; currently AUH.",
    "source_grain": "Explicit observation grain ('daily' for 2023+, 'monthly' for 2022).",
    "is_load_factor_outlier": "Flag marking observations with unclipped load factor > 100%.",
    "source_file": "Original source file name for provenance.",
}


VIEW_DESCRIPTIONS = {
    "guest_actuals": "Guest rows with a populated target for analysis and model training.",
    "guest_prediction_rows": "Guest rows whose target must be predicted.",
    "guest_daily_totals": "Guest facts aggregated to one row per date and dataset split.",
    "flight_daily_totals": "Flight facts aggregated to daily demand, capacity, and weighted load factor.",
    "guest_flight_daily": "Safe daily join between guest totals and flight totals.",
    "flight_all": "Unified view combining daily observations and 2022 monthly records with source_grain flag.",
}
