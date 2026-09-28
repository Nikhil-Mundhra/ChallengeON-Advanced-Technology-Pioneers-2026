-- Daily guest totals with flight demand and capacity.
SELECT *
FROM guest_flight_daily
ORDER BY date DESC
LIMIT 30;

-- International guest history for a nationality.
SELECT date, guests, new_arrivals, same_day_guests
FROM guest_actuals
WHERE nationality = 'INDIA'
ORDER BY date;

-- Prediction rows that need a guest forecast.
SELECT date, residence_group, nationality, new_arrivals, same_day_guests
FROM guest_prediction_rows
ORDER BY date, residence_group, nationality;

-- Monthly flight demand and weighted load factor.
SELECT
    date_trunc('month', date) AS month,
    SUM(total_pax) AS total_pax,
    SUM(total_seats) AS total_seats,
    SUM(total_pax)::DOUBLE / NULLIF(SUM(total_seats), 0) AS load_factor
FROM flight_daily
GROUP BY month
ORDER BY month;
